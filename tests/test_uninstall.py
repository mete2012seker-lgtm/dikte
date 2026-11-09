"""uninstall testleri: kurulum kontrolü, veri boyutu, otomatik başlatma, kaldırıcı çağrısı.

Gerçek kayıt defteri ve gerçek kaldırıcı kullanılmaz: winreg ve subprocess sahteleniyor.
"""

import sys
from pathlib import Path

import pytest

from dikte import config, uninstall


@pytest.fixture
def paketli(tmp_path, monkeypatch):
    """Kurulu sürüm taklidi: veri kökleri geçici klasöre yönlendirilir."""
    monkeypatch.setattr(config, "_FROZEN", True)
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(config, "TEMP_DIR", tmp_path / "temp")
    monkeypatch.setattr(config, "KEEP_MODELS_FLAG", tmp_path / "keep_models.flag")
    monkeypatch.setattr(config, "is_packaged", lambda: True)
    return tmp_path


def test_is_installed_kaldirici_yoksa_false(paketli, monkeypatch):
    monkeypatch.setattr(uninstall, "uninstaller_path", lambda: paketli / "unins000.exe")
    assert uninstall.is_installed() is False


def test_is_installed_kaldirici_varsa_true(paketli, monkeypatch):
    kaldirici = paketli / "unins000.exe"
    kaldirici.write_bytes(b"x")
    monkeypatch.setattr(uninstall, "uninstaller_path", lambda: kaldirici)
    assert uninstall.is_installed() is True


def test_is_installed_gelistirme_modunda_false(monkeypatch):
    monkeypatch.setattr(config, "is_packaged", lambda: False)
    assert uninstall.is_installed() is False


def test_data_bytes_kurulum_klasorunu_saymaz(paketli, monkeypatch):
    """Kurulum klasörü (exe_dir) veri boyutuna eklenmez; çift sayım olmaz."""
    kurulum = paketli / "programfiles"
    kurulum.mkdir()
    (kurulum / "Dikte.exe").write_bytes(b"e" * 5000)
    monkeypatch.setattr(config, "exe_dir", lambda: kurulum)
    (config.MODELS_DIR).mkdir(parents=True)
    (config.MODELS_DIR / "m.bin").write_bytes(b"m" * 1000)
    (config.DATA_DIR).mkdir(parents=True)
    (config.DATA_DIR / "settings.json").write_bytes(b"s" * 200)
    assert uninstall.data_bytes() == 1200


def test_format_size():
    assert uninstall.format_size(500) == "500 B"
    assert uninstall.format_size(1536) == "1,5 KB"


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

    def OpenKey(self, _root, _path, _res, _access):
        return FakeKey()

    def SetValueEx(self, _key, name, _res, _typ, value):
        self.values[name] = value

    def DeleteValue(self, _key, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        del self.values[name]

    def QueryValueEx(self, _key, name):
        if name not in self.values:
            raise OSError(name)
        return self.values[name], 1


@pytest.fixture
def kayit(monkeypatch):
    fake = FakeWinreg()
    monkeypatch.setitem(sys.modules, "winreg", fake)
    return fake


def test_autostart_ac_kapat(kayit):
    uninstall.set_autostart(True)
    assert uninstall.autostart_enabled() is True
    uninstall.set_autostart(False)
    assert uninstall.autostart_enabled() is False


def test_autostart_kapatmak_yoksa_hata_vermez(kayit):
    uninstall.set_autostart(False)  # kayıt zaten yok
    assert uninstall.autostart_enabled() is False


def test_run_uninstaller_modelleri_koru_bayragi_yazar(paketli, monkeypatch, kayit):
    kaldirici = paketli / "unins000.exe"
    kaldirici.write_bytes(b"x")
    monkeypatch.setattr(uninstall, "uninstaller_path", lambda: kaldirici)
    cagrilar = []
    monkeypatch.setattr(uninstall.subprocess, "Popen", lambda args, **_k: cagrilar.append(args))
    uninstall.run_uninstaller(keep_models=True)
    assert config.KEEP_MODELS_FLAG.exists()
    assert cagrilar and "/SILENT" in cagrilar[0]


def test_run_uninstaller_modelleri_sil_bayragi_kaldirir(paketli, monkeypatch, kayit):
    kaldirici = paketli / "unins000.exe"
    kaldirici.write_bytes(b"x")
    config.KEEP_MODELS_FLAG.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(uninstall, "uninstaller_path", lambda: kaldirici)
    monkeypatch.setattr(uninstall.subprocess, "Popen", lambda *_a, **_k: None)
    uninstall.run_uninstaller(keep_models=False)
    assert not config.KEEP_MODELS_FLAG.exists()


def test_run_uninstaller_otomatik_baslatmayi_temizler(paketli, monkeypatch, kayit):
    kaldirici = paketli / "unins000.exe"
    kaldirici.write_bytes(b"x")
    kayit.values[config.AUTOSTART_VALUE] = "eski"
    monkeypatch.setattr(uninstall, "uninstaller_path", lambda: kaldirici)
    monkeypatch.setattr(uninstall.subprocess, "Popen", lambda *_a, **_k: None)
    uninstall.run_uninstaller(keep_models=True)
    assert config.AUTOSTART_VALUE not in kayit.values


def test_run_uninstaller_kaldirici_yoksa_hata(paketli, monkeypatch):
    monkeypatch.setattr(uninstall, "uninstaller_path", lambda: paketli / "yok.exe")
    with pytest.raises(uninstall.UninstallError):
        uninstall.run_uninstaller()


def test_run_uninstaller_popen_hatasi_turkce(paketli, monkeypatch, kayit):
    kaldirici = paketli / "unins000.exe"
    kaldirici.write_bytes(b"x")
    monkeypatch.setattr(uninstall, "uninstaller_path", lambda: kaldirici)

    def patla(*_a, **_k):
        raise OSError("erisim yok")

    monkeypatch.setattr(uninstall.subprocess, "Popen", patla)
    with pytest.raises(uninstall.UninstallError) as exc:
        uninstall.run_uninstaller()
    assert "başlatılamadı" in str(exc.value)
