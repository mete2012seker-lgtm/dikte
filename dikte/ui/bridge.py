"""pywebview köprüsü, sistem tepsisi ve pencere."""

from __future__ import annotations

import logging
import sys

from .. import config

logger = logging.getLogger(__name__)


class Api:
    """JavaScript'in çağırabildiği metotlar. Hepsi sözlük döndürür."""

    def __init__(self, controller, window=None) -> None:
        self._controller = controller
        self._window = window

    def set_window(self, window) -> None:
        self._window = window

    def window_hide_to_tray(self) -> dict:
        if self._window is not None:
            try:
                self._window.hide()
                return {"ok": True}
            except Exception as exc:
                return {"ok": False, "message": str(exc)}
        return {"ok": False, "message": "Pencere referansı yok."}

    def snapshot(self) -> dict:
        return self._controller.snapshot()

    def toggle_record(self) -> dict:
        return self._controller.toggle_record()

    def copy(self, text: str) -> dict:
        return self._controller.copy(text)

    def refresh_last(self) -> dict:
        return self._controller.refresh_last()

    # ---------- yapay zeka ----------

    def clean_text(self, text: str) -> dict:
        return self._controller.clean_text(text)

    def translate_text(self, text: str) -> dict:
        return self._controller.translate_text(text)

    def ai_cancel(self) -> dict:
        return self._controller.ai_cancel()

    def clean_text_async(self, text: str) -> dict:
        return self._controller.clean_text_async(text)

    def translate_text_async(self, text: str) -> dict:
        return self._controller.translate_text_async(text)

    def ai_start_task(self, mode: str, text: str) -> dict:
        return self._controller.ai_start_task(mode, text)

    def ai_state(self) -> dict:
        return self._controller.ai_state()

    def ai_settings_save(self, payload: dict | None = None) -> dict:
        return self._controller.ai_settings_save(payload)

    def openrouter_key_save(self, key: str) -> dict:
        return self._controller.openrouter_key_save(key)

    def openrouter_key_delete(self) -> dict:
        return self._controller.openrouter_key_delete()

    def openrouter_key_test(self) -> dict:
        return self._controller.openrouter_key_test()

    def openrouter_models(
        self, refresh: bool = False, all_models: bool = False, query: str = ""
    ) -> dict:
        return self._controller.openrouter_models(refresh, all_models, query)

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

    def models_cancel_download(self) -> dict:
        return self._controller.models_cancel_download()

    def models_add_custom(self, repo_id: str, label: str = "") -> dict:
        return self._controller.models_add_custom(repo_id, label)

    def models_remove_custom(self, name: str) -> dict:
        return self._controller.models_remove_custom(name)

    def model_activate(self, name: str) -> dict:
        return self._controller.model_activate(name)

    def model_delete(self, name: str) -> dict:
        return self._controller.model_delete(name)

    # ---------- metin modelleri ----------

    def text_model_download(self, name: str) -> dict:
        return self._controller.text_model_download(name)

    def text_model_pause(self, name: str) -> dict:
        return self._controller.text_model_pause(name)

    def text_model_resume(self, name: str) -> dict:
        return self._controller.text_model_resume(name)

    def text_model_cancel(self, name: str) -> dict:
        return self._controller.text_model_cancel(name)

    def text_model_activate(self, name: str) -> dict:
        return self._controller.text_model_activate(name)

    def text_model_delete(self, name: str) -> dict:
        return self._controller.text_model_delete(name)

    def text_model_open_folder(self, name: str = "") -> dict:
        return self._controller.text_model_open_folder(name)

    def text_models_add_custom(
        self, repo_or_url: str, filename: str = "", label: str = ""
    ) -> dict:
        return self._controller.text_models_add_custom(repo_or_url, filename, label)

    def text_models_remove_custom(self, model_id: str) -> dict:
        return self._controller.text_models_remove_custom(model_id)

    # ---------- ayarlar ----------

    def settings_get(self) -> dict:
        return self._controller.settings_get()

    def settings_save(self, payload: dict | None = None) -> dict:
        return self._controller.settings_save(payload)

    # ---------- karşılama sihirbazı ----------

    def wizard_status(self) -> dict:
        return self._controller.wizard_status()

    def wizard_complete(self, payload: dict | None = None) -> dict:
        return self._controller.wizard_complete(payload)

    # ---------- uygulama (otomatik başlatma / kaldırma) ----------

    def uninstall_info(self) -> dict:
        return self._controller.uninstall_info()

    def uninstall(self, payload: dict | None = None) -> dict:
        return self._controller.uninstall(payload)

    def autostart_set(self, enabled: bool) -> dict:
        return self._controller.autostart_set(bool(enabled))

    # ---------- güncelleme & rollback ----------

    def update_check(self, force: bool = False) -> dict:
        return self._controller.update_check(force=bool(force))

    def update_apply(self) -> dict:
        return self._controller.update_apply()

    def update_list_releases(self) -> dict:
        return self._controller.update_list_releases()

    def update_rollback(self, version: str, installer_url: str, sha256: str = "") -> dict:
        return self._controller.update_rollback(version, installer_url, sha256)

    def update_cancel(self) -> dict:
        return self._controller.update_cancel()


