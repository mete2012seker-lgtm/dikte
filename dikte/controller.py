"""Uygulamanın beyni: durum, kayıt, çeviri, pano, geçmiş, modeller ve ayarlar."""

from __future__ import annotations

import logging
import os
import shutil
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from . import config, diagnostics, openrouter, text_engine, uninstall, updater
from .audio import AudioError, AudioRecorder, Recording
from .clipboard import ClipboardError
from .engine import EngineError, TranscriptionEngine
from .history import HistoryError, HistoryStore
from .hotkey import HotkeyError, HotkeyListener
from .instance import (
    DEFAULT_APP_ID,
    apply_window_icon,
    set_app_user_model_id,
    start_window_icon_watcher,
)
from .models import ModelError, ModelManager, get_model
from .paste import paste_if_allowed
from .secrets import SecretError, SecretStore, mask as mask_key
from . import text_models
from .text_models import LocalTextModel
from .settings import (
    AUTO_MODEL,
    DEFAULT_HOTKEY,
    HOTKEY_CHOICES,
    SettingsError,
    SettingsStore,
    hotkey_label,
    output_language_label,
    text_provider_label,
)
from .state import (
    ALLOWED,
    CLEANING,
    ERROR,
    LOADING,
    PROCESSING,
    READY,
    RECORDING,
    STATE_LABELS,
    InvalidTransition,
    StateMachine,
)

logger = logging.getLogger(__name__)


def _default_beep(kind: str) -> None:
    """Kısa başlangıç/bitiş tonu. Ses çalınamazsa uygulama etkilenmez."""
    try:
        import winsound

        winsound.Beep(880 if kind == "start" else 620, 80)
    except Exception:
        pass


def format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    if seconds >= 60:
        return f"{seconds // 60} dk {seconds % 60:02d} sn"
    return f"{seconds} sn"


