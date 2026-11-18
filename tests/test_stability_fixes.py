"""Faz A+B kararlılık düzeltmeleri için regresyon testleri."""

import io
import sys
import threading
import time
import urllib.error
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from dikte import __main__ as dikte_main
from dikte import config, error_reporter, text_models, uninstall
from dikte.audio import AudioRecorder
from dikte.controller import Controller
from dikte.engine import EngineInfo, TranscriptResult
from dikte.hotkey import HotkeyListener
from dikte.settings import SettingsStore
from dikte.state import CLEANING, READY
from dikte.text_engine import TextResult


@pytest.fixture(autouse=True)
def isolated_stability_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(config, "TEMP_DIR", tmp_path / "temp")
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "data" / "settings.json")
    monkeypatch.setattr(config, "HISTORY_FILE", tmp_path / "data" / "history.json")
    monkeypatch.setattr(config, "SECRETS_FILE", tmp_path / "data" / "secrets.json")
    monkeypatch.setattr(config, "CUSTOM_MODELS_FILE", tmp_path / "data" / "custom_models.json")
    monkeypatch.setattr(config, "LAST_RECORDING", tmp_path / "temp" / "last.wav")
    config.ensure_runtime_dirs()


class _FakeEngine:
    def __init__(self, text="Deneme metni."):
        self.text = text
        self.model_name = "large-v3"
        self.warnings = []
        self.unloaded = 0

    def set_model(self, name):
        self.model_name = name

    def load(self):
        return EngineInfo(self.model_name, config.model_label(self.model_name), "CPU", "int8", 0.1)

    def unload(self):
        self.unloaded += 1

    def transcribe(self, wav_path, language=None):
        return TranscriptResult(self.text, 1.0, 0.1)


class _FakeHotkey:
    def configure(self, key):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def set_key(self, key):
        pass


class _FakeRecorder:
    def start(self):
        pass

    def stop(self):
        return None

    def cancel(self):
        pass


def _make_controller(tmp_path, **kwargs):
    settings = SettingsStore(tmp_path / "data" / "settings.json")
    ctrl = Controller(
        engine=kwargs.get("engine") or _FakeEngine(),
        recorder=kwargs.get("recorder") or _FakeRecorder(),
        hotkey=kwargs.get("hotkey") or _FakeHotkey(),
        settings_store=settings,
        model_manager=kwargs.get("model_manager"),
        clipper=lambda text: None,
        beeper=lambda kind: None,
        memory_provider=lambda gpu: None,
        text_processor=kwargs.get("text_processor"),
    )
    ctrl.load_engine()
    return ctrl


