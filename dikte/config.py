"""Uygulama sabitleri ve yolları."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

APP_NAME = "Dikte"
APP_TITLE = "Dikte — VoxNote AI"

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parent
UI_DIR = PACKAGE_DIR / "ui"

# Testler ve farklı kurulumlar için ortam değişkeniyle değiştirilebilir.
MODELS_DIR = Path(os.environ.get("DIKTE_MODELS_DIR", ROOT_DIR / "models"))
LOG_DIR = Path(os.environ.get("DIKTE_LOG_DIR", ROOT_DIR / "logs"))
TEMP_DIR = Path(os.environ.get("DIKTE_TEMP_DIR", Path(tempfile.gettempdir()) / "dikte"))
DATA_DIR = Path(os.environ.get("DIKTE_DATA_DIR", ROOT_DIR / "data"))

SETTINGS_FILE = DATA_DIR / "settings.json"
HISTORY_FILE = DATA_DIR / "history.json"
LAST_RECORDING = TEMP_DIR / "last.wav"

HISTORY_LIMIT = 500

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


def ensure_runtime_dirs() -> None:
    """Model, log, veri ve geçici kayıt klasörlerini hazırlar."""
    for folder in (MODELS_DIR, LOG_DIR, TEMP_DIR, DATA_DIR):
        folder.mkdir(parents=True, exist_ok=True)
