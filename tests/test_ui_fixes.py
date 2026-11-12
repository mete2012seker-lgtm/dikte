"""Test suite for UI, Animation, Theme and Auto-save fixes."""

from __future__ import annotations

import re
from pathlib import Path
import pytest

from dikte import settings, config

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "dikte" / "ui"
INDEX_HTML = UI_DIR / "index.html"
STYLE_CSS = UI_DIR / "style.css"
APP_JS = UI_DIR / "app.js"


def test_index_html_microphone_morph_structure():
    """index.html must match design/mikrofon_morph_animasyonu.html structure exactly."""
    content = INDEX_HTML.read_text(encoding="utf-8")
    assert '<div class="stage" id="stage">' in content
    assert '<canvas id="waveCanvas"></canvas>' in content
    assert '<div class="halo-wrapper" aria-hidden="true">' in content
    assert '<div class="halo-ring halo-ring--outer"></div>' in content
    assert '<div class="halo-ring halo-ring--inner"></div>' in content
    assert 'class="mic-btn"' in content
    assert 'class="icon-morph"' in content
    assert 'class="mic-svg"' in content
    assert 'class="stop-square"' in content
    assert '<div class="status-line">' in content
    assert 'id="statusDot"' in content
    assert 'id="statusText"' in content

    # Old obsolete wave elements must be removed
    assert 'class="stage-row"' not in content
    assert 'id="waveLeft"' not in content
    assert 'id="waveRight"' not in content


def test_index_html_brand_and_theme_toggle():
    """index.html must have clean brand logo, toggle button and theme button."""
    content = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="brandToggle"' in content
    assert 'class="brand-logo"' in content
    assert 'class="brand-ic"' in content
    assert 'id="sidebarCollapseBtn"' in content
    assert 'id="themeToggle"' in content
    assert 'id="themeBtnLabel"' in content
    assert 'id="dikteAiModelPill"' in content
    assert 'class="auto-save-label"' in content


def test_index_html_design_style_controls():
    """index.html must have design choice toggle buttons."""
    content = INDEX_HTML.read_text(encoding="utf-8")
    assert 'data-design-choice="dikte_ai"' in content
    assert 'data-design-choice="classic"' in content


def test_style_css_morph_animation_properties():
    """style.css must have exact cubic-bezier easing and morphing transforms."""
    content = STYLE_CSS.read_text(encoding="utf-8")
    assert "cubic-bezier(0.22, 1, 0.36, 1)" in content or "cubic-bezier(0.22,1,0.36,1)" in content
    assert ".halo-wrapper" in content
    assert ".halo-ring--outer" in content
    assert ".halo-ring--inner" in content
    assert "height:320px" in content or "height: 320px" in content
    assert "calc(-50% + 72px)" in content
    assert ".stage.is-recording .mic-btn" in content
    assert "scale(0.41)" in content
    assert ".stage.is-recording .stop-square" in content
    assert "opacity: 1" in content or "opacity:1" in content


def test_style_css_dikte_ai_and_classic_themes():
    """style.css must support both dikte_ai and classic in light and dark modes."""
    content = STYLE_CSS.read_text(encoding="utf-8")
    assert 'html[data-design="dikte_ai"].light' in content
    assert 'html[data-design="dikte_ai"].dark' in content
    assert 'html[data-design="classic"]' in content

    # In dikte_ai mode, single column layout and aside hidden
    assert 'html[data-design="dikte_ai"] #page-dikte .dikte-layout' in content
    assert 'html[data-design="dikte_ai"] #page-dikte .dikte-layout aside' in content
    assert 'html[data-design="dikte_ai"] .active-model-pill' in content
    assert 'html[data-design="dikte_ai"] .statusbar' in content


def test_app_js_morph_wave_logic():
    """app.js must implement the 48-bar morphing audio wave simulation from design."""
    content = APP_JS.read_text(encoding="utf-8")
    assert "BARS_PER_SIDE = 24" in content
    assert "TOTAL_BARS = BARS_PER_SIDE * 2" in content
    assert "sampleCurveX" in content
    assert "sampleCurveY" in content
    assert "3 * y1 * t" in content
    assert "easeMorph" in content
    assert "idleHeights" in content
    assert "renderWaveAnim" in content
    assert "centerY = h * 0.43" in content
    assert "dikteAiModelPill" in content


def test_app_js_activity_timeline_deduplication():
    """app.js renderActivity must collapse repetitive 'Ayarlar kaydedildi' entries."""
    content = APP_JS.read_text(encoding="utf-8")
    assert "function renderActivity(items)" in content
    assert "Ayarlar kaydedildi" in content
    assert "foundSettingsSaved" in content or "sawSettingsSaved" in content


def test_app_js_instant_settings_save():
    """app.js must provide triggerInstantSettingsSave."""
    content = APP_JS.read_text(encoding="utf-8")
    assert "function triggerInstantSettingsSave()" in content
    assert "api.ai_settings_save" in content