def _wait_until(pred, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pred():
            return True
        time.sleep(0.01)
    return pred()


def test_ai_cancel_and_immediate_ai_start_task_token_isolation_and_seq(tmp_path):
    first_started = threading.Event()
    release_first = threading.Event()
    call_count = 0

    def slow_then_fast(text, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            first_started.set()
            release_first.wait(timeout=2.0)
            return TextResult(text="ESKI_GOREV_SONUCU", translated=False, unchanged=False)
        return TextResult(text="YENI_GOREV_SONUCU", translated=False, unchanged=False)

    ctrl = _make_controller(tmp_path, text_processor=slow_then_fast)
    ctrl.settings.save(text_provider="openrouter")
    seq_before = ctrl.snapshot()["seq"]

    res1 = ctrl.ai_start_task("clean", "ham metin")
    assert res1["ok"] is True
    assert first_started.wait(timeout=1.0)

    cancel_res = ctrl.ai_cancel()
    assert cancel_res["ok"] is True
    assert ctrl.snapshot()["state"] == READY

    # İptal edilen ilk görev bitmeden hemen ikinci görevi başlat
    res2 = ctrl.ai_start_task("clean", "ham metin 2")
    assert res2["ok"] is True
    assert _wait_until(lambda: ctrl.snapshot()["state"] == READY and ctrl.snapshot()["latest_text"] == "YENI_GOREV_SONUCU")

    # Şimdi ilk görev uyanıp dönse bile yeni sonucu ve state'i ezmemeli
    release_first.set()
    time.sleep(0.05)
    snap = ctrl.snapshot()
    assert snap["state"] == READY
    assert snap["latest_text"] == "YENI_GOREV_SONUCU"
    assert snap["seq"] == seq_before + 1
    assert snap["replace_last"] is True


def test_local_process_text_and_transcribe_path_serialized_by_engine_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(text_models, "is_installed", lambda name: True)
    active = []
    overlap = []
    first_entered = threading.Event()
    allow_first_exit = threading.Event()
    llama_called = threading.Event()

    class _TrackingEngine(_FakeEngine):
        def transcribe(self, wav_path, language=None):
            active.append("transcribe")
            if len(active) > 1:
                overlap.append(list(active))
            first_entered.set()
            allow_first_exit.wait(timeout=2.0)
            active.remove("transcribe")
            return TranscriptResult("ses", 1.0, 0.1)

    class _TrackingTextRuntime:
        model_name = "qwen3-4b"

        def load(self, name, prefer_gpu=True):
            self.model_name = name
            return "CPU"

        def unload(self):
            self.model_name = None

        def generate(self, system, user, max_tokens=512):
            active.append("llama")
            if len(active) > 1:
                overlap.append(list(active))
            llama_called.set()
            time.sleep(0.03)
            active.remove("llama")
            return "temiz"

    ctrl = _make_controller(tmp_path, engine=_TrackingEngine())
    ctrl._text_runtime = _TrackingTextRuntime()
    ctrl.settings.save(text_provider="local", text_model="qwen3-4b")

    wav = tmp_path / "temp" / "sample.wav"
    wav.write_bytes(b"RIFF")

    t1 = threading.Thread(target=lambda: ctrl._transcribe_path(wav))
    t1.start()
    assert first_entered.wait(timeout=1.0)

    t2_res = []
    t2 = threading.Thread(target=lambda: t2_res.append(ctrl._local_process_text("deneme", False)))
    t2.start()
    time.sleep(0.05)
    # _transcribe_path kilidi tutarken _local_process_text içeri girmemiş olmalı
    assert overlap == []
    assert not llama_called.is_set()

    allow_first_exit.set()
    t1.join(timeout=2.0)
    t2.join(timeout=2.0)
    assert overlap == []
    assert llama_called.is_set()
    assert t2_res and t2_res[0].text == "temiz"


def test_hotkey_listener_non_blocking_dispatch_and_canonical_release(monkeypatch):
    entered = threading.Event()
    release_cb = threading.Event()
    events = []

    def on_press():
        events.append("press")
        entered.set()
        release_cb.wait(timeout=1.0)

    def on_release():
        events.append("release")

    captured = {}

    class FakeListener:
        def __init__(self, on_press, on_release):
            captured["on_press"] = on_press
            captured["on_release"] = on_release
            self.daemon = True

        def start(self):
            pass

        def stop(self):
            pass

    pynput_mod = ModuleType("pynput")
    kb_mod = ModuleType("pynput.keyboard")
    kb_mod.Listener = FakeListener
    pynput_mod.keyboard = kb_mod
    monkeypatch.setitem(sys.modules, "pynput", pynput_mod)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", kb_mod)

    listener = HotkeyListener(on_press, on_release, key="ctrl+d")
    listener.start()

    k_ctrl = SimpleNamespace(name="ctrl_l", vk=162)
    k_d_press = SimpleNamespace(name=None, vk=68, char="\x04")
    k_d_release = SimpleNamespace(name=None, vk=68, char="d")

    t0 = time.monotonic()
    captured["on_press"](k_ctrl)
    captured["on_press"](k_d_press)
    elapsed = time.monotonic() - t0
    # pynput hook iş parçacığı callback tamamlanmasını beklemeden dönmeli
    assert elapsed < 0.2
    assert entered.wait(timeout=1.0)
    release_cb.set()

    # Ctrl bırakıldıktan sonra D farklı char ile bırakılsa bile canonical ID eşleşmeli
    captured["on_release"](k_d_release)
    assert _wait_until(lambda: events == ["press", "release"])
    assert listener._pressed is False

    listener.stop()
    assert listener._worker_thread is None


def test_audio_recorder_thread_safe_chunks_and_max_record_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MAX_RECORD_SECONDS", 1)
    captured_cb = {}

    class FakeStream:
        def __init__(self, samplerate, channels, dtype, blocksize, callback):
            captured_cb["fn"] = callback

        def start(self):
            pass

        def stop(self):
            pass

        def close(self):
            pass

    fake_sd = ModuleType("sounddevice")
    fake_sd.RawInputStream = FakeStream
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)

    rec = AudioRecorder(sample_rate=100, temp_dir=tmp_path / "temp")
    rec.start()
    cb = captured_cb["fn"]

    # 1 sn * 100 Hz = 100 frame; 2. çağrı 160 frame'e çıkarır, 3. çağrı limiti görüp keser
    cb(b"\x01\x00" * 80, 80, None, None)
    cb(b"\x01\x00" * 80, 80, None, None)
    cb(b"\x01\x00" * 80, 80, None, None)
    assert rec._max_duration_reached is True

    result = rec.stop()
    assert result is not None
    assert result.frames == 160


def test_local_text_model_load_cpu_fallback_wraps_error(tmp_path, monkeypatch):
    model_path = tmp_path / "models" / "qwen3-4b.gguf"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"GGUF" + b"\x00" * 2048)

    monkeypatch.setattr(text_models, "text_model_path", lambda name: model_path)
    monkeypatch.setattr(text_models.LocalTextModel, "available", staticmethod(lambda: True))
    monkeypatch.setattr(text_models.diagnostics, "prepare_cuda_dlls", lambda: [])

    class BrokenLlama:
        def __init__(self, **kwargs):
            raise RuntimeError("boom")

    fake_llama_mod = ModuleType("llama_cpp")
    fake_llama_mod.Llama = BrokenLlama
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_llama_mod)

    runtime = text_models.LocalTextModel()
    with pytest.raises(text_models.TextModelError, match="yüklenemedi"):
        runtime.load("qwen3-4b", prefer_gpu=True)


