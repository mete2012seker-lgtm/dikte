"""Kod Denetimi Faz 1 regresyon testleri (Y1, Y2, Y3 ve Orta Faz 1 sağlamlaştırmaları)."""

from __future__ import annotations

import http.client
import io
import json
import sys
import threading
import time
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from dikte import config, diagnostics, hotkey, models, paste, text_engine, text_models
from dikte.audio import AudioRecorder
from dikte.controller import Controller
from dikte.engine import EngineInfo, TranscriptResult
from dikte.history import HistoryError, HistoryStore
from dikte.hotkey import HotkeyListener, _canonical_key_id, key_to_tokens
from dikte.instance import SingleInstance
from dikte.settings import SettingsError, SettingsStore
from dikte.state import CLEANING, LOADING, READY


@pytest.fixture(autouse=True)
def isolated_faz1_dirs(tmp_path, monkeypatch):
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
    def __init__(self, text="Merhaba dünya."):
        self.text = text
        self.model_name = "large-v3"
        self.warnings = []
        self.load_hook = None
        self.transcribe_hook = None

    def set_model(self, name):
        self.model_name = name

    def load(self):
        if self.load_hook:
            self.load_hook()
        return EngineInfo(self.model_name or "large-v3", "Whisper Large", "CPU", "int8", 0.1)

    def unload(self):
        pass

    def transcribe(self, wav_path, language=None):
        if self.transcribe_hook:
            self.transcribe_hook()
        return TranscriptResult(self.text, 1.0, 0.1)


class _FakeRecorder:
    def __init__(self, duration=1.5):
        self.duration = duration

    def start(self):
        pass

    def stop(self):
        from dikte.audio import Recording

        p = Path(config.TEMP_DIR) / f"rec-{time.time_ns()}.wav"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"RIFF")
        return Recording(path=p, duration=self.duration, frames=24000)

    def cancel(self):
        pass

    def cleanup(self, path):
        if path:
            Path(path).unlink(missing_ok=True)


class _FakeHotkey:
    def __init__(self):
        self.key = "right_ctrl"
        self.started = False

    def configure(self, key):
        self.key = key

    def set_key(self, key):
        self.key = key

    def start(self):
        self.started = True

    def stop(self):
        self.started = False


def _make_controller(tmp_path, **kwargs):
    settings = kwargs.pop("settings_store", None) or SettingsStore(tmp_path / "data" / "settings.json")
    ctrl = Controller(
        engine=kwargs.pop("engine", _FakeEngine()),
        recorder=kwargs.pop("recorder", _FakeRecorder()),
        hotkey=kwargs.pop("hotkey", _FakeHotkey()),
        settings_store=settings,
        clipper=kwargs.pop("clipper", lambda t: None),
        beeper=kwargs.pop("beeper", lambda k: None),
        memory_provider=lambda gpu: None,
        load_in_background=False,
        paster=lambda: False,
        **kwargs,
    )
    ctrl.load_engine()
    return ctrl


# ---------------- Y1 ----------------


def test_y1_load_engine_during_refresh_keeps_cleaning_state(tmp_path):
    engine = _FakeEngine()
    ctrl = _make_controller(tmp_path, engine=engine)

    wav = tmp_path / "temp" / "last.wav"
    wav.write_bytes(b"RIFF")
    ctrl._last_recording = wav
    ctrl._seq = 1
    ctrl._refresh_seq = 1

    state_after_reload = []
    transcribe_entered = threading.Event()
    allow_transcribe_finish = threading.Event()

    def hook_transcribe():
        # Yenileme sürerken (CLEANING) ses modeli yeniden yüklense bile state READY'ye kaçmamalı
        ctrl._whisper_loaded = False
        ctrl.load_engine()
        state_after_reload.append(ctrl.snapshot()["state"])
        transcribe_entered.set()
        allow_transcribe_finish.wait(timeout=2.0)

    engine.transcribe_hook = hook_transcribe
    res = ctrl.refresh_last()
    assert res["ok"] is True
    assert transcribe_entered.wait(timeout=2.0)

    # load_engine() CLEANING durumunu READY'ye kaçırmamış olmalı!
    assert state_after_reload == [CLEANING]
    assert ctrl.snapshot()["state"] == CLEANING

    allow_transcribe_finish.set()
    assert ctrl.wait_until_ready(2.0)
    assert ctrl.snapshot()["state"] == READY


