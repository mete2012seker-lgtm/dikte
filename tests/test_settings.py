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
