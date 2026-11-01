"""Temizle/Çevir akışı: sağlayıcı kapalı, başarı, hata ve otomatik çeviri."""

import time
from pathlib import Path

import pytest

from dikte import config
from dikte.audio import Recording
from dikte.controller import Controller
from dikte.engine import EngineInfo, TranscriptResult
from dikte.settings import SettingsStore
from dikte.state import READY
from dikte.text_engine import TextEngineError, TextResult


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TEMP_DIR", tmp_path / "temp")
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(config, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(config, "LAST_RECORDING", tmp_path / "last.wav")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    (tmp_path / "temp").mkdir(exist_ok=True)


class FakeEngine:
    def __init__(self, text="Merhaba dünya bugün güzel"):
        self.text = text
        self.warnings = []
        self.model_name = None

    def set_model(self, name):
        self.model_name = name

    def load(self):
        return EngineInfo("large-v3", "Whisper Large", "GPU", "float16", 0.1)

    def transcribe(self, wav_path):
        return TranscriptResult(self.text, 1.0, 0.1)


class FakeRecorder:
    def __init__(self, duration=2.0):
        self.duration = duration
        self.recording = False
        self.path = None

    def start(self):
        self.recording = True

    def stop(self):
        self.recording = False
        self.path = Path(config.TEMP_DIR) / f"test-{time.time_ns()}.wav"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(b"RIFF-test")
        return Recording(path=self.path, duration=self.duration, frames=32000)

    def cancel(self):
        self.recording = False

    def cleanup(self, path):
        if path:
            Path(path).unlink(missing_ok=True)


class FakeHotkey:
    def __init__(self):
        self.key = "right_ctrl"

    def configure(self, key):
        self.key = key

    def set_key(self, key):
        self.key = key

    def start(self):
        pass

    def stop(self):
        pass


class FakeSecrets:
    def __init__(self, key="sk-or-v1-abcdef1234"):
        self.key = key

    def load_key(self):
        return self.key

    def save_key(self, key):
        self.key = key
        return "sk-or-…" + key[-4:]

    def delete_key(self):
        had = self.key is not None
        self.key = None
        return had

    def masked(self):
        return None


class FakeProcessor:
    def __init__(self, result="İşlenmiş metin", error=None):
        self.result = result
        self.error = error
        self.calls = []

    def __call__(self, text, **kwargs):
        self.calls.append({"text": text, **kwargs})
        if self.error:
            raise self.error
        return TextResult(self.result, kwargs.get("translate", True))


def make_controller(engine=None, processor=None, secrets=None, clipper=None, text=None, model_lister=None):
    settings = SettingsStore(config.SETTINGS_FILE)
    controller = Controller(
        engine=engine or FakeEngine(),
        recorder=FakeRecorder(),
        hotkey=FakeHotkey(),
        clipper=clipper or (lambda text: None),
        beeper=lambda kind: None,
        memory_provider=lambda use_gpu: None,
        load_in_background=False,
        settings_store=settings,
        secret_store=secrets or FakeSecrets(),
        text_processor=processor or FakeProcessor(),
        model_lister=model_lister,
    )
    controller.load_engine()
    return controller


def dictation(controller, text=None):
    controller.toggle_record()
    controller.toggle_record()
    assert controller.wait_until_ready(5)


def test_provider_none_blocks_clean_and_keeps_state():
    controller = make_controller()
    result = controller.clean_text("Merhaba dünya.")
    assert result["ok"] is False
    assert result["code"] == "provider_off"
    assert controller.snapshot()["state"] == READY
    assert controller.snapshot()["seq"] == 0


def test_clean_text_returns_processed_text_and_copies():
    copied = []
    processor = FakeProcessor(result="Merhaba dünya.")
    controller = make_controller(processor=processor, clipper=copied.append)
    controller.settings.save(text_provider="openrouter", openrouter_model="test/model")

    result = controller.clean_text("merhaba dünya")
    assert result["ok"] is True
    assert result["text"] == "Merhaba dünya."
    assert copied == ["Merhaba dünya."]
    assert processor.calls[0]["translate"] is False
    assert processor.calls[0]["api_key"] == "sk-or-v1-abcdef1234"
    assert controller.snapshot()["state"] == READY


def test_translate_uses_target_language_and_translate_flag():
    processor = FakeProcessor(result="Hello world.")
    controller = make_controller(processor=processor)
    controller.settings.save(
        text_provider="openrouter", openrouter_model="test/model", output_language="en"
    )

    result = controller.translate_text("merhaba dünya")
    assert result["ok"] is True
    assert result["translated"] is True
    call = processor.calls[0]
    assert call["translate"] is True
    assert call["target_language"] == "en"


def test_failed_clean_does_not_change_text():
    processor = FakeProcessor(error=TextEngineError("401"))
    controller = make_controller(processor=processor)
    controller.settings.save(text_provider="openrouter", openrouter_model="test/model")

    result = controller.clean_text("Merhaba dünya.")
    snapshot = controller.snapshot()
    assert result["ok"] is False
    assert result["code"] == "401"
    assert snapshot["latest_text"] == ""
    assert snapshot["state"] == READY
    assert snapshot["activity"][0]["kind"] == "err"


def test_auto_translate_applies_after_dictation():
    processor = FakeProcessor(result="Hello world today nice")
    controller = make_controller(processor=processor)
    controller.settings.save(
        text_provider="openrouter",
        openrouter_model="test/model",
        auto_translate=True,
        output_language="en",
    )

    dictation(controller)
    snapshot = controller.snapshot()
    assert snapshot["seq"] == 1
    assert snapshot["latest_text"] == "Hello world today nice"
    assert snapshot["state"] == READY
    assert processor.calls[0]["target_language"] == "en"


def test_auto_translate_skips_short_text():
    processor = FakeProcessor(result="değişmemeli")
    controller = make_controller(engine=FakeEngine(text="Merhaba dünya"), processor=processor)
    controller.settings.save(text_provider="openrouter", auto_translate=True)

    dictation(controller)
    snapshot = controller.snapshot()
    assert snapshot["latest_text"] == "Merhaba dünya"
    assert processor.calls == []
    assert any(item["title"] == "Kısa metin" for item in snapshot["activity"])


def test_auto_translate_failure_keeps_raw_text():
    processor = FakeProcessor(error=TextEngineError("net"))
    controller = make_controller(processor=processor)
    controller.settings.save(text_provider="openrouter", auto_translate=True)

    dictation(controller)
    snapshot = controller.snapshot()
    assert snapshot["latest_text"] == "Merhaba dünya bugün güzel"
    assert any(item["title"] == "Otomatik çeviri yapılamadı" for item in snapshot["activity"])


def test_ai_settings_save_normalizes_invalid_provider():
    controller = make_controller()
    result = controller.ai_settings_save({"text_provider": "bulut", "output_language": "de"})
    assert result["ok"] is True
    assert controller.settings.get("text_provider") == "none"
    assert controller.settings.get("output_language") == "de"


def test_ai_settings_save_ignores_unknown_keys():
    controller = make_controller()
    controller.ai_settings_save({"secret_backdoor": True})
    assert controller.settings.get("secret_backdoor") is None


def test_key_save_and_delete_updates_state():
    secrets = FakeSecrets(key=None)
    controller = make_controller(secrets=secrets)
    assert controller.snapshot()["ai"]["key_set"] is False

    saved = controller.openrouter_key_save("sk-or-v1-abcd9999")
    assert saved["ok"] is True
    assert controller.snapshot()["ai"]["key_set"] is True
    assert controller.snapshot()["ai"]["key_masked"].endswith("9999")

    deleted = controller.openrouter_key_delete()
    assert deleted["ok"] is True
    assert controller.snapshot()["ai"]["key_set"] is False


def test_key_test_without_key_reports_no_key():
    controller = make_controller(secrets=FakeSecrets(key=None))
    result = controller.openrouter_key_test()
    assert result["ok"] is False
    assert result["code"] == "no_key"


def test_openrouter_key_is_not_required_for_local_provider_state():
    controller = make_controller(secrets=FakeSecrets(key=None))
    controller.settings.save(text_provider="local")
    snapshot = controller.snapshot()
    assert snapshot["ai"]["provider"] == "local"


def test_busy_state_rejects_manual_clean():
    controller = make_controller()
    controller.settings.save(text_provider="openrouter", openrouter_model="test/model")
    controller.toggle_record()  # RECORDING
    result = controller.clean_text("Merhaba dünya.")
    assert result["ok"] is False
    assert "bekle" in result["message"]


def test_invalid_provider_in_file_does_not_break_startup():
    """Kullanıcı ayar dosyasını elle bozsa da uygulama açılır."""
    (config.SETTINGS_FILE).write_text(
        '{"text_provider": "bulut", "output_language": "xx", "auto_translate": "evet"}',
        encoding="utf-8",
    )
    controller = make_controller()
    snapshot = controller.snapshot()
    assert snapshot["state"] == READY
    assert snapshot["ai"]["provider"] == "none"
    assert snapshot["ai"]["output_language"] == "tr"
    assert snapshot["ai"]["auto_translate"] is False
    assert controller.clean_text("Merhaba dünya.")["code"] == "provider_off"


def test_openrouter_models_all_and_query():
    calls = []

    def lister(refresh=False, all_models=False):
        calls.append(all_models)
        return [
            {"id": "openai/pahali", "name": "OpenAI Pahalı", "input_price": 5.0,
             "output_price": 15.0, "context": 128000},
            {"id": "qwen/ucuz", "name": "Qwen Ucuz", "input_price": 0.05,
             "output_price": 0.10, "context": 32000},
        ]

    controller = make_controller(model_lister=lister)
    result = controller.openrouter_models(all_models=True)
    assert result["ok"] is True
    assert result["total"] == 2
    assert calls[-1] is True
    assert result["models"][0]["price_label"].startswith("~$")
    assert result["models"][0]["context_label"] == "128K bağlam"

    filtered = controller.openrouter_models(all_models=True, query="qwen")
    assert [m["id"] for m in filtered["models"]] == ["qwen/ucuz"]

    cheap = controller.openrouter_models()
    assert calls[-1] is False
    assert len(cheap["models"]) == 2


def test_model_lister_error_returns_turkish_message():
    from dikte.openrouter import OpenRouterError

    def lister(refresh=False, all_models=False):
        raise OpenRouterError("net", "yok")

    result = make_controller(model_lister=lister).openrouter_models()
    assert result["ok"] is False
    assert result["code"] == "net"
    assert "ulaşılamadı" in result["message"]


def test_show_all_setting_persists():
    controller = make_controller()
    controller.ai_settings_save({"openrouter_show_all": True})
    assert controller.snapshot()["ai"]["openrouter_show_all"] is True


def test_router_model_setting_is_reset_on_startup():
    config.SETTINGS_FILE.write_text(
        '{"text_provider": "openrouter", "openrouter_model": "openrouter/auto"}',
        encoding="utf-8",
    )
    controller = make_controller()
    assert controller.settings.get("openrouter_model") is None
    assert controller.snapshot()["ai"]["openrouter_model"] is None
