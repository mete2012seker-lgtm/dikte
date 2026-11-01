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
