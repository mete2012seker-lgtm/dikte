/* Dikte arayüzü: Python köprüsünden gelen veriyi ekrana yansıtır. */
(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));

  const stage = $("#stage");
  const statusText = $("#statusText");
  const shortcutHint = $("#shortcutHint");
  const micBtn = $("#micBtn");
  const transcript = $("#transcript");
  const undoBtn = $("#undoBtn");
  const modelName = $("#modelName");
  const device = $("#device");
  const readyLed = $("#readyLed");
  const readyText = $("#readyText");
  const memFill = $("#memFill");
  const memText = $("#memText");
  const activityList = $("#activityList");
  const systemLed = $("#systemLed");
  const systemText = $("#systemText");
  const refreshBtn = $("#refreshBtn");
  const refreshLabel = $("#refreshLabel");

  const STATUS = {
    loading: "Model yükleniyor…",
    ready: "Dinlemeye hazır",
    recording: "Dinleniyor…",
    processing: "İşleniyor…",
    error: "Hata",
  };

  const PAGES = ["page-dikte", "page-gecmis", "page-modeller", "page-ayarlar"];
  const HISTORY_LABEL = { all: "Tümü", today: "Bugün", week: "Bu hafta" };

  let api = null;
  let polling = false;
  let lastSeq = 0;
  let lastActivity = "";
  let lastError = null;
  let currentPage = "page-dikte";
  let refreshing = false;
  let lastState = null;

  const appended = [];

  let historyQuery = "";
  let historyPeriod = "all";
  let historyTimer = null;
  let historyItems = [];
  let historyDisabled = false;

  let modelsState = null;
  let modelsTimer = null;
  let selectedModel = null;
  let modelsSignature = "";
  let lastNotifiedDownload = "";

  let settingsState = null;
  let settingsDirty = false;

  /* ---------- küçük yardımcılar ---------- */

  function toast(message, kind) {
    if (!message) return;
    const wrap = $("#toastWrap");
    const element = document.createElement("div");
    element.className = "toast";
    const dot = document.createElement("span");
    dot.className = "led";
    dot.style.background =
      kind === "error" ? "var(--error)" : kind === "warn" ? "var(--processing)" :
      kind === "info" ? "var(--listening)" : "var(--ready)";
    const text = document.createElement("span");
    text.textContent = message;
    element.append(dot, text);
    wrap.appendChild(element);
    setTimeout(() => {
      element.style.transition = "opacity .2s, transform .2s";
      element.style.opacity = "0";
      element.style.transform = "translateY(4px)";
    }, 2600);
    setTimeout(() => element.remove(), 2900);
  }

  function hasApi(name) {
    return api && typeof api[name] === "function";
  }

  function formatDuration(seconds) {
    const total = Math.max(0, Math.round(Number(seconds) || 0));
    if (total >= 60) {
      const minutes = Math.floor(total / 60);
      const rest = String(total % 60).padStart(2, "0");
      return minutes + " dk " + rest + " sn";
    }
    return total + " sn";
  }

  function formatDate(iso) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return iso || "";
    try {
      return new Intl.DateTimeFormat("tr-TR", {
        day: "numeric", month: "long", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      }).format(date);
    } catch (error) {
      return date.toLocaleString();
    }
  }

  function buildWave(element, count, towardRight) {
    element.innerHTML = "";
    for (let i = 0; i < count; i++) {
      const t = i / (count - 1);
      const envelope = Math.pow(towardRight ? t : 1 - t, 1.5);
      const height = Math.round(6 + envelope * 52 + Math.random() * 8);
      const bar = document.createElement("span");
      bar.style.height = height + "px";
      bar.style.animationDelay = (-Math.random() * 3).toFixed(2) + "s";
      bar.style.animationDuration = (2.6 + Math.random() * 1.4).toFixed(2) + "s";
      element.appendChild(bar);
    }
  }
  buildWave($("#waveLeft"), 26, true);
  buildWave($("#waveRight"), 26, false);

  /* ---------- sayfa yönlendirici ---------- */

  function showPage(pageId) {
    if (!PAGES.includes(pageId)) pageId = "page-dikte";
    currentPage = pageId;
    PAGES.forEach((id) => {
      const section = document.getElementById(id);
      if (section) section.classList.toggle("is-active", id === pageId);
    });
    $$(".nav-btn").forEach((button) => {
      const active = button.dataset.page === pageId;
      button.classList.toggle("is-active", active);
      if (active) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });

    if (pageId === "page-gecmis") loadHistory();
    if (pageId === "page-modeller") {
      loadModels();
      startModelsPolling();
    } else {
      stopModelsPolling();
    }
    if (pageId === "page-ayarlar") loadSettings();
  }

  $$(".nav-btn").forEach((button) => {
    button.addEventListener("click", () => showPage(button.dataset.page));
  });

  /* ---------- durum ---------- */

  function applyState(state) {
    stage.classList.toggle("is-listening", state === "recording");
    stage.classList.toggle("is-processing", state === "processing");
    stage.classList.toggle("is-loading", state === "loading");
    stage.classList.toggle("is-error", state === "error");

    micBtn.setAttribute("aria-pressed", state === "recording" ? "true" : "false");
    micBtn.setAttribute("aria-label",
      state === "recording" ? "Kaydı bitir" :
      state === "loading" ? "Model yükleniyor" : "Kaydı başlat");

    if (state === "recording") {
      shortcutHint.textContent = "Durdurmak için tekrar tıkla";
    } else if (state === "loading") {
      shortcutHint.textContent = "Model yükleniyor, lütfen bekle";
    } else if (state === "processing") {
      shortcutHint.textContent = "İşleniyor, lütfen bekle";
    } else if (state === "error") {
      shortcutHint.textContent = "Tekrar denemek için mikrofon düğmesine bas";
    } else {
      shortcutHint.textContent = (window.__hotkeyLabel || "Sağ Ctrl") + " (basılı tut)";
    }
    if (state !== lastState) {
      lastState = state;
      applySettingsAvailability(state);
    }
  }

  function applyModel(snapshot) {
    modelName.textContent = snapshot.model || (snapshot.state === "error" ? "Model yok" : "Model yükleniyor…");
    device.textContent = snapshot.device || "—";

    const state = snapshot.state;
    const isReady = state === "ready" || state === "recording" || state === "processing";
    readyText.textContent = isReady ? "Evet" : state === "loading" ? "Yükleniyor" : "Hayır";
    readyLed.style.background = isReady ? "var(--ready)" : state === "loading" ? "var(--processing)" : "var(--error)";
    readyLed.style.boxShadow = isReady
      ? "0 0 8px rgba(46,212,122,.8)"
      : state === "loading" ? "0 0 8px rgba(242,178,62,.7)" : "0 0 8px rgba(239,91,91,.7)";

    const memory = snapshot.memory;
    if (memory && typeof memory.used === "number" && typeof memory.total === "number") {
      const percent = Math.max(0, Math.min(100, Number(memory.percent) || (memory.used / memory.total) * 100));
      memFill.style.width = percent + "%";
      memText.textContent = memory.used + " " + memory.unit + " / " + memory.total + " " + memory.unit;
      memText.title = memory.source === "RAM" ? "Sistem belleği (RAM)" : "Ekran kartı belleği (VRAM)";
    } else {
      memFill.style.width = "0%";
      memText.textContent = "—";
    }

    if (state === "error") {
      systemLed.style.background = "var(--error)";
      systemLed.style.boxShadow = "0 0 8px rgba(239,91,91,.8)";
      systemText.textContent = "Kurulum gerekli";
    } else if (state === "loading") {
      systemLed.style.background = "var(--processing)";
      systemLed.style.boxShadow = "0 0 8px rgba(242,178,62,.7)";
      systemText.textContent = "Model yükleniyor";
    } else {
      systemLed.style.background = "var(--ready)";
      systemLed.style.boxShadow = "0 0 8px rgba(46,212,122,.8)";
      systemText.textContent = "Yerel sistem hazır";
    }
  }

  function renderActivity(items) {
    const key = JSON.stringify(items);
    if (key === lastActivity) return;
    lastActivity = key;
    activityList.innerHTML = "";
    if (!items || !items.length) {
      const empty = document.createElement("div");
      empty.className = "activity-empty";
      empty.textContent = "Henüz etkinlik yok.";
      activityList.appendChild(empty);
      return;
    }
    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "tl-item";
      const dot = document.createElement("span");
      dot.className = "tl-dot " + (item.kind === "ok" ? "ok" : item.kind === "warn" ? "warn" : item.kind === "err" ? "err" : "");
      const line = document.createElement("div");
      line.className = "tl-line";
      const time = document.createElement("span");
      time.className = "tl-time";
      time.textContent = item.time || "";
      const title = document.createElement("span");
      title.className = "tl-title";
      title.textContent = item.title || "";
      line.append(time, title);
      const sub = document.createElement("div");
      sub.className = "tl-sub";
      sub.textContent = item.sub || "";
      row.append(dot, line, sub);
      activityList.appendChild(row);
    });
  }

  function appendText(text) {
    if (!text) return;
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    transcript.appendChild(paragraph);
    appended.push(paragraph);
    undoBtn.disabled = false;
    transcript.scrollTop = transcript.scrollHeight;
  }

  function replaceLastText(text) {
    if (!text) return;
    const paragraphs = transcript.querySelectorAll("p");
    const last = paragraphs[paragraphs.length - 1];
    if (!last) {
      appendText(text);
      return;
    }
    last.textContent = text;
    transcript.scrollTop = transcript.scrollHeight;
  }

  function apply(snapshot) {
    if (!snapshot) return;
    window.__hotkeyLabel = snapshot.hotkey || "Sağ Ctrl";
    applyState(snapshot.state);
    statusText.textContent = snapshot.error && snapshot.state === "error"
      ? snapshot.error
      : STATUS[snapshot.state] || STATUS.ready;
    statusText.title = snapshot.error || statusText.textContent;
    statusText.style.color = snapshot.state === "error" ? "var(--error)" : "var(--text)";

    applyModel(snapshot);
    renderActivity(snapshot.activity || []);

    if (Number(snapshot.seq) > lastSeq && snapshot.latest_text) {
      lastSeq = Number(snapshot.seq);
      if (snapshot.replace_last) replaceLastText(snapshot.latest_text);
      else appendText(snapshot.latest_text);
      if (currentPage === "page-gecmis") loadHistory();
    } else if (Number(snapshot.seq) > lastSeq) {
      lastSeq = Number(snapshot.seq);
    }

    if (!refreshing) {
      refreshBtn.disabled = !snapshot.can_refresh;
      refreshLabel.textContent = "Transkripsiyonu Yenile";
    } else if (snapshot.state === "ready" || snapshot.state === "error") {
      refreshing = false;
      refreshBtn.disabled = !snapshot.can_refresh;
      refreshLabel.textContent = "Transkripsiyonu Yenile";
    }

    if (snapshot.state === "error" && snapshot.error && snapshot.error !== lastError) {
      lastError = snapshot.error;
      toast(snapshot.error, "error");
    }
    if (snapshot.state !== "error") lastError = null;
  }

  /* ---------- Python köprüsü ---------- */

  async function pollOnce() {
    if (!polling) return;
    try {
      const snapshot = await api.snapshot();
      apply(snapshot);
    } catch (error) {
      console.error("Durum okunamadı:", error);
    }
    if (polling) setTimeout(pollOnce, 250);
  }

  function startPolling() {
    if (polling || !window.pywebview || !window.pywebview.api) return;
    api = window.pywebview.api;
    polling = true;
    pollOnce();
  }

  window.addEventListener("pywebviewready", startPolling);
  if (window.pywebview && window.pywebview.api) startPolling();

  /* ---------- geçmiş ---------- */

  function renderHistory() {
    const list = $("#historyList");
    const count = $("#historyCount");
    if (!list) return;

    if (historyDisabled) {
      $("#historyCard").hidden = true;
      $("#historyDisabled").hidden = false;
      return;
    }
    $("#historyCard").hidden = false;
    $("#historyDisabled").hidden = true;

    count.textContent = historyItems.length + " kayıt";
    list.innerHTML = "";
    if (!historyItems.length) {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = historyQuery
        ? "Aramanla eşleşen kayıt yok."
        : "Henüz kayıt yok. İlk dikteni yap, burada görünsün.";
      list.appendChild(empty);
      return;
    }

    historyItems.forEach((item) => {
      const row = document.createElement("div");
      row.className = "h-item";
      row.dataset.id = item.id;

      const icon = document.createElement("div");
      icon.className = "h-ico";
      icon.innerHTML = '<svg class="ic"><use href="#i-clock"/></svg>';

      const main = document.createElement("div");
      const top = document.createElement("div");
      top.className = "h-top";
      const date = document.createElement("span");
      date.className = "h-date";
      date.textContent = formatDate(item.created_at);
      const meta = document.createElement("span");
      meta.className = "h-meta";
      meta.textContent = formatDuration(item.duration) + " · " + item.words + " kelime";
      top.append(date, meta);
      const preview = document.createElement("div");
      preview.className = "h-preview";
      preview.textContent = item.text;
      preview.title = item.text;
      main.append(top, preview);

      const actions = document.createElement("div");
      actions.className = "h-actions";
      const openBtn = document.createElement("button");
      openBtn.className = "btn";
      openBtn.textContent = "Aç";
      openBtn.addEventListener("click", () => openHistory(item.id));
      const copyBtn = document.createElement("button");
      copyBtn.className = "btn";
      copyBtn.textContent = "Kopyala";
      copyBtn.addEventListener("click", () => copyHistory(item.text));
      const deleteBtn = document.createElement("button");
      deleteBtn.className = "btn btn-danger";
      deleteBtn.textContent = "Sil";
      deleteBtn.addEventListener("click", () => deleteHistory(item.id, row));
      actions.append(openBtn, copyBtn, deleteBtn);

      row.append(icon, main, actions);
      list.appendChild(row);
    });
  }

  async function loadHistory() {
    if (!hasApi("history_list")) return;
    try {
      const result = await api.history_list(historyQuery, historyPeriod);
      historyDisabled = Boolean(result && result.disabled);
      historyItems = (result && result.items) || [];
      renderHistory();
    } catch (error) {
      console.error("Geçmiş okunamadı:", error);
      toast("Geçmiş okunamadı.", "error");
    }
  }

  async function openHistory(id) {
    if (!hasApi("history_open")) return;
    try {
      const result = await api.history_open(id);
      if (!result || !result.ok) {
        toast((result && result.message) || "Kayıt açılamadı.", "warn");
        return;
      }
      showPage("page-dikte");
      toast("Kayıt Dikte ekranına eklendi.");
    } catch (error) {
      toast("Kayıt açılamadı.", "error");
    }
  }

  async function copyHistory(text) {
    if (!hasApi("copy")) return;
    try {
      const result = await api.copy(text);
      toast(result && result.ok ? "Metin panoya kopyalandı." : (result && result.message) || "Kopyalanamadı.",
        result && result.ok ? "info" : "error");
    } catch (error) {
      toast("Kopyalanamadı.", "error");
    }
  }

  async function deleteHistory(id, row) {
    if (!hasApi("history_delete")) return;
    row.classList.add("removing");
    window.setTimeout(async () => {
      try {
        const result = await api.history_delete(id);
        if (result && result.ok) {
          toast("Kayıt silindi.");
          loadHistory();
        } else {
          row.classList.remove("removing");
          toast((result && result.message) || "Kayıt silinemedi.", "warn");
        }
      } catch (error) {
        row.classList.remove("removing");
        toast("Kayıt silinemedi.", "error");
      }
    }, 200);
  }

  $("#historySearch").addEventListener("input", (event) => {
    historyQuery = event.target.value;
    window.clearTimeout(historyTimer);
    historyTimer = window.setTimeout(loadHistory, 250);
  });

  $$("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      $$("[data-filter]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      historyPeriod = button.dataset.filter;
      loadHistory();
    });
  });

  $("#goSettingsBtn").addEventListener("click", () => showPage("page-ayarlar"));

  /* ---------- modeller ---------- */

  function modelStatus(item) {
    if (item.active) return { text: "Aktif", cls: "" };
    if (item.downloading) return { text: "İndiriliyor", cls: "busy" };
    if (item.installed) return { text: "İndirildi", cls: "" };
    if (item.partial) return { text: "Yarım indirme", cls: "busy" };
    return { text: "İndirilmedi", cls: "muted" };
  }

  function renderModels() {
    const list = $("#modelList");
    if (!list) return;
    const items = (modelsState && modelsState.items) || [];
    $("#modelCount").textContent = items.length + " model";

    const query = ($("#modelSearch").value || "").toLocaleLowerCase("tr");
    const visible = items.filter((item) =>
      !query || (item.label + " " + item.desc).toLocaleLowerCase("tr").includes(query)
    );

    if (!selectedModel || !items.some((item) => item.name === selectedModel)) {
      const active = items.find((item) => item.active);
      selectedModel = (active || items[0] || {}).name || null;
    }

    list.innerHTML = "";
    if (!visible.length) {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "Aramanla eşleşen model yok.";
      list.appendChild(empty);
      renderDetail();
      return;
    }

    const download = modelsState && modelsState.download;

    visible.forEach((item) => {
      const card = document.createElement("div");
      card.className = "m-card" + (item.name === selectedModel ? " is-selected" : "");
      card.dataset.name = item.name;

      const icon = document.createElement("div");
      icon.className = "m-ico";
      icon.innerHTML = '<svg class="ic"><use href="#i-mic"/></svg>';

      const main = document.createElement("div");
      main.className = "m-main";
      const name = document.createElement("div");
      name.className = "m-name";
      name.textContent = item.label;
      const desc = document.createElement("div");
      desc.className = "m-desc";
      desc.textContent = item.desc;
      const tags = document.createElement("div");
      tags.className = "m-tags";
      (item.tags || []).slice(0, 3).forEach((tag) => {
        const span = document.createElement("span");
        span.className = "tag";
        span.textContent = tag;
        tags.appendChild(span);
      });
      main.append(name, desc, tags);

      if (item.downloading && download && download.name === item.name) {
        const wrap = document.createElement("div");
        wrap.className = "dl-wrap";
        const bar = document.createElement("div");
        bar.className = "dl-bar";
        const fill = document.createElement("i");
        fill.style.width = Math.max(1, download.percent || 0) + "%";
        bar.appendChild(fill);
        const text = document.createElement("span");
        text.className = "dl-text";
        text.textContent = "%" + (download.percent || 0);
        wrap.append(bar, text);
        main.appendChild(wrap);
      }

      const size = document.createElement("div");
      size.className = "m-size";
      size.textContent = item.installed ? item.size_label : item.approx_label;
      const quant = document.createElement("small");
      quant.textContent = item.installed ? "diskte" : "indirme";
      size.appendChild(quant);

      const status = modelStatus(item);
      const statusBox = document.createElement("div");
      statusBox.className = "m-status " + status.cls;
      const dot = document.createElement("span");
      dot.className = "dot";
      statusBox.append(dot, document.createTextNode(status.text));

      const actions = document.createElement("div");
      actions.className = "m-actions";

      const action = document.createElement("button");
      action.className = "m-btn";
      if (item.active) {
        action.classList.add("is-active");
        action.textContent = "Aktif";
        action.disabled = true;
      } else if (item.downloading) {
        action.textContent = "İndiriliyor";
        action.disabled = true;
      } else if (item.installed) {
        action.classList.add("primary");
        action.textContent = "Aktifleştir";
        action.addEventListener("click", (event) => {
          event.stopPropagation();
          activateModel(item.name);
        });
      } else {
        action.textContent = "İndir";
        action.addEventListener("click", (event) => {
          event.stopPropagation();
          downloadModel(item.name);
        });
      }
      actions.appendChild(action);

      if (item.installed || item.partial) {
        const remove = document.createElement("button");
        remove.className = "icon-btn";
        remove.title = "Modeli sil";
        remove.setAttribute("aria-label", "Modeli sil");
        remove.innerHTML = '<svg class="ic" style="width:15px;height:15px"><use href="#i-trash"/></svg>';
        remove.disabled = item.active || item.downloading;
        remove.addEventListener("click", (event) => {
          event.stopPropagation();
          deleteModel(item.name, item.label);
        });
        actions.appendChild(remove);
      }

      card.append(icon, main, size, statusBox, actions);
      card.addEventListener("click", () => {
        selectedModel = item.name;
        renderModels();
        renderDetail();
      });
      list.appendChild(card);
    });

    renderDetail();
  }

  function renderDetail() {
    const panel = $("#detailPanel");
    const descPanel = $("#descPanel");
    if (!panel || !descPanel || !modelsState) return;
    const items = modelsState.items || [];
    const item = items.find((entry) => entry.name === selectedModel) || items[0];
    if (!item) {
      panel.innerHTML = '<div class="empty">Model bulunamadı.</div>';
      descPanel.innerHTML = "";
      return;
    }

    const status = modelStatus(item);
    panel.innerHTML =
      '<div class="detail-head"><svg class="ic"><use href="#i-models"/></svg>Model Detayları' +
        '<button class="icon-btn x" id="closeDetail" aria-label="Paneli kapat"><svg class="ic" style="width:15px;height:15px"><use href="#i-close"/></svg></button></div>' +
      '<div class="detail-model"><div class="m-ico"><svg class="ic"><use href="#i-mic"/></svg></div>' +
        '<div><div class="model-name" id="detailName"></div><div class="model-sub">Konuşma tanıma modeli</div></div></div>' +
      '<div class="d-row">Kategori<span>Konuşma Tanıma</span></div>' +
      '<div class="d-row">Boyut<span id="detailSize"></span></div>' +
      '<div class="d-row">Dil Desteği<span>Türkçe ve çoklu dil</span></div>' +
      '<div class="d-row">Cihaz Desteği<span>GPU / CPU</span></div>' +
      '<div class="divider"></div>' +
      '<div class="d-row">Model Durumu<span id="detailStatus"></span></div>' +
      '<div class="d-actions"><button class="btn btn-primary" id="detailAction"></button></div>' +
      '<div class="d-actions"><button class="btn btn-danger" id="detailDelete"><svg class="ic"><use href="#i-trash"/></svg>Sil</button></div>';

    panel.querySelector("#detailName").textContent = item.label;
    panel.querySelector("#detailSize").textContent =
      (item.installed ? item.size_label + " (diskte)" : item.approx_label + " (indirme)");
    const statusSpan = panel.querySelector("#detailStatus");
    const led = document.createElement("span");
    led.className = "led";
    led.style.background = item.active ? "var(--ready)" : item.installed ? "var(--ready)" : "#5C6A85";
    led.style.boxShadow = item.active || item.installed ? "0 0 7px rgba(46,212,122,.7)" : "none";
    statusSpan.append(led, document.createTextNode(status.text));

    const action = panel.querySelector("#detailAction");
    if (item.active) {
      action.textContent = "Aktif Model";
      action.disabled = true;
    } else if (item.downloading) {
      action.textContent = "İndiriliyor…";
      action.disabled = true;
    } else if (item.installed) {
      action.innerHTML = '<svg class="ic"><use href="#i-check"/></svg>Aktifleştir';
      action.addEventListener("click", () => activateModel(item.name));
    } else {
      action.innerHTML = '<svg class="ic"><use href="#i-download"/></svg>İndir';
      action.addEventListener("click", () => downloadModel(item.name));
    }

    const remove = panel.querySelector("#detailDelete");
    remove.disabled = item.active || item.downloading || (!item.installed && !item.partial);
    remove.addEventListener("click", () => deleteModel(item.name, item.label));

    panel.querySelector("#closeDetail").addEventListener("click", () => {
      panel.style.display = "none";
    });
    panel.style.display = "";

    descPanel.innerHTML =
      '<h3><svg class="ic"><use href="#i-bulb"/></svg>Model Açıklaması</h3>' +
      '<p id="descText"></p><ul class="desc-list" id="descList"></ul>';
    descPanel.querySelector("#descText").textContent = item.desc;
    const list = descPanel.querySelector("#descList");
    (item.tags || []).forEach((tag) => {
      const li = document.createElement("li");
      li.innerHTML = '<svg class="ic"><use href="#i-check"/></svg><span></span>';
      li.querySelector("span").textContent = tag;
      list.appendChild(li);
    });
  }

  async function loadModels() {
    if (!hasApi("models_list")) return;
    try {
      const result = await api.models_list();
      modelsState = result || null;
      const signature = JSON.stringify({
        items: (result.items || []).map((item) => [item.name, item.active, item.installed, item.partial, item.size_bytes]),
        download: result.download ? [result.download.name, result.download.state, result.download.percent] : null,
      });
      if (signature !== modelsSignature) {
        modelsSignature = signature;
        renderModels();
      }
      handleDownloadNotice(result.download);
    } catch (error) {
      console.error("Modeller okunamadı:", error);
    }
  }

  function handleDownloadNotice(download) {
    if (!download) return;
    if (download.state === "done" && lastNotifiedDownload !== download.name + ":done") {
      lastNotifiedDownload = download.name + ":done";
      toast(download.label + " indirildi.", "info");
      loadModels();
    } else if (download.state === "error" && lastNotifiedDownload !== download.name + ":error") {
      lastNotifiedDownload = download.name + ":error";
      toast(download.error || "Model indirilemedi.", "error");
    }
  }

  function startModelsPolling() {
    stopModelsPolling();
    modelsTimer = window.setInterval(() => {
      if (currentPage === "page-modeller") loadModels();
    }, 700);
  }

  function stopModelsPolling() {
    if (modelsTimer) {
      window.clearInterval(modelsTimer);
      modelsTimer = null;
    }
  }

  async function downloadModel(name) {
    if (!hasApi("model_download")) return;
    lastNotifiedDownload = "";
    try {
      const result = await api.model_download(name);
      toast((result && result.message) || (result && result.ok ? "İndirme başladı." : "İndirme başlatılamadı."),
        result && result.ok ? "info" : "warn");
      loadModels();
    } catch (error) {
      toast("İndirme başlatılamadı.", "error");
    }
  }

  async function activateModel(name) {
    if (!hasApi("model_activate")) return;
    try {
      const result = await api.model_activate(name);
      toast((result && result.message) || (result && result.ok ? "Model yükleniyor…" : "Model değiştirilemedi."),
        result && result.ok ? "info" : "warn");
      loadModels();
    } catch (error) {
      toast("Model değiştirilemedi.", "error");
    }
  }

  async function deleteModel(name, label) {
    if (!hasApi("model_delete")) return;
    if (!window.confirm(label + " modeli diskten silinsin mi?")) return;
    try {
      const result = await api.model_delete(name);
      toast((result && result.message) || (result && result.ok ? "Model silindi." : "Model silinemedi."),
        result && result.ok ? "info" : "warn");
      loadModels();
    } catch (error) {
      toast("Model silinemedi.", "error");
    }
  }

  $("#modelSearch").addEventListener("input", renderModels);

  /* ---------- ayarlar ---------- */

  function markDirty() {
    settingsDirty = true;
    $("#settingsDirty").hidden = false;
  }

  function setSwitch(on) {
    const button = $("#historySwitch");
    button.classList.toggle("on", Boolean(on));
    button.setAttribute("aria-checked", on ? "true" : "false");
  }

  function switchOn() {
    return $("#historySwitch").classList.contains("on");
  }

  function updateHotkeyPreview() {
    const select = $("#hotkeySelect");
    const option = select.options[select.selectedIndex];
    $("#hotkeyNow").textContent = option ? option.textContent : "—";
  }

  function applySettingsAvailability(state) {
    const busy = state === "recording" || state === "processing" || state === "loading";
    const save = $("#saveSettingsBtn");
    const select = $("#hotkeySelect");
    const sw = $("#historySwitch");
    if (save) save.disabled = busy;
    if (select) select.disabled = busy;
    if (sw) sw.disabled = busy;
  }

  async function loadSettings() {
    if (!hasApi("settings_get")) return;
    try {
      const data = await api.settings_get();
      settingsState = data;
      const select = $("#hotkeySelect");
      select.innerHTML = "";
      (data.choices || []).forEach((choice) => {
        const option = document.createElement("option");
        option.value = choice.id;
        option.textContent = choice.label;
        select.appendChild(option);
      });
      select.value = data.hotkey;
      setSwitch(data.save_history);
      updateHotkeyPreview();
      settingsDirty = false;
      $("#settingsDirty").hidden = true;
      applySettingsAvailability(data.state);
    } catch (error) {
      console.error("Ayarlar okunamadı:", error);
      toast("Ayarlar okunamadı.", "error");
    }
  }

  $("#hotkeySelect").addEventListener("change", () => {
    updateHotkeyPreview();
    markDirty();
  });

  $("#historySwitch").addEventListener("click", () => {
    setSwitch(!switchOn());
    markDirty();
  });

  $("#saveSettingsBtn").addEventListener("click", async () => {
    if (!hasApi("settings_save")) return;
    const payload = {
      hotkey: $("#hotkeySelect").value,
      save_history: switchOn(),
    };
    try {
      const result = await api.settings_save(payload);
      if (result && result.ok) {
        settingsDirty = false;
        $("#settingsDirty").hidden = true;
        settingsState = result.settings || settingsState;
        toast(result.message || "Ayarlar kaydedildi.");
        if (currentPage === "page-gecmis") loadHistory();
      } else {
        toast((result && result.message) || "Ayarlar kaydedilemedi.", "warn");
      }
    } catch (error) {
      toast("Ayarlar kaydedilemedi.", "error");
    }
  });

  $("#resetSettingsBtn").addEventListener("click", () => {
    $("#hotkeySelect").value = "right_ctrl";
    setSwitch(true);
    updateHotkeyPreview();
    markDirty();
    toast("Varsayılanlar seçildi. Uygulamak için Kaydet'e bas.", "info");
  });

  $("#clearHistoryBtn").addEventListener("click", async () => {
    if (!hasApi("history_clear")) return;
    if (!window.confirm("Kaydedilmiş tüm dikte metinleri silinsin mi? Bu işlem geri alınamaz.")) return;
    try {
      const result = await api.history_clear();
      toast(result && result.ok ? "Geçmiş temizlendi." : ((result && result.message) || "Geçmiş temizlenemedi."),
        result && result.ok ? "info" : "warn");
      if (currentPage === "page-gecmis") loadHistory();
    } catch (error) {
      toast("Geçmiş temizlenemedi.", "error");
    }
  });

  /* ---------- eylemler ---------- */

  micBtn.addEventListener("click", async () => {
    if (!api) { toast("Uygulama bağlantısı hazır değil.", "info"); return; }
    try {
      const result = await api.toggle_record();
      if (result && result.message) toast(result.message, result.ok ? "info" : "warn");
    } catch (error) {
      toast("Mikrofon işlemi başlatılamadı.", "error");
    }
  });

  $("#copyBtn").addEventListener("click", async () => {
    const text = transcript.innerText.replace(/\u00a0/g, " ").trim();
    if (!text) { toast("Kopyalanacak metin yok.", "info"); return; }
    if (!api) { toast("Uygulama bağlantısı hazır değil.", "info"); return; }
    try {
      const result = await api.copy(text);
      if (result && result.ok) {
        const label = $("#copyLabel");
        label.textContent = "Kopyalandı";
        toast("Metin panoya kopyalandı.");
        setTimeout(() => { label.textContent = "Kopyala"; }, 1600);
      } else {
        toast((result && result.message) || "Metin panoya kopyalanamadı.", "error");
      }
    } catch (error) {
      toast("Metin panoya kopyalanamadı.", "error");
    }
  });

  undoBtn.addEventListener("click", () => {
    while (appended.length) {
      const paragraph = appended.pop();
      if (paragraph && paragraph.isConnected) {
        paragraph.remove();
        toast("Son dikte geri alındı.");
        if (!appended.length) undoBtn.disabled = true;
        return;
      }
    }
    undoBtn.disabled = true;
    toast("Geri alınacak dikte yok.", "info");
  });

  refreshBtn.addEventListener("click", async () => {
    if (!hasApi("refresh_last")) return;
    if (!api) { toast("Uygulama bağlantısı hazır değil.", "info"); return; }
    refreshing = true;
    refreshBtn.disabled = true;
    refreshLabel.textContent = "Yenileniyor…";
    try {
      const result = await api.refresh_last();
      if (!result || !result.ok) {
        refreshing = false;
        refreshLabel.textContent = "Transkripsiyonu Yenile";
        toast((result && result.message) || "Yenilenemedi.", "warn");
      }
    } catch (error) {
      refreshing = false;
      refreshLabel.textContent = "Transkripsiyonu Yenile";
      toast("Yenilenemedi.", "error");
    }
  });

  $$("[data-coming]").forEach((button) => {
    button.addEventListener("click", () => {
      toast(button.dataset.coming || "Bu bölüm sonraki sürümde gelecek.", "info");
    });
  });

  $("#topLang").addEventListener("change", () => { $("#topLang").value = "Türkçe"; });

  showPage("page-dikte");
})();
