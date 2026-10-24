"""Mikrofon kaydı: 16 kHz mono, geçici .wav dosyası."""

from __future__ import annotations

import logging
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
        self._recording = False
        self._started_at = 0.0

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
        self._chunks = []

        def callback(indata, frames, _time_info, status) -> None:
            if status:
                logger.debug("Ses akışı uyarısı: %s", status)
            self._chunks.append(bytes(indata))

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

        data = b"".join(self._chunks)
        self._chunks = []
        frame_count = len(data) // 2  # int16 = 2 bayt
        duration = frame_count / float(self.sample_rate)
        wall_clock = time.perf_counter() - self._started_at
        logger.info("Kayıt durdu | süre=%.2f sn | akış=%.2f sn", duration, wall_clock)

        if frame_count == 0:
            return Recording(path=None, duration=0.0, frames=0)

        path = self.temp_dir / f"kayit-{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1_000_000}.wav"
        self._write_wav(path, data)
        return Recording(path=path, duration=round(duration, 2), frames=frame_count)

    def cancel(self) -> None:
        """Kaydı yazmadan iptal eder."""
        self._recording = False
        self._safe_close()
        self._chunks = []

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