def test_y1_ai_cancel_does_not_clobber_refresh_and_stale_refresh_token_ignored(tmp_path):
    entered = threading.Event()
    release = threading.Event()
    engine = _FakeEngine()
    engine.transcribe_hook = lambda: (entered.set(), release.wait(timeout=2.0))

    ctrl = _make_controller(tmp_path, engine=engine)
    wav = tmp_path / "temp" / "last.wav"
    wav.write_bytes(b"RIFF")
    ctrl._last_recording = wav
    ctrl._seq = 1
    ctrl._refresh_seq = 1

    res = ctrl.refresh_last()
    assert res["ok"] is True
    assert entered.wait(timeout=2.0)
    assert ctrl.snapshot()["state"] == CLEANING

    # refresh sürerken ai_cancel() CLEANING durumunu bozmamalı
    ctrl.ai_cancel()
    assert ctrl.snapshot()["state"] == CLEANING

    release.set()
    assert ctrl.wait_until_ready(2.0)
    assert ctrl.snapshot()["state"] == READY

    # Eski token ile çağrılan _refresh_worker yeni AI CLEANING durumunu READY'ye çekememeli
    ctrl._machine.set(CLEANING)
    ctrl._cleaning_owner = "ai"
    ctrl._refresh_token = 99
    engine.transcribe_hook = None
    ctrl._refresh_worker(wav, token=1)
    assert ctrl.snapshot()["state"] == CLEANING


# ---------------- Y2 ----------------


def test_y2_real_pynput_key_ctrl_r_vk_extraction_and_stuck_recovery(monkeypatch):
    from pynput.keyboard import Key

    assert _canonical_key_id(Key.ctrl_r) == ("key", 163, "ctrl_r")
    tokens = key_to_tokens(Key.ctrl_r)
    assert {"right_ctrl", "ctrl"}.issubset(tokens)

    events = []
    listener = HotkeyListener(lambda: events.append("press"), lambda: events.append("release"), key="right_ctrl")
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

    pynput_mock = ModuleType("pynput")
    kb_mock = ModuleType("pynput.keyboard")
    kb_mock.Listener = FakeListener
    pynput_mock.keyboard = kb_mock
    monkeypatch.setitem(sys.modules, "pynput", pynput_mock)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", kb_mock)

    down_vks = {163}
    monkeypatch.setattr(hotkey, "_is_vk_physically_down", lambda vk: vk in down_vks)

    listener.start()
    captured["on_press"](Key.ctrl_r)
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline and "press" not in events:
        time.sleep(0.01)
    assert listener._pressed is True

    # Fiziksel bırakılma oldu ama on_release kaçtı; başka bir tuşa basılınca takılı Key.ctrl_r kurtarılmalı
    down_vks.clear()
    captured["on_press"](Key.space)
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline and "release" not in events:
        time.sleep(0.01)
    assert listener._pressed is False
    assert events == ["press", "release"]
    listener.stop()


def test_y2_set_key_before_start_does_not_start_listener():
    listener = HotkeyListener(lambda: None, lambda: None, key="right_ctrl")
    try:
        listener.set_key("f8")
        assert listener.key == "f8"
        assert listener._listener is None
    finally:
        listener.stop()


# ---------------- Y3 ----------------


