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


def test_check_url_yok(monkeypatch):
    monkeypatch.setattr(config, "UPDATE_URL", "")
    with pytest.raises(updater.UpdaterError) as exc:
        updater.check(force=True)
    assert exc.value.code == "no_url"


def test_check_bozuk_json(monkeypatch):
    monkeypatch.setattr(
        updater.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(b"bozuk{")
    )
    with pytest.raises(updater.UpdaterError) as exc:
        updater.check(force=True, url="https://ornek/latest.json")
    assert exc.value.code == "bad_json"


def test_download_alan_adi_reddi(tmp_path):
    onceki = config.UPDATE_URL
    config.UPDATE_URL = "https://guvenli-sunucu/latest.json"
    try:
        with pytest.raises(updater.UpdaterError) as exc:
            updater.download("https://kotu-sunucu/kur.exe", dest_dir=tmp_path)
        assert exc.value.code == "host_rejected"
    finally:
        config.UPDATE_URL = onceki


def test_check_sha_yok_yeni_surumde_reddedilir(monkeypatch):
    data = json.dumps({"version": "9.0.0", "url": "https://ornek/kur.exe"}).encode()
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(data))
    with pytest.raises(updater.UpdaterError) as exc:
        updater.check(force=True, url="https://ornek/latest.json")
    assert exc.value.code == "bad_sha"


def test_check_sha_bicimi_bozuk_sessiz_none(monkeypatch):
    data = json.dumps({"version": "9.0.0", "url": "https://ornek/kur.exe", "sha256": "xyz"}).encode()
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(data))
    assert updater.check(force=False, url="https://ornek/latest.json") is None


def test_check_url_bos_sessiz_olmaz(monkeypatch):
    onceki = config.UPDATE_URL
    config.UPDATE_URL = ""
    try:
        with pytest.raises(updater.UpdaterError) as exc:
            updater.check(force=False)
        assert exc.value.code == "no_url"
    finally:
        config.UPDATE_URL = onceki


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


# --- Uçtan uca güncelleme akışı: sahte latest.json + sahte kurucu ---

from types import SimpleNamespace

from dikte.controller import Controller


def _flow_controller():
    # update_apply yalnız UPDATE_MESSAGES ve updater'ı kullanır; tam Controller kurmadan çağrılır.
    return SimpleNamespace(UPDATE_MESSAGES=Controller.UPDATE_MESSAGES, settings=None)


def _latest(monkeypatch, payload: dict):
    data = json.dumps(payload).encode()
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(data))
    monkeypatch.setattr(config, "UPDATE_URL", "https://ornek/latest.json")


def test_akis_basarili_sha_uyar_kurulur(monkeypatch, tmp_path):
    kurucu = b"sahte kurucu ikilisi"
    _latest(monkeypatch, {
        "version": "9.0.0",
        "url": "https://ornek/Dikte-Setup.exe",
        "sha256": hashlib.sha256(kurucu).hexdigest(),
    })
    monkeypatch.setattr(updater, "download", lambda *_a, **_k: _yaz(tmp_path, kurucu))
    calistirilan = []
    monkeypatch.setattr(updater, "apply", lambda p: calistirilan.append(p))
    sonuc = Controller.update_apply(_flow_controller())
    assert sonuc["ok"] is True
    assert len(calistirilan) == 1


def test_akis_bozuk_ozet_kurmaz_ve_siler(monkeypatch, tmp_path):
    _latest(monkeypatch, {
        "version": "9.0.0",
        "url": "https://ornek/Dikte-Setup.exe",
        "sha256": "0" * 64,
    })
    monkeypatch.setattr(updater, "download", lambda *_a, **_k: _yaz(tmp_path, b"kurucu"))
    calistirilan = []
    monkeypatch.setattr(updater, "apply", lambda p: calistirilan.append(p))
    sonuc = Controller.update_apply(_flow_controller())
    assert sonuc["ok"] is False
    assert sonuc["code"] == "sha_mismatch"
    assert calistirilan == []
    assert not (tmp_path / "kurucu.bin").exists()


def test_akis_sha_bildirimi_yoksa_indirmez(monkeypatch):
    _latest(monkeypatch, {"version": "9.0.0", "url": "https://ornek/Dikte-Setup.exe"})
    indirilen = []
    monkeypatch.setattr(updater, "download", lambda *a, **k: indirilen.append(a))
    sonuc = Controller.update_apply(_flow_controller())
    assert sonuc["ok"] is False
    assert sonuc["code"] == "bad_sha"
    assert "SHA-256" in sonuc["message"]
    assert indirilen == []


def test_akis_eksik_indirme_turkce_mesaj(monkeypatch):
    _latest(monkeypatch, {"version": "9.0.0", "url": "https://ornek/x.exe", "sha256": "a" * 64})

    def eksik(*_a, **_k):
        raise updater.UpdaterError("incomplete")

    monkeypatch.setattr(updater, "download", eksik)
    sonuc = Controller.update_apply(_flow_controller())
    assert sonuc["code"] == "incomplete"
    assert "tamamlanmadı" in sonuc["message"]


def test_update_check_sha256_dondurur(monkeypatch):
    _latest(monkeypatch, {"version": "9.0.0", "url": "https://ornek/x.exe", "sha256": "b" * 64})
    saved = []
    stub = SimpleNamespace(
        UPDATE_MESSAGES=Controller.UPDATE_MESSAGES,
        settings=SimpleNamespace(save=lambda **kw: saved.append(kw)),
    )
    sonuc = Controller.update_check(stub, force=True)
    assert sonuc["update_available"] is True
    assert sonuc["sha256"] == "b" * 64


def _yaz(tmp_path, icerik: bytes):
    yol = tmp_path / "kurucu.bin"
    yol.write_bytes(icerik)
    return yol
