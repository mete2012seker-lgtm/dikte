"""Windows sistem tepsisi (system tray) yöneticisi.

pystray ve Pillow kullanarak görev çubuğu tepsisinde simge, bildirim ve menü sağlar.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import Menu, MenuItem
except ImportError:  # pragma: no cover
    pystray = None
    Menu = None
    MenuItem = None

from . import config

logger = logging.getLogger(__name__)

# Aynı süreçte asla birden fazla pystray.Icon çalıştırılmaması için singleton kilit ve referans
_tray_lock = threading.Lock()
_active_tray_manager: Optional[SystemTrayManager] = None


def get_active_tray_manager() -> Optional[SystemTrayManager]:
    """Süreç içindeki aktif sistem tepsisi yöneticisini döner."""
    with _tray_lock:
        return _active_tray_manager


def is_tray_running() -> bool:
    """Süreçte çalışan bir sistem tepsisi ikonu olup olmadığını döner."""
    with _tray_lock:
        return _active_tray_manager is not None and _active_tray_manager.is_running


def create_fallback_icon() -> Image.Image:
    """İkon dosyası bulunamazsa koyu arka plan üzerinde mavi ses dalgalı yedek ikon üretir."""
    size = (64, 64)
    image = Image.new("RGBA", size, color=(16, 24, 40, 255))
    draw = ImageDraw.Draw(image)
    wave_heights = [12, 24, 38, 48, 38, 24, 12]
    start_x = 10
    step_x = 7
    center_y = 32
    for i, h in enumerate(wave_heights):
        x = start_x + i * step_x
        draw.line(
            [(x, center_y - h // 2), (x, center_y + h // 2)],
            fill=(61, 91, 245, 255),
            width=3,
        )
    return image


def load_icon_image(icon_path: Path | str | None = None) -> Image.Image:
    """Tepsi ikonunu belirtilen yoldan veya varsayılan dosyalardan yükler."""
    if icon_path:
        cand = Path(icon_path)
        try:
            if cand.is_file():
                return Image.open(cand)
        except Exception as exc:
            logger.debug("İkon dosyası açılamadı (%s): %s", cand, exc)
        return create_fallback_icon()

    root = getattr(config, "ROOT_DIR", getattr(config, "ROOT", Path(__file__).resolve().parent.parent))
    candidates = [
        root / "dikte" / "ui" / "assets" / "icon.png",
        root / "assets" / "icon.ico",
        root / "installer" / "Dikte.ico",
        Path(__file__).parent / "ui" / "assets" / "icon.png",
    ]

    for cand in candidates:
        try:
            if cand.is_file():
                return Image.open(cand)
        except Exception as exc:
            logger.debug("İkon dosyası açılamadı (%s): %s", cand, exc)

    return create_fallback_icon()


class SystemTrayManager:
    """Sistem tepsisi (System Tray) ikonu ve menü denetleyicisi."""

    def __init__(
        self,
        on_show: Optional[Callable[[], None]] = None,
        on_hide: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
        get_status_text: Optional[Callable[[], str]] = None,
        icon_path: Optional[Path | str] = None,
        is_visible_check: Optional[Callable[[], bool]] = None,
    ) -> None:
        self.on_show = on_show or (lambda: None)
        self.on_hide = on_hide or (lambda: None)
        self.on_quit = on_quit or (lambda: None)
        self.get_status_text = get_status_text or (lambda: "Durum: Dinlemeye hazır")
        self.is_visible_check = is_visible_check
        self.icon_path = icon_path

        self._image = load_icon_image(icon_path)
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._window_visible_fallback = True

    @property
    def is_running(self) -> bool:
        return self._is_running

    def toggle_visibility(self) -> None:
        """Pencere görünürse gizler, gizliyse gösterir."""
        if self.is_visible_check is not None:
            try:
                visible = bool(self.is_visible_check())
            except Exception as exc:
                logger.debug("is_visible_check hatası: %s", exc)
                visible = self._window_visible_fallback
        else:
            visible = self._window_visible_fallback

        if visible:
            self._window_visible_fallback = False
            try:
                self.on_hide()
            except Exception as exc:
                logger.warning("on_hide çağrısında hata: %s", exc)
        else:
            self._window_visible_fallback = True
            try:
                self.on_show()
            except Exception as exc:
                logger.warning("on_show çağrısında hata: %s", exc)

    def _on_toggle_click(self, icon=None, item=None) -> None:
        self.toggle_visibility()

    def _on_quit_click(self, icon=None, item=None) -> None:
        self.stop()
        try:
            self.on_quit()
        except Exception as exc:
            logger.warning("on_quit çağrısında hata: %s", exc)

    def _status_label(self, item=None) -> str:
        try:
            txt = self.get_status_text()
            if not txt.startswith("Durum:"):
                return f"Durum: {txt}"
            return txt
        except Exception as exc:
            logger.debug("get_status_text hatası: %s", exc)
            return "Durum: Dinlemeye hazır"

    def _create_menu(self) -> Menu:
        if Menu is None or MenuItem is None:
            return None
        return Menu(
            MenuItem(
                "Göster / Gizle",
                self._on_toggle_click,
                default=True,
            ),
            MenuItem(
                self._status_label,
                None,
                enabled=False,
            ),
            MenuItem(
                "Çıkış",
                self._on_quit_click,
            ),
        )

    def start(self) -> None:
        """Tepsi ikonunu arka plan daemon thread'inde başlatır (singleton garantili)."""
        global _active_tray_manager
        with _tray_lock:
            if self._is_running:
                return

            if _active_tray_manager is not None and _active_tray_manager is not self:
                if _active_tray_manager.is_running:
                    logger.warning(
                        "Aktif bir sistem tepsisi yöneticisi zaten çalışıyor. İkinci bir pystray.Icon başlatılmayacak."
                    )
                    return

            if pystray is None:
                logger.warning("pystray kurulu değil, sistem tepsisi devre dışı")
                return

            menu = self._create_menu()
            try:
                self._icon = pystray.Icon(
                    name="Dikte",
                    icon=self._image,
                    title="Dikte",
                    menu=menu,
                )
            except Exception as exc:
                logger.exception("pystray.Icon oluşturulamadı: %s", exc)
                return

            _active_tray_manager = self
            self._is_running = True

            def _runner() -> None:
                try:
                    self._icon.run()
                except Exception as exc:
                    logger.warning("Sistem tepsisi çalışma hatası: %s", exc)
                finally:
                    self._is_running = False
                    with _tray_lock:
                        global _active_tray_manager
                        if _active_tray_manager is self:
                            _active_tray_manager = None

            self._thread = threading.Thread(
                target=_runner, name="SystemTrayThread", daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        """Tepsi ikonunu güvenli şekilde durdurur."""
        global _active_tray_manager
        with _tray_lock:
            self._is_running = False
            if self._icon is not None:
                try:
                    self._icon.stop()
                except Exception as exc:
                    logger.debug("pystray durdurulurken hata: %s", exc)
                self._icon = None
            if _active_tray_manager is self:
                _active_tray_manager = None

    def update_icon(self, image: Image.Image) -> None:
        """Tepsi simgesini günceller."""
        self._image = image
        if self._icon is not None:
            try:
                self._icon.icon = image
            except Exception as exc:
                logger.debug("İkon güncelleme hatası: %s", exc)

    def notify(self, title: str, message: str) -> None:
        """Masaüstü bildirimi gönderir."""
        if self._icon is not None and hasattr(self._icon, "notify"):
            try:
                self._icon.notify(message, title)
            except Exception as exc:
                logger.debug("Bildirim gönderme hatası: %s", exc)
