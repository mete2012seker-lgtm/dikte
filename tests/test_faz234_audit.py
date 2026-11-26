"""Kod Denetimi Faz 2, Faz 3 ve Faz 4 TDD regresyon testleri."""

from __future__ import annotations

import io
import json
import sys
import threading
import urllib.error
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from dikte import __main__ as dikte_main
from dikte import config, error_reporter, openrouter, text_engine, text_models, uninstall, updater
from dikte.controller import Controller

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "dikte" / "ui" / "index.html"


# ---------------- Faz 3: Kurucu, __main__, error_reporter, updater, openrouter, uninstall, requirements ----------------


def test_y6_dikte_iss_cleans_env_temp_and_no_unused_macro():
    iss = (ROOT / "installer" / "Dikte.iss").read_text(encoding="utf-8")
    assert r"{%TEMP}\dikte" in iss
    assert r"{tmp}\dikte" not in iss
    assert "MyAppExeName" not in iss


def test_o1_cmd_ui_does_not_swallow_type_error_with_second_run_app(monkeypatch):
    calls = []

    def bad_run_app(controller, debug=False, start_in_tray=False):
        calls.append((debug, start_in_tray))
        raise TypeError("gercek baslangic hatasi")

    fake_bridge = ModuleType("dikte.ui.bridge")
    fake_bridge.run_app = bad_run_app
    monkeypatch.setitem(sys.modules, "dikte.ui.bridge", fake_bridge)
    monkeypatch.setattr("dikte.controller.Controller", lambda engine=None: SimpleNamespace(maybe_startup_update_check=lambda: None))
    monkeypatch.setattr(dikte_main, "TranscriptionEngine", lambda force_device=None: object())

    with pytest.raises(TypeError, match="gercek baslangic hatasi"):
        dikte_main.cmd_ui(None, debug=False, start_in_tray=True)
    assert len(calls) == 1


def test_error_reporter_masks_double_backslash_json_user_path():
    raw = r'{"path": "C:\\Users\\aksek\\AppData\\Local\\Dikte\\dikte.log"}'
    sanitized = error_reporter.sanitize_text(raw)
    assert "aksek" not in sanitized
    assert "<KULLANICI>" in sanitized


