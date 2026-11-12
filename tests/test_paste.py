"""Otomatik yapıştırma testleri (gerçek tuş gönderilmez)."""

import os

import pytest

from dikte import paste


def test_is_own_window_compares_pid():
    assert paste.is_own_window(pid_getter=lambda: os.getpid()) is True
    assert paste.is_own_window(pid_getter=lambda: 0) is False


def test_paste_disabled_does_not_send(monkeypatch):
    sent = []
    monkeypatch.setattr(paste, "is_own_window", lambda: False)
    monkeypatch.setattr(paste, "send_ctrl_v", lambda: sent.append(1))
    assert paste.paste_if_allowed(False) is False
    assert sent == []


def test_paste_skipped_in_own_window(monkeypatch):
    sent = []
    monkeypatch.setattr(paste, "is_own_window", lambda: True)
    monkeypatch.setattr(paste, "send_ctrl_v", lambda: sent.append(1))
    assert paste.paste_if_allowed(True) is False
    assert sent == []


def test_paste_sends_in_other_window(monkeypatch):
    sent = []
    monkeypatch.setattr(paste, "is_own_window", lambda: False)
    monkeypatch.setattr(paste, "send_ctrl_v", lambda: sent.append(1))
    assert paste.paste_if_allowed(True) is True
    assert sent == [1]


def test_paste_failure_is_silent(monkeypatch):
    def boom():
        raise RuntimeError("tuş gönderilemedi")

    monkeypatch.setattr(paste, "is_own_window", lambda: False)
    monkeypatch.setattr(paste, "send_ctrl_v", boom)
    assert paste.paste_if_allowed(True) is False


def test_is_own_or_child_pid(monkeypatch):
    my_pid = os.getpid()
    assert paste._is_own_or_child_pid(my_pid) is True

    class FakeChild:
        def __init__(self, pid):
            self.pid = pid

    class FakeProcess:
        def children(self, recursive=True):
            return [FakeChild(999988)]

    import sys
    fake_psutil = type("FakePsutil", (), {"Process": lambda self_pid: FakeProcess()})
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)

    assert paste._is_own_or_child_pid(999988) is True
    assert paste._is_own_or_child_pid(123456) is False


def test_is_own_window_tray_and_taskbar_skip(monkeypatch):
    class FakeUser32:
        def __init__(self, hwnd=1001, class_name="Shell_TrayWnd", pid=999999):
            self._hwnd = hwnd
            self._class_name = class_name
            self._pid = pid

        def GetForegroundWindow(self):
            return self._hwnd

        def GetClassNameW(self, hwnd, buf, max_len):
            buf.value = self._class_name
            return len(self._class_name)

        def GetWindowThreadProcessId(self, hwnd, byref_pid):
            import ctypes
            ctypes.cast(byref_pid, ctypes.POINTER(ctypes.c_ulong)).contents.value = self._pid
            return 1

    # 1. hwnd == 0 -> True (atla)
    monkeypatch.setattr(paste, "_user32", lambda: FakeUser32(hwnd=0))
    assert paste.is_own_window() is True

    # 2. Görev çubuğu / tepsi sınıfları -> True (atla)
    for cls in ("Shell_TrayWnd", "NotifyIconOverflowWindow", "Progman", "WorkerW"):
        monkeypatch.setattr(paste, "_user32", lambda cls=cls: FakeUser32(hwnd=2001, class_name=cls, pid=1234))
        assert paste.is_own_window() is True

    # 3. Kendi sürecimiz -> True (atla)
    my_pid = os.getpid()
    monkeypatch.setattr(paste, "_user32", lambda: FakeUser32(hwnd=3001, class_name="Window", pid=my_pid))
    assert paste.is_own_window() is True

    # 4. Harici uygulama penceresi (Notepad, Word, vb.) -> False (yapıştırmaya izin ver)
    external_pid = my_pid + 99999
    monkeypatch.setattr(paste, "_user32", lambda: FakeUser32(hwnd=4001, class_name="Notepad", pid=external_pid))
    monkeypatch.setattr(paste, "_is_own_or_child_pid", lambda pid: False)
    assert paste.is_own_window() is False


