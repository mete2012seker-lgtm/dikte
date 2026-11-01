"""OpenRouter anahtarını Windows DPAPI ile şifreleyerek saklar.

Dosyada düz metin anahtar bulunmaz. Şifre çözme yalnız aynı Windows kullanıcısında,
aynı makinede çalışır; başka yerde anahtar yeniden girilmelidir.
"""

from __future__ import annotations

import base64
import ctypes
import json
import logging
import os
import sys
from ctypes import wintypes
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

CRYPTPROTECT_UI_FORBIDDEN = 0x01
MASK_PREFIX = "sk-or-…"


class SecretError(RuntimeError):
    """Anahtar şifrelenemedi veya çözülemedi."""


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _crypt32():
    if sys.platform != "win32":
        raise SecretError("Anahtar saklama bu platformda desteklenmiyor.")
    crypt32 = ctypes.windll.crypt32
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    return crypt32


def _blob(data: bytes) -> _DataBlob:
    buffer = ctypes.create_string_buffer(data, len(data))
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))


def _free(blob: _DataBlob) -> None:
    try:
        ctypes.windll.kernel32.LocalFree(blob.pbData)
    except Exception:
        pass


def protect(data: bytes) -> bytes:
    """DPAPI ile şifreler (yalnız geçerli kullanıcıda çözülebilir)."""
    if not data:
        raise SecretError("Boş anahtar saklanamaz.")
    crypt32 = _crypt32()
    source = _blob(data)
    result = _DataBlob()
    ok = crypt32.CryptProtectData(
        ctypes.byref(source), None, None, None, None,
        CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(result),
    )
    if not ok:
        raise SecretError("Anahtar şifrelenemedi.")
    try:
        return ctypes.string_at(result.pbData, int(result.cbData))
    finally:
        _free(result)


def unprotect(blob: bytes) -> bytes:
    """DPAPI şifresini çözer; başka kullanıcıda hata verir."""
    if not blob:
        raise SecretError("Şifreli anahtar boş.")
    crypt32 = _crypt32()
    source = _blob(blob)
    result = _DataBlob()
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None,
        CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(result),
    )
    if not ok:
        raise SecretError("Anahtar çözülemedi; yeniden girilmesi gerekiyor.")
    try:
        return ctypes.string_at(result.pbData, int(result.cbData))
    finally:
        _free(result)


def mask(key: str) -> str:
    """Ekranda gösterilecek maskeli biçim: sk-or-…abcd."""
    key = (key or "").strip()
    if len(key) < 4:
        return MASK_PREFIX
    return MASK_PREFIX + key[-4:]


class SecretStore:
    """data/secrets.json içinde DPAPI blob'u tutar."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or config.SECRETS_FILE)

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except Exception as exc:
            logger.warning("Sır dosyası okunamadı: %s", exc)
            return {}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(self.path.name + ".tmp")
        try:
            temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.path)
        except Exception as exc:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                pass
            raise SecretError("Anahtar kaydedilemedi.") from exc

    def has_key(self) -> bool:
        return bool(self.load_key())

    def save_key(self, key: str) -> str:
        key = (key or "").strip()
        if len(key) < 8:
            raise SecretError("Geçerli bir OpenRouter anahtarı gir.")
        encrypted = protect(key.encode("utf-8"))
        data = self._read()
        data["openrouter"] = {"blob": base64.b64encode(encrypted).decode("ascii")}
        self._write(data)
        return mask(key)

    def load_key(self) -> str | None:
        entry = self._read().get("openrouter")
        if not isinstance(entry, dict):
            return None
        blob = entry.get("blob")
        if not isinstance(blob, str) or not blob:
            return None
        try:
            raw = unprotect(base64.b64decode(blob, validate=True))
            return raw.decode("utf-8")
        except Exception as exc:
            logger.warning("Anahtar çözülemedi: %s", exc)
            return None

    def masked(self) -> str | None:
        key = self.load_key()
        return mask(key) if key else None

    def delete_key(self) -> bool:
        data = self._read()
        if "openrouter" not in data:
            return False
        data.pop("openrouter", None)
        if data:
            self._write(data)
        else:
            try:
                self.path.unlink(missing_ok=True)
            except Exception as exc:
                raise SecretError("Anahtar silinemedi.") from exc
        return True