def test_downloader_http_416_and_progress_without_closure(tmp_path, monkeypatch):
    payload = b"GGUF" + b"\x00" * 1024
    spec = text_models.TextModel(
        name="qwen3-1.7b",
        label="Qwen 3 1.7B",
        desc="test",
        repo="org/repo",
        filename="qwen3-1.7b.gguf",
        size_bytes=len(payload),
        tags=(),
    )
    monkeypatch.setattr(text_models, "get_text_model", lambda name: spec)

    part = text_models.partial_path("qwen3-1.7b")
    part.parent.mkdir(parents=True, exist_ok=True)
    part.write_bytes(b"GGUFstale-part")

    class FakeResp:
        status = 200
        headers = {"Content-Length": str(len(payload))}

        def __init__(self, data):
            self._bio = io.BytesIO(data)

        def read(self, n):
            return self._bio.read(n)

        def close(self):
            pass

    calls = [0]

    def fake_opener(req, timeout=60):
        calls[0] += 1
        if calls[0] == 1:
            raise urllib.error.HTTPError(req.full_url, 416, "Range Not Satisfiable", {}, None)
        return FakeResp(payload)

    progress_calls = []

    def on_progress(written, total):
        progress_calls.append((written, total))

    dl = text_models.Downloader(opener=fake_opener)
    res = dl.download("qwen3-1.7b", progress=on_progress)
    assert res["completed"] is True
    assert calls[0] == 2
    assert progress_calls == [(len(payload), len(payload))]


def test_main_uninstall_exit_codes(monkeypatch):
    monkeypatch.setattr(uninstall, "run_uninstaller", lambda **kwargs: True)
    assert dikte_main.main(["--uninstall"]) == 0

    def fail_uninstall(**kwargs):
        raise uninstall.UninstallError("kaldırma hatası")

    monkeypatch.setattr(uninstall, "run_uninstaller", fail_uninstall)
    assert dikte_main.main(["--uninstall"]) == 1


def test_controller_diagnostics_methods_and_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(error_reporter, "_read_pyav_info", lambda: ("12.0.0", True))
    ctrl = _make_controller(tmp_path)

    snap = ctrl.snapshot()
    assert "diagnostics" in snap
    assert isinstance(snap["diagnostics"], dict)
    assert "has_issue" in snap["diagnostics"]

    diag_get = ctrl.diagnostics_get()
    assert diag_get["ok"] is True
    assert "report_text" in diag_get

    diag_copy = ctrl.diagnostics_copy()
    assert diag_copy["ok"] is True
    assert "text" in diag_copy

    diag_export = ctrl.diagnostics_export()
    assert diag_export["ok"] is True
    assert Path(diag_export["path"]).exists()

    diag_js = ctrl.diagnostics_log_js_error({"message": "Test JS err", "source": "app.js", "line": 42})
    assert diag_js["ok"] is True

    diag_dismiss = ctrl.diagnostics_dismiss_crash()
    assert diag_dismiss["ok"] is True
