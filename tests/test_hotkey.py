"""Kısayol (hotkey) testleri: serbest kombinasyonlar, token eşleme ve dinleyici döngüsü."""

import pytest

from dikte.hotkey import (
    DEFAULT_HOTKEY,
    HOTKEY_CHOICES,
    HotkeyError,
    HotkeyListener,
    format_hotkey_label,
    is_valid_hotkey,
    key_to_tokens,
    normalize_hotkey,
    parse_hotkey,
)


class DummyKey:
    """pynput Key simülasyonu."""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"DummyKey({self.name})"


class DummyKeyCode:
    """pynput KeyCode simülasyonu."""

    def __init__(self, char: str | None = None, vk: int | None = None):
        self.char = char
        self.vk = vk

    def __repr__(self):
        return f"DummyKeyCode(char={self.char}, vk={self.vk})"


def test_hotkey_validation():
    # Eski 7 sabit tuş
    for k in HOTKEY_CHOICES:
        assert is_valid_hotkey(k) is True

    # F tuşları
    assert is_valid_hotkey("f7") is True
    assert is_valid_hotkey("f12") is True

    # 2'li ve 3'lü kombinasyonlar
    assert is_valid_hotkey("ctrl+shift+d") is True
    assert is_valid_hotkey("alt+space") is True
    assert is_valid_hotkey("ctrl+alt+s") is True
    assert is_valid_hotkey("shift+f8") is True

    # Geçersiz durumlar
    assert is_valid_hotkey("") is False
    assert is_valid_hotkey("a") is False  # Tek başına harf reddedilir
    assert is_valid_hotkey("5") is False  # Tek başına rakam reddedilir
    assert is_valid_hotkey("ctrl+shift+alt+d") is False  # 4 tuş fazla
    assert is_valid_hotkey("ctrl+ctrl") is False  # Tekrarlı tuş
    assert is_valid_hotkey("ctrl+bilinmeyen") is False


def test_hotkey_normalization():
    assert normalize_hotkey("shift+ctrl+d") == "ctrl+shift+d"
    assert normalize_hotkey("space+alt") == "alt+space"
    assert normalize_hotkey("right_ctrl") == "right_ctrl"
    assert normalize_hotkey("gecersiz_tus") == DEFAULT_HOTKEY


def test_format_hotkey_label():
    assert format_hotkey_label("right_ctrl") == "Sağ Ctrl"
    assert format_hotkey_label("left_alt") == "Sol Alt"
    assert format_hotkey_label("ctrl+shift+d") == "Ctrl + Shift + D"
    assert format_hotkey_label("alt+space") == "Alt + Space"
    assert format_hotkey_label("shift+f8") == "Shift + F8"


def test_key_to_tokens_special_and_modifiers():
    # Spesifik ve genel modifier'lar
    assert "right_ctrl" in key_to_tokens(DummyKey("ctrl_r"))
    assert "ctrl" in key_to_tokens(DummyKey("ctrl_r"))
    assert "left_ctrl" in key_to_tokens(DummyKey("ctrl_l"))
    assert "alt" in key_to_tokens(DummyKey("alt_r"))
    assert "shift" in key_to_tokens(DummyKey("shift_l"))
    assert "space" in key_to_tokens(DummyKey("space"))
    assert "f8" in key_to_tokens(DummyKey("f8"))


def test_key_to_tokens_vk_and_ctrl_char():
    # Ctrl basılıyken pynput'ta char '\x04' olur ama vk=68 (D tuşu)
    tokens = key_to_tokens(DummyKeyCode(char="\x04", vk=68))
    assert "d" in tokens

    # Rakam 1 (vk=49)
    assert "1" in key_to_tokens(DummyKeyCode(char="1", vk=49))

    # F8 (vk=119)
    assert "f8" in key_to_tokens(DummyKeyCode(vk=119))


def test_hotkey_listener_combo_lifecycle(monkeypatch):
    press_count = 0
    release_count = 0

    def on_press():
        nonlocal press_count
        press_count += 1

    def on_release():
        nonlocal release_count
        release_count += 1

    listener = HotkeyListener(on_press, on_release, key="ctrl+shift+d")

    # Manuel simülasyon için start() içindeki callback'leri yakalayalım
    captured_callbacks = {}

    class FakeListener:
        def __init__(self, on_press, on_release):
            captured_callbacks["on_press"] = on_press
            captured_callbacks["on_release"] = on_release
            self.daemon = True

        def start(self):
            pass

        def stop(self):
            pass

    import sys
    from types import ModuleType

    pynput_mock = ModuleType("pynput")
    keyboard_mock = ModuleType("pynput.keyboard")
    keyboard_mock.Listener = FakeListener
    pynput_mock.keyboard = keyboard_mock
    monkeypatch.setitem(sys.modules, "pynput", pynput_mock)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", keyboard_mock)

    listener.start()
    sim_press = captured_callbacks["on_press"]
    sim_release = captured_callbacks["on_release"]

    k_ctrl = DummyKey("ctrl_l")
    k_shift = DummyKey("shift_l")
    k_d = DummyKeyCode(char="\x04", vk=68)

    # 1. Ctrl'ye basıldı -> henüz tetiklenmemeli
    sim_press(k_ctrl)
    assert press_count == 0

    # 2. Shift'e basıldı -> henüz tetiklenmemeli
    sim_press(k_shift)
    assert press_count == 0

    # 3. D'ye basıldı -> hedef 'ctrl+shift+d' tamamlandı -> tetiklenmeli!
    sim_press(k_d)
    assert press_count == 1
    assert listener._pressed is True

    # 4. D bırakıldı -> hedeften biri eksildi -> release tetiklenmeli!
    sim_release(k_d)
    assert release_count == 1
    assert listener._pressed is False

    # 5. D tekrar basıldı -> tekrar press tetiklenmeli
    sim_press(k_d)
    assert press_count == 2
    assert listener._pressed is True

    # 6. Ctrl bırakıldı -> release tetiklenmeli
    sim_release(k_ctrl)
    assert release_count == 2
    assert listener._pressed is False

    # 7. reset_state testi
    sim_press(k_ctrl)
    sim_press(k_d)  # Shift ve Ctrl basılıydı, D de basıldı -> tekrar press
    assert press_count == 3
    listener.reset_state()
    assert listener._pressed is False
    assert release_count == 3

    listener.stop()
