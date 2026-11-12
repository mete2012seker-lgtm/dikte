import json
from pathlib import Path

import pytest

from dikte.settings import DEFAULTS, HOTKEY_CHOICES, SettingsStore


def test_defaults_when_file_missing(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    data = store.as_dict()
    assert data["save_history"] is True
    assert data["hotkey"] == "right_ctrl"
    assert data["active_model"] == "auto"


def test_save_and_reload(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    store.save(save_history=False, hotkey="f9", active_model="small")

    again = SettingsStore(path)
    assert again.get("save_history") is False
    assert again.get("hotkey") == "f9"
    assert again.get("active_model") == "small"


def test_unknown_fields_are_preserved(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"save_history": False, "future": 42}), encoding="utf-8")
    store = SettingsStore(path)
    assert store.get("future") == 42
    assert store.get("save_history") is False


def test_invalid_hotkey_falls_back(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"hotkey": "a"}), encoding="utf-8")
    store = SettingsStore(path)
    assert store.get("hotkey") == "right_ctrl"


def test_corrupt_file_is_backed_up(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{bozuk", encoding="utf-8")
    store = SettingsStore(path)
    assert store.as_dict()["save_history"] is True
    backups = list(tmp_path.glob("settings.bozuk-*.json"))
    assert backups, "Bozuk dosya yedeklenmeli"


def test_atomic_write_leaves_no_temp_file(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    store.save(hotkey="f10")
    assert path.exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_hotkey_choices_are_preset_only():
    assert set(HOTKEY_CHOICES) == {
        "right_ctrl",
        "left_ctrl",
        "right_alt",
        "left_alt",
        "f8",
        "f9",
        "f10",
    }
    assert DEFAULTS["hotkey"] == "right_ctrl"


# ---------- v1.3 alanları ----------


def test_v13_defaults(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    data = store.as_dict()
    assert data["output_language"] == "tr"
    assert data["auto_translate"] is False
    assert data["input_language"] == "auto"
    assert data["auto_paste"] is True
    assert data["text_provider"] == "none"
    assert data["theme"] == "system"
    assert data["text_model"] == "qwen3-4b"
    assert data["update_check_on_start"] is True


def test_text_provider_choices_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    for provider in ("local", "openrouter", "none"):
        store.save(text_provider=provider)
        assert SettingsStore(path).get("text_provider") == provider


def test_invalid_text_provider_falls_back_to_none(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"text_provider": "bulut"}), encoding="utf-8")
    assert SettingsStore(path).get("text_provider") == "none"


def test_invalid_output_language_falls_back_to_tr(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"output_language": "fr"}), encoding="utf-8")
    assert SettingsStore(path).get("output_language") == "tr"


def test_invalid_theme_falls_back_to_system(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "neon"}), encoding="utf-8")
    assert SettingsStore(path).get("theme") == "system"


def test_non_bool_flags_fall_back(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"auto_translate": "evet", "auto_paste": 0, "effects": None}),
        encoding="utf-8",
    )
    data = SettingsStore(path).as_dict()
    assert data["auto_translate"] is False
    assert data["auto_paste"] is True
    assert data["effects"] is True


def test_empty_system_prompt_falls_back(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"system_prompt": "   "}), encoding="utf-8")
    assert "dikte düzeltme" in SettingsStore(path).get("system_prompt")


def test_openrouter_model_is_optional(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    assert store.get("openrouter_model") is None
    store.save(openrouter_model="deepseek/x")
    assert store.get("openrouter_model") == "deepseek/x"
    store.save(openrouter_model="")
    assert store.get("openrouter_model") is None


def test_update_last_check_type_checked(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"update_last_check": 42}), encoding="utf-8")
    assert SettingsStore(path).get("update_last_check") is None


def test_unknown_v13_fields_survive_save(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"future_v2": {"a": 1}}), encoding="utf-8")
    store = SettingsStore(path)
    store.save(output_language="de")
    assert SettingsStore(path).get("future_v2") == {"a": 1}
    assert SettingsStore(path).get("output_language") == "de"


def test_settings_write_uses_lock_unique_tmp_and_fsync(tmp_path, monkeypatch):
    import os

    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    assert hasattr(store, "_lock"), "SettingsStore._lock olmalı"

    fsync_calls = []
    real_fsync = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (fsync_calls.append(fd), real_fsync(fd))[1])

    seen_temps = []
    real_replace = os.replace

    def track_replace(src, dst):
        seen_temps.append(Path(src).name)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", track_replace)
    store.save(hotkey="f8")
    store.save(hotkey="f9")

    assert len(fsync_calls) >= 2
    assert len(seen_temps) == 2
    assert seen_temps[0] != "settings.json.tmp"
    assert seen_temps[0] != seen_temps[1]


# ---------- Faz 3-4 yeni alanlar ve çoklu tuş ----------


def test_new_fields_defaults_and_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    data = store.as_dict()
    assert data["design_style"] == "dikte_ai"
    assert data["setup_done"] is False
    assert data["sidebar_collapsed"] is False

    store.save(design_style="classic", setup_done=True, sidebar_collapsed=True)
    reloaded = SettingsStore(path).as_dict()
    assert reloaded["design_style"] == "classic"
    assert reloaded["setup_done"] is True
    assert reloaded["sidebar_collapsed"] is True


def test_design_style_invalid_fallback(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"design_style": "gecersiz"}), encoding="utf-8")
    assert SettingsStore(path).get("design_style") == "dikte_ai"


def test_multikey_hotkey_save_and_normalize(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)

    # 3'lü kombinasyon
    store.save(hotkey="shift+ctrl+d")
    assert store.get("hotkey") == "ctrl+shift+d"
    assert SettingsStore(path).get("hotkey") == "ctrl+shift+d"

    # 2'li kombinasyon
    store.set_hotkey("space+alt")
    assert store.get("hotkey") == "alt+space"

    # Geçersiz kombinasyon set_hotkey ile ValueError vermeli
    with pytest.raises(ValueError):
        store.set_hotkey("ctrl+shift+alt+d+x")

    # Geçersiz kombinasyon dosyadan okununca varsayılana düşmeli
    path.write_text(json.dumps({"hotkey": "1+2+3+4"}), encoding="utf-8")
    assert SettingsStore(path).get("hotkey") == "right_ctrl"


def test_input_language_roundtrip_and_fallback(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    for lang in ("tr", "auto"):
        store.save(input_language=lang)
        assert SettingsStore(path).get("input_language") == lang

    path.write_text(json.dumps({"input_language": "fr"}), encoding="utf-8")
    assert SettingsStore(path).get("input_language") == "auto"



