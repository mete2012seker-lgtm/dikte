"""Global kısayol dinleyicisi (Sağ Ctrl, basılı tut / bırak)."""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)


class HotkeyError(RuntimeError):
    pass


class HotkeyListener:
    def __init__(self, on_press, on_release) -> None:
        self._on_press = on_press
        self._on_release = on_release
        self._listener = None
        self._pressed = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._listener is not None:
            return
        try:
            from pynput import keyboard
        except Exception as exc:
            raise HotkeyError("Klavye dinleyicisi yüklenemedi (pynput).") from exc

        right_ctrl = keyboard.Key.ctrl_r

        def on_press(key) -> None:
            if key == right_ctrl and not self._pressed:
                self._pressed = True
                try:
                    self._on_press()
                except Exception:
                    logger.exception("Kısayol basılma işleyicisi hata verdi")

        def on_release(key) -> None:
            if key == right_ctrl and self._pressed:
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
        logger.info("Kısayol dinleyicisi hazır: Sağ Ctrl")

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
