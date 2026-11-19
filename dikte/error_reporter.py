"""Gömülü hata yakalama, log analizi, gizlilik maskeleme ve tanılama raporu aracı."""

from __future__ import annotations

import faulthandler
import json
import logging
import os
import platform
import re
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config, diagnostics

logger = logging.getLogger(__name__)

_SAFE_SETTINGS_KEYS = (
    "active_model",
    "text_provider",
    "text_model",
    "openrouter_model",
    "input_language",
    "output_language",
    "auto_translate",
    "auto_paste",
    "hotkey",
    "design_style",
    "theme",
    "save_history",
    "setup_done",
    "update_check_on_start",
)

_MASK_TOKEN = "***MASKELENDI***"
_RE_SK_OPENROUTER = re.compile(r"sk-or-v1-[A-Za-z0-9_-]+")
_RE_SK_GENERIC = re.compile(r"sk-[A-Za-z0-9_-]{12,}")
_RE_BEARER = re.compile(r"(?i)\bBearer\s+\S+")
_RE_API_KEY = re.compile(r"(?i)api[_-]?key\s*[:=]\s*\S+")
_RE_WIN_USER_BACKSLASH = re.compile(r"(?i)([A-Za-z]:\\Users\\)([^\\\"'<>|;,:\r\n]+)")
_RE_WIN_USER_SLASH = re.compile(r"(?i)([A-Za-z]:/Users/)([^/\"'<>|;,:\r\n]+)")

_JS_THROTTLE_SECONDS = 30.0
_MAX_LOG_BYTES = 64 * 1024
_MAX_LOG_LINES = 120

_hooks_installed = False
_orig_sys_excepthook = sys.excepthook
_orig_threading_excepthook = getattr(threading, "excepthook", None)
_faulthandler_file: Any = None
_previous_crash_info: dict | None = None
_js_error_cache: dict[str, float] = {}
_state_lock = threading.Lock()


