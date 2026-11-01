"""Etkin pencereye Ctrl+V gönderir (otomatik yapıştırma).

Dikte'nin kendi penceresi etkinse yapıştırma atlanır. Yönetici pencerelerine
Windows UIPI nedeniyle tuş gitmeyebilir; bu durumda kullanıcı elle yapıştırır.
"""

from __future__ import annotations

import ctypes
import logging
import os
import sys

logger = logging.getLogger(__name__)

VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002


def _user32():
    if sys.platform != "win32":
        raise RuntimeError("Otomatik yapıştırma yalnız Windows'ta çalışır.")
    return ctypes.windll.user32


def foreground_pid() -> int:
    """Etkin pencerenin süreç kimliği."""
    user32 = _user32()
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return 0
    pid = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def send_ctrl_v() -> None:
    """Ctrl+V tuş kombinasyonunu gönderir."""
    user32 = _user32()
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def is_own_window(pid_getter=foreground_pid) -> bool:
    return pid_getter() == os.getpid()


def paste_if_allowed(enabled: bool = True) -> bool:
    """Ayar açıksa veya Dikte penceresi etkinse yapıştırmaz."""
    if not enabled:
        return False
    if is_own_window():
        return False
    try:
        send_ctrl_v()
        return True
    except Exception as exc:
        logger.warning("Otomatik yapıştırma başarısız: %s", exc)
        return False