def test_send_key_fallback_to_keybd_event(monkeypatch):
    calls = []

    class MockUser32:
        def MapVirtualKeyW(self, vk, flag):
            return 0x1E

        def SendInput(self, n, p_inp, size):
            calls.append(("SendInput_fail",))
            raise RuntimeError("SendInput unsupported")

        def keybd_event(self, vk, scan, flags, extra):
            calls.append(("keybd_event", vk, flags))

    monkeypatch.setattr(paste, "_user32", lambda: MockUser32())
    paste._send_key(0x11, up=False)
    assert calls == [("SendInput_fail",), ("keybd_event", 0x11, 0)]


def test_send_ctrl_v_sequence_and_modifier_release(monkeypatch):
    events = []
    pasting_during = []

    class MockUser32:
        def GetAsyncKeyState(self, vk):
            # Yalnızca VK_RCONTROL basılı kalsın; VK_MENU basılı değil
            if vk == paste.VK_RCONTROL:
                return 0x8000
            return 0

        def MapVirtualKeyW(self, vk, flag):
            return 0

        def SendInput(self, n, p_inp, size):
            pasting_during.append(paste.is_pasting())
            inp = getattr(p_inp, "_obj", getattr(p_inp, "contents", None))
            if inp is not None:
                events.append((inp.ki.wVk, inp.ki.dwFlags))
            return 1

    monkeypatch.setattr(paste, "_user32", lambda: MockUser32())
    monkeypatch.setattr(paste.time, "sleep", lambda s: None)

    assert paste.is_pasting() is False
    paste.send_ctrl_v()
    assert paste.is_pasting() is False
    assert all(pasting_during), "SendInput sırasında is_pasting() True olmalı"

    # VK_RCONTROL extended key olarak bırakılmalı (KEYEVENTF_KEYUP | KEYEVENTF_EXTENDEDKEY)
    assert (paste.VK_RCONTROL, paste.KEYEVENTF_KEYUP | paste.KEYEVENTF_EXTENDEDKEY) in events

    # Basılı olmayan VK_MENU için keyup GÖNDERİLMEMELİ (menü çubuğu odağını çalmamak için)
    menu_events = [ev for ev in events if ev[0] == paste.VK_MENU]
    assert menu_events == []

    # Ctrl+V basma ve bırakma adımlarının sırasını kontrol et (son 4 olay)
    ctrl_v_events = events[-4:]
    assert ctrl_v_events == [
        (paste.VK_CONTROL, 0),
        (paste.VK_V, 0),
        (paste.VK_V, paste.KEYEVENTF_KEYUP),
        (paste.VK_CONTROL, paste.KEYEVENTF_KEYUP),
    ]


def test_is_own_window_hidden_tray_allows_paste(monkeypatch):
    class MockUser32:
        def GetForegroundWindow(self):
            return 5001

        def GetClassNameW(self, hwnd, buf, max_len):
            buf.value = "Chrome_WidgetWin_1"
            return 18

        def GetWindowThreadProcessId(self, hwnd, byref_pid):
            import ctypes
            ctypes.cast(byref_pid, ctypes.POINTER(ctypes.c_ulong)).contents.value = os.getpid()
            return 1

        def IsWindowVisible(self, hwnd):
            # Pencere sistem tepsisinde gizli
            return 0

    monkeypatch.setattr(paste, "_user32", lambda: MockUser32())
    monkeypatch.setattr(paste, "_is_own_or_child_pid", lambda pid: True)

    # Kendi penceremiz ama tepside gizli (IsWindowVisible=0) -> False dönmeli (yapıştırmaya izin ver)
    assert paste.is_own_window() is False


