"""İkon, Sistem Tepsisi (Tray), Selftest Sesi ve Başlangıç parametreleri testleri."""

import sys
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from dikte import config, tray, uninstall
from dikte import __main__ as main_module
from dikte.tray import SystemTrayManager, create_fallback_icon, load_icon_image


def test_icon_files_exist_and_valid():
    """Üretilen ikon ve ses dosyalarının varlığını ve geçerliliğini doğrular."""
    root = getattr(config, "ROOT_DIR", getattr(config, "ROOT", Path(__file__).resolve().parent.parent))
    ico_path = root / "assets" / "icon.ico"
    installer_ico = root / "installer" / "Dikte.ico"
    png_path = root / "dikte" / "ui" / "assets" / "icon.png"

    assert ico_path.exists(), "assets/icon.ico bulunamadı"
    assert installer_ico.exists(), "installer/Dikte.ico bulunamadı"
    assert png_path.exists(), "dikte/ui/assets/icon.png bulunamadı"

    with Image.open(ico_path) as img:
        assert img.format == "ICO"

    with Image.open(installer_ico) as img:
        assert img.format == "ICO"

    with Image.open(png_path) as img:
        assert img.format == "PNG"
        assert img.size == (256, 256)


def test_selftest_audio_and_text_valid():
    """Selftest için sentetik ses ve beklenen metin dosyasını doğrular."""
    wav_path = config.SELFTEST_WAV
    txt_path = config.SELFTEST_TEXT

    assert wav_path.exists(), "tests/data/test.wav bulunamadı"
    assert txt_path.exists(), "tests/data/test.txt bulunamadı"

    expected_text = txt_path.read_text(encoding="utf-8").strip()
    assert "Dikte test kaydı başarılı." in expected_text

    with wave.open(str(wav_path), "rb") as wf:
        assert wf.getnchannels() == 1  # Mono
        assert wf.getframerate() == 16000  # 16 kHz
        assert wf.getsampwidth() == 2  # 16-bit
        duration = wf.getnframes() / wf.getframerate()
        assert 1.0 <= duration <= 10.0  # 1-10 saniye aralığında


def test_fallback_icon_generation():
    """Yedek ikonun Pillow ile sorunsuz üretildiğini doğrular."""
    fallback = create_fallback_icon()
    assert isinstance(fallback, Image.Image)
    assert fallback.size == (64, 64)
    assert fallback.mode == "RGBA"


def test_load_icon_image_fallback():
    """Var olmayan bir yoldan ikon istendiğinde fallback ikona dönülmeli."""
    img = load_icon_image(Path("gecersiz/yol/yok.png"))
    assert isinstance(img, Image.Image)
    assert img.size == (64, 64)


def test_system_tray_menu_and_toggle():
    """Sistem tepsisi menü elemanlarını ve görünürlük geçişlerini test eder."""
    on_show_mock = MagicMock()
    on_hide_mock = MagicMock()
    on_quit_mock = MagicMock()

    is_vis = [False]

    def check_visible():
        return is_vis[0]

    manager = SystemTrayManager(
        on_show=on_show_mock,
        on_hide=on_hide_mock,
        on_quit=on_quit_mock,
        get_status_text=lambda: "Dinlemeye hazır",
        is_visible_check=check_visible,
    )

    # 1. Başlangıçta gizli -> toggle gösterir
    manager.toggle_visibility()
    assert on_show_mock.call_count == 1
    assert on_hide_mock.call_count == 0

    # 2. Şimdi görünür yap -> toggle gizler
    is_vis[0] = True
    manager.toggle_visibility()
    assert on_hide_mock.call_count == 1

    # 3. Durum metni kontrolü
    assert manager._status_label() == "Durum: Dinlemeye hazır"

    # 4. Çıkış tıklaması
    with patch.object(manager, "stop") as stop_mock:
        manager._on_quit_click()
        stop_mock.assert_called_once()
        on_quit_mock.assert_called_once()


def test_system_tray_start_and_stop():
    """Sistem tepsisinin sahte pystray.Icon ile başlatılıp durdurulmasını test eder."""
    import threading

    fake_icon_instance = MagicMock()
    stop_event = threading.Event()
    fake_icon_instance.stop.side_effect = stop_event.set
    fake_icon_instance.run.side_effect = lambda: stop_event.wait(timeout=2.0)

    with patch("pystray.Icon", return_value=fake_icon_instance):
        manager = SystemTrayManager()
        manager.start()
        assert manager.is_running is True

        # notify testi
        manager.notify("Test Başlık", "Test Mesaj")
        fake_icon_instance.notify.assert_called_with("Test Mesaj", "Test Başlık")

        # stop testi
        manager.stop()
        fake_icon_instance.stop.assert_called_once()
        assert manager.is_running is False


def test_set_app_user_model_id():
    """Windows görev çubuğu kimliği atama fonksiyonunu test eder."""
    # Fonksiyonun bool döndüğünü ve çökmediğini doğrular
    result = main_module.set_app_user_model_id("VoxNoteAI.Dikte.Desktop.Test")
    assert isinstance(result, bool)


def test_main_argparse_tray_flags():
    """--tray ve --minimized bayraklarının argparse tarafından tanındığını doğrular."""
    parser = main_module.build_parser()

    args_tray = parser.parse_args(["--tray"])
    assert args_tray.tray is True
    assert args_tray.minimized is False

    args_min = parser.parse_args(["--minimized"])
    assert args_min.tray is False
    assert args_min.minimized is True


def test_autostart_writes_tray_flag(monkeypatch):
    """set_autostart(True) komutunun sonuna --tray argümanı eklediğini doğrular."""
    class FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class FakeWinreg:
        HKEY_CURRENT_USER = 1
        KEY_SET_VALUE = 2
        KEY_QUERY_VALUE = 1
        REG_SZ = 1

        def __init__(self):
            self.values = {}

        def OpenKey(self, _root, _path, _res, _access):
            return FakeKey()

        def SetValueEx(self, _key, name, _res, _typ, value):
            self.values[name] = value

        def QueryValueEx(self, _key, name):
            if name not in self.values:
                raise OSError(name)
            return self.values[name], 1

    fake = FakeWinreg()
    monkeypatch.setitem(sys.modules, "winreg", fake)

    uninstall.set_autostart(True)
    target = fake.values[config.AUTOSTART_VALUE]
    assert "--tray" in target
    assert target.endswith("--tray")