def test_y3_custom_gguf_truncated_download_fails_and_keeps_part(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    custom_spec = text_models.TextModel(
        "custom-trunc", "Custom Trunc", "Test", "org/repo", "trunc.gguf", 0, ("Özel",)
    )
    monkeypatch.setattr(text_models, "get_text_model", lambda name: custom_spec)

    class TruncatedResp:
        status = 200
        headers = {"Content-Length": "10000"}

        def __init__(self):
            self._bio = io.BytesIO(b"GGUF" + b"\x00" * 4092)  # 4096 bayt (< 10000)

        def read(self, n):
            return self._bio.read(n)

        def close(self):
            pass

    dl = text_models.Downloader(opener=lambda req, timeout=60: TruncatedResp(), chunk_size=1024)
    with pytest.raises(text_models.TextModelError):
        dl.download("custom-trunc")

    assert not text_models.text_model_path("custom-trunc").exists()
    part = text_models.partial_path("custom-trunc")
    assert part.exists()
    assert part.stat().st_size == 4096


@pytest.mark.parametrize(
    "exc_factory",
    [
        lambda: http.client.IncompleteRead(b"part", 100),
        lambda: ConnectionResetError("reset"),
        lambda: TimeoutError("timed out"),
    ],
)
def test_y3_download_network_errors_wrapped_and_keep_part(tmp_path, monkeypatch, exc_factory):
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    spec = text_models.TextModel(
        "test-net", "Test Net", "Test", "org/repo", "net.gguf", 10_000, ("Test",)
    )
    monkeypatch.setattr(text_models, "get_text_model", lambda name: spec)

    class FailingResp:
        status = 200
        headers = {"Content-Length": "10000"}

        def __init__(self):
            self._calls = 0

        def read(self, n):
            self._calls += 1
            if self._calls == 1:
                return b"GGUF" + b"\x00" * 500
            raise exc_factory()

        def close(self):
            pass

    dl = text_models.Downloader(opener=lambda req, timeout=60: FailingResp(), chunk_size=1024)
    with pytest.raises(text_models.TextModelError):
        dl.download("test-net")

    part = text_models.partial_path("test-net")
    assert part.exists()
    assert part.stat().st_size == 504


def test_y3_local_text_model_load_unloads_first_and_generate_wraps_error(tmp_path, monkeypatch):
    model_path = tmp_path / "models" / "qwen3-4b.gguf"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"GGUF" + b"\x00" * 2048)

    monkeypatch.setattr(text_models, "text_model_path", lambda name: model_path)
    monkeypatch.setattr(text_models.LocalTextModel, "available", staticmethod(lambda: True))
    monkeypatch.setattr(text_models.diagnostics, "prepare_cuda_dlls", lambda: None)

    events = []

    class FakeLlama:
        def __init__(self, **kwargs):
            events.append(("llama_init", runtime._llm))

        def create_chat_completion(self, **kwargs):
            raise RuntimeError("cuda failure")

    fake_llama_mod = ModuleType("llama_cpp")
    fake_llama_mod.Llama = FakeLlama
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_llama_mod)

    runtime = text_models.LocalTextModel()
    runtime._llm = object()
    runtime.model_name = "old-model"
    runtime.device = "GPU"

    orig_unload = runtime.unload

    def spy_unload():
        events.append(("unload", runtime._llm))
        orig_unload()

    runtime.unload = spy_unload

    device = runtime.load("qwen3-4b", prefer_gpu=False)
    assert device == "CPU"
    assert events[0][0] == "unload"
    assert events[1] == ("llama_init", None)

    with pytest.raises(text_models.TextModelError):
        runtime.generate("sys", "usr")


def test_y3_concurrent_downloads_rejected_in_managers(tmp_path, monkeypatch):
    # 1. ModelManager
    mgr = models.ModelManager(models_dir=tmp_path / "models")
    started = threading.Event()
    release = threading.Event()

    def slow_dl(name, models_dir):
        started.set()
        release.wait(timeout=2.0)
        return str(models.model_folder(models_dir, name))

    monkeypatch.setattr(models, "_download_model", slow_dl)
    t = threading.Thread(target=lambda: mgr.download("tiny"))
    t.start()
    assert started.wait(timeout=2.0)

    with pytest.raises(models.ModelError):
        mgr.download("small")

    release.set()
    t.join(timeout=2.0)

    # 2. TextModelManager
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    tmgr = text_models.TextModelManager(models_dir=tmp_path / "models")
    t_started = threading.Event()
    t_release = threading.Event()

    def slow_text_dl(name, progress=None, pause_event=None, cancel_event=None):
        t_started.set()
        t_release.wait(timeout=2.0)
        return {"completed": True, "paused": False, "cancelled": False, "size": 100}

    tmgr._downloader = SimpleNamespace(download=slow_text_dl)
    t2 = threading.Thread(target=lambda: tmgr.download("qwen3-1.7b"))
    t2.start()
    assert t_started.wait(timeout=2.0)

    with pytest.raises(text_models.TextModelError):
        tmgr.download("qwen3-4b")

    t_release.set()
    t2.join(timeout=2.0)


