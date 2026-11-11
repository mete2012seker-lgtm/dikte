"""DPAPI anahtar saklama testleri."""

import base64
import json
import sys

import pytest

from dikte.secrets import SecretError, SecretStore, mask

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="DPAPI yalnız Windows")


def test_roundtrip_same_user(tmp_path):
    store = SecretStore(tmp_path / "secrets.json")
    store.save_key("sk-or-v1-abcdef1234")
    assert store.load_key() == "sk-or-v1-abcdef1234"
    assert store.has_key() is True


def test_plain_text_key_is_not_written(tmp_path):
    store = SecretStore(tmp_path / "secrets.json")
    store.save_key("sk-or-v1-abcdef1234")
    raw = (tmp_path / "secrets.json").read_text(encoding="utf-8")
    assert "abcdef1234" not in raw
    data = json.loads(raw)
    assert isinstance(data["openrouter"]["blob"], str)
    base64.b64decode(data["openrouter"]["blob"], validate=True)


def test_corrupt_blob_returns_none(tmp_path):
    path = tmp_path / "secrets.json"
    path.write_text(json.dumps({"openrouter": {"blob": "bozuk"}}), encoding="utf-8")
    store = SecretStore(path)
    assert store.load_key() is None
    assert store.has_key() is False


def test_missing_file_returns_none(tmp_path):
    store = SecretStore(tmp_path / "yok.json")
    assert store.load_key() is None
    assert store.masked() is None


def test_mask_keeps_last_four():
    assert mask("sk-or-v1-abcdef1234") == "sk-or-…1234"
    assert mask("ab") == "sk-or-…"


def test_delete_is_idempotent(tmp_path):
    path = tmp_path / "secrets.json"
    store = SecretStore(path)
    store.save_key("sk-or-v1-abcdef1234")
    assert store.delete_key() is True
    assert not path.exists()
    assert store.delete_key() is False


def test_short_key_is_rejected(tmp_path):
    store = SecretStore(tmp_path / "secrets.json")
    with pytest.raises(SecretError):
        store.save_key("kısa")
    assert store.load_key() is None


def test_secret_store_uses_lock_unique_tmp_and_fsync(tmp_path, monkeypatch):
    import os
    from pathlib import Path

    store = SecretStore(tmp_path / "secrets.json")
    assert hasattr(store, "_lock"), "SecretStore._lock olmalı"

    fsync_calls = []
    real_fsync = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (fsync_calls.append(fd), real_fsync(fd))[1])

    seen_temps = []
    real_replace = os.replace

    def track_replace(src, dst):
        seen_temps.append(Path(src).name)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", track_replace)
    store.save_key("sk-or-v1-abcdef1234")
    store.save_key("sk-or-v1-abcdef5678")

    assert len(fsync_calls) >= 2
    assert len(seen_temps) == 2
    assert seen_temps[0] != "secrets.json.tmp"
    assert seen_temps[0] != seen_temps[1]

