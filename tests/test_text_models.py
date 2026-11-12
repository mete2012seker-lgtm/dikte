"""GGUF kataloğu, dayanıklı indirme ve yerel motor testleri (yerel HTTP sunucusu)."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from dikte import config, text_models
from dikte.text_models import (
    Downloader,
    TextModel,
    TextModelError,
    get_text_model,
    is_installed,
    partial_path,
    scan,
    text_model_path,
)

PAYLOAD = b"GGUF" + (bytes(range(256)) * 4096)[4:]  # 1 MiB, GGUF sihirli baytlı


class Handler(BaseHTTPRequestHandler):
    range_requested = []

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/404"):
            self.send_response(404)
            self.end_headers()
            return
        data = PAYLOAD
        start = 0
        header = self.headers.get("Range")
        if header and header.startswith("bytes="):
            start = int(header.split("=", 1)[1].split("-", 1)[0])
            Handler.range_requested.append(header)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(data) - 1}/{len(data)}")
        else:
            self.send_response(200)
        body = data[start:]
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture()
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    Handler.range_requested = []
    yield f"http://127.0.0.1:{httpd.server_address[1]}/{{repo}}/{{filename}}"
    httpd.shutdown()


@pytest.fixture()
def tiny_model(tmp_path, monkeypatch, server):
    monkeypatch.setattr(config, "MODELS_DIR", tmp_path / "models")
    spec = TextModel(
        "test-1b", "Test 1B", "Test modeli.",
        "repo/x", "test-1b.gguf", len(PAYLOAD), ("Test",),
    )
    monkeypatch.setattr(text_models, "TEXT_MODELS", (spec,))
    monkeypatch.setattr(text_models, "MODEL_HOST", server)
    return spec


def test_download_completes_and_renames_part(tiny_model):
    result = Downloader(chunk_size=64 * 1024).download("test-1b")
    assert result["completed"] is True
    assert text_model_path("test-1b").exists()
    assert text_model_path("test-1b").read_bytes() == PAYLOAD
    assert not partial_path("test-1b").exists()
    assert is_installed("test-1b") is True


def test_resume_uses_range_header(tiny_model):
    part = partial_path("test-1b")
    part.parent.mkdir(parents=True, exist_ok=True)
    start = 100_000
    part.write_bytes(PAYLOAD[:start])

    progress = []
    result = Downloader(chunk_size=64 * 1024).download("test-1b", progress=progress.append)
    assert result["completed"] is True
    assert text_model_path("test-1b").read_bytes() == PAYLOAD
    assert any(header == f"bytes={start}-" for header in Handler.range_requested)
    assert progress and progress[-1] >= len(PAYLOAD)


def test_pause_keeps_partial_file(tiny_model):
    pause = threading.Event()
    pause.set()
    result = Downloader().download("test-1b", pause_event=pause)
    assert result["paused"] is True
    assert result["completed"] is False
    assert not text_model_path("test-1b").exists()
    assert not partial_path("test-1b").exists() or partial_path("test-1b").stat().st_size == 0


def test_resume_after_pause_completes(tiny_model):
    pause = threading.Event()
    pause.set()
    Downloader().download("test-1b", pause_event=pause)
    pause.clear()
    result = Downloader().download("test-1b", pause_event=pause)
    assert result["completed"] is True
    assert text_model_path("test-1b").read_bytes() == PAYLOAD


def test_cancel_keeps_part_and_reports(tiny_model):
    cancel = threading.Event()
    cancel.set()
    result = Downloader().download("test-1b", cancel_event=cancel)
    assert result["cancelled"] is True
    assert not text_model_path("test-1b").exists()


def test_404_gives_turkish_error(tiny_model):
    original = text_models.MODEL_HOST
    text_models.MODEL_HOST = "http://127.0.0.1:1/404/{repo}/{filename}"
    try:
        with pytest.raises(TextModelError) as err:
            Downloader().download("test-1b")
        assert "ulaşılamadı" in str(err.value) or "bulunamadı" in str(err.value)
    finally:
        text_models.MODEL_HOST = original


def test_scan_reports_states(tiny_model):
    items = {item["name"]: item for item in scan()}
    assert items["test-1b"]["installed"] is False
    assert items["test-1b"]["partial"] is False

    Downloader().download("test-1b")
    items = {item["name"]: item for item in scan()}
    assert items["test-1b"]["installed"] is True
    assert items["test-1b"]["kind"] == "text"
    assert items["test-1b"]["size_label"].endswith("MB")


def test_delete_removes_model_and_part(tiny_model):
    Downloader().download("test-1b")
    partial_path("test-1b").write_bytes(b"x")
    text_models.delete("test-1b")
    assert not text_model_path("test-1b").exists()
    assert not partial_path("test-1b").exists()


def test_unknown_model_is_rejected():
    with pytest.raises(TextModelError):
        get_text_model("yok")


def test_local_runtime_without_package_reports_error():
    runtime = text_models.LocalTextModel()
    if runtime.available():
        pytest.skip("llama.cpp kurulu; bu test paket yokken geçerli")
    with pytest.raises(TextModelError) as err:
        runtime.load("qwen3-4b")
    assert "llama.cpp" in str(err.value)


def test_oversized_part_is_restarted(tiny_model):
    part = partial_path("test-1b")
    part.parent.mkdir(parents=True, exist_ok=True)
    part.write_bytes(PAYLOAD + b"fazla")

    result = Downloader(chunk_size=64 * 1024).download("test-1b")
    assert result["completed"] is True
    assert text_model_path("test-1b").read_bytes() == PAYLOAD


def test_friendly_http_errors():
    import urllib.error

    def error(code):
        return urllib.error.HTTPError("http://x", code, "hata", {}, None)

    assert "bulunamadı" in text_models._friendly_http_error(error(404))
    assert "geçersiz" in text_models._friendly_http_error(error(416))
    assert "Sunucu hatası (500)" in text_models._friendly_http_error(error(500))


def test_corrupt_non_gguf_file_is_not_considered_installed(tiny_model):
    path = text_model_path("test-1b")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"HTML" + PAYLOAD[4:])
    assert is_installed("test-1b") is False


def test_corrupt_complete_part_is_redownloaded(tiny_model):
    part = partial_path("test-1b")
    part.parent.mkdir(parents=True, exist_ok=True)
    part.write_bytes(b"NOPE" + PAYLOAD[4:])

    result = Downloader(chunk_size=64 * 1024).download("test-1b")
    assert result["completed"] is True
    assert text_model_path("test-1b").read_bytes()[:4] == b"GGUF"
    assert is_installed("test-1b") is True


def test_custom_text_model_lifecycle_and_manager(tmp_path, monkeypatch):
    custom_file = tmp_path / "custom_models.json"
    models_dir = tmp_path / "models"
    monkeypatch.setattr(config, "CUSTOM_MODELS_FILE", custom_file)
    monkeypatch.setattr(config, "MODELS_DIR", models_dir)

    mgr = text_models.TextModelManager(models_dir=models_dir)

    # 1. Hugging Face URL'si ile ekle
    url = "https://huggingface.co/bartowski/Qwen2.5-3B-GGUF/resolve/main/Qwen2.5-3B-Q4_K_M.gguf"
    added = mgr.add_custom_text_model(url, label="Qwen 2.5 3B")
    m_id = added["name"]
    assert added["repo"] == "bartowski/Qwen2.5-3B-GGUF"
    assert added["filename"] == "Qwen2.5-3B-Q4_K_M.gguf"
    assert added["custom"] is True

    # 2. scan() içinde listelenmeli, başlangıçta installed=False
    scanned = {item["name"]: item for item in mgr.scan()}
    assert m_id in scanned
    assert scanned[m_id]["installed"] is False
    assert mgr.is_installed(m_id) is False
    assert mgr.is_downloaded(m_id) is False

    # 3. Sahte GGUF dosyası yazalım (> 1024 bayt ve b"GGUF" magic)
    target_path = mgr.path(m_id)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(PAYLOAD)  # 1 MiB GGUF

    # is_downloaded kontrolü b"GGUF" ve > 1024 bayt ile True olmalı
    assert mgr.is_installed(m_id) is True
    assert mgr.is_downloaded(m_id) is True

    # 4. delete() yalnız diskteki dosyayı silmeli, kart listede kalmalı
    mgr.delete(m_id)
    assert not target_path.exists()
    scanned_after_delete = {item["name"]: item for item in mgr.scan()}
    assert m_id in scanned_after_delete
    assert scanned_after_delete[m_id]["installed"] is False

    # 5. remove_custom_text_model() hem diskten hem de custom_models.json'dan silmeli
    mgr.remove_custom_text_model(m_id)
    scanned_after_remove = {item["name"]: item for item in mgr.scan()}
    assert m_id not in scanned_after_remove