# ---------------- Orta Faz 1 ----------------


def test_orta_beep_runs_outside_lock_in_daemon_thread(tmp_path):
    beep_entered = threading.Event()
    beep_release = threading.Event()
    beep_info = {}

    def blocking_beeper(kind):
        beep_info["daemon"] = threading.current_thread().daemon
        beep_info["lock_free"] = ctrl._lock.acquire(blocking=False)
        if beep_info["lock_free"]:
            ctrl._lock.release()
        beep_entered.set()
        beep_release.wait(timeout=2.0)

    ctrl = _make_controller(tmp_path, beeper=blocking_beeper)
    t0 = time.monotonic()
    res = ctrl._start_recording()
    elapsed = time.monotonic() - t0
    assert res["ok"] is True
    assert elapsed < 0.2  # beeper beklemeden dönmeli
    assert beep_entered.wait(timeout=1.0)
    assert beep_info["daemon"] is True
    assert beep_info["lock_free"] is True
    beep_release.set()


def test_orta_voice_download_token_and_join_prevents_overwrite(tmp_path):
    started_1 = threading.Event()
    release_1 = threading.Event()
    worker1_exited = threading.Event()
    entered_2_before_1_exited = []
    call_num = [0]

    class FakeModels:
        def scan(self):
            return {}

        def installed(self, name):
            return False

        def size(self, name):
            return 0

        def download(self, name, progress=None):
            call_num[0] += 1
            if call_num[0] == 1:
                started_1.set()
                release_1.wait(timeout=2.0)
                try:
                    raise models.ModelError("İndirme iptal edildi.")
                finally:
                    worker1_exited.set()
            entered_2_before_1_exited.append(not worker1_exited.is_set())
            return "ok"

        def cancel_download(self):
            return {"cancelled": True}

    ctrl = _make_controller(tmp_path, model_manager=FakeModels())
    assert hasattr(ctrl, "_voice_download_token")
    res1 = ctrl.model_download("tiny")
    assert res1["ok"] is True
    assert started_1.wait(timeout=1.0)

    ctrl.models_cancel_download()

    # Eski thread bitmeden yeni indirme başlatılınca önce eskisini join etmeli ve token ile korumalı
    threading.Timer(0.05, release_1.set).start()
    res2 = ctrl.model_download("tiny")
    assert res2["ok"] is True
    ctrl._download_thread.join(timeout=2.0)
    assert entered_2_before_1_exited == [False]
    assert ctrl._download["state"] == "done"

    # Eski token ile çağrılan _download_worker yeni indirmeyi bozmamalı
    ctrl._download = {"name": "tiny", "state": "downloading", "bytes": 10, "total": 100, "percent": 10, "error": None}
    ctrl._voice_download_token = 99
    ctrl._download_worker("tiny", token=1)
    assert ctrl._download["state"] == "downloading"


def test_orta_local_process_text_checks_ai_cancel_between_retries(tmp_path, monkeypatch):
    monkeypatch.setattr(text_models, "is_installed", lambda name: True)
    monkeypatch.setattr(text_models.LocalTextModel, "available", staticmethod(lambda: True))
    ctrl = _make_controller(tmp_path)
    ctrl.settings.save(text_provider="local", text_model="qwen3-4b")

    calls = [0]

    class FakeRuntime:
        model_name = "qwen3-4b"
        device = "CPU"

        def load(self, name, prefer_gpu=True):
            return "CPU"

        def unload(self):
            self.model_name = None

        def generate(self, system, user, max_tokens=512):
            calls[0] += 1
            ctrl._ai_cancel_event.set()
            return ""  # validation hatası -> normalde 2. denemeyi tetikler

    ctrl._text_runtime = FakeRuntime()
    with pytest.raises(text_engine.TextEngineError):
        ctrl._local_process_text("Merhaba dünya bugün.", False)
    assert calls[0] == 1


