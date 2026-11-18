"""Mikrofon kaydı: 16 kHz mono, geçici .wav dosyası."""

from __future__ import annotations

import logging
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path

from . import config, diagnostics

logger = logging.getLogger(__name__)


class AudioError(RuntimeError):
    pass


@dataclass
class Recording:
    path: Path | None
    duration: float
    frames: int


class AudioRecorder:
    def __init__(self, sample_rate: int = config.SAMPLE_RATE, temp_dir: Path | None = None) -> None:
        self.sample_rate = sample_rate
        self.temp_dir = Path(temp_dir or config.TEMP_DIR)
        self._stream = None
        self._chunks: list[bytes] = []
        self._chunks_lock = threading.Lock()
        self._recording = False
        self._started_at = 0.0
        self._max_frames = int(self.sample_rate * getattr(config, "MAX_RECORD_SECONDS", 600))
        self._recorded_frames = 0
        self._max_duration_reached = False
        self._stream_error: str | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        if self._recording:
            return
        try:
            import sounddevice as sd
        except Exception as exc:
            logger.exception("sounddevice yüklenemedi")
            raise AudioError(diagnostics.MSG_MIC_MISSING) from exc

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        with self._chunks_lock:
            self._chunks = []
            self._recorded_frames = 0
            self._max_duration_reached = False
            self._stream_error = None

        def callback(indata, frames, _time_info, status) -> None:
            if status:
                logger.warning("Ses akışı uyarısı: %s", status)
                if getattr(status, "input_overflow", False):
                    logger.warning("Ses akışında tampon taşması (input_overflow) oluştu.")
                if getattr(status, "error", False):
                    with self._chunks_lock:
                        self._stream_error = f"Ses akışı kritik hata verdi: {status}"
                    return
            try:
                chunk = bytes(indata)
            except Exception as exc:
                logger.warning("Ses verisi okunamadı: %s", exc)
                with self._chunks_lock:
                    self._stream_error = "Ses akışı kritik hata verdi."
                return
            with self._chunks_lock:
                if self._recorded_frames >= self._max_frames:
                    if not self._max_duration_reached:
                        self._max_duration_reached = True
                        logger.warning(
                            "Maksimum kayıt süresine (%s sn) ulaşıldı; yeni ses parçaları alınmıyor.",
                            getattr(config, "MAX_RECORD_SECONDS", 600),
                        )
                    return
                self._chunks.append(chunk)
                self._recorded_frames += len(chunk) // 2

        try:
            self._stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                channels=config.CHANNELS,
                dtype="int16",
                blocksize=800,
                callback=callback,
            )
            self._stream.start()
        except Exception as exc:
            self._safe_close()
            logger.exception("Mikrofon açılamadı")
            raise AudioError(diagnostics.MSG_MIC_MISSING) from exc

        self._recording = True
        self._started_at = time.perf_counter()
        logger.info("Kayıt başladı")

    def stop(self) -> Recording | None:
        if not self._recording:
            return None
        self._recording = False
        self._safe_close()

        with self._chunks_lock:
            data = b"".join(self._chunks)
            self._chunks = []
            self._recorded_frames = 0
            stream_error = self._stream_error
            self._stream_error = None
        if stream_error and not data:
            raise AudioError(stream_error)
        frame_count = len(data) // 2  # int16 = 2 bayt
        duration = frame_count / float(self.sample_rate)
        wall_clock = time.perf_counter() - self._started_at
        logger.info("Kayıt durdu | süre=%.2f sn | akış=%.2f sn", duration, wall_clock)

        if frame_count == 0:
            return Recording(path=None, duration=0.0, frames=0)

        path = self.temp_dir / f"kayit-{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1_000_000}.wav"
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self._write_wav(path, data)
        except Exception as exc:
            self.cleanup(path)
            logger.exception("Ses kaydı diske yazılamadı")
            raise AudioError("Ses kaydı diske yazılamadı.") from exc
        return Recording(path=path, duration=round(duration, 2), frames=frame_count)

    def cancel(self) -> None:
        """Kaydı yazmadan iptal eder."""
        self._recording = False
        self._safe_close()
        with self._chunks_lock:
            self._chunks = []
            self._recorded_frames = 0
            self._stream_error = None

    def _write_wav(self, path: Path, data: bytes) -> None:
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(config.CHANNELS)
            handle.setsampwidth(2)
            handle.setframerate(self.sample_rate)
            handle.writeframes(data)

    def _safe_close(self) -> None:
        stream = self._stream
        self._stream = None
        if stream is None:
            return
        try:
            stream.stop()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    @staticmethod
    def cleanup(path: Path | None) -> None:
        """Geçici ses dosyasını siler."""
        if not path:
            return
        try:
            Path(path).unlink(missing_ok=True)
            logger.info("Geçici ses dosyası silindi")
        except Exception as exc:
            logger.warning("Geçici dosya silinemedi: %s", exc)
