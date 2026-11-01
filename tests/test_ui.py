"""Arayüz testleri: Python köprüsü sahte (stub) ile dört sayfa doğrulanır."""

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
  replace_last: false,
  model: null,
  model_name: null,
  device: null,
  compute: null,
  memory: null,
  activity: [],
  error: null,
  hotkey: "Sağ Ctrl",
  language: "Türkçe",
  save_history: true,
  can_refresh: false,
  download: null
};
window.__copied = null;
window.__calls = [];
window.__historyDisabled = false;
window.__history = [
  { id: "h1", created_at: "2026-10-27T10:42:00", duration: 154,
    words: 248, model: "large-v3",
    text: "Bu akşam okuduğum makalede yerel yapay zeka modellerinin gizlilik avantajları anlatılıyordu." },
  { id: "h2", created_at: "2026-10-26T09:15:00", duration: 72,
    words: 132, model: "small",
    text: "Sabah toplantısında konuşulan üç ana başlığı not aldım." }
];
window.__settings = {
  save_history: true,
  hotkey: "right_ctrl",
  hotkey_label: "Sağ Ctrl",
  active_model: "large-v3",
  state: "ready",
  choices: [
    { id: "right_ctrl", label: "Sağ Ctrl" },
    { id: "left_ctrl", label: "Sol Ctrl" },
    { id: "right_alt", label: "Sağ Alt" },
    { id: "left_alt", label: "Sol Alt" },
    { id: "f8", label: "F8" },
    { id: "f9", label: "F9" },
    { id: "f10", label: "F10" }
  ]
};
window.__models = {
  active_model: "large-v3",
  device: "GPU",
  download: null,
  items: [
    { name: "large-v3", label: "Whisper Large v3", desc: "En yüksek doğruluk.",
      tags: ["En yüksek doğruluk", "Çoklu dil"], approx_label: "~ 2,9 GB",
      installed: true, partial: false, size_label: "2,9 GB", size_bytes: 3000000000,
      active: true, downloading: false },
    { name: "small", label: "Whisper Small", desc: "Hızlı ve hafif.",
      tags: ["Hızlı", "Düşük bellek"], approx_label: "~ 480 MB",
      installed: true, partial: false, size_label: "461 MB", size_bytes: 461000000,
      active: false, downloading: false },
    { name: "tiny", label: "Whisper Tiny", desc: "En küçük model.",
      tags: ["En küçük", "Deneme"], approx_label: "~ 75 MB",
      installed: false, partial: false, size_label: "—", size_bytes: 0,
      active: false, downloading: false }
  ]
};

function snapshotCopy() { const copy = JSON.parse(JSON.stringify(window.__snap)); copy.ai.state = copy.state; return copy; }

window.__ai = {
  provider: "none",
  provider_label: "Kapalı",
  output_language: "tr",
  output_language_label: "Türkçe",
  auto_translate: false,
  input_language: "auto",
  auto_paste: true,
  text_model: "qwen3-4b",
  openrouter_model: null,
  system_prompt: "Varsayılan prompt",
  default_system_prompt: "Varsayılan prompt",
  key_set: false,
  key_masked: null,
  state: "ready",
  ready: true
};
window.__snap.ai = window.__ai;
window.__settings.ai = window.__ai;

