"""Cihaz, bellek ve hata teşhisi yardımcıları."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

_cuda_prepared = False
_dll_handles: list = []


def prepare_cuda_dlls() -> None:
    """pip ile kurulan CUDA DLL'lerini Windows'a tanıtır.

    CTranslate2, cublas/cuDNN DLL'lerini PATH üzerinde arar. Sanal ortamdaki
    nvidia paketleri PATH'e otomatik eklenmediği için burada ekliyoruz.
    """
    global _cuda_prepared
    if _cuda_prepared or sys.platform != "win32":
        _cuda_prepared = True
        return
    _cuda_prepared = True
    try:
        import importlib
        import sysconfig

        bases = set()
        if getattr(sys, "frozen", False):
            frozen_nvidia = config.exe_dir() / "nvidia"
            if frozen_nvidia.is_dir():
                bases.add(frozen_nvidia)
        # nvidia paketleri namespace paket olabilir; __file__ boş kalırsa
        # doğrudan sanal ortamın site-packages klasörünü kullan.
        try:
            site_packages = Path(sysconfig.get_paths()["purelib"])
            base_candidate = site_packages / "nvidia"
            if base_candidate.is_dir():
                bases.add(base_candidate)
        except Exception:
            pass

        for module_name in ("nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_runtime"):
            try:
                module = importlib.import_module(module_name)
                if module.__file__:
                    bases.add(Path(module.__file__).resolve().parent.parent)
            except Exception:
                continue

        added = []
        for base in bases:
            for relative in (("cublas", "bin"), ("cudnn", "bin"), ("cudnn", "lib"), ("cuda_runtime", "bin")):
                folder = base.joinpath(*relative)
                if not folder.is_dir():
                    continue
                try:
                    # Handle yaşamalı; aksi halde Windows klasörü kaldırır.
                    _dll_handles.append(os.add_dll_directory(str(folder)))
                except Exception:
                    pass
                os.environ["PATH"] = str(folder) + os.pathsep + os.environ.get("PATH", "")
                added.append(str(folder))
        if added:
            logger.info("CUDA DLL klasörleri PATH'e eklendi: %s", ", ".join(added))
    except Exception as exc:
        logger.debug("CUDA DLL hazırlığı yapılamadı: %s", exc)



def configure_console() -> None:
    """Windows konsolunda Türkçe karakterlerin bozulmasını engeller."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# Kullanıcıya gösterilecek sabit Türkçe mesajlar.
MSG_MODEL_MISSING = (
    "Model bulunamadı. Kurulum için komut penceresinde şunu çalıştır: "
    "python -m dikte --kurulum"
)
MSG_MIC_MISSING = (
    "Mikrofon bulunamadı. Windows Ayarlar > Gizlilik ve güvenlik > Mikrofon "
    "bölümünden izni kontrol et."
)
MSG_TRANSCRIBE_FAILED = "Yazıya çevirme başarısız oldu. Lütfen tekrar dene."
MSG_CLIPBOARD_FAILED = "Metin panoya kopyalanamadı. Kopyala düğmesini dene."
MSG_GPU_FALLBACK = "GPU kullanılamadı, CPU moduna geçildi (int8)."
MSG_PLAN_FALLBACK = "Model yüklenemedi, yedek plana geçildi."
MSG_EMPTY_AUDIO = "Ses algılanamadı. Kayıt çok kısa veya sessizdi."


def setup_logging() -> None:
    """Log dosyasını hazırlar. Konuşulan metin asla loglanmaz."""
    config.ensure_runtime_dirs()
    log_file = config.LOG_DIR / "dikte.log"
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    root.addHandler(handler)
    # Konsolda da kısa bilgi görünsün.
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(console)


def cuda_device_count() -> int:
    """CUDA görünen cihaz sayısı. Kütüphane yoksa 0 döner."""
    prepare_cuda_dlls()
    try:
        import ctranslate2

        return int(ctranslate2.get_cuda_device_count())
    except Exception as exc:  # kütüphane yok veya sürücü sorunlu
        logger.info("CUDA kontrolü yapılamadı: %s", exc)
        return 0


def format_gb(value_bytes: float) -> float:
    return round(value_bytes / (1024**3), 1)


def read_memory(use_gpu: bool) -> dict | None:
    """Kullanılan/toplam belleği GB olarak döndürür."""
    if use_gpu:
        try:
            import pynvml

            pynvml.nvmlInit()
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                return {
                    "used": format_gb(info.used),
                    "total": format_gb(info.total),
                    "unit": "GB",
                    "source": "VRAM",
                    "percent": round(info.used / info.total * 100, 1),
                }
            finally:
                pynvml.nvmlShutdown()
        except Exception as exc:
            logger.debug("VRAM okunamadı: %s", exc)
            return None

    try:
        import psutil

        used = psutil.Process().memory_info().rss
        total = psutil.virtual_memory().total
        return {
            "used": format_gb(used),
            "total": format_gb(total),
            "unit": "GB",
            "source": "RAM",
            "percent": round(used / total * 100, 1),
        }
    except Exception as exc:
        logger.debug("RAM okunamadı: %s", exc)
        return None


def python_version_warning() -> str | None:
    if sys.version_info < (3, 10):
        return "Dikte için Python 3.10 veya üzeri gerekir."
    return None


def log_environment(info: dict) -> None:
    logger.info(
        "Ortam | python=%s | cuda=%s | model=%s | cihaz=%s",
        info.get("python"),
        info.get("cuda"),
        info.get("model"),
        info.get("device"),
    )


def open_log_folder() -> Path:
    return config.LOG_DIR
