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
  const outputLang = $("#outputLang");
  const autoTranslate = $("#autoTranslate");
  const cleanBtn = $("#cleanBtn");
  const translateBtn = $("#translateBtn");
  const textModelRow = $("#textModelRow");

  const STATUS = {
    loading: "Model yükleniyor…",
    ready: "Dinlemeye hazır",
    recording: "Dinleniyor…",
    processing: "İşleniyor…",
    cleaning: "Metin düzenleniyor…",
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
  let selectedTextModel = null;
  let modelsSignature = "";
  let lastNotifiedDownload = "";
  let modelTab = "text";

  let settingsState = null;
  let settingsDirty = false;
  let aiState = null;
  let aiBusy = false;
  let aiSaveInFlight = 0;
  let lastAiSaveTime = 0;

  /* ---------- Faz 3.1 & 3.2: Yan Menü Daraltma ---------- */
  const brandToggle = $("#brandToggle");
  function toggleSidebar(collapsed, persist) {
    const isCollapsed = collapsed !== undefined
      ? Boolean(collapsed)
      : !document.body.classList.contains("sidebar-collapsed");
    document.body.classList.toggle("sidebar-collapsed", isCollapsed);
    if (persist && hasApi("settings_save")) {
      api.settings_save({ sidebar_collapsed: isCollapsed }).catch(() => {});
    }
  }
  const sidebarCollapseBtn = $("#sidebarCollapseBtn");
  if (brandToggle) {
    brandToggle.addEventListener("click", () => toggleSidebar(undefined, true));
  }
  if (sidebarCollapseBtn) {
    sidebarCollapseBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSidebar(undefined, true);
    });
  }

  /* ---------- Faz 3.4: Tasarım Dili (dikte_ai / classic) ---------- */
  let designStyle = "dikte_ai";
  try {
    designStyle = localStorage.getItem("design_style") || document.documentElement.getAttribute("data-design") || "dikte_ai";
  } catch (e) {
    designStyle = document.documentElement.getAttribute("data-design") || "dikte_ai";
  }

  function setDesignStyle(style, persist) {
    designStyle = (style === "classic") ? "classic" : "dikte_ai";
    try { localStorage.setItem("design_style", designStyle); } catch (e) {}
    document.documentElement.setAttribute("data-design", designStyle);
    document.body.classList.toggle("design-dikte-ai", designStyle === "dikte_ai");
    document.body.classList.toggle("design-classic", designStyle === "classic");
    $$("#designStyleGroup [data-design-choice]").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.designChoice === designStyle);
    });
    if (persist) {
      if (hasApi("ai_settings_save")) {
        api.ai_settings_save({ design_style: designStyle }).catch(() => {});
      }
      if (hasApi("settings_save")) {
        api.settings_save({ design_style: designStyle }).catch(() => {});
      }
    }
  }
  window.setDesignStyle = setDesignStyle;
  $$("#designStyleGroup [data-design-choice]").forEach((btn) => {
    btn.addEventListener("click", () => setDesignStyle(btn.dataset.designChoice, true));
  });
  setDesignStyle(designStyle, false);

  /* ---------- Faz 3.4: Mikrofon Morfizmi & Canvas Ses Dalgaları (design/mikrofon_morph_animasyonu.html birebir) ---------- */
  const waveCanvas = $("#waveCanvas");
  let waveCtx = waveCanvas ? waveCanvas.getContext("2d") : null;
  let isRecordingState = false;
  let morphValue = 0; // current eased 0..1
  let morphFrom = 0;
  let morphTo = 0;
  let morphStartTime = 0;
  const MORPH_DURATION_MS = 850;

  const BARS_PER_SIDE = 24;
  const TOTAL_BARS = BARS_PER_SIDE * 2;

  const leftProfile = [
    0.07, 0.08, 0.08, 0.11, 0.15, 0.12, 0.20, 0.25,
    0.18, 0.30, 0.38, 0.44, 0.32, 0.56, 0.68, 0.50,
    0.74, 0.88, 0.62, 0.94, 0.82, 0.72, 0.58, 0.48
  ];
  const rightProfile = [
    0.52, 0.64, 0.78, 0.88, 0.95, 0.68, 0.82, 0.72,
    0.54, 0.62, 0.44, 0.36, 0.48, 0.34, 0.26, 0.22,
    0.28, 0.18, 0.14, 0.12, 0.09, 0.08, 0.08, 0.06
  ];
  const idleHeights = [...leftProfile, ...rightProfile];
  const currentHeights = idleHeights.map((h) => h * 64);

  function resizeWaveCanvas() {
    if (!waveCanvas || !stage) return;
    const rect = stage.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    waveCanvas.width = rect.width * dpr;
    waveCanvas.height = rect.height * dpr;
    if (waveCtx) waveCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener("resize", resizeWaveCanvas);
  if (typeof ResizeObserver !== "undefined" && stage) {
    const ro = new ResizeObserver(() => resizeWaveCanvas());
    ro.observe(stage);
  }
  setTimeout(resizeWaveCanvas, 50);

  // Exact cubic-bezier(0.22, 1, 0.36, 1) matching CSS --morph-ease
  function sampleCurveX(t, x1, x2) {
    return ((1 - 3 * x2 + 3 * x1) * t * t * t) + ((3 * x2 - 6 * x1) * t * t) + (3 * x1 * t);
  }
  function sampleCurveY(t, y1, y2) {
    return ((1 - 3 * y2 + 3 * y1) * t * t * t) + ((3 * y2 - 6 * y1) * t * t) + (3 * y1 * t);
  }
  function sampleCurveDerivativeX(t, x1, x2) {
    return (3 * (1 - 3 * x2 + 3 * x1) * t * t) + (2 * (3 * x2 - 6 * x1) * t) + (3 * x1);
  }
  function easeMorph(x) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    const x1 = 0.22, y1 = 1, x2 = 0.36, y2 = 1;
    let t = x;
    for (let i = 0; i < 6; i++) {
      const err = sampleCurveX(t, x1, x2) - x;
      const d = sampleCurveDerivativeX(t, x1, x2);
      if (Math.abs(err) < 1e-5 || Math.abs(d) < 1e-6) break;
      t -= err / d;
    }
    return sampleCurveY(Math.max(0, Math.min(1, t)), y1, y2);
  }
  function lerp(a, b, t) { return a + (b - a) * t; }

  function drawRoundedBar(ctx, x, centerY, width, height, alpha, glowStrength) {
    const radius = width / 2;
    const top = centerY - height / 2;

    const grad = ctx.createLinearGradient(0, top, 0, top + height);
    grad.addColorStop(0, `rgba(74, 108, 247, ${0.75 * alpha})`);
    grad.addColorStop(0.5, `rgba(116, 152, 255, ${1 * alpha})`);
    grad.addColorStop(1, `rgba(59, 89, 212, ${0.75 * alpha})`);

    ctx.save();
    ctx.fillStyle = grad;
    ctx.shadowColor = `rgba(88, 130, 255, ${0.55 * glowStrength})`;
    ctx.shadowBlur = 10 * glowStrength;

    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(x - width / 2, top, width, height, radius);
    } else {
      ctx.rect(x - width / 2, top, width, height);
    }
    ctx.fill();
    ctx.restore();
  }

  function renderWaveAnim(now) {
    if (waveCtx && waveCanvas && stage) {
      if (morphValue !== morphTo) {
        const elapsed = Math.max(0, now - morphStartTime);
        const rawT = Math.min(1, elapsed / MORPH_DURATION_MS);
        const easedT = easeMorph(rawT);
        morphValue = lerp(morphFrom, morphTo, easedT);
        if (rawT >= 1) morphValue = morphTo;
      }

      const m = morphValue;
      const w = stage.clientWidth;
      const h = stage.clientHeight;
      if (w > 0 && h > 0) {
        const centerX = w / 2;
        const centerY = h * 0.43;
        const scale = Math.min(1, w / 860);

        waveCtx.clearRect(0, 0, w, h);

        const timeSec = now * 0.001;
        const barWidth = lerp(3.6, 4.2, m) * Math.max(0.72, scale);

        const idleStep = 9.8 * scale;
        const idleInnerGap = 132 * scale;

        const activeStep = 9.4 * scale;
        const activeStartX = centerX - ((TOTAL_BARS - 1) * activeStep) / 2;

        for (let i = 0; i < TOTAL_BARS; i++) {
          const isLeft = i < BARS_PER_SIDE;

          let idleX;
          if (isLeft) {
            const distFromInner = (BARS_PER_SIDE - 1) - i;
            idleX = centerX - idleInnerGap - distFromInner * idleStep;
          } else {
            const distFromInner = i - BARS_PER_SIDE;
            idleX = centerX + idleInnerGap + distFromInner * idleStep;
          }

          const activeX = activeStartX + i * activeStep;
          const x = lerp(idleX, activeX, m);

          const sideDist = isLeft
            ? (BARS_PER_SIDE - 1 - i) / (BARS_PER_SIDE - 1)
            : (i - BARS_PER_SIDE) / (BARS_PER_SIDE - 1);
          const ambientWave1 = Math.sin(timeSec * 2.4 - sideDist * 5.2);
          const ambientWave2 = Math.cos(timeSec * 1.5 + sideDist * 3.1) * 0.5;
          const ambientFactor = 0.82 + 0.34 * ((ambientWave1 + ambientWave2 + 1.5) / 3.0);
          const ambientFloor = (1 - sideDist * 0.75) * (4 + 4 * Math.sin(timeSec * 2.8 - sideDist * 4.5));
          let idleH = Math.max(4, (idleHeights[i] * 72 * ambientFactor + ambientFloor) * scale);

          const normCenter = Math.abs(i - (TOTAL_BARS - 1) / 2) / ((TOTAL_BARS - 1) / 2);
          const centerEnvelope = Math.pow(1 - normCenter * 0.78, 1.35);

          const wave1 = Math.sin(timeSec * 5.2 - i * 0.34);
          const wave2 = Math.sin(timeSec * 8.7 + i * 0.52) * 0.6;
          const wave3 = Math.cos(timeSec * 3.1 - i * 0.18) * 0.5;
          const syllablePulse = 0.55 + 0.45 * Math.sin(timeSec * 2.6 + Math.sin(timeSec * 1.3));
          const combined = (wave1 + wave2 + wave3 + 2.1) / 4.2;
          let activeH = (12 + combined * 118 * centerEnvelope * syllablePulse) * scale;

          const targetH = lerp(idleH, activeH, m);
          currentHeights[i] = lerp(currentHeights[i], targetH, 0.24);

          const alpha = lerp(0.88, 1.0, m);
          const glow = lerp(0.45, 0.95, m);

          drawRoundedBar(waveCtx, x, centerY, barWidth, Math.max(4, currentHeights[i]), alpha, glow);
        }
      }
    }
    requestAnimationFrame(renderWaveAnim);
  }
  requestAnimationFrame(renderWaveAnim);

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

  /* ---------- tema ---------- */

  const themeMedia = window.matchMedia("(prefers-color-scheme: dark)");
  let themeMode = document.documentElement.getAttribute("data-theme-mode") || "system";
  let themeTransitioning = false;

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function resolvedTheme(mode) {
    if (mode === "dark") return "dark";
    if (mode === "light") return "light";
    return themeMedia.matches ? "dark" : "light";
  }

  function paintTheme(mode) {
    const resolved = resolvedTheme(mode);
    const root = document.documentElement;
    root.classList.toggle("dark", resolved === "dark");
    root.classList.toggle("light", resolved === "light");
    root.setAttribute("data-theme-mode", mode);
  }

  function updateThemeControls() {
    const dark = document.documentElement.classList.contains("dark");
    $$(".theme-btn").forEach((toggle) => {
      const use = toggle.querySelector("use");
      if (use) use.setAttribute("href", dark ? "#i-sun" : "#i-moon");
      toggle.setAttribute("aria-pressed", dark ? "true" : "false");
      toggle.title = dark ? "Açık temaya geç" : "Koyu temaya geç";
    });
    const label = $("#themeBtnLabel");
    if (label) {
      label.textContent = dark ? "Açık" : "Koyu";
    }
    $$("[data-theme-choice]").forEach((button) => {
      button.classList.toggle("is-active", button.dataset.themeChoice === themeMode);
    });
  }

  function setTheme(mode, persist) {
    themeMode = ["system", "light", "dark"].includes(mode) ? mode : "system";
    paintTheme(themeMode);
    try {
      localStorage.setItem("theme", themeMode);
    } catch (error) {}
    updateThemeControls();
    if (persist) {
      if (hasApi("ai_settings_save")) saveAi({ theme: themeMode });
      triggerInstantSettingsSave();
    }
  }
  window.setTheme = setTheme;

  function toggleTheme(anchor) {
    if (themeTransitioning) return;
    const root = document.documentElement;
    const next = root.classList.contains("dark") ? "light" : "dark";
    const apply = () => setTheme(next, true);
    if (!document.startViewTransition || prefersReducedMotion()) {
      apply();
      return;
    }
    const rect = anchor.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const x = (cx / window.innerWidth) * 100;
    const y = (cy / window.innerHeight) * 100;
    const radius = Math.hypot(
      Math.max(cx, window.innerWidth - cx),
      Math.max(cy, window.innerHeight - cy)
    );
    const base = Math.hypot(window.innerWidth, window.innerHeight) / Math.SQRT2;
    const percent = (radius / base) * 100;
    themeTransitioning = true;
    const transition = document.startViewTransition(apply);
    transition.ready
      .then(() => {
        root.animate(
          { clipPath: [`circle(0% at ${x}% ${y}%)`, `circle(${percent}% at ${x}% ${y}%)`] },
          {
            duration: 400,
            easing: "ease-in-out",
            fill: "forwards",
            pseudoElement: "::view-transition-new(root)",
          }
        );
      })
      .catch(() => {});
    transition.finished.finally(() => {
      themeTransitioning = false;
    });
  }

  themeMedia.addEventListener("change", () => {
    if (themeMode === "system") paintTheme("system");
  });
  updateThemeControls();

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
    if (!element) return;
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

    if (pageId === "page-dikte") {
      requestAnimationFrame(resizeWaveCanvas);
    }
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
    const rec = (state === "recording");
    stage.classList.toggle("is-listening", rec);
    stage.classList.toggle("is-recording", rec);
    stage.classList.toggle("is-processing", state === "processing");
    stage.classList.toggle("is-cleaning", state === "cleaning");
    stage.classList.toggle("is-loading", state === "loading");
    stage.classList.toggle("is-error", state === "error");

    if (isRecordingState !== rec) {
      isRecordingState = rec;
      morphFrom = morphValue;
      morphTo = rec ? 1 : 0;
      morphStartTime = performance.now();
    }

    const textCard = $(".text-card");
    if (textCard) {
      textCard.classList.toggle("is-shine",
        state === "processing" || state === "loading" || state === "cleaning");
    }

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
    } else if (state === "cleaning") {
      shortcutHint.textContent = "Metin düzenleniyor, lütfen bekle";
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
  window.applyState = applyState;

  function applyModel(snapshot) {
    const rawModel = snapshot.model || (snapshot.state === "error" ? "Model yok" : "Model yükleniyor…");
    modelName.textContent = rawModel;
    const dikteAiModelPill = $("#dikteAiModelPill");
    if (dikteAiModelPill) {
      dikteAiModelPill.textContent = snapshot.model || "—";
    }
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
    if (!items || !items.length) {
      lastActivity = "";
      activityList.innerHTML = "";
      const empty = document.createElement("div");
      empty.className = "activity-empty";
      empty.textContent = "Henüz etkinlik yok.";
      activityList.appendChild(empty);
      return;
    }
    // Deduplicate repetitive "Ayarlar kaydedildi" entries:
    // Only keep the most recent "Ayarlar kaydedildi" entry in the timeline!
    let foundSettingsSaved = false;
    const cleanItems = [];
    for (const item of items) {
      if (item && item.title === "Ayarlar kaydedildi") {
        if (!foundSettingsSaved) {
          cleanItems.push(item);
          foundSettingsSaved = true;
        }
      } else {
        cleanItems.push(item);
      }
    }
    const key = JSON.stringify(cleanItems);
    if (key === lastActivity) return;
    lastActivity = key;
    activityList.innerHTML = "";
    cleanItems.forEach((item, index) => {
      const row = document.createElement("div");
      row.className = "tl-item";
      row.style.setProperty("--i", String(Math.min(index, 5)));
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
    applyAi(snapshot.ai);
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

    historyItems.forEach((item, index) => {
      const row = document.createElement("div");
      row.className = "h-item";
      row.style.setProperty("--i", String(Math.min(index, 5)));
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

  function textStatus(item) {
    if (item.downloading) return { text: "İndiriliyor", cls: "busy" };
    if (item.paused) return { text: "Duraklatıldı", cls: "busy" };
    if (item.loaded) return { text: "Yüklü", cls: "" };
    if (item.active) return { text: "Aktif", cls: "" };
    if (item.installed) return { text: "İndirildi", cls: "" };
    if (item.partial) return { text: "Yarım indirme", cls: "busy" };
    return { text: "İndirilmedi", cls: "muted" };
  }

  function renderTextModels(list, items) {
    const panel = $("#detailPanel");
    if (panel) panel.style.display = "";
    const note = $("#localEngineNote");
    if (note) note.hidden = Boolean(modelsState && modelsState.local_text_available);

    const query = ($("#modelSearch").value || "").toLocaleLowerCase("tr");
    const visible = items.filter((item) =>
      !query || (item.label + " " + item.desc).toLocaleLowerCase("tr").includes(query)
    );

    if (!selectedTextModel || !visible.some((i) => i.name === selectedTextModel)) {
      const active = visible.find((i) => i.active);
      selectedTextModel = (active || visible[0] || {}).name || null;
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

    const download = modelsState && modelsState.text_download;

    visible.forEach((item) => {
      const card = document.createElement("div");
      card.className = "m-card" + (item.name === selectedTextModel ? " is-selected" : "");
      card.dataset.name = item.name;
      card.style.cursor = "pointer";

      const icon = document.createElement("div");
      icon.className = "m-ico";
      icon.innerHTML = '<svg class="ic"><use href="#i-spark"/></svg>';

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

      const isDownloading = download && download.name === item.name;
      if (isDownloading && (download.state === "downloading" || download.state === "pausing")) {
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

      const status = textStatus(item);
      const statusBox = document.createElement("div");
      statusBox.className = "m-status " + status.cls;
      const dot = document.createElement("span");
      dot.className = "dot";
      statusBox.append(dot, document.createTextNode(status.text));

      const actions = document.createElement("div");
      actions.className = "m-actions";

      const state = isDownloading ? download.state : null;
      if (state === "downloading" || state === "pausing") {
        const pause = document.createElement("button");
        pause.className = "m-btn";
        pause.textContent = "Duraklat";
        pause.addEventListener("click", () => textModelAction("text_model_pause", item.name));
        const cancel = document.createElement("button");
        cancel.className = "m-btn";
        cancel.textContent = "İptal";
        cancel.addEventListener("click", () => textModelAction("text_model_cancel", item.name));
        actions.append(pause, cancel);
      } else if (state === "paused") {
        const resume = document.createElement("button");
        resume.className = "m-btn primary";
        resume.textContent = "Devam et";
        resume.addEventListener("click", () => textModelAction("text_model_resume", item.name));
        const cancel = document.createElement("button");
        cancel.className = "m-btn";
        cancel.textContent = "İptal";
        cancel.addEventListener("click", () => textModelAction("text_model_cancel", item.name));
        actions.append(resume, cancel);
      } else if (item.installed) {
        const activate = document.createElement("button");
        activate.className = "m-btn";
        if (item.active || item.loaded) {
          activate.classList.add("is-active");
          activate.textContent = item.loaded ? "Yüklü" : "Aktif";
          activate.disabled = true;
        } else {
          activate.classList.add("primary");
          activate.textContent = "Aktifleştir";
          activate.addEventListener("click", () => textModelAction("text_model_activate", item.name));
        }
        actions.appendChild(activate);
      } else {
        const downloadBtn = document.createElement("button");
        downloadBtn.className = "m-btn primary";
        downloadBtn.textContent = item.partial ? "Devam et" : "İndir";
        downloadBtn.addEventListener("click", () => textModelAction("text_model_download", item.name));
        actions.appendChild(downloadBtn);
      }

      if (item.installed || item.partial) {
        const remove = document.createElement("button");
        remove.className = "icon-btn";
        remove.title = "Modeli sil";
        remove.setAttribute("aria-label", "Modeli sil");
        remove.innerHTML = '<svg class="ic" style="width:15px;height:15px"><use href="#i-trash"/></svg>';
        remove.disabled = item.downloading || item.loaded;
        remove.addEventListener("click", () => {
          if (!window.confirm(item.label + " diskten silinsin mi?")) return;
          textModelAction("text_model_delete", item.name);
        });
        actions.appendChild(remove);
      }

      // Faz 4.3: "⋯" (üç nokta) işlem menüsü
      const menuWrap = document.createElement("div");
      menuWrap.className = "model-menu-wrap";
      const menuBtn = document.createElement("button");
      menuBtn.className = "model-menu-btn";
      menuBtn.setAttribute("aria-label", "Model menüsü");
      menuBtn.textContent = "⋯";
      const menuDropdown = document.createElement("div");
      menuDropdown.className = "model-dropdown";

      if (item.installed && !item.active && !item.loaded) {
        const itemAct = document.createElement("button");
        itemAct.className = "model-dropdown-item";
        itemAct.textContent = "Aktifleştir";
        itemAct.addEventListener("click", (e) => {
          e.stopPropagation();
          menuDropdown.classList.remove("is-open");
          textModelAction("text_model_activate", item.name);
        });
        menuDropdown.appendChild(itemAct);
      }

      if (item.installed || item.partial) {
        const itemDel = document.createElement("button");
        itemDel.className = "model-dropdown-item danger";
        itemDel.textContent = "Dosyayı Sil";
        itemDel.addEventListener("click", (e) => {
          e.stopPropagation();
          menuDropdown.classList.remove("is-open");
          if (!window.confirm(item.label + " diskten silinsin mi?")) return;
          textModelAction("text_model_delete", item.name);
        });
        menuDropdown.appendChild(itemDel);
      }

      if (item.custom) {
        const itemRem = document.createElement("button");
        itemRem.className = "model-dropdown-item danger";
        itemRem.textContent = "Listeden Kaldır";
        itemRem.addEventListener("click", async (e) => {
          e.stopPropagation();
          menuDropdown.classList.remove("is-open");
          if (!window.confirm(item.label + " listeden tamamen kaldırılsın mı?")) return;
          if (hasApi("text_models_remove_custom")) {
            await api.text_models_remove_custom(item.name);
            toast("Özel model listeden kaldırıldı.", "info");
            loadModels();
          }
        });
        menuDropdown.appendChild(itemRem);
      }

      menuBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        $$(".model-dropdown.is-open").forEach(d => { if (d !== menuDropdown) d.classList.remove("is-open"); });
        menuDropdown.classList.toggle("is-open");
      });
      menuWrap.append(menuBtn, menuDropdown);
      actions.appendChild(menuWrap);

      card.append(icon, main, size, statusBox, actions);
      card.addEventListener("click", (e) => {
        if (e.target.closest("button") || e.target.closest(".model-menu-wrap") || e.target.closest(".model-dropdown")) {
          return;
        }
        selectedTextModel = item.name;
        renderModels();
      });
      list.appendChild(card);
    });
  }

  async function textModelAction(method, name) {
    if (!hasApi(method)) return;
    try {
      const result = await api[method](name);
      if (result && result.message) toast(result.message, result.ok ? "info" : "warn");
    } catch (error) {
      toast("İşlem yapılamadı.", "error");
    }
    loadModels();
  }

  function renderModels() {
    const list = $("#modelList");
    if (!list) return;
    const isText = modelTab === "text";
    const items = isText
      ? ((modelsState && modelsState.text_items) || [])
      : ((modelsState && modelsState.items) || []);
    $("#modelCount").textContent = items.length + " model";
    const title = $("#listTitle");
    if (title) title.textContent = isText ? "Metin Modelleri" : "Ses Modelleri";
    if (isText) {
      renderTextModels(list, items);
      renderDetail();
      return;
    }
    const panel = $("#detailPanel");
    const descPanel = $("#descPanel");
    if (panel && modelsState) panel.style.display = "";

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

      // Faz 4.3: Ses modeli indirme iptali
      if (item.downloading || (download && download.name === item.name && download.state === "downloading")) {
        const cancelBtn = document.createElement("button");
        cancelBtn.className = "m-btn";
        cancelBtn.textContent = "İptal";
        cancelBtn.addEventListener("click", async (e) => {
          e.stopPropagation();
          if (hasApi("models_cancel_download")) {
            await api.models_cancel_download();
            toast("Ses modeli indirme iptal edildi.", "info");
            loadModels();
          }
        });
        actions.appendChild(cancelBtn);
      }

      // Faz 4.3: "⋯" (üç nokta) işlem menüsü
      const menuWrap = document.createElement("div");
      menuWrap.className = "model-menu-wrap";
      const menuBtn = document.createElement("button");
      menuBtn.className = "model-menu-btn";
      menuBtn.setAttribute("aria-label", "Model menüsü");
      menuBtn.textContent = "⋯";
      const menuDropdown = document.createElement("div");
      menuDropdown.className = "model-dropdown";

      if (item.installed && !item.active) {
        const itemAct = document.createElement("button");
        itemAct.className = "model-dropdown-item";
        itemAct.textContent = "Aktifleştir";
        itemAct.addEventListener("click", (e) => {
          e.stopPropagation();
          menuDropdown.classList.remove("is-open");
          activateModel(item.name);
        });
        menuDropdown.appendChild(itemAct);
      }

      if (item.installed || item.partial) {
        const itemDel = document.createElement("button");
        itemDel.className = "model-dropdown-item danger";
        itemDel.textContent = "Dosyayı Sil";
        itemDel.addEventListener("click", (e) => {
          e.stopPropagation();
          menuDropdown.classList.remove("is-open");
          deleteModel(item.name, item.label);
        });
        menuDropdown.appendChild(itemDel);
      }

      if (item.custom) {
        const itemRem = document.createElement("button");
        itemRem.className = "model-dropdown-item danger";
        itemRem.textContent = "Listeden Kaldır";
        itemRem.addEventListener("click", async (e) => {
          e.stopPropagation();
          menuDropdown.classList.remove("is-open");
          if (!window.confirm(item.label + " listeden tamamen kaldırılsın mı?")) return;
          if (hasApi("models_remove_custom")) {
            await api.models_remove_custom(item.name);
            toast("Özel ses modeli listeden kaldırıldı.", "info");
            loadModels();
          }
        });
        menuDropdown.appendChild(itemRem);
      }

      menuBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        $$(".model-dropdown.is-open").forEach(d => { if (d !== menuDropdown) d.classList.remove("is-open"); });
        menuDropdown.classList.toggle("is-open");
      });
      menuWrap.append(menuBtn, menuDropdown);
      actions.appendChild(menuWrap);

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

    if (modelTab === "text") {
      const items = (modelsState && modelsState.text_items) || [];
      const item = items.find((entry) => entry.name === selectedTextModel) ||
                   items.find((entry) => entry.active) ||
                   items[0];
      if (!item) {
        panel.innerHTML = '<div class="empty">Model bulunamadı.</div>';
        descPanel.innerHTML = "";
        return;
      }
      const download = modelsState && modelsState.text_download;
      const isDownloading = download && download.name === item.name;
      const state = isDownloading ? download.state : null;
      const status = textStatus(item);

      let statusText = status.text;
      if (isDownloading && (download.state === "downloading" || download.state === "pausing")) {
        statusText = `İndiriliyor (%${download.percent || 0})`;
      }

      panel.innerHTML =
        '<div class="detail-head"><svg class="ic"><use href="#i-spark"/></svg>Model Detayları' +
          '<button class="icon-btn x" id="closeDetail" aria-label="Paneli kapat"><svg class="ic" style="width:15px;height:15px"><use href="#i-close"/></svg></button></div>' +
        '<div class="detail-model"><div class="m-ico"><svg class="ic"><use href="#i-spark"/></svg></div>' +
          '<div><div class="model-name" id="detailName"></div><div class="model-sub">Yerel GGUF metin modeli</div></div></div>' +
        '<div class="d-row">Kategori<span>Yapay Zeka Metin Modeli</span></div>' +
        '<div class="d-row">Boyut<span id="detailSize"></span></div>' +
        '<div class="d-row">Bellek / Donanım<span id="detailVram"></span></div>' +
        '<div class="d-row">Hız / Kalite<span id="detailPerf"></span></div>' +
        '<div class="d-row">Dosya<span id="detailFile" style="word-break:break-all"></span></div>' +
        '<div class="d-row">Klasör<span id="detailFolder"></span></div>' +
        '<div class="divider"></div>' +
        '<div class="d-row">Model Durumu<span id="detailStatus"></span></div>' +
        '<div class="d-actions" id="detailActionRow"></div>';

      panel.querySelector("#detailName").textContent = item.label;
      panel.querySelector("#detailSize").textContent = item.installed
        ? (item.size_label || "—") + " (diskte)"
        : (item.approx_label || "—") + " (indirme)";
      panel.querySelector("#detailVram").textContent = item.vram_label || "GPU / CPU (GGUF)";
      panel.querySelector("#detailPerf").textContent = (item.speed_label && item.quality_label)
        ? (item.speed_label + " · " + item.quality_label)
        : "Dengeli";
      panel.querySelector("#detailFile").textContent = item.filename || "—";
      panel.querySelector("#detailFolder").textContent = item.folder || (item.installed ? "models\\text" : "İndirilince oluşturulur");

      const statusSpan = panel.querySelector("#detailStatus");
      const led = document.createElement("span");
      led.className = "led";
      led.style.background = (item.active || item.loaded) ? "var(--ready)" : item.installed ? "var(--ready)" : (isDownloading ? "var(--processing)" : "#5C6A85");
      led.style.boxShadow = (item.active || item.loaded || item.installed) ? "0 0 7px rgba(46,212,122,.7)" : "none";
      statusSpan.append(led, document.createTextNode(statusText));

      const actionRow = panel.querySelector("#detailActionRow");
      if (state === "downloading" || state === "pausing") {
        const pauseBtn = document.createElement("button");
        pauseBtn.className = "btn";
        pauseBtn.textContent = "Duraklat";
        pauseBtn.addEventListener("click", () => textModelAction("text_model_pause", item.name));
        const cancelBtn = document.createElement("button");
        cancelBtn.className = "btn";
        cancelBtn.textContent = "İptal";
        cancelBtn.addEventListener("click", () => textModelAction("text_model_cancel", item.name));
        actionRow.append(pauseBtn, cancelBtn);
      } else if (state === "paused") {
        const resumeBtn = document.createElement("button");
        resumeBtn.className = "btn btn-primary";
        resumeBtn.textContent = "Devam et";
        resumeBtn.addEventListener("click", () => textModelAction("text_model_resume", item.name));
        const cancelBtn = document.createElement("button");
        cancelBtn.className = "btn";
        cancelBtn.textContent = "İptal";
        cancelBtn.addEventListener("click", () => textModelAction("text_model_cancel", item.name));
        actionRow.append(resumeBtn, cancelBtn);
      } else if (item.installed) {
        const actBtn = document.createElement("button");
        actBtn.className = "btn btn-primary";
        if (item.active || item.loaded) {
          actBtn.textContent = item.loaded ? "Yüklü" : "Aktif Model";
          actBtn.disabled = true;
        } else {
          actBtn.innerHTML = '<svg class="ic"><use href="#i-check"/></svg>Aktifleştir';
          actBtn.addEventListener("click", () => textModelAction("text_model_activate", item.name));
        }
        const delBtn = document.createElement("button");
        delBtn.className = "btn btn-danger";
        delBtn.innerHTML = '<svg class="ic"><use href="#i-trash"/></svg>Sil';
        delBtn.disabled = item.active || item.loaded;
        delBtn.addEventListener("click", () => {
          if (!window.confirm(item.label + " diskten silinsin mi?")) return;
          textModelAction("text_model_delete", item.name);
        });
        actionRow.append(actBtn, delBtn);
      } else {
        const dlBtn = document.createElement("button");
        dlBtn.className = "btn btn-primary";
        dlBtn.innerHTML = '<svg class="ic"><use href="#i-download"/></svg>' + (item.partial ? "Devam et" : "İndir");
        dlBtn.addEventListener("click", () => textModelAction("text_model_download", item.name));
        actionRow.appendChild(dlBtn);
      }

      panel.querySelector("#closeDetail").addEventListener("click", () => {
        panel.style.display = "none";
      });
      panel.style.display = "";

      descPanel.innerHTML =
        '<h3><svg class="ic"><use href="#i-spark"/></svg>Model Açıklaması</h3>' +
        '<p id="descText"></p><ul class="desc-list" id="descList"></ul>';
      descPanel.querySelector("#descText").textContent = item.desc || item.description || "Yerel GGUF metin modeli.";
      const dList = descPanel.querySelector("#descList");
      const defaultFeatures = [
        "Türkçe, İngilizce ve Almanca metin temizleme ve çeviri",
        "Çevrimdışı yerel GGUF motoru (llama.cpp)",
        "İndirme duraklatma ve kaldığı yerden devam etme desteği"
      ];
      const tags = (item.tags && item.tags.length) ? item.tags : defaultFeatures;
      tags.forEach((tag) => {
        const li = document.createElement("li");
        li.innerHTML = '<svg class="ic"><use href="#i-check"/></svg><span></span>';
        li.querySelector("span").textContent = tag;
        dList.appendChild(li);
      });
      return;
    }

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
      updateBento();
      const signature = JSON.stringify({
        tab: modelTab,
        items: (result.items || []).map((item) => [item.name, item.active, item.installed, item.partial, item.size_bytes]),
        text: (result.text_items || []).map((item) => [
          item.name, item.installed, item.partial, item.active, item.loaded,
          item.bytes, item.downloading, item.paused,
        ]),
        download: result.download ? [result.download.name, result.download.state, result.download.percent] : null,
        textDownload: result.text_download
          ? [result.text_download.name, result.text_download.state, result.text_download.percent]
          : null,
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

  $$("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      modelTab = button.dataset.tab;
      $$("[data-tab]").forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-selected", active ? "true" : "false");
      });
      renderModels();
    });
  });

  /* ---------- yapay zeka ---------- */

  function transcriptText() {
    return transcript.innerText.replace(/\u00a0/g, " ").trim();
  }

  function applyAi(ai) {
    if (!ai) return;
    aiState = Object.assign({}, ai, { state: ai.state || (aiState && aiState.state) || "ready" });

    const canSyncInput = (aiSaveInFlight === 0) && (Date.now() - lastAiSaveTime > 400);

    if (canSyncInput) {
      if (outputLang && ai.output_language && document.activeElement !== outputLang) {
        outputLang.value = ai.output_language;
      }
      if (autoTranslate) {
        autoTranslate.checked = Boolean(ai.auto_translate);
      }
      const outSet = $("#outputLangSettings");
      if (outSet && ai.output_language && document.activeElement !== outSet) {
        outSet.value = ai.output_language;
      }
      const autoTrSet = $("#autoTranslateSettings");
      if (autoTrSet) {
        setSwitchEl(autoTrSet, Boolean(ai.auto_translate));
      }
      const autoPaste = $("#autoPasteSwitch");
      if (autoPaste && ai.auto_paste !== undefined) {
        setSwitchEl(autoPaste, ai.auto_paste !== false);
      }
      const inLang = $("#inputLang");
      if (inLang && ai.input_language && document.activeElement !== inLang) {
        inLang.value = ai.input_language;
      }
      const txtProv = $("#textProvider");
      if (txtProv && ai.provider && document.activeElement !== txtProv) {
        txtProv.value = ai.provider;
      }
    }

    if (textModelRow) {
      if (ai.provider === "none" || !ai.provider) {
        textModelRow.textContent = "Sağlayıcı kapalı";
      } else if (ai.provider === "openrouter") {
        textModelRow.textContent = (ai.openrouter_model || "Model seçilmedi") + " · OpenRouter";
      } else {
        textModelRow.textContent = ai.text_model || "Seçilmedi";
      }
    }
    applyEffects(ai.effects !== false);
    updateActionButtons();
    updateBento();
  }

  function updateActionButtons() {
    if (!cleanBtn || !translateBtn) return;
    const state = aiState ? aiState.state : "loading";
    const busy = !aiState || aiBusy ||
      state === "loading" || state === "recording" ||
      state === "processing" || state === "cleaning";
    const providerOn = Boolean(aiState && aiState.provider !== "none");
    const hasText = Boolean(transcriptText());
    const disabled = busy || !providerOn || !hasText;
    cleanBtn.disabled = disabled;
    translateBtn.disabled = disabled;
    const hint = !providerOn
      ? "Ayarlar → Yapay Zeka'dan sağlayıcı seç"
      : "Önce bir dikte yap veya metin yaz";
    cleanBtn.title = (busy || !providerOn || !hasText) ? hint : "Metni yapay zeka ile düzelt";
    translateBtn.title = (busy || !providerOn || !hasText) ? hint : "Metni seçili çıktı diline çevir";
  }

  function replaceAllText(text) {
    transcript.innerHTML = "";
    appended.length = 0;
    const parts = String(text || "").split(/\n+/).map((line) => line.trim()).filter(Boolean);
    if (!parts.length) {
      undoBtn.disabled = true;
      return;
    }
    parts.forEach((line) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = line;
      transcript.appendChild(paragraph);
      appended.push(paragraph);
    });
    undoBtn.disabled = false;
    transcript.scrollTop = transcript.scrollHeight;
  }

  async function saveAi(patch) {
    if (!hasApi("ai_settings_save")) return null;
    aiSaveInFlight++;
    try {
      const result = await api.ai_settings_save(patch);
      if (result && result.ok) {
        applyAi(result.ai);
        syncAiControls(result.ai);
        return result.ai;
      }
      toast((result && result.message) || "Ayar kaydedilemedi.", "warn");
    } catch (error) {
      toast("Ayar kaydedilemedi.", "error");
    } finally {
      aiSaveInFlight--;
      lastAiSaveTime = Date.now();
    }
    return null;
  }

  async function runAi(kind) {
    const name = kind === "translate" ? "translate_text" : "clean_text";
    if (!hasApi(name)) {
      toast("Uygulama bağlantısı hazır değil.", "info");
      return;
    }
    const text = transcriptText();
    if (!text) {
      toast("Önce bir dikte yap veya metin yaz.", "info");
      return;
    }
    if (aiBusy) return;
    const button = kind === "translate" ? translateBtn : cleanBtn;
    const label = kind === "translate" ? $("#translateLabel") : $("#cleanLabel");
    const original = label ? label.textContent : "";
    aiBusy = true;
    button.disabled = true;
    if (label) label.textContent = kind === "translate" ? "Çevriliyor…" : "Temizleniyor…";
    try {
      const result = await api[name](text);
      if (result && result.ok) {
        replaceAllText(result.text);
        toast(result.message || "Metin güncellendi.");
      } else {
        toast((result && result.message) || "Metin işlenemedi.", "warn");
      }
    } catch (error) {
      toast("Metin işlenemedi.", "error");
    } finally {
      aiBusy = false;
      if (label) label.textContent = original;
      updateActionButtons();
    }
  }

  function applyProviderSections(ai) {
    const provider = ai && ai.provider ? ai.provider : "none";
    const openSection = $("#openRouterSection");
    const localSection = $("#localAiSection");
    const offNote = $("#aiOffNote");
    if (openSection) openSection.hidden = provider !== "openrouter";
    if (localSection) localSection.hidden = provider !== "local";
    if (offNote) offNote.hidden = provider !== "none";
    const localName = $("#localModelName");
    if (localName) {
      localName.textContent = ai && ai.text_model
        ? ai.text_model + " (yerel)"
        : "Metin modeli seçilmedi.";
    }
  }

  function setKeyState(ai) {
    const state = $("#orKeyState");
    const remove = $("#orKeyDelete");
    const hasKey = Boolean(ai && ai.key_set);
    if (state) state.textContent = hasKey ? "Anahtar kayıtlı: " + (ai.key_masked || "") : "Anahtar yok";
    if (remove) remove.disabled = !hasKey;
  }

  function syncAiControls(ai) {
    if (!ai) return;
    applyProviderSections(ai);
    setKeyState(ai);
    const provider = $("#textProvider");
    if (provider) provider.value = ai.provider || "none";
    const input = $("#inputLang");
    if (input) input.value = ai.input_language || "auto";
    const outputSettings = $("#outputLangSettings");
    if (outputSettings) outputSettings.value = ai.output_language || "tr";
    setSwitchEl($("#autoPasteSwitch"), ai.auto_paste !== false);
    setSwitchEl($("#autoTranslateSettings"), Boolean(ai.auto_translate));
    setSwitchEl($("#effectsSwitch"), ai.effects !== false);
    const showAll = $("#orShowAll");
    if (showAll) showAll.checked = Boolean(ai.openrouter_show_all);
    const prompt = $("#systemPrompt");
    if (prompt) prompt.value = ai.system_prompt || ai.default_system_prompt || "";
    const select = $("#orModelSelect");
    if (select && ai.openrouter_model) {
      const exists = Array.from(select.options).some((option) => option.value === ai.openrouter_model);
      if (!exists) {
        const option = document.createElement("option");
        option.value = ai.openrouter_model;
        option.textContent = ai.openrouter_model;
        select.appendChild(option);
      }
      select.value = ai.openrouter_model;
    }
  }

  async function loadOpenRouterModels(refresh) {
    if (!hasApi("openrouter_models")) return;
    const select = $("#orModelSelect");
    if (!select) return;
    const showAll = Boolean($("#orShowAll") && $("#orShowAll").checked);
    const query = ($("#orModelSearch") && $("#orModelSearch").value) || "";
    let result = null;
    try {
      result = await api.openrouter_models(Boolean(refresh), showAll, query);
    } catch (error) {
      toast("Model listesi alınamadı.", "error");
      return;
    }
    const models = (result && result.models) || [];
    const previous = select.value || (aiState && aiState.openrouter_model) || "";
    select.innerHTML = "";
    if (!models.length) {
      const option = document.createElement("option");
      option.value = previous || "";
      option.textContent = result && result.ok
        ? "Aramanla eşleşen model yok"
        : "Model listesi alınamadı";
      select.appendChild(option);
      if (result && !result.ok) toast(result.message || "Model listesi alınamadı.", "warn");
      return;
    }
    models.forEach((model) => {
      const option = document.createElement("option");
      option.value = model.id;
      option.textContent = model.name + " · " + model.price_label;
      if (model.context_label) option.title = model.context_label;
      select.appendChild(option);
    });
    const keep = previous && models.some((model) => model.id === previous);
    if (previous && !keep && !query) {
      const option = document.createElement("option");
      option.value = previous;
      option.textContent = previous;
      select.appendChild(option);
    }
    if (previous && (keep || !query)) {
      select.value = previous;
    } else if (models[0]) {
      select.value = models[0].id;
      if (!previous) saveAi({ openrouter_model: models[0].id });
    }
  }

  if (cleanBtn) cleanBtn.addEventListener("click", () => runAi("clean"));
  if (translateBtn) translateBtn.addEventListener("click", () => runAi("translate"));
  transcript.addEventListener("input", updateActionButtons);
  if (outputLang) {
    outputLang.addEventListener("change", () => saveAi({ output_language: outputLang.value }));
  }
  if (autoTranslate) {
    autoTranslate.addEventListener("change", () => {
      saveAi({ auto_translate: autoTranslate.checked });
      if (autoTranslate.checked && aiState && (aiState.provider === "none" || !aiState.provider)) {
        toast("Otomatik çevirinin çalışması için Ayarlar → Yapay Zeka'dan bir sağlayıcı (Yerel veya OpenRouter) seçin.", "warn");
      }
    });
  }

  $("#textProvider").addEventListener("change", async () => {
    const ai = await saveAi({ text_provider: $("#textProvider").value });
    if (ai && ai.provider === "openrouter") loadOpenRouterModels(false);
    triggerInstantSettingsSave();
  });
  $("#inputLang").addEventListener("change", () => {
    saveAi({ input_language: $("#inputLang").value });
    triggerInstantSettingsSave();
  });
  $("#outputLangSettings").addEventListener("change", () => {
    saveAi({ output_language: $("#outputLangSettings").value });
    triggerInstantSettingsSave();
  });
  $("#autoPasteSwitch").addEventListener("click", () => {
    const on = !switchOnEl($("#autoPasteSwitch"));
    setSwitchEl($("#autoPasteSwitch"), on);
    saveAi({ auto_paste: on });
    triggerInstantSettingsSave();
  });
  $("#autoTranslateSettings").addEventListener("click", () => {
    const on = !switchOnEl($("#autoTranslateSettings"));
    setSwitchEl($("#autoTranslateSettings"), on);
    saveAi({ auto_translate: on });
    triggerInstantSettingsSave();
  });
  $("#systemPrompt").addEventListener("change", () => saveAi({ system_prompt: $("#systemPrompt").value }));
  $("#systemPromptReset").addEventListener("click", () => {
    const value = (aiState && aiState.default_system_prompt) || "";
    $("#systemPrompt").value = value;
    saveAi({ system_prompt: value });
  });
  $("#goModelsBtn").addEventListener("click", () => showPage("page-modeller"));
  $("#orModelRefresh").addEventListener("click", () => loadOpenRouterModels(true));
  $("#orModelSelect").addEventListener("change", () => saveAi({ openrouter_model: $("#orModelSelect").value }));
  $("#orShowAll").addEventListener("change", async () => {
    await saveAi({ openrouter_show_all: Boolean($("#orShowAll").checked) });
    loadOpenRouterModels(false);
  });
  let orModelsTimer = null;
  $("#orModelSearch").addEventListener("input", () => {
    window.clearTimeout(orModelsTimer);
    orModelsTimer = window.setTimeout(() => loadOpenRouterModels(false), 300);
  });

  $("#orKeySave").addEventListener("click", async () => {
    if (!hasApi("openrouter_key_save")) return;
    const input = $("#orKeyInput");
    const value = (input.value || "").trim();
    if (!value) {
      $("#orKeyStatus").textContent = "Önce anahtarı yaz.";
      return;
    }
    const result = await api.openrouter_key_save(value);
    $("#orKeyStatus").textContent = (result && result.message) || "";
    if (result && result.ok) {
      input.value = "";
      input.placeholder = result.masked || "sk-or-…";
      applyAi(result.ai);
      syncAiControls(result.ai);
    }
  });

  $("#orKeyTest").addEventListener("click", async () => {
    if (!hasApi("openrouter_key_test")) return;
    $("#orKeyStatus").textContent = "Deneniyor…";
    try {
      const result = await api.openrouter_key_test();
      $("#orKeyStatus").textContent = (result && result.message) || "";
    } catch (error) {
      $("#orKeyStatus").textContent = "Bağlantı denenemedi.";
    }
  });

  $("#orKeyDelete").addEventListener("click", async () => {
    if (!hasApi("openrouter_key_delete")) return;
    if (!window.confirm("OpenRouter anahtarı silinsin mi?")) return;
    const result = await api.openrouter_key_delete();
    $("#orKeyStatus").textContent = (result && result.message) || "";
    if (result && result.ok) {
      const input = $("#orKeyInput");
      input.value = "";
      input.placeholder = "sk-or-…";
      applyAi(result.ai);
      syncAiControls(result.ai);
    }
  });

  $$(".theme-btn").forEach((btn) => {
    btn.addEventListener("click", () => toggleTheme(btn));
  });
  $$("[data-theme-choice]").forEach((button) => {
    button.addEventListener("click", () => setTheme(button.dataset.themeChoice, true));
  });

  /* ---------- efektler ve bento ---------- */

  function applyEffects(on) {
    document.body.classList.toggle("fx-on", Boolean(on));
    setSwitchEl($("#effectsSwitch"), Boolean(on));
  }

  function providerSummary(ai) {
    if (!ai || ai.provider === "none" || !ai.provider) return "Kapalı";
    if (ai.provider === "openrouter") return (ai.openrouter_model || "Model seçilmedi") + " · OpenRouter";
    return ai.text_model || "Yerel";
  }

  function updateBento() {
    const audioSub = $("#bentoAudioSub");
    const textSub = $("#bentoTextSub");
    const providerSub = $("#bentoProviderSub");
    if (audioSub) {
      const items = (modelsState && modelsState.items) || [];
      const installed = items.filter((item) => item.installed).length;
      const active = items.find((item) => item.active);
      audioSub.textContent = installed
        ? installed + " yüklü" + (active ? " · aktif: " + (active.label || active.name) : "")
        : "Henüz model yüklenmedi";
    }
    if (textSub) {
      const items = (modelsState && modelsState.text_items) || [];
      const installed = items.filter((item) => item.installed).length;
      const active = items.find((item) => item.active || item.loaded);
      textSub.textContent = installed
        ? installed + " yüklü" + (active ? " · aktif: " + (active.label || active.name) : "")
        : "Henüz model yüklenmedi";
    }
    if (providerSub) providerSub.textContent = providerSummary(aiState);
  }

  $("#effectsSwitch").addEventListener("click", async () => {
    const next = !(aiState && aiState.effects !== false);
    const ai = await saveAi({ effects: next });
    if (ai) applyEffects(next);
    triggerInstantSettingsSave();
  });

  /* MagicCard: fareyi izleyen kart ışığı */
  document.addEventListener("pointermove", (event) => {
    const target = event.target && event.target.closest
      ? event.target.closest(".card, .m-card, .h-item, .bento-card")
      : null;
    $$("[data-fx-glow]").forEach((el) => el.removeAttribute("data-fx-glow"));
    if (target) {
      const rect = target.getBoundingClientRect();
      target.style.setProperty("--mx", (event.clientX - rect.left) + "px");
      target.style.setProperty("--my", (event.clientY - rect.top) + "px");
      target.setAttribute("data-fx-glow", "");
    }
  }, { passive: true });

  /* ---------- ayarlar ---------- */

  function markDirty() {
    settingsDirty = true;
    $("#settingsDirty").hidden = false;
  }

  function setSwitchEl(element, on) {
    if (!element) return;
    element.classList.toggle("on", Boolean(on));
    element.setAttribute("aria-checked", on ? "true" : "false");
  }

  function switchOnEl(element) {
    return Boolean(element && element.classList.contains("on"));
  }

  function setSwitch(on) {
    setSwitchEl($("#historySwitch"), on);
  }

  function switchOn() {
    return switchOnEl($("#historySwitch"));
  }

  function updateHotkeyPreview() {
    const select = $("#hotkeySelect");
    const option = select.options[select.selectedIndex];
    $("#hotkeyNow").textContent = option ? option.textContent : "—";
  }

  function applySettingsAvailability(state) {
    const busy = state === "recording" || state === "processing" || state === "loading" || state === "cleaning";
    const save = $("#saveSettingsBtn");
    const select = $("#hotkeySelect");
    const sw = $("#historySwitch");
    if (save) save.disabled = busy;
    if (select) select.disabled = busy;
    if (sw) sw.disabled = busy;
    [
      "#textProvider", "#inputLang", "#outputLangSettings", "#autoPasteSwitch",
      "#autoTranslateSettings", "#systemPrompt", "#systemPromptReset", "#orKeyInput",
      "#orKeySave", "#orKeyTest", "#orModelSelect", "#orModelRefresh",
      "#orModelSearch", "#orShowAll",
    ].forEach((selector) => {
      const element = $(selector);
      if (element) element.disabled = busy;
    });
    if (!busy) setKeyState(aiState);
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
      const hasOption = Array.from(select.options).some((opt) => opt.value === data.hotkey);
      if (!hasOption && data.hotkey) {
        const customOpt = document.createElement("option");
        customOpt.value = data.hotkey;
        customOpt.textContent = formatKeyLabel(data.hotkey);
        select.appendChild(customOpt);
      }
      select.value = data.hotkey;
      setSwitch(data.save_history);
      updateHotkeyPreview();
      if (data.ai) {
        applyAi(Object.assign({}, data.ai, { state: data.state }));
        syncAiControls(data.ai);
        setTheme(data.ai.theme || "system", false);
        if (data.ai.provider === "openrouter") loadOpenRouterModels(false);
      }
      settingsDirty = false;
      $("#settingsDirty").hidden = true;
      applySettingsAvailability(data.state);
      loadUninstallInfo();
      initUpdateCard({
        version: data.ai && data.ai.version,
        last_check_text: data.ai && data.ai.update_last_check_text,
        auto_check: data.ai && data.ai.update_check_on_start,
      });
      if (data.sidebar_collapsed !== undefined) toggleSidebar(data.sidebar_collapsed, false);
      if (data.design_style) setDesignStyle(data.design_style, false);
      checkWelcomeWizard(data);
      loadRollbackReleases();
    } catch (error) {
      console.error("Ayarlar okunamadı:", error);
      toast("Ayarlar okunamadı.", "error");
    }
  }

  /* ---------- Faz 3.5: Ayarlarda Anında Otomatik Kaydetme ---------- */
  let instantSaveTimer = null;
  function triggerInstantSettingsSave() {
    clearTimeout(instantSaveTimer);
    instantSaveTimer = setTimeout(async () => {
      const currentHotkey = ($("#hotkeySelect") && $("#hotkeySelect").value)
        ? $("#hotkeySelect").value
        : ((settingsState && settingsState.hotkey) || "right_ctrl");
      const payload = {
        save_history: switchOn(),
        hotkey: currentHotkey,
        design_style: designStyle,
        sidebar_collapsed: document.body.classList.contains("sidebar-collapsed"),
        theme: themeMode,
        output_language: $("#outputLangSettings") ? $("#outputLangSettings").value : "tr",
        auto_translate: switchOnEl($("#autoTranslateSettings")),
        input_language: $("#inputLang") ? $("#inputLang").value : "auto",
        auto_paste: switchOnEl($("#autoPasteSwitch")),
        text_provider: $("#textProvider") ? $("#textProvider").value : "none",
        effects: switchOnEl($("#effectsSwitch")),
        autostart: switchOnEl($("#autostartSwitch")),
        update_check_on_start: switchOnEl($("#updateAutoSwitch")),
      };
      if ($("#systemPrompt")) {
        payload.system_prompt = $("#systemPrompt").value;
      }
      try {
        if (hasApi("ai_settings_save")) {
          await api.ai_settings_save(payload);
        }
        if (hasApi("settings_save")) {
          await api.settings_save({
            hotkey: payload.hotkey,
            save_history: payload.save_history,
            design_style: payload.design_style,
            sidebar_collapsed: payload.sidebar_collapsed,
          });
        }
        settingsDirty = false;
        const dirty = $("#settingsDirty");
        if (dirty) dirty.hidden = true;
      } catch (e) {
        console.warn("Otomatik kaydetme hatası:", e);
      }
    }, 400);
  }

  $("#hotkeySelect").addEventListener("change", () => {
    updateHotkeyPreview();
    markDirty();
    triggerInstantSettingsSave();
  });

  $("#historySwitch").addEventListener("click", () => {
    setSwitch(!switchOn());
    markDirty();
    triggerInstantSettingsSave();
  });

  $("#saveSettingsBtn").addEventListener("click", async () => {
    clearTimeout(instantSaveTimer);
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

  $("#topLang")?.addEventListener("change", () => {});

  /* ---------- uygulama: otomatik baslatma ve kaldirma ---------- */

  let uninstallState = null;
  let uninstallStep = 0;

  async function loadUninstallInfo() {
    if (!hasApi("uninstall_info")) return;
    try {
      uninstallState = await api.uninstall_info();
    } catch (error) {
      return;
    }
    if (!uninstallState) return;
    setSwitchEl($("#autostartSwitch"), Boolean(uninstallState.autostart));
    const btn = $("#uninstallBtn");
    if (!uninstallState.installed) {
      btn.disabled = true;
      btn.title = "Bu sürüm kurulumla gelmedi";
      $("#uninstallDesc").textContent =
        "Bu sürüm geliştirme kopyası; kaldırıcı yok. Silinecek veri yaklaşık " +
        uninstallState.size_text + ".";
    } else {
      $("#uninstallDesc").textContent =
        "Silinecek veri yaklaşık " + uninstallState.size_text +
        ": geçmiş, ayarlar ve günlükler her durumda silinir. Modeller ikinci onayda korunabilir. Bu işlem geri alınamaz.";
    }
  }

  $("#autostartSwitch").addEventListener("click", async () => {
    if (!hasApi("ai_settings_save")) return;
    const next = !switchOnEl($("#autostartSwitch"));
    try {
      const result = await api.ai_settings_save({ autostart: next });
      if (result && result.ok) {
        setSwitchEl($("#autostartSwitch"), next);
        if (uninstallState) uninstallState.autostart = next;
        toast(next ? "Windows açılışında başlatılacak." : "Windows açılışında başlatılmayacak.", "info");
        triggerInstantSettingsSave();
      } else {
        toast((result && result.message) || "Kaydedilemedi.", "warn");
      }
    } catch (error) {
      toast("Kaydedilemedi.", "error");
    }
  });

  $("#uninstallBtn").addEventListener("click", () => {
    if (uninstallState && !uninstallState.installed) return;
    uninstallStep = 1;
    $("#uninstallYes").textContent = "Evet, kaldır";
    $("#uninstallStatus").textContent = "";
    $("#uninstallConfirm").hidden = false;
  });

  $("#uninstallNo").addEventListener("click", () => {
    uninstallStep = 0;
    $("#uninstallConfirm").hidden = true;
  });

  $("#uninstallYes").addEventListener("click", async () => {
    if (uninstallStep === 1) {
      uninstallStep = 2;
      const size = uninstallState ? uninstallState.size_text : "tüm";
      $("#uninstallQuestion").textContent =
        "İkinci onay: yaklaşık " + size + " veri kalıcı olarak silinecek. Emin misin?";
      $("#uninstallKeepRow").hidden = false;
      $("#uninstallYes").textContent = "Evet, her şeyi sil";
      return;
    }
    if (!hasApi("uninstall")) return;
    const status = $("#uninstallStatus");
    status.textContent = "Kaldırıcı başlatılıyor…";
    try {
      const keepModels = $("#uninstallKeepModels").checked;
      const result = await api.uninstall({ keep_models: keepModels });
      status.textContent = result && result.ok
        ? (result.message || "Kaldırıcı başlatıldı")
        : (result && result.message) || "Kaldırıcı başlatılamadı.";
    } catch (error) {
      status.textContent = "Kaldırıcı başlatılamadı.";
    }
  });

  /* ---------- guncelleme karti ---------- */

  let updateInfo = null;

  function initUpdateCard(data) {
    if (!data) return;
    $("#updateVersion").textContent = data.version || "—";
    $("#updateLastCheck").textContent = data.last_check_text || "—";
    setSwitchEl($("#updateAutoSwitch"), Boolean(data.auto_check));
  }

  $("#updateCheckBtn").addEventListener("click", async () => {
    if (!hasApi("update_check")) return;
    const btn = $("#updateCheckBtn");
    const status = $("#updateStatus");
    btn.disabled = true;
    status.textContent = "Denetleniyor…";
    try {
      const result = await api.update_check(true);
      if (result && result.ok && result.update_available) {
        updateInfo = result;
        status.textContent = result.message || ("Yeni sürüm: " + result.version);
        $("#updateApplyBtn").disabled = false;
      } else if (result && result.ok) {
        status.textContent = result.message || "Güncelsin.";
        $("#updateApplyBtn").disabled = true;
      } else {
        status.textContent = (result && result.message) || "Denetlenemedi.";
        $("#updateApplyBtn").disabled = true;
      }
    } catch (error) {
      status.textContent = "Sunucuya ulaşılamadı.";
      $("#updateApplyBtn").disabled = true;
    }
    btn.disabled = false;
  });

  $("#updateApplyBtn").addEventListener("click", async () => {
    if (!hasApi("update_apply") || !updateInfo) return;
    const btn = $("#updateApplyBtn");
    const status = $("#updateStatus");
    btn.disabled = true;
    btn.textContent = "İndiriliyor…";
    try {
      const result = await api.update_apply();
      if (result && result.ok) {
        status.textContent = result.message || "Kurulum başlatıldı.";
        toast(result.message || "Kurulum başlatıldı; uygulama kapanacak.", "info");
      } else {
        status.textContent = (result && result.message) || "Kurulum başlatılamadı.";
        toast((result && result.message) || "Kurulum başlatılamadı.", "error");
      }
    } catch (error) {
      status.textContent = "Kurulum başlatılamadı.";
    }
    btn.textContent = "Uygulamayı Güncelle";
  });

  $("#updateAutoSwitch").addEventListener("click", async () => {
    if (!hasApi("ai_settings_save")) return;
    const next = !switchOnEl($("#updateAutoSwitch"));
    try {
      const result = await api.ai_settings_save({ update_check_on_start: next });
      if (result && result.ok) {
        setSwitchEl($("#updateAutoSwitch"), next);
        toast(next ? "Açılışta sürüm denetlenecek." : "Açılışta sürüm denetlenmeyecek.", "info");
        triggerInstantSettingsSave();
      } else {
        toast((result && result.message) || "Kaydedilemedi.", "warn");
      }
    } catch (error) {
      toast("Kaydedilemedi.", "error");
    }
  });

  /* ---------- Faz 4.4: Hugging Face Özel Model Ekle Modalı ---------- */
  const customModelModal = $("#customModelModal");
  const addCustomModelBtn = $("#addCustomModelBtn");
  const customModelClose = $("#customModelClose");
  const customModelCancel = $("#customModelCancel");
  const customModelSubmit = $("#customModelSubmit");
  const customModelKind = $("#customModelKind");
  const customModelRepo = $("#customModelRepo");
  const customModelFilename = $("#customModelFilename");
  const customModelLabel = $("#customModelLabel");
  const customModelStatus = $("#customModelStatus");
  const groupCustomFilename = $("#groupCustomFilename");
  const customModelRepoLabel = $("#customModelRepoLabel");

  if (addCustomModelBtn && customModelModal) {
    addCustomModelBtn.addEventListener("click", () => {
      customModelKind.value = modelTab === "text" ? "text" : "audio";
      updateCustomModelForm();
      customModelModal.hidden = false;
      if (customModelStatus) customModelStatus.textContent = "";
    });

    const closeModal = () => { customModelModal.hidden = true; };
    if (customModelClose) customModelClose.addEventListener("click", closeModal);
    if (customModelCancel) customModelCancel.addEventListener("click", closeModal);

    function updateCustomModelForm() {
      const isText = customModelKind.value === "text";
      if (groupCustomFilename) groupCustomFilename.hidden = !isText;
      if (customModelRepoLabel) {
        customModelRepoLabel.textContent = isText
          ? "Hugging Face Repo ID veya Doğrudan GGUF URL:"
          : "Hugging Face Whisper Repo ID:";
      }
      if (customModelRepo) {
        customModelRepo.placeholder = isText
          ? "ör. unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF"
          : "ör. openai/whisper-large-v3-turbo veya user/repo";
      }
    }
    if (customModelKind) customModelKind.addEventListener("change", updateCustomModelForm);

    if (customModelSubmit) {
      customModelSubmit.addEventListener("click", async () => {
        const repo = (customModelRepo ? customModelRepo.value : "").trim();
        const filename = (customModelFilename ? customModelFilename.value : "").trim();
        const label = (customModelLabel ? customModelLabel.value : "").trim();
        const isText = customModelKind.value === "text";

        if (!repo) {
          if (customModelStatus) customModelStatus.textContent = "Repo ID veya URL boş olamaz.";
          return;
        }

        if (customModelStatus) customModelStatus.textContent = "Ekleniyor…";
        customModelSubmit.disabled = true;
        try {
          let res = null;
          if (isText) {
            if (hasApi("text_models_add_custom")) {
              res = await api.text_models_add_custom(repo, filename, label);
            }
          } else {
            if (hasApi("models_add_custom")) {
              res = await api.models_add_custom(repo, label);
            }
          }
          if (res && res.ok) {
            toast(res.message || "Özel model başarıyla eklendi.", "info");
            closeModal();
            loadModels();
          } else {
            if (customModelStatus) customModelStatus.textContent = (res && res.message) || "Model eklenemedi.";
          }
        } catch (e) {
          if (customModelStatus) customModelStatus.textContent = "Model eklenirken hata oluştu.";
        }
        customModelSubmit.disabled = false;
      });
    }
  }

  /* ---------- Faz 4.1: 1–3 Tuşlu Kısayol Yakalayıcı ---------- */
  const hotkeyRecorderBtn = $("#hotkeyRecorderBtn");
  const hotkeyRecorderStatus = $("#hotkeyRecorderStatus");
  let recordingHotkey = false;

  function formatKeyLabel(key) {
    if (!key) return "";
    const parts = key.toLowerCase().split("+");
    return parts.map(p => {
      if (p === "ctrl" || p === "control" || p === "right_ctrl" || p === "left_ctrl") return "Ctrl";
      if (p === "shift" || p === "right_shift" || p === "left_shift") return "Shift";
      if (p === "alt" || p === "right_alt" || p === "left_alt") return "Alt";
      if (p === "space") return "Space";
      return p.toUpperCase();
    }).join(" + ");
  }

  if (hotkeyRecorderBtn) {
    hotkeyRecorderBtn.addEventListener("click", () => {
      recordingHotkey = true;
      hotkeyRecorderBtn.disabled = true;
      if (hotkeyRecorderStatus) {
        hotkeyRecorderStatus.hidden = false;
        hotkeyRecorderStatus.textContent = "Tuşlara basın (örn: Ctrl+Shift+D)...";
      }
    });

    window.addEventListener("keydown", (e) => {
      if (!recordingHotkey) return;
      e.preventDefault();
      e.stopPropagation();

      if (["Control", "Shift", "Alt", "Meta"].includes(e.key)) {
        let pressed = [];
        if (e.ctrlKey) pressed.push("Ctrl");
        if (e.shiftKey) pressed.push("Shift");
        if (e.altKey) pressed.push("Alt");
        if (hotkeyRecorderStatus) hotkeyRecorderStatus.textContent = pressed.join("+") + " + ...";
        return;
      }

      let combo = [];
      if (e.ctrlKey) combo.push("ctrl");
      if (e.shiftKey) combo.push("shift");
      if (e.altKey) combo.push("alt");

      let keyName = e.key.toLowerCase();
      if (e.code && e.code.startsWith("Key")) keyName = e.code.slice(3).toLowerCase();
      else if (e.code && e.code.startsWith("Digit")) keyName = e.code.slice(5);
      else if (e.code === "Space") keyName = "space";
      else if (e.code && e.code.startsWith("F") && !isNaN(e.code.slice(1))) keyName = e.code.toLowerCase();

      if (!combo.includes(keyName)) combo.push(keyName);
      const hotkeyStr = combo.join("+");

      recordingHotkey = false;
      hotkeyRecorderBtn.disabled = false;
      const formatted = formatKeyLabel(hotkeyStr);
      if (hotkeyRecorderStatus) hotkeyRecorderStatus.textContent = formatted;
      const hotkeyNow = $("#hotkeyNow");
      if (hotkeyNow) hotkeyNow.textContent = formatted;
      window.__hotkeyLabel = formatted;
      if (shortcutHint) shortcutHint.textContent = formatted + " (basılı tut)";

      const select = $("#hotkeySelect");
      if (select) {
        let opt = Array.from(select.options).find((o) => o.value === hotkeyStr);
        if (!opt) {
          opt = document.createElement("option");
          opt.value = hotkeyStr;
          opt.textContent = formatted;
          select.appendChild(opt);
        }
        select.value = hotkeyStr;
      }
      if (settingsState) {
        settingsState.hotkey = hotkeyStr;
      }

      if (hasApi("settings_save")) {
        api.settings_save({ hotkey: hotkeyStr }).then(() => {
          toast("Kısayol güncellendi: " + formatted, "info");
        }).catch(() => {});
      }
    });
  }


  /* ---------- Faz 5.1: Önceki Sürümlere Dön (Rollback) ---------- */
  const rollbackSelect = $("#rollbackSelect");
  const rollbackBtn = $("#rollbackBtn");

  async function loadRollbackReleases() {
    if (!rollbackSelect || !hasApi("update_list_releases")) return;
    try {
      const releases = await api.update_list_releases();
      rollbackSelect.innerHTML = "";
      const list = Array.isArray(releases) ? releases : ((releases && releases.releases) || []);
      if (!list || !list.length) {
        rollbackSelect.innerHTML = '<option value="">Önceki sürüm bulunamadı</option>';
        if (rollbackBtn) rollbackBtn.disabled = true;
        return;
      }
      const defaultOpt = document.createElement("option");
      defaultOpt.value = "";
      defaultOpt.textContent = "Geri dönülecek sürüm seçin…";
      rollbackSelect.appendChild(defaultOpt);

      list.forEach((rel) => {
        const opt = document.createElement("option");
        opt.value = rel.tag_name || rel.version;
        opt.textContent = (rel.name || rel.tag_name) + (rel.is_current ? " (Mevcut)" : "");
        opt.dataset.url = rel.installer_url || "";
        opt.dataset.sha256 = rel.sha256 || "";
        if (rel.is_current) opt.disabled = true;
        rollbackSelect.appendChild(opt);
      });
      rollbackSelect.addEventListener("change", () => {
        if (rollbackBtn) rollbackBtn.disabled = !rollbackSelect.value;
      });
    } catch (e) {
      if (rollbackSelect) rollbackSelect.innerHTML = '<option value="">Sürümler alınamadı</option>';
    }
  }

  if (rollbackBtn) {
    rollbackBtn.addEventListener("click", async () => {
      const target = rollbackSelect ? rollbackSelect.value : "";
      if (!target) return;
      const selectedOpt = rollbackSelect ? rollbackSelect.options[rollbackSelect.selectedIndex] : null;
      const installerUrl = (selectedOpt && selectedOpt.dataset.url) || "";
      const sha256 = (selectedOpt && selectedOpt.dataset.sha256) || "";

      if (!window.confirm(target + " sürümüne geri dönülsün mü? Mevcut sürüm kaldırılıp bu sürüm kurulacak.")) return;
      rollbackBtn.disabled = true;
      rollbackBtn.textContent = "İndiriliyor…";
      try {
        if (hasApi("update_rollback")) {
          const res = await api.update_rollback(target, installerUrl, sha256);
          toast((res && res.message) || "Rollback işlemi başlatıldı.", "info");
        }
      } catch (e) {
        toast("Rollback başlatılamadı.", "error");
      }
      rollbackBtn.disabled = false;
      rollbackBtn.textContent = "Bu Sürüme Dön";
    });
  }

  /* ---------- Faz 4.4: 5 Adımlı Karşılama Sihirbazı ---------- */
  const welcomeWizard = $("#welcomeWizard");
  const wizardPrevBtn = $("#wizardPrevBtn");
  const wizardNextBtn = $("#wizardNextBtn");
  const wizardFinishBtn = $("#wizardFinishBtn");
  const restartWizardBtn = $("#restartWizardBtn");
  let currentWizardStep = 1;

  function showWizardStep(step) {
    currentWizardStep = step;
    for (let i = 1; i <= 5; i++) {
      const stepEl = $("#wizardStep" + i);
      if (stepEl) stepEl.hidden = (i !== step);
      const ind = $(`[data-step="${i}"]`);
      if (ind) {
        ind.classList.toggle("is-active", i === step);
        ind.classList.toggle("is-done", i < step);
      }
    }
    if (wizardPrevBtn) wizardPrevBtn.disabled = (step === 1);
    if (wizardNextBtn) wizardNextBtn.hidden = (step === 5);
    if (wizardFinishBtn) wizardFinishBtn.hidden = (step !== 5);

    if (step === 2) {
      const hwTitle = $("#wizardHwTitle");
      const hwDesc = $("#wizardHwDesc");
      if (hwTitle && modelsState) {
        const hasGpu = modelsState.device === "GPU";
        hwTitle.textContent = hasGpu ? "NVIDIA GPU Algılandı" : "Standart CPU Modu";
        hwDesc.textContent = hasGpu
          ? "GPU hızlandırma aktif. CUDA bileşenleri ile maksimum performans."
          : "NVIDIA ekran kartı bulunamadı. Dikte CPU ile optimize çalışacak.";
      }
    }
  }

  if (wizardPrevBtn) {
    wizardPrevBtn.addEventListener("click", () => {
      if (currentWizardStep > 1) showWizardStep(currentWizardStep - 1);
    });
  }
  if (wizardNextBtn) {
    wizardNextBtn.addEventListener("click", () => {
      if (currentWizardStep < 5) showWizardStep(currentWizardStep + 1);
    });
  }

  $$(".wizard-choice").forEach((label) => {
    label.addEventListener("click", () => {
      const radio = label.querySelector('input[type="radio"]');
      if (radio) {
        const name = radio.name;
        $$(`.wizard-choice input[name="${name}"]`).forEach((r) => {
          r.closest(".wizard-choice").classList.remove("is-selected");
        });
        label.classList.add("is-selected");
        radio.checked = true;
      }
    });
  });

  if (wizardFinishBtn) {
    wizardFinishBtn.addEventListener("click", async () => {
      const designVal = ($('input[name="wizardDesign"]:checked') || {}).value || "dikte_ai";
      const modelVal = ($('input[name="wizardModel"]:checked') || {}).value || "small";
      const hotkeyVal = ($('input[name="wizardHotkey"]:checked') || {}).value || "right_ctrl";

      setDesignStyle(designVal, true);

      if (welcomeWizard) welcomeWizard.hidden = true;
      toast("Kurulum tamamlandı! Dikte hazır.", "info");

      if (hasApi("wizard_complete")) {
        await api.wizard_complete({
          design_style: designVal,
          active_model: modelVal,
          hotkey: hotkeyVal,
          setup_done: true,
        }).catch(() => {});
      } else if (hasApi("settings_save")) {
        await api.settings_save({
          design_style: designVal,
          active_model: modelVal,
          hotkey: hotkeyVal,
          setup_done: true,
        }).catch(() => {});
      }
    });
  }

  if (restartWizardBtn) {
    restartWizardBtn.addEventListener("click", () => {
      if (welcomeWizard) {
        welcomeWizard.hidden = false;
        showWizardStep(1);
      }
    });
  }

  async function checkWelcomeWizard(settings) {
    if (!welcomeWizard) return;
    if (settings && settings.setup_done === false) {
      welcomeWizard.hidden = false;
      showWizardStep(1);
      return;
    }
    if (hasApi("wizard_status")) {
      try {
        const st = await api.wizard_status();
        if (st && st.setup_done === false) {
          welcomeWizard.hidden = false;
          showWizardStep(1);
        }
      } catch (e) {}
    }
  }

  showPage("page-dikte");
})();
