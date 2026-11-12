"""Global kısayol dinleyicisi: 1-3 tuşlu serbest kombinasyonlar, basılı tut / bırak."""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

# Geriye dönük uyumluluk için eski 7 sabit tuş etiketi
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

# Desteklenen tuş tanımları
MODIFIER_ORDER = {
    "ctrl": 10,
    "left_ctrl": 11,
    "right_ctrl": 12,
    "alt": 20,
    "left_alt": 21,
    "right_alt": 22,
    "shift": 30,
    "left_shift": 31,
    "right_shift": 32,
}

ALL_MODIFIERS = set(MODIFIER_ORDER.keys())

SPECIAL_KEYS = {
    "space": "Space",
    "tab": "Tab",
    "enter": "Enter",
    "caps_lock": "Caps Lock",
    "insert": "Insert",
    "delete": "Delete",
    "home": "Home",
    "end": "End",
    "page_up": "Page Up",
    "page_down": "Page Down",
    **{f"f{i}": f"F{i}" for i in range(1, 13)},
}

TOKEN_LABELS = {
    "ctrl": "Ctrl",
    "left_ctrl": "Sol Ctrl",
    "right_ctrl": "Sağ Ctrl",
    "alt": "Alt",
    "left_alt": "Sol Alt",
    "right_alt": "Sağ Alt",
    "shift": "Shift",
    "left_shift": "Sol Shift",
    "right_shift": "Sağ Shift",
    **SPECIAL_KEYS,
}


class HotkeyError(RuntimeError):
    pass


def parse_hotkey(spec: str) -> list[str]:
    """Kısayol dizgesini ayrıştırır ve token listesi döndürür."""
    if not spec or not isinstance(spec, str):
        return []
    clean = spec.strip().lower()
    if clean in HOTKEY_CHOICES:
        return [clean]
    parts = [p.strip() for p in clean.split("+") if p.strip()]
    return parts


def is_valid_hotkey(value: str) -> bool:
    """1, 2 veya 3 tuşlu kısayol dizgesinin geçerliliğini denetler."""
    if not value or not isinstance(value, str):
        return False
    parts = parse_hotkey(value)
    if not parts or len(parts) > 3:
        return False

    # Tekrar eden tuş olmamalı
    if len(parts) != len(set(parts)):
        return False

    # Tek tuş kuralı: Tek başına harf (a-z) veya rakam (0-9) yazı yazmayı bozacağı için reddedilir.
    if len(parts) == 1:
        tok = parts[0]
        if tok in HOTKEY_CHOICES:
            return True
        if tok in ALL_MODIFIERS or tok in SPECIAL_KEYS:
            return True
        return False

    # 2 veya 3 tuşlu kombinasyon
    for tok in parts:
        if tok in ALL_MODIFIERS or tok in SPECIAL_KEYS:
            continue
        if len(tok) == 1 and (tok.isalpha() or tok.isdigit()):
            continue
        return False
    return True


def normalize_hotkey(value: str) -> str:
    """Kısayol dizgesini standart biçime çevirir (ör. 'shift+ctrl+d' -> 'ctrl+shift+d')."""
    if not is_valid_hotkey(value):
        return DEFAULT_HOTKEY
    parts = parse_hotkey(value)
    if len(parts) == 1:
        return parts[0]

    def sort_key(tok: str) -> tuple[int, str]:
        if tok in MODIFIER_ORDER:
            return (0, f"{MODIFIER_ORDER[tok]:02d}")
        if tok in SPECIAL_KEYS:
            return (1, tok)
        return (2, tok)

    sorted_parts = sorted(parts, key=sort_key)
    return "+".join(sorted_parts)


def format_hotkey_label(value: str) -> str:
    """Arayüzde gösterilecek Türkçe okunaklı etiket üretir."""
    if not is_valid_hotkey(value):
        return HOTKEY_CHOICES.get(DEFAULT_HOTKEY, "Sağ Ctrl")
    parts = parse_hotkey(normalize_hotkey(value))
    if len(parts) == 1 and parts[0] in HOTKEY_CHOICES:
        return HOTKEY_CHOICES[parts[0]]

    labels = []
    for tok in parts:
        if tok in TOKEN_LABELS:
            labels.append(TOKEN_LABELS[tok])
        elif len(tok) == 1 and tok.isalpha():
            labels.append(tok.upper())
        else:
            labels.append(tok)
    return " + ".join(labels)


