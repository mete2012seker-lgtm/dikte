"""Sürüm tutarlılığı: tek kaynak config.APP_VERSION; paket, kurucu ve latest.json aynı sürümü taşır."""

import json
import re
from pathlib import Path

import dikte
from dikte import config, openrouter, text_models

ROOT = Path(__file__).resolve().parents[1]


def test_paket_surumu_config_ile_ayni():
    assert dikte.__version__ == config.APP_VERSION


def test_user_agent_surumu_config_ile_ayni():
    assert text_models.USER_AGENT == f"Dikte/{config.APP_VERSION}"
    assert openrouter.USER_AGENT == f"Dikte/{config.APP_VERSION}"


def test_inno_eski_surumu_icermez():
    iss = (ROOT / "installer" / "Dikte.iss").read_text(encoding="utf-8")
    assert "1.3.0" not in iss
    assert "1.6.0" in iss  # yedek sürüm; build.ps1 version.iss ile üstüne yazar


def test_latest_json_surumu_config_ile_ayni():
    data = json.loads((ROOT / "installer" / "latest.json").read_text(encoding="utf-8"))
    assert data["version"] == config.APP_VERSION
    assert re.fullmatch(r"[0-9a-f]{64}", data["sha256"])


def test_update_url_github_releases():
    assert config.UPDATE_URL == (
        "https://github.com/mete2012seker-lgtm/dikte/releases/latest/download/latest.json"
    )
