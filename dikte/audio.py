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

DEFAULT_INPUT_DEVICE = "default"
_SKIP_MAPPER_NAMES = frozenset(
    {
        "microsoft ses eşleştiricisi - input",
        "microsoft sound mapper - input",
        "birincil ses yakalama sürücüsü",
        "primary sound capture driver",
    }
)


def _clean_device_name(name: object) -> str:
    return " ".join(str(name or "").replace("\r", " ").replace("\n", " ").split())


def _hostapi_rank(hostapi_name: str) -> int:
    low = (hostapi_name or "").lower()
    if "wasapi" in low:
        return 0
    if "directsound" in low:
        return 1
    if "mme" in low:
        return 2
    if "wdm-ks" in low:
        return 4
    return 3


def list_input_devices() -> list[dict]:
    """Kullanılabilir giriş (mikrofon) cihazlarını döndürür; hata olursa yalnız varsayılan döner."""
    default_entry = {"id": DEFAULT_INPUT_DEVICE, "label": "Sistem Varsayılanı"}
    try:
        import sounddevice as sd
    except Exception:
        return [default_entry]
    if sd is None:
        return [default_entry]

    try:
        devices = sd.query_devices()
    except Exception as exc:
        logger.warning("Mikrofon listesi alınamadı: %s", exc)
        return [default_entry]

    hostapis: list[dict] = []
    query_hostapis = getattr(sd, "query_hostapis", None)
    if callable(query_hostapis):
        try:
            hostapis = list(query_hostapis() or [])
        except Exception:
            hostapis = []

    candidates: list[tuple[int, int, str]] = []
    for idx, dev in enumerate(devices or []):
        try:
            channels = int(dev.get("max_input_channels", 0) or 0)
        except Exception:
            channels = 0
        if channels <= 0:
            continue
        name = _clean_device_name(dev.get("name", ""))
        if not name:
            continue
        host_idx = dev.get("hostapi")
        host_name = ""
        if isinstance(host_idx, int) and 0 <= host_idx < len(hostapis):
            host_name = str(hostapis[host_idx].get("name", ""))
        candidates.append((_hostapi_rank(host_name), idx, name))

    non_wdm = [c for c in candidates if c[0] < 4]
    pool = non_wdm if non_wdm else candidates

    best_by_name: dict[str, tuple[int, int]] = {}
    for rank, idx, name in pool:
        if len(pool) > 1 and name.lower() in _SKIP_MAPPER_NAMES:
            continue
        prev = best_by_name.get(name)
        if prev is None or rank < prev[0]:
            best_by_name[name] = (rank, idx)

    if not best_by_name:
        for rank, idx, name in pool:
            if name not in best_by_name:
                best_by_name[name] = (rank, idx)

    ordered = sorted(best_by_name.items(), key=lambda kv: (kv[1][0], kv[1][1]))
    items = [default_entry]
    for name, _ in ordered:
        items.append({"id": name, "label": name})
    return items


class AudioError(RuntimeError):
    pass


@dataclass
class Recording:
    path: Path | None
    duration: float
    frames: int


