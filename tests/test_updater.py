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


def test_list_releases_and_fetch_payload(monkeypatch):
    sample_releases = [
        {
            "tag_name": "v1.6.0",
            "name": "Dikte 1.6.0",
            "published_at": "2026-11-09T10:00:00Z",
            "body": "sha256: " + "a" * 64 + "\nNotlar",
            "assets": [
                {
                    "name": "Dikte-Setup-1.6.0.exe",
                    "browser_download_url": "https://github.com/repo/releases/download/v1.6.0/Dikte-Setup-1.6.0.exe",
                }
            ],
        },
        {
            "tag_name": "v1.5.0",
            "name": "Dikte 1.5.0",
            "published_at": "2026-11-01T10:00:00Z",
            "body": "Eski sürüm. SHA-256: " + "b" * 64,
            "assets": [
                {
                    "name": "Dikte-Setup-1.5.0.exe",
                    "browser_download_url": "https://github.com/repo/releases/download/v1.5.0/Dikte-Setup-1.5.0.exe",
                }
            ],
        },
        {
            "tag_name": "v2.0.0",
            "name": "Dikte 2.0.0",
            "published_at": "2026-12-01T10:00:00Z",
            "body": "Gelecek sürüm",
            "assets": [],
        },
    ]

    data = json.dumps(sample_releases).encode("utf-8")
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(data))

    payload = updater.fetch_releases_payload("https://api.github.com/repos/test/releases")
    assert "releases" in payload
    assert len(payload["releases"]) == 3

    # list_releases denetimi
    releases = updater.list_releases(
        "https://api.github.com/repos/test/releases",
        current_version="1.6.0",
    )
    assert len(releases) == 3

    v16 = releases[0]
    assert v16["version"] == "1.6.0"
    assert v16["is_current"] is True
    assert v16["is_downgrade"] is False
    assert v16["installer_url"].endswith(".exe")
    assert v16["sha256"] == "a" * 64

    v15 = releases[1]
    assert v15["version"] == "1.5.0"
    assert v15["is_current"] is False
    assert v15["is_downgrade"] is True
    assert v15["sha256"] == "b" * 64

    v20 = releases[2]
    assert v20["version"] == "2.0.0"
    assert v20["is_current"] is False
    assert v20["is_downgrade"] is False


def test_download_installer_cancel_and_progress(tmp_path, monkeypatch):
    import threading

    kurucu = b"x" * 1024
    monkeypatch.setattr(config, "UPDATE_URL", "https://ornek/latest.json")
    monkeypatch.setattr(
        updater.urllib.request,
        "urlopen",
        lambda *_a, **_k: FakeResponse(kurucu),
    )

    # 1. progress_cb çağrılmalı
    progress_calls = []
    yol = updater.download_installer(
        "https://ornek/kurucu.exe",
        dest_dir=tmp_path,
        progress_cb=lambda d, t: progress_calls.append((d, t)),
        allow_missing_sha256=True,
    )
    assert yol.exists()
    assert progress_calls

    # 2. cancel_event ile durdurulabilmeli
    cancel_ev = threading.Event()
    cancel_ev.set()
    with pytest.raises(updater.UpdaterError) as exc:
        updater.download_installer(
            "https://ornek/kurucu2.exe",
            dest_dir=tmp_path,
            cancel_event=cancel_ev,
        )
    assert exc.value.code == "cancelled"

