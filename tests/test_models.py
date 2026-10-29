import pytest

from dikte import models


def make_snapshot(models_dir, name, size=1024):
    folder = models.model_folder(models_dir, name) / "snapshots" / "abc"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "model.bin"
    path.write_bytes(b"x" * size)
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
