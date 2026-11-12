"""Windows tek kopya (single-instance) kilidi, pencere öne getirme ve Win32 ikon yönetimi.

Uygulamanın aynı anda birden fazla açılmasını engeller, ikinci kopyada mevcut
pencereyi öne getirir ve Win32 pencere/görev çubuğu ikonlarını force eder.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from . import config

logger = logging.getLogger(__name__)

DEFAULT_MUTEX_NAME = "Local\\DikteSingleInstanceMutex"
DEFAULT_APP_ID = "Dikte.VoxNoteAI.1.6"

# Win32 sabitleri
ERROR_ALREADY_EXISTS = 183
SW_RESTORE = 9
SW_SHOW = 5
WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040
GW_OWNER = 4


def set_app_user_model_id(app_id: str = DEFAULT_APP_ID) -> bool:
    """Windows görev çubuğunda uygulamanın kendi ikonunun görünmesini sağlar."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        shell32 = ctypes.windll.shell32
        shell32.SetCurrentProcessExplicitAppUserModelID.argtypes = [wintypes.LPCWSTR]
        shell32.SetCurrentProcessExplicitAppUserModelID.restype = ctypes.c_long
        hr = shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        return hr == 0
    except Exception as exc:
        logger.debug("SetCurrentProcessExplicitAppUserModelID hatası: %s", exc)
        return False


class SingleInstance:
    """Windows Named Mutex ile tek kopya çalışma garantisi sağlar."""

    def __init__(self, name: str = DEFAULT_MUTEX_NAME) -> None:
        self.name = name
        self.handle: Optional[int] = None
        self.acquired = False
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """Mutex'i edinir. Zaten başka kopya varsa False döner."""
        with self._lock:
            if self.acquired:
                return True

            if sys.platform != "win32":
                # Windows harici ortamlar (ör. Linux CI) için fallback
                self.acquired = True
                return True

            try:
                import ctypes
                from ctypes import wintypes

                kernel32 = ctypes.windll.kernel32
                kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
                kernel32.CreateMutexW.restype = wintypes.HANDLE
                kernel32.GetLastError.argtypes = []
                kernel32.GetLastError.restype = wintypes.DWORD

                handle = kernel32.CreateMutexW(None, False, self.name)
                last_error = kernel32.GetLastError()

                if not handle or last_error == ERROR_ALREADY_EXISTS:
                    if handle:
                        kernel32.CloseHandle(handle)
                    self.handle = None
                    self.acquired = False
                    return False

                self.handle = handle
                self.acquired = True
                return True
            except Exception as exc:
                logger.warning("SingleInstance mutex oluşturulamadı: %s", exc)
                return False

    def release(self) -> None:
        """Mutex tanıtıcısını serbest bırakır."""
        with self._lock:
            if self.handle and sys.platform == "win32":
                try:
                    import ctypes
                    from ctypes import wintypes

                    kernel32 = ctypes.windll.kernel32
                    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
                    kernel32.CloseHandle.restype = wintypes.BOOL
                    kernel32.CloseHandle(self.handle)
                except Exception as exc:
                    logger.debug("Mutex kapatılırken hata: %s", exc)
                finally:
                    self.handle = None
            self.acquired = False

    def __enter__(self) -> SingleInstance:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    def __del__(self) -> None:
        try:
            self.release()
        except Exception:
            pass


def find_dikte_window() -> Optional[int]:
    """Açık olan Dikte uygulamasının Win32 pencere tanıtıcısını (HWND) bulur."""
    if sys.platform != "win32":
        return None

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        user32.FindWindowW.restype = wintypes.HWND

        # 1. Tam başlık ile ara (config.APP_TITLE: "Dikte — VoxNote AI")
        app_title = getattr(config, "APP_TITLE", "Dikte — VoxNote AI")
        hwnd = user32.FindWindowW(None, app_title)
        if hwnd:
            return hwnd

        # 2. Kısa başlık ile ara ("Dikte")
        hwnd = user32.FindWindowW(None, "Dikte")
        if hwnd:
            return hwnd

        # 3. EnumWindows ile başlığında "Dikte" geçen görünür/ana pencereyi ara
        found_hwnds: list[int] = []

        def _enum_proc(hwnd_cand: int, lparam: int) -> bool:
            length = user32.GetWindowTextLengthW(hwnd_cand)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd_cand, buff, length + 1)
                title = buff.value
                if "Dikte" in title:
                    found_hwnds.append(hwnd_cand)
                    return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(_enum_proc), 0)

        if found_hwnds:
            return found_hwnds[0]

    except Exception as exc:
        logger.debug("find_dikte_window hatası: %s", exc)

    return None


