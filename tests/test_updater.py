"""updater testleri: sürüm karşılaştırma, denetim, indirme, SHA doğrulama."""

import hashlib
import io
import json
import urllib.error

import pytest

from dikte import config, updater


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_compare_versions_buyuk():
    assert updater.compare_versions("1.6.9", "1.6.10") == 1


def test_compare_versions_esit():
    assert updater.compare_versions("1.6.0", "1.6.0") == 0


def test_compare_versions_kucuk():
    assert updater.compare_versions("2.0.0", "1.9.9") == -1


def test_check_http_reddi():
    with pytest.raises(updater.UpdaterError) as exc:
        updater.check(force=True, url="http://ornek/latest.json")
    assert exc.value.code == "http_rejected"


def test_check_ag_yok_sessiz(monkeypatch):
    def fail(*_a, **_k):
        raise urllib.error.URLError("ag yok")

    monkeypatch.setattr(updater.urllib.request, "urlopen", fail)
    assert updater.check(force=False, url="https://ornek/latest.json") is None


def test_check_yeni_surum_var(monkeypatch):
    data = json.dumps(
        {
            "version": "1.9.0",
            "url": "https://ornek/Dikte-1.9.0-kurulum.exe",
            "sha256": "ab" * 32,
            "notes": "not",
        }
    ).encode()
    monkeypatch.setattr(
        updater.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(data)
    )
    result = updater.check(force=True, url="https://ornek/latest.json")
    assert result["update_available"] is True
    assert result["version"] == "1.9.0"


def test_check_son_surum(monkeypatch):
    data = json.dumps({"version": config.APP_VERSION, "url": "https://ornek/x.exe"}).encode()
    monkeypatch.setattr(
        updater.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(data)
    )
    result = updater.check(force=True, url="https://ornek/latest.json")
    assert result["update_available"] is False


def test_check_url_yok():
    with pytest.raises(updater.UpdaterError) as exc:
        updater.check(force=True, url="")
    assert exc.value.code == "no_url"


def test_check_bozuk_json(monkeypatch):
    monkeypatch.setattr(
        updater.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(b"bozuk{")
    )
    with pytest.raises(updater.UpdaterError) as exc:
        updater.check(force=True, url="https://ornek/latest.json")
    assert exc.value.code == "bad_json"


def test_download_alan_adi_reddi(tmp_path):
    config.UPDATE_URL = "https://guvenli-sunucu/latest.json"
    try:
        with pytest.raises(updater.UpdaterError) as exc:
            updater.download("https://kotu-sunucu/kur.exe", dest_dir=tmp_path)
        assert exc.value.code == "host_rejected"
    finally:
        config.UPDATE_URL = ""


def test_verify_sha256_uyusmazlik_siler(tmp_path):
    dosya = tmp_path / "kur.exe"
    dosya.write_bytes(b"deneme")
    ok = updater.verify_sha256(dosya, hashlib.sha256(b"baska").hexdigest())
    assert ok is False
    assert not dosya.exists()


def test_verify_sha256_uyusur(tmp_path):
    dosya = tmp_path / "kur.exe"
    dosya.write_bytes(b"deneme")
    ok = updater.verify_sha256(dosya, hashlib.sha256(b"deneme").hexdigest())
    assert ok is True
    assert dosya.exists()
