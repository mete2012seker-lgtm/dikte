"""Kalıcı ayarlar: aktif model, kısayol ve geçmiş tercihi."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)


class SettingsError(RuntimeError):
    pass


HOTKEY_CHOICES = {
    "right_ctrl": "Sağ Ctrl",
    "left_ctrl": "Sol Ctrl",
    "right_alt": "Sağ Alt",
    "left_alt": "Sol Alt",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
}

DEFAULT_HOTKEY = "right_ctrl"
AUTO_MODEL = "auto"

DEFAULTS = {
    "version": 1,
    "save_history": True,
    "hotkey": DEFAULT_HOTKEY,
    "active_model": AUTO_MODEL,
}


def hotkey_label(key_id: str) -> str:
    return HOTKEY_CHOICES.get(key_id, HOTKEY_CHOICES[DEFAULT_HOTKEY])


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
        self._data = dict(DEFAULTS)
        self.load()

    def load(self) -> dict:
        data = dict(DEFAULTS)
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    raise ValueError("Ayarlar bir nesne değil")
                data.update(raw)
            except Exception as exc:
                logger.warning("Ayarlar okunamadı (%s), yedekleniyor", exc)
                self._backup()
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
        result["version"] = 1
        result["save_history"] = bool(data.get("save_history", DEFAULTS["save_history"]))
        hotkey = data.get("hotkey", DEFAULT_HOTKEY)
        result["hotkey"] = hotkey if hotkey in HOTKEY_CHOICES else DEFAULT_HOTKEY
        model = data.get("active_model", AUTO_MODEL)
        result["active_model"] = model if isinstance(model, str) and model else AUTO_MODEL
        return result

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def as_dict(self) -> dict:
        return dict(self._data)

    def save(self, **changes) -> dict:
        merged = dict(self._data)
        merged.update(changes)
        data = self._validate(merged)
        self._write(data)
        self._data = data
        return dict(data)

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(self.path.name + ".tmp")
        try:
            temp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temp, self.path)
        except Exception as exc:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                pass
            raise SettingsError("Ayarlar kaydedilemedi.") from exc
