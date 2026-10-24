import threading
import time
from pathlib import Path

import pytest

from dikte import config, diagnostics
from dikte.audio import AudioError, Recording
from dikte.clipboard import ClipboardError
from dikte.controller import Controller, format_duration
from dikte.engine import EngineError, EngineInfo, TranscriptResult
from dikte.state import ERROR, PROCESSING, READY, RECORDING


class FakeEngine:
    def __init__(self, text="Merhaba dünya.", fail_load=False, fail_transcribe=False, gate=None):
        self.text = text
        self.fail_load = fail_load
        self.fail_transcribe = fail_transcribe
        self.gate = gate
        self.transcribe_calls = 0
        self.warnings = []

    def load(self):
        if self.fail_load:
            raise EngineError(diagnostics.MSG_MODEL_MISSING, kind="model_missing")
        return EngineInfo("large-v3", "Whisper Large", "GPU", "float16", 0.1)

    def transcribe(self, wav_path):
        self.transcribe_calls += 1
        if self.gate is not None:
            self.gate.wait(timeout=3)
        if self.fail_transcribe:
            raise EngineError(diagnostics.MSG_TRANSCRIBE_FAILED, kind="transcribe")
        return TranscriptResult(self.text, 1.0, 0.1)


class FakeRecorder:
    def __init__(self, duration=2.0, fail_start=False):
        self.duration = duration
        self.fail_start = fail_start
        self.recording = False
        self.cleaned = []
        self.path = None

    def start(self):
        if self.fail_start:
            raise AudioError(diagnostics.MSG_MIC_MISSING)
        self.recording = True

    def stop(self):
        self.recording = False
        self.path = Path(config.TEMP_DIR) / f"test-{time.time_ns()}.wav"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(b"RIFF-test")
        return Recording(path=self.path, duration=self.duration, frames=int(self.duration * 16000))

    def cancel(self):
        self.recording = False

    def cleanup(self, path):
        self.cleaned.append(path)
        if path:
            Path(path).unlink(missing_ok=True)


class FakeHotkey:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


def make_controller(**kwargs):
    recorder = kwargs.pop("recorder", FakeRecorder())
    engine = kwargs.pop("engine", FakeEngine())
    clipboard = kwargs.pop("clipper", lambda text: None)
    controller = Controller(
        engine=engine,
        recorder=recorder,
        hotkey=FakeHotkey(),
        clipper=clipboard,
        beeper=lambda kind: None,
        memory_provider=lambda use_gpu: {
            "used": 4.8,
            "total": 12.0,
            "unit": "GB",
            "source": "VRAM" if use_gpu else "RAM",
            "percent": 40.0,
        },
        load_in_background=False,
        **kwargs,
    )
    controller.load_engine()
    return controller


def test_load_engine_makes_controller_ready():
    controller = make_controller()
    snapshot = controller.snapshot()
    assert snapshot["state"] == READY
    assert snapshot["model"] == "Whisper Large"
    assert snapshot["device"] == "GPU"
    assert snapshot["memory"]["used"] == 4.8
    assert snapshot["activity"][0]["title"] == "Model yüklendi"


def test_load_failure_sets_error():
    controller = make_controller(engine=FakeEngine(fail_load=True))
    snapshot = controller.snapshot()
    assert snapshot["state"] == ERROR
    assert "Model bulunamadı" in snapshot["error"]


def test_full_dictation_flow_copies_text_and_cleans_wav():
    copied = []
    recorder = FakeRecorder(duration=2.0)
    controller = make_controller(recorder=recorder, clipper=copied.append)

    result = controller.toggle_record()
    assert result["ok"] is True
    assert controller.snapshot()["state"] == RECORDING

    result = controller.toggle_record()
    assert result["state"] == PROCESSING
    assert controller.wait_until_ready(3)

    snapshot = controller.snapshot()
    assert snapshot["state"] == READY
    assert snapshot["seq"] == 1
    assert snapshot["latest_text"] == "Merhaba dünya."
    assert copied == ["Merhaba dünya."]
    assert snapshot["activity"][0]["title"] == "Dikte tamamlandı"
    assert recorder.path is not None and not recorder.path.exists()
    assert recorder.cleaned


def test_short_recording_is_skipped():
    recorder = FakeRecorder(duration=0.2)
    engine = FakeEngine()
    controller = make_controller(recorder=recorder, engine=engine)

    controller.toggle_record()
    result = controller.toggle_record()
    assert result.get("skipped") is True
    snapshot = controller.snapshot()
    assert snapshot["state"] == READY
    assert snapshot["seq"] == 0
    assert engine.transcribe_calls == 0
    assert snapshot["activity"][0]["title"] == "Ses algılanamadı"
    assert not recorder.path.exists()


