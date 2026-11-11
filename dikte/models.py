"""Ses modeli kataloğu: disk durumu, indirme ve silme."""

from __future__ import annotations

import logging
import shutil
import threading
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


GB = 1024**3
MB = 1024**2

SPEECH_MODELS: tuple[SpeechModel, ...] = (
    SpeechModel(
        "large-v3",
        "Whisper Large v3",
        "En yüksek doğruluk. Gürültülü ve uzun kayıtlarda dengeli sonuç verir.",
        int(2.9 * GB),
        ("En yüksek doğruluk", "Çoklu dil", "GPU önerilir"),
    ),
    SpeechModel(
        "large-v3-turbo",
        "Whisper Large v3 Turbo",
        "Large v3'e yakın doğruluk, belirgin biçimde daha hızlı çeviri.",
        int(1.6 * GB),
        ("Hızlı", "Yüksek doğruluk", "Çoklu dil"),
    ),
    SpeechModel(
        "medium",
        "Whisper Medium",
        "Uzun kayıtlarda yüksek doğruluk; orta seviye bellek kullanımı.",
        int(1.5 * GB),
        ("Dengeli", "Çoklu dil", "Orta bellek"),
    ),
    SpeechModel(
        "small",
        "Whisper Small",
        "Günlük dikte için hızlı ve hafif; düşük bellekli sistemlere uygun.",
        int(480 * MB),
        ("Hızlı", "Düşük bellek", "CPU yedeği"),
    ),
    SpeechModel(
        "base",
        "Whisper Base",
        "Kısa kayıtlarda çok hızlı; doğruluk Small'a göre daha düşük.",
        int(145 * MB),
        ("Çok hızlı", "En düşük bellek", "Kısa kayıtlar"),
    ),
    SpeechModel(
        "tiny",
        "Whisper Tiny",
        "Deneme ve çok hızlı önizleme için en küçük model.",
        int(75 * MB),
        ("En küçük", "Deneme", "Düşük doğruluk"),
    ),
)

_MODEL_NAMES = {model.name for model in SPEECH_MODELS}


def get_model(name: str) -> SpeechModel:
    for model in SPEECH_MODELS:
        if model.name == name:
            return model
    raise ModelError("Bilinmeyen model.")


def repo_folder_name(name: str) -> str:
    return f"models--Systran--faster-whisper-{name}"


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
    """Her model için disk durumunu döndürür."""
    result: dict[str, dict] = {}
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
        }
    return result


class ModelManager:
    """Modül fonksiyonlarını bir klasör etrafında toplar; testlerde sahtelenebilir."""

    def __init__(self, models_dir: Path | None = None) -> None:
        from . import config

        self.models_dir = Path(models_dir or config.MODELS_DIR)

    def scan(self) -> dict[str, dict]:
        return scan(self.models_dir)

    def installed(self, name: str) -> bool:
        return model_file(self.models_dir, name) is not None

    def size(self, name: str) -> int:
        return installed_size(self.models_dir, name)

    def folder(self, name: str) -> Path:
        return model_folder(self.models_dir, name)

    def download(self, name: str, progress=None) -> str:
        return download(name, self.models_dir, progress=progress)

    def delete(self, name: str) -> None:
        delete(name, self.models_dir)


def _download_model(name: str, models_dir: Path) -> str:
    from faster_whisper.utils import download_model

    try:
        return download_model(name, cache_dir=str(models_dir))
    except TypeError:
        # Eski faster-whisper sürümlerinde parametre adı farklı.
        return download_model(name, output_dir=str(models_dir))


def download(name: str, models_dir: Path, progress=None) -> str:
    """Modeli indirir. İlerleme, klasör boyutu izlenerek bildirilir."""
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
            report()

    watcher = threading.Thread(target=monitor, name=f"model-izle-{name}", daemon=True)
    watcher.start()
    try:
        report()
        path = _download_model(name, models_dir)
        logger.info("Model indirildi: %s -> %s", name, path)
        return str(path)
    except Exception as exc:
        logger.exception("Model indirilemedi: %s", name)
        raise ModelError(
            "Model indirilemedi. İnternet bağlantısını kontrol edip tekrar dene."
        ) from exc
    finally:
        stop.set()
        report()


def delete(name: str, models_dir: Path) -> None:
    """Model klasörünü ve kilit girdisini siler."""
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