def test_error_reporter_truncates_large_native_crash_log(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    data_dir = tmp_path / "data"
    temp_dir = tmp_path / "temp"
    models_dir = tmp_path / "models"
    monkeypatch.setattr(config, "LOG_DIR", log_dir)
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    monkeypatch.setattr(config, "TEMP_DIR", temp_dir)
    monkeypatch.setattr(config, "MODELS_DIR", models_dir)
    config.ensure_runtime_dirs()

    native = log_dir / "native_crash.log"
    native.write_bytes(b"A" * (600 * 1024) + b"\nLAST_LINE_OK\n")

    old_fh = error_reporter._faulthandler_file
    error_reporter._faulthandler_file = None
    monkeypatch.setattr(error_reporter.faulthandler, "enable", lambda **_k: None)
    try:
        error_reporter.install_global_hooks()
    finally:
        if error_reporter._faulthandler_file is not None:
            try:
                error_reporter._faulthandler_file.close()
            except Exception:
                pass
        error_reporter._faulthandler_file = old_fh

    assert native.stat().st_size <= 512 * 1024
    assert b"LAST_LINE_OK" in native.read_bytes()


def test_error_reporter_rule5_requires_same_line_match():
    collected = {
        "env": {"pyav_compatible": True, "sounddevice_input": True},
        "runtime": {"current_error": None},
        "log_tail": (
            "2026-11-24 10:00:00 | INFO | dikte.text_models | model.gguf yuklendi\n"
            "2026-11-24 10:00:05 | ERROR | dikte.text_models | llama_cpp out of memory error\n"
        ),
        "crash_info": None,
    }
    diag = error_reporter._analyze_collected(collected)
    assert diag["code"] == "llama_oom_or_missing"


def test_controller_update_messages_and_single_sha256_hash(tmp_path, monkeypatch):
    assert "cancelled" in Controller.UPDATE_MESSAGES
    assert "launch_failed" in Controller.UPDATE_MESSAGES

    installer_file = tmp_path / "Dikte-Setup-9.0.0.exe"
    installer_file.write_bytes(b"kurucu-icerik")
    import hashlib

    sha = hashlib.sha256(b"kurucu-icerik").hexdigest()
    monkeypatch.setattr(updater, "check", lambda force=True: {
        "update_available": True,
        "version": "9.0.0",
        "url": "https://ornek/Dikte-Setup-9.0.0.exe",
        "sha256": sha,
    })

    def fake_download(url, cancel_event=None, sha256=None):
        assert sha256 == sha
        return installer_file

    verify_calls = []
    monkeypatch.setattr(updater, "download", fake_download)
    monkeypatch.setattr(updater, "verify_sha256", lambda *a, **k: verify_calls.append(1) or True)
    monkeypatch.setattr(updater, "apply", lambda p: None)

    stub = SimpleNamespace(
        UPDATE_MESSAGES=Controller.UPDATE_MESSAGES,
        _update_cancel_event=threading.Event(),
        _schedule_exit_after_apply=lambda: None,
    )
    res = Controller.update_apply(stub)
    assert res["ok"] is True
    assert verify_calls == []


def test_updater_rejects_empty_expected_host_and_handles_bad_content_length(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPDATE_URL", "")
    with pytest.raises(updater.UpdaterError) as exc:
        updater.download("https://evil.com/Dikte-Setup.exe", dest_dir=tmp_path)
    assert exc.value.code == "host_rejected"

    monkeypatch.setattr(config, "UPDATE_URL", "https://ornek/latest.json")

    class BadHeaderResp(io.BytesIO):
        headers = {"Content-Length": "not-a-number"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *_a, **_k: BadHeaderResp(b"kurucu"))
    path = updater.download("https://ornek/Dikte.exe", dest_dir=tmp_path, allow_missing_sha256=True)
    assert path.exists()


@pytest.mark.parametrize(
    "http_code,expected_code",
    [(403, "403"), (400, "bad_response"), (404, "bad_response")],
)
def test_openrouter_maps_403_400_404(monkeypatch, http_code, expected_code):
    def boom(*_a, **_k):
        raise urllib.error.HTTPError("https://openrouter.ai/api/v1/models", http_code, "err", {}, None)

    monkeypatch.setattr(openrouter.urllib.request, "urlopen", boom)
    with pytest.raises(openrouter.OpenRouterError) as exc:
        openrouter._request_json("https://openrouter.ai/api/v1/models")
    assert exc.value.code == expected_code
    assert "403" in text_engine.CODE_MESSAGES


def test_uninstall_autostart_uses_module_flag_when_not_packaged(monkeypatch):
    class FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class FakeWinreg:
        HKEY_CURRENT_USER = 1
        KEY_SET_VALUE = 2
        KEY_QUERY_VALUE = 1
        REG_SZ = 1

        def __init__(self):
            self.values = {}

        def OpenKey(self, root, path, _res, access):
            assert root == self.HKEY_CURRENT_USER
            assert path == config.AUTOSTART_RUN_KEY
            assert access in (self.KEY_SET_VALUE, self.KEY_QUERY_VALUE)
            return FakeKey()

        def SetValueEx(self, _k, name, _r, _t, value):
            self.values[name] = value

    fake = FakeWinreg()
    monkeypatch.setitem(sys.modules, "winreg", fake)
    monkeypatch.setattr(config, "is_packaged", lambda: False)
    uninstall.set_autostart(True)
    assert "-m dikte --tray" in fake.values[config.AUTOSTART_VALUE]

    monkeypatch.setattr(config, "is_packaged", lambda: True)
    uninstall.set_autostart(True)
    assert "-m dikte" not in fake.values[config.AUTOSTART_VALUE]
    assert fake.values[config.AUTOSTART_VALUE].endswith("--tray")


def test_requirements_txt_includes_onnxruntime():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "onnxruntime" in req


# ---------------- Faz 4: fsutil, text_engine local, engine mock branch ----------------


def test_fsutil_atomic_write_and_backup(tmp_path):
    from dikte import fsutil

    target = tmp_path / "sub" / "data.json"
    fsutil.atomic_write_json(target, {"a": "ğüşiçö"})
    assert json.loads(target.read_text(encoding="utf-8")) == {"a": "ğüşiçö"}

    backup = fsutil.backup_corrupt_path(target)
    assert ".bozuk-" in backup.name
    assert backup.parent == target.parent


def test_text_engine_local_provider_with_runtime():
    attempts = []

    class FakeLocalRuntime:
        def generate(self, system, user, max_tokens=512):
            attempts.append((system, user, max_tokens))
            if len(attempts) == 1:
                return "yarın sabah toplantı var"
            return "Tomorrow morning there is a meeting."

    res = text_engine.generate(
        "yarın sabah toplantı var",
        target_language="en",
        translate=True,
        provider="local",
        local_runtime=FakeLocalRuntime(),
    )
    assert res.text == "Tomorrow morning there is a meeting."
    assert len(attempts) == 2
    assert "DİKKAT" in attempts[1][0]
    assert attempts[1][2] >= attempts[0][2]

    cancel = threading.Event()
    cancel.set()
    with pytest.raises(text_engine.TextEngineError) as exc:
        text_engine.generate(
            "yarın sabah toplantı var",
            provider="local",
            local_runtime=FakeLocalRuntime(),
            cancel_event=cancel,
        )
    assert exc.value.code == "cancelled"


def test_engine_passes_vad_and_prompt_even_for_magicmock(tmp_path):
    from dikte.engine import TranscriptionEngine

    engine = TranscriptionEngine(model_dir=tmp_path)
    mock_model = MagicMock()
    seg = MagicMock()
    seg.text = "Merhaba"
    mock_model.transcribe.return_value = ([seg], MagicMock(duration=1.0))
    engine._model = mock_model

    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFF")
    engine.transcribe(wav, language="tr")

    kwargs = mock_model.transcribe.call_args.kwargs
    assert "vad_parameters" in kwargs
    assert "initial_prompt" in kwargs


# ---------------- Faz 2: Playwright UI denetim testleri ----------------


def _ui_stub() -> str:
    from tests.test_ui import STUB

    return STUB


@pytest.fixture()
def ui_page():
    playwright_mod = pytest.importorskip("playwright.sync_api")
    pw = playwright_mod.sync_playwright().start()
    try:
        browser = pw.chromium.launch(channel="msedge")
    except Exception as exc:
        pw.stop()
        pytest.skip(f"Edge tarayıcısı bulunamadı: {exc}")
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.add_init_script(_ui_stub())
    page.goto(PAGE.as_uri())
    page.wait_for_function("() => document.querySelector('#statusText') !== null")
    yield page
    browser.close()
    pw.stop()


def test_y4_instant_save_failure_keeps_settings_dirty_and_shows_toast(ui_page):
    ui_page.evaluate("""() => {
      window.pywebview.api.settings_save = async () => ({ ok: false, message: "Salt okunur disk hatası" });
    }""")
    ui_page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    ui_page.wait_for_function("() => document.querySelectorAll('#hotkeySelect option').length === 7")
    ui_page.locator("#hotkeySelect").select_option("f9")
    ui_page.wait_for_timeout(550)
    assert not ui_page.locator("#settingsDirty").is_hidden()
    assert "Salt okunur disk hatası" in ui_page.locator("#toastWrap").inner_text()


def test_y5_call_api_protects_custom_remove_cancel_and_or_key(ui_page):
    unhandled = []
    ui_page.on("pageerror", lambda err: unhandled.append(str(err)))
    ui_page.evaluate("""() => {
      window.confirm = () => true;
      window.__models.text_items[0].custom = true;
      window.__models.items[2].custom = true;
      window.__models.download = { name: "tiny", label: "Whisper Tiny", state: "downloading", percent: 50, bytes: 50, total: 100 };
      window.__models.items[2].downloading = true;
      window.pywebview.api.text_models_remove_custom = async () => ({ ok: false, message: "Metin silinemedi" });
      window.pywebview.api.models_cancel_download = async () => ({ ok: false, message: "İptal başarısız" });
      window.pywebview.api.models_remove_custom = async () => ({ ok: false, message: "Ses silinemedi" });
      window.pywebview.api.openrouter_key_save = async () => { throw new Error("DPAPI hatası"); };
      window.pywebview.api.openrouter_key_delete = async () => { throw new Error("Silme hatası"); };
    }""")
    ui_page.locator('.nav-btn[data-page="page-modeller"]').click()
    ui_page.wait_for_function("() => document.querySelectorAll('#modelList .m-card').length === 2")

    # Text custom remove failure must show warn toast, not success
    ui_page.locator('#modelList .m-card[data-name="qwen3-4b"] .model-menu-btn').click()
    ui_page.locator('#modelList .m-card[data-name="qwen3-4b"] .model-dropdown-item', has_text="Listeden Kaldır").click()
    ui_page.wait_for_function("() => document.querySelector('#toastWrap').innerText.includes('Metin silinemedi')")

    # Audio cancel failure & remove failure
    ui_page.locator("#tabAudio").click()
    ui_page.wait_for_function("() => document.querySelectorAll('#modelList .m-card').length === 3")
    ui_page.locator('#modelList .m-card[data-name="tiny"] .m-btn', has_text="İptal").click()
    ui_page.wait_for_function("() => document.querySelector('#toastWrap').innerText.includes('İptal başarısız')")

    ui_page.locator('#modelList .m-card[data-name="tiny"] .model-menu-btn').click()
    ui_page.locator('#modelList .m-card[data-name="tiny"] .model-dropdown-item', has_text="Listeden Kaldır").click()
    ui_page.wait_for_function("() => document.querySelector('#toastWrap').innerText.includes('Ses silinemedi')")

    # OpenRouter save & delete reject safely without unhandled pageerror
    ui_page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    ui_page.wait_for_function("() => !document.querySelector('#textProvider').disabled")
    ui_page.select_option("#textProvider", "openrouter")
    ui_page.fill("#orKeyInput", "sk-or-v1-12345678")
    ui_page.locator("#orKeySave").click()
    ui_page.wait_for_timeout(150)
    assert unhandled == []


def test_faz2_visibility_pauses_polling_and_raf(ui_page):
    ui_page.evaluate("""() => {
      window.__snapCalls = 0;
      const origSnap = window.pywebview.api.snapshot;
      window.pywebview.api.snapshot = async () => { window.__snapCalls++; return origSnap(); };
      window.__rafCount = 0;
      const origRaf = window.requestAnimationFrame.bind(window);
      window.requestAnimationFrame = (fn) => { window.__rafCount++; return origRaf(fn); };
    }""")
    ui_page.wait_for_timeout(350)
    assert ui_page.evaluate("() => window.__snapCalls > 0 && window.__rafCount > 0")

    ui_page.evaluate("""() => {
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
      document.dispatchEvent(new Event('visibilitychange'));
      window.__snapCalls = 0;
      window.__rafCount = 0;
    }""")
    ui_page.wait_for_timeout(450)
    assert ui_page.evaluate("() => window.__snapCalls === 0")
    assert ui_page.evaluate("() => window.__rafCount === 0")

    ui_page.evaluate("""() => {
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    ui_page.wait_for_timeout(350)
    assert ui_page.evaluate("() => window.__snapCalls > 0 && window.__rafCount > 0")


def test_faz2_menu_modal_search_double_delete_notes_and_keys(ui_page):
    # 1. Menu & modal outside click / Escape / input reset
    ui_page.locator('.nav-btn[data-page="page-modeller"]').click()
    ui_page.wait_for_function("() => document.querySelectorAll('#modelList .m-card').length === 2")
    ui_page.locator(".model-menu-btn").first.click()
    assert ui_page.locator(".model-dropdown.is-open").count() == 1
    ui_page.keyboard.press("Escape")
    assert ui_page.locator(".model-dropdown.is-open").count() == 0

    ui_page.locator(".model-menu-btn").first.click()
    assert ui_page.locator(".model-dropdown.is-open").count() == 1
    ui_page.locator("#modelSearch").click()
    assert ui_page.locator(".model-dropdown.is-open").count() == 0

    ui_page.locator("#addCustomModelBtn").click()
    ui_page.fill("#customModelRepo", "stale/repo")
    ui_page.fill("#customModelLabel", "Stale Label")
    ui_page.keyboard.press("Escape")
    assert ui_page.locator("#customModelModal").is_hidden()
    ui_page.locator("#addCustomModelBtn").click()
    assert ui_page.locator("#customModelRepo").input_value() == ""
    assert ui_page.locator("#customModelLabel").input_value() == ""
    ui_page.locator("#customModelClose").click()

    # 2. Audio search uses visible.some(...) and active model "Dosyayı Sil" is disabled
    ui_page.locator("#tabAudio").click()
    ui_page.wait_for_function("() => document.querySelectorAll('#modelList .m-card').length === 3")
    active_del = ui_page.locator('#modelList .m-card[data-name="large-v3"] .model-dropdown-item', has_text="Dosyayı Sil")
    assert active_del.is_disabled()
    ui_page.fill("#modelSearch", "Tiny")
    assert "Whisper Tiny" in ui_page.locator("#detailName").inner_text()
    ui_page.fill("#modelSearch", "")

    # 3. History delete double-click lock during 200ms animation
    ui_page.evaluate("() => { window.__calls = []; }")
    ui_page.locator('.nav-btn[data-page="page-gecmis"]').click()
    ui_page.wait_for_function("() => document.querySelectorAll('#historyList .h-item').length === 2")
    del_btn = ui_page.locator('#historyList .h-item[data-id="h1"] .btn-danger')
    del_btn.click()
    del_btn.click(force=True)
    ui_page.wait_for_function("() => document.querySelectorAll('#historyList .h-item').length === 1")
    assert ui_page.evaluate("() => window.__calls.filter(c => c === 'history_delete:h1').length") == 1

    # 4. Update notes populated & button label preserved on success
    ui_page.evaluate("""() => {
      window.__updateResult = {
        ok: true, update_available: true, version: "1.7.0",
        url: "https://ornek/Dikte-Setup-1.7.0.exe", sha256: "a".repeat(64),
        notes: "Sürüm notları: performans iyileştirildi.", message: "Yeni sürüm: 1.7.0"
      };
      window.__updateApplyResult = { ok: true, message: "Kurulum başlatıldı." };
    }""")
    ui_page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    ui_page.wait_for_function("() => document.querySelectorAll('#hotkeySelect option').length === 7")
    ui_page.locator("#updateCheckBtn").click()
    ui_page.wait_for_function("() => document.querySelector('#updateNotes').textContent.includes('performans iyileştirildi')")
    ui_page.locator("#updateApplyBtn").click()
    ui_page.wait_for_function("() => document.querySelector('#updateStatus').textContent.includes('Kurulum')")
    assert ui_page.locator("#updateApplyBtn").is_disabled()
    assert ui_page.locator("#updateApplyBtn").inner_text() != "Uygulamayı Güncelle"

    # 5. Wizard finish keeps wizard open when wizard_complete fails & avoids double settings_save
    ui_page.evaluate("""() => {
      window.__calls = [];
      window.pywebview.api.wizard_complete = async (p) => {
        window.__calls.push("wizard_complete:" + JSON.stringify(p));
        return { ok: false, message: "Sihirbaz kaydedilemedi" };
      };
    }""")
    ui_page.locator("#restartWizardBtn").click()
    for _ in range(4):
        ui_page.locator("#wizardNextBtn").click()
    ui_page.locator("#wizardFinishBtn").click()
    ui_page.wait_for_function("() => document.querySelector('#toastWrap').innerText.includes('Sihirbaz kaydedilemedi')")
    assert not ui_page.locator("#welcomeWizard").is_hidden()
    assert not ui_page.evaluate("() => window.__calls.some(c => c.startsWith('settings_save:'))")
