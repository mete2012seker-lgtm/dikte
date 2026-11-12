"""Metin (GGUF) model kataloğu, dayanıklı indirme ve yerel çalıştırma.

İndirme `.part` dosyasına yazar; duraklat/iptal sonrası aynı bayttan devam eder.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import config, diagnostics
from .models import human_size, load_custom_models, save_custom_models

logger = logging.getLogger(__name__)

USER_AGENT = f"Dikte/{config.APP_VERSION}"
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
    custom_list = load_custom_models().get("text", [])
    for item in custom_list:
        if item.get("name") == name or item.get("id") == name:
            return TextModel(
                name=item.get("name") or item.get("id", name),
                label=item.get("label", name),
                desc=item.get("desc", f"Hugging Face: {item.get('repo', '')}"),
                repo=item.get("repo", ""),
                filename=item.get("filename", f"{name}.gguf"),
                size_bytes=int(item.get("size_bytes") or 0),
                tags=tuple(item.get("tags") or ("Özel", "Hugging Face")),
            )
    raise TextModelError("Bilinmeyen metin modeli.")


def models_dir() -> Path:
    return Path(config.text_models_dir())


def text_model_path(name: str) -> Path:
    return models_dir() / get_text_model(name).filename


def partial_path(name: str) -> Path:
    path = text_model_path(name)
    return path.with_name(path.name + ".part")


GGUF_MAGIC = b"GGUF"


def _has_gguf_magic(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 4:
            return False
        with open(path, "rb") as handle:
            return handle.read(4) == GGUF_MAGIC
    except OSError:
        return False


def is_installed(name: str) -> bool:
    path = text_model_path(name)
    try:
        spec = get_text_model(name)
        if spec.size_bytes == 0:
            return (
                path.exists()
                and path.is_file()
                and path.stat().st_size > 1024
                and _has_gguf_magic(path)
            )
        return (
            path.exists()
            and path.stat().st_size == spec.size_bytes
            and _has_gguf_magic(path)
        )
    except (OSError, TextModelError):
        return False


is_downloaded = is_installed


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


delete_model = delete
delete_text_model = delete


def _text_model_metadata(name: str) -> tuple[str, str, str]:
    """Returns (vram_label, speed_label, quality_label)."""
    lowered = name.lower()
    if "1.7b" in lowered or "1_7b" in lowered:
        return "~1.5 GB VRAM / 4 GB RAM", "Çok Hızlı", "İyi"
    if "3b" in lowered or "3.2" in lowered:
        return "~2.5 GB VRAM / 6 GB RAM", "Hızlı", "Yüksek"
    if "4b" in lowered:
        return "~3.0 GB VRAM / 8 GB RAM", "Dengeli", "Çok Yüksek"
    return "GGUF · Yerel", "Hızlı", "Yüksek"


def scan() -> list[dict]:
    items = []
    # 1. Yerleşik metin modelleri
    for spec in TEXT_MODELS:
        installed = is_installed(spec.name)
        part = partial_bytes(spec.name)
        p = text_model_path(spec.name)
        vram_lbl, speed_lbl, quality_lbl = _text_model_metadata(spec.name)
        items.append(
            {
                "name": spec.name,
                "id": spec.name,
                "kind": "text",
                "label": spec.label,
                "desc": spec.desc,
                "tags": list(spec.tags),
                "size_bytes": spec.size_bytes,
                "approx_bytes": spec.size_bytes,
                "approx_label": "~ " + human_size(spec.size_bytes),
                "size_label": human_size(spec.size_bytes) if installed else "—",
                "installed": installed,
                "partial": (not installed) and part > 0,
                "bytes": installed_bytes(spec.name) if installed else part,
                "custom": False,
                "repo": spec.repo,
                "repo_id": spec.repo,
                "filename": spec.filename,
                "path": str(p),
                "folder": str(p.parent) if installed else "",
                "vram_label": vram_lbl,
                "speed_label": speed_lbl,
                "quality_label": quality_lbl,
            }
        )

    # 2. Özel metin modelleri
    custom_list = load_custom_models().get("text", [])
    for c in custom_list:
        m_name = c.get("name") or c.get("id")
        if not m_name:
            continue
        installed = is_installed(m_name)
        part = partial_bytes(m_name)
        inst_bytes = installed_bytes(m_name)
        size_b = int(c.get("size_bytes") or 0)
        actual_size = inst_bytes if installed else size_b
        p = text_model_path(m_name)
        vram_lbl, speed_lbl, quality_lbl = _text_model_metadata(m_name)
        items.append(
            {
                "name": m_name,
                "id": m_name,
                "kind": "text",
                "label": c.get("label", m_name),
                "desc": c.get("desc", f"Hugging Face: {c.get('repo', '')}"),
                "tags": list(c.get("tags") or ["Özel", "Hugging Face"]),
                "size_bytes": actual_size,
                "approx_bytes": actual_size,
                "approx_label": f"~ {human_size(actual_size)}" if actual_size > 0 else "—",
                "size_label": human_size(actual_size) if installed else "—",
                "installed": installed,
                "partial": (not installed) and part > 0,
                "bytes": inst_bytes if installed else part,
                "custom": True,
                "repo": c.get("repo", ""),
                "repo_id": c.get("repo", ""),
                "filename": c.get("filename", ""),
                "path": str(p),
                "folder": str(p.parent) if installed else "",
                "vram_label": c.get("vram_label") or "GGUF · Yerel",
                "speed_label": c.get("speed_label") or "Değişken",
                "quality_label": c.get("quality_label") or "Özel Model",
            }
        )
    return items


def _normalize_text_repo_and_file(repo_or_url: str, filename: str = "") -> tuple[str, str]:
    if not repo_or_url or not isinstance(repo_or_url, str):
        raise TextModelError("Geçerli bir Hugging Face model adresi veya depo kimliği girin.")
    val = repo_or_url.strip()
    extracted_filename = (filename or "").strip()

    if val.lower().startswith("http://") or val.lower().startswith("https://"):
        parsed = urllib.parse.urlparse(val)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) >= 2:
            repo = f"{parts[0]}/{parts[1]}"
            if not extracted_filename and len(parts) >= 3:
                last = parts[-1]
                if last.lower().endswith(".gguf"):
                    extracted_filename = last
        else:
            raise TextModelError("Geçerli bir Hugging Face repo kimliği veya URL girin.")
    else:
        parts = [p.strip() for p in val.split("/") if p.strip()]
        if len(parts) == 2:
            repo = f"{parts[0]}/{parts[1]}"
        elif len(parts) >= 3 and not extracted_filename:
            repo = f"{parts[0]}/{parts[1]}"
            if parts[-1].lower().endswith(".gguf"):
                extracted_filename = parts[-1]
        else:
            raise TextModelError("Geçerli bir Hugging Face repo kimliği girin (ör. kullanici/model).")

    if not extracted_filename:
        sub = repo.split("/")[-1]
        extracted_filename = f"{sub}.gguf"
    elif not extracted_filename.lower().endswith(".gguf"):
        extracted_filename = f"{extracted_filename}.gguf"

    return repo, extracted_filename


def add_custom_text_model(repo_or_url: str, filename: str = "", label: str = "") -> dict:
    """Hugging Face özel metin (GGUF) modeli ekler ve custom_models.json dosyasına kaydeder."""
    repo, clean_filename = _normalize_text_repo_and_file(repo_or_url, filename)
    slug = "custom-text-" + f"{repo}--{clean_filename}".replace("/", "--").replace(".", "-").lower()

    data = load_custom_models()
    text_list = data.get("text", [])
    for existing in text_list:
        if existing.get("name") == slug or (
            existing.get("repo") == repo and existing.get("filename") == clean_filename
        ):
            if label.strip():
                existing["label"] = label.strip()
                save_custom_models(data)
            return existing

    new_model = {
        "name": slug,
        "id": slug,
        "repo": repo,
        "filename": clean_filename,
        "label": label.strip() or clean_filename.replace(".gguf", "").replace("-", " ").title(),
        "desc": f"Hugging Face: {repo}/{clean_filename}",
        "size_bytes": 0,
        "approx_label": "—",
        "tags": ["Özel", "Hugging Face"],
        "custom": True,
    }
    text_list.append(new_model)
    data["text"] = text_list
    save_custom_models(data)
    logger.info("Özel metin modeli eklendi: %s (%s / %s)", slug, repo, clean_filename)
    return new_model


def remove_custom_text_model(model_id: str) -> None:
    """Özel metin modelini diskten siler ve custom_models.json dosyasından kaldırır."""
    data = load_custom_models()
    text_list = data.get("text", [])
    found = next((m for m in text_list if m.get("name") == model_id or m.get("id") == model_id), None)
    if not found:
        raise TextModelError("Özel model bulunamadı veya yerleşik modeller listeden kaldırılamaz.")

    m_name = found.get("name") or model_id
    try:
        delete(m_name)
    except TextModelError:
        pass

    data["text"] = [m for m in text_list if m.get("name") != m_name and m.get("id") != m_name]
    save_custom_models(data)
    logger.info("Özel metin modeli listeden kaldırıldı: %s", m_name)


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
        if spec.size_bytes > 0 and existing == spec.size_bytes:
            if _has_gguf_magic(part):
                os.replace(part, final)
                return {"completed": True, "paused": False, "cancelled": False, "size": existing}
            try:
                part.unlink(missing_ok=True)
            except OSError:
                pass
            existing = 0
        if (spec.size_bytes > 0 and existing > spec.size_bytes) or (existing >= 4 and not _has_gguf_magic(part)):
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

        # Determine total size from Content-Length or Content-Range
        headers_obj = getattr(response, "headers", None)
        total_remote = 0
        if headers_obj is not None:
            cr = headers_obj.get("Content-Range", "") or ""
            if cr and "/" in cr:
                try:
                    total_remote = int(cr.split("/")[-1].strip())
                except Exception:
                    pass
            if not total_remote:
                cl = headers_obj.get("Content-Length")
                if cl:
                    try:
                        cl_int = int(cl)
                        total_remote = resume_from + cl_int if resume_from else cl_int
                    except Exception:
                        pass
        elif hasattr(response, "length"):
            total_remote = int(getattr(response, "length", 0) or 0)

        effective_total = total_remote if total_remote > 0 else spec.size_bytes

        if spec.size_bytes <= 0 and effective_total > 0:
            try:
                data = load_custom_models()
                for c in data.get("text", []):
                    if c.get("name") == name or c.get("id") == name:
                        c["size_bytes"] = effective_total
                        save_custom_models(data)
                        break
            except Exception:
                pass
            if progress is not None and hasattr(progress, "__closure__") and progress.__closure__:
                for cell in progress.__closure__:
                    val = cell.cell_contents
                    if hasattr(val, "_text_download") and isinstance(val._text_download, dict):
                        val._text_download["total"] = effective_total
                    elif isinstance(val, dict) and "total" in val and "bytes" in val:
                        val["total"] = effective_total

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
                        try:
                            progress(written, effective_total)
                        except TypeError:
                            progress(written)
        finally:
            try:
                response.close()
            except Exception:
                pass

        if spec.size_bytes > 0 and written != spec.size_bytes:
            raise TextModelError(
                f"İndirme tamamlanmadı ({human_size(written)} / {human_size(spec.size_bytes)})."
            )
        if spec.size_bytes == 0 and written <= 1024:
            raise TextModelError("İndirilen model dosyası çok küçük veya eksik.")
        if not _has_gguf_magic(part):
            try:
                part.unlink(missing_ok=True)
            except OSError:
                pass
            raise TextModelError("İndirilen dosya geçerli bir GGUF modeli değil.")
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


class TextModelManager:
    """Metin modelleri yönetim sınıfı."""

    def __init__(self, models_dir: Path | None = None) -> None:
        self._models_dir = Path(models_dir) if models_dir else None
        self._pause_event = threading.Event()
        self._cancel_event = threading.Event()
        self._current_download_name: str | None = None
        self._downloader = Downloader()

    def scan(self) -> list[dict]:
        return scan()

    def list_models(self) -> list[dict]:
        return self.scan()

    def is_installed(self, name: str) -> bool:
        return is_installed(name)

    def is_downloaded(self, name: str) -> bool:
        return is_installed(name)

    def path(self, name: str) -> Path:
        return text_model_path(name)

    def download(self, name: str, progress=None) -> dict:
        self._cancel_event.clear()
        self._pause_event.clear()
        self._current_download_name = name
        try:
            return self._downloader.download(
                name,
                progress=progress,
                pause_event=self._pause_event,
                cancel_event=self._cancel_event,
            )
        finally:
            self._current_download_name = None

    def pause_download(self) -> dict:
        self._pause_event.set()
        return {"paused": True}

    def cancel_download(self) -> dict:
        self._cancel_event.set()
        name = self._current_download_name
        if name:
            try:
                delete_part(name)
            except Exception:
                pass
        return {"cancelled": True}

    def delete(self, name: str) -> None:
        delete(name)

    def delete_model(self, name: str) -> None:
        self.delete(name)

    def add_custom_text_model(self, repo_or_url: str, filename: str = "", label: str = "") -> dict:
        return add_custom_text_model(repo_or_url, filename, label)

    def remove_custom_text_model(self, model_id: str) -> None:
        remove_custom_text_model(model_id)