def key_to_tokens(key) -> set[str]:
    """pynput Key veya KeyCode nesnesinden token kümesi çıkarır."""
    tokens: set[str] = set()
    if key is None:
        return tokens

    # 1. pynput.keyboard.Key veya .name
    name = getattr(key, "name", None)
    if name:
        name_lower = str(name).lower()
        if name_lower in ("ctrl_r", "right_ctrl"):
            tokens.update({"right_ctrl", "ctrl"})
        elif name_lower in ("ctrl_l", "left_ctrl"):
            tokens.update({"left_ctrl", "ctrl"})
        elif name_lower in ("alt_r", "right_alt", "alt_gr"):
            tokens.update({"right_alt", "alt"})
        elif name_lower in ("alt_l", "left_alt"):
            tokens.update({"left_alt", "alt"})
        elif name_lower in ("shift_r", "right_shift"):
            tokens.update({"right_shift", "shift"})
        elif name_lower in ("shift_l", "left_shift", "shift"):
            tokens.update({"left_shift", "shift"})
        elif name_lower in SPECIAL_KEYS:
            tokens.add(name_lower)
        else:
            tokens.add(name_lower)

    # 2. Windows vk (Virtual Key code) — Ctrl basılıyken char kontrol koduna dönüşür!
    vk = getattr(key, "vk", None)
    if vk is not None:
        if 65 <= vk <= 90:  # A-Z
            tokens.add(chr(vk).lower())
        elif 48 <= vk <= 57:  # 0-9
            tokens.add(chr(vk))
        elif 96 <= vk <= 105:  # Numpad 0-9
            tokens.add(str(vk - 96))
        elif 112 <= vk <= 123:  # F1-F12
            tokens.add(f"f{vk - 111}")
        elif vk == 32:
            tokens.add("space")
        elif vk == 9:
            tokens.add("tab")
        elif vk == 13:
            tokens.add("enter")
        elif vk in (162, 163):  # VK_LCONTROL, VK_RCONTROL
            tokens.add("ctrl")
            tokens.add("left_ctrl" if vk == 162 else "right_ctrl")
        elif vk in (164, 165):  # VK_LMENU, VK_RMENU (Alt)
            tokens.add("alt")
            tokens.add("left_alt" if vk == 164 else "right_alt")
        elif vk in (160, 161):  # VK_LSHIFT, VK_RSHIFT
            tokens.add("shift")
            tokens.add("left_shift" if vk == 160 else "right_shift")

    # 3. char (eğer vk yakalamadıysa)
    char = getattr(key, "char", None)
    if char and isinstance(char, str) and len(char) == 1:
        c = char.lower()
        if c.isalnum() and ord(c) < 128:
            tokens.add(c)

    return tokens


class HotkeyListener:
    """1-3 tuşlu global kısayol dinleyicisi."""

    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        key: str = DEFAULT_HOTKEY,
    ) -> None:
        self._on_press = on_press
        self._on_release = on_release
        self._key = normalize_hotkey(key) if is_valid_hotkey(key) else DEFAULT_HOTKEY
        self._target_tokens = set(parse_hotkey(self._key))
        self._listener = None
        self._pressed = False
        self._pressed_keys: dict[object, set[str]] = {}

    @property
    def key(self) -> str:
        return self._key

    def configure(self, key: str) -> None:
        """Dinleyiciyi başlatmadan tuşu ayarlar (açılışta kullanılır)."""
        if not is_valid_hotkey(key):
            raise HotkeyError("Bu tuş kısayol olarak kullanılamaz.")
        self._key = normalize_hotkey(key)
        self._target_tokens = set(parse_hotkey(self._key))

    def set_key(self, key: str) -> None:
        """Tuşu değiştirir; dinleyici çalışıyorsa yeniden başlatır."""
        if not is_valid_hotkey(key):
            raise HotkeyError("Bu tuş kısayol olarak kullanılamaz.")
        normalized = normalize_hotkey(key)
        if normalized == self._key and self._listener is not None:
            return
        was_running = self._listener is not None
        if was_running:
            self.stop()
        previous = self._key
        self._key = normalized
        self._target_tokens = set(parse_hotkey(self._key))
        try:
            self.start()
        except HotkeyError:
            self._key = previous
            self._target_tokens = set(parse_hotkey(self._key))
            if was_running:
                try:
                    self.start()
                except HotkeyError:
                    logger.exception("Eski kısayol geri yüklenemedi")
            raise

    def start(self) -> None:
        if self._listener is not None:
            return
        try:
            from pynput import keyboard
        except Exception as exc:
            raise HotkeyError("Klavye dinleyicisi yüklenemedi (pynput).") from exc

        if not self._target_tokens:
            raise HotkeyError("Seçilen kısayol tuşu geçersiz.")

        def on_press(key) -> None:
            tokens = key_to_tokens(key)
            if not tokens:
                return
            self._pressed_keys[key] = tokens
            active = {tok for toks in self._pressed_keys.values() for tok in toks}
            if self._target_tokens.issubset(active) and not self._pressed:
                self._pressed = True
                try:
                    self._on_press()
                except Exception:
                    logger.exception("Kısayol basılma işleyicisi hata verdi")

        def on_release(key) -> None:
            tokens = self._pressed_keys.pop(key, None)
            if tokens is None:
                to_remove = [k for k in self._pressed_keys if k == key]
                for k in to_remove:
                    self._pressed_keys.pop(k, None)
            active = {tok for toks in self._pressed_keys.values() for tok in toks}
            if self._pressed and not self._target_tokens.issubset(active):
                self._pressed = False
                try:
                    self._on_release()
                except Exception:
                    logger.exception("Kısayol bırakılma işleyicisi hata verdi")

        try:
            self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._listener.daemon = True
            self._listener.start()
        except Exception as exc:
            self._listener = None
            raise HotkeyError(
                "Kısayol dinleyicisi başlatılamadı. Antivirüs engelliyor olabilir."
            ) from exc
        logger.info("Kısayol dinleyicisi hazır: %s", format_hotkey_label(self._key))

    def reset_state(self) -> None:
        """Pencere odak kaybı veya beklenmeyen durumlarda basılı durumunu sıfırlar."""
        self._pressed_keys.clear()
        if self._pressed:
            self._pressed = False
            try:
                self._on_release()
            except Exception:
                logger.exception("Kısayol sıfırlama bırakma hatası")

    def stop(self) -> None:
        listener = self._listener
        self._listener = None
        self.reset_state()
        if listener is None:
            return
        try:
            listener.stop()
        except Exception:
            pass
