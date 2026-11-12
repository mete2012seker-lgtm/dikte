"""Ses modeli kataloğu: disk durumu, indirme, silme ve Hugging Face özel modeller."""

from __future__ import annotations

import json
import logging
import os
import shutil
import threading
import urllib.parse
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpeechModel:
    name: str
    label: str
    desc: str
    approx_bytes: int
    tags: tuple[str, ...]
    repo_id: str = ""
    custom: bool = False


GB = 1024**3
MB = 1024**2

SPEECH_MODELS: tuple[SpeechModel, ...] = (
    SpeechModel(
        "large-v3",
        "Whisper Large v3",
        "En yüksek doğruluk. Gürültülü ve uzun kayıtlarda dengeli sonuç verir.",
        int(2.9 * GB),
        ("En yüksek doğruluk", "Çoklu dil", "GPU önerilir"),
        repo_id="Systran/faster-whisper-large-v3",
        custom=False,
    ),
    SpeechModel(
        "large-v3-turbo",
        "Whisper Large v3 Turbo",
        "Large v3'e yakın doğruluk, belirgin biçimde daha hızlı çeviri.",
        int(1.6 * GB),
        ("Hızlı", "Yüksek doğruluk", "Çoklu dil"),
        repo_id="Systran/faster-whisper-large-v3-turbo",
        custom=False,
    ),
    SpeechModel(
        "medium",
        "Whisper Medium",
        "Uzun kayıtlarda yüksek doğruluk; orta seviye bellek kullanımı.",
        int(1.5 * GB),
        ("Dengeli", "Çoklu dil", "Orta bellek"),
        repo_id="Systran/faster-whisper-medium",
        custom=False,
    ),
    SpeechModel(
        "small",
        "Whisper Small",
        "Günlük dikte için hızlı ve hafif; düşük bellekli sistemlere uygun.",
        int(480 * MB),
        ("Hızlı", "Düşük bellek", "CPU yedeği"),
        repo_id="Systran/faster-whisper-small",
        custom=False,
    ),
    SpeechModel(
        "base",
        "Whisper Base",
        "Kısa kayıtlarda çok hızlı; doğruluk Small'a göre daha düşük.",
        int(145 * MB),
        ("Çok hızlı", "En düşük bellek", "Kısa kayıtlar"),
        repo_id="Systran/faster-whisper-base",
        custom=False,
    ),
    SpeechModel(
        "tiny",
        "Whisper Tiny",
        "Deneme ve çok hızlı önizleme için en küçük model.",
        int(75 * MB),
        ("En küçük", "Deneme", "Düşük doğruluk"),
        repo_id="Systran/faster-whisper-tiny",
        custom=False,
    ),
)

_MODEL_NAMES = {model.name for model in SPEECH_MODELS}
_CUSTOM_MODELS_LOCK = threading.RLock()


def _custom_models_path() -> Path:
    from . import config

    return Path(config.CUSTOM_MODELS_FILE)


def load_custom_models(path: Path | None = None) -> dict[str, list[dict]]:
    """custom_models.json dosyasını güvenle okur."""
    file_path = Path(path) if path else _custom_models_path()
    with _CUSTOM_MODELS_LOCK:
        if not file_path.exists():
            return {"speech": [], "text": []}
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return {"speech": [], "text": []}
            return {
                "speech": list(raw.get("speech") or []),
                "text": list(raw.get("text") or []),
            }
        except Exception as exc:
            logger.warning("Özel modeller okunamadı (%s)", exc)
            return {"speech": [], "text": []}


def save_custom_models(data: dict[str, list[dict]], path: Path | None = None) -> None:
    """custom_models.json dosyasını atomik yazar."""
    file_path = Path(path) if path else _custom_models_path()
    with _CUSTOM_MODELS_LOCK:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp = file_path.with_name(
            f"{file_path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
        )
        try:
            payload = json.dumps(data, ensure_ascii=False, indent=2)
            with open(temp, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, file_path)
        except Exception as exc:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                pass
            raise ModelError("Özel modeller kaydedilemedi.") from exc