def test_orta_wizard_complete_reverts_hotkey_on_settings_save_failure(tmp_path):
    hk = _FakeHotkey()
    ctrl = _make_controller(tmp_path, hotkey=hk)

    def broken_save(**kwargs):
        raise SettingsError("diske yazılamadı")

    ctrl.settings.save = broken_save
    res = ctrl.wizard_complete({"hotkey": "f8"})
    assert res["ok"] is False
    assert hk.key == "right_ctrl"


def test_orta_text_model_delete_rejected_during_loading(tmp_path, monkeypatch):
    ctrl = _make_controller(tmp_path)
    deleted = []
    monkeypatch.setattr(text_models, "delete", lambda name: deleted.append(name))

    ctrl._machine.set(LOADING)
    res = ctrl.text_model_delete("qwen3-4b")
    assert res["ok"] is False
    assert deleted == []


def test_orta_audio_recorder_has_state_lock(tmp_path, monkeypatch):
    rec = AudioRecorder(temp_dir=tmp_path / "temp")
    assert hasattr(rec, "_state_lock")

    class FakeStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            time.sleep(0.03)

        def stop(self):
            pass

        def close(self):
            pass

    monkeypatch.setitem(sys.modules, "sounddevice", SimpleNamespace(RawInputStream=FakeStream))

    t1 = threading.Thread(target=rec.start)
    t1.start()
    time.sleep(0.005)
    t2 = threading.Thread(target=rec.cancel)
    t2.start()
    t1.join(timeout=1.0)
    t2.join(timeout=1.0)
    assert rec.is_recording is False


def test_orta_paste_lock_serializes_concurrent_calls(monkeypatch):
    assert hasattr(paste, "_paste_lock")
    active = []
    overlaps = []

    class FakeUser32:
        def GetAsyncKeyState(self, vk):
            return 0

        def MapVirtualKeyW(self, vk, flag):
            return 0

        def SendInput(self, n, p_inp, size):
            active.append(1)
            if len(active) > 1:
                overlaps.append(len(active))
            time.sleep(0.01)
            active.pop()
            return 1

    monkeypatch.setattr(paste, "_user32", lambda: FakeUser32())
    monkeypatch.setattr(paste.time, "sleep", lambda s: None)

    t1 = threading.Thread(target=paste.send_ctrl_v)
    t2 = threading.Thread(target=paste.send_ctrl_v)
    t1.start()
    t2.start()
    t1.join(timeout=2.0)
    t2.join(timeout=2.0)

    assert overlaps == []
    assert paste.is_pasting() is False


def test_orta_instance_uses_win32_use_last_error(monkeypatch):
    if sys.platform != "win32":
        pytest.skip("Windows'a özgü")
    import ctypes

    calls = []
    real_windll = ctypes.WinDLL

    def spy_windll(name, *args, **kwargs):
        calls.append((name, kwargs))
        return real_windll(name, *args, **kwargs)

    monkeypatch.setattr(ctypes, "WinDLL", spy_windll)
    inst = SingleInstance(name="Local\\DikteFaz1AuditTestMutex")
    try:
        assert inst.acquire() is True
        assert any(name == "kernel32" and kw.get("use_last_error") is True for name, kw in calls)
    finally:
        inst.release()


