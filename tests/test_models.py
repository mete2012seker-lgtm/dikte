import pytest

from dikte import models


def make_snapshot(models_dir, name, size=1024, with_metadata=True):
    folder = models.model_folder(models_dir, name) / "snapshots" / "abc"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "model.bin"
    path.write_bytes(b"x" * size)
    if with_metadata:
        (folder / "config.json").write_text("{}", encoding="utf-8")
        (folder / "tokenizer.json").write_text("{}", encoding="utf-8")
    return folder


def test_catalog_has_six_speech_models():
    names = [model.name for model in models.SPEECH_MODELS]
    assert names == ["large-v3", "large-v3-turbo", "medium", "small", "base", "tiny"]
    assert len(names) == len(set(names)) == 6


def test_repo_folder_name():
    assert models.repo_folder_name("small") == "models--Systran--faster-whisper-small"


def test_scan_detects_installed_and_missing(tmp_path):
    make_snapshot(tmp_path, "small", size=2048)
    result = models.scan(tmp_path)

    assert result["small"]["installed"] is True
    assert result["small"]["size_bytes"] >= 2048
    assert result["small"]["partial"] is False
    assert result["base"]["installed"] is False
    assert result["base"]["size_label"] == "—"


def test_scan_detects_partial_download(tmp_path):
    folder = models.model_folder(tmp_path, "medium") / "blobs"
    folder.mkdir(parents=True)
    (folder / "parca").write_bytes(b"x" * 512)

    result = models.scan(tmp_path)
    assert result["medium"]["installed"] is False
    assert result["medium"]["partial"] is True
    assert result["medium"]["size_bytes"] >= 512


def test_human_size():
    assert models.human_size(0) == "0 KB"
    assert models.human_size(75 * models.MB) == "75 MB"
    assert models.human_size(int(2.9 * models.GB)) == "2,9 GB"


def test_delete_removes_folder_and_lock(tmp_path):
    folder = make_snapshot(tmp_path, "tiny", size=16)
    lock = tmp_path / ".locks" / models.repo_folder_name("tiny")
    lock.mkdir(parents=True)

    models.delete("tiny", tmp_path)
    assert not folder.exists()
    assert not lock.exists()
    assert models.scan(tmp_path)["tiny"]["installed"] is False


def test_delete_missing_model_raises(tmp_path):
    with pytest.raises(models.ModelError):
        models.delete("tiny", tmp_path)


def test_download_reports_progress_and_installs(tmp_path, monkeypatch):
    sizes = []

    def fake_download(name, models_dir):
        make_snapshot(models_dir, name, size=1024)
        return str(models.model_folder(models_dir, name))

    monkeypatch.setattr(models, "_download_model", fake_download)
    path = models.download("tiny", tmp_path, progress=sizes.append)

    assert path
    assert models.scan(tmp_path)["tiny"]["installed"] is True
    assert sizes
    assert sizes[-1] >= 1024


def test_download_error_is_turkish(tmp_path, monkeypatch):
    def broken(name, models_dir):
        raise OSError("ağ yok")

    monkeypatch.setattr(models, "_download_model", broken)
    with pytest.raises(models.ModelError) as error:
        models.download("tiny", tmp_path)
    assert "indirilemedi" in str(error.value).lower()


def test_unknown_model_is_rejected(tmp_path):
    with pytest.raises(models.ModelError):
        models.get_model("bilinmeyen")
    with pytest.raises(models.ModelError):
        models.download("bilinmeyen", tmp_path)


def test_snapshot_missing_config_or_tokenizer_is_not_installed(tmp_path):
    make_snapshot(tmp_path, "small", size=2048, with_metadata=False)
    result = models.scan(tmp_path)
    assert result["small"]["installed"] is False
    assert result["small"]["partial"] is True


def test_custom_speech_model_lifecycle(tmp_path, monkeypatch):
    from dikte import config

    custom_file = tmp_path / "custom_models.json"
    monkeypatch.setattr(config, "CUSTOM_MODELS_FILE", custom_file)
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")

    # 1. Özel ses modeli ekle
    added = models.add_custom_model("kullanici/turkce-whisper", label="Türkçe Whisper")
    assert added["name"].startswith("custom-")
    assert added["repo_id"] == "kullanici/turkce-whisper"
    assert added["label"] == "Türkçe Whisper"

    # URL ile de eklenebilmeli ve tekrarda etiket güncellenebilmeli
    dup = models.add_custom_model(
        "https://huggingface.co/kullanici/turkce-whisper", label="Yeni Etiket"
    )
    assert dup["name"] == added["name"]
    assert dup["label"] == "Yeni Etiket"

    # 2. Disk durumunda taranabilmeli
    scan_res = models.scan(tmp_path / "models")
    m_name = added["name"]
    assert m_name in scan_res
    assert scan_res[m_name]["custom"] is True
    assert scan_res[m_name]["installed"] is False

    # 3. Snapshot dosyası oluşturunca installed True olmalı
    make_snapshot(tmp_path / "models", m_name, size=1024)
    scan_res2 = models.scan(tmp_path / "models")
    assert scan_res2[m_name]["installed"] is True

    # 4. delete() çağrılınca dosya silinmeli ama kart custom_models.json içinde KALMALI
    models.delete(m_name, tmp_path / "models")
    assert not (tmp_path / "models" / models.repo_folder_name(m_name)).exists()
    assert m_name in models.scan(tmp_path / "models")
    assert models.scan(tmp_path / "models")[m_name]["installed"] is False

    # 5. remove_custom_model() çağrılınca custom_models.json'dan da kaldırılmalı
    models.remove_custom_model(m_name, tmp_path / "models")
    assert m_name not in models.scan(tmp_path / "models")

    # Yerleşik modeller remove_custom_model ile silinemez
    with pytest.raises(models.ModelError):
        models.remove_custom_model("tiny", tmp_path / "models")


def test_model_manager_cancel_download(tmp_path, monkeypatch):
    from dikte import config

    mgr = models.ModelManager(models_dir=tmp_path / "models")
    res = mgr.cancel_download()
    assert res == {"cancelled": True}