def activate_existing_instance() -> bool:
    """Mevcut açık olan Dikte penceresini restore edip öne getirir."""
    if sys.platform != "win32":
        return False

    hwnd = find_dikte_window()
    if not hwnd:
        logger.debug("Öne getirilecek Dikte penceresi bulunamadı.")
        return False

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL
        user32.BringWindowToTop.argtypes = [wintypes.HWND]
        user32.BringWindowToTop.restype = wintypes.BOOL

        # Küçültülmüşse (minimize) SW_RESTORE, gizliyse veya normaldeyse SW_SHOW
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        else:
            user32.ShowWindow(hwnd, SW_SHOW)

        # Foreground kilidini aşmak için AttachThreadInput desteği
        try:
            fore_hwnd = user32.GetForegroundWindow()
            fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
            cur_thread = ctypes.windll.kernel32.GetCurrentThreadId()
            if fore_thread and fore_thread != cur_thread:
                user32.AttachThreadInput(cur_thread, fore_thread, True)
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.AttachThreadInput(cur_thread, fore_thread, False)
            else:
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
        except Exception:
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)

        logger.info("Mevcut Dikte penceresi öne getirildi (HWND: %s).", hwnd)
        return True
    except Exception as exc:
        logger.warning("Pencere öne getirilirken hata: %s", exc)
        return False


def resolve_icon_path(icon_path: Path | str | None = None) -> Optional[Path]:
    """assets/icon.ico veya yedek .ico dosyası yolunu döner."""
    if icon_path:
        cand = Path(icon_path).resolve()
        if cand.is_file():
            return cand

    root = getattr(config, "ROOT_DIR", getattr(config, "ROOT", Path(__file__).resolve().parent.parent))
    candidates = [
        root / "assets" / "icon.ico",
        root / "installer" / "Dikte.ico",
        Path(__file__).resolve().parent.parent / "assets" / "icon.ico",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def apply_window_icon(hwnd: Optional[int] = None, icon_path: Path | str | None = None) -> bool:
    """Win32 SendMessageW ile pencere ve görev çubuğu ikonunu assets/icon.ico olarak zorlar."""
    if sys.platform != "win32":
        return False

    if hwnd is None:
        hwnd = find_dikte_window()
    if not hwnd:
        return False

    resolved_path = resolve_icon_path(icon_path)
    if not resolved_path:
        logger.debug("İkon dosyası (.ico) bulunamadı.")
        return False

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        user32.LoadImageW.argtypes = [
            wintypes.HINSTANCE,
            wintypes.LPCWSTR,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.LoadImageW.restype = wintypes.HANDLE

        user32.SendMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.SendMessageW.restype = wintypes.LPARAM

        user32.GetParent.argtypes = [wintypes.HWND]
        user32.GetParent.restype = wintypes.HWND

        user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetWindow.restype = wintypes.HWND

        path_str = str(resolved_path)

        # 16x16 küçük ikon (başlık çubuğu)
        cx_sm = user32.GetSystemMetrics(49) or 16
        cy_sm = user32.GetSystemMetrics(50) or 16
        hicon_sm = user32.LoadImageW(None, path_str, IMAGE_ICON, cx_sm, cy_sm, LR_LOADFROMFILE)
        if not hicon_sm:
            hicon_sm = user32.LoadImageW(None, path_str, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)

        # 32x32 büyük ikon (Alt+Tab ve görev çubuğu)
        cx_lg = user32.GetSystemMetrics(11) or 32
        cy_lg = user32.GetSystemMetrics(12) or 32
        hicon_lg = user32.LoadImageW(None, path_str, IMAGE_ICON, cx_lg, cy_lg, LR_LOADFROMFILE)
        if not hicon_lg:
            hicon_lg = user32.LoadImageW(None, path_str, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)

        if not hicon_sm and not hicon_lg:
            logger.debug("LoadImageW ile ikon yüklenemedi: %s", path_str)
            return False

        targets = [hwnd]
        parent = user32.GetParent(hwnd)
        if parent and parent not in targets:
            targets.append(parent)
        owner = user32.GetWindow(hwnd, GW_OWNER)
        if owner and owner not in targets:
            targets.append(owner)

        applied = False
        for target in targets:
            if target:
                if hicon_sm:
                    user32.SendMessageW(target, WM_SETICON, ICON_SMALL, hicon_sm)
                    applied = True
                if hicon_lg:
                    user32.SendMessageW(target, WM_SETICON, ICON_BIG, hicon_lg)
                    applied = True

        if applied:
            logger.debug("Win32 pencere ikonu uygulandı (HWND: %s, targets: %s)", hwnd, targets)
        return applied
    except Exception as exc:
        logger.warning("apply_window_icon hatası: %s", exc)
        return False


def start_window_icon_watcher(
    timeout: float = 10.0,
    interval: float = 0.25,
    icon_path: Path | str | None = None,
    daemon: bool = True,
) -> threading.Thread:
    """Pencere oluşturulana kadar periyodik olarak arayıp ikonu uygulayan thread başlatır."""

    def _watcher() -> None:
        start_time = time.time()
        while time.time() - start_time < timeout:
            hwnd = find_dikte_window()
            if hwnd:
                if apply_window_icon(hwnd, icon_path):
                    break
            time.sleep(interval)

    thread = threading.Thread(target=_watcher, name="WindowIconWatcherThread", daemon=daemon)
    thread.start()
    return thread
