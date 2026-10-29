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


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    """Testler gerçek data/, %TEMP% ve models/ klasörlerini kirletmesin."""
    monkeypatch.setattr(config, "TEMP_DIR", tmp_path / "temp")
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(config, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(config, "LAST_RECORDING", tmp_path / "last.wav")
    (tmp_path / "temp").mkdir(exist_ok=True)


class FakeEngine:
    def __init__(self, text="Merhaba dünya.", fail_load=False, fail_transcribe=False, gate=None):
        self.text = text
        self.fail_load = fail_load
        self.fail_transcribe = fail_transcribe
        self.gate = gate
        self.transcribe_calls = 0
        self.warnings = []
        self.model_name = None
        self.loaded_models = []
        self.fail_models = set()

    def set_model(self, name):
        self.model_name = name

    def unload(self):
        pass

    def load(self):
        if self.model_name in self.fail_models:
            raise EngineError(diagnostics.MSG_MODEL_MISSING, kind="model_missing")
        if self.fail_load:
            raise EngineError(diagnostics.MSG_MODEL_MISSING, kind="model_missing")
        name = self.model_name or "large-v3"
        self.loaded_models.append(name)
        return EngineInfo(name, config.model_label(name), "GPU", "float16", 0.1)

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
        self.key = "right_ctrl"
        self.fail_set = False

    def configure(self, key):
        self.key = key

    def set_key(self, key):
        if self.fail_set:
            from dikte.hotkey import HotkeyError

            raise HotkeyError("Kısayol değiştirilemedi.")
        self.key = key

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


def make_controller(**kwargs):
    recorder = kwargs.pop("recorder", FakeRecorder())
    engine = kwargs.pop("engine", FakeEngine())
    hotkey = kwargs.pop("hotkey", FakeHotkey())
    clipboard = kwargs.pop("clipper", lambda text: None)
    controller = Controller(
        engine=engine,
        recorder=recorder,
        hotkey=hotkey,
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


def wait_for_state(controller, state, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if controller.snapshot()["state"] == state:
            return True
        time.sleep(0.02)
    return False


class FakeModels:
    def __init__(self, installed=("large-v3", "small")):
        from dikte.models import SPEECH_MODELS

        self.available = set(installed)
        self.specs = {model.name: model for model in SPEECH_MODELS}
        self.deleted = []
        self.downloads = []

    def installed(self, name):
        return name in self.available

    def size(self, name):
        return 1000 if name in self.available else 0

    def scan(self):
        items = {}
        for name, spec in self.specs.items():
            installed = name in self.available
            items[name] = {
                "name": name,
                "label": spec.label,
                "desc": spec.desc,
                "tags": list(spec.tags),
                "approx_bytes": spec.approx_bytes,
                "approx_label": "~ 1 GB",
                "installed": installed,
                "partial": False,
                "size_bytes": 1000 if installed else 0,
                "size_label": "1 KB" if installed else "—",
                "folder": "",
            }
        return items

    def download(self, name, progress=None):
        if progress:
            progress(100)
            progress(1000)
        self.available.add(name)
        self.downloads.append(name)
        return "path"

    def delete(self, name):
        self.available.discard(name)
        self.deleted.append(name)


def dictation(controller, text="Merhaba."):
    controller.engine.text = text
    controller.toggle_record()
    controller.toggle_record()
    assert controller.wait_until_ready(3)


def test_history_saved_and_hidden_when_disabled():
    controller = make_controller(model_manager=FakeModels())
    dictation(controller, "İlk kayıt.")

    listed = controller.history_list()
    assert listed["disabled"] is False
    assert listed["total"] == 1
    assert listed["items"][0]["text"] == "İlk kayıt."

    result = controller.settings_save({"save_history": False})
    assert result["ok"] is True
    assert controller.history_list() == {"disabled": True, "items": [], "total": 0}

    dictation(controller, "Kaydedilmemeli.")
    assert controller.snapshot()["latest_text"] == "Kaydedilmemeli."

    controller.settings_save({"save_history": True})
    listed = controller.history_list()
    assert listed["total"] == 1
    assert listed["items"][0]["text"] == "İlk kayıt."


def test_history_open_adds_text_to_screen():
    controller = make_controller(model_manager=FakeModels())
    dictation(controller, "Geçmişe giden metin.")
    record_id = controller.history_list()["items"][0]["id"]

    controller.engine.text = "Yeni dikte."
    dictation(controller, "Yeni dikte.")
    result = controller.history_open(record_id)
    assert result["ok"] is True
    snapshot = controller.snapshot()
    assert snapshot["seq"] == 3
    assert snapshot["latest_text"] == "Geçmişe giden metin."
    assert snapshot["replace_last"] is False
    # Açılan kayıt son dikte olmadığı için Yenile pasif olmalı.
    assert snapshot["can_refresh"] is False
    assert controller.refresh_last()["ok"] is False


def test_refresh_last_replaces_paragraph_and_updates_history():
    controller = make_controller(model_manager=FakeModels())
    dictation(controller, "İlk çeviri.")
    assert controller.snapshot()["can_refresh"] is True

    controller.engine.text = "Yenilenmiş çeviri."
    result = controller.refresh_last()
    assert result["ok"] is True
    assert wait_for_state(controller, READY)

    snapshot = controller.snapshot()
    assert snapshot["latest_text"] == "Yenilenmiş çeviri."
    assert snapshot["replace_last"] is True
    assert snapshot["seq"] == 2
    items = controller.history_list()["items"]
    assert len(items) == 1
    assert items[0]["text"] == "Yenilenmiş çeviri."


def test_refresh_without_recording_is_rejected():
    controller = make_controller(model_manager=FakeModels())
    result = controller.refresh_last()
    assert result["ok"] is False
    assert "kayıt" in result["message"].lower()


def test_model_activate_switches_engine_and_saves_setting():
    models = FakeModels(installed=("large-v3", "small"))
    controller = make_controller(model_manager=models)

    result = controller.model_activate("small")
    assert result["ok"] is True
    assert wait_for_state(controller, READY)

    snapshot = controller.snapshot()
    assert snapshot["model_name"] == "small"
    assert controller.engine.model_name == "small"
    assert controller.settings.get("active_model") == "small"
    titles = [item["title"] for item in snapshot["activity"]]
    assert "Model değiştirildi" in titles


def test_model_activate_falls_back_to_old_model_on_error():
    models = FakeModels(installed=("large-v3", "small"))
    controller = make_controller(model_manager=models)
    assert controller.snapshot()["model_name"] == "large-v3"

    controller.engine.fail_models.add("small")
    result = controller.model_activate("small")
    assert result["ok"] is True
    assert wait_for_state(controller, READY)

    snapshot = controller.snapshot()
    assert snapshot["model_name"] == "large-v3"
    assert controller.settings.get("active_model") == "auto"
    titles = [item["title"] for item in snapshot["activity"]]
    assert "Model değiştirilemedi" in titles


def test_model_activate_rejects_missing_model_and_busy_state():
    controller = make_controller(model_manager=FakeModels(installed=("large-v3",)))
    assert controller.model_activate("medium")["ok"] is False

    gate = threading.Event()
    controller.engine.gate = gate
    controller.toggle_record()
    controller.toggle_record()
    assert controller.snapshot()["state"] == PROCESSING
    assert controller.model_activate("large-v3")["ok"] is False
    gate.set()
    assert controller.wait_until_ready(3)


def test_model_delete_guards_active_and_downloading():
    models = FakeModels()
    controller = make_controller(model_manager=models)
    assert controller.model_delete("large-v3")["ok"] is False
    assert models.deleted == []

    controller.model_activate("small")
    assert wait_for_state(controller, READY)
    result = controller.model_delete("large-v3")
    assert result["ok"] is True
    assert models.deleted == ["large-v3"]


def test_model_download_updates_state_and_installs():
    models = FakeModels(installed=("large-v3",))
    controller = make_controller(model_manager=models)
    result = controller.model_download("tiny")
    assert result["ok"] is True

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        download = controller.snapshot()["download"]
        if download and download["state"] == "done":
            break
        time.sleep(0.02)
    download = controller.snapshot()["download"]
    assert download["state"] == "done"
    assert download["percent"] == 100
    assert "tiny" in models.available


def test_hotkey_change_is_applied_and_persisted():
    controller = make_controller(engine=FakeEngine(), model_manager=FakeModels())
    result = controller.settings_save({"hotkey": "f9"})
    assert result["ok"] is True
    assert controller.snapshot()["hotkey"] == "F9"
    assert controller.settings.get("hotkey") == "f9"


def test_hotkey_change_failure_keeps_old_setting():
    hotkey = FakeHotkey()
    controller = make_controller(hotkey=hotkey, model_manager=FakeModels())
    hotkey.fail_set = True
    result = controller.settings_save({"hotkey": "f9"})
    assert result["ok"] is False
    assert controller.settings.get("hotkey") == "right_ctrl"
    assert controller.snapshot()["hotkey"] == "Sağ Ctrl"


def test_settings_rejected_while_recording():
    controller = make_controller(model_manager=FakeModels())
    controller.toggle_record()
    result = controller.settings_save({"save_history": False})
    assert result["ok"] is False
    controller.toggle_record()
    assert controller.wait_until_ready(3)


def test_last_recording_is_removed_on_shutdown():
    controller = make_controller(model_manager=FakeModels())
    dictation(controller, "Kapanış testi.")
    last_path = Path(config.LAST_RECORDING)
    assert last_path.exists()
    controller.shutdown()
    assert not last_path.exists()
