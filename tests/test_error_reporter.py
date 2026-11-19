"""Gömülü hata yakalama, log döndürme, gizlilik maskeleme ve tanılama testleri."""

import json
import logging
import logging.handlers
from types import SimpleNamespace

import pytest

from dikte import config, diagnostics, error_reporter


@pytest.fixture(autouse=True)
def isolated_diag_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(config, "TEMP_DIR", tmp_path / "temp")
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "data" / "settings.json")
    monkeypatch.setattr(config, "HISTORY_FILE", tmp_path / "data" / "history.json")
    monkeypatch.setattr(config, "SECRETS_FILE", tmp_path / "data" / "secrets.json")
    monkeypatch.setattr(config, "LAST_RECORDING", tmp_path / "temp" / "last.wav")
    monkeypatch.setattr(error_reporter, "_previous_crash_info", None)
    monkeypatch.setattr(error_reporter, "_js_error_cache", {})
    config.ensure_runtime_dirs()


def test_setup_logging_uses_rotating_file_handler(monkeypatch):
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    for h in old_handlers:
        root.removeHandler(h)
    try:
        diagnostics.setup_logging()
        rotating = [h for h in root.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(rotating) == 1
        assert rotating[0].maxBytes == 2 * 1024 * 1024
        assert rotating[0].backupCount == 3
    finally:
        for h in list(root.handlers):
            root.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass
        for h in old_handlers:
            root.addHandler(h)


def test_sanitize_text_masks_keys_and_windows_user_paths():
    raw = (
        "key=sk-or-v1-abcdef1234567890 "
        "other=sk-1234567890abcdef12 "
        "Authorization: Bearer tok_secret_999 "
        "api_key=mysecretvalue123 "
        r"path=C:\Users\aksek\Desktop\dikte\file.txt "
        "slash=D:/Users/mehmet/AppData/Local/Dikte"
    )
    sanitized = error_reporter.sanitize_text(raw)
    assert "sk-or-v1-abcdef1234567890" not in sanitized
    assert "sk-1234567890abcdef12" not in sanitized
    assert "tok_secret_999" not in sanitized
    assert "mysecretvalue123" not in sanitized
    assert "aksek" not in sanitized
    assert "mehmet" not in sanitized
    assert r"C:\Users\<KULLANICI>" in sanitized
    assert "D:/Users/<KULLANICI>" in sanitized


def test_privacy_invariant_excludes_history_secrets_last_wav_and_latest():
    (config.DATA_DIR / "history.json").write_text(
        json.dumps([{"text": "GIZLI_KONUSMA_METNI_123"}]), encoding="utf-8"
    )
    (config.DATA_DIR / "secrets.json").write_text(
        json.dumps({"openrouter_api_key": "sk-or-v1-supersecretkey999"}), encoding="utf-8"
    )
    (config.TEMP_DIR / "last.wav").write_bytes(b"RIFF_SECRET_AUDIO")

    fake_settings = SimpleNamespace(
        get=lambda key: "large-v3" if key == "active_model" else None
    )
    fake_controller = SimpleNamespace(
        snapshot=lambda: {
            "state": "ready",
            "model_name": "large-v3",
            "device": "CPU",
            "hotkey_id": "right_ctrl",
            "error": None,
            "latest_text": "COK_GIZLI_DIKTE_METNI_XYZ",
            "activity": [],
        },
        settings=fake_settings,
        _latest="COK_GIZLI_DIKTE_METNI_XYZ",
    )

    payload = error_reporter.get_diagnostics_payload(fake_controller)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "GIZLI_KONUSMA_METNI_123" not in serialized
    assert "sk-or-v1-supersecretkey999" not in serialized
    assert "COK_GIZLI_DIKTE_METNI_XYZ" not in serialized
    assert "RIFF_SECRET_AUDIO" not in serialized


def test_mark_running_start_and_clean_shutdown_and_dismiss_crash():
    # Temiz ilk başlatma
    assert error_reporter.mark_running_start() is False
    assert (config.DATA_DIR / "running.lock").exists()

    # Temiz kapanış kilidi siler
    error_reporter.mark_clean_shutdown()
    assert not (config.DATA_DIR / "running.lock").exists()

    # Kirli kapanış simülasyonu (running.lock duruyor)
    (config.DATA_DIR / "running.lock").write_text('{"pid": 9999}', encoding="utf-8")
    (config.DATA_DIR / "last_crash.json").write_text(
        json.dumps({"type": "RuntimeError", "message": "boom"}), encoding="utf-8"
    )
    assert error_reporter.mark_running_start() is True
    diag = error_reporter.analyze_errors()
    assert diag["has_issue"] is True
    assert diag["code"] == "previous_crash"
    assert diag["crash_detected"] is True

    # Çökme uyarısını kapatma
    error_reporter.dismiss_crash()
    assert not (config.DATA_DIR / "last_crash.json").exists()
    diag_after = error_reporter.analyze_errors()
    assert diag_after["crash_detected"] is False


@pytest.mark.parametrize(
    "log_text,expected_code",
    [
        ("av.open metadata_errors failed", "pyav_incompatible"),
        ("cublas64_12.dll not found", "cuda_dll_missing"),
        ("WebView2 runtime not found", "webview2_missing"),
        ("invalid gguf model error", "model_missing_or_corrupt"),
        ("SSL: CERTIFICATE_VERIFY_FAILED huggingface", "network_hf_ssl"),
        ("PortAudioError: no default input device", "mic_permission_or_device"),
        ("hotkey listener failed", "hotkey_hook_failed"),
        ("SendInput UIPI blocked failed", "paste_uipi_blocked"),
        ("OpenRouter HTTP 401 unauthorized", "openrouter_auth_quota"),
        ("llama_cpp out of memory error", "llama_oom_or_missing"),
        ("UI JS hatası: TypeError: null", "js_error"),
    ],
)
def test_analyze_errors_classification_rules(monkeypatch, log_text, expected_code):
    monkeypatch.setattr(error_reporter, "_read_pyav_info", lambda: ("12.0.0", True))
    (config.LOG_DIR / "dikte.log").write_text(log_text + "\n", encoding="utf-8")
    diag = error_reporter.analyze_errors()
    assert diag["has_issue"] is True
    assert diag["code"] == expected_code


def test_analyze_errors_clean_state(monkeypatch):
    monkeypatch.setattr(error_reporter, "_read_pyav_info", lambda: ("12.0.0", True))
    diag = error_reporter.analyze_errors()
    assert diag["has_issue"] is False
    assert diag["severity"] == "ok"
    assert diag["code"] is None


def test_export_report_writes_sanitized_txt():
    (config.LOG_DIR / "dikte.log").write_text(
        r"Hata: sk-or-v1-secret999 C:\Users\gizliuser\test.py", encoding="utf-8"
    )
    out_path = error_reporter.export_report()
    assert out_path.exists()
    assert out_path.parent == config.LOG_DIR
    content = out_path.read_text(encoding="utf-8")
    assert "DİKTE TANILAMA RAPORU" in content
    assert "sk-or-v1-secret999" not in content
    assert "gizliuser" not in content


def test_record_js_error_throttling(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(error_reporter.time, "monotonic", lambda: now[0])

    r1 = error_reporter.record_js_error({"message": "Script error", "source": "app.js", "line": 10})
    assert r1 == {"ok": True}

    now[0] = 105.0
    r2 = error_reporter.record_js_error({"message": "Script error", "source": "app.js", "line": 10})
    assert r2 == {"ok": True, "throttled": True}

    now[0] = 131.0
    r3 = error_reporter.record_js_error({"message": "Script error", "source": "app.js", "line": 10})
    assert r3 == {"ok": True}


def test_sanitize_text_masks_spaced_windows_username():
    raw = (
        r"err=C:\Users\Ali Veli\AppData\Local\Dikte\dikte.log "
        "url=D:/Users/Ali Veli/AppData/Roaming/file.txt"
    )
    sanitized = error_reporter.sanitize_text(raw)
    assert "Ali Veli" not in sanitized
    assert r"C:\Users\<KULLANICI>\AppData\Local\Dikte\dikte.log" in sanitized
    assert "D:/Users/<KULLANICI>/AppData/Roaming/file.txt" in sanitized


def test_format_report_includes_native_crash_tail():
    (config.LOG_DIR / "native_crash.log").write_text(
        "Windows fatal exception: access violation at 0x0000\n",
        encoding="utf-8",
    )
    report = error_reporter.format_report_text()
    assert "[ÇÖKME BİLGİSİ]" in report
    assert "Yerel (Native) Çökme Kaydı:" in report
    assert "Windows fatal exception: access violation" in report


def test_setup_logging_attaches_file_handler_even_with_preexisting_root_handler():
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    for h in old_handlers:
        root.removeHandler(h)
    preexisting = logging.StreamHandler()
    root.addHandler(preexisting)
    try:
        diagnostics.setup_logging()
        diagnostics.setup_logging()  # İkinci çağrı mükerrer eklememeli
        rotating = [h for h in root.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(rotating) == 1
        assert rotating[0].baseFilename.endswith("dikte.log")
    finally:
        for h in list(root.handlers):
            root.removeHandler(h)
            if h is not preexisting:
                try:
                    h.close()
                except Exception:
                    pass
        try:
            preexisting.close()
        except Exception:
            pass
        for h in old_handlers:
            root.addHandler(h)