def test_empty_transcription_does_not_add_text():
    controller = make_controller(engine=FakeEngine(text="   "))
    controller.toggle_record()
    controller.toggle_record()
    assert controller.wait_until_ready(3)
    snapshot = controller.snapshot()
    assert snapshot["seq"] == 0
    assert snapshot["state"] == READY
    assert snapshot["activity"][0]["title"] == "Ses algılanamadı"


def test_transcription_error_then_retry():
    controller = make_controller(engine=FakeEngine(fail_transcribe=True))
    controller.toggle_record()
    controller.toggle_record()
    assert controller.wait_until_ready(3)
    snapshot = controller.snapshot()
    assert snapshot["state"] == ERROR
    assert "Yazıya çevirme" in snapshot["error"]

    # Hata durumunda tekrar basınca yeniden kayıt başlar.
    controller.engine.fail_transcribe = False
    result = controller.toggle_record()
    assert result["ok"] is True
    assert controller.snapshot()["state"] == RECORDING
    controller.toggle_record()
    assert controller.wait_until_ready(3)
    assert controller.snapshot()["seq"] == 1


def test_second_recording_starts_new_dictation():
    controller = make_controller(engine=FakeEngine(text="Birinci."))
    controller.toggle_record()
    controller.toggle_record()
    assert controller.wait_until_ready(3)

    controller.engine.text = "İkinci."
    controller.toggle_record()
    controller.toggle_record()
    assert controller.wait_until_ready(3)

    snapshot = controller.snapshot()
    assert snapshot["seq"] == 2
    assert snapshot["latest_text"] == "İkinci."


def test_requests_while_processing_are_rejected():
    gate = threading.Event()
    controller = make_controller(engine=FakeEngine(gate=gate))
    controller.toggle_record()
    controller.toggle_record()
    assert controller.snapshot()["state"] == PROCESSING

    result = controller.toggle_record()
    assert result["ok"] is False
    assert controller.snapshot()["state"] == PROCESSING

    gate.set()
    assert controller.wait_until_ready(3)
    assert controller.snapshot()["state"] == READY


def test_microphone_error_sets_error_and_recovers():
    controller = make_controller(recorder=FakeRecorder(fail_start=True))
    result = controller.toggle_record()
    assert result["ok"] is False
    assert controller.snapshot()["state"] == ERROR
    assert "Mikrofon" in controller.snapshot()["error"]


def test_clipboard_error_keeps_text():
    def broken_copy(_text):
        raise ClipboardError("pano yok")

    controller = make_controller(clipper=broken_copy)
    controller.toggle_record()
    controller.toggle_record()
    assert controller.wait_until_ready(3)
    snapshot = controller.snapshot()
    assert snapshot["seq"] == 1
    assert snapshot["state"] == READY
    titles = [item["title"] for item in snapshot["activity"]]
    assert "Panoya kopyalanamadı" in titles


def test_copy_validates_empty_text():
    controller = make_controller()
    assert controller.copy("")["ok"] is False
    assert controller.copy("  ")["ok"] is False
    assert controller.copy("deneme")["ok"] is True


def test_gpu_failure_falls_back_to_cpu_once():
    engine = FakeEngine(fail_transcribe=True)

    def use_cpu_fallback():
        engine.fail_transcribe = False
        engine.text = "CPU üzerinden metin."
        return EngineInfo("small", "Whisper Small", "CPU", "int8", 0.0)

    engine.use_cpu_fallback = use_cpu_fallback
    controller = make_controller(engine=engine)
    controller.toggle_record()
    controller.toggle_record()
    assert controller.wait_until_ready(3)

    snapshot = controller.snapshot()
    assert snapshot["state"] == READY
    assert snapshot["device"] == "CPU"
    assert snapshot["latest_text"] == "CPU üzerinden metin."
    titles = [item["title"] for item in snapshot["activity"]]
    assert "GPU kullanılamadı" in titles


def test_hotkey_press_and_release_use_same_flow():
    controller = make_controller()
    controller.on_hotkey_press()
    assert controller.snapshot()["state"] == RECORDING
    controller.on_hotkey_release()
    assert controller.wait_until_ready(3)
    assert controller.snapshot()["seq"] == 1


@pytest.mark.parametrize(
    "seconds,expected",
    [(0, "0 sn"), (12, "12 sn"), (60, "1 dk 00 sn"), (154, "2 dk 34 sn")],
)
def test_format_duration(seconds, expected):
    assert format_duration(seconds) == expected
