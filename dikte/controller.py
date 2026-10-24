"""Uygulamanın beyni: durum, kayıt, çeviri, pano ve etkinlikler."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from datetime import datetime

from . import config, diagnostics
from .audio import AudioError, AudioRecorder, Recording
from .clipboard import ClipboardError
from .engine import EngineError, TranscriptionEngine
from .hotkey import HotkeyError, HotkeyListener
from .state import (
    ALLOWED,
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
    ) -> None:
        self.engine = engine if engine is not None else TranscriptionEngine()
        self.recorder = recorder if recorder is not None else AudioRecorder()
        self.hotkey = (
            hotkey
            if hotkey is not None
            else HotkeyListener(self.on_hotkey_press, self.on_hotkey_release)
        )
        self._clipper = clipper if clipper is not None else self._default_clipper
        self._beeper = beeper if beeper is not None else _default_beep
        self._memory_provider = memory_provider or diagnostics.read_memory
        self._load_in_background = load_in_background

        self._machine = StateMachine(LOADING)
        self._lock = threading.RLock()
        self._info = None
        self._error: str | None = None
        self._activity: deque[dict] = deque(maxlen=7)
        self._seq = 0
        self._latest = ""
        self._worker: threading.Thread | None = None
        self._closed = False
        self._memory_cache: tuple[float, dict | None] = (0.0, None)
        self._gpu_warning_shown = False

    # ---------- yaşam döngüsü ----------

    def start(self) -> None:
        """Motoru arka planda yükler ve kısayolu başlatır."""
        if self._load_in_background:
            threading.Thread(target=self.load_engine, name="motor-yukle", daemon=True).start()
        try:
            self.hotkey.start()
        except HotkeyError as exc:
            logger.warning("Kısayol başlatılamadı: %s", exc)
            with self._lock:
                self._add_activity("Kısayol başlatılamadı", str(exc), "err")

    def load_engine(self) -> None:
        with self._lock:
            if self._info is not None:
                return
        try:
            info = self.engine.load()
        except Exception as exc:
            message = str(exc) if isinstance(exc, EngineError) else diagnostics.MSG_MODEL_MISSING
            logger.error("Motor yüklenemedi: %s", exc)
            with self._lock:
                self._error = message
                self._set_state(ERROR)
                self._add_activity("Model yüklenemedi", message, "err")
            return

        with self._lock:
            self._info = info
            self._error = None
            self._set_state(READY)
            self._add_activity(
                "Model yüklendi",
                f"{info.model_label} · {info.device} · {info.compute_type}",
                "info",
            )
            warnings = list(getattr(self.engine, "warnings", []) or [])
            if warnings and not self._gpu_warning_shown:
                self._gpu_warning_shown = True
                self._add_activity("GPU kullanılamadı", "CPU modu (small, int8)", "warn")
        logger.info("Model hazır: %s (%s)", info.model_label, info.device)

    def shutdown(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        try:
            self.hotkey.stop()
        except Exception:
            pass
        try:
            self.recorder.cancel()
        except Exception:
            pass
        logger.info("Uygulama kapatıldı")

    # ---------- kısayol ve düğme ----------

    def on_hotkey_press(self) -> None:
        self.toggle_record()

    def on_hotkey_release(self) -> None:
        self._stop_recording(trigger="kısayol")

    def toggle_record(self) -> dict:
        """Mikrofon düğmesi için başlat/durdur."""
        with self._lock:
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

    # ---------- çeviri işçisi ----------

    def _transcribe(self, recording: Recording):
        """GPU çevirisi çökerse bir kez CPU yedeğini dener."""
        try:
            return self.engine.transcribe(recording.path)
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
                self._add_activity("GPU kullanılamadı", "CPU moduna geçildi (small, int8)", "warn")
            return self.engine.transcribe(recording.path)

    def _process(self, recording: Recording) -> None:
        try:
            result = self._transcribe(recording)
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

            with self._lock:
                self._latest = text
                self._seq += 1
                self._error = None
                words = len(text.split())
                self._add_activity(
                    "Dikte tamamlandı",
                    f"({format_duration(recording.duration)}) · {words} kelime",
                    "ok",
                )
                if not copy_ok:
                    self._add_activity("Panoya kopyalanamadı", "Kopyala düğmesini dene.", "err")
        except Exception as exc:
            logger.exception("Çeviri başarısız: %s", exc)
            with self._lock:
                self._error = (
                    str(exc) if isinstance(exc, EngineError) else diagnostics.MSG_TRANSCRIBE_FAILED
                )
                self._set_state(ERROR)
                self._add_activity("Çeviri hatası", self._error, "err")
        finally:
            self.recorder.cleanup(recording.path)
            with self._lock:
                # Başarılı veya boş sonuçta işlem biter; hata durumunda ERROR korunur.
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
                "model": info.model_label if info else None,
                "model_name": info.model_name if info else None,
                "device": info.device if info else None,
                "compute": info.compute_type if info else None,
                "memory": self._memory(info),
                "activity": [dict(item) for item in self._activity],
                "error": self._error,
                "hotkey": config.HOTKEY_LABEL,
                "language": config.LANGUAGE_LABEL,
            }

    def wait_until_ready(self, timeout: float = 5.0) -> bool:
        """Testler ve konsol aracı için: işlem bitene kadar bekler."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.snapshot()["state"] != PROCESSING:
                return True
            time.sleep(0.02)
        return False

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
