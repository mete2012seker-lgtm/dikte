"""Global kısayol dinleyicisi: 1-3 tuşlu serbest kombinasyonlar, basılı tut / bırak."""

from __future__ import annotations

import ctypes
import logging
import sys
import threading
from collections import deque
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
HOTKEY_MODES = ("hold", "toggle")

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
    vk = getattr(key, "vk", None) or getattr(getattr(key, "value", None), "vk", None)
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


_PASTE_RELATED_TOKENS = frozenset({
    "v",
    "ctrl",
    "left_ctrl",
    "right_ctrl",
    "shift",
    "left_shift",
    "right_shift",
    "alt",
    "left_alt",
    "right_alt",
})


def _is_pasting() -> bool:
    try:
        from .paste import is_pasting

        return bool(is_pasting())
    except Exception:
        return False


def _is_vk_physically_down(vk: int) -> bool | None:
    """Windows'ta sanal tuşun fiziksel olarak basılı olup olmadığını döner."""
    if sys.platform != "win32":
        return None
    try:
        state = ctypes.windll.user32.GetAsyncKeyState(int(vk))
        return bool(state & 0x8000)
    except Exception:
        return None


def _canonical_key_id(key) -> tuple:
    """pynput Key/KeyCode nesnesi için modifier+char değişiminden etkilenmeyen kimlik üretir."""
    if key is None:
        return ("none", None)
    vk = getattr(key, "vk", None) or getattr(getattr(key, "value", None), "vk", None)
    name = getattr(key, "name", None)
    if name is not None:
        name = str(name).lower()
    if vk is not None or name is not None:
        return ("key", vk, name)
    char = getattr(key, "char", None)
    if char is not None:
        return ("char", str(char).lower())
    return ("obj", repr(key))


