"""pywebview köprüsü ve pencere."""

from __future__ import annotations

import logging

from .. import config

logger = logging.getLogger(__name__)


class Api:
    """JavaScript'in çağırabildiği metotlar. Hepsi sözlük döndürür."""

    def __init__(self, controller) -> None:
        self._controller = controller

    def snapshot(self) -> dict:
        return self._controller.snapshot()

    def toggle_record(self) -> dict:
        return self._controller.toggle_record()

    def copy(self, text: str) -> dict:
        return self._controller.copy(text)

    def refresh_last(self) -> dict:
        return self._controller.refresh_last()

    # ---------- geçmiş ----------

    def history_list(self, query: str = "", period: str = "all") -> dict:
        return self._controller.history_list(query, period)

    def history_open(self, record_id: str) -> dict:
        return self._controller.history_open(record_id)

    def history_delete(self, record_id: str) -> dict:
        return self._controller.history_delete(record_id)

    def history_clear(self) -> dict:
        return self._controller.history_clear()

    # ---------- modeller ----------

    def models_list(self) -> dict:
        return self._controller.models_list()

    def model_download(self, name: str) -> dict:
        return self._controller.model_download(name)

    def model_activate(self, name: str) -> dict:
        return self._controller.model_activate(name)

    def model_delete(self, name: str) -> dict:
        return self._controller.model_delete(name)

    # ---------- ayarlar ----------

    def settings_get(self) -> dict:
        return self._controller.settings_get()

    def settings_save(self, payload: dict | None = None) -> dict:
        return self._controller.settings_save(payload)


def run_app(controller=None, debug: bool = False) -> int:
    try:
        import webview
    except Exception as exc:
        print("Arayüz kütüphanesi (pywebview) yüklenemedi.")
        print("Kurulum için: .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        logger.exception("pywebview yüklenemedi")
        return 1

    from ..controller import Controller

    controller = controller or Controller()
    api = Api(controller)

    try:
        window = webview.create_window(
            config.APP_TITLE,
            url=str(config.UI_DIR / "index.html"),
            js_api=api,
            width=config.WINDOW_WIDTH,
            height=config.WINDOW_HEIGHT,
            min_size=(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT),
            background_color=config.WINDOW_BACKGROUND,
            text_select=True,
        )
    except Exception as exc:
        print("Pencere oluşturulamadı.")
        logger.exception("Pencere hatası: %s", exc)
        return 1

    def on_closed() -> None:
        controller.shutdown()

    try:
        window.events.closed += on_closed
    except Exception:
        pass

    controller.start()
    try:
        webview.start(debug=debug)
    except Exception as exc:
        logger.exception("Arayüz başlatılamadı: %s", exc)
        print("Arayüz başlatılamadı. Microsoft Edge WebView2 çalışma zamanının kurulu olduğunu kontrol et.")
        print("İndirme: https://developer.microsoft.com/microsoft-edge/webview2/")
        return 1
    finally:
        controller.shutdown()
    return 0