class Controller:
    """Arayüz ve kısayol aynı yolu kullanır; tüm geçişler kilitlidir."""

    def __init__(
        self,
        engine=None,
        recorder=None,
        hotkey=None,
        clipper=None,
        beeper=None,
        memory_provider=None,
        load_in_background: bool = True,
        settings_store=None,
        history_store=None,
        model_manager=None,
        last_recording_path: Path | None = None,
        secret_store=None,
        text_processor=None,
        model_lister=None,
        text_downloader=None,
        paster=None,
    ) -> None:
        self.engine = engine if engine is not None else TranscriptionEngine()
        self.recorder = recorder if recorder is not None else AudioRecorder()
        self.settings = settings_store if settings_store is not None else SettingsStore()
        self.history = history_store if history_store is not None else HistoryStore()
        self.models = model_manager if model_manager is not None else ModelManager()
        self.secrets = secret_store if secret_store is not None else SecretStore()
        self._text_processor = text_processor or text_engine.generate
        self._model_lister = model_lister or openrouter.list_models
        self._text_downloader = text_downloader or text_models.Downloader()
        self._paster = paster or paste_if_allowed
        self.hotkey = (
            hotkey
            if hotkey is not None
            else HotkeyListener(self.on_hotkey_press, self.on_hotkey_release)
        )
        self._clipper = clipper if clipper is not None else self._default_clipper
        self._beeper = beeper if beeper is not None else _default_beep
        self._memory_provider = memory_provider or diagnostics.read_memory
        self._load_in_background = load_in_background
        self._last_recording_path = Path(last_recording_path or config.LAST_RECORDING)

        set_app_user_model_id(DEFAULT_APP_ID)

        self._machine = StateMachine(LOADING)
        self._lock = threading.RLock()
        self._engine_lock = threading.RLock()
        self._info = None
        self._error: str | None = None
        self._activity: deque[dict] = deque(maxlen=7)
        self._seq = 0
        self._refresh_seq = 0
        self._last_history_id: str | None = None
        self._latest = ""
        self._replace_last = False
        self._worker: threading.Thread | None = None
        self._hotkey_events: deque[str] = deque()
        self._hotkey_thread: threading.Thread | None = None
        self._closed = False
        self._memory_cache: tuple[float, dict | None] = (0.0, None)
        self._gpu_warning_shown = False
        self._models_cache: tuple[float, dict | None] = (0.0, None)
        self._download: dict | None = None
        self._download_thread: threading.Thread | None = None
        self._text_download: dict | None = None
        self._text_download_thread: threading.Thread | None = None
        self._text_download_token = 0
        self._text_pause = threading.Event()
        self._text_cancel = threading.Event()
        self._text_runtime = LocalTextModel()
        self._whisper_loaded = False
        self._last_ai_copy_ok = True
        self._last_recording: Path | None = None
        self._startup_notes: list[tuple[str, str, str]] = []
        self._key_cache: tuple[bool, str | None] | None = None
        self._ai_cancel_event = threading.Event()
        self._ai_worker: threading.Thread | None = None
        self._update_cancel_event = threading.Event()

        self._save_history = bool(self.settings.get("save_history", True))
        self._hotkey_id = str(self.settings.get("hotkey", DEFAULT_HOTKEY))
        self._prepare_model_choice()
        self._prepare_hotkey()
        self._prepare_ai_model()
        self._remove_last_recording()

    # ---------- kurulum ----------

    def _prepare_model_choice(self) -> None:
        active = str(self.settings.get("active_model", AUTO_MODEL))
        if active == AUTO_MODEL:
            return
        try:
            exists = self.models.installed(active)
        except Exception:
            exists = False
        if exists:
            if hasattr(self.engine, "set_model"):
                self.engine.set_model(active)
            return
        self._startup_notes.append(
            (
                "Seçili model bulunamadı",
                f"{active} diskte yok; otomatik seçime dönüldü.",
                "warn",
            )
        )
        try:
            self.settings.save(active_model=AUTO_MODEL)
        except Exception:
            logger.warning("Ayar dosyası güncellenemedi", exc_info=True)

    def _prepare_hotkey(self) -> None:
        configure = getattr(self.hotkey, "configure", None)
        if configure is None:
            return
        try:
            configure(self._hotkey_id)
        except Exception as exc:
            logger.warning("Kısayol ayarı uygulanamadı: %s", exc)
            self._hotkey_id = DEFAULT_HOTKEY
            try:
                configure(DEFAULT_HOTKEY)
            except Exception:
                pass

    def _prepare_ai_model(self) -> None:
        """Eski sürümden kalan yönlendirici model kimliğini temizler (gerçek model değil)."""
        model = self.settings.get("openrouter_model")
        if isinstance(model, str) and model.startswith("openrouter/"):
            try:
                self.settings.save(openrouter_model=None)
                logger.info("Yönlendirici model kimliği temizlendi: %s", model)
            except Exception:
                logger.warning("Model ayarı temizlenemedi", exc_info=True)

    def _remove_last_recording(self) -> None:
        path = self._last_recording_path
        self._last_recording = None
        try:
            if path.exists():
                path.unlink()
                logger.info("Eski geçici yenileme kaydı silindi")
        except Exception as exc:
            logger.warning("Eski geçici kayıt silinemedi: %s", exc)

    # ---------- yaşam döngüsü ----------

    def start(self) -> None:
        """Motoru arka planda yükler, görev çubuğu/pencere ikonunu zorlar ve kısayolu başlatır."""
        set_app_user_model_id(DEFAULT_APP_ID)
        start_window_icon_watcher(daemon=True)

        with self._lock:
            if self._closed:
                return
        if self._load_in_background:
            threading.Thread(target=self.load_engine, name="motor-yukle", daemon=True).start()
        try:
            self.hotkey.start()
        except Exception as exc:
            logger.warning("Kısayol başlatılamadı: %s", exc)
            with self._lock:
                self._add_activity("Kısayol başlatılamadı", str(exc), "err")

    def apply_window_icon(self, hwnd: int | None = None) -> bool:
        """Pencereye Win32 üzerinden icon.ico atar."""
        return apply_window_icon(hwnd)

    def load_engine(self) -> None:
        with self._engine_lock:
            with self._lock:
                if self._whisper_loaded or self._closed:
                    return
                if self._machine.state == READY:
                    self._set_state(LOADING)
            try:
                info = self.engine.load()
            except Exception as exc:
                message = str(exc) if isinstance(exc, EngineError) else diagnostics.MSG_MODEL_MISSING
                logger.error("Motor yüklenemedi: %s", exc)
                with self._lock:
                    self._whisper_loaded = False
                    self._error = message
                    self._set_state(ERROR)
                    self._add_activity("Model yüklenemedi", message, "err")
                return

            with self._lock:
                self._info = info
                self._whisper_loaded = True
                self._error = None
                self._set_state(READY)
                self._add_activity(
                    "Model yüklendi",
                    f"{info.model_label} · {info.device} · {info.compute_type}",
                    "info",
                )
                for title, sub, kind in self._startup_notes:
                    self._add_activity(title, sub, kind)
                self._startup_notes.clear()
                warnings = list(getattr(self.engine, "warnings", []) or [])
                if warnings and not self._gpu_warning_shown:
                    self._gpu_warning_shown = True
                    self._add_activity("GPU kullanılamadı", "CPU modu (small, int8)", "warn")
            logger.info("Model hazır: %s (%s)", info.model_label, info.device)

    def _unload_whisper(self) -> None:
        with self._engine_lock:
            with self._lock:
                if not self._whisper_loaded:
                    return
                self._whisper_loaded = False
            try:
                self.engine.unload()
            except Exception:
                logger.warning("Ses modeli boşaltılamadı", exc_info=True)

    def _prepare_whisper(self) -> None:
        """Dikte başlamadan önce metin modelini boşaltıp ses modelini yükler."""
        with self._engine_lock:
            with self._lock:
                has_text = bool(self._text_runtime.model_name)
                whisper_loaded = self._whisper_loaded
            if has_text:
                self._text_runtime.unload()
                with self._lock:
                    self._add_activity("Metin modeli bellekten boşaltıldı", "Dikte için yer açıldı.", "info")
            if not whisper_loaded:
                with self._lock:
                    if self._machine.state == READY:
                        self._set_state(LOADING)
                self.load_engine()

    def shutdown(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._hotkey_events.clear()
            self._text_cancel.set()
            self._text_pause.set()
            self._ai_cancel_event.set()
            self._update_cancel_event.set()
            threads = [
                self._worker,
                self._download_thread,
                self._text_download_thread,
                self._hotkey_thread,
                self._ai_worker,
            ]
        try:
            self.hotkey.stop()
        except Exception:
            pass
        try:
            self.recorder.cancel()
        except Exception:
            pass
        for thread in threads:
            if thread is not None and thread.is_alive() and thread is not threading.current_thread():
                thread.join(timeout=2.0)
        try:
            self._text_runtime.unload()
        except Exception:
            pass
        self._remove_last_recording()
        for temp_dir in {getattr(self.recorder, "temp_dir", None), Path(config.TEMP_DIR)}:
            if temp_dir and Path(temp_dir).exists():
                for wav in Path(temp_dir).glob("kayit-*.wav"):
                    try:
                        wav.unlink(missing_ok=True)
                    except OSError:
                        pass
        logger.info("Uygulama kapatıldı")

    # ---------- kısayol ve düğme ----------

    def on_hotkey_press(self) -> None:
        with self._lock:
            if self._closed:
                return
            worker_alive = self._hotkey_thread is not None and self._hotkey_thread.is_alive()
            needs_reload = not self._whisper_loaded or bool(self._text_runtime.model_name)
            if worker_alive or needs_reload or self._hotkey_events:
                self._hotkey_events.append("press")
                if not worker_alive:
                    self._hotkey_thread = threading.Thread(
                        target=self._hotkey_worker, name="kisayol-isci", daemon=True
                    )
                    self._hotkey_thread.start()
                return
        self.toggle_record()

    def on_hotkey_release(self) -> None:
        with self._lock:
            if self._closed:
                return
            worker_alive = self._hotkey_thread is not None and self._hotkey_thread.is_alive()
            if worker_alive or self._hotkey_events:
                self._hotkey_events.append("release")
                if not worker_alive:
                    self._hotkey_thread = threading.Thread(
                        target=self._hotkey_worker, name="kisayol-isci", daemon=True
                    )
                    self._hotkey_thread.start()
                return
        self._stop_recording(trigger="kısayol")

    def _hotkey_worker(self) -> None:
        while True:
            with self._lock:
                if self._closed or not self._hotkey_events:
                    return
                event = self._hotkey_events.popleft()
            if event == "press":
                with self._lock:
                    state = self._machine.state
                    if state == RECORDING:
                        self._stop_recording(trigger="kısayol")
                        continue
                    if state == ERROR and self._info is not None:
                        self._error = None
                        self._set_state(READY)
                        state = READY
                    if state != READY:
                        continue
                self._prepare_whisper()
                with self._lock:
                    if self._closed or self._machine.state != READY:
                        continue
                    if self._hotkey_events and self._hotkey_events[0] == "release":
                        self._hotkey_events.popleft()
                        continue
                    self._start_recording()
            elif event == "release":
                self._stop_recording(trigger="kısayol")

    def toggle_record(self) -> dict:
        """Mikrofon düğmesi için başlat/durdur."""
        with self._lock:
            if self._closed:
                return {"ok": False, "state": self._machine.state, "message": "Uygulama kapatıldı."}
            state = self._machine.state
            if state == RECORDING:
                return self._stop_recording(trigger="düğme")
            if state == ERROR:
                if self._info is None:
                    return {
                        "ok": False,
                        "state": state,
                        "message": self._error or diagnostics.MSG_MODEL_MISSING,
                    }
                # Çeviri hatasından sonra tekrar denenebilir.
                self._error = None
                self._set_state(READY)
                state = READY
            if state != READY:
                message = (
                    "Model yükleniyor, lütfen bekle."
                    if state == LOADING
                    else "İşleniyor, bitince tekrar dene."
                )
                return {"ok": False, "state": state, "message": message}

        # Metin modeli yüklüyse boşaltıp ses modelini geri getir (VRAM takası).
        if not self._whisper_loaded or bool(self._text_runtime.model_name):
            self._prepare_whisper()
        with self._lock:
            if self._machine.state != READY:
                return {
                    "ok": False,
                    "state": self._machine.state,
                    "message": self._error or "Ses modeli hazır değil.",
                }
        return self._start_recording()

    def _start_recording(self) -> dict:
        with self._lock:
            if self._machine.state != READY:
                return {"ok": False, "state": self._machine.state}
            try:
                self.recorder.start()
            except AudioError as exc:
                self._error = str(exc)
                self._set_state(ERROR)
                self._add_activity("Mikrofon açılamadı", str(exc), "err")
                return {"ok": False, "state": ERROR, "message": str(exc)}
            self._set_state(RECORDING)
            self._beeper("start")
            return {"ok": True, "state": RECORDING}

    def _stop_recording(self, trigger: str = "kısayol") -> dict:
        with self._lock:
            if self._machine.state != RECORDING:
                return {"ok": False, "state": self._machine.state}
            try:
                recording = self.recorder.stop()
            except AudioError as exc:
                self._error = str(exc)
                self._set_state(ERROR)
                self._add_activity("Kayıt durdurulamadı", str(exc), "err")
                return {"ok": False, "state": ERROR, "message": str(exc)}

            self._beeper("stop")
            if recording is None or recording.duration < config.MIN_RECORD_SECONDS:
                if recording is not None:
                    self.recorder.cleanup(recording.path)
                self._set_state(READY)
                self._add_activity(
                    "Ses algılanamadı",
                    "Kayıt çok kısaydı (en az 0,4 sn).",
                    "warn",
                )
                return {"ok": True, "state": READY, "skipped": True}

            self._set_state(PROCESSING)
            self._worker = threading.Thread(
                target=self._process,
                args=(recording,),
                name="ceviri",
                daemon=True,
            )
            self._worker.start()
            logger.info("Çeviri başladı (%s, %.2f sn)", trigger, recording.duration)
            return {"ok": True, "state": PROCESSING}

    # ---------- çeviri işçileri ----------

    def _transcribe_path(self, path: Path):
        """GPU çevirisi çökerse bir kez CPU yedeğini dener."""
        if not self._whisper_loaded or bool(self._text_runtime.model_name):
            self._prepare_whisper()
        input_lang = str(self.settings.get("input_language", "tr"))

        def do_transcribe():
            try:
                return self.engine.transcribe(path, language=input_lang)
            except TypeError:
                return self.engine.transcribe(path)

        try:
            return do_transcribe()
        except EngineError as exc:
            can_fallback = (
                self._info is not None
                and self._info.device == "GPU"
                and hasattr(self.engine, "use_cpu_fallback")
            )
            if not can_fallback:
                raise
            logger.warning("GPU çevirisi başarısız (%s), CPU deneniyor", exc)
            info = self.engine.use_cpu_fallback()
            with self._lock:
                self._info = info
                self._add_activity("GPU kullanılamadı", "CPU moduna geçildi", "warn")
            return do_transcribe()

    def _keep_last_recording(self, source: Path | None) -> None:
        if not source:
            return
        target = self._last_recording_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.replace(source, target)
            except OSError:
                shutil.copyfile(source, target)
                source.unlink(missing_ok=True)
            self._last_recording = target
        except Exception as exc:
            logger.warning("Yenileme kaydı saklanamadı: %s", exc)

    def _process(self, recording: Recording) -> None:
        try:
            result = self._transcribe_path(recording.path)
            text = result.text.strip()
            if not text:
                with self._lock:
                    self._add_activity("Ses algılanamadı", "Konuşma anlaşılamadı.", "warn")
                return

            copy_ok = True
            try:
                self._clipper(text)
            except ClipboardError as exc:
                copy_ok = False
                logger.warning("Pano hatası: %s", exc)

            self._keep_last_recording(recording.path)

            self._last_ai_copy_ok = copy_ok
            text = self._auto_ai_text(text)
            copy_ok = self._last_ai_copy_ok

            pasted = False
            if copy_ok and bool(self.settings.get("auto_paste", True)):
                try:
                    time.sleep(0.05)
                    pasted = bool(self._paster())
                except Exception as exc:
                    logger.warning("Otomatik yapıştırma hatası: %s", exc)

            with self._lock:
                self._latest = text
                self._seq += 1
                self._refresh_seq = self._seq
                self._replace_last = False
                self._error = None
                words = len(text.split())
                self._add_activity(
                    "Dikte tamamlandı",
                    f"({format_duration(recording.duration)}) · {words} kelime",
                    "ok",
                )
                if not copy_ok:
                    self._add_activity("Panoya kopyalanamadı", "Kopyala düğmesini dene.", "err")
                if pasted:
                    self._add_activity("Etkin pencereye yapıştırıldı", "Otomatik yapıştırma açık.", "info")
                model_name = self._info.model_name if self._info else ""

            record_id = self._save_history_record(text, recording.duration, model_name)
            with self._lock:
                self._last_history_id = record_id
        except Exception as exc:
            logger.exception("Çeviri başarısız: %s", exc)
            with self._lock:
                self._error = (
                    str(exc) if isinstance(exc, EngineError) else diagnostics.MSG_TRANSCRIBE_FAILED
                )
                self._set_state(ERROR)
                self._add_activity("Çeviri hatası", self._error, "err")
        finally:
            # Kaynak dosya son kayıt olarak taşınsa bile geçici kopya silinir.
            self.recorder.cleanup(recording.path)
            with self._lock:
                # Başarılı veya boş sonuçta işlem biter; hata durumunda ERROR korunur.
                if self._machine.state == PROCESSING:
                    self._set_state(READY)

    def _save_history_record(self, text: str, duration: float, model_name: str) -> str | None:
        if not self._save_history:
            return None
        try:
            record = self.history.add(text, duration, len(text.split()), model_name)
            return record["id"]
        except Exception as exc:
            logger.warning("Geçmişe kaydedilemedi: %s", exc)
            with self._lock:
                self._add_activity("Geçmiş kaydedilemedi", str(exc), "err")
            return None

    def refresh_last(self) -> dict:
        """Son kaydın sesini tekrar çevirir."""
        with self._lock:
            if self._machine.state != READY:
                return {
                    "ok": False,
                    "state": self._machine.state,
                    "message": "Şu anda yenilenemez, lütfen bekle.",
                }
            path = self._last_recording
            if not path or not Path(path).exists() or self._seq != self._refresh_seq:
                return {"ok": False, "message": "Yenilenecek kayıt yok."}
            self._error = None
        self._prepare_whisper()
        with self._lock:
            if self._machine.state != READY:
                return {
                    "ok": False,
                    "state": self._machine.state,
                    "message": self._error or "Ses modeli hazır değil.",
                }
            self._set_state(PROCESSING)
        self._worker = threading.Thread(
            target=self._refresh_worker,
            args=(path,),
            name="yenile",
            daemon=True,
        )
        self._worker.start()
        return {"ok": True, "state": PROCESSING}

    def _refresh_worker(self, path: Path) -> None:
        try:
            result = self._transcribe_path(path)
            text = result.text.strip()
            if not text:
                with self._lock:
                    self._add_activity("Ses algılanamadı", "Konuşma anlaşılamadı.", "warn")
                return

            copy_ok = True
            try:
                self._clipper(text)
            except ClipboardError as exc:
                copy_ok = False
                logger.warning("Pano hatası: %s", exc)

            self._last_ai_copy_ok = copy_ok
            text = self._auto_ai_text(text)
            copy_ok = self._last_ai_copy_ok

            with self._lock:
                self._latest = text
                self._seq += 1
                self._refresh_seq = self._seq
                self._replace_last = True
                self._error = None
                record_id = self._last_history_id
                self._add_activity("Transkripsiyon yenilendi", f"{len(text.split())} kelime", "ok")
                if not copy_ok:
                    self._add_activity("Panoya kopyalanamadı", "Kopyala düğmesini dene.", "err")

            if self._save_history and record_id:
                try:
                    self.history.update_text(record_id, text)
                except Exception as exc:
                    logger.warning("Geçmiş güncellenemedi: %s", exc)
        except Exception as exc:
            logger.exception("Yenileme başarısız: %s", exc)
            with self._lock:
                self._error = (
                    str(exc) if isinstance(exc, EngineError) else diagnostics.MSG_TRANSCRIBE_FAILED
                )
                self._set_state(ERROR)
                self._add_activity("Yenileme hatası", self._error, "err")
        finally:
            with self._lock:
                if self._machine.state == PROCESSING:
                    self._set_state(READY)

    # ---------- pano ve anlık görüntü ----------

    def copy(self, text: str) -> dict:
        if not text or not text.strip():
            return {"ok": False, "message": "Kopyalanacak metin yok."}
        try:
            self._clipper(text)
        except ClipboardError as exc:
            return {"ok": False, "message": str(exc)}
        return {"ok": True}

    def snapshot(self) -> dict:
        with self._lock:
            info = self._info
            state = self._machine.state
            return {
                "state": state,
                "status": STATE_LABELS.get(state, state),
                "seq": self._seq,
                "latest_text": self._latest,
                "replace_last": self._replace_last,
                "model": info.model_label if info else None,
                "model_name": info.model_name if info else None,
                "device": info.device if info else None,
                "compute": info.compute_type if info else None,
                "memory": self._memory(info),
                "activity": [dict(item) for item in self._activity],
                "error": self._error,
                "hotkey": hotkey_label(self._hotkey_id),
                "hotkey_id": self._hotkey_id,
                "design_style": str(self.settings.get("design_style", "dikte_ai")),
                "setup_done": bool(self.settings.get("setup_done", False)),
                "sidebar_collapsed": bool(self.settings.get("sidebar_collapsed", False)),
                "language": config.LANGUAGE_LABEL,
                "save_history": self._save_history,
                "can_refresh": bool(
                    self._last_recording
                    and self._last_recording.exists()
                    and self._seq == self._refresh_seq
                )
                and state == READY,
                "download": dict(self._download) if self._download else None,
                "ai": self._ai_payload(),
            }

    def wait_until_ready(self, timeout: float = 5.0) -> bool:
        """Testler ve konsol aracı için: işlem bitene kadar bekler."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.snapshot()["state"] != PROCESSING:
                return True
            time.sleep(0.02)
        return False

    # ---------- geçmiş ----------

    def history_list(self, query: str = "", period: str = "all") -> dict:
        if not self._save_history:
            return {"disabled": True, "items": [], "total": 0}
        try:
            items = self.history.list(query, period)
        except Exception as exc:
            logger.warning("Geçmiş okunamadı: %s", exc)
            return {"disabled": False, "items": [], "total": 0, "error": str(exc)}
        return {"disabled": False, "items": items, "total": len(items)}

    def history_open(self, record_id: str) -> dict:
        if not self._save_history:
            return {"ok": False, "message": "Geçmiş kaydedilmiyor."}
        record = self.history.get(record_id)
        if record is None:
            return {"ok": False, "message": "Kayıt bulunamadı."}
        with self._lock:
            self._latest = record["text"]
            self._last_history_id = record_id
            self._seq += 1
            self._replace_last = False
        return {"ok": True, "text": record["text"], "id": record_id}

    def history_delete(self, record_id: str) -> dict:
        try:
            removed = self.history.delete(record_id)
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        if removed:
            with self._lock:
                if self._last_history_id == record_id:
                    self._last_history_id = None
        return {"ok": removed, "message": None if removed else "Kayıt bulunamadı."}

    def history_clear(self) -> dict:
        try:
            self.history.clear()
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        with self._lock:
            self._last_history_id = None
        return {"ok": True}

    # ---------- modeller ----------

    def models_list(self) -> dict:
        now = time.monotonic()
        cached_at, cached = self._models_cache
        if cached is None or now - cached_at > 1.0:
            try:
                cached = self.models.scan()
            except Exception as exc:
                logger.warning("Model listesi okunamadı: %s", exc)
                cached = {}
            self._models_cache = (now, cached)

        with self._lock:
            active = self._info.model_name if self._info else None
            device = self._info.device if self._info else None
            download = dict(self._download) if self._download else None

        items = []
        for name, data in cached.items():
            item = dict(data)
            item["active"] = name == active
            item["downloading"] = bool(
                download and download.get("name") == name and download.get("state") == "downloading"
            )
            items.append(item)

        text_items = text_models.scan()
        with self._lock:
            text_download = dict(self._text_download) if self._text_download else None
            text_active = str(self.settings.get("text_model", ""))
            text_loaded = self._text_runtime.model_name
        for item in text_items:
            item["active"] = bool(item["installed"] and item["name"] == text_active)
            item["loaded"] = item["name"] == text_loaded
            item["downloading"] = bool(
                text_download
                and text_download.get("name") == item["name"]
                and text_download.get("state") in ("downloading", "pausing")
            )
            item["paused"] = bool(
                text_download
                and text_download.get("name") == item["name"]
                and text_download.get("state") == "paused"
            )
        active_text = next((item for item in text_items if item["active"]), None)
        return {
            "items": items,
            "text_items": text_items,
            "active_model": active or AUTO_MODEL,
            "active_text_model": active_text["name"] if active_text else None,
            "device": device,
            "download": download,
            "text_download": text_download,
            "local_text_available": LocalTextModel.available(),
        }

    def model_download(self, name: str) -> dict:
        try:
            spec = get_model(name)
        except ModelError as exc:
            return {"ok": False, "message": str(exc)}
        try:
            # Disk taraması kilidi uzun süre tutmasın diye kilit dışında.
            already_installed = self.models.installed(name)
        except Exception:
            already_installed = False
        with self._lock:
            if self._download and self._download.get("state") == "downloading":
                return {"ok": False, "message": "Başka bir model indiriliyor, lütfen bekle."}
            if already_installed:
                return {"ok": False, "message": "Bu model zaten indirilmiş."}
            self._download = {
                "name": name,
                "label": spec.label,
                "state": "downloading",
                "bytes": self.models.size(name),
                "total": spec.approx_bytes,
                "percent": 0,
                "error": None,
            }
            self._models_cache = (0.0, None)

        self._download_thread = threading.Thread(
            target=self._download_worker,
            args=(name,),
            name="model-indir",
            daemon=True,
        )
        self._download_thread.start()
        return {"ok": True, "message": f"{spec.label} indiriliyor."}

    def _download_worker(self, name: str) -> None:
        def on_progress(size: int) -> None:
            with self._lock:
                download = self._download
                if not download or download.get("name") != name:
                    return
                if download.get("state") != "downloading":
                    return
                download["bytes"] = size
                total = download.get("total") or 0
                if total:
                    download["percent"] = max(0, min(99, int(size / total * 100)))

        try:
            self.models.download(name, progress=on_progress)
            size = self.models.size(name)
        except Exception as exc:
            logger.warning("Model indirilemedi: %s", exc)
            with self._lock:
                if self._download and self._download.get("name") == name:
                    self._download["state"] = "error"
                    self._download["error"] = str(exc)
                self._add_activity("Model indirilemedi", f"{name}: {exc}", "err")
            self._models_cache = (0.0, None)
            return

        with self._lock:
            if self._download and self._download.get("name") == name:
                self._download["state"] = "done"
                self._download["percent"] = 100
                self._download["bytes"] = size
            self._add_activity("Model indirildi", name, "ok")
        self._models_cache = (0.0, None)

    def model_activate(self, name: str) -> dict:
        try:
            get_model(name)
        except ModelError as exc:
            return {"ok": False, "message": str(exc)}
        with self._lock:
            state = self._machine.state
            if state in (RECORDING, PROCESSING):
                return {"ok": False, "message": "Kayıt veya çeviri sürerken model değiştirilemez."}
            if state == LOADING:
                return {"ok": False, "message": "Model yükleniyor, lütfen bekle."}
            try:
                installed = self.models.installed(name)
            except Exception:
                installed = False
            if not installed:
                return {"ok": False, "message": "Bu model önce indirilmeli."}
            old_model = getattr(self.engine, "model_name", None) or (
                self._info.model_name if self._info else None
            )
            self._error = None
            self._set_state(LOADING)

        threading.Thread(
            target=self._activate_worker,
            args=(name, old_model),
            name="model-yukle",
            daemon=True,
        ).start()
        return {"ok": True, "state": LOADING}

    def _activate_worker(self, name: str, old_model: str | None) -> None:
        with self._engine_lock:
            if self._text_runtime.model_name:
                self._text_runtime.unload()
            try:
                if hasattr(self.engine, "set_model"):
                    self.engine.set_model(name)
                if hasattr(self.engine, "unload"):
                    self.engine.unload()
                self._whisper_loaded = False
                info = self.engine.load()
            except Exception as exc:
                logger.error("Model değiştirilemedi: %s", exc)
                message = str(exc) if isinstance(exc, EngineError) else diagnostics.MSG_MODEL_MISSING
                reverted = False
                if old_model:
                    try:
                        if hasattr(self.engine, "set_model"):
                            self.engine.set_model(old_model)
                        if hasattr(self.engine, "unload"):
                            self.engine.unload()
                        info = self.engine.load()
                        reverted = True
                    except Exception:
                        logger.exception("Eski model geri yüklenemedi")
                with self._lock:
                    if reverted:
                        self._info = info
                        self._whisper_loaded = True
                        self._error = None
                        self._set_state(READY)
                        self._add_activity(
                            "Model değiştirilemedi",
                            f"{message} · {info.model_label} kullanılmaya devam ediyor.",
                            "warn",
                        )
                    else:
                        self._error = message
                        self._set_state(ERROR)
                        self._add_activity("Model yüklenemedi", message, "err")
                self._models_cache = (0.0, None)
                return

            try:
                self.settings.save(active_model=info.model_name or name)
            except Exception:
                logger.warning("Aktif model ayarı kaydedilemedi", exc_info=True)
            with self._lock:
                self._info = info
                self._whisper_loaded = True
                self._error = None
                self._set_state(READY)
                self._add_activity(
                    "Model değiştirildi",
                    f"{info.model_label} · {info.device} · {info.compute_type}",
                    "ok",
                )
            self._models_cache = (0.0, None)

    def model_delete(self, name: str) -> dict:
        with self._lock:
            if self._info and self._info.model_name == name:
                return {"ok": False, "message": "Aktif model silinemez. Önce başka bir model seç."}
            if self._download and self._download.get("name") == name:
                return {"ok": False, "message": "İndirme sürerken model silinemez."}
        try:
            self.models.delete(name)
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        self._models_cache = (0.0, None)
        with self._lock:
            self._add_activity("Model silindi", name, "info")
        return {"ok": True, "message": f"{name} silindi."}

    def models_cancel_download(self) -> dict:
        """Süren ses modeli indirmesini iptal eder."""
        with self._lock:
            if self._download and self._download.get("state") == "downloading":
                self._download["state"] = "cancelled"
        try:
            cancel_fn = getattr(self.models, "cancel_download", None)
            if cancel_fn is not None:
                cancel_fn()
        except Exception as exc:
            logger.warning("Ses modeli indirme iptali hatası: %s", exc)
        self._models_cache = (0.0, None)
        with self._lock:
            self._add_activity("Ses modeli indirme iptal edildi", "", "warn")
        return {"ok": True, "message": "İndirme iptal edildi."}

    def models_add_custom(self, repo_id: str, label: str = "") -> dict:
        """Hugging Face ses modeli ekler."""
        try:
            add_fn = getattr(self.models, "add_custom_model", None)
            if add_fn is not None:
                model = add_fn(repo_id, label)
            else:
                from . import models as m_mod
                model = m_mod.add_custom_model(repo_id, label)
            self._models_cache = (0.0, None)
            with self._lock:
                self._add_activity("Özel ses modeli eklendi", label or repo_id, "ok")
            return {"ok": True, "model": model}
        except Exception as exc:
            logger.warning("Özel ses modeli eklenemedi: %s", exc)
            return {"ok": False, "message": str(exc)}

    def models_remove_custom(self, name: str) -> dict:
        """Özel ses modelini listeden tamamen kaldırır."""
        try:
            rem_fn = getattr(self.models, "remove_custom_model", None)
            if rem_fn is not None:
                rem_fn(name)
            else:
                from . import models as m_mod
                m_mod.remove_custom_model(name, getattr(self.models, "models_dir", None))
            self._models_cache = (0.0, None)
            with self._lock:
                self._add_activity("Özel model listeden kaldırıldı", name, "info")
            return {"ok": True, "message": f"{name} listeden kaldırıldı."}
        except Exception as exc:
            logger.warning("Özel model kaldırılamadı: %s", exc)
            return {"ok": False, "message": str(exc)}

    # ---------- metin modelleri ----------

    def _disk_free(self) -> int:
        path = text_models.models_dir()
        try:
            path.mkdir(parents=True, exist_ok=True)
            return shutil.disk_usage(path).free
        except Exception:
            return 1 << 62

    def text_model_download(self, name: str) -> dict:
        try:
            spec = text_models.get_text_model(name)
        except text_models.TextModelError as exc:
            return {"ok": False, "message": str(exc)}
        if text_models.is_installed(name):
            return {"ok": False, "message": "Bu metin modeli zaten indirilmiş."}
        with self._lock:
            if self._closed:
                return {"ok": False, "message": "Uygulama kapatıldı."}
            if self._text_download and self._text_download.get("state") in ("downloading", "pausing"):
                return {"ok": False, "message": "Başka bir metin modeli indiriliyor, lütfen bekle."}
        if self._disk_free() < spec.size_bytes + 200 * 1024**2:
            return {"ok": False, "message": "Diskte yeterli yer yok."}

        with self._lock:
            self._text_download = {
                "name": name,
                "label": spec.label,
                "state": "downloading",
                "bytes": text_models.partial_bytes(name),
                "total": spec.size_bytes,
                "percent": 0,
                "error": None,
            }
        self._start_text_download(name)
        return {"ok": True, "message": f"{spec.label} indiriliyor."}

    def _start_text_download(self, name: str) -> None:
        prev = self._text_download_thread
        if prev is not None and prev.is_alive() and prev is not threading.current_thread():
            prev.join(timeout=2.0)
        with self._lock:
            self._text_download_token += 1
            token = self._text_download_token
            pause_event = threading.Event()
            cancel_event = threading.Event()
            self._text_pause = pause_event
            self._text_cancel = cancel_event
        self._text_download_thread = threading.Thread(
            target=self._text_download_worker,
            args=(name, token, pause_event, cancel_event),
            name="metin-indir",
            daemon=True,
        )
        self._text_download_thread.start()

    def _text_download_worker(
        self,
        name: str,
        token: int | None = None,
        pause_event: threading.Event | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        if token is None:
            token = self._text_download_token
        pause_ev = pause_event or self._text_pause
        cancel_ev = cancel_event or self._text_cancel

        def on_progress(written: int) -> None:
            with self._lock:
                if self._text_download_token != token:
                    return
                download = self._text_download
                if not download or download.get("name") != name:
                    return
                download["bytes"] = written
                total = download.get("total") or 0
                if total:
                    download["percent"] = max(0, min(99, int(written / total * 100)))

        try:
            result = self._text_downloader.download(
                name,
                progress=on_progress,
                pause_event=pause_ev,
                cancel_event=cancel_ev,
            )
        except Exception as exc:
            logger.warning("Metin modeli indirilemedi: %s", exc)
            with self._lock:
                if self._text_download_token == token and self._text_download and self._text_download.get("name") == name:
                    self._text_download["state"] = "error"
                    self._text_download["error"] = str(exc)
                    self._add_activity("Metin modeli indirilemedi", f"{name}: {exc}", "err")
            self._models_cache = (0.0, None)
            return

        cancelled = bool(result.get("cancelled") or cancel_ev.is_set())
        with self._lock:
            is_current = self._text_download_token == token
            download = self._text_download if is_current else None
            if download and download.get("name") == name:
                download["bytes"] = result.get("size", download.get("bytes", 0))
                if cancelled:
                    download["state"] = "cancelled"
                    download["percent"] = 0
                elif result.get("completed"):
                    download["state"] = "done"
                    download["percent"] = 100
                    self._add_activity("Metin modeli indirildi", name, "ok")
                elif result.get("paused"):
                    download["state"] = "paused"
        if cancelled and is_current:
            try:
                text_models.delete_part(name)
            except text_models.TextModelError:
                pass
        self._models_cache = (0.0, None)

    def text_model_pause(self, name: str) -> dict:
        with self._lock:
            download = self._text_download
            if not download or download.get("name") != name or download.get("state") != "downloading":
                return {"ok": False, "message": "Bu model indirilmiyor."}
            download["state"] = "pausing"
            pause_ev = self._text_pause
        pause_ev.set()
        return {"ok": True, "message": "Duraklatılıyor…"}

    def text_model_resume(self, name: str) -> dict:
        with self._lock:
            if self._closed:
                return {"ok": False, "message": "Uygulama kapatıldı."}
            download = self._text_download
            if not download or download.get("name") != name or download.get("state") not in ("paused", "pausing"):
                return {"ok": False, "message": "Devam edecek bir indirme yok."}
            prev = self._text_download_thread
        if prev is not None and prev.is_alive() and prev is not threading.current_thread():
            prev.join(timeout=2.0)
        with self._lock:
            download = self._text_download
            if not download or download.get("name") != name or download.get("state") not in ("paused", "pausing"):
                return {"ok": False, "message": "Devam edecek bir indirme yok."}
            download["state"] = "downloading"
            total = download.get("total") or 0
            if total:
                download["percent"] = max(0, min(99, int(download.get("bytes", 0) / total * 100)))
        self._start_text_download(name)
        return {"ok": True, "message": "İndirme devam ediyor."}

    def text_model_cancel(self, name: str) -> dict:
        with self._lock:
            download = self._text_download
            if not download or download.get("name") != name or download.get("state") not in (
                "downloading", "pausing", "paused"
            ):
                return {"ok": False, "message": "İptal edilecek indirme yok."}
            download["state"] = "cancelled"
            download["percent"] = 0
            cancel_ev = self._text_cancel
            pause_ev = self._text_pause
            prev = self._text_download_thread
        cancel_ev.set()
        pause_ev.clear()
        if prev is not None and prev.is_alive() and prev is not threading.current_thread():
            prev.join(timeout=2.0)
        try:
            text_models.delete_part(name)
        except text_models.TextModelError:
            pass
        return {"ok": True, "message": "İndirme iptal edildi."}

    def text_model_activate(self, name: str) -> dict:
        try:
            spec = text_models.get_text_model(name)
        except text_models.TextModelError as exc:
            return {"ok": False, "message": str(exc)}
        if not text_models.is_installed(name):
            return {"ok": False, "message": "Önce modeli indir."}
        if not LocalTextModel.available():
            return {
                "ok": False,
                "message": "Yerel metin motoru (llama.cpp) kurulu değil. OpenRouter sağlayıcısını kullanabilirsin.",
            }
        with self._lock:
            if self._machine.state != READY:
                return {"ok": False, "message": "Şu anda model değiştirilemez, lütfen bekle."}
            self._set_state(LOADING)
        try:
            self._unload_whisper()
            device = self._text_runtime.load(name, prefer_gpu=True)
        except Exception as exc:
            logger.warning("Metin modeli yüklenemedi: %s", exc)
            with self._lock:
                self._set_state(READY)
                self._add_activity("Metin modeli yüklenemedi", str(exc), "err")
            return {"ok": False, "message": str(exc) or "Metin modeli yüklenemedi."}

        try:
            self.settings.save(text_model=name)
        except SettingsError:
            logger.warning("Metin modeli ayarı kaydedilemedi", exc_info=True)
        with self._lock:
            self._set_state(READY)
            self._add_activity("Metin modeli yüklendi", f"{spec.label} · {device}", "ok")
        self._models_cache = (0.0, None)
        return {"ok": True, "message": f"{spec.label} yüklendi ({device})."}

    def text_model_delete(self, name: str) -> dict:
        if self._text_runtime.model_name == name:
            return {"ok": False, "message": "Yüklü metin modeli silinemez. Önce başka model seç."}
        with self._lock:
            if self._text_download and self._text_download.get("name") == name and self._text_download.get("state") in (
                "downloading", "pausing"
            ):
                return {"ok": False, "message": "İndirme sürerken model silinemez."}
        try:
            text_models.delete(name)
        except text_models.TextModelError as exc:
            return {"ok": False, "message": str(exc)}
        self._models_cache = (0.0, None)
        return {"ok": True, "message": f"{name} silindi."}

    def text_model_open_folder(self, name: str = "") -> dict:
        try:
            folder = text_models.models_dir()
            folder.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(folder))  # noqa: S606
            return {"ok": True, "message": str(folder)}
        except Exception as exc:
            logger.warning("Klasör açılamadı: %s", exc)
            return {"ok": False, "message": "Klasör açılamadı."}

    def text_models_add_custom(
        self, repo_or_url: str, filename: str = "", label: str = ""
    ) -> dict:
        """Hugging Face GGUF metin modeli ekler."""
        try:
            add_fn = getattr(text_models, "add_custom_text_model", None)
            if add_fn is None:
                return {"ok": False, "message": "Özel metin modeli desteği henüz hazır değil."}
            model = add_fn(repo_or_url, filename=filename, label=label)
            self._models_cache = (0.0, None)
            with self._lock:
                self._add_activity("Özel metin modeli eklendi", label or filename or repo_or_url, "ok")
            return {"ok": True, "model": model}
        except Exception as exc:
            logger.warning("Özel metin modeli eklenemedi: %s", exc)
            return {"ok": False, "message": str(exc)}

    def text_models_remove_custom(self, model_id: str) -> dict:
        """Özel metin modelini listeden tamamen kaldırır."""
        try:
            rem_fn = getattr(text_models, "remove_custom_text_model", None)
            if rem_fn is None:
                return {"ok": False, "message": "Özel metin modeli kaldırma henüz hazır değil."}
            rem_fn(model_id)
            self._models_cache = (0.0, None)
            with self._lock:
                self._add_activity("Özel metin modeli kaldırıldı", model_id, "info")
            return {"ok": True, "message": f"{model_id} listeden kaldırıldı."}
        except Exception as exc:
            logger.warning("Özel metin modeli kaldırılamadı: %s", exc)
            return {"ok": False, "message": str(exc)}

    # ---------- ayarlar ----------

    def settings_get(self) -> dict:
        with self._lock:
            state = self._machine.state
        return {
            "save_history": self._save_history,
            "hotkey": self._hotkey_id,
            "hotkey_label": hotkey_label(self._hotkey_id),
            "active_model": str(self.settings.get("active_model", AUTO_MODEL)),
            "design_style": str(self.settings.get("design_style", "dikte_ai")),
            "setup_done": bool(self.settings.get("setup_done", False)),
            "sidebar_collapsed": bool(self.settings.get("sidebar_collapsed", False)),
            "effects": bool(self.settings.get("effects", True)),
            "theme": str(self.settings.get("theme", "system")),
            "state": state,
            "ai": self._ai_payload(),
            "choices": [
                {"id": key, "label": label} for key, label in HOTKEY_CHOICES.items()
            ],
        }

    def settings_save(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        with self._lock:
            state = self._machine.state
            if state in (RECORDING, PROCESSING, LOADING, CLEANING):
                return {"ok": False, "message": "Kayıt, çeviri veya model yüklemesi sürerken ayarlar kaydedilemez."}
            current_hotkey = self._hotkey_id

        changes: dict = {}
        new_hotkey = payload.get("hotkey")
        hotkey_changed = bool(new_hotkey and new_hotkey != current_hotkey)
        if hotkey_changed:
            set_key = getattr(self.hotkey, "set_key", None)
            if set_key is None:
                return {"ok": False, "message": "Kısayol değiştirilemiyor."}
            try:
                set_key(new_hotkey)
            except HotkeyError as exc:
                return {"ok": False, "message": str(exc)}
            except Exception as exc:
                logger.exception("Kısayol değiştirilemedi")
                return {"ok": False, "message": f"Kısayol değiştirilemedi: {exc}"}
            changes["hotkey"] = new_hotkey

        if "save_history" in payload:
            changes["save_history"] = bool(payload["save_history"])
        if "design_style" in payload:
            changes["design_style"] = str(payload["design_style"])
        if "setup_done" in payload:
            changes["setup_done"] = bool(payload["setup_done"])
        if "sidebar_collapsed" in payload:
            changes["sidebar_collapsed"] = bool(payload["sidebar_collapsed"])
        if "effects" in payload:
            changes["effects"] = bool(payload["effects"])
        if "theme" in payload:
            changes["theme"] = str(payload["theme"])
        if "active_model" in payload:
            changes["active_model"] = str(payload["active_model"])

        try:
            data = self.settings.save(**changes)
        except SettingsError as exc:
            if hotkey_changed:
                try:
                    self.hotkey.set_key(current_hotkey)
                except Exception:
                    logger.exception("Kısayol geri alınamadı")
            return {"ok": False, "message": str(exc)}

        with self._lock:
            self._save_history = bool(data.get("save_history", True))
            self._hotkey_id = str(data.get("hotkey", DEFAULT_HOTKEY))
            self._add_activity("Ayarlar kaydedildi", "Kısayol ve geçmiş tercihi güncellendi.", "info")
        return {"ok": True, "message": "Ayarlar kaydedildi.", "settings": self.settings_get()}

    # ---------- yapay zeka (temizle / çevir) ----------

    AI_SETTING_KEYS = {
        "output_language",
        "auto_translate",
        "input_language",
        "auto_paste",
        "text_provider",
        "text_model",
        "openrouter_model",
        "openrouter_show_all",
        "system_prompt",
        "theme",
        "design_style",
        "setup_done",
        "sidebar_collapsed",
        "effects",
        "update_check_on_start",
        "autostart",
    }

    def _provider(self) -> str:
        return str(self.settings.get("text_provider", "none"))

    def _openrouter_key(self, refresh: bool = False) -> str | None:
        if refresh or self._key_cache is None:
            try:
                key = self.secrets.load_key()
            except Exception:
                logger.warning("Anahtar okunamadı", exc_info=True)
                key = None
            self._key_cache = (True, key)
        return self._key_cache[1]

    def _ai_payload(self) -> dict:
        provider = self._provider()
        key = self._openrouter_key()
        output_language = str(self.settings.get("output_language", "tr"))
        return {
            "provider": provider,
            "provider_label": text_provider_label(provider),
            "output_language": output_language,
            "output_language_label": output_language_label(output_language),
            "auto_translate": bool(self.settings.get("auto_translate", False)),
            "input_language": str(self.settings.get("input_language", "auto")),
            "auto_paste": bool(self.settings.get("auto_paste", True)),
            "text_model": str(self.settings.get("text_model", "")),
            "text_model_loaded": self._text_runtime.model_name,
            "text_model_device": self._text_runtime.device,
            "local_text_available": LocalTextModel.available(),
            "openrouter_model": self.settings.get("openrouter_model"),
            "openrouter_show_all": bool(self.settings.get("openrouter_show_all", False)),
            "system_prompt": str(self.settings.get("system_prompt", config.DEFAULT_SYSTEM_PROMPT)),
            "default_system_prompt": config.DEFAULT_SYSTEM_PROMPT,
            "theme": str(self.settings.get("theme", "system")),
            "design_style": str(self.settings.get("design_style", "dikte_ai")),
            "setup_done": bool(self.settings.get("setup_done", False)),
            "sidebar_collapsed": bool(self.settings.get("sidebar_collapsed", False)),
            "effects": bool(self.settings.get("effects", True)),
            "key_set": bool(key),
            "key_masked": mask_key(key) if key else None,
            "update_check_on_start": bool(self.settings.get("update_check_on_start", True)),
            "update_last_check_text": self._update_last_check_text(),
            "version": config.APP_VERSION,
        }

    def _update_last_check_text(self) -> str:
        raw = self.settings.get("update_last_check")
        if not raw:
            return "—"
        try:
            when = datetime.fromisoformat(str(raw))
            return when.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            return "—"

    def ai_state(self) -> dict:
        with self._lock:
            state = self._machine.state
        payload = self._ai_payload()
        payload["state"] = state
        payload["ready"] = state == READY
        return payload

    def ai_settings_save(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        with self._lock:
            if self._machine.state in (RECORDING, PROCESSING, LOADING, CLEANING):
                return {"ok": False, "message": "İşlem sürerken ayarlar kaydedilemez."}
        changes = {key: value for key, value in payload.items() if key in self.AI_SETTING_KEYS}
        try:
            self.settings.save(**changes)
        except SettingsError as exc:
            return {"ok": False, "message": str(exc)}
        if "autostart" in changes:
            result = self.autostart_set(bool(changes["autostart"]))
            if not result.get("ok"):
                return result
        return {"ok": True, "message": "Ayarlar kaydedildi.", "ai": self.ai_state()}

    # ---------- uygulama (otomatik başlatma / kaldırma) ----------

    def autostart_set(self, enabled: bool) -> dict:
        try:
            uninstall.set_autostart(bool(enabled))
        except uninstall.UninstallError as exc:
            return {"ok": False, "message": str(exc)}
        return {"ok": True, "enabled": bool(enabled)}

    def uninstall_info(self) -> dict:
        return {
            "ok": True,
            "installed": uninstall.is_installed(),
            "version": config.APP_VERSION,
            "size_text": uninstall.format_size(uninstall.data_bytes()),
            "autostart": uninstall.autostart_enabled(),
        }

    def uninstall(self, payload: dict | None = None) -> dict:
        keep_models = bool((payload or {}).get("keep_models", True))
        try:
            uninstall.run_uninstaller(keep_models=keep_models)
        except uninstall.UninstallError as exc:
            logger.warning("Kaldırıcı başlatılamadı: %s", exc)
            return {"ok": False, "message": str(exc)}
        return {"ok": True, "message": "Kaldırıcı başlatıldı"}

    # ---------- güncelleme (v1.6) ----------

    UPDATE_MESSAGES = {
        "http_rejected": "Güncelleme denetimi yalnız HTTPS üzerinden yapılır.",
        "no_url": "Güncelleme sunucusu yapılandırılmamış.",
        "net": "Sunucuya ulaşılamadı.",
        "bad_json": "Güncelleme bildirimi okunamadı.",
        "bad_sha": "Güncelleme bildiriminde geçerli SHA-256 özeti yok; kurulum iptal edildi.",
        "no_sha": "Güncelleme bildiriminde SHA-256 özeti yok; kurulum iptal edildi.",
        "host_rejected": "İndirme adresi güvenilir değil.",
        "bad_url": "İndirme adresi geçersiz.",
        "incomplete": "İndirme tamamlanmadı. Tekrar dene.",
        "sha_mismatch": "İndirilen dosyanın özeti uyuşmuyor; dosya silindi.",
        "missing_installer": "Kurucu dosyası bulunamadı.",
    }

    def update_check(self, force: bool = False) -> dict:
        """Güncelleme denetimi. force=False açılışta sessiz denetim için."""
        try:
            result = updater.check(force=force)
        except updater.UpdaterError as exc:
            message = self.UPDATE_MESSAGES.get(exc.code, "Denetlenemedi.")
            logger.info("Güncelleme denetimi başarısız (%s)", exc.code)
            return {"ok": False, "code": exc.code, "message": message}
        if result is None:
            return {"ok": False, "code": "net", "message": "Sunucuya ulaşılamadı."}
        self.settings.save(update_last_check=datetime.now(timezone.utc).isoformat())
        if not result.get("update_available"):
            return {
                "ok": True,
                "update_available": False,
                "version": result.get("version", ""),
                "notes": result.get("notes", ""),
                "message": "Güncelsin.",
            }
        return {
            "ok": True,
            "update_available": True,
            "version": result.get("version", ""),
            "notes": result.get("notes", ""),
            "url": result.get("url", ""),
            "sha256": result.get("sha256", ""),
            "message": f"Yeni sürüm: {result.get('version', '')}",
        }

    def update_apply(self) -> dict:
        """Denetim, indirme, SHA-256 doğrulama ve sessiz kurulum tek sonuç üzerinden yürür."""
        try:
            result = updater.check(force=True)
        except updater.UpdaterError as exc:
            return {"ok": False, "code": exc.code, "message": self.UPDATE_MESSAGES.get(exc.code, "Denetlenemedi.")}
        if result is None or not result.get("update_available"):
            return {"ok": False, "code": "no_update", "message": "Yeni sürüm yok."}
        sha = result.get("sha256", "")
        url = result.get("url", "")
        try:
            path = updater.download(url)
        except updater.UpdaterError as exc:
            logger.info("Güncelleme indirilemedi (%s)", exc.code)
            return {"ok": False, "code": exc.code, "message": self.UPDATE_MESSAGES.get(exc.code, "İndirme başarısız. Bağlantını kontrol et.")}
        if not updater.verify_sha256(path, sha):
            return {"ok": False, "code": "sha_mismatch", "message": self.UPDATE_MESSAGES["sha_mismatch"]}
        try:
            updater.apply(path)
        except updater.UpdaterError as exc:
            return {"ok": False, "code": exc.code, "message": self.UPDATE_MESSAGES.get(exc.code, "Kurulum başlatılamadı.")}
        return {"ok": True, "message": "Kurulum başlatıldı; uygulama kapanacak."}

    def update_list_releases(self) -> dict:
        """GitHub Releases üzerinden geçmiş sürümleri listeler."""
        try:
            list_fn = getattr(updater, "list_releases", None)
            if list_fn is not None:
                items = list_fn()
                return {"ok": True, "releases": items, "total": len(items)}
            fn = getattr(updater, "fetch_releases_payload", None)
            if fn is not None:
                payload = fn()
                items = payload.get("releases", [])
                return {"ok": True, "releases": items, "total": len(items)}
            return {"ok": False, "message": "Releases listesi alınamadı.", "releases": []}
        except Exception as exc:
            logger.warning("Releases listesi alınamadı: %s", exc)
            return {"ok": False, "message": str(exc), "releases": []}

    def update_cancel(self) -> dict:
        """Güncelleme/rollback indirmesini iptal eder."""
        self._update_cancel_event.set()
        return {"ok": True, "message": "İndirme iptal edildi."}

    def update_rollback(self, version: str, installer_url: str, sha256: str = "") -> dict:
        """Seçilen eski sürümü indirir ve kurucuyu başlatır."""
        if not installer_url:
            return {"ok": False, "message": "Kurucu adresi belirtilmedi."}
        self._update_cancel_event.clear()
        try:
            dl_fn = getattr(updater, "download_installer", None) or getattr(updater, "download", None)
            if dl_fn is None:
                return {"ok": False, "message": "İndirme aracı bulunamadı."}
            import inspect
            sig = inspect.signature(dl_fn)
            kwargs = {}
            if "cancel_event" in sig.parameters:
                kwargs["cancel_event"] = self._update_cancel_event
            if "allow_missing_sha256" in sig.parameters and not sha256:
                kwargs["allow_missing_sha256"] = True
            path = dl_fn(installer_url, **kwargs)
        except updater.UpdaterError as exc:
            return {"ok": False, "code": exc.code, "message": self.UPDATE_MESSAGES.get(exc.code, str(exc))}
        except Exception as exc:
            logger.warning("Rollback indirilemedi: %s", exc)
            return {"ok": False, "message": f"İndirme başarısız: {exc}"}

        if sha256 and hasattr(updater, "verify_sha256"):
            if not updater.verify_sha256(path, sha256):
                return {"ok": False, "code": "sha_mismatch", "message": self.UPDATE_MESSAGES["sha_mismatch"]}

        try:
            updater.apply(path)
        except updater.UpdaterError as exc:
            return {"ok": False, "code": exc.code, "message": self.UPDATE_MESSAGES.get(exc.code, "Kurulum başlatılamadı.")}
        except Exception as exc:
            return {"ok": False, "message": f"Kurulum başlatılamadı: {exc}"}

        return {"ok": True, "message": f"Sürüm {version} kurulumu başlatıldı; uygulama kapanacak."}

    # ---------- karşılama sihirbazı (Faz 4.4) ----------

    def wizard_status(self) -> dict:
        setup_done = bool(self.settings.get("setup_done", False))
        cuda_cnt = 0
        try:
            cuda_cnt = diagnostics.cuda_device_count()
        except Exception:
            pass
        cuda_ready = cuda_cnt > 0
        has_gpu = cuda_ready
        if not has_gpu:
            try:
                import pynvml
                pynvml.nvmlInit()
                has_gpu = pynvml.nvmlDeviceGetCount() > 0
            except Exception:
                try:
                    import shutil, subprocess
                    if shutil.which("nvidia-smi"):
                        r = subprocess.run(["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                        has_gpu = (r.returncode == 0)
                except Exception:
                    pass

        models_info = self.models_list()
        return {
            "ok": True,
            "setup_done": setup_done,
            "has_nvidia_gpu": has_gpu,
            "cuda_ready": cuda_ready,
            "models": models_info.get("items", []),
            "active_model": models_info.get("active_model", AUTO_MODEL),
            "design_style": str(self.settings.get("design_style", "dikte_ai")),
            "hotkey": self._hotkey_id,
            "hotkey_label": hotkey_label(self._hotkey_id),
        }

    def wizard_complete(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        changes = {"setup_done": True}
        if "design_style" in payload:
            changes["design_style"] = str(payload["design_style"])
        if "active_model" in payload:
            changes["active_model"] = str(payload["active_model"])
        if "hotkey" in payload:
            changes["hotkey"] = str(payload["hotkey"])
        if "save_history" in payload:
            changes["save_history"] = bool(payload["save_history"])

        if "hotkey" in payload and payload["hotkey"] != self._hotkey_id:
            set_key = getattr(self.hotkey, "set_key", None)
            if set_key is not None:
                try:
                    set_key(payload["hotkey"])
                except Exception as exc:
                    logger.warning("Sihirbazda kısayol ayarlanamadı: %s", exc)

        if "active_model" in payload and payload["active_model"] != AUTO_MODEL:
            try:
                if self.models.installed(payload["active_model"]):
                    if hasattr(self.engine, "set_model"):
                        self.engine.set_model(payload["active_model"])
            except Exception:
                pass

        try:
            self.settings.save(**changes)
        except Exception as exc:
            logger.warning("Sihirbaz ayarları kaydedilemedi: %s", exc)
            return {"ok": False, "message": str(exc)}

        with self._lock:
            if "hotkey" in changes:
                self._hotkey_id = str(changes["hotkey"])
            self._add_activity("Kurulum sihirbazı tamamlandı", "Ayarlar kaydedildi.", "ok")

        return {"ok": True, "message": "Kurulum tamamlandı.", "settings": self.settings_get()}

    def maybe_startup_update_check(self) -> None:
        """Açılışta sessiz sürüm denetimi.
        Yalnız kurulu (PyInstaller) sürümde ve ayar açıksa çalışır;
        hata olursa uygulama çalışmaya devam eder.
        """
        if not config.is_packaged():
            return
        if not self.settings.get("update_check_on_start", True):
            return
        threading.Thread(
            target=self.update_check, kwargs={"force": False}, daemon=True
        ).start()

    def openrouter_key_save(self, key: str) -> dict:
        try:
            masked = self.secrets.save_key(key)
        except SecretError as exc:
            return {"ok": False, "message": str(exc)}
        except Exception as exc:
            logger.exception("Anahtar kaydedilemedi")
            return {"ok": False, "message": f"Anahtar kaydedilemedi: {exc}"}
        self._key_cache = (True, (key or "").strip())
        return {"ok": True, "message": "Anahtar kaydedildi.", "masked": masked, "ai": self.ai_state()}

    def openrouter_key_delete(self) -> dict:
        try:
            self.secrets.delete_key()
        except SecretError as exc:
            return {"ok": False, "message": str(exc)}
        self._key_cache = (True, None)
        return {"ok": True, "message": "Anahtar silindi.", "ai": self.ai_state()}

    def openrouter_key_test(self) -> dict:
        key = self._openrouter_key(refresh=True)
        if not key:
            return {"ok": False, "code": "no_key", "message": text_engine.CODE_MESSAGES["no_key"]}
        try:
            models = openrouter.fetch_models(key)
        except openrouter.OpenRouterError as exc:
            return {
                "ok": False,
                "code": exc.code,
                "message": text_engine.CODE_MESSAGES.get(exc.code, str(exc)),
            }
        except Exception as exc:
            logger.exception("Anahtar testi başarısız")
            return {"ok": False, "code": "net", "message": text_engine.CODE_MESSAGES["net"]}
        return {"ok": True, "message": f"Bağlantı çalışıyor ({len(models)} model)."}

    def openrouter_models(
        self,
        refresh: bool = False,
        all_models: bool = False,
        query: str = "",
    ) -> dict:
        """Model listesi. `all_models` açıksa tüm katalog, kapalıysa ucuz öneriler."""
        try:
            models = self._model_lister(refresh=refresh, all_models=all_models)
        except openrouter.OpenRouterError as exc:
            return {
                "ok": False,
                "code": exc.code,
                "message": text_engine.CODE_MESSAGES.get(exc.code, str(exc)),
                "models": [],
            }
        except Exception as exc:
            logger.warning("Model listesi alınamadı: %s", exc)
            return {"ok": False, "code": "net", "message": "Model listesi alınamadı.", "models": []}
        models = openrouter.search(models, query)
        items = [
            {
                "id": model["id"],
                "name": model["name"],
                "price_label": f"~${model['input_price']:.2f} / ${model['output_price']:.2f}",
                "context_label": f"{model['context'] // 1000}K bağlam",
            }
            for model in models[:400]
        ]
        return {"ok": True, "models": items, "total": len(items)}

    def clean_text(self, text: str) -> dict:
        """Metni konuşulan dilde düzeltir; çeviri yapmaz."""
        return self._run_text(text, translate=False)

    def translate_text(self, text: str) -> dict:
        """Metni düzeltir ve seçili çıktı diline çevirir."""
        return self._run_text(text, translate=True)

    def ai_cancel(self) -> dict:
        self._ai_cancel_event.set()
        with self._lock:
            if self._machine.state == CLEANING:
                self._set_state(READY)
                self._add_activity("Yapay zeka iptal edildi", "İşlem kullanıcı tarafından durduruldu.", "warn")
        return {"ok": True, "message": "İptal edildi."}

    def clean_text_async(self, text: str) -> dict:
        return self.ai_start_task("clean", text)

    def translate_text_async(self, text: str) -> dict:
        return self.ai_start_task("translate", text)

    def ai_start_task(self, mode: str, text: str) -> dict:
        with self._lock:
            if self._machine.state != READY:
                return {"ok": False, "message": "Şu anda işlenemez, lütfen bekle."}
            if self._provider() == "none":
                return {"ok": False, "code": "provider_off", "message": text_engine.CODE_MESSAGES["provider_off"]}
            self._ai_cancel_event.clear()
            self._set_state(CLEANING)

        def worker() -> None:
            translate = (mode == "translate")
            try:
                res = self._process_text(text, translate)
                if self._ai_cancel_event.is_set():
                    return
                copy_ok = True
                try:
                    self._clipper(res.text)
                except ClipboardError:
                    copy_ok = False
                self._update_history_text(res.text)
                pasted = False
                if copy_ok and bool(self.settings.get("auto_paste", True)):
                    try:
                        time.sleep(0.05)
                        pasted = bool(self._paster())
                    except Exception as exc:
                        logger.warning("Otomatik yapıştırma hatası: %s", exc)
                with self._lock:
                    if not self._ai_cancel_event.is_set():
                        self._latest = res.text
                        self._add_activity(
                            "Metin çevrildi" if translate and not res.unchanged else "Metin düzenlendi",
                            f"{text_engine.count_words(res.text)} kelime",
                            "ok",
                        )
                        if pasted:
                            self._add_activity("Etkin pencereye yapıştırıldı", "Otomatik yapıştırma açık.", "info")
            except Exception as exc:
                logger.warning("AI async hatası: %s", exc)
                with self._lock:
                    if not self._ai_cancel_event.is_set():
                        self._add_activity("Metin işlenemedi", str(exc), "err")
            finally:
                with self._lock:
                    if self._machine.state == CLEANING:
                        self._set_state(READY)

        self._ai_worker = threading.Thread(target=worker, name="ai-task", daemon=True)
        self._ai_worker.start()
        return {"ok": True, "state": CLEANING}

    def _run_text(self, text: str, translate: bool) -> dict:
        text = (text or "").strip()
        if not text:
            return {
                "ok": False,
                "code": "empty_text",
                "message": text_engine.CODE_MESSAGES["empty_text"],
            }
        if self._provider() == "none":
            return {
                "ok": False,
                "code": "provider_off",
                "message": text_engine.CODE_MESSAGES["provider_off"],
            }
        with self._lock:
            if self._machine.state != READY:
                return {"ok": False, "message": "Şu anda işlenemez, lütfen bekle."}
            self._error = None
            self._ai_cancel_event.clear()
            self._set_state(CLEANING)
        try:
            result = self._process_text(text, translate)
        except text_engine.TextEngineError as exc:
            logger.warning("Metin işlenemedi (%s): %s", exc.code, exc)
            with self._lock:
                self._add_activity("Metin işlenemedi", str(exc), "err")
            return {"ok": False, "code": exc.code, "message": str(exc)}
        except Exception as exc:
            logger.exception("Metin işlemi beklenmedik hata")
            with self._lock:
                self._add_activity("Metin işlenemedi", str(exc), "err")
            return {
                "ok": False,
                "code": "bad_response",
                "message": text_engine.CODE_MESSAGES["bad_response"],
            }
        finally:
            with self._lock:
                if self._machine.state == CLEANING:
                    self._set_state(READY)

        if self._ai_cancel_event.is_set():
            return {
                "ok": False,
                "cancelled": True,
                "code": "cancelled",
                "message": "İşlem iptal edildi.",
            }

        copy_ok = True
        try:
            self._clipper(result.text)
        except ClipboardError:
            copy_ok = False
        self._update_history_text(result.text)
        message = "Metin çevrildi." if translate else "Metin düzenlendi."
        if result.unchanged and translate:
            message = "Metin değişmedi; model çeviri yapmadı. Farklı bir model dene."
        with self._lock:
            self._latest = result.text
            self._add_activity(
                "Metin çevrildi" if translate and not result.unchanged else "Metin düzenlendi",
                f"{text_engine.count_words(result.text)} kelime",
                "ok",
            )
            if result.unchanged and translate:
                self._add_activity("Çeviri yapılmadı", "Model metni değiştirmedi.", "warn")
            if not copy_ok:
                self._add_activity("Panoya kopyalanamadı", "Kopyala düğmesini dene.", "err")
        return {
            "ok": True,
            "text": result.text,
            "translated": result.translated,
            "unchanged": result.unchanged,
            "message": message,
        }

    def _process_text(self, text: str, translate: bool) -> "text_engine.TextResult":
        provider = self._provider()
        if provider == "local":
            return self._local_process_text(text, translate)
        key = self._openrouter_key() if provider == "openrouter" else None
        model = self.settings.get("openrouter_model") if provider == "openrouter" else None
        return self._text_processor(
            text,
            target_language=str(self.settings.get("output_language", "tr")),
            translate=translate,
            provider=provider,
            api_key=key,
            model=model,
            system_prompt=str(self.settings.get("system_prompt") or config.DEFAULT_SYSTEM_PROMPT),
        )

    def _local_process_text(self, text: str, translate: bool) -> "text_engine.TextResult":
        name = str(self.settings.get("text_model", ""))
        try:
            spec = text_models.get_text_model(name)
        except text_models.TextModelError as exc:
            raise text_engine.TextEngineError("local_missing") from exc
        if not text_models.is_installed(name):
            raise text_engine.TextEngineError("local_missing")
        if not LocalTextModel.available():
            raise text_engine.TextEngineError(
                "local_load", "Yerel metin motoru (llama.cpp) kurulu değil. OpenRouter sağlayıcısını seç."
            )
        if self._text_runtime.model_name != name:
            self._unload_whisper()
            try:
                device = self._text_runtime.load(name, prefer_gpu=True)
            except Exception as exc:
                raise text_engine.TextEngineError("local_load") from exc
            with self._lock:
                self._add_activity("Metin modeli yüklendi", f"{spec.label} · {device}", "info")

        target = str(self.settings.get("output_language", "tr"))
        prompt = str(self.settings.get("system_prompt") or config.DEFAULT_SYSTEM_PROMPT)
        budget = max(512, text_engine.count_words(text) * 8 + 256)
        messages = text_engine.build_messages(text, target, translate, prompt, strict=False)
        last_error = None
        for attempt in range(2):
            raw = self._text_runtime.generate(
                messages[0]["content"], messages[1]["content"], max_tokens=budget
            )
            candidate = text_engine.strip_response(raw)
            try:
                text_engine.validate_output(text, candidate, translate, target)
            except text_engine.TextEngineError as exc:
                last_error = exc
                if attempt == 0:
                    messages = text_engine.build_messages(
                        text, target, translate, prompt, strict=True
                    )
                    budget = max(1024, budget * 2)
                    continue
                raise
            same = (
                translate
                and text_engine.count_words(text) >= 3
                and candidate.strip().lower() == text.strip().lower()
            )
            if same and attempt == 0:
                messages = text_engine.build_messages(
                    text, target, translate, prompt, strict=True
                )
                budget = max(1024, budget * 2)
                continue
            return text_engine.TextResult(
                text=candidate, translated=bool(translate) and not same, unchanged=same
            )
        raise last_error or text_engine.TextEngineError("bad_response")

    def _auto_ai_text(self, text: str) -> str:
        """Otomatik çevir açıksa dikte sonrası metni temizler/çevirir."""
        if not bool(self.settings.get("auto_translate", False)):
            return text
        provider = self._provider()
        if provider == "none":
            with self._lock:
                self._add_activity(
                    "Otomatik çeviri atlandı",
                    "Yapay zeka sağlayıcısı seçilmedi (Ayarlar → Yapay Zeka'dan seçin).",
                    "warn",
                )
            return text
        if not text_engine.should_translate_auto(text):
            with self._lock:
                self._add_activity("Kısa metin", "Çeviri atlandı (3 kelimeden kısa).", "warn")
            return text
        try:
            result = self._process_text(text, translate=True)
        except text_engine.TextEngineError as exc:
            with self._lock:
                self._add_activity("Otomatik çeviri yapılamadı", str(exc), "err")
            return text
        except Exception as exc:
            logger.exception("Otomatik çeviri hatası: %s", exc)
            return text
        if not result.text or result.text == text:
            if result.unchanged:
                with self._lock:
                    self._add_activity(
                        "Çeviri yapılmadı", "Model metni değiştirmedi; farklı model dene.", "warn"
                    )
            return text
        try:
            self._clipper(result.text)
            self._last_ai_copy_ok = True
        except ClipboardError:
            self._last_ai_copy_ok = False
        with self._lock:
            self._add_activity("Metin düzenlendi", "Temizlik ve çeviri uygulandı.", "ok")
        return result.text

    def _update_history_text(self, text: str) -> None:
        if not self._save_history or not self._last_history_id:
            return
        try:
            self.history.update_text(self._last_history_id, text)
        except Exception as exc:
            logger.warning("Geçmiş güncellenemedi: %s", exc)

    # ---------- yardımcılar ----------

    @staticmethod
    def _default_clipper(text: str) -> None:
        from .clipboard import copy_text

        copy_text(text)

    def _memory(self, info) -> dict | None:
        if info is None:
            return None
        now = time.monotonic()
        cached_at, cached_value = self._memory_cache
        if now - cached_at < 1.0:
            return cached_value
        try:
            value = self._memory_provider(info.device == "GPU")
        except Exception as exc:
            logger.debug("Bellek okunamadı: %s", exc)
            value = None
        self._memory_cache = (now, value)
        return value

    def _set_state(self, new_state: str) -> None:
        if new_state not in ALLOWED.get(self._machine.state, set()):
            logger.warning("Geçersiz durum geçişi: %s -> %s", self._machine.state, new_state)
            return
        try:
            self._machine.set(new_state)
        except InvalidTransition:
            logger.warning("Durum değiştirilemedi: %s", new_state)

    def _add_activity(self, title: str, sub: str, kind: str = "info") -> None:
        self._activity.appendleft(
            {
                "time": datetime.now().strftime("%H:%M"),
                "title": title,
                "sub": sub,
                "kind": kind,
            }
        )
