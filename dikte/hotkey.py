"""Global kısayol dinleyicisi: basılı tut / bırak."""

from __future__ import annotations

import logging

from .settings import DEFAULT_HOTKEY, HOTKEY_CHOICES

logger = logging.getLogger(__name__)

# Ayar kimliği -> pynput Key özniteliği.
_KEY_ATTRIBUTES = {
    "right_ctrl": "ctrl_r",
    "left_ctrl": "ctrl_l",
    "right_alt": "alt_r",
    "left_alt": "alt_l",
    "f8": "f8",
    "f9": "f9",
    "f10": "f10",
}


class HotkeyError(RuntimeError):
    pass


class HotkeyListener:
    def __init__(self, on_press, on_release, key: str = DEFAULT_HOTKEY) -> None:
        self._on_press = on_press
        self._on_release = on_release
        self._key = key if key in _KEY_ATTRIBUTES else DEFAULT_HOTKEY
        self._listener = None
        self._pressed = False

    @property
    def key(self) -> str:
        return self._key

    def configure(self, key: str) -> None:
        """Dinleyiciyi başlatmadan tuşu ayarlar (açılışta kullanılır)."""
        if key not in _KEY_ATTRIBUTES:
            raise HotkeyError("Bu tuş kısayol olarak kullanılamaz.")
        self._key = key

    def set_key(self, key: str) -> None:
        """Tuşu değiştirir; dinleyici çalışıyorsa yeniden başlatır."""
        if key not in _KEY_ATTRIBUTES:
            raise HotkeyError("Bu tuş kısayol olarak kullanılamaz.")
        if key == self._key and self._listener is not None:
            return
        was_running = self._listener is not None
        if was_running:
            self.stop()
        previous = self._key
        self._key = key
        try:
            self.start()
        except HotkeyError:
            self._key = previous
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

        attribute = _KEY_ATTRIBUTES.get(self._key)
        if attribute is None:
            raise HotkeyError("Bu tuş kısayol olarak kullanılamaz.")
        target = getattr(keyboard.Key, attribute, None)
        if target is None:
            raise HotkeyError("Seçilen kısayol tuşu bu sistemde bulunamadı.")

        def on_press(key) -> None:
            if key == target and not self._pressed:
                self._pressed = True
                try:
                    self._on_press()
                except Exception:
                    logger.exception("Kısayol basılma işleyicisi hata verdi")

        def on_release(key) -> None:
            if key == target and self._pressed:
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
        logger.info("Kısayol dinleyicisi hazır: %s", HOTKEY_CHOICES.get(self._key, self._key))

    def stop(self) -> None:
        listener = self._listener
        self._listener = None
        self._pressed = False
        if listener is None:
            return
        try:
            listener.stop()
        except Exception:
            pass
