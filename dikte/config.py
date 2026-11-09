"""Uygulama sabitleri ve yolları."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

APP_NAME = "Dikte"
APP_TITLE = "Dikte — VoxNote AI"
APP_VERSION = "1.6.0"
UNINSTALL_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Dikte_is1"
AUTOSTART_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_VALUE = "Dikte"
# v1.6: yayın yeri GitHub Releases (karar 2026-11-07).
UPDATE_URL = "https://github.com/mete2012seker-lgtm/dikte/releases/latest/download/latest.json"

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parent
UI_DIR = PACKAGE_DIR / "ui"

# Testler ve farklı kurulumlar için ortam değişkeniyle değiştirilebilir.
# Kurulu (PyInstaller) sürümde tüm kullanıcı verisi %LOCALAPPDATA%\Dikte altındadır;
# kurulum klasörü (Program Files) veri içermez, böylece kaldırma yalnız kendi verisini siler.
_FROZEN = bool(getattr(sys, "frozen", False)) and not os.environ.get("DIKTE_DEV")
_APPDATA_ROOT = Path(os.environ.get("LOCALAPPDATA", ROOT_DIR)) / "Dikte"
_APPDATA_DATA_DIR = _APPDATA_ROOT / "data"

MODELS_DIR = Path(os.environ.get("DIKTE_MODELS_DIR", _APPDATA_ROOT / "models" if _FROZEN else ROOT_DIR / "models"))
LOG_DIR = Path(os.environ.get("DIKTE_LOG_DIR", _APPDATA_ROOT / "logs" if _FROZEN else ROOT_DIR / "logs"))
TEMP_DIR = Path(os.environ.get("DIKTE_TEMP_DIR", Path(tempfile.gettempdir()) / "dikte"))
DATA_DIR = Path(os.environ.get("DIKTE_DATA_DIR", _APPDATA_DATA_DIR if _FROZEN else ROOT_DIR / "data"))
# Kaldırıcı bu bayrağı okur: varsa modeller silinmez (Inno [Code] bölümü).
KEEP_MODELS_FLAG = _APPDATA_ROOT / "keep_models.flag"

SETTINGS_FILE = DATA_DIR / "settings.json"
HISTORY_FILE = DATA_DIR / "history.json"
SECRETS_FILE = DATA_DIR / "secrets.json"
OPENROUTER_MODELS_FILE = DATA_DIR / "openrouter_models.json"
LAST_RECORDING = TEMP_DIR / "last.wav"

HISTORY_LIMIT = 500

OPENROUTER_API = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS_URL = OPENROUTER_API + "/models"
OPENROUTER_CHAT_URL = OPENROUTER_API + "/chat/completions"
OPENROUTER_CACHE_HOURS = 24
OPENROUTER_MAX_INPUT_PRICE = 0.30
OPENROUTER_MAX_OUTPUT_PRICE = 0.60
OPENROUTER_MIN_CONTEXT = 8_000
OPENROUTER_MAX_MODELS = 12
OPENROUTER_TIMEOUT = 25.0
TEXT_REQUEST_MAX_TOKENS = 2048

OUTPUT_LANGUAGES = {"tr": "Türkçe", "en": "İngilizce", "de": "Almanca"}
TEXT_PROVIDERS = ("none", "local", "openrouter")
THEMES = ("system", "light", "dark")

DEFAULT_SYSTEM_PROMPT = (
    "Sen bir dikte düzeltme asistanısın. Sana verilen metni anlamını bozmadan düzelt:\n"
    "noktalama, büyük harf, tekrarlar ve dolgu kelimeleri (ee, yani, hmm) temizle.\n"
    "Çeviri istenmişse hedef dile doğal ve akıcı biçimde çevir.\n"
    "Metne bilgi ekleme, yorum yapma, açıklama yazma. Yalnızca son metni döndür."
)

MIN_AUTO_TRANSLATE_WORDS = 3

SELFTEST_WAV = ROOT_DIR / "tests" / "data" / "test.wav"
SELFTEST_TEXT = ROOT_DIR / "tests" / "data" / "test.txt"

LANGUAGE = "tr"
LANGUAGE_LABEL = "Türkçe"
HOTKEY_LABEL = "Sağ Ctrl"

GPU_MODEL = "large-v3"
GPU_COMPUTE = "float16"
CPU_MODEL = "small"
CPU_COMPUTE = "int8"

MODEL_LABELS = {
    "tiny": "Whisper Tiny",
    "base": "Whisper Base",
    "small": "Whisper Small",
    "medium": "Whisper Medium",
    "large-v3": "Whisper Large",
    "large-v3-turbo": "Whisper Large Turbo",
}

SAMPLE_RATE = 16_000
CHANNELS = 1
MIN_RECORD_SECONDS = 0.4
POLL_MS = 200

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000
WINDOW_MIN_WIDTH = 1280
WINDOW_MIN_HEIGHT = 800
WINDOW_BACKGROUND = "#060A14"


def model_label(name: str) -> str:
    """Teknik model adını arayüzde görünen ada çevirir."""
    return MODEL_LABELS.get(name, name)


def is_packaged() -> bool:
    """PyInstaller ile kurulmuş sürümde True döner."""
    return bool(getattr(sys, "frozen", False)) and not os.environ.get("DIKTE_DEV")


def exe_dir() -> Path:
    """Kurulu sürümde uygulamanın bulunduğu klasör."""
    if is_packaged():
        return Path(sys.executable).resolve().parent
    return ROOT_DIR


def text_models_dir() -> Path:
    """GGUF metin modellerinin klasörü (testlerde MODELS_DIR değişebilir)."""
    return Path(MODELS_DIR) / "text"


def ensure_runtime_dirs() -> None:
    """Model, log, veri ve geçici kayıt klasörlerini hazırlar."""
    for folder in (MODELS_DIR, text_models_dir(), LOG_DIR, TEMP_DIR, DATA_DIR):
        folder.mkdir(parents=True, exist_ok=True)