window.pywebview = {
  api: {
    snapshot: async () => snapshotCopy(),
    toggle_record: async () => ({ ok: true, state: window.__snap.state }),
    copy: async (text) => { window.__copied = text; return { ok: true }; },
    refresh_last: async () => { window.__calls.push("refresh_last"); return { ok: true, state: "processing" }; },
    history_list: async (query, period) => {
      const q = (query || "").toLocaleLowerCase("tr");
      const items = window.__history.filter((item) =>
        !q || item.text.toLocaleLowerCase("tr").includes(q));
      return { disabled: window.__historyDisabled, items, total: items.length };
    },
    history_open: async (id) => {
      window.__calls.push("history_open:" + id);
      const item = window.__history.find((entry) => entry.id === id);
      return item ? { ok: true, text: item.text, id } : { ok: false, message: "yok" };
    },
    history_delete: async (id) => {
      window.__calls.push("history_delete:" + id);
      window.__history = window.__history.filter((entry) => entry.id !== id);
      return { ok: true };
    },
    history_clear: async () => { window.__history = []; return { ok: true }; },
    models_list: async () => JSON.parse(JSON.stringify(window.__models)),
    model_download: async (name) => { window.__calls.push("download:" + name); return { ok: true, message: name + " indiriliyor." }; },
    model_activate: async (name) => { window.__calls.push("activate:" + name); return { ok: true, state: "loading" }; },
    model_delete: async (name) => { window.__calls.push("delete:" + name); return { ok: true, message: name + " silindi." }; },
    settings_get: async () => JSON.parse(JSON.stringify(window.__settings)),
    settings_save: async (payload) => {
      window.__calls.push("settings_save:" + JSON.stringify(payload));
      window.__settings = Object.assign(window.__settings, payload);
      return { ok: true, message: "Ayarlar kaydedildi.", settings: window.__settings };
    },
    ai_state: async () => JSON.parse(JSON.stringify(window.__ai)),
    ai_settings_save: async (payload) => {
      window.__calls.push("ai_settings_save:" + JSON.stringify(payload));
      if ("text_provider" in payload) {
        window.__ai.provider = payload.text_provider;
        window.__ai.provider_label =
          payload.text_provider === "openrouter" ? "OpenRouter"
          : payload.text_provider === "local" ? "Yerel model" : "Kapalı";
      }
      Object.assign(window.__ai, payload);
      Object.assign(window.__snap.ai, window.__ai);
      return { ok: true, message: "Ayarlar kaydedildi.", ai: JSON.parse(JSON.stringify(window.__ai)) };
    },
    clean_text: async (text) => {
      window.__calls.push("clean_text");
      return { ok: true, text: "TEMİZ: " + text, message: "Metin düzenlendi." };
    },
    translate_text: async (text) => {
      window.__calls.push("translate_text");
      return { ok: true, text: "ÇEVİRİ: " + text, message: "Metin çevrildi." };
    },
    openrouter_key_save: async (key) => {
      window.__ai.key_set = true;
      window.__ai.key_masked = "sk-or-…" + key.slice(-4);
      Object.assign(window.__snap.ai, window.__ai);
      return { ok: true, message: "Anahtar kaydedildi.", masked: window.__ai.key_masked,
               ai: JSON.parse(JSON.stringify(window.__ai)) };
    },
    openrouter_key_delete: async () => {
      window.__ai.key_set = false;
      window.__ai.key_masked = null;
      Object.assign(window.__snap.ai, window.__ai);
      return { ok: true, message: "Anahtar silindi.", ai: JSON.parse(JSON.stringify(window.__ai)) };
    },
    openrouter_key_test: async () => ({ ok: true, message: "Bağlantı çalışıyor (3 model)." }),
    openrouter_models: async (refresh, all_models, query) => {
      window.__modelCalls = window.__modelCalls || [];
      window.__modelCalls.push({
        refresh: Boolean(refresh),
        all_models: Boolean(all_models),
        query: query || ""
      });
      const catalog = [
        { id: "deepseek/ucuz", name: "DeepSeek Ucuz", price_label: "~$0.05 / $0.10" },
        { id: "qwen/kucuk", name: "Qwen Küçük", price_label: "~$0.08 / $0.12" },
        { id: "openai/pahali", name: "OpenAI Pahalı", price_label: "~$5.00 / $15.00", expensive: true }
      ];
      let items = all_models ? catalog : catalog.filter((m) => !m.expensive);
      const q = (query || "").toLowerCase();
      if (q) items = items.filter((m) => (m.id + " " + m.name).toLowerCase().includes(q));
      return { ok: true, models: items.map((m) => ({
        id: m.id, name: m.name, price_label: m.price_label
      })) };
    }
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
    page.evaluate("(values) => Object.assign(window.__snap, values)", values)


def fresh(page):
    page.goto(PAGE.as_uri())
    page.wait_for_function(
        "() => document.querySelector('#statusText').textContent.includes('Model yükleniyor')"
    )


def test_dikte_ekrani_durumlari(page):
    fresh(page)
    assert page.locator("#stage").get_attribute("class") == "stage is-loading"

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
    assert page.locator("#shortcutHint").inner_text() == "Sağ Ctrl (basılı tut)"

    set_snapshot(page, state="recording")
    page.wait_for_function(
        "() => document.querySelector('#stage').classList.contains('is-listening')"
    )
    assert page.locator("#statusText").inner_text() == "Dinleniyor…"

    set_snapshot(page, state="processing")
    page.wait_for_function(
        "() => document.querySelector('#stage').classList.contains('is-processing')"
    )

    set_snapshot(
        page,
        state="ready",
        seq=1,
        latest_text="Merhaba dünya. Türkçe karakterler: ı, ğ, ş, ç, ö, ü.",
        can_refresh=True,
        activity=[
            {"time": "10:43", "title": "Dikte tamamlandı", "sub": "(0 dk 08 sn) · 7 kelime", "kind": "ok"},
            {"time": "10:42", "title": "Model yüklendi", "sub": "Whisper Large · GPU", "kind": "info"},
        ],
    )
    page.wait_for_function("() => document.querySelectorAll('#transcript p').length === 1")
    assert "Türkçe karakterler" in page.locator("#transcript").inner_text()
    assert not page.locator("#undoBtn").is_disabled()
    assert not page.locator("#refreshBtn").is_disabled()

    set_snapshot(page, seq=2, latest_text="İkinci paragraf.")
    page.wait_for_function("() => document.querySelectorAll('#transcript p').length === 2")
    page.locator("#copyBtn").click()
    page.wait_for_function("() => window.__copied !== null")
    copied = page.evaluate("() => window.__copied")
    assert copied.startswith("Merhaba dünya.")
    assert "İkinci paragraf." in copied

    page.locator("#undoBtn").click()
    page.wait_for_function("() => document.querySelectorAll('#transcript p').length === 1")
    assert "İkinci paragraf." not in page.locator("#transcript").inner_text()

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

    set_snapshot(page, state="ready", error=None)
    page.wait_for_function(
        "() => document.querySelector('#statusText').textContent === 'Dinlemeye hazır'"
    )
    page.evaluate("() => document.querySelectorAll('.toast').forEach((t) => t.remove())")
    page.wait_for_timeout(1800)
    page.evaluate("() => { document.querySelector('#copyLabel').textContent = 'Kopyala'; }")
    page.screenshot(path=str(ARTIFACTS / "ui-dikte.png"))


def test_sayfa_yonlendirme_ve_ekran_goruntuleri(page):
    fresh(page)

    page.locator('.nav-btn[data-page="page-gecmis"]').click()
    page.wait_for_function("() => document.querySelector('#page-gecmis').classList.contains('is-active')")
    page.wait_for_function("() => document.querySelectorAll('#historyList .h-item').length === 2")
    assert page.locator('.nav-btn[data-page="page-gecmis"]').get_attribute("aria-current") == "page"
    assert "2 kayıt" in page.locator("#historyCount").inner_text()
    page.wait_for_timeout(200)
    page.screenshot(path=str(ARTIFACTS / "ui-gecmis.png"))

    page.locator('.nav-btn[data-page="page-modeller"]').click()
    page.wait_for_function("() => document.querySelector('#page-modeller').classList.contains('is-active')")
    page.wait_for_function("() => document.querySelectorAll('#modelList .m-card').length === 3")
    assert "Whisper Large v3" in page.locator("#modelList").inner_text()
    assert "Aktif" in page.locator("#modelList").inner_text()
    assert "Model Detayları" in page.locator("#detailPanel").inner_text()
    page.wait_for_timeout(200)
    page.screenshot(path=str(ARTIFACTS / "ui-modeller.png"))

    page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    page.wait_for_function("() => document.querySelector('#page-ayarlar').classList.contains('is-active')")
    page.wait_for_function("() => document.querySelectorAll('#hotkeySelect option').length === 7")
    assert page.locator("#hotkeySelect").input_value() == "right_ctrl"
    assert page.locator("#historySwitch").get_attribute("aria-checked") == "true"
    page.wait_for_timeout(200)
    page.screenshot(path=str(ARTIFACTS / "ui-ayarlar.png"))

    page.locator('.nav-btn[data-page="page-dikte"]').click()
    page.wait_for_function("() => document.querySelector('#page-dikte').classList.contains('is-active')")


def test_gecmis_arama_acma_ve_silme(page):
    fresh(page)
    page.locator('.nav-btn[data-page="page-gecmis"]').click()
    page.wait_for_function("() => document.querySelectorAll('#historyList .h-item').length === 2")

    page.locator("#historySearch").fill("gizlilik")
    page.wait_for_function("() => document.querySelectorAll('#historyList .h-item').length === 1")
    assert "2 kayıt" not in page.locator("#historyCount").inner_text()

    page.locator("#historySearch").fill("")
    page.wait_for_function("() => document.querySelectorAll('#historyList .h-item').length === 2")

    page.locator('#historyList .h-item[data-id="h1"] .h-actions .btn').first.click()
    page.wait_for_function("() => document.querySelector('#page-dikte').classList.contains('is-active')")
    assert page.evaluate("() => window.__calls.includes('history_open:h1')")

    page.locator('.nav-btn[data-page="page-gecmis"]').click()
    page.wait_for_function("() => document.querySelectorAll('#historyList .h-item').length === 2")
    page.locator('#historyList .h-item[data-id="h1"] .btn-danger').click()
    page.wait_for_function("() => document.querySelectorAll('#historyList .h-item').length === 1")
    assert page.evaluate("() => window.__calls.includes('history_delete:h1')")


def test_gecmis_kapaliyken_bilgi_karti(page):
    fresh(page)
    page.evaluate("() => { window.__historyDisabled = true; }")
    page.locator('.nav-btn[data-page="page-gecmis"]').click()
    page.wait_for_function("() => !document.querySelector('#historyDisabled').hidden")
    assert "Geçmiş kaydedilmiyor" in page.locator("#historyDisabled").inner_text()
    assert page.locator("#historyCard").is_hidden()

    page.locator("#goSettingsBtn").click()
    page.wait_for_function("() => document.querySelector('#page-ayarlar').classList.contains('is-active')")
    page.evaluate("() => { window.__historyDisabled = false; }")


def test_modeller_indir_aktiflestir_sil(page):
    fresh(page)
    page.evaluate("() => { window.__calls = []; }")
    page.locator('.nav-btn[data-page="page-modeller"]').click()
    page.wait_for_function("() => document.querySelectorAll('#modelList .m-card').length === 3")

    page.locator('#modelList .m-card[data-name="tiny"] .m-btn').click()
    page.wait_for_function("() => window.__calls.some((c) => c === 'download:tiny')")

    page.locator('#modelList .m-card[data-name="small"] .m-btn').click()
    page.wait_for_function("() => window.__calls.some((c) => c === 'activate:small')")

    page.on("dialog", lambda dialog: dialog.accept())
    page.locator('#modelList .m-card[data-name="small"] .icon-btn').click()
    page.wait_for_function("() => window.__calls.some((c) => c === 'delete:small')")


def test_modeller_indirme_ilerlemesi(page):
    fresh(page)
    page.evaluate(
        """() => {
          window.__models.download = { name: "tiny", label: "Whisper Tiny", state: "downloading", percent: 42, bytes: 42, total: 100, error: null };
          window.__models.items.forEach((item) => { item.downloading = item.name === "tiny"; });
        }"""
    )
    page.locator('.nav-btn[data-page="page-modeller"]').click()
    page.wait_for_function("() => document.querySelectorAll('#modelList .m-card').length === 3")
    page.wait_for_function("() => document.querySelector('#modelList .dl-bar i') !== null")
    assert "%42" in page.locator("#modelList").inner_text()
    page.evaluate("() => { window.__models.download = null; window.__models.items.forEach((item) => { item.downloading = false; }); }")


def test_ayarlar_kaydet_ve_varsayilan(page):
    fresh(page)
    page.evaluate("() => { window.__calls = []; }")
    page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    page.wait_for_function("() => document.querySelectorAll('#hotkeySelect option').length === 7")

    page.locator("#hotkeySelect").select_option("f9")
    page.locator("#historySwitch").click()
    page.wait_for_function("() => !document.querySelector('#settingsDirty').hidden")
    assert page.locator("#hotkeyNow").inner_text() == "F9"
    assert page.locator("#historySwitch").get_attribute("aria-checked") == "false"

    page.locator("#saveSettingsBtn").click()
    page.wait_for_function("() => window.__calls.some((c) => c.startsWith('settings_save:'))")
    call = page.evaluate("() => window.__calls.find((c) => c.startsWith('settings_save:'))")
    assert '"hotkey":"f9"' in call
    assert '"save_history":false' in call
    page.wait_for_function("() => document.querySelector('#settingsDirty').hidden")

    page.locator("#resetSettingsBtn").click()
    assert page.locator("#hotkeySelect").input_value() == "right_ctrl"
    assert page.locator("#historySwitch").get_attribute("aria-checked") == "true"
    page.evaluate("() => { window.__settings.save_history = true; window.__settings.hotkey = 'right_ctrl'; }")


def test_yenile_son_paragrafi_degistirir(page):
    fresh(page)
    set_snapshot(page, state="ready", seq=1, latest_text="İlk çeviri.", can_refresh=True)
    page.wait_for_function("() => document.querySelectorAll('#transcript p').length === 1")
    page.evaluate("() => { window.__calls = []; }")

    page.locator("#refreshBtn").click()
    page.wait_for_function("() => window.__calls.includes('refresh_last')")

    set_snapshot(
        page,
        state="processing",
        can_refresh=False,
    )
    page.wait_for_function("() => document.querySelector('#refreshLabel').textContent === 'Yenileniyor…'")

    set_snapshot(
        page,
        state="ready",
        seq=2,
        replace_last=True,
        latest_text="Düzeltilmiş çeviri.",
        can_refresh=True,
    )
    page.wait_for_function(
        "() => document.querySelectorAll('#transcript p').length === 1 && document.querySelector('#transcript').innerText.includes('Düzeltilmiş')"
    )
    assert "İlk çeviri." not in page.locator("#transcript").inner_text()
    assert not page.locator("#refreshBtn").is_disabled()


def test_cikti_dili_ve_otomatik_cevir(page):
    fresh(page)
    options = page.eval_on_selector_all("#outputLang option", "els => els.map((o) => o.value)")
    assert options == ["tr", "en", "de"]
    assert not page.locator("#autoTranslate").is_checked()
    assert page.locator("#cleanBtn").is_disabled()
    assert "v1.3" not in page.locator("#cleanBtn").inner_text()

    page.select_option("#outputLang", "en")
    page.wait_for_function("() => window.__ai.output_language === 'en'")

    page.locator("#autoTranslate").check()
    page.wait_for_function("() => window.__ai.auto_translate === true")


def test_temizle_cevir_akisi(page):
    fresh(page)
    page.evaluate(
        "() => { window.__ai.provider = 'openrouter';"
        " window.__snap.ai.provider = 'openrouter'; }"
    )
    set_snapshot(page, state="ready", seq=1, latest_text="Merhaba dünya bugün.")
    page.wait_for_function("() => document.querySelectorAll('#transcript p').length === 1")
    page.wait_for_function("() => !document.querySelector('#cleanBtn').disabled")

    page.locator("#cleanBtn").click()
    page.wait_for_function(
        "() => document.querySelector('#transcript').innerText.startsWith('TEMİZ:')"
    )
    assert "clean_text" in page.evaluate("() => window.__calls")

    page.locator("#translateBtn").click()
    page.wait_for_function(
        "() => document.querySelector('#transcript').innerText.startsWith('ÇEVİRİ:')"
    )
    assert "translate_text" in page.evaluate("() => window.__calls")


def test_ayarlar_yapay_zeka_karti(page):
    fresh(page)
    set_snapshot(page, state="ready")
    page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    page.wait_for_function(
        "() => document.querySelector('#page-ayarlar').classList.contains('is-active')"
    )
    page.wait_for_function("() => !document.querySelector('#textProvider').disabled")

    assert page.locator("#aiOffNote").is_visible()
    assert page.locator("#openRouterSection").is_hidden()
    assert page.locator("#localAiSection").is_hidden()

    page.select_option("#textProvider", "openrouter")
    page.wait_for_function("() => !document.querySelector('#openRouterSection').hidden")
    assert page.locator("#aiOffNote").is_hidden()
    assert "Anahtar yok" in page.locator("#orKeyState").inner_text()

    page.fill("#orKeyInput", "sk-or-v1-abcd9999")
    page.locator("#orKeySave").click()
    page.wait_for_function(
        "() => document.querySelector('#orKeyState').textContent.includes('9999')"
    )
    assert not page.locator("#orKeyDelete").is_disabled()

    page.locator("#orKeyTest").click()
    page.wait_for_function(
        "() => document.querySelector('#orKeyStatus').textContent.includes('Bağlantı')"
    )

    page.select_option("#textProvider", "local")
    page.wait_for_function("() => !document.querySelector('#localAiSection').hidden")
    assert "qwen3-4b" in page.locator("#localModelName").inner_text()


def test_ayarlar_cikti_dili_dikte_ile_senkron(page):
    fresh(page)
    set_snapshot(page, state="ready")
    page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    page.wait_for_function("() => document.querySelector('#outputLangSettings') !== null")
    page.wait_for_function("() => !document.querySelector('#outputLangSettings').disabled")
    page.select_option("#outputLangSettings", "de")
    page.wait_for_function("() => document.querySelector('#outputLang').value === 'de'")


def test_tum_openrouter_modelleri_ve_arama(page):
    fresh(page)
    set_snapshot(page, state="ready")
    page.locator('.nav-btn[data-page="page-ayarlar"]').click()
    page.wait_for_function("() => !document.querySelector('#textProvider').disabled")
    page.select_option("#textProvider", "openrouter")
    page.wait_for_function(
        "() => Array.from(document.querySelectorAll('#orModelSelect option')).length >= 2"
    )
    ids = page.eval_on_selector_all("#orModelSelect option", "els => els.map((o) => o.value)")
    assert "openai/pahali" not in ids

    page.locator("#orShowAll").check()
    page.wait_for_function(
        "() => Array.from(document.querySelectorAll('#orModelSelect option'))"
        ".some((o) => o.value === 'openai/pahali')"
    )
    assert page.evaluate("() => window.__ai.openrouter_show_all") is True

    page.fill("#orModelSearch", "pahali")
    page.wait_for_function(
        "() => document.querySelectorAll('#orModelSelect option').length === 1"
    )
    assert page.locator("#orModelSelect option").first.get_attribute("value") == "openai/pahali"
