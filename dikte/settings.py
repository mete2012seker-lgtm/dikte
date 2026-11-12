"""Kalıcı ayarlar: model, kısayol, geçmiş, dil ve metin sağlayıcısı."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path

from . import config
from .hotkey import (
    DEFAULT_HOTKEY,
    HOTKEY_CHOICES,
    format_hotkey_label,
    is_valid_hotkey,
    normalize_hotkey,
)

logger = logging.getLogger(__name__)


class SettingsError(RuntimeError):
    pass


TEXT_PROVIDER_CHOICES = {
    "none": "Kapalı",
    "local": "Yerel model",
    "openrouter": "OpenRouter",
}

OUTPUT_LANGUAGE_CHOICES = dict(config.OUTPUT_LANGUAGES)
INPUT_LANGUAGE_CHOICES = {"auto": "Otomatik", "tr": "Türkçe"}
THEME_CHOICES = {"system": "Sistem", "light": "Açık", "dark": "Koyu"}
DESIGN_STYLE_CHOICES = {"dikte_ai": "Sade Dikte.AI", "classic": "Klasik (Magic UI)"}

AUTO_MODEL = "auto"
DEFAULT_TEXT_MODEL = "qwen3-4b"
DEFAULT_THEME = "system"
DEFAULT_DESIGN_STYLE = "dikte_ai"

DEFAULTS = {
    "version": 2,
    "save_history": True,
    "hotkey": DEFAULT_HOTKEY,
    "active_model": AUTO_MODEL,
    "output_language": "tr",
    "auto_translate": False,
    "input_language": "auto",
    "auto_paste": True,
    "text_provider": "none",
    "text_model": DEFAULT_TEXT_MODEL,
    "openrouter_model": None,
    "openrouter_show_all": False,
    "system_prompt": config.DEFAULT_SYSTEM_PROMPT,
    "theme": DEFAULT_THEME,
    "design_style": DEFAULT_DESIGN_STYLE,
    "setup_done": False,
    "sidebar_collapsed": False,
    "autostart": False,
    "update_check_on_start": True,
    "update_last_check": None,
    "effects": True,
}


def hotkey_label(key_id: str) -> str:
    return format_hotkey_label(key_id)


def output_language_label(code: str) -> str:
    return OUTPUT_LANGUAGE_CHOICES.get(code, OUTPUT_LANGUAGE_CHOICES["tr"])


def text_provider_label(provider: str) -> str:
    return TEXT_PROVIDER_CHOICES.get(provider, TEXT_PROVIDER_CHOICES["none"])


def _choice(value, allowed, default):
    return value if isinstance(value, str) and value in allowed else default


def _flag(value, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _text(value, default: str) -> str:
    return value if isinstance(value, str) and value.strip() else default


def _backup_path(path: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.stem}.bozuk-{stamp}{path.suffix}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}.bozuk-{stamp}-{counter}{path.suffix}")
        counter += 1
    return candidate


class SettingsStore:
    """settings.json dosyasını okur/yazar. Bozuk dosya uygulamayı durdurmaz."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or config.SETTINGS_FILE)
        self._lock = threading.RLock()
        self._data = dict(DEFAULTS)
        self.load()

    def load(self) -> dict:
        with self._lock:
            data = dict(DEFAULTS)
            if self.path.exists():
                try:
                    raw = json.loads(self.path.read_text(encoding="utf-8"))
                    if not isinstance(raw, dict):
                        raise ValueError("Ayarlar bir nesne değil")
                    data.update(raw)
                except (json.JSONDecodeError, ValueError, TypeError) as exc:
                    logger.warning("Ayarlar okunamadı (%s), yedekleniyor", exc)
                    self._backup()
                except OSError as exc:
                    logger.warning("Ayarlar dosyasına erişilemedi (%s)", exc)
                    return dict(self._data)
            self._data = self._validate(data)
            return dict(self._data)

    def _backup(self) -> None:
        try:
            self.path.rename(_backup_path(self.path))
        except Exception as exc:
            logger.warning("Bozuk ayar dosyası yedeklenemedi: %s", exc)

    @staticmethod
    def _validate(data: dict) -> dict:
        result = dict(DEFAULTS)
        result.update({key: value for key, value in data.items() if key not in DEFAULTS})
        result["version"] = 2
        result["save_history"] = _flag(data.get("save_history"), DEFAULTS["save_history"])
        raw_hotkey = data.get("hotkey")
        if isinstance(raw_hotkey, str) and is_valid_hotkey(raw_hotkey):
            result["hotkey"] = normalize_hotkey(raw_hotkey)
        else:
            result["hotkey"] = DEFAULT_HOTKEY
        result["active_model"] = _text(data.get("active_model"), AUTO_MODEL)

        result["output_language"] = _choice(
            data.get("output_language"), OUTPUT_LANGUAGE_CHOICES, "tr"
        )
        result["auto_translate"] = _flag(
            data.get("auto_translate"), DEFAULTS["auto_translate"]
        )
        result["input_language"] = _choice(
            data.get("input_language"), INPUT_LANGUAGE_CHOICES, "auto"
        )
        result["auto_paste"] = _flag(data.get("auto_paste"), DEFAULTS["auto_paste"])
        result["text_provider"] = _choice(
            data.get("text_provider"), TEXT_PROVIDER_CHOICES, "none"
        )
        result["text_model"] = _text(data.get("text_model"), DEFAULT_TEXT_MODEL)
        openrouter_model = data.get("openrouter_model")
        result["openrouter_model"] = (
            openrouter_model if isinstance(openrouter_model, str) and openrouter_model.strip() else None
        )
        result["openrouter_show_all"] = _flag(
            data.get("openrouter_show_all"), DEFAULTS["openrouter_show_all"]
        )
        result["system_prompt"] = _text(
            data.get("system_prompt"), config.DEFAULT_SYSTEM_PROMPT
        )
        result["theme"] = _choice(data.get("theme"), THEME_CHOICES, DEFAULT_THEME)
        result["design_style"] = _choice(
            data.get("design_style"), config.DESIGN_STYLES, DEFAULT_DESIGN_STYLE
        )
        result["setup_done"] = _flag(data.get("setup_done"), DEFAULTS["setup_done"])
        result["sidebar_collapsed"] = _flag(
            data.get("sidebar_collapsed"), DEFAULTS["sidebar_collapsed"]
        )
        result["autostart"] = _flag(data.get("autostart"), DEFAULTS["autostart"])
        result["update_check_on_start"] = _flag(
            data.get("update_check_on_start"), DEFAULTS["update_check_on_start"]
        )
        last_check = data.get("update_last_check")
        result["update_last_check"] = last_check if isinstance(last_check, str) else None
        result["effects"] = _flag(data.get("effects"), DEFAULTS["effects"])
        return result

    def get(self, key: str, default=None):
        with self._lock:
            return self._data.get(key, default)

    def set_hotkey(self, hotkey: str) -> dict:
        if not is_valid_hotkey(hotkey):
            raise ValueError("Geçersiz kısayol kombinasyonu.")
        return self.save(hotkey=normalize_hotkey(hotkey))

    def as_dict(self) -> dict:
        with self._lock:
            return dict(self._data)

    def save(self, **changes) -> dict:
        with self._lock:
            merged = dict(self._data)
            merged.update(changes)
            data = self._validate(merged)
            self._write(data)
            self._data = data
            return dict(data)

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(
            f"{self.path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
        )
        try:
            payload = json.dumps(data, ensure_ascii=False, indent=2)
            with open(temp, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self.path)
        except Exception as exc:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                pass
            raise SettingsError("Ayarlar kaydedilemedi.") from exc
