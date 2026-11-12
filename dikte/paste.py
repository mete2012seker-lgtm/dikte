"""Etkin pencereye Ctrl+V gönderir (otomatik yapıştırma).

Dikte'nin kendi penceresi etkinse yapıştırma atlanır. Yönetici pencerelerine
Windows UIPI nedeniyle tuş gitmeyebilir; bu durumda kullanıcı elle yapıştırır.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
import os
import sys
import time

logger = logging.getLogger(__name__)

VK_CONTROL = 0x11
VK_V = 0x56
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_SHIFT = 0x10
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_MENU = 0x12
VK_LMENU = 0xA4
VK_RMENU = 0xA5

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

_is_pasting = False


def is_pasting() -> bool:
    """Ctrl+V yapıştırma işleminin şu an aktif olup olmadığını döner."""
    return _is_pasting


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION),
    ]


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


def _send_key(vk: int, up: bool = False) -> None:
    """SendInput kullanarak tuş basma/bırakma olayı gönderir; başarısız olursa keybd_event'e düşer."""
    user32 = _user32()
    flags = KEYEVENTF_KEYUP if up else 0
    if vk in (VK_RCONTROL, VK_RMENU):
        flags |= KEYEVENTF_EXTENDEDKEY

    try:
        scan = int(user32.MapVirtualKeyW(vk, 0))
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.ki = KEYBDINPUT(
            wVk=vk,
            wScan=scan,
            dwFlags=flags,
            time=0,
            dwExtraInfo=0,
        )
        res = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        if res == 1:
            return
    except Exception as exc:
        logger.debug("SendInput başarısız, keybd_event fallback kullanılıyor: %s", exc)

    try:
        user32.keybd_event(vk, 0, flags, 0)
    except Exception as exc:
        logger.warning("keybd_event başarısız (vk=%s, flags=%s): %s", vk, flags, exc)


def send_ctrl_v() -> None:
    """Ctrl+V tuş kombinasyonunu gönderir.

    Kısayoldan kalan basılı değiştirici tuşları (Ctrl, Shift, Alt) temizler,
    pano IPC oturma payını bekler ve sıralı olarak Ctrl+V basıp bırakır.
    """
    global _is_pasting
    _is_pasting = True
    try:
        user32 = _user32()

        # a) Değiştirici tuşların (Ctrl, Shift, Alt) bırakılmasını bekle (en fazla 200 ms)
        all_modifiers = (
            VK_CONTROL,
            VK_LCONTROL,
            VK_RCONTROL,
            VK_SHIFT,
            VK_LSHIFT,
            VK_RSHIFT,
            VK_MENU,
            VK_LMENU,
            VK_RMENU,
        )
        start_wait = time.time()
        while time.time() - start_wait < 0.200:
            pressed = any(
                bool(user32.GetAsyncKeyState(vk) & 0x8000)
                for vk in all_modifiers
            )
            if not pressed:
                break
            time.sleep(0.015)

        # YALNIZCA hâlâ basılı kalmış olan tuşlar için açıkça KEYEVENTF_KEYUP gönder
        # (Basılı olmayan Alt'a keyup göndermek hedef pencerenin menü çubuğuna odak kaptırabilir!)
        for vk in all_modifiers:
            if bool(user32.GetAsyncKeyState(vk) & 0x8000):
                _send_key(vk, up=True)

        # b) Pano IPC ve klavye durumunun oturması için bekleme (25 ms)
        time.sleep(0.025)

        # c) Ctrl down -> bekle -> V down -> bekle -> V up -> bekle -> Ctrl up
        _send_key(VK_CONTROL, up=False)
        time.sleep(0.015)
        _send_key(VK_V, up=False)
        time.sleep(0.015)
        _send_key(VK_V, up=True)
        time.sleep(0.015)
        _send_key(VK_CONTROL, up=True)
    finally:
        time.sleep(0.020)
        _is_pasting = False


def _is_own_or_child_pid(pid: int) -> bool:
    my_pid = os.getpid()
    if pid == my_pid:
        return True
    try:
        import psutil

        parent = psutil.Process(my_pid)
        for child in parent.children(recursive=True):
            if child.pid == pid:
                return True
    except Exception:
        pass
    return False


def is_own_window(pid_getter=foreground_pid) -> bool:
    """Etkin pencerenin Dikte'ye (veya sistem masaüstü/görev çubuğuna) ait olup olmadığını denetler."""
    # a) Birim testlerinde özel pid_getter geçilmişse geriye dönük uyumluluğu koru
    if pid_getter is not foreground_pid:
        return pid_getter() == os.getpid()

    if sys.platform != "win32":
        return pid_getter() == os.getpid()

    user32 = _user32()

    # Geçici pencere geçişlerinde GetForegroundWindow() 0 dönebilir; 5 kez tekrar dene
    hwnd = 0
    for _ in range(5):
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            break
        time.sleep(0.015)

    if not hwnd:
        return True

    # Masaüstü, görev çubuğu ve tepsi pencerelerine yapıştırma yapılmaz
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    cls_name = buf.value
    if cls_name in ("Shell_TrayWnd", "NotifyIconOverflowWindow", "Progman", "WorkerW"):
        return True

    pid_val = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_val))
    pid = int(pid_val.value)
    if _is_own_or_child_pid(pid):
        # Dikte penceresi ekranda görünürse yapıştırma yapılmaz; tepside gizliyse yapıştırmaya izin ver
        if hasattr(user32, "IsWindowVisible"):
            try:
                return bool(user32.IsWindowVisible(hwnd))
            except Exception:
                pass
        return True

    return False


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
