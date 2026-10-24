/* Dikte arayüzü: Python'dan gelen anlık görüntüyü ekrana yansıtır. */
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

  const STATUS = {
    loading: "Model yükleniyor…",
    ready: "Dinlemeye hazır",
    recording: "Dinleniyor…",
    processing: "İşleniyor…",
    error: "Hata",
  };

  let api = null;
  let polling = false;
  let lastSeq = 0;
  let lastActivity = "";
  let lastError = null;
  const appended = [];

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
      shortcutHint.textContent = "Sağ Ctrl (basılı tut)";
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

  function apply(snapshot) {
    if (!snapshot) return;
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
      appendText(snapshot.latest_text);
    } else if (Number(snapshot.seq) > lastSeq) {
      lastSeq = Number(snapshot.seq);
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

  $$("[data-coming]").forEach((button) => {
    button.addEventListener("click", () => {
      toast(button.dataset.coming + " bölümü v1.1'de gelecek.", "info");
    });
  });

  $("#topLang").addEventListener("change", () => { $("#topLang").value = "Türkçe"; });
})();
