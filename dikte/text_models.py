"""Metin (GGUF) model kataloğu, dayanıklı indirme ve yerel çalıştırma.

İndirme `.part` dosyasına yazar; duraklat/iptal sonrası aynı bayttan devam eder.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import config, diagnostics
from .models import human_size

logger = logging.getLogger(__name__)

USER_AGENT = "Dikte/1.3"
MODEL_HOST = "https://huggingface.co/{repo}/resolve/main/{filename}"
CHUNK_SIZE = 1 << 20


class TextModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class TextModel:
    name: str
    label: str
    desc: str
    repo: str
    filename: str
    size_bytes: int
    tags: tuple[str, ...]


TEXT_MODELS: tuple[TextModel, ...] = (
    TextModel(
        "qwen3-1.7b",
        "Qwen3 1.7B",
        "En küçük ve en hızlı metin modeli; kısa düzeltmeler için yeterli.",
        "bartowski/Qwen_Qwen3-1.7B-GGUF",
        "Qwen_Qwen3-1.7B-Q4_K_M.gguf",
        1_282_439_584,
        ("En hızlı", "En az bellek", "Deneme"),
    ),
    TextModel(
        "qwen3-4b",
        "Qwen3 4B",
        "Denge modeli: düzeltme ve çeviride iyi kalite, makul bellek.",
        "bartowski/Qwen_Qwen3-4B-GGUF",
        "Qwen_Qwen3-4B-Q4_K_M.gguf",
        2_497_280_960,
        ("Dengeli", "Önerilen", "Türkçe iyi"),
    ),
    TextModel(
        "gemma3-4b",
        "Gemma 3 4B",
        "Akıcı çeviri ve noktalama; talimat takibi güçlü.",
        "bartowski/google_gemma-3-4b-it-GGUF",
        "google_gemma-3-4b-it-Q4_K_M.gguf",
        2_489_758_112,
        ("Çeviri", "Akıcı", "Orta bellek"),
    ),
    TextModel(
        "llama32-3b",
        "Llama 3.2 3B",
        "Hafif ve hızlı; kısa metinlerde pratik.",
        "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        2_019_377_696,
        ("Hafif", "Hızlı", "Kısa metin"),
    ),
)

_TEXT_NAMES = {model.name for model in TEXT_MODELS}


def get_text_model(name: str) -> TextModel:
    for model in TEXT_MODELS:
        if model.name == name:
            return model
    raise TextModelError("Bilinmeyen metin modeli.")


def models_dir() -> Path:
    return Path(config.text_models_dir())


def text_model_path(name: str) -> Path:
    return models_dir() / get_text_model(name).filename


def partial_path(name: str) -> Path:
    path = text_model_path(name)
    return path.with_name(path.name + ".part")


def is_installed(name: str) -> bool:
    path = text_model_path(name)
    return path.exists() and path.stat().st_size == get_text_model(name).size_bytes


def installed_bytes(name: str) -> int:
    path = text_model_path(name)
    try:
        return path.stat().st_size if path.exists() else 0
    except OSError:
        return 0


def partial_bytes(name: str) -> int:
    path = partial_path(name)
    try:
        return path.stat().st_size if path.exists() else 0
    except OSError:
        return 0


def delete_part(name: str) -> None:
    """Yarım kalan `.part` dosyasını siler (iptal)."""
    try:
        partial_path(name).unlink(missing_ok=True)
    except OSError as exc:
        raise TextModelError("Yarım dosya silinemedi.") from exc


def delete(name: str) -> None:
    spec = get_text_model(name)
    for path in (text_model_path(name), partial_path(name)):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise TextModelError("Model silinemedi; dosya başka işlemde olabilir.") from exc
    logger.info("Metin modeli silindi: %s", spec.name)


def scan() -> list[dict]:
    items = []
    for spec in TEXT_MODELS:
        installed = is_installed(spec.name)
        part = partial_bytes(spec.name)
        items.append(
            {
                "name": spec.name,
                "kind": "text",
                "label": spec.label,
                "desc": spec.desc,
                "tags": list(spec.tags),
                "size_bytes": spec.size_bytes,
                "approx_label": "~ " + human_size(spec.size_bytes),
                "size_label": human_size(spec.size_bytes) if installed else "—",
                "installed": installed,
                "partial": (not installed) and part > 0,
                "bytes": installed_bytes(spec.name) if installed else part,
            }
        )
    return items


def _url(spec: TextModel) -> str:
    return MODEL_HOST.format(repo=spec.repo, filename=spec.filename)


def _friendly_http_error(exc: urllib.error.HTTPError) -> str:
    if exc.code == 404:
        return "Model dosyası sunucuda bulunamadı."
    if exc.code == 416:
        return "İndirme aralığı sunucuda geçersiz."
    return f"Sunucu hatası ({exc.code})."


class Downloader:
    """Tek metin modeli indirir; duraklatma ve iptal bayraklarıyla yönlendirilir."""

    def __init__(self, opener=None, chunk_size: int = CHUNK_SIZE) -> None:
        self._opener = opener or urllib.request.urlopen
        self._chunk_size = chunk_size

    def download(
        self,
        name: str,
        progress=None,
        pause_event: threading.Event | None = None,
        cancel_event: threading.Event | None = None,
    ) -> dict:
        spec = get_text_model(name)
        final = text_model_path(name)
        part = partial_path(name)
        final.parent.mkdir(parents=True, exist_ok=True)

        existing = part.stat().st_size if part.exists() else 0
        if existing == spec.size_bytes:
            os.replace(part, final)
            return {"completed": True, "paused": False, "cancelled": False, "size": existing}
        if existing > spec.size_bytes:
            # Bozuk/fazla baytlı yarım dosya: baştan indir.
            try:
                part.unlink(missing_ok=True)
            except OSError:
                pass
            existing = 0

        headers = {"User-Agent": USER_AGENT}
        if existing:
            headers["Range"] = f"bytes={existing}-"
        request = urllib.request.Request(_url(spec), headers=headers)
        try:
            response = self._opener(request, timeout=60)
        except urllib.error.HTTPError as exc:
            raise TextModelError(_friendly_http_error(exc)) from exc
        except Exception as exc:
            raise TextModelError("Model sunucusuna ulaşılamadı.") from exc

        status = int(getattr(response, "status", 200) or 200)
        resume_from = existing if existing and status == 206 else 0
        if status == 206:
            content_range = ""
            headers_obj = getattr(response, "headers", None)
            if headers_obj is not None:
                content_range = headers_obj.get("Content-Range", "") or ""
            if content_range and not content_range.startswith(f"bytes {resume_from}-"):
                resume_from = 0
        mode = "ab" if resume_from else "wb"
        written = resume_from
        try:
            with open(part, mode) as handle:
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        return {"completed": False, "paused": False, "cancelled": True, "size": written}
                    if pause_event is not None and pause_event.is_set():
                        return {"completed": False, "paused": True, "cancelled": False, "size": written}
                    chunk = response.read(self._chunk_size)
                    if not chunk:
                        break
                    handle.write(chunk)
                    written += len(chunk)
                    if progress is not None:
                        progress(written)
        finally:
            try:
                response.close()
            except Exception:
                pass

        if written != spec.size_bytes:
            raise TextModelError(
                f"İndirme tamamlanmadı ({human_size(written)} / {human_size(spec.size_bytes)})."
            )
        try:
            os.replace(part, final)
        except OSError as exc:
            raise TextModelError("Model dosyası taşınamadı; dosya kilitli olabilir.") from exc
        return {"completed": True, "paused": False, "cancelled": False, "size": written}


class LocalTextModel:
    """llama.cpp sarmalayıcısı. Paket yoksa `local_missing` mesajıyla çağıran taraf düşer."""

    def __init__(self) -> None:
        self._llm = None
        self.model_name: str | None = None
        self.device: str | None = None

    @staticmethod
    def available() -> bool:
        return importlib.util.find_spec("llama_cpp") is not None

    def load(self, name: str, prefer_gpu: bool = True) -> str:
        if not self.available():
            raise TextModelError("Yerel metin motoru kurulu değil (llama.cpp).")
        path = text_model_path(name)
        if not path.exists():
            raise TextModelError("Metin modeli yüklü değil.")
        diagnostics.prepare_cuda_dlls()
        from llama_cpp import Llama

        layers = -1 if prefer_gpu else 0
        try:
            self._llm = Llama(model_path=str(path), n_gpu_layers=layers, n_ctx=4096, verbose=False)
            self.device = "GPU" if prefer_gpu else "CPU"
        except Exception as exc:
            if not prefer_gpu:
                raise TextModelError("Metin modeli yüklenemedi.") from exc
            logger.warning("GPU yüklemesi başarısız, CPU deneniyor: %s", exc)
            self._llm = Llama(model_path=str(path), n_gpu_layers=0, n_ctx=4096, verbose=False)
            self.device = "CPU"
        self.model_name = name
        return self.device

    def generate(self, system: str, user: str, max_tokens: int = 512) -> str:
        if self._llm is None:
            raise TextModelError("Metin modeli yüklü değil.")
        result = self._llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
            max_tokens=max_tokens,
        )
        choices = result.get("choices") if isinstance(result, dict) else None
        if not choices:
            return ""
        message = choices[0].get("message") if isinstance(choices[0], dict) else {}
        content = (message or {}).get("content") or ""
        return content if isinstance(content, str) else ""

    def unload(self) -> None:
        self._llm = None
        self.model_name = None
        self.device = None