def run_ui(controller=None, debug: bool = False, start_in_tray: bool = False) -> int:
    try:
        import webview
    except Exception as exc:
        print("Arayüz kütüphanesi (pywebview) yüklenemedi.")
        print("Kurulum için: .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        logger.exception("pywebview yüklenemedi")
        return 1

    from ..controller import Controller
    from ..tray import SystemTrayManager

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
            hidden=start_in_tray,
        )
    except Exception as exc:
        print("Pencere oluşturulamadı.")
        logger.exception("Pencere hatası: %s", exc)
        return 1

    api.set_window(window)

    _quitting = False
    _window_visible = not start_in_tray

    def is_window_visible() -> bool:
        if sys.platform == "win32":
            try:
                import ctypes
                from ..instance import find_dikte_window

                hwnd = find_dikte_window()
                if hwnd:
                    user32 = ctypes.windll.user32
                    return bool(user32.IsWindowVisible(hwnd))
            except Exception:
                pass
        return _window_visible

    def on_show() -> None:
        nonlocal _window_visible
        _window_visible = True
        try:
            window.show()
            window.restore()
        except Exception:
            pass

    def on_hide() -> None:
        nonlocal _window_visible
        _window_visible = False
        try:
            window.hide()
        except Exception:
            pass

    def toggle_window() -> None:
        nonlocal _window_visible
        if is_window_visible():
            on_hide()
        else:
            on_show()

    def on_quit() -> None:
        nonlocal _quitting
        _quitting = True
        try:
            tray_mgr.stop()
        except Exception:
            pass
        try:
            window.destroy()
        except Exception:
            pass
        controller.shutdown()

    def get_status_text() -> str:
        try:
            snap = controller.snapshot()
            return f"Durum: {snap.get('status', 'Hazır')}"
        except Exception:
            return "Durum: Dinlemeye hazır"

    tray_mgr = SystemTrayManager(
        on_show=on_show,
        on_hide=on_hide,
        on_quit=on_quit,
        get_status_text=get_status_text,
        is_visible_check=is_window_visible,
    )

    def on_closing() -> bool:
        nonlocal _quitting, _window_visible
        if not _quitting:
            _window_visible = False
            try:
                window.hide()
            except Exception:
                pass
            return False
        return True

    def on_closed() -> None:
        nonlocal _quitting
        _quitting = True
        try:
            tray_mgr.stop()
        except Exception:
            pass
        controller.shutdown()

    try:
        window.events.closing += on_closing
    except Exception:
        pass
    try:
        window.events.closed += on_closed
    except Exception:
        pass

    def on_loaded() -> None:
        if start_in_tray:
            on_hide()

    try:
        window.events.loaded += on_loaded
    except Exception:
        pass

    tray_mgr.start()
    controller.start()

    try:
        webview.start(debug=debug)
    except Exception as exc:
        logger.exception("Arayüz başlatılamadı: %s", exc)
        print("Arayüz başlatılamadı. Microsoft Edge WebView2 çalışma zamanının kurulu olduğunu kontrol et.")
        print("İndirme: https://developer.microsoft.com/microsoft-edge/webview2/")
        return 1
    finally:
        _quitting = True
        try:
            tray_mgr.stop()
        except Exception:
            pass
        controller.shutdown()
    return 0


run_app = run_ui