def test_orta_custom_models_corrupt_entries_backup_and_concurrent_writes(tmp_path, monkeypatch):
    custom_file = tmp_path / "data" / "custom_models.json"
    monkeypatch.setattr(config, "CUSTOM_MODELS_FILE", custom_file)
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")

    # 1. Bozuk JSON yedeklenmeli
    custom_file.write_text("{bozuk-json", encoding="utf-8")
    res = models.load_custom_models()
    assert res == {"speech": [], "text": []}
    assert list(custom_file.parent.glob("custom_models.bozuk-*.json"))

    # 2. Liste olmayan değer ve 'name' alanı olmayan bozuk kayıt atlanmalı
    custom_file.write_text(
        json.dumps(
            {
                "speech": "bozuk-string",
                "text": [
                    {"repo": "x/y"},  # name yok -> atlanmalı
                    "gecersiz-ogeyim",
                    {"name": "ok-text", "repo": "a/b", "filename": "m.gguf"},
                ],
            }
        ),
        encoding="utf-8",
    )
    loaded = models.load_custom_models()
    assert loaded["speech"] == []
    assert [m["name"] for m in loaded["text"]] == ["ok-text"]
    assert models.scan(tmp_path / "models")
    assert any(m["name"] == "ok-text" for m in text_models.scan())

    # 3. Eşzamanlı eklemelerde kayıt kaybı olmamalı
    custom_file.unlink(missing_ok=True)
    errors = []

    def add_speech(i):
        try:
            models.add_custom_model(f"user{i}/whisper-test-{i}")
        except Exception as exc:
            errors.append(exc)

    def add_text(i):
        try:
            text_models.add_custom_text_model(f"user{i}/text-test-{i}", filename=f"m{i}.gguf")
        except Exception as exc:
            errors.append(exc)

    threads = [
        *[threading.Thread(target=add_speech, args=(i,)) for i in range(6)],
        *[threading.Thread(target=add_text, args=(i,)) for i in range(6)],
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=3.0)

    assert errors == []
    final = models.load_custom_models()
    assert len(final["speech"]) == 6
    assert len(final["text"]) == 6


def test_orta_history_save_failure_preserves_in_memory_items(tmp_path, monkeypatch):
    store = HistoryStore(tmp_path / "data" / "history.json")
    rec1 = store.add("Birinci", 1.0, 1)
    rec2 = store.add("İkinci", 1.0, 1)
    before_ids = [r["id"] for r in store.list()]

    def failing_save(*args, **kwargs):
        raise HistoryError("Disk dolu")

    monkeypatch.setattr(store, "_save", failing_save)

    with pytest.raises(HistoryError):
        store.add("Üçüncü", 1.0, 1)
    assert [r["id"] for r in store.list()] == before_ids

    with pytest.raises(HistoryError):
        store.delete(rec1["id"])
    assert [r["id"] for r in store.list()] == before_ids

    with pytest.raises(HistoryError):
        store.update_text(rec2["id"], "Değişmiş")
    assert store.get(rec2["id"])["text"] == "İkinci"

    with pytest.raises(HistoryError):
        store.clear()
    assert [r["id"] for r in store.list()] == before_ids


def test_orta_diagnostics_cuda_lock_serializes_prepare(tmp_path, monkeypatch):
    if sys.platform != "win32":
        pytest.skip("Windows'a özgü")
    import sysconfig

    assert hasattr(diagnostics, "_cuda_lock")
    monkeypatch.setattr(diagnostics, "_cuda_prepared", False)

    entered = threading.Event()
    release = threading.Event()
    second_done = threading.Event()

    real_get_paths = sysconfig.get_paths

    def slow_get_paths(*args, **kwargs):
        entered.set()
        release.wait(timeout=2.0)
        return real_get_paths(*args, **kwargs)

    monkeypatch.setattr(sysconfig, "get_paths", slow_get_paths)

    t1 = threading.Thread(target=diagnostics.prepare_cuda_dlls)
    t1.start()
    assert entered.wait(timeout=1.0)

    t2 = threading.Thread(target=lambda: (diagnostics.prepare_cuda_dlls(), second_done.set()))
    t2.start()
    time.sleep(0.05)
    assert not second_done.is_set()

    release.set()
    t1.join(timeout=2.0)
    t2.join(timeout=2.0)
    assert second_done.is_set()