def _normalize_speech_repo(repo_or_url: str) -> str:
    """Hugging Face repo_id veya URL'sini 'owner/repo' biçimine normalize eder."""
    if not repo_or_url or not isinstance(repo_or_url, str):
        raise ModelError("Geçerli bir Hugging Face repo kimliği girin (ör. kullanici/model-adi).")
    val = repo_or_url.strip()
    if val.lower().startswith("http://") or val.lower().startswith("https://"):
        parsed = urllib.parse.urlparse(val)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) >= 2:
            val = f"{parts[0]}/{parts[1]}"
        else:
            raise ModelError("Geçerli bir Hugging Face repo kimliği girin (ör. kullanici/model-adi).")
    parts = [p.strip() for p in val.split("/") if p.strip()]
    if len(parts) == 2 and not any(" " in p for p in parts):
        return f"{parts[0]}/{parts[1]}"
    raise ModelError("Geçerli bir Hugging Face repo kimliği girin (ör. kullanici/model-adi).")


def get_model(name: str) -> SpeechModel:
    """Model adına göre SpeechModel nesnesi döndürür (yerleşik veya özel)."""
    for model in SPEECH_MODELS:
        if model.name == name:
            return model
    custom_list = load_custom_models().get("speech", [])
    for item in custom_list:
        if item.get("name") == name:
            return SpeechModel(
                name=item["name"],
                label=item.get("label", item["name"]),
                desc=item.get("desc", f"Hugging Face: {item.get('repo_id', '')}"),
                approx_bytes=int(item.get("approx_bytes") or 0),
                tags=tuple(item.get("tags") or ("Özel", "Hugging Face")),
                repo_id=item.get("repo_id", ""),
                custom=True,
            )
    raise ModelError("Bilinmeyen model.")


def repo_folder_name(name: str) -> str:
    """faster-whisper disk klasör adını üretir."""
    if name in _MODEL_NAMES:
        return f"models--Systran--faster-whisper-{name}"
    custom_list = load_custom_models().get("speech", [])
    for item in custom_list:
        if item.get("name") == name:
            repo_id = item.get("repo_id", "")
            if repo_id:
                return f"models--{repo_id.replace('/', '--')}"
    return f"models--{name.replace('/', '--')}"


def model_folder(models_dir: Path, name: str) -> Path:
    return Path(models_dir) / repo_folder_name(name)


def human_size(size_bytes: float) -> str:
    def number(value: float, digits: int) -> str:
        if abs(value - round(value)) < 0.05:
            return str(int(round(value)))
        return f"{value:.{digits}f}".replace(".", ",")

    if size_bytes >= GB:
        return f"{number(size_bytes / GB, 1)} GB"
    if size_bytes >= MB:
        return f"{number(size_bytes / MB, 1)} MB"
    return f"{size_bytes / 1024:.0f} KB"


def folder_size(path: Path) -> int:
    """Klasördeki dosyaların toplam baytı. Klasör yoksa 0."""
    path = Path(path)
    if not path.exists():
        return 0
    total = 0
    try:
        for item in path.rglob("*"):
            try:
                if item.is_file():
                    total += item.stat().st_size
            except OSError:
                continue
    except OSError:
        return total
    return total


_TOKENIZER_FILES = ("tokenizer.json", "vocabulary.txt", "vocabulary.json")


def _snapshot_complete(snap_dir: Path) -> bool:
    config_file = snap_dir / "config.json"
    if not (config_file.is_file() and config_file.stat().st_size > 0):
        return False
    return any(
        (snap_dir / tok).is_file() and (snap_dir / tok).stat().st_size > 0
        for tok in _TOKENIZER_FILES
    )


def model_file(models_dir: Path, name: str) -> Path | None:
    snapshots = model_folder(models_dir, name) / "snapshots"
    if not snapshots.exists():
        return None
    try:
        for candidate in snapshots.rglob("model.bin"):
            if (
                candidate.is_file()
                and candidate.stat().st_size > 0
                and _snapshot_complete(candidate.parent)
            ):
                return candidate
    except OSError:
        return None
    return None


def installed_size(models_dir: Path, name: str) -> int:
    folder = model_folder(models_dir, name)
    if not folder.exists():
        return 0
    return folder_size(folder)