class AudioRecorder:
    def __init__(
        self,
        sample_rate: int = config.SAMPLE_RATE,
        temp_dir: Path | None = None,
        device: str | int | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.temp_dir = Path(temp_dir or config.TEMP_DIR)
        self._device = self._normalize_device(device)
        self._stream = None
        self._chunks: list[bytes] = []
        self._chunks_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._recording = False
        self._started_at = 0.0
        self._max_frames = int(self.sample_rate * getattr(config, "MAX_RECORD_SECONDS", 600))
        self._recorded_frames = 0
        self._max_duration_reached = False
        self._stream_error: str | None = None
        self._last_callback_at: float = 0.0

    @staticmethod
    def _normalize_device(device: str | int | None) -> str:
        if device is None:
            return DEFAULT_INPUT_DEVICE
        text = str(device).strip()
        return text if text else DEFAULT_INPUT_DEVICE

    @property
    def device(self) -> str:
        with self._state_lock:
            return self._device

    def set_device(self, device: str | int | None) -> None:
        with self._state_lock:
            self._device = self._normalize_device(device)

    @staticmethod
    def _resolve_input_device(sd, device_spec: str) -> int | None:
        if not device_spec or device_spec == DEFAULT_INPUT_DEVICE:
            return None
        query_devices = getattr(sd, "query_devices", None)
        if not callable(query_devices):
            return None
        try:
            devices = list(query_devices() or [])
        except Exception as exc:
            logger.warning("Mikrofon cihazı doğrulanamadı (%s): %s", device_spec, exc)
            return None

        hostapis: list[dict] = []
        query_hostapis = getattr(sd, "query_hostapis", None)
        if callable(query_hostapis):
            try:
                hostapis = list(query_hostapis() or [])
            except Exception:
                hostapis = []

        matches: list[tuple[int, int]] = []
        target_clean = _clean_device_name(device_spec)
        for idx, dev in enumerate(devices):
            try:
                channels = int(dev.get("max_input_channels", 0) or 0)
            except Exception:
                channels = 0
            if channels <= 0:
                continue
            if _clean_device_name(dev.get("name", "")) == target_clean:
                host_idx = dev.get("hostapi")
                host_name = (
                    str(hostapis[host_idx].get("name", ""))
                    if isinstance(host_idx, int) and 0 <= host_idx < len(hostapis)
                    else ""
                )
                matches.append((_hostapi_rank(host_name), idx))

        if matches:
            matches.sort()
            return matches[0][1]

        if device_spec.isdigit():
            idx = int(device_spec)
            if 0 <= idx < len(devices):
                try:
                    if int(devices[idx].get("max_input_channels", 0) or 0) > 0:
                        return idx
                except Exception:
                    pass

        logger.warning(
            "Seçili mikrofon bulunamadı (%s); sistem varsayılanına dönülüyor.",
            device_spec,
        )
        return None

    @property
    def is_recording(self) -> bool:
        with self._state_lock:
            return self._recording

    def start(self) -> None:
        with self._state_lock:
            self._start_locked()

    def _start_locked(self) -> None:
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
            self._last_callback_at = time.monotonic()
            if status:
                logger.warning("Ses akışı uyarısı: %s", status)
                is_overflow = bool(getattr(status, "input_overflow", False))
                is_nonfatal_flag = bool(
                    getattr(status, "input_underflow", False)
                    or getattr(status, "output_underflow", False)
                    or getattr(status, "output_overflow", False)
                    or getattr(status, "priming_output", False)
                )
                if is_overflow:
                    logger.warning("Ses akışında tampon taşması (input_overflow) oluştu.")
                if getattr(status, "error", False) or (not is_overflow and not is_nonfatal_flag):
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

        selected_device = self._resolve_input_device(sd, self._device)
        stream_kwargs = {
            "samplerate": self.sample_rate,
            "channels": config.CHANNELS,
            "dtype": "int16",
            "blocksize": 800,
            "callback": callback,
        }
        if selected_device is not None:
            stream_kwargs["device"] = selected_device
        try:
            self._stream = sd.RawInputStream(**stream_kwargs)
            self._stream.start()
        except Exception as exc:
            self._safe_close()
            if selected_device is not None:
                logger.warning(
                    "Seçili mikrofon (%s) açılamadı (%s); sistem varsayılanı deneniyor.",
                    self._device,
                    exc,
                )
                try:
                    stream_kwargs.pop("device", None)
                    self._stream = sd.RawInputStream(**stream_kwargs)
                    self._stream.start()
                except Exception as fallback_exc:
                    self._safe_close()
                    logger.exception("Mikrofon açılamadı")
                    raise AudioError(diagnostics.MSG_MIC_MISSING) from fallback_exc
            else:
                logger.exception("Mikrofon açılamadı")
                raise AudioError(diagnostics.MSG_MIC_MISSING) from exc

        self._recording = True
        self._started_at = time.perf_counter()
        self._last_callback_at = time.monotonic()
        logger.info("Kayıt başladı")

    def stop(self) -> Recording | None:
        with self._state_lock:
            return self._stop_locked()

    def _stop_locked(self) -> Recording | None:
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
        with self._state_lock:
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
