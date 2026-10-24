"""Arayüz testi: Python köprüsü sahte (stub) ile dört ana durumu doğrular."""

from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "dikte" / "ui" / "index.html"
ARTIFACTS = ROOT / "artifacts"

STUB = r"""
window.__snap = {
  state: "loading",
  status: "Model yükleniyor…",
  seq: 0,
  latest_text: "",
  model: null,
  model_name: null,
  device: null,
  compute: null,
  memory: null,
  activity: [],
  error: null,
  hotkey: "Sağ Ctrl",
  language: "Türkçe"
};
window.__copied = null;
window.pywebview = {
  api: {
    snapshot: async () => JSON.parse(JSON.stringify(window.__snap)),
    toggle_record: async () => ({ ok: true, state: window.__snap.state }),
    copy: async (text) => { window.__copied = text; return { ok: true }; }
  }
};
"""


@pytest.fixture(scope="module")
def page():
    from playwright.sync_api import sync_playwright

    ARTIFACTS.mkdir(exist_ok=True)
    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.launch(channel="msedge")
    except Exception as exc:  # Edge yoksa testi atla
        playwright.stop()
        pytest.skip(f"Edge tarayıcısı bulunamadı: {exc}")

    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.add_init_script(STUB)
    page.goto(PAGE.as_uri())
    yield page
    browser.close()
    playwright.stop()


def set_snapshot(page, **values):
    page.evaluate(
        """(values) => Object.assign(window.__snap, values)""",
        values,
    )


def test_dikte_ekrani_durumlari(page):
    # İlk açılış: model yükleniyor.
    page.wait_for_function(
        "() => document.querySelector('#statusText').textContent.includes('Model yükleniyor')"
    )
    assert page.locator("#stage").get_attribute("class") == "stage is-loading"

    # Hazır: gerçek model, cihaz ve bellek bilgisi.
    set_snapshot(
        page,
        state="ready",
        model="Whisper Large",
        model_name="large-v3",
        device="GPU",
        compute="float16",
        memory={"used": 4.8, "total": 12.0, "unit": "GB", "source": "VRAM", "percent": 40.0},
        activity=[{"time": "10:42", "title": "Model yüklendi", "sub": "Whisper Large · GPU", "kind": "info"}],
    )
    page.wait_for_function(
        "() => document.querySelector('#statusText').textContent === 'Dinlemeye hazır'"
    )
    assert page.locator("#modelName").inner_text() == "Whisper Large"
    assert page.locator("#device").inner_text() == "GPU"
    assert page.locator("#memText").inner_text() == "4.8 GB / 12 GB"
    assert "Model yüklendi" in page.locator("#activityList").inner_text()

    # Dinleniyor.
    set_snapshot(page, state="recording")
    page.wait_for_function(
        "() => document.querySelector('#stage').classList.contains('is-listening')"
    )
    assert page.locator("#statusText").inner_text() == "Dinleniyor…"
    assert page.locator("#shortcutHint").inner_text() == "Durdurmak için tekrar tıkla"

    # İşleniyor.
    set_snapshot(page, state="processing")
    page.wait_for_function(
        "() => document.querySelector('#stage').classList.contains('is-processing')"
    )

    # Yeni dikte metni eklenir.
    set_snapshot(
        page,
        state="ready",
        seq=1,
        latest_text="Merhaba dünya. Türkçe karakterler: ı, ğ, ş, ç, ö, ü.",
        activity=[
            {"time": "10:43", "title": "Dikte tamamlandı", "sub": "(0 dk 08 sn) · 7 kelime", "kind": "ok"},
            {"time": "10:42", "title": "Model yüklendi", "sub": "Whisper Large · GPU", "kind": "info"},
        ],
    )
    page.wait_for_function("() => document.querySelectorAll('#transcript p').length === 1")
    assert "Türkçe karakterler" in page.locator("#transcript").inner_text()
    assert not page.locator("#undoBtn").is_disabled()
    assert "Dikte tamamlandı" in page.locator("#activityList").inner_text()

    # İkinci dikte eklenir, Kopyala tüm metni Python'a gönderir.
    set_snapshot(page, seq=2, latest_text="İkinci paragraf.")
    page.wait_for_function("() => document.querySelectorAll('#transcript p').length === 2")
    page.locator("#copyBtn").click()
    page.wait_for_function("() => window.__copied !== null")
    copied = page.evaluate("() => window.__copied")
    assert copied.startswith("Merhaba dünya.")
    assert "İkinci paragraf." in copied

    # Geri Al son paragrafı kaldırır.
    page.locator("#undoBtn").click()
    page.wait_for_function("() => document.querySelectorAll('#transcript p').length === 1")
    assert "İkinci paragraf." not in page.locator("#transcript").inner_text()

    # Hata durumu.
    set_snapshot(
        page,
        state="error",
        error="Model bulunamadı. Kurulum için: python -m dikte --kurulum",
    )
    page.wait_for_function(
        "() => document.querySelector('#stage').classList.contains('is-error')"
    )
    assert "Model bulunamadı" in page.locator("#statusText").inner_text()
    assert page.locator("#readyText").inner_text() == "Hayır"

    # Hatadan sonra hazıra dönüş.
    set_snapshot(page, state="ready", error=None)
    page.wait_for_function(
        "() => document.querySelector('#statusText').textContent === 'Dinlemeye hazır'"
    )
    page.wait_for_function(
        "() => !document.querySelector('#stage').classList.contains('is-error')"
    )

    # Ekran görüntüsü için bildirimleri ve geçici düğme yazısını temizle.
    page.evaluate("() => document.querySelectorAll('.toast').forEach((t) => t.remove())")
    page.wait_for_timeout(1800)
    page.evaluate("() => { document.querySelector('#copyLabel').textContent = 'Kopyala'; }")
    page.screenshot(path=str(ARTIFACTS / "ui-dikte.png"))


def test_v11_ozellikleri_pasif(page):
    page.goto(PAGE.as_uri())
    page.wait_for_function(
        "() => document.querySelector('#statusText').textContent.includes('Model yükleniyor')"
    )
    assert page.locator("#refreshBtn").is_disabled()
    assert page.locator("#cleanBtn").is_disabled()
    assert page.locator("#topLang").is_disabled()

    page.locator('.nav-btn[data-coming="Modeller"]').click()
    page.wait_for_function("() => document.querySelectorAll('.toast').length > 0")
    assert "v1.1" in page.locator(".toast").last.inner_text()