def scan(models_dir: Path) -> dict[str, dict]:
    """Her model için disk durumunu döndürür (yerleşik ve özel modeller)."""
    result: dict[str, dict] = {}
    models_dir = Path(models_dir)

    # 1. Yerleşik modeller
    for model in SPEECH_MODELS:
        folder = model_folder(models_dir, model.name)
        size = folder_size(folder)
        has_model = model_file(models_dir, model.name) is not None
        exists = folder.exists()
        result[model.name] = {
            "name": model.name,
            "label": model.label,
            "desc": model.desc,
            "tags": list(model.tags),
            "approx_bytes": model.approx_bytes,
            "approx_label": f"~ {human_size(model.approx_bytes)}",
            "installed": has_model,
            "partial": bool(exists and not has_model and size > 0),
            "size_bytes": size,
            "size_label": human_size(size) if size else "—",
            "folder": str(folder),
            "custom": False,
            "repo_id": model.repo_id,
        }

    # 2. Özel modeller
    custom_list = load_custom_models().get("speech", [])
    for item in custom_list:
        m_name = item["name"]
        folder = model_folder(models_dir, m_name)
        size = folder_size(folder)
        has_model = model_file(models_dir, m_name) is not None
        exists = folder.exists()
        approx = int(item.get("approx_bytes") or 0)
        result[m_name] = {
            "name": m_name,
            "label": item.get("label", m_name),
            "desc": item.get("desc", f"Hugging Face: {item.get('repo_id', '')}"),
            "tags": list(item.get("tags") or ["Özel", "Hugging Face"]),
            "approx_bytes": approx,
            "approx_label": f"~ {human_size(approx)}" if approx else "—",
            "installed": has_model,
            "partial": bool(exists and not has_model and size > 0),
            "size_bytes": size,
            "size_label": human_size(size) if size else "—",
            "folder": str(folder),
            "custom": True,
            "repo_id": item.get("repo_id", ""),
        }

    return result


def add_custom_model(repo_id: str, label: str = "") -> dict:
    """Hugging Face ses modeli ekler ve custom_models.json dosyasına kaydeder."""
    clean_repo = _normalize_speech_repo(repo_id)
    slug = "custom-" + clean_repo.replace("/", "--").replace(".", "-").lower()

    data = load_custom_models()
    speech_list = data.get("speech", [])
    for existing in speech_list:
        if existing.get("repo_id") == clean_repo or existing.get("name") == slug:
            if label.strip():
                existing["label"] = label.strip()
                save_custom_models(data)
            return existing

    new_model = {
        "name": slug,
        "repo_id": clean_repo,
        "label": label.strip() or clean_repo.split("/")[-1],
        "desc": f"Hugging Face özel modeli: {clean_repo}",
        "approx_bytes": 0,
        "approx_label": "—",
        "tags": ["Özel", "Hugging Face"],
        "custom": True,
    }
    speech_list.append(new_model)
    data["speech"] = speech_list
    save_custom_models(data)
    logger.info("Özel ses modeli eklendi: %s (%s)", slug, clean_repo)
    return new_model


def remove_custom_model(name: str, models_dir: Path | None = None) -> None:
    """Özel ses modelini diskten siler ve custom_models.json dosyasından kaldırır."""
    data = load_custom_models()
    speech_list = data.get("speech", [])
    found = next((m for m in speech_list if m.get("name") == name), None)
    if not found:
        raise ModelError("Özel model bulunamadı veya yerleşik modeller listeden kaldırılamaz.")

    from . import config

    mdir = Path(models_dir or config.MODELS_DIR)
    try:
        delete(name, mdir)
    except ModelError:
        pass

    data["speech"] = [m for m in speech_list if m.get("name") != name]
    save_custom_models(data)
    logger.info("Özel ses modeli listeden kaldırıldı: %s", name)


def _download_model(name: str, models_dir: Path) -> str:
    from faster_whisper.utils import download_model

    model_spec = get_model(name)
    target = model_spec.repo_id if model_spec.custom and model_spec.repo_id else name

    try:
        return download_model(target, cache_dir=str(models_dir))
    except TypeError:
        return download_model(target, output_dir=str(models_dir))


