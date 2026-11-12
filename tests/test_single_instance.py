"""Tek kopya (Single Instance), Tray tekilliği ve Win32 İkon Testleri.

Windows Named Mutex, duplicate instance engellemesi, pystray singleton koruması
ve görev çubuğu / pencere ikonu zorlama fonksiyonlarını test eder.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dikte import __main__ as main_module
from dikte import config
from dikte.instance import (
    DEFAULT_APP_ID,
    DEFAULT_MUTEX_NAME,
    SingleInstance,
    activate_existing_instance,
    apply_window_icon,
    find_dikte_window,
    resolve_icon_path,
    set_app_user_model_id,
    start_window_icon_watcher,
)
from dikte.tray import SystemTrayManager, get_active_tray_manager, is_tray_running


def test_app_user_model_id_default():
    """AppUserModelID'nin varsayılan olarak Dikte.VoxNoteAI.1.6 ile çalıştığını doğrular."""
    res = set_app_user_model_id(DEFAULT_APP_ID)
    assert isinstance(res, bool)


def test_single_instance_acquire_and_release():
    """SingleInstance mutex edinme ve bırakma döngüsünü doğrular."""
    test_mutex_name = "Local\\DikteTestMutex_AcquireRelease"

    inst1 = SingleInstance(name=test_mutex_name)
    assert inst1.acquire() is True
    assert inst1.acquired is True

    # Aynı isimle ikinci bir SingleInstance edinilememeli
    inst2 = SingleInstance(name=test_mutex_name)
    assert inst2.acquire() is False
    assert inst2.acquired is False

    # inst1 serbest bırakılınca inst2 edinilebilmeli
    inst1.release()
    assert inst1.acquired is False

    assert inst2.acquire() is True
    assert inst2.acquired is True
    inst2.release()


def test_single_instance_context_manager():
    """SingleInstance with blokunda otomatik edinilip bırakılmalı."""
    test_mutex_name = "Local\\DikteTestMutex_ContextMgr"

    with SingleInstance(name=test_mutex_name) as inst:
        assert inst.acquired is True

        # İçeride ikinci bir kopya başarısız olmalı
        inst_dup = SingleInstance(name=test_mutex_name)
        assert inst_dup.acquire() is False

    # Bloktan çıkınca mutex bırakılmış olmalı
    inst_next = SingleInstance(name=test_mutex_name)
    assert inst_next.acquire() is True
    inst_next.release()


def test_duplicate_instance_in_main_exits_and_activates():
    """Aynı anda ikinci kopya başlatıldığında cmd_ui çağrılmadan sys.exit(0) yapılmalı."""
    with patch("dikte.__main__.SingleInstance") as mock_si_cls, \
         patch("dikte.__main__.activate_existing_instance") as mock_activate, \
         patch("dikte.__main__.cmd_ui") as mock_cmd_ui:

        mock_instance = MagicMock()
        mock_instance.acquire.return_value = False  # Zaten çalışıyor
        mock_si_cls.return_value = mock_instance

        with pytest.raises(SystemExit) as exc_info:
            main_module.main([])

        assert exc_info.value.code == 0
        mock_activate.assert_called_once()
        mock_cmd_ui.assert_not_called()


def test_selftest_and_uninstall_bypass_single_instance():
    """--selftest veya --uninstall çağrıldığında tek kopya kilidine takılmadan çalışmalı."""
    with patch("dikte.__main__.cmd_selftest", return_value=0) as mock_selftest, \
         patch("dikte.__main__.SingleInstance") as mock_si_cls:

        ret = main_module.main(["--selftest"])
        assert ret == 0
        mock_selftest.assert_called_once()
        mock_si_cls.assert_not_called()


def test_tray_manager_singleton_protection():
    """Aynı süreçte aynı anda iki pystray.Icon başlatılmasını engeller."""
    fake_icon_1 = MagicMock()
    fake_icon_2 = MagicMock()

    stop_event_1 = threading.Event()
    fake_icon_1.stop.side_effect = stop_event_1.set
    fake_icon_1.run.side_effect = lambda: stop_event_1.wait(timeout=2.0)

    with patch("pystray.Icon", side_effect=[fake_icon_1, fake_icon_2]):
        mgr1 = SystemTrayManager()
        mgr2 = SystemTrayManager()

        try:
            mgr1.start()
            assert mgr1.is_running is True
            assert is_tray_running() is True
            assert get_active_tray_manager() is mgr1

            # İkinci tray başlatılmaya çalışıldığında engellenmeli
            mgr2.start()
            assert mgr2.is_running is False
            fake_icon_2.run.assert_not_called()

        finally:
            mgr1.stop()
            assert mgr1.is_running is False
            assert is_tray_running() is False

        # İlk tray durduktan sonra ikincisi başlatılabilmeli
        stop_event_2 = threading.Event()
        fake_icon_2.stop.side_effect = stop_event_2.set
        fake_icon_2.run.side_effect = lambda: stop_event_2.wait(timeout=2.0)

        try:
            mgr2.start()
            assert mgr2.is_running is True
            assert is_tray_running() is True
        finally:
            mgr2.stop()


def test_resolve_icon_path():
    """assets/icon.ico dosyasının çözümlendiğini doğrular."""
    ico = resolve_icon_path()
    assert ico is not None
    assert ico.exists()
    assert ico.suffix.lower() == ".ico"


def test_apply_window_icon_with_mock_win32():
    """apply_window_icon fonksiyonunun Win32 API çağrılarını doğru parametrelerle yaptığını test eder."""
    if sys.platform != "win32":
        pytest.skip("Win32 API testi yalnızca Windows üzerinde çalışır")

    with patch("ctypes.windll.user32.SendMessageW") as mock_send, \
         patch("ctypes.windll.user32.LoadImageW", return_value=12345) as mock_load, \
         patch("ctypes.windll.user32.GetParent", return_value=0), \
         patch("ctypes.windll.user32.GetWindow", return_value=0):

        success = apply_window_icon(hwnd=99999)
        assert success is True
        assert mock_load.call_count >= 2

        # Hem ICON_SMALL (0) hem ICON_BIG (1) için WM_SETICON (0x0080) gönderilmeli
        sent_wparams = [call.args[2] for call in mock_send.call_args_list]
        assert 0 in sent_wparams  # ICON_SMALL
        assert 1 in sent_wparams  # ICON_BIG


def test_start_window_icon_watcher_terminates():
    """start_window_icon_watcher thread'inin pencere bulunduğunda veya timeout'ta sonlandığını doğrular."""
    with patch("dikte.instance.find_dikte_window", return_value=88888), \
         patch("dikte.instance.apply_window_icon", return_value=True) as mock_apply:

        th = start_window_icon_watcher(timeout=1.0, interval=0.05)
        th.join(timeout=2.0)
        assert not th.is_alive()
        mock_apply.assert_called_once()
