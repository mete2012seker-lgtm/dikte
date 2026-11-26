"""Ekranda odak çalmayan küçük 'Dinliyor / Yazıyor' durum göstergesi."""

from __future__ import annotations

import ctypes
import logging
import os
import queue
import sys
import threading

logger = logging.getLogger(__name__)

GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020

STATE_APPEARANCE: dict[str, tuple[str, str]] = {
    "recording": ("Dinliyor...", "#EF4444"),
    "processing": ("Yazıyor...", "#4C9BFF"),
    "cleaning": ("Yazıyor...", "#4C9BFF"),
}


class FloatingIndicator:
    """Windows'ta ekran alt-ortasında odak çalmayan hafif hap göstergesi."""

    def __init__(self, enabled: bool = True, headless: bool | None = None) -> None:
        self._lock = threading.Lock()
        self._enabled = bool(enabled)
        self._state = "loading"
        self._visible = False
        self._text = ""
        self._dot_color = "#4C9BFF"
        self._closed = False
        self._unavailable = False
        if headless is None:
            self._headless = bool(
                os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("DIKTE_HEADLESS")
            )
        else:
            self._headless = bool(headless)
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._thread: threading.Thread | None = None

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    @property
    def visible(self) -> bool:
        with self._lock:
            return self._visible

    @property
    def text(self) -> str:
        with self._lock:
            return self._text

    @property
    def dot_color(self) -> str:
        with self._lock:
            return self._dot_color

    def set_enabled(self, enabled: bool) -> None:
        next_enabled = bool(enabled)
        with self._lock:
            if self._enabled == next_enabled:
                return
            self._enabled = next_enabled
            current_state = self._state
        self.update(current_state)

    def update(self, state: str) -> None:
        """Gösterge durumunu bloklamadan günceller."""
        with self._lock:
            self._state = str(state or "")
            if self._closed or not self._enabled:
                self._visible = False
                self._text = ""
                payload = ("state", False, "", self._dot_color)
            elif self._state in STATE_APPEARANCE:
                text, color = STATE_APPEARANCE[self._state]
                self._visible = True
                self._text = text
                self._dot_color = color
                payload = ("state", True, text, color)
            else:
                self._visible = False
                self._text = ""
                payload = ("state", False, "", self._dot_color)

            should_spawn = (
                not self._headless
                and not self._unavailable
                and not self._closed
                and payload[1]
                and self._thread is None
            )
            if should_spawn:
                self._thread = threading.Thread(
                    target=self._run_loop, name="FloatingIndicator", daemon=True
                )
                self._thread.start()
            has_thread = self._thread is not None and not self._headless and not self._unavailable

        if has_thread:
            try:
                self._queue.put(payload)
            except Exception:
                pass

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._visible = False
            self._text = ""
            thread = self._thread
        if thread is not None:
            try:
                self._queue.put(("quit", False, "", ""))
            except Exception:
                pass
            if thread.is_alive() and thread is not threading.current_thread():
                thread.join(timeout=0.5)

    stop = close

    def _apply_win32_noactivate(self, hwnd: int) -> None:
        if sys.platform != "win32" or not hwnd:
            return
        try:
            user32 = ctypes.windll.user32
            top_hwnd = user32.GetParent(hwnd) or hwnd
            style = user32.GetWindowLongW(top_hwnd, GWL_EXSTYLE)
            new_style = style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST
            user32.SetWindowLongW(top_hwnd, GWL_EXSTYLE, new_style)
            user32.SetWindowPos(
                top_hwnd,
                -1,  # HWND_TOPMOST
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
            )
        except Exception as exc:
            logger.debug("Gösterge Win32 stili uygulanamadı: %s", exc)

    def _run_loop(self) -> None:
        try:
            import tkinter as tk
        except Exception:
            with self._lock:
                self._unavailable = True
            return

        try:
            root = tk.Tk()
        except Exception:
            with self._lock:
                self._unavailable = True
            return

        try:
            width, height = 164, 40
            root.withdraw()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            try:
                root.attributes("-alpha", 0.94)
            except Exception:
                pass
            root.configure(bg="#0F172A")

            canvas = tk.Canvas(
                root,
                width=width,
                height=height,
                bg="#0F172A",
                highlightthickness=1,
                highlightbackground="#334155",
                bd=0,
            )
            canvas.pack(fill="both", expand=True)
            dot_id = canvas.create_oval(16, 14, 28, 26, fill="#EF4444", outline="")
            text_id = canvas.create_text(
                40,
                height // 2,
                text="Dinliyor...",
                anchor="w",
                fill="#F8FAFC",
                font=("Segoe UI", 10, "bold"),
            )

            root.update_idletasks()
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            pos_x = max(0, (screen_w - width) // 2)
            pos_y = max(0, screen_h - height - 72)
            root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
            self._apply_win32_noactivate(root.winfo_id())

            shown = False

            def poll_queue() -> None:
                nonlocal shown
                latest_cmd = None
                while True:
                    try:
                        item = self._queue.get_nowait()
                    except queue.Empty:
                        break
                    latest_cmd = item
                    if item[0] == "quit":
                        try:
                            root.destroy()
                        except Exception:
                            pass
                        return

                if latest_cmd is not None and latest_cmd[0] == "state":
                    _, want_visible, label, color = latest_cmd
                    if want_visible:
                        canvas.itemconfig(dot_id, fill=color)
                        canvas.itemconfig(text_id, text=label)
                        if not shown:
                            root.deiconify()
                            self._apply_win32_noactivate(root.winfo_id())
                            shown = True
                    elif shown:
                        root.withdraw()
                        shown = False

                with self._lock:
                    closed = self._closed
                if closed:
                    try:
                        root.destroy()
                    except Exception:
                        pass
                    return
                root.after(40, poll_queue)

            root.after(10, poll_queue)
            root.mainloop()
        except Exception as exc:
            logger.debug("Gösterge döngüsü sonlandı: %s", exc)
            with self._lock:
                self._unavailable = True
            try:
                root.destroy()
            except Exception:
                pass