def sanitize_text(text: str | None) -> str:
    """API anahtarlarını, Bearer belirteçlerini ve Windows kullanıcı yollarını maskeler."""
    if text is None:
        return ""
    value = str(text)
    if not value:
        return ""
    value = _RE_SK_OPENROUTER.sub(_MASK_TOKEN, value)
    value = _RE_SK_GENERIC.sub(_MASK_TOKEN, value)
    value = _RE_BEARER.sub(_MASK_TOKEN, value)
    value = _RE_API_KEY.sub(_MASK_TOKEN, value)
    value = _RE_WIN_USER_BACKSLASH.sub(r"\1<KULLANICI>", value)
    value = _RE_WIN_USER_SLASH.sub(r"\1<KULLANICI>", value)
    return value


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(
        f"{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        with open(tmp_path, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _atomic_write_json(path: Path, payload: dict) -> None:
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def _crash_file() -> Path:
    return config.DATA_DIR / "last_crash.json"


def _running_lock_file() -> Path:
    return config.DATA_DIR / "running.lock"


def _native_crash_file() -> Path:
    return config.LOG_DIR / "native_crash.log"


def _write_crash_record(exc_type: type[BaseException] | None, exc_value: BaseException | None, exc_tb: Any) -> None:
    try:
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        tb_text = sanitize_text("".join(tb_lines))
        msg_text = sanitize_text(str(exc_value) if exc_value is not None else "")
        type_name = exc_type.__name__ if exc_type is not None else "UnknownError"
        record = {
            "timestamp": _now_iso(),
            "type": type_name,
            "message": msg_text,
            "traceback": tb_text,
        }
        _atomic_write_json(_crash_file(), record)
    except Exception:
        pass


def install_global_hooks() -> None:
    """faulthandler, sys.excepthook ve threading.excepthook kancalarını kurar."""
    global _hooks_installed, _orig_sys_excepthook, _orig_threading_excepthook, _faulthandler_file
    with _state_lock:
        try:
            config.ensure_runtime_dirs()
            native_path = _native_crash_file()
            native_path.parent.mkdir(parents=True, exist_ok=True)
            if _faulthandler_file is None or getattr(_faulthandler_file, "closed", True):
                _faulthandler_file = open(native_path, "a", encoding="utf-8")
                faulthandler.enable(file=_faulthandler_file, all_threads=True)
        except Exception as exc:
            logger.debug("faulthandler etkinleştirilemedi: %s", exc)

        if _hooks_installed:
            return
        _orig_sys_excepthook = sys.excepthook
        _orig_threading_excepthook = getattr(threading, "excepthook", None)

        def _sys_hook(exc_type, exc_value, exc_tb):
            if issubclass(exc_type, KeyboardInterrupt):
                if _orig_sys_excepthook:
                    _orig_sys_excepthook(exc_type, exc_value, exc_tb)
                return
            try:
                logger.error(
                    "Yakalanmayan uygulama hatası: %s",
                    sanitize_text(str(exc_value)),
                    exc_info=(exc_type, exc_value, exc_tb),
                )
            except Exception:
                pass
            _write_crash_record(exc_type, exc_value, exc_tb)
            if _orig_sys_excepthook and _orig_sys_excepthook is not _sys_hook:
                try:
                    _orig_sys_excepthook(exc_type, exc_value, exc_tb)
                except Exception:
                    pass

        def _thread_hook(args):
            exc_type = getattr(args, "exc_type", None)
            exc_value = getattr(args, "exc_value", None)
            exc_tb = getattr(args, "exc_traceback", None)
            if exc_type in (KeyboardInterrupt, SystemExit):
                if _orig_threading_excepthook:
                    _orig_threading_excepthook(args)
                return
            thread_name = getattr(getattr(args, "thread", None), "name", "unknown")
            try:
                logger.error(
                    "Yakalanmayan iş parçacığı hatası (%s): %s",
                    thread_name,
                    sanitize_text(str(exc_value)),
                    exc_info=(exc_type, exc_value, exc_tb),
                )
            except Exception:
                pass
            _write_crash_record(exc_type, exc_value, exc_tb)
            if _orig_threading_excepthook and _orig_threading_excepthook is not _thread_hook:
                try:
                    _orig_threading_excepthook(args)
                except Exception:
                    pass

        sys.excepthook = _sys_hook
        if hasattr(threading, "excepthook"):
            threading.excepthook = _thread_hook
        _hooks_installed = True


def mark_running_start() -> bool:
    """Önceki oturumun kirli kapanıp kapanmadığını kontrol eder ve yeni kilidi yazar."""
    global _previous_crash_info
    config.ensure_runtime_dirs()
    lock_path = _running_lock_file()
    crash_path = _crash_file()

    dirty_lock = None
    if lock_path.exists():
        try:
            dirty_lock = json.loads(lock_path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            dirty_lock = {"raw": True}

    crash_data = None
    if crash_path.exists():
        try:
            crash_data = json.loads(crash_path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            crash_data = {"type": "UnknownCrash", "message": "Okunamayan çökme kaydı"}

    detected = bool(dirty_lock is not None or crash_data is not None)
    with _state_lock:
        if detected:
            _previous_crash_info = {
                "detected": True,
                "dirty_shutdown": dirty_lock is not None,
                "lock_info": dirty_lock,
                "crash": crash_data,
            }
        else:
            _previous_crash_info = None

    try:
        _atomic_write_json(
            lock_path,
            {
                "pid": os.getpid(),
                "version": config.APP_VERSION,
                "started_at": _now_iso(),
            },
        )
    except Exception as exc:
        logger.debug("running.lock yazılamadı: %s", exc)

    return detected


def mark_clean_shutdown() -> None:
    """Temiz kapanışta running.lock dosyasını siler."""
    try:
        lock_path = _running_lock_file()
        if lock_path.exists():
            lock_path.unlink()
    except Exception as exc:
        logger.debug("running.lock silinemedi: %s", exc)


def dismiss_crash() -> None:
    """Çökme kaydını ve oturum içi çökme uyarısını temizler."""
    global _previous_crash_info
    with _state_lock:
        _previous_crash_info = None
    try:
        crash_path = _crash_file()
        if crash_path.exists():
            crash_path.unlink()
    except Exception as exc:
        logger.debug("last_crash.json silinemedi: %s", exc)


def _check_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _read_pyav_info() -> tuple[str | None, bool]:
    try:
        import av

        version = str(getattr(av, "__version__", ""))
        major_str = version.split(".", 1)[0]
        digits = "".join(ch for ch in major_str if ch.isdigit())
        major = int(digits) if digits else 0
        return version or None, (11 <= major < 16)
    except Exception:
        return None, False


def _read_sounddevice_input() -> dict:
    try:
        import sounddevice as sd

        dev = sd.query_devices(kind="input")
        name = sanitize_text(str(dev.get("name", ""))) if isinstance(dev, dict) else sanitize_text(str(dev))
        return {"available": True, "name": name}
    except Exception as exc:
        return {"available": False, "error": sanitize_text(str(exc))}


def _read_log_tail() -> str:
    log_path = config.LOG_DIR / "dikte.log"
    if not log_path.exists():
        return ""
    try:
        size = log_path.stat().st_size
        with open(log_path, "rb") as fh:
            if size > _MAX_LOG_BYTES:
                fh.seek(size - _MAX_LOG_BYTES)
            raw = fh.read()
        text = raw.decode("utf-8", errors="replace")
        lines = text.splitlines()
        if size > _MAX_LOG_BYTES and lines:
            lines = lines[1:]
        tail = "\n".join(lines[-_MAX_LOG_LINES:])
        return sanitize_text(tail)
    except Exception as exc:
        return f"Log okunamadı: {sanitize_text(str(exc))}"


def _read_crash_info() -> dict | None:
    with _state_lock:
        prev = dict(_previous_crash_info) if _previous_crash_info else None

    crash_file_data = None
    crash_path = _crash_file()
    if crash_path.exists():
        try:
            crash_file_data = json.loads(crash_path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            crash_file_data = {"type": "UnknownCrash", "message": "Çökme dosyası bozuk"}

    native_tail = ""
    native_path = _native_crash_file()
    if native_path.exists():
        try:
            if native_path.stat().st_size > 0:
                raw = native_path.read_bytes()[-16384:]
                native_tail = sanitize_text(raw.decode("utf-8", errors="replace")).strip()
        except Exception:
            pass

    if not prev and not crash_file_data and not native_tail:
        return None

    return {
        "detected": bool(prev or crash_file_data),
        "previous_session": prev,
        "last_crash": crash_file_data,
        "native_crash_tail": native_tail,
    }


def _extract_controller_info(controller: Any) -> dict:
    if controller is None:
        return {}
    snap: dict = {}
    try:
        if hasattr(controller, "snapshot") and callable(controller.snapshot):
            res = controller.snapshot()
            if isinstance(res, dict):
                snap = res
    except Exception:
        snap = {}

    activity_raw = snap.get("activity") or []
    safe_activity = []
    for item in activity_raw:
        if not isinstance(item, dict):
            continue
        safe_activity.append(
            {
                "title": sanitize_text(str(item.get("title", ""))),
                "sub": sanitize_text(str(item.get("sub", ""))),
                "kind": str(item.get("kind", "ok")),
            }
        )

    safe_settings: dict[str, Any] = {}
    settings_obj = getattr(controller, "settings", None)
    if settings_obj is not None:
        for key in _SAFE_SETTINGS_KEYS:
            try:
                if hasattr(settings_obj, "get") and callable(settings_obj.get):
                    val = settings_obj.get(key)
                    if val is not None:
                        safe_settings[key] = sanitize_text(val) if isinstance(val, str) else val
            except Exception:
                continue

    err = snap.get("error")
    if err is None:
        err = getattr(controller, "_error", None)

    return {
        "state": snap.get("state") or getattr(controller, "state", None),
        "active_model": snap.get("model_name") or snap.get("model"),
        "device": snap.get("device"),
        "hotkey_id": snap.get("hotkey_id"),
        "current_error": sanitize_text(str(err)) if err else None,
        "activity": safe_activity,
        "safe_settings": safe_settings,
    }


def collect_diagnostics(controller: Any = None) -> dict:
    """Sistem, çalışma zamanı, güvenli ayarlar ve maskelenmiş log bilgilerini toplar.

    GİZLİLİK KURALI: history.json, secrets.json, last.wav ve konuşma metni ASLA okunmaz.
    """
    try:
        cuda_count = diagnostics.cuda_device_count()
    except Exception:
        cuda_count = 0

    pyav_version, pyav_compatible = _read_pyav_info()

    env_info = {
        "app_version": config.APP_VERSION,
        "python_version": platform.python_version(),
        "packaged": config.is_packaged(),
        "os": platform.platform(),
        "cuda_devices": cuda_count,
        "pyav_version": pyav_version,
        "pyav_compatible": pyav_compatible,
        "llama_cpp_available": _check_module("llama_cpp"),
        "sounddevice_input": _read_sounddevice_input(),
        "pynput_available": _check_module("pynput"),
        "pystray_available": _check_module("pystray"),
        "pywebview_available": _check_module("webview"),
    }

    runtime = _extract_controller_info(controller)
    log_tail = _read_log_tail()
    crash_info = _read_crash_info()

    return {
        "env": env_info,
        "runtime": runtime,
        "log_tail": log_tail,
        "crash_info": crash_info,
    }


def _build_diagnosis(
    has_issue: bool,
    severity: str,
    code: str | None,
    summary_title: str,
    explanation: str,
    steps: list[str],
    crash_detected: bool,
) -> dict:
    return {
        "has_issue": has_issue,
        "severity": severity,
        "code": code,
        "summary_title": summary_title,
        "explanation": explanation,
        "steps": steps,
        "crash_detected": crash_detected,
    }


def _analyze_collected(collected: dict) -> dict:
    env = collected.get("env") or {}
    runtime = collected.get("runtime") or {}
    log_tail = collected.get("log_tail") or ""
    crash_info = collected.get("crash_info")
    current_error = runtime.get("current_error") or ""

    combined = f"{current_error}\n{log_tail}".lower()
    crash_detected = bool(crash_info and crash_info.get("detected"))

    # 1. Önceki çökme / kirli kapanış
    if crash_detected:
        last_crash = (crash_info or {}).get("last_crash") or {}
        err_type = last_crash.get("type") or "Beklenmedik Kapanış"
        return _build_diagnosis(
            True,
            "error",
            "previous_crash",
            "Önceki oturumda beklenmedik kapanış tespit edildi",
            f"Uygulama bir önceki çalışmada düzgün kapanmadı ({err_type}).",
            [
                "Aşağıdaki tanılama raporunu dışa aktararak hata ayrıntısını saklayabilirsin.",
                "Sorun tekrar ederse Ayarlar > Yapay Zeka veya Modeller bölümünden son seçtiğin modeli kontrol et.",
                "Uyarıyı kapatmak için 'Çökme Uyarısını Kapat' düğmesini kullan.",
            ],
            True,
        )

    # 2. PyAV uyumsuzluğu
    if (env.get("pyav_version") and not env.get("pyav_compatible")) or (
        "metadata_errors" in combined or "av.open" in combined
    ):
        return _build_diagnosis(
            True,
            "error",
            "pyav_incompatible",
            "PyAV sürümü faster-whisper ile uyumsuz",
            f"Kurulu PyAV sürümü ({env.get('pyav_version') or 'bilinmiyor'}) 11–15 aralığında olmalıdır.",
            [
                "PyAV 16 ve üzeri sürümlerde ses açma çağrısı çöker.",
                "Geliştirici ortamında 'pip install \"av>=11,<16\"' çalıştır veya güncel Dikte kurucusunu yeniden kur.",
            ],
            False,
        )

    # 3. CUDA DLL eksikliği
    if any(k in combined for k in ("cublas", "cudnn", "cudart", "c10_cuda", "nvcuda", "cuda dll")) and any(
        k in combined
        for k in (
            "error",
            "hata",
            "failed",
            "not found",
            "bulunamad",
            "cannot open",
            "could not load",
            "eksik",
            "loadlibrary",
            "dll load failed",
        )
    ):
        return _build_diagnosis(
            True,
            "error",
            "cuda_dll_missing",
            "CUDA hızlandırma bileşenleri eksik veya yüklenemedi",
            "NVIDIA GPU hızlandırması için gereken CUDA DLL dosyaları bulunamadı.",
            [
                "Kurulum sonrası karşılama sihirbazından CUDA bileşenini indirebilir veya CPU modunda devam edebilirsin.",
                "NVIDIA ekran kartı sürücünün güncel olduğundan emin ol.",
            ],
            False,
        )

    # 4. WebView2 eksikliği
    if any(k in combined for k in ("webview2", "edgechromium")) and any(
        k in combined for k in ("not found", "eksik", "failed", "bulunamad", "error")
    ):
        return _build_diagnosis(
            True,
            "error",
            "webview2_missing",
            "Microsoft Edge WebView2 çalışma zamanı eksik",
            "Dikte arayüzünün açılması için Windows WebView2 bileşeni gerekiyor.",
            [
                "Microsoft Edge WebView2 Evergreen Runtime kurucusunu yükleyip uygulamayı yeniden başlat.",
            ],
            False,
        )

    # 5. Model eksik veya bozuk
    if any(
        k in combined
        for k in (
            "model bulunamad",
            "unable to open file",
            "invalid gguf",
            "gguf",
            "checksum",
            "sha256",
            "model bozuk",
        )
    ) and any(k in combined for k in ("hata", "error", "failed", "bulunamad", "bozuk", "corrupt")):
        return _build_diagnosis(
            True,
            "error",
            "model_missing_or_corrupt",
            "Ses veya metin modeli eksik ya da bozuk",
            "Seçili model dosyası diskte bulunamadı veya doğrulanamadı.",
            [
                "Modeller sayfasından aktif modeli yeniden indir.",
                "İndirme yarıda kaldıysa modeli silip tekrar indir.",
            ],
            False,
        )

    # 6. Ağ / Hugging Face / SSL hatası
    if any(
        k in combined
        for k in (
            "sslerror",
            "ssl:",
            "certificate_verify_failed",
            "getaddrinfo failed",
            "connectionerror",
            "urlopen error",
        )
    ) or (
        any(k in combined for k in ("huggingface", "hf_hub", "ssl", "certificate"))
        and any(k in combined for k in ("error", "hata", "failed", "timeout", "bağlanamad", "reddedildi"))
    ):
        return _build_diagnosis(
            True,
            "warn",
            "network_hf_ssl",
            "Ağ bağlantısı veya SSL sertifika hatası",
            "Model indirme veya güncelleme sunucusuna bağlanılamadı.",
            [
                "İnternet bağlantını, VPN veya kurumsal proxy/güvenlik duvarı ayarlarını kontrol et.",
                "Birkaç dakika sonra indirmeyi tekrar dene.",
            ],
            False,
        )

    # 7. Mikrofon izni veya cihaz hatası
    if any(
        k in combined
        for k in (
            "mikrofon bulunamad",
            "portaudio",
            "no default input device",
            "invalid number of channels",
            "paunanticipatedhosterror",
        )
    ):
        return _build_diagnosis(
            True,
            "error",
            "mic_permission_or_device",
            "Mikrofon erişimi veya ses giriş cihazı sorunu",
            "Ses kaydı başlatılırken mikrofon açılamadı.",
            [
                "Windows Ayarlar > Gizlilik ve güvenlik > Mikrofon bölümünden masaüstü uygulamalarına izin ver.",
                "Mikrofonunun takılı ve Windows'ta varsayılan giriş cihazı seçili olduğunu doğrula.",
            ],
            False,
        )

    # 8. Kısayol dinleyici hatası
    if any(k in combined for k in ("kısayol dinlenemedi", "hotkey", "pynput")) and any(
        k in combined for k in ("hata", "error", "failed", "başlatılamad")
    ):
        return _build_diagnosis(
            True,
            "warn",
            "hotkey_hook_failed",
            "Genel kısayol dinleyicisi başlatılamadı",
            "Klavye kısayolunu yakalayan arka plan dinleyicisi engellendi.",
            [
                "Ayarlar'dan farklı bir bas-konuş kısayolu seçmeyi dene.",
                "Güvenlik yazılımı klavye kancasını engelliyorsa Dikte'ye izin ver.",
            ],
            False,
        )

    # 9. Otomatik yapıştırma UIPI engeli
    if any(k in combined for k in ("uipi", "sendinput", "otomatik yapıştırma")) and any(
        k in combined for k in ("engell", "failed", "denied", "hata", "yapıştırılamad")
    ):
        return _build_diagnosis(
            True,
            "warn",
            "paste_uipi_blocked",
            "Otomatik yapıştırma hedef pencere tarafından engellendi",
            "Yönetici yetkili bir pencereye yapıştırma Windows güvenlik kuralına (UIPI) takıldı.",
            [
                "Metin yine de panoya kopyalanmıştır; Ctrl+V ile yapıştırabilirsin.",
                "Yönetici pencerelere sürekli yazman gerekiyorsa Dikte'yi yönetici olarak çalıştır.",
            ],
            False,
        )

    # 10. OpenRouter yetkilendirme / kota hatası
    if "openrouter" in combined and any(
        k in combined for k in ("401", "402", "403", "429", "unauthorized", "insufficient", "kota", "rate limit")
    ):
        return _build_diagnosis(
            True,
            "warn",
            "openrouter_auth_quota",
            "OpenRouter API anahtarı veya kredi limiti hatası",
            "OpenRouter isteği yetkilendirme veya bakiye nedeniyle reddedildi.",
            [
                "Ayarlar > Yapay Zeka bölümünden OpenRouter API anahtarını kontrol et ve 'Test et' düğmesine bas.",
                "OpenRouter hesabındaki kalan krediyi ve model limitlerini kontrol et.",
            ],
            False,
        )

    # 11. llama-cpp / VRAM bellek hatası
    if any(k in combined for k in ("llama_cpp", "llama.cpp", "out of memory", "cuda out of memory", "ggml")) and any(
        k in combined for k in ("error", "hata", "failed", "memory", "yetersiz", "bulunamad")
    ):
        return _build_diagnosis(
            True,
            "warn",
            "llama_oom_or_missing",
            "Yerel metin modeli belleği veya motor hatası",
            "Yerel yapay zeka metin modeli yüklenemedi veya VRAM/RAM yetersiz kaldı.",
            [
                "Daha küçük bir metin modeli (ör. qwen3-1.7b) seç veya arka planda VRAM kullanan uygulamaları kapat.",
                "Alternatif olarak Ayarlar > Yapay Zeka'dan OpenRouter veya 'Yok' seçeneğini kullanabilirsin.",
            ],
            False,
        )

    # 12. Arayüz JavaScript hatası
    if "ui js hatası:" in combined:
        return _build_diagnosis(
            True,
            "warn",
            "js_error",
            "Arayüz betik (JavaScript) hatası kaydedildi",
            "Uygulama arayüzünde bir betik hatası yakalandı.",
            [
                "Uygulamayı yeniden başlatmayı dene.",
                "Sorun sürerse tanılama raporunu dışa aktarıp paylaş.",
            ],
            False,
        )

    return _build_diagnosis(
        False,
        "ok",
        None,
        "Sorun tespit edilmedi",
        "Sistem ve log kayıtları normal görünüyor.",
        [],
        False,
    )


def analyze_errors(controller: Any = None) -> dict:
    """Loglar, çalışma durumu ve ortam bilgilerini analiz ederek olası sorunu döndürür."""
    collected = collect_diagnostics(controller)
    return _analyze_collected(collected)


def _build_system_summary(collected: dict) -> dict:
    env = collected.get("env") or {}
    runtime = collected.get("runtime") or {}
    return {
        "app_version": env.get("app_version"),
        "python_version": env.get("python_version"),
        "packaged": env.get("packaged"),
        "os": env.get("os"),
        "cuda_devices": env.get("cuda_devices"),
        "pyav_version": env.get("pyav_version"),
        "pyav_compatible": env.get("pyav_compatible"),
        "llama_cpp_available": env.get("llama_cpp_available"),
        "sounddevice_input": env.get("sounddevice_input"),
        "pynput_available": env.get("pynput_available"),
        "pystray_available": env.get("pystray_available"),
        "pywebview_available": env.get("pywebview_available"),
        "state": runtime.get("state"),
        "active_model": runtime.get("active_model"),
        "device": runtime.get("device"),
        "hotkey_id": runtime.get("hotkey_id"),
        "current_error": runtime.get("current_error"),
        "safe_settings": runtime.get("safe_settings") or {},
    }


def _format_from_collected(collected: dict, diagnosis: dict) -> str:
    env = collected.get("env") or {}
    runtime = collected.get("runtime") or {}
    log_tail = collected.get("log_tail") or "(Log kaydı yok)"
    crash_info = collected.get("crash_info")

    lines = [
        "============================================================",
        f"DİKTE TANILAMA RAPORU — v{env.get('app_version', config.APP_VERSION)}",
        f"Tarih (UTC): {_now_iso()}",
        "============================================================",
        "",
        "[ÖZET]",
        f"Durum      : {diagnosis.get('severity', 'ok').upper()}",
        f"Kod        : {diagnosis.get('code') or '-'}",
        f"Başlık     : {diagnosis.get('summary_title')}",
        f"Açıklama   : {diagnosis.get('explanation')}",
    ]

    steps = diagnosis.get("steps") or []
    if steps:
        lines.append("")
        lines.append("[ÖNERİLEN ADIMLAR]")
        for idx, step in enumerate(steps, 1):
            lines.append(f"{idx}. {step}")

    sd_in = env.get("sounddevice_input") or {}
    mic_str = sd_in.get("name") if sd_in.get("available") else f"Kullanılamıyor ({sd_in.get('error', '-')})"
    lines.extend(
        [
            "",
            "[SİSTEM DURUMU]",
            f"İşletim Sistemi : {env.get('os')}",
            f"Python          : {env.get('python_version')}",
            f"Paketli Kurulum : {'Evet' if env.get('packaged') else 'Hayır'}",
            f"CUDA Cihazı     : {env.get('cuda_devices')}",
            f"PyAV            : {env.get('pyav_version') or 'Yok'} (Uyumlu: {'Evet' if env.get('pyav_compatible') else 'Hayır'})",
            f"llama-cpp       : {'Var' if env.get('llama_cpp_available') else 'Yok'}",
            f"Mikrofon        : {mic_str}",
            f"pynput/pystray/webview: {env.get('pynput_available')}/{env.get('pystray_available')}/{env.get('pywebview_available')}",
        ]
    )

    if runtime:
        lines.extend(
            [
                "",
                "[ÇALIŞMA DURUMU]",
                f"Durum           : {runtime.get('state') or '-'}",
                f"Aktif Model     : {runtime.get('active_model') or '-'}",
                f"Cihaz           : {runtime.get('device') or '-'}",
                f"Kısayol         : {runtime.get('hotkey_id') or '-'}",
                f"Aktif Hata      : {runtime.get('current_error') or 'Yok'}",
            ]
        )

    safe_settings = runtime.get("safe_settings") or {}
    if safe_settings:
        lines.append("")
        lines.append("[GÜVENLİ AYARLAR]")
        for key, val in safe_settings.items():
            lines.append(f"{key}: {val}")

    if crash_info:
        lines.append("")
        lines.append("[ÇÖKME BİLGİSİ]")
        last_crash = crash_info.get("last_crash") or {}
        if last_crash:
            lines.append(f"Zaman : {last_crash.get('timestamp', '-')}")
            lines.append(f"Tür   : {last_crash.get('type', '-')}")
            lines.append(f"Mesaj : {sanitize_text(str(last_crash.get('message', '-')))}")
            tb = sanitize_text(str(last_crash.get("traceback", "")))
            if tb:
                lines.append(tb.strip())
        native_tail = sanitize_text(str(crash_info.get("native_crash_tail") or "")).strip()
        if native_tail:
            lines.append("Yerel (Native) Çökme Kaydı:")
            lines.append(native_tail)

    lines.extend(
        [
            "",
            "[SON LOG KAYITLARI (MASKELENMİŞ)]",
            log_tail,
            "",
        ]
    )
    return "\n".join(lines)


def format_report_text(controller: Any = None) -> str:
    """Paylaşıma hazır, gizli verilerden arındırılmış Türkçe .txt raporu üretir."""
    collected = collect_diagnostics(controller)
    diagnosis = _analyze_collected(collected)
    return _format_from_collected(collected, diagnosis)


def get_diagnostics_payload(controller: Any = None) -> dict:
    """Arayüz için tek çağrıda tüm tanılama yükünü döndürür."""
    collected = collect_diagnostics(controller)
    diagnosis = _analyze_collected(collected)
    report_text = _format_from_collected(collected, diagnosis)
    return {
        "ok": True,
        "has_issue": bool(diagnosis.get("has_issue")),
        "diagnosis": diagnosis,
        "system_summary": _build_system_summary(collected),
        "log_tail": collected.get("log_tail") or "",
        "report_text": report_text,
    }


def export_report(controller: Any = None) -> Path:
    """Tanılama raporunu LOG_DIR altında zaman damgalı .txt dosyasına kaydeder."""
    config.ensure_runtime_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = config.LOG_DIR / f"dikte-tanilama-{stamp}.txt"
    content = format_report_text(controller)
    _atomic_write_text(target, content)
    return target


def record_js_error(payload: dict | None) -> dict:
    """Arayüzden gelen JavaScript hatalarını maskeleyip hız sınırlayarak loglar."""
    data = payload if isinstance(payload, dict) else {}
    message = sanitize_text(str(data.get("message") or "Bilinmeyen arayüz hatası"))[:400]
    source = sanitize_text(str(data.get("source") or "-"))[:200]
    line = data.get("line", "-")
    col = data.get("col", "-")

    cache_key = f"{message}|{source}|{line}|{col}"
    now = time.monotonic()
    with _state_lock:
        last_seen = _js_error_cache.get(cache_key)
        if last_seen is not None and (now - last_seen) < _JS_THROTTLE_SECONDS:
            return {"ok": True, "throttled": True}
        _js_error_cache[cache_key] = now
        if len(_js_error_cache) > 100:
            oldest = min(_js_error_cache, key=_js_error_cache.get)
            _js_error_cache.pop(oldest, None)

    logger.error("UI JS hatası: %s (kaynak=%s, satır=%s, sütun=%s)", message, source, line, col)
    return {"ok": True}


def write_emergency_report(exc: BaseException) -> Path | None:
    """Başlatma sırasında ölümcül hata olursa acil durum raporu yazar."""
    try:
        config.ensure_runtime_dirs()
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = config.LOG_DIR / f"dikte-acil-rapor-{stamp}.txt"
        tb_text = sanitize_text("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
        body = "\n".join(
            [
                f"DİKTE ACİL DURUM RAPORU — v{config.APP_VERSION}",
                f"Tarih (UTC): {_now_iso()}",
                f"Hata Türü  : {type(exc).__name__}",
                f"Mesaj      : {sanitize_text(str(exc))}",
                "",
                tb_text,
            ]
        )
        _atomic_write_text(target, body)
        return target
    except Exception:
        return None


def show_emergency_dialog(title: str, message: str) -> None:
    """Windows'ta acil durum hata penceresi gösterir; başsız/diğer ortamlarda sessizce atlar."""
    if sys.platform != "win32" or os.environ.get("DIKTE_HEADLESS"):
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, str(message), str(title), 0x10)
    except Exception:
        pass