def download(
    name: str,
    models_dir: Path,
    progress=None,
    cancel_event: threading.Event | None = None,
) -> str:
    """Modeli indirir. cancel_event ile durdurulabilir."""
    get_model(name)
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    folder = model_folder(models_dir, name)
    stop = threading.Event()

    def report() -> None:
        if progress is None:
            return
        try:
            progress(folder_size(folder))
        except Exception:
            logger.debug("İlerleme bildirilemedi", exc_info=True)

    def monitor() -> None:
        while not stop.wait(0.5):
            if cancel_event is not None and cancel_event.is_set():
                break
            report()

    watcher = threading.Thread(target=monitor, name=f"model-izle-{name}", daemon=True)
    watcher.start()
    try:
        report()
        if cancel_event is not None and cancel_event.is_set():
            raise ModelError("İndirme iptal edildi.")

        path = _download_model(name, models_dir)

        if cancel_event is not None and cancel_event.is_set():
            shutil.rmtree(folder, ignore_errors=True)
            raise ModelError("İndirme iptal edildi.")

        logger.info("Model indirildi: %s -> %s", name, path)
        return str(path)
    except ModelError:
        raise
    except Exception as exc:
        if cancel_event is not None and cancel_event.is_set():
            shutil.rmtree(folder, ignore_errors=True)
            raise ModelError("İndirme iptal edildi.") from exc
        logger.exception("Model indirilemedi: %s", name)
        raise ModelError(
            "Model indirilemedi. İnternet bağlantısını kontrol edip tekrar dene."
        ) from exc
    finally:
        stop.set()
        report()


def delete(name: str, models_dir: Path) -> None:
    """Model klasörünü ve kilit girdisini siler (özel modeller custom_models.json'da kalır)."""
    get_model(name)
    models_dir = Path(models_dir)
    folder = model_folder(models_dir, name)
    lock = models_dir / ".locks" / repo_folder_name(name)
    if not folder.exists() and not lock.exists():
        raise ModelError("Model zaten kurulu değil.")
    try:
        if folder.exists():
            shutil.rmtree(folder)
        if lock.exists():
            shutil.rmtree(lock)
    except PermissionError as exc:
        raise ModelError(
            "Model silinemedi. Dosya başka bir işlem tarafından kullanılıyor olabilir."
        ) from exc
    except Exception as exc:
        logger.exception("Model silinemedi: %s", name)
        raise ModelError("Model silinemedi. Ayrıntı log dosyasında.") from exc
    logger.info("Model silindi: %s", name)


class ModelManager:
    """Modül fonksiyonlarını bir klasör etrafında toplar; testlerde sahtelenebilir."""

    def __init__(self, models_dir: Path | None = None) -> None:
        from . import config

        self.models_dir = Path(models_dir or config.MODELS_DIR)
        self._cancel_event = threading.Event()
        self._current_download_name: str | None = None

    def scan(self) -> dict[str, dict]:
        return scan(self.models_dir)

    def list_models(self) -> dict[str, dict]:
        return self.scan()

    def installed(self, name: str) -> bool:
        return model_file(self.models_dir, name) is not None

    def size(self, name: str) -> int:
        return installed_size(self.models_dir, name)

    def folder(self, name: str) -> Path:
        return model_folder(self.models_dir, name)

    def download(self, name: str, progress=None) -> str:
        self._cancel_event.clear()
        self._current_download_name = name
        try:
            return download(
                name,
                self.models_dir,
                progress=progress,
                cancel_event=self._cancel_event,
            )
        finally:
            self._current_download_name = None

    def cancel_download(self) -> dict:
        """Süren indirmeyi iptal eder ve yarım kalan klasörü temizler."""
        self._cancel_event.set()
        name = self._current_download_name
        if name:
            folder = self.folder(name)
            try:
                shutil.rmtree(folder, ignore_errors=True)
            except Exception:
                pass
        return {"cancelled": True}

    def delete(self, name: str) -> None:
        delete(name, self.models_dir)

    def add_custom_model(self, repo_id: str, label: str = "") -> dict:
        return add_custom_model(repo_id, label)

    def remove_custom_model(self, name: str) -> None:
        remove_custom_model(name, self.models_dir)
