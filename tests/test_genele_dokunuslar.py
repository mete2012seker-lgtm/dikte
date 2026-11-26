"""Genele hitap eden 5 dokunuş için birim, entegrasyon ve Playwright arayüz testleri."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from dikte import config, diagnostics
from dikte.audio import AudioRecorder, list_input_devices
from dikte.controller import Controller
from dikte.engine import EngineInfo, TranscriptResult
from dikte.hotkey import HotkeyError, HotkeyListener
from dikte.indicator import FloatingIndicator
from dikte.settings import DEFAULTS, HOTKEY_MODE_CHOICES, SettingsStore
from dikte.state import CLEANING, ERROR, LOADING, PROCESSING, READY, RECORDING
from dikte.ui.bridge import Api


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TEMP_DIR", tmp_path / "temp")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "data" / "settings.json")
    monkeypatch.setattr(config, "HISTORY_FILE", tmp_path / "data" / "history.json")
    monkeypatch.setattr(config, "SECRETS_FILE", tmp_path / "data" / "secrets.json")
    monkeypatch.setattr(config, "CUSTOM_MODELS_FILE", tmp_path / "data" / "custom_models.json")
    monkeypatch.setattr(config, "LAST_RECORDING", tmp_path / "temp" / "last.wav")
    (tmp_path / "temp").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)


# ---------- 1. Settings doğrulama ----------


def test_settings_new_defaults_and_validation(tmp_path):
    assert HOTKEY_MODE_CHOICES == {"hold": "Basılı Tut", "toggle": "Bas-Bırak"}
    assert DEFAULTS["hotkey_mode"] == "hold"
    assert DEFAULTS["input_device"] == "default"
    assert DEFAULTS["show_indicator"] is True

    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    data = store.as_dict()
    assert data["hotkey_mode"] == "hold"
    assert data["input_device"] == "default"
    assert data["show_indicator"] is True

    store.save(hotkey_mode="toggle", input_device="USB Mic", show_indicator=False)
    reloaded = SettingsStore(path)
    assert reloaded.get("hotkey_mode") == "toggle"
    assert reloaded.get("input_device") == "USB Mic"
    assert reloaded.get("show_indicator") is False

    # Geçersiz değerler güvenle varsayılana düşer
    path.write_text(
        '{"hotkey_mode": "gecersiz", "input_device": "   ", "show_indicator": "evet"}',
        encoding="utf-8",
    )
    fallback = SettingsStore(path).as_dict()
    assert fallback["hotkey_mode"] == "hold"
    assert fallback["input_device"] == "default"
    assert fallback["show_indicator"] is True


# ---------- 2. Bas-Bırak (Toggle) Kısayol Modu ----------


def _setup_fake_pynput(monkeypatch):
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
    monkeypatch.setattr("dikte.hotkey._is_vk_physically_down", lambda vk: None)
    return captured


def _wait_until(pred, timeout=1.5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pred():
            return True
        time.sleep(0.01)
    return pred()


def test_hotkey_listener_toggle_mode(monkeypatch):
    captured = _setup_fake_pynput(monkeypatch)
    events = []
    listener = HotkeyListener(
        lambda: events.append("press"),
        lambda: events.append("release"),
        key="right_ctrl",
        mode="toggle",
    )
    assert listener.mode == "toggle"
    listener.start()

    k_rctrl = SimpleNamespace(name="ctrl_r", vk=163)

    # 1. basış -> press tetikler; bırakınca release tetiklemez
    captured["on_press"](k_rctrl)
    assert _wait_until(lambda: events == ["press"])
    captured["on_release"](k_rctrl)
    time.sleep(0.05)
    assert events == ["press"]

    # 2. basış -> release tetikler; bırakınca tekrar tetiklemez
    captured["on_press"](k_rctrl)
    assert _wait_until(lambda: events == ["press", "release"])
    captured["on_release"](k_rctrl)
    time.sleep(0.05)
    assert events == ["press", "release"]

    # 3. basış -> yeniden press tetikler
    captured["on_press"](k_rctrl)
    assert _wait_until(lambda: events == ["press", "release", "press"])

    # hold moduna geçiş
    listener.set_mode("hold")
    assert listener.mode == "hold"
    captured["on_release"](k_rctrl)
    time.sleep(0.03)
    events.clear()
    captured["on_press"](k_rctrl)
    assert _wait_until(lambda: events == ["press"])
    captured["on_release"](k_rctrl)
    assert _wait_until(lambda: events == ["press", "release"])

    with pytest.raises(HotkeyError):
        listener.set_mode("invalid")

    listener.stop()


class _FakeEngine:
    model_name = "small"
    warnings = []

    def set_model(self, name):
        self.model_name = name

    def unload(self):
        pass

    def load(self):
        return EngineInfo("small", "Whisper Small", "CPU", "int8", 0.1)

    def transcribe(self, wav_path, language=None):
        return TranscriptResult("Deneme kaydı.", 1.0, 0.1)


class _FakeRecorder:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.device = "default"
        self.recording = False

    def set_device(self, device):
        self.device = device or "default"

    def start(self):
        self.recording = True

    def stop(self):
        self.recording = False
        wav = self.temp_dir / f"rec-{time.time_ns()}.wav"
        wav.parent.mkdir(parents=True, exist_ok=True)
        wav.write_bytes(b"RIFF-test")
        from dikte.audio import Recording

        return Recording(path=wav, duration=1.5, frames=24000)

    def cancel(self):
        self.recording = False

    def cleanup(self, path):
        if path:
            Path(path).unlink(missing_ok=True)


class _FakeIndicator:
    def __init__(self):
        self.enabled = True
        self.states = []
        self.closed = False

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)

    def update(self, state: str):
        self.states.append(state)

    def close(self):
        self.closed = True


def test_controller_toggle_mode_and_settings_integration(tmp_path, monkeypatch):
    captured = _setup_fake_pynput(monkeypatch)
    store = SettingsStore(tmp_path / "data" / "settings.json")
    store.save(hotkey_mode="toggle")

    ind = _FakeIndicator()
    ctrl_ref = {}
    listener = HotkeyListener(
        lambda: ctrl_ref["ctrl"].on_hotkey_press(),
        lambda: ctrl_ref["ctrl"].on_hotkey_release(),
        key="right_ctrl",
        mode="hold",
    )
    ctrl = Controller(
        engine=_FakeEngine(),
        recorder=_FakeRecorder(tmp_path / "temp"),
        hotkey=listener,
        clipper=lambda text: None,
        beeper=lambda kind: None,
        memory_provider=lambda gpu: None,
        load_in_background=False,
        settings_store=store,
        indicator=ind,
    )
    ctrl_ref["ctrl"] = ctrl
    ctrl.load_engine()
    ctrl.start()

    assert listener.mode == "toggle"
    assert ctrl.snapshot()["hotkey_mode"] == "toggle"

    k_rctrl = SimpleNamespace(name="ctrl_r", vk=163)
    captured["on_press"](k_rctrl)
    assert _wait_until(lambda: ctrl.snapshot()["state"] == RECORDING)

    # Tuşu bırakınca toggle modunda kayıt durmamalı
    captured["on_release"](k_rctrl)
    time.sleep(0.06)
    assert ctrl.snapshot()["state"] == RECORDING

    # İkinci basışta durup çevirmeli
    captured["on_press"](k_rctrl)
    assert _wait_until(lambda: ctrl.snapshot()["seq"] == 1 and ctrl.snapshot()["state"] == READY)
    assert ctrl.snapshot()["latest_text"] == "Deneme kaydı."

    # settings_save ile moda geri dönüş ve geçersiz mod koruması
    bad = ctrl.settings_save({"hotkey_mode": "bilinmeyen"})
    assert bad["ok"] is False

    res = ctrl.settings_save({"hotkey_mode": "hold"})
    assert res["ok"] is True
    assert listener.mode == "hold"
    assert ctrl.snapshot()["hotkey_mode"] == "hold"

    ctrl.shutdown()
    assert ind.closed is True


# ---------- 3. Mikrofon Seçimi ----------


def test_list_input_devices_filters_and_handles_errors(monkeypatch):
    fake_sd = ModuleType("sounddevice")
    fake_sd.query_hostapis = lambda: [
        {"name": "MME"},
        {"name": "Windows WASAPI"},
    ]
    fake_sd.query_devices = lambda: [
        {"name": "Hoparlör", "max_input_channels": 0, "hostapi": 1},
        {"name": "Dahili Mikrofon", "max_input_channels": 2, "hostapi": 0},
        {"name": "Dahili Mikrofon", "max_input_channels": 2, "hostapi": 1},
        {"name": "USB Kulaklık", "max_input_channels": 1, "hostapi": 1},
    ]
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)

    devices = list_input_devices()
    assert devices[0] == {"id": "default", "label": "Sistem Varsayılanı"}
    ids = [d["id"] for d in devices]
    assert "Hoparlör" not in ids
    assert ids.count("Dahili Mikrofon") == 1
    assert "USB Kulaklık" in ids

    # query_devices hata verirse yalnızca Sistem Varsayılanı döner
    fake_sd.query_devices = lambda: (_ for _ in ()).throw(RuntimeError("portaudio hatası"))
    assert list_input_devices() == [{"id": "default", "label": "Sistem Varsayılanı"}]

    # sounddevice hiç yoksa çökmez
    monkeypatch.setitem(sys.modules, "sounddevice", None)
    assert list_input_devices() == [{"id": "default", "label": "Sistem Varsayılanı"}]


def test_audio_recorder_device_selection_and_fallback(tmp_path, monkeypatch):
    opened_devices = []

    class FakeStream:
        def __init__(self, **kwargs):
            opened_devices.append(kwargs.get("device"))

        def start(self):
            pass

        def stop(self):
            pass

        def close(self):
            pass

    fake_sd = ModuleType("sounddevice")
    fake_sd.RawInputStream = FakeStream
    fake_sd.query_hostapis = lambda: [{"name": "Windows WASAPI"}]
    fake_sd.query_devices = lambda: [
        {"name": "Hoparlör", "max_input_channels": 0, "hostapi": 0},
        {"name": "USB Mic", "max_input_channels": 1, "hostapi": 0},
    ]
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)

    rec = AudioRecorder(temp_dir=tmp_path, device="USB Mic")
    rec.start()
    assert opened_devices[-1] == 1  # USB Mic cihaz indeksi
    rec.cancel()

    # Cihaz çıkarıldığında sistem varsayılanına (None) zarif düşüş
    rec.set_device("Artik Olmayan Mic")
    rec.start()
    assert opened_devices[-1] is None
    rec.cancel()


def test_controller_and_bridge_audio_devices(tmp_path, monkeypatch):
    fake_sd = ModuleType("sounddevice")
    fake_sd.query_devices = lambda: [
        {"name": "Masa Mikrofonu", "max_input_channels": 1},
    ]
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)

    rec = _FakeRecorder(tmp_path / "temp")
    ctrl = Controller(
        engine=_FakeEngine(),
        recorder=rec,
        hotkey=SimpleNamespace(configure=lambda k: None, start=lambda: None, stop=lambda: None, set_key=lambda k: None, set_mode=lambda m: None),
        clipper=lambda text: None,
        beeper=lambda kind: None,
        memory_provider=lambda gpu: None,
        load_in_background=False,
        indicator=_FakeIndicator(),
    )
    ctrl.load_engine()
    api = Api(ctrl)
    res = api.audio_devices()
    assert res["ok"] is True
    assert res["active"] == "default"
    assert any(d["id"] == "Masa Mikrofonu" for d in res["devices"])

    save_res = ctrl.settings_save({"input_device": "Masa Mikrofonu"})
    assert save_res["ok"] is True
    assert rec.device == "Masa Mikrofonu"
    assert ctrl.settings_get()["input_device"] == "Masa Mikrofonu"


# ---------- 4. FloatingIndicator ----------


def test_floating_indicator_states_and_headless_safety():
    ind = FloatingIndicator(enabled=True, headless=True)
    assert ind.visible is False

    ind.update(RECORDING)
    assert ind.visible is True
    assert ind.text == "Dinliyor..."

    ind.update(PROCESSING)
    assert ind.visible is True
    assert ind.text == "Yazıyor..."

    ind.update(CLEANING)
    assert ind.visible is True
    assert ind.text == "Yazıyor..."

    ind.update(READY)
    assert ind.visible is False

    ind.update(ERROR)
    assert ind.visible is False

    # Devre dışıyken asla görünmez
    ind.set_enabled(False)
    ind.update(RECORDING)
    assert ind.visible is False

    # Tekrar açılıp kayıt gelince görünür, close() sonrası görünmez
    ind.set_enabled(True)
    ind.update(RECORDING)
    assert ind.visible is True
    ind.set_enabled(False)
    assert ind.visible is False

    ind.close()
    ind.update(RECORDING)
    assert ind.visible is False


def test_controller_notifies_indicator_on_transitions_and_settings(tmp_path):
    ind = _FakeIndicator()
    rec = _FakeRecorder(tmp_path / "temp")
    ctrl = Controller(
        engine=_FakeEngine(),
        recorder=rec,
        hotkey=SimpleNamespace(configure=lambda k: None, start=lambda: None, stop=lambda: None, set_key=lambda k: None, set_mode=lambda m: None),
        clipper=lambda text: None,
        beeper=lambda kind: None,
        memory_provider=lambda gpu: None,
        load_in_background=False,
        indicator=ind,
    )
    ctrl.load_engine()
    assert READY in ind.states

    ctrl.toggle_record()
    assert RECORDING in ind.states
    ctrl.toggle_record()
    assert _wait_until(lambda: ctrl.snapshot()["state"] == READY and PROCESSING in ind.states)

    res = ctrl.settings_save({"show_indicator": False})
    assert res["ok"] is True
    assert ind.enabled is False
    assert ctrl.settings_get()["show_indicator"] is False

    ctrl.shutdown()
    assert ind.closed is True


# ---------- 5. Playwright UI Testleri ----------


@pytest.fixture(scope="module")
def ui_page():
    playwright_mod = pytest.importorskip("playwright.sync_api")
    from tests.test_ui import PAGE, STUB

    pw = playwright_mod.sync_playwright().start()
    try:
        browser = pw.chromium.launch(channel="msedge")
    except Exception as exc:
        pw.stop()
        pytest.skip(f"Edge tarayıcısı bulunamadı: {exc}")
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.add_init_script(STUB)
    page.goto(PAGE.as_uri())
    page.wait_for_function("() => document.querySelector('#statusText') !== null")
    yield page
    browser.close()
    pw.stop()


def test_ui_5_dokunus_ayarlar_ve_dikte_etkilesimi(ui_page):
    from tests.test_ui import PAGE

    ui_page.goto(PAGE.as_uri())
    ui_page.wait_for_function("() => document.querySelector('#statusText').textContent.includes('Model yükleniyor')")
    ui_page.evaluate("() => { window.__snap.state = 'ready'; }")
    ui_page.wait_for_function("() => document.querySelector('#statusText').textContent === 'Dinlemeye hazır'")

    # 1. Dikte alt ipucunda varsayılan basılı tut ipucu
    assert "Basılı tut ve konuş" in ui_page.locator("#shortcutHint").inner_text()

    # 2. Ayarlar sayfasına geç ve temel / gelişmiş düzeni doğrula
    ui_page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    ui_page.wait_for_function("() => document.querySelector('#page-ayarlar').classList.contains('is-active')")
    ui_page.wait_for_function("() => document.querySelectorAll('#micDeviceSelect option').length >= 2")

    # Gelişmiş ayarlar varsayılan open ve kapatılıp açılabiliyor
    adv = ui_page.locator("#advancedSettings")
    assert adv.evaluate("el => el.open") is True
    assert ui_page.locator("#aiCard").is_visible()
    adv.locator("summary").click()
    assert adv.evaluate("el => el.open") is False
    adv.locator("summary").click()
    assert adv.evaluate("el => el.open") is True

    # 3. Bas-Bırak modu seçimi ve anında kayıt
    ui_page.evaluate("() => { window.__calls = []; }")
    ui_page.locator("#hotkeyModeSelect").select_option("toggle")
    ui_page.wait_for_function("() => window.__calls.some(c => c.includes('\"hotkey_mode\":\"toggle\"'))")

    # Dikte ekranına dönünce alt ipucu toggle moduna göre güncellenmeli
    ui_page.locator('.nav-btn[data-page="page-dikte"]').click()
    ui_page.wait_for_function("() => document.querySelector('#shortcutHint').textContent.includes('Başlatmak için bas, bitirmek için tekrar bas')")

    # 4. Mikrofon seçimi + yenileme + gösterge anahtarı
    ui_page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    ui_page.wait_for_function("() => document.querySelectorAll('#micDeviceSelect option').length >= 2")
    ui_page.evaluate("() => { window.__calls = []; }")
    ui_page.locator("#micDeviceSelect").select_option(index=1)
    ui_page.wait_for_function("() => window.__calls.some(c => c.includes('\"input_device\":'))")

    ui_page.locator("#micRefreshBtn").click()
    ui_page.wait_for_function("() => window.__calls.includes('audio_devices')")

    ui_page.locator("#showIndicatorSwitch").click()
    assert ui_page.locator("#showIndicatorSwitch").get_attribute("aria-checked") == "false"
    ui_page.wait_for_function("() => window.__calls.some(c => c.includes('\"show_indicator\":false'))")
