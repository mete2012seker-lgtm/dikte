"""Kaldırma desteği: kurulum kontrolü, boyut hesabı ve kaldırıcıyı başlatma.

Kurulu sürümde Inno Setup `unins000.exe` dosyasını uygulama klasörüne yazar.
Geliştirme ortamında uygulama kurulmuş sayılmaz.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)


class UninstallError(RuntimeError):
    """Kaldırma işlemi başlatılamadı."""


def uninstaller_path() -> Path:
    """Inno Setup kaldırıcısının yolu (kurulu değilse de yol döner)."""
    return config.exe_dir() / "unins000.exe"


def is_installed() -> bool:
    """Uygulama kurulumla geldi mi (kaldırıcı var mı)?"""
    if not config.is_packaged():
        return False
    return uninstaller_path().exists()


def _dir_size(folder: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(folder):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
    return total


def data_bytes() -> int:
    """Kaldırıldığında silinecek verinin toplam boyutu (modeller + veri + log)."""
    total = 0
    for folder in (config.MODELS_DIR, config.DATA_DIR, config.LOG_DIR, config.TEMP_DIR):
        total += _dir_size(Path(folder))
    if config.is_packaged():
        total += _dir_size(config.exe_dir())
    return total


def format_size(num: int) -> str:
    """Baytı insan okur biçime çevirir (1,2 GB gibi)."""
    value = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}".replace(".", ",")
        value /= 1024
    return f"{value:.1f} TB"


def set_autostart(enabled: bool) -> None:
    """Windows açılışında başlatmayı HKCU Run anahtarına yazar ya da siler."""
    try:
        import winreg
    except ImportError as exc:
        raise UninstallError("Bu işlev yalnızca Windows'ta çalışır.") from exc
    try:
        run_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, config.AUTOSTART_RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
    except OSError as exc:
        raise UninstallError("Kayıt defterine yazılamadı.") from exc
    with run_key:
        if enabled:
            target = f'"{sys.executable}"'
            winreg.SetValueEx(run_key, config.AUTOSTART_VALUE, 0, winreg.REG_SZ, target)
        else:
            try:
                winreg.DeleteValue(run_key, config.AUTOSTART_VALUE)
            except FileNotFoundError:
                pass


def autostart_enabled() -> bool:
    """Windows açılışında başlatma açık mı?"""
    try:
        import winreg
    except ImportError:
        return False
    try:
        run_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, config.AUTOSTART_RUN_KEY, 0, winreg.KEY_QUERY_VALUE
        )
        winreg.QueryValueEx(run_key, config.AUTOSTART_VALUE)
        return True
    except OSError:
        return False


def run_uninstaller() -> None:
    """Inno Setup kaldırıcısını sessiz kipte başlatır."""
    path = uninstaller_path()
    if not path.exists():
        raise UninstallError("Kaldırıcı bulunamadı. Bu sürüm kurulumla gelmemiş.")
    try:
        subprocess.Popen(
            [str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
            cwd=str(path.parent),
            close_fds=True,
        )
    except OSError as exc:
        logger.exception("Kaldırıcı başlatılamadı")
        raise UninstallError(f"Kaldırıcı başlatılamadı: {exc}") from exc