class HotkeyListener:
    """1-3 tuşlu global kısayol dinleyicisi."""

    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        key: str = DEFAULT_HOTKEY,
        mode: str = "hold",
    ) -> None:
        self._on_press = on_press
        self._on_release = on_release
        self._key = normalize_hotkey(key) if is_valid_hotkey(key) else DEFAULT_HOTKEY
        self._mode = mode if mode in HOTKEY_MODES else "hold"
        self._target_tokens = set(parse_hotkey(self._key))
        self._listener = None
        self._pressed = False
        self._toggle_active = False
        self._keys_lock = threading.Lock()
        self._lifecycle_lock = threading.RLock()
        self._pressed_keys: dict[tuple, set[str]] = {}
        self._event_cond = threading.Condition()
        self._event_queue: deque[str | None] = deque()
        self._worker_thread: threading.Thread | None = None
        self._worker_running = False

    @property
    def key(self) -> str:
        return self._key

    @property
    def mode(self) -> str:
        with self._keys_lock:
            return self._mode

    def set_mode(self, mode: str) -> None:
        """Kısayol modunu değiştirir ('hold' veya 'toggle')."""
        if mode not in HOTKEY_MODES:
            raise HotkeyError("Geçersiz kısayol modu.")
        with self._keys_lock:
            self._mode = mode
            self._toggle_active = False

    def sync_toggle_state(self, active: bool) -> None:
        """Toggle durumunu denetleyicinin gerçek kayıt durumuyla eşler."""
        with self._keys_lock:
            self._toggle_active = bool(active)

    def _enqueue_event(self, event: str) -> None:
        with self._event_cond:
            self._event_queue.append(event)
            self._event_cond.notify()

    def _event_worker(self) -> None:
        while True:
            with self._event_cond:
                while not self._event_queue and self._worker_running:
                    self._event_cond.wait(timeout=0.5)
                if not self._event_queue and not self._worker_running:
                    break
                event = self._event_queue.popleft()
            if event is None:
                break
            if event == "press":
                try:
                    self._on_press()
                except Exception:
                    logger.exception("Kısayol basılma işleyicisi hata verdi")
            elif event == "release":
                try:
                    self._on_release()
                except Exception:
                    logger.exception("Kısayol bırakılma işleyicisi hata verdi")

    def configure(self, key: str, mode: str | None = None) -> None:
        """Dinleyiciyi başlatmadan tuşu (ve istenirse modu) ayarlar (açılışta kullanılır)."""
        if not is_valid_hotkey(key):
            raise HotkeyError("Bu tuş kısayol olarak kullanılamaz.")
        if mode is not None and mode not in HOTKEY_MODES:
            raise HotkeyError("Geçersiz kısayol modu.")
        with self._lifecycle_lock:
            self._key = normalize_hotkey(key)
            self._target_tokens = set(parse_hotkey(self._key))
            if mode is not None:
                with self._keys_lock:
                    self._mode = mode
                    self._toggle_active = False

    def set_key(self, key: str) -> None:
        """Tuşu değiştirir; dinleyici çalışıyorsa yeniden başlatır."""
        if not is_valid_hotkey(key):
            raise HotkeyError("Bu tuş kısayol olarak kullanılamaz.")
        normalized = normalize_hotkey(key)
        with self._lifecycle_lock:
            if normalized == self._key and self._listener is not None:
                return
            was_running = self._listener is not None
            if was_running:
                self.stop()
            with self._keys_lock:
                previous = self._key
                self._key = normalized
                self._target_tokens = set(parse_hotkey(self._key))
            try:
                if was_running:
                    self.start()
            except HotkeyError:
                with self._keys_lock:
                    self._key = previous
                    self._target_tokens = set(parse_hotkey(self._key))
                if was_running:
                    try:
                        self.start()
                    except HotkeyError:
                        logger.exception("Eski kısayol geri yüklenemedi")
                raise

    def start(self) -> None:
        with self._lifecycle_lock:
            if self._listener is not None:
                return
            try:
                from pynput import keyboard
            except Exception as exc:
                raise HotkeyError("Klavye dinleyicisi yüklenemedi (pynput).") from exc

            if not self._target_tokens:
                raise HotkeyError("Seçilen kısayol tuşu geçersiz.")

            with self._keys_lock:
                self._pressed_keys.clear()
                self._pressed = False
                self._toggle_active = False

            with self._event_cond:
                self._event_queue.clear()
                self._worker_running = True
            self._worker_thread = threading.Thread(
                target=self._event_worker, name="HotkeyEventWorker", daemon=True
            )
            self._worker_thread.start()

            def on_press(key) -> None:
                tokens = key_to_tokens(key)
                if not tokens:
                    return
                if _is_pasting() and (tokens & _PASTE_RELATED_TOKENS):
                    return

                key_id = _canonical_key_id(key)
                should_reset = False
                with self._keys_lock:
                    for existing_id in list(self._pressed_keys.keys()):
                        if existing_id[0] == "key" and isinstance(existing_id[1], int):
                            if _is_vk_physically_down(existing_id[1]) is False:
                                self._pressed_keys.pop(existing_id, None)
                    if self._pressed:
                        active_before = {tok for toks in self._pressed_keys.values() for tok in toks}
                        if not self._target_tokens.issubset(active_before):
                            should_reset = True

                if should_reset:
                    self.reset_state()

                event_to_send = None
                with self._keys_lock:
                    self._pressed_keys[key_id] = tokens
                    active = {tok for toks in self._pressed_keys.values() for tok in toks}
                    if self._target_tokens.issubset(active) and not self._pressed:
                        self._pressed = True
                        if self._mode == "toggle":
                            self._toggle_active = not self._toggle_active
                            event_to_send = "press" if self._toggle_active else "release"
                        else:
                            event_to_send = "press"

                if event_to_send:
                    self._enqueue_event(event_to_send)

            def on_release(key) -> None:
                tokens = key_to_tokens(key)
                key_id = _canonical_key_id(key)
                should_release = False
                with self._keys_lock:
                    in_pressed = key_id in self._pressed_keys or (
                        bool(tokens) and any(toks == tokens for toks in self._pressed_keys.values())
                    )
                    if _is_pasting() and tokens and (tokens & _PASTE_RELATED_TOKENS) and not in_pressed:
                        return
                    removed = self._pressed_keys.pop(key_id, None)
                    if removed is None and tokens:
                        to_remove = [k for k, toks in self._pressed_keys.items() if toks == tokens]
                        for k in to_remove:
                            self._pressed_keys.pop(k, None)
                    active = {tok for toks in self._pressed_keys.values() for tok in toks}
                    if self._pressed and not self._target_tokens.issubset(active):
                        self._pressed = False
                        if self._mode != "toggle":
                            should_release = True

                if should_release:
                    self._enqueue_event("release")

            try:
                self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
                self._listener.daemon = True
                self._listener.start()
            except Exception as exc:
                self._listener = None
                self._stop_worker()
                raise HotkeyError(
                    "Kısayol dinleyicisi başlatılamadı. Antivirüs engelliyor olabilir."
                ) from exc
            logger.info("Kısayol dinleyicisi hazır: %s", format_hotkey_label(self._key))

    def _stop_worker(self) -> None:
        with self._event_cond:
            self._worker_running = False
            self._event_queue.append(None)
            self._event_cond.notify_all()
        worker = self._worker_thread
        self._worker_thread = None
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=1.0)

    def reset_state(self) -> None:
        """Pencere odak kaybı veya beklenmeyen durumlarda basılı durumunu sıfırlar."""
        should_release = False
        with self._keys_lock:
            self._pressed_keys.clear()
            if self._pressed:
                self._pressed = False
                if self._mode != "toggle":
                    should_release = True

        if should_release:
            if self._worker_running:
                self._enqueue_event("release")
            else:
                try:
                    self._on_release()
                except Exception:
                    logger.exception("Kısayol sıfırlama bırakma hatası")

    def stop(self) -> None:
        with self._lifecycle_lock:
            listener = self._listener
            self._listener = None
            if listener is not None:
                try:
                    listener.stop()
                except Exception:
                    pass
            with self._keys_lock:
                self._toggle_active = False
            self.reset_state()
            self._stop_worker()
