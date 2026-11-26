# STATE.md — Güncel Durum

Bu dosya yeni sohbette kaldığımız yerden devam etmek içindir. Her oturum sonunda güncellenir.

## Şu anki aşama
**2026-11-26 — Kod Denetimi Faz 1–4, Genele Hitap Eden 5 Dokunuş, Vitrin Yenilemesi ve 4 HyperFrames Videosu tamamlandı:**
- **Kod Denetimi Faz 1–4:** `reports/2026-11-24-kod-denetimi-raporu.md` içindeki tüm yüksek (Y1–Y6) ve orta bulgular, ~500 satırlık ortaklaştırma (`dikte/fsutil.py`, `app.js` model kartı/detay paneli birleştirmesi, `text_engine.py` yerel AI tekilleştirmesi, ölü kod temizliği) ve 7 test maskesi TDD ile giderildi.
- **Genele Hitap Eden 5 Dokunuş:** Ayarlar'a **Bas-Bırak** kısayol modu (`hotkey_mode`), **Mikrofon seçimi** (`audio.py` `list_input_devices`), Windows'ta odak çalmayan **mini "Dinliyor / Yazıyor" göstergesi** (`dikte/indicator.py`) ve teknik ayarları **Gelişmiş Ayarlar** altında toplayan sade düzen eklendi.
- **Vitrin & 4 HyperFrames Videosu:** `docs/index.html` + `README*.md` içine `docs/assets/og-card.png` (1200×630), 4 günlük kullanım senaryosu, SmartScreen açıklaması ve EN/TR 50s video seçici eklendi; `video-arastirma` (Neon) brifiyle (`reports/2026-11-26-video-arastirma-brifi.md`) `video-uretim` (Neon) ekibi HyperFrames üzerinden 4 MP4 (Yatay 16:9 50s TR/EN + Shorts 9:16 30s TR/EN) ve 2 web optimize kopya (`docs/assets/dikte-tanitim-tr.mp4`, `dikte-tanitim-en.mp4`) üretti.
- **Doğrulama:** **465 passed, 1 skipped** (`77.17s`), `--selftest` (`Whisper Large | GPU | float16`) çıkış kodu `0`, Playwright Edge `docs/index.html` 6 kombinasyon (`EN`/`TR` × `1440/768/360px`) `overflow: False`, `0` hata.
- **2026-11-25 — Genele Hitap Etme, Rakip İncelemesi ve Sade Tanıtım Araştırması (salt-okunur) tamamlandı:**
- Gelir amacı gütmeden ve süre baskısı olmadan (~1.000 kullanıcı/indirme hedefiyle) Dikte'nin mevcut kodu, vitrini ve benzer ücretsiz/açık kaynak projeler (`Handy`, `Buzz`, `OpenWhispr`, `Vibe`, `Whispering`, `HoldToSpeak`, `LocalFlow`, `PieFlow`) Exa ile araştırıldı.
- Sonuçlar `reports/2026-11-25-yayin-ve-buyume-raporu.md` dosyasına kaydedildi ve `reports/README.md` dizinine eklendi; uygulama koduna dokunulmadı.
- **2026-11-24 — v1.6.1 Tam Kod Denetimi (salt-okunur) ve `asama-baslat` Protokol Güncellemesi tamamlandı:**
- `calisma-duzeni.md` uyarınca commit `102cfc6` üzerinde 4 paralel salt-okunur `Gemini 4 Hydrogen (Medium)` işçisi ve koordinatör satır doğrulamasıyla kapsamlı kod denetimi yapıldı; rapor `reports/2026-11-24-kod-denetimi-raporu.md` dosyasına yazıldı ve `reports/README.md` dizinine eklendi (**0 blocker, 6 yüksek, ~40 orta, 7 test maskesi, ~500 satır kısaltma fırsatı**). Kod dosyalarına dokunulmadı; başlangıç ölçüsü **AST 25/25 OK** ve **413 passed, 1 skipped** (100,4 sn).
- `.agent/skills/asama-baslat/SKILL.md` (ve şablon/yedek kopyaları), `.agent/skills/asama-bitir/SKILL.md` ve `calisma-duzeni.md` §10 güncellendi: alt ajan/işçi modeli **Gemini 4 Hydrogen** ve zorluğa göre değiştirilebilir düşünme seviyesi (`low`/`medium`/`high`/`xhigh`) olarak netleştirildi; `asama-baslat` içine önceki oturumları ve kararları kontrol etmek için **Obsidian MCP hafıza kontrolü** eklendi.
- **2026-11-21 — Çok Dilli Vitrin: İngilizce Varsayılan README ve GitHub Pages (EN / TR) tamamlandı:**
- `README.md` tamamen İngilizceye çevrildi (GitHub ana sayfasında varsayılan İngilizce görünüm) ve en üstüne **English | [Türkçe](README.tr.md)** dil geçiş bağlantıları eklendi; mevcut Türkçe içerik `README.tr.md` dosyasına taşındı (`?lang=tr` site bağlantılarıyla).
- `docs/index.html` varsayılan İngilizce (`<html lang="en" class="dark">`) olarak güncellendi; üst çubuğa **EN | TR** dil seçme düğmesi, `localStorage` tercihi ve `?lang=tr`/`?lang=en` desteği eklendi. Playwright Edge ile `1440x900`, `768x1024` ve `360x800` ekranlarda `default=en`, `TR → EN` geçişi, `overflow: False` ve `0` JS hatası doğrulandı.
- **2026-11-20 — Remotion Tanıtım Videosu, Web Sitesi ve README Yayını tamamlandı (v1.6.1 canlı):**
- `video/` klasöründe 45 saniyelik (1350 kare, `1920x1080`, `30 fps`, H.264 + AAC) 7 sahneli Remotion tanıtım videosu ve deterministik 9 WAV ses efekti kiti üretildi; 15 sahne karesi görsel olarak denetlenip Sahne 5 logo kırpılması ve dairesel dalga easing'i düzeltildi.
- Web akışına uygun sıkıştırılmış `docs/assets/dikte-tanitim.mp4` (`9.185.093` bayt, `+faststart`, H.264 `1920x1080` + AAC) ve 1080p kapak görseli `docs/assets/dikte-tanitim-poster.png` oluşturuldu.
- GitHub Pages (`docs/index.html`) içine `#tanitim-videosu` oynatıcı bölümü (1440/768/360px `overflow: False`), `README.md` alt bölümüne ise tıklanabilir kapak ve doğrudan izleme/indirme bağlantıları eklendi.
- **v1.6.1 — Canlı Yayın, `onnxruntime` Kurulum Hatası Düzeltmesi ve GitHub Pages İndirme Sitesi tamamlandı (2026-11-19):**
  - `run_dikte.py`/`__main__.py` `onnxruntime` erken yükleme, `engine.py` `vad_filter=False` yedeği, `error_reporter.py` `_recent_session_log()` + `onnxruntime_dll_error` kuralı.
  - Güncel kurucu `installer\Output\Dikte-Setup-1.6.1.exe` (178.553.401 bayt, SHA-256: `953e4f5c0f3599a09c8880efd546334e17a9535883938c0bf59967efe55f3dfd`) `v1.6.1` GitHub Release ve `https://mete2012seker-lgtm.github.io/dikte/` yayında (**413 passed, 1 skipped**).
- Sıradaki adım: yeni `Dikte-Setup-1.6.1.exe` ile son konuşma/güncelleme testi ve isteğe bağlı topluluk dağıtımı (`winget`, AlternativeTo).

## Biten (kanıtla)
- **Kod Denetimi Faz 1–4, 5 Dokunuş, Vitrin Yenilemesi ve 4 HyperFrames Videosu (2026-11-26):**
  - **Faz 1–4:** `dikte/controller.py` (Y1 `_cleaning_owner` + `_refresh_token`), `dikte/hotkey.py` (Y2 `Key.value.vk`), `dikte/text_models.py` (Y3 `effective_total` + ağ/kilit), `dikte/ui/app.js` (Y4–Y5 `callApi`, `visibilitychange` tepsi pil tasarrufu, menü/modal Escape), `installer/Dikte.iss` (Y6 `{%TEMP}\dikte` + model sorusu), `dikte/fsutil.py` (ortak atomik yazma/yedek/HF/elevate), 7 test maskesi temizliği (`tests/test_faz1_audit.py`, `tests/test_faz234_audit.py`).
  - **5 Dokunuş:** `hotkey_mode` (`hold`/`toggle`), `list_input_devices()` + `input_device`, `dikte/indicator.py` (`FloatingIndicator`, `WS_EX_NOACTIVATE`), `<details id="advancedSettings" open>` (`tests/test_genele_dokunuslar.py`).
  - **Vitrin & Video:** `docs/assets/og-card.png`, `docs/index.html` (4 senaryo, SmartScreen, EN/TR 50s video seçici), `reports/2026-11-26-video-arastirma-brifi.md`, `video-hf/` (4 HyperFrames MP4 + 2 web MP4 + 2 poster).
  - **Kanıt:** `pytest -q` **465 passed, 1 skipped** (`77.17s`), `--selftest` çıkış kodu `0` (`GPU / float16`, `%80` benzerlik), Playwright Edge `docs/index.html` 6/6 OK, `ffprobe` 6/6 MP4 OK. Obsidian: `02-Projeler/dikte-projesi/2026-11-26-faz1-4-dokunuslar-ve-hyperframes.md`.
- **Genele Hitap Etme ve Sade Tanıtım Araştırması (2026-11-25):**
  - **Rapor:** `reports/2026-11-25-yayin-ve-buyume-raporu.md` (`reports/README.md` güncellendi); Exa rakip/ekosistem araştırması + mevcut kod/vitrin incelemesi. Uygulama kodu değişmedi (`dikte/`, `docs/`, `installer/`, `tests/` dokunulmadı).
  - **Obsidian Kaydı:** `02-Projeler/dikte-projesi/2026-11-25-yayin-ve-buyume-stratejisi.md` ve `_genel-bakis.md` güncellendi.
- **v1.6.1 Tam Kod Denetimi ve `asama-baslat` Protokol Güncellemesi (2026-11-24):**
  - **Denetim Raporu:** `reports/2026-11-24-kod-denetimi-raporu.md` (`reports/README.md` güncellendi); 4 paralel `Gemini 4 Hydrogen (Medium)` işçisi + 7 kritik iddianın satır doğrulaması; 0 blocker, 6 yüksek (`controller.py:287`, `hotkey.py:392`, `text_models.py:568-573`, `app.js:2211-2218`, `app.js` 5 köprü çağrısı, `Dikte.iss:73`), ~40 orta, 7 test maskesi, ~500 satır kısaltma planı.
  - **Doğrulama:** AST 25/25 dosya OK, `pytest -q` **413 passed, 1 skipped** (100,4 sn), gizli bilgi taraması temiz.
  - **Protokol Güncellemesi:** `asama-baslat`, `asama-bitir` ve `calisma-duzeni.md` §10 içinde `Gemini 4 Hydrogen` (değiştirilebilir düşünme seviyesi) ve Obsidian MCP geçmiş kontrolü zorunlu hale getirildi.
- **Çok Dilli Vitrin: İngilizce Varsayılan README ve Web Sitesi (2026-11-21):**
  - **README (`README.md`, `README.tr.md`):** GitHub ana sayfasında varsayılan İngilizce açıklama (`README.md`) ve üstte tıklanabilir `English | Türkçe` bağlantıları; `README.tr.md` Türkçe sürümü; her iki dosyada 6/6 yerel görsel/dosya bağlantısı doğrulandı (`missing=[]`).
  - **GitHub Pages (`docs/index.html`):** Varsayılan `<html lang="en">`, üst çubukta `EN | TR` dil seçici (`#langSwitch`), `localStorage` hatırlama, `?lang=tr`/`?lang=en` sorgu parametresi ve dinamik tema/kopyala etiketleri.
  - **Doğrulama:** Playwright Edge `1440x900`, `768x1024`, `360x800` (`default=en`, `TR → EN` geçişi, `overflow_en=False`, `overflow_tr=False`, `errors=0`, `?lang=tr` OK).
- **Remotion Tanıtım Videosu, Web Sitesi ve README Yayını (2026-11-20):**
  - **Video Kaynağı (`video/`):** `src/theme.ts` (Dikte koyu/açık renk paleti, `@fontsource` yerel Türkçe fontlar), 5 katmanlı `StageLayers` + `DotPattern`, `MicMorphWave` (48 bar + morphing mikrofon), `MagicUI` (`ShineBorderCard`, `MagicCard`, `AnimatedListItem`, `Keycap3D`), 7 sahne (`Scene1Hook`..`Scene7CTA`) ve `scripts/generate-sfx.mjs` (9 adet 16-bit WAV ses efekti).
  - **Web & README Entegrasyonu:** `docs/assets/dikte-tanitim.mp4` (`9.185.093` bayt, `ffprobe`: `h264 1920x1080 30fps + aac, 45.013s`), `docs/assets/dikte-tanitim-poster.png`, `docs/index.html` (`#tanitim-videosu` + üst menü bağlantısı) ve `README.md` (`## Tanıtım Videosu`).
  - **Doğrulama:** `npm --prefix video run typecheck` (exit 0), `pytest -q` (**413 passed, 1 skipped**, 68.03 sn), 15 kontrol karesi görsel denetimi, Playwright `docs/index.html` (`1440x900`, `768x1024`, `360x800` `overflow: False`, `mp4_http=200`).
- **v1.6.1 Canlı Yayın, `onnxruntime`/VAD Düzeltmesi ve İndirme Sitesi (2026-11-19, 2. Oturum):**
  - **Kök Neden & Düzeltme:** `run_dikte.py` ve `dikte/__main__.py` içinde `onnxruntime` erken yükleme; `dikte/engine.py` içinde `onnxruntime`/VAD hatasında otomatik `vad_filter=False` yedeği; `dikte/error_reporter.py` içinde `_recent_session_log()` ve `onnxruntime_dll_error` kuralı (+3 regresyon testi).
  - **Vitrin & GitHub Pages:** `README.md` yenilendi; `docs/index.html` (masaüstü/tablet/telefon 360px–1440px `overflow: False`, Playwright Edge doğrulamalı) ve `docs/assets/` (maskeli v1.6.1 ekran görüntüleri + ikon) eklendi; `https://mete2012seker-lgtm.github.io/dikte/` yayında (`status: built`).
  - **Kurucu & Canlı GitHub Release:** `Dikte-Setup-1.6.1.exe` (178.553.401 bayt, SHA-256: `953e4f5c0f3599a09c8880efd546334e17a9535883938c0bf59967efe55f3dfd`) + `installer/latest.json` (`561` bayt) `gh release upload --clobber` ile `v1.6.1` sürümüne yüklendi (`https://github.com/mete2012seker-lgtm/dikte/releases/tag/v1.6.1`).
  - **Doğrulama:** Tam test süiti **413 passed, 1 skipped**; paketli `dist\Dikte\Dikte.exe --selftest --cpu` çıkış kodu `0` (`VAD filter removed 00:00.304 of audio`).
- **v1.6.1 Yayın Öncesi Denetim ve Faz 1–3 Sertleştirmesi (2026-11-19):**
  - **Denetim Raporu:** `reports/2026-11-19-yayin-oncesi-denetim-raporu.md` (4 paralel `Gemini 4 Hydrogen Medium` işçisi + satır düzeyinde çapraz doğrulama).
  - **Yayın Zinciri & Güvenlik:** `dikte/updater.py` & `dikte/uninstall.py` Windows UAC `ShellExecuteW("runas")`, `controller.uninstall()` temiz kapanış, `download_installer` `sha256=None` reddi + rollback SHA-256 zorunluluğu, semver ön sürüm sıralaması, `draft`/`prerelease` filtresi, `release-assets.githubusercontent.com`, `config.UNINSTALL_REG_KEY` Inno `AppId` eşlemesi.
  - **Backend, Veri & Tanılama:** `text_models.py`/`models.py` HF alan adı ve `../` yol geçişi engeli + dosya kapanışı sonrası temizlik + HTTP 206 düzeltmesi; `hotkey.py` `on_release` ve `GetAsyncKeyState` takılı tuş kurtarma; `audio.py` akış hatası ve callback zaman damgası; `engine.py`/`controller.py` `AUTO_MODEL` normalize; `paste.py` UIPI `SendInput` kontrolü; `clipboard.py` 3x tekrar; `error_reporter.py` `native_crash_tail` + boşluklu kullanıcı adı maskeleme + benzersiz atomik yazma; `diagnostics.py` `setup_logging()` handler ve `OSError` koruması.
  - **Arayüz & Test Maskeleri:** `app.js` Sihirbaz GPU tespiti (`has_nvidia_gpu`), `snapshot.ai.state`, açılışta tema/tasarım/sidebar senkronu, `#updateApplyBtn` hata sonrası açılma, `Escape` ile kısayol kaydı iptali; `tests/test_ui.py` `copy.ai.state` test maskesi temizlendi.
  - **Kurucu & Testler:** `Dikte-Setup-1.6.1.exe` (178.532.285 bayt, SHA-256: `9bf2b45b9bb16f2b1811dc8350a6ce6df8e2a971b1e68d97ab9db1dea92b7799`); tam süit **410 passed, 1 skipped** (+41 yeni test).
- **v1.6.1 OpenWhispr Analizi, Gömülü Hata Tespit Aracı ve Faz A/B Stabilite (2026-11-18):**
  - **OpenWhispr Analizi & Denetim (`reports/2026-11-18-openwhispr-tanilama-ve-stabilite-raporu.md`):** Pano yedekleme/geri yükleme, Özel Sözlük, tepsi modu Floating Pill ve mikrofon/RMS dersleri çıkarıldı; 16 mimari/mantıksal bulgu satır kanıtıyla belgelendi.
  - **Gömülü Hata Tespit & Log Kopyalama Aracı (`dikte/error_reporter.py`, `dikte/diagnostics.py`):** `RotatingFileHandler` (2 MB × 3), `faulthandler` (`native_crash.log`), `sys/threading.excepthook`, `running.lock` beklenmedik kapanma tespiti, gizlilik maskelemesi (API anahtarları/kullanıcı yolu hariç; `history.json`/`secrets.json`/`last.wav`/`_latest` asla okunmaz), 10+ Türkçe çözüm kuralı, `#diagBanner`, `#diagModal`, Ayarlar → **Sorun Giderme ve Tanılama** kartı, tepside `"Tanılama Raporu Kopyala"`, JS `error`/`unhandledrejection` köprüsü ve başsız açılış hatası için `MessageBoxW`.
  - **Faz A/B Çökme, Kilit ve Akış Düzeltmeleri:** `_engine_lock` → `_lock` kilit sırası (`_transcribe_path`, `_local_process_text`, `text_model_activate`), `ai_cancel()` için `_ai_task_token` + `_seq += 1`, `HotkeyListener` hook thread'inden işçi kuyruğuna devir + kanonik tuş kimliği, `AudioRecorder` `_chunks_lock` + `MAX_RECORD_SECONDS = 600`, `tray.py` & `bridge.py` kapanış/kilit tekilleştirme, `--uninstall` çıkış kodu düzeltmesi, `updater.apply()` sonrası temiz kapanış (`_schedule_exit_after_apply`), `text_models.py` HTTP 416 + `__closure__` kaldırma + CPU fallback sarmalama, `uninstall.py` `with winreg.OpenKey`, ilk açılış sihirbazı, atomik ayar kaydı ve `applyModel()` `cleaning` durumu.
  - **Paketleme Düzeltmesi (`Dikte.spec`):** `collect_all("faster_whisper")` eklenerek `silero_vad_v6.onnx` eksikliği giderildi; `dist\Dikte\Dikte.exe --selftest --cpu` çıkış kodu 0 ile doğrulandı.
  - **Kurucu & Testler:** `Dikte-Setup-1.6.1.exe` (178.515.604 bayt, SHA-256: `ad2d1ea4fd1e87c382b25f548ad572d0762ba6897a68e5781aaefe58a5d0889a`); `installer/latest.json` güncellendi; tam süit **369 passed, 1 skipped**.
- **Sistem Tepsisi, Otomatik Yapıştırma, Arayüz ve Model Sağlamlaştırma Turu (2026-11-12, 3. Oturum):**
  - **Sistem Tepsisi & Global Kısayol Otomatik Yapıştırma:** `dikte/paste.py` ve `dikte/hotkey.py` Windows düzeyinde güçlendirildi; `SendInput` + `MapVirtualKeyW` ile güvenli tuş gönderimi yapıldı. Değiştirici tuşların bırakılması `GetAsyncKeyState` ile beklendi ve yalnızca hâlâ basılı olan tuşlara `KEYEVENTF_KEYUP` gönderildi (böylece basılı olmayan `Alt` tuşuna keyup gönderilip hedef uygulamanın Dosya/Düzen menü çubuğuna odak kaptırması engellendi). `VK_RCONTROL` ve `VK_RMENU` için `KEYEVENTF_EXTENDEDKEY` eklendi. `is_pasting()` bayrağı ile `HotkeyListener`'ın yapay `Ctrl+V`'yi kısayol basılışı sanıp kendini yeniden tetiklemesi engellendi. Uygulama sistem tepsisinde gizliyken (`IsWindowVisible(hwnd) == 0`) yapıştırmanın engellenmemesi sağlandı.
  - **Dikte Çeviri Doğruluğu & Sıfır Gecikme:** `dikte/engine.py` ve `data/settings.json` güncellendi; girdi dili `"tr"` olarak sabitlendi. Whisper motoruna Türkçe `initial_prompt` ("Türkçe sesli dikte kaydı, doğru imla ve noktalama ile.") ve Silero VAD filtre parametreleri (`speech_pad_ms=400`, `min_silence_duration_ms=500`, `threshold=0.35`) eklendi. `controller.py` içinde Whisper zaten yüklüyse kaydın sıfır gecikmeyle başlaması sağlandı.
  - **Yan Menü Logo ve Katlama İyileştirmesi:** `dikte/ui/style.css` içinde `.brand-logo` hem geniş hem daraltılmış modda `min-width: 40px; min-height: 40px; flex: 0 0 40px;` olarak kilitlendi; logo büzüşmesi tamamen önlendi. `#sidebarCollapseBtn` dikey yerleşim ve `rotate(180deg)` animasyonu kazandı; yan menü genişlik geçişi `.22s ease` yumuşatıldı.
  - **Metin Modelleri Sağ Detay Paneli:** `dikte/ui/app.js` ve `dikte/text_models.py` güncellendi; Modeller sayfasında herhangi bir metin modeline tıklandığında sağdaki `Model Detayları` ve `Model Açıklaması` panelleri ses modellerindeki zenginlikle (GGUF boyutu, VRAM/RAM gereksinimi, Hız/Kalite, Dosya/Klasör ve İndir/Duraklat/Devam/İptal/Aktifleştir/Sil aksiyonları) açılması sağlandı.
  - **Otomatik Çeviri & Çıktı Dili Kararlılığı:** `dikte/text_engine.py` içinde Qwen3 modellerinin ürettiği `<think>...</think>` ve `<thought>...</thought>` akıl yürütme blokları regex ile temizlendi; DE/EN/TR kelime sözlüğü genişletilerek `not_translated` hataları önlendi. `controller.py` içinde yerel modeller için 2 denemeli yeniden deneme ve dinamik token bütçesi eklendi. `app.js` içinde `aiSaveInFlight` ve 400ms koruma gecikmesiyle 250ms'lik `snapshot()` polling'inin seçimleri ezmesi engellendi; sağlayıcı kapalıyken (`provider === "none"`) Dikte sayfasında açıklayıcı toast uyarısı gösterildi.
  - **Dağıtım ve Genel İyileştirmeler:** `Dikte.spec` içine `pynvml` ve `tests/data` veri klasörü eklendi; `installer/Dikte.iss` içine `CloseApplications=yes` eklendi; `dikte_ai` modunda sağ panelin boş tıklama yutması `pointer-events: none;` ile çözüldü; `update_rollback(target, installer_url, sha256)` 3 argümanlı API çağrısı senkronize edildi.
  - **Test Durumu:** **343 passed, 1 skipped** (46.74 sn).
  - **Tek Kopya Kilidi (Single Instance Mutex):** `dikte/instance.py` eklendi; Windows Named Mutex (`Local\DikteSingleInstanceMutex`) ile uygulamanın aynı anda birden fazla açılması ve çift sistem tepsisi ikonu oluşturması engellendi. İkinci kopya açıldığında mevcut pencereyi Win32 API (`SW_RESTORE` + `SetForegroundWindow`) ile öne getirip sessizce kapanır (`tests/test_single_instance.py`, 9 test).
  - **Sistem Tepsisi Singleton Kilidi:** `dikte/tray.py` içine modül düzeyi singleton kilidi (`_tray_lock` + `_active_tray_manager`) eklendi, mükerrer tepsi ikonları tamamen önlendi.
  - **Pencere ve Görev Çubuğu İkonu (Win32):** Görev çubuğunda ve pencere başlığında varsayılan Python logosu yerine `assets/icon.ico` görünmesi sağlandı; `SetCurrentProcessExplicitAppUserModelID("Dikte.VoxNoteAI.1.6")` ve Win32 `LoadImageW` + `WM_SETICON` (`ICON_SMALL` ve `ICON_BIG`) pencere ikonu izleyicisi (`start_window_icon_watcher`) entegre edildi.
  - **Birebir Mikrofon Morph Animasyonu & 48 Bar Dalga:** `design/mikrofon_morph_animasyonu.html` dosyasındaki 48 barlık ses dalgası, konsantrik halo halkaları ve kırmızı durdur karesine dönüşen morph animasyonu yorum katılmadan birebir `dikte/ui/index.html`, `dikte/ui/style.css` ve `dikte/ui/app.js` içine taşındı (`sampleCurveY` ve sekme geçişinde `resizeWaveCanvas` / ResizeObserver boyutu düzeltildi).
  - **Sade Dikte.AI ve Klasik Magic UI Geçişi:** `dikte_ai` modunda tek sütunlu ferah düzen, üstte `● Model` rozeti, gizli sağ panel ve alt çubuk; `classic` modunda 2 sütunlu sağ panel, alt çubuk, DotPattern ve MagicCard yapısı tam ayrıştırıldı.
  - **Ayarlar Anında Kayıt ve Etkinlik Tekilleştirme:** Ayarlar sayfasındaki tüm kontroller anında otomatik kayda (`triggerInstantSettingsSave`) bağlandı ve "Son etkinlikler" listesindeki mükerrer `"Ayarlar kaydedildi"` satırları tekilleştirildi.
  - **Header ve UI İyileştirmeleri:** Sol üst köşedeki iç içe kutu görüntüsü temiz vektörel mikrofon SVG ikonu ile değiştirildi; sağ üstteki tema düğmesi `"Açık / Koyu"` pill butonuna dönüştürüldü.
  - **Test Durumu:** **320 passed, 1 skipped** (`tests/test_single_instance.py` 9 test, `tests/test_ui_fixes.py` 8 test; 45.42 sn).
- **Faz 3, Faz 4 ve Faz 5 tamamlandı (2026-11-12):**
  - **Yeni Logo & İkonlar:** `assets/icon.ico`, `dikte/ui/assets/icon.png` ve `installer/Dikte.ico` `design/download` baz alınarak Pillow ile üretildi; masaüstü kısayolu `C:\Users\aksek\Desktop\Dikte.lnk` güncellendi.
  - **Sistem Tepsisi (System Tray):** `dikte/tray.py` ile `pystray` + `Pillow` menüsü (Göster/Gizle, Dinleme Durumu, Çıkış); `--tray` ve `--minimized` sessiz başlatma bayrakları; pencere kapatıldığında tepsiye gizlenme ve arka planda global kısayol dinleme.
  - **Mikrofon Morfizmi & Ses Dalgası:** `design/mikrofon_morph_animasyonu.html`'deki `#waveCanvas` canvas ses dalgası ve morphing mikrofon düğmesi Dikte ekranına entegre edildi.
  - **Sidebar Katlama & Minimalist Görünüm:** Sol menü aç/kapa (daralma) desteği ve `sidebar_collapsed` ayarı; slogan ve rozet metin temizliği yapıldı.
  - **Tasarım Dili Seçimi:** Ayarlar → Görünüm'de varsayılan `Sade Dikte.AI` (`dikte_ai`) ve `Klasik Magic UI v1.4` (`classic`) seçeneği.
  - **1–3 Tuşlu Serbest Kısayol:** `dikte/hotkey.py` serbest kombinasyon yakalayıcısı (hotkey recorder, `Ctrl+Shift+D`, `Alt+Space` vb.) ve Ayarlar'da anında otomatik kaydetme.
  - **Hugging Face Özel Model Desteği:** `data/custom_models.json` ile hem Ses (HF repo ID) hem Metin (GGUF URL/HF) modelleri ekleme modalı (`#customModelModal`), kart "⋯" menüsü (Aktifleştir, Sil, Listeden Kaldır) ve ses modeli indirme iptali.
  - **Karşılama Sihirbazı (5 Adım):** `#welcomeWizard` (Hoş Geldiniz, Donanım/CUDA, Ses Modeli, Kısayol, Tamamlandı; `setup_done`).
  - **Güncelleme Rollback:** Ayarlar → Güncelleme kartında eski sürümlere tek tıkla geri dönme (`update_list_releases`, `update_rollback`).
  - **Selftest Sentetik Ses:** `tests/data/test.wav` (16 kHz mono WAV) ve `test.txt` üretildi; `python -m dikte --selftest --cpu` kodu 0 ile geçti.
  - **Test Süiti:** **303 passed, 1 skipped** (40.68 sn).
  - **Kurucu Paket:** `build.ps1` ile `installer\Output\Dikte-Setup-1.6.0.exe` (177.467.632 bayt, SHA-256: `74d92d7ff6ebced7b295769ed4e7c1a7aa6607ecc85d2c7324f31644ffe8bf31`) derlendi; `latest.json` güncellendi; `dist\Dikte\Dikte.exe --selftest --cpu` exit code 0 ile doğrulandı. Masaüstüne kopyalandı (`C:\Users\aksek\Desktop\Dikte-Setup-1.6.0.exe`).
- **v1.2 tamamlandı (2026-10-27):** Geçmiş, Modeller (6 ses modeli), Ayarlar ve "Transkripsiyonu Yenile" çalışıyor. Python 3.12.10; PyAV `>=11,<16`.
- **83 pytest testi geçti** (2026-11-01, 12,34 sn).
- **Gerçek GPU selftesti:** `large-v3 / cuda / float16`, model yükleme 7,3 sn; TTS test sesi çevrildi.
- **Gerçek model değiştirme ve indirme:** `large-v3 → tiny`, GPU float16; tiny silinip Hugging Face'ten yeniden indirildi (78.204.524 bayt).
- **Gerçek uygulama:** pywebview penceresi + model `ready`; çıkışta `%TEMP%\dikte\last.wav` silindi.
- **Arayüz:** 4 sayfa Playwright ile doğrulandı; `artifacts/ui-*.png`.
- **v1.2 elle testleri:** kullanıcı 2026-10-31'de "her şey çalışıyor" dedi (mikrofon, kısayol, geçmiş anahtarı).
- **Magic UI denemesi (2026-10-31):** `web/` altında Next.js 16 + shadcn + Magic UI (`AnimatedList`, `BentoGrid`, `AnimatedThemeToggler`); lint/build geçti, dev sunucu 200. Üretim arayüzü değil.
- **v1.3/v1.4/v1.5 kapsamları onaylandı (2026-11-01):** ayrıntı PLAN.md Aşama 7, 9, 10.
- **v1.3 / 7a tamamlandı (2026-11-01):** `secrets.py` (DPAPI), `openrouter.py` (ucuz filtre + önbellek), `text_engine.py` (prompt, yanıt temizleme, hata kodları), `cleaning` durumu, controller `clean_text`/`translate_text` + otomatik çevir, Dikte sayfasında çıktı dili/otomatik çevir/Temizle/Çevir, Ayarlar'da Yapay Zeka + Yapıştırma/Dil kartları.
- **Otomatik çeviri sağlamlaştırıldı (2026-11-01):** boş yanıtta token bütçesi büyütülüp tekrar, açıklama/tırnak temizleme, çıktı dili denetimi (tr/en/de), kısa metin halüsinasyon koruması; yönlendirici/muhakeme/negatif fiyatlı modeller öneri listesinden çıkarıldı. Gerçek test: 6/6 cümle geçti, ~$0,0001.
- **Metin modelleri eklendi (2026-11-01):** `text_models.py` ile 4 GGUF modeli (Qwen3 1.7B/4B, Gemma 3 4B, Llama 3.2 3B), `.part` + Range ile duraklat/devam/iptal, disk alanı kontrolü, Modeller sayfasında **Metin/Ses sekmeleri**, indirme/duraklat/iptal/aktifleştir/sil eylemleri ve ses↔metin bellek takası.
- **186 test geçti**; Playwright 15 test.
- **Otomatik yapıştırma eklendi (2026-11-01):** `paste.py` etkin pencereye Ctrl+V gönderir; Dikte penceresi etkinse atlar; `auto_paste` kapatılabilir.
- **Tema eklendi (2026-11-01):** sağ panelde "Aktif model" kartının üstünde yuvarlak düğme; AnimatedThemeToggler davranışı (View Transitions + circle clip-path, 400 ms); Ayarlar → Görünüm kartı (Sistem/Açık/Koyu); açık tema paleti. `artifacts/ui-tema-*.png`.
- **201 test geçti**; Playwright 17 test (alt ajanla doğrulandı, skip yok).
- **llama-cpp-python kuruldu (2026-11-03):** GPU whl (cu124) + `nvidia-cuda-runtime-cu12`; `cudart64_12.dll` eksiği `diagnostics` yoluna eklenerek çözüldü. Gemma 3 4B GGUF ile GPU yükleme 1,7 sn; üretim ~60 tok/s. `text_models.py` yükleme öncesi `prepare_cuda_dlls()` çağırıyor.
- **v1.4 Magic UI efektleri tamamlandı (2026-11-03):** MagicCard (fareyi izleyen kart ışığı), ShineBorder (işleme sırasında dönen kenar), AnimatedList (geçmiş/etkinlik satırlarının kademeli girişi), BentoGrid (Modeller sayfası üstünde 3'lü özet), DotPattern (Dikte zemininde nokta deseni). Ayarlar → Görünüm'de "Arayüz efektleri" anahtarı; prefers-reduced-motion desteği. Ekran görüntüleri design/v2/ altında (10 PNG).
- **206 test geçti** (2026-11-03); Playwright 23 test.
- **Gözden geçirme düzeltmeleri (2026-11-01):** tema ayarı AI yükünde döndürülüyor (Ayarlar'da sıfırlanmıyor), `refresh_last` ses modelini geri yüklüyor, ses modeli değiştirilirken yüklü metin modeli boşaltılıyor, OpenRouter'da model seçilmemişse açık hata, `.part` boyutu büyükse baştan indirme, `Content-Range` başlangıcı doğrulanıyor, açık tema sekme seçicisi düzeltildi.
- **Uygulama açılışı doğrulandı (2026-11-01):** `python -m dikte` penceresi açıldı (başlık `Dikte — VoxNote AI`), log: `Model hazır: Whisper Large | GPU | float16`; kapatınca süreç kapandı.
- **Denetim + doküman senkronu (2026-11-07):** `Dikte-Denetim-Raporu.md` kod satırlarıyla doğrulandı; testler **220 passed, 1 skipped** (41,08 sn); `uygulanacak plan.md` yeniden yazıldı; STATE/PLAN/AGENTS/architecture gerçek duruma çekildi. Kod değişmedi.
- **Faz 1 yayın hazırlığı tamamlandı (2026-11-09):** `config.APP_VERSION = "1.6.0"`, `sha256` akışı, `UPDATE_URL`, kaldırma temizliği ve `installer\Output\Dikte-Setup-1.6.0.exe` (172 MB) üretildi; 245 pytest geçti.
- **Faz 2 veri kaybı ve çökme hataları tamamlandı (2026-11-11):** `uygulanacak plan.md` §4'teki 11 maddenin tamamı TDD ile uygulandı; 18 yeni regresyon testi eklendi (**263 passed, 1 skipped**); `Model: "flash"` alt ajanıyla kod ve testler satır satır denetlendi. Masaüstüne `C:\Users\aksek\Desktop\Dikte.lnk` kısayolu oluşturuldu.

## Yarım kalan
- **Sihirbaz 2. adım CUDA indirme butonu:** `#wizardCudaActions` / `#wizardCudaMsg` yer tutucusu duruyor; isteğe bağlı CUDA indirme uç noktası henüz bağlı değil.
- **v1.7.0 kullanıcı yerel testi ve kurucu derlemesi:** Kullanıcının yeni özellikleri (Bas-Bırak, mikrofon seçimi, mini "Dinliyor" göstergesi) ve 4 HyperFrames videosunu yerel olarak onaylamasından sonra `APP_VERSION` `1.7.0`'a çıkarılıp `build.ps1` ile kurucu derlenecek.

## Sıradaki ilk adım
1. Kullanıcının `.venv\Scripts\python.exe -m dikte` ile Bas-Bırak, mikrofon seçimi ve odak çalmayan mini "Dinliyor/Yazıyor" göstergesini gerçek ortamda test etmesi; `video-hf/out/` içindeki 4 videoyu gözden geçirmesi.
2. Onay sonrası sürümü `1.7.0`'a çıkarıp `build.ps1` ile `Dikte-Setup-1.7.0.exe` derlemek ve isteğe bağlı `gh release` ile yayınlamak.

## Açık sorunlar
- **Kullanıcı Kabul Testi (Yeni Kurucu):** Yeni `Dikte-Setup-1.6.1.exe` (`onnxruntime` erken yükleme + VAD yedeği) ile gerçek bilgisayarda canlı konuşma ve kaldırma testi kullanıcı tarafından doğrulanacaktır.
- **Windows SmartScreen:** Kurucu dijital imzasız olduğu için ilk indirmede mavi uyarı çıkabilir (`README.md` ve sitede SHA-256 doğrulama adımı eklendi; orta vadede SignPath veya Microsoft Store değerlendirilebilir).
- **VRAM takası:** 8 GB'de ses + metin modeli aynı anda tutulmaz; bellek takas mantığı kodda hazır, kullanıcı gerçek donanımda ağır modellerle deneyebilir.
- **llama.cpp GPU hızı:** ilk üretim çağrısı CUDA başlatma yüzünden ~50 sn ısınma sürebilir; sonraki çağrılar ~60 tok/s hızındadır.

## Bu oturumda alınan kararlar (kullanıcı onaylı)
- Çıktı dili Türkçe/İngilizce/Almanca; "Otomatik çevir" kutusu dil seçicisinin yanında.
- "Yapay Zeka ile Temizle" ve "Çevir" butonları aynı satırda; aynı dilde yalnız temizlik, 3 kelimeden kısa metinde çeviri yok.
- Dil kararını metin modeli tek çağrıda verir; Whisper dili otomatik algılar.
- Metin modeli iki sağlayıcı: uygulama içi GGUF (llama.cpp) ve OpenRouter. Anahtar Ayarlar'da, DPAPI ile şifreli; ucuz/küçük modeller; sistem promptu düzenlenebilir.
- Ses ve metin modeli aynı anda bellekte tutulmaz; VRAM veya CPU/RAM'de takasla çalışır.
- Modeller sayfası Metin/Ses sekmeleri; her modelde "⋯" menüsü; indirmede duraklat/devam/iptal.
- Kısayol arka planda çalışır; sonuç panoya + etkin pencereye otomatik yapıştırılır.
- v1.4: Magic UI esintili CSS/JS uyarlaması; karanlık mod Sistem/Açık/Koyu.
- v1.5: PyInstaller + Inno Setup kurucu; veriler `%LOCALAPPDATA%\Dikte`; çift onaylı kaldırma.
- v1.6: Otomatik güncelleme (açılışta sessiz denetim + Ayarlar'da "Uygulamayı Güncelle"); `latest.json` → SHA-256 doğrulama → sessiz kurulum → yeniden açılış.
- OpenRouter API anahtarı Ayarlar sayfasında ayrı alan (gizli yazı, Kaydet/Sil/Test et), DPAPI ile şifreli.
- Metin sağlayıcısı varsayılanı `none` (kapalı); kullanıcı seçmeden Temizle/Çevir çalışmaz.
- Otomatik yapıştırma varsayılan açık; kurucu tek CPU paketi.
- Tema düğmesi sağ panelde "Aktif model" kartının 12 px üstünde; AnimatedThemeToggler (circle, 400 ms).
- Denetimde 4 salt-okunur alt ajan ana ajanla aynı modeli kullanır; plan/denetim dışında tek ajan çalışır.
- Goal bölünmesi: parti 1–5, sonra 6–10, sonra 11–13.
- OpenRouter'da "Tüm modelleri göster" açılınca katalogdaki herhangi bir model aranıp seçilebilir; varsayılan liste ucuz/küçük modellerdir.
- v1.6 yayın yeri **GitHub Releases** olarak seçildi (2026-11-04); `UPDATE_URL` henüz doldurulmadı. Açık tema paleti 2026-11-01'de onaylandı.
- Metin modelleri: 4 GGUF modeli (`qwen3-1.7b`, `qwen3-4b`, `gemma3-4b`, `llama32-3b`), Hugging Face'ten `.part` + Range ile indirme, duraklat/devam/iptal, disk kontrolü.
- Modeller sayfası Metin/Ses sekmeleri; metin modelinde indir/duraklat/iptal/aktifleştir/sil.
- Bellek takası: dikte başlarken metin modeli boşaltılır, ses modeli geri yüklenir.
- Otomatik yapıştırma: etkin pencereye Ctrl+V; Dikte penceresi etkinse atlanır; varsayılan açık.
- Tema: düğme sağ panelde "Aktif model" kartının üstünde; Ayarlar → Görünüm (Sistem/Açık/Koyu); açık tema paleti onaylandı.
- 2026-11-03: AGENTS.md'den alt ajanlar bölümü silindi (artık tek ajan çalışır).
- 2026-11-07: **Plan/denetim düzeni zorunlu:** `calisma-duzeni.md` sırası (keşif → doküman → 4 paralel salt-okunur alt ajan → sentez → rapor → doğrulama) uygulanır; bulgular `dosya:satır` kanıtıyla yazılır. Denetim dışında tek ajan çalışır.
- 2026-11-04: v1.4 efektleri kullanıcı tarafından gözle onaylandı; v1.5 karşılama sihirbazı kurucu kapsamına alındı.
- 2026-11-07: Bu oturumda **yalnız doküman/plan** yapıldı; eski `uygulanacak plan.md` silinip denetim + doğrulanmış kod durumuna göre yeniden yazıldı. Kod değişmedi.
- 2026-11-07: **Kurulum:** Program Files + `PrivilegesRequired=admin`; **sürüm 1.6.0**; kaldırmada kullanıcı seçer (Inno `[UninstallDelete]` + "Modelleri koru" bayrağı); PyInstaller + Inno Setup kurulacak.
- 2026-11-07: **Yayın:** GitHub Releases; `latest.json` + kurucu yüklemeyi kullanıcı yapar; `UPDATE_URL` Releases `latest/download` yolu. **Sihirbaz:** CUDA yalnız GPU varsa. **Selftest:** sentetik TTS. **7e:** tamamlanacak. **web/:** notla tutulur. **Lisans:** MIT. **İkon:** basit `.ico` üretilir. **Eski `data/`:** taşınmaz, temiz başlangıç.
- 2026-11-11: **Faz 1 testi:** Kullanıcı önce `installer\Output\Dikte-Setup-1.6.0.exe` ile kurulum ve kaldırma testini yapacak. Yeni sekmede `/asama-baslat` ile başlanacak; model ne yapacağını/yapmayacağını, testleri ve alt ajan kurallarını detaylı listeleyecek, kullanıcı onay vermeden kod yazmayacak.
- 2026-11-11: **Faz 2 düzeni:** 11 veri kaybı ve çökme maddesi tek seferde arka arkaya uygulanacak.
- 2026-11-11: **Karşılama sihirbazı CUDA:** İsteğe bağlı olacak ("İndir" veya "CPU ile devam et / Atla").
- 2026-11-11: **Ses modeli indirme:** faster-whisper için yalnız "İptal" butonu eklenecek.
- 2026-11-11: **Selftest sesi:** 3 saniyelik sentetik Türkçe ses ("Dikte test kaydı başarılı.") ve `test.txt` üretilecek.
- 2026-11-11: **Alt ajan (sub-agent) kuralı:** Alt ajanlar daima `gemini-3.8-flash-medium` (`Model: "flash"`) ile çağrılacak. Kolay ama uzun kodlama görevlerinde ve test koşumlarında kullanılacak; aşama bitiminde modellerin yaptıklarını/yapmadıklarını denetleyip ana ajana raporlayacak.
- 2026-11-11: **Faz 2 tamamlandı:** 11 veri kaybı ve çökme maddesi TDD ile tek seferde uygulandı ve `Model: "flash"` alt ajanıyla denetlendi (**263 passed, 1 skipped**).
- 2026-11-11: **Masaüstü kısayolu ve sistem tepsisi:** Masaüstüne `Dikte.lnk` kısayolu eklendi; uygulamanın sistem tepsisine (System Tray) küçültülmesi ve pencere kapalıyken arka planda çalışması Faz 3.2 kapsamına alındı.
- 2026-11-12: **belirsizleri-sor Nihai Kararları:**
  - **Varsayılan Tasarım:** Varsayılan arayüz modeli `Sade Dikte.AI + Mikrofon Morph` (`design_style = "dikte_ai"` varsayılan; Ayarlar → Görünüm'den `"classic"` Magic UI v1.4 seçilebilir; her iki modda da mikrofon alanında `design/mikrofon_morph_animasyonu.html` canvas dalga + morphing mikrofon yer alır).
  - **Hugging Face Özel Modeller:** `data/custom_models.json` dosyasında kalıcı saklanır; model kartında "Sil" denildiğinde diskteki model dosyası silinir ama kart listede kalır, kartın "⋯" menüsünde ayrıca "Listeden Kaldır" seçeneği bulunur.
  - **Faz 5.2 Kapsamı ve Dağıtım:** Bu oturumda tüm kodlar yazılıp `build.ps1` ile güncel `Dikte-Setup-1.6.0.exe` derlenecek; sentetik test sesi (`tests/data/test.wav` + `test.txt`) ile selftest ve paketli açılış testi otomatik doğrulanacak; gerçek VM testi ve GitHub Release yüklemesi kullanıcıya bırakılacak.
  - **Ajan Kararları (İkon & Tepsi):** Logo kaynağı `design/download` (ses dalgalı mavi ikon) alınıp `.ico` ve `.png` üretilir; sistem tepsisi `pystray + Pillow` ile kurulur; tepsi menüsü `Göster/Gizle | Durum | Çıkış` olur.
- **2026-11-20 (Tanıtım Videosu):** `video/` altında 45 sn 1080p 7 sahneli Remotion tanıtım videosu üretildi; `docs/assets/dikte-tanitim.mp4` (`+faststart`, `9,18 MB`) + kapak görseli GitHub Pages (`docs/index.html`) ve `README.md` alt bölümüne eklendi; `video/node_modules`, `.remotion`, `out/`, `public/sfx/` `.gitignore` ile hariç tutuldu.
- **2026-11-21 (Çok Dilli Vitrin — EN / TR):** GitHub depo ana sayfası (`README.md`) varsayılan İngilizce, Türkçe sürümü `README.tr.md` ve üstlerinde karşılıklı tıklanabilir `English | Türkçe` bağlantıları olacak şekilde ayrıldı; `docs/index.html` varsayılan İngilizce yapılıp üst çubuğa `EN | TR` dil seçici eklendi.
- **2026-11-24 (Kod Denetimi ve `asama-baslat` Güncellemesi):** v1.6.1 kodu salt-okunur tam denetimden geçirildi (`reports/2026-11-24-kod-denetimi-raporu.md`); `asama-baslat` skill'ine önceki oturumlar için **Obsidian MCP kontrolü** ve alt aşamalar/işçiler için değiştirilebilir düşünme seviyeli **Gemini 4 Hydrogen** (`low`/`medium`/`high`/`xhigh`) kuralı eklendi.
- **2026-11-25 (Sade Yayın & Tanıtım Araştırması):** Gelir amacı güdülmüyor; ~1.000 kullanıcı/indirme yeterli, süre sınırı ve abartılı büyüme kampanyası yok. Bu oturumda yalnızca araştırma yapılıp rapor (`reports/2026-11-25-yayin-ve-buyume-raporu.md`) ve Obsidian notu kaydedildi; uygulama koduna dokunulmadı.
- **2026-11-26 (Swarm ile Faz 1–4, 5 Dokunuş, Vitrin ve 4 HyperFrames Videosu):** Kullanıcı v1.6.1 testlerini tamamladı; Swarm onayıyla Kod Denetimi Faz 1–4, genele hitap eden 5 dokunuş (Bas-Bırak, mikrofon seçimi, mini "Dinliyor/Yazıyor" göstergesi, Gelişmiş Ayarlar), vitrin/OG kartı yenilemesi ve HyperFrames ile 4 tanıtım videosu (Yatay 16:9 50s TR/EN + Shorts 9:16 30s TR/EN + web EN/TR kopyaları) tamamlandı. `v1.7.0` kurucu derlemesi kullanıcının yerel testinden sonraya bırakıldı.

## Test durumu
| Test | Sonuç |
| :--- | :--- |
| `pytest -q` | **465 passed, 1 skipped** (2026-11-26 doğrulandı, 77,17 sn) |
| HyperFrames 4 video + 2 web MP4 (`ffprobe`) | **Geçti:** `dikte-yatay-tr/en.mp4` (`1920×1080`, `50s`), `dikte-shorts-tr/en.mp4` (`1080×1920`, `30s`), `docs/assets/dikte-tanitim-tr/en.mp4` (`+faststart`, `h264+aac`) |
| GitHub Pages EN/TR & video geçişi | **Geçti:** Playwright Edge `1440×900`, `768×1024`, `360×800` × EN & TR (`overflow: False`, `0` hata, `og-card.png` 200, dil bazlı MP4/poster 200) |
| Remotion TypeScript (`tsc --noEmit`) | **Geçti** (exit 0, 2026-11-20) |
| Tanıtım videosu render & `ffprobe` | **Geçti:** `video/out/dikte-tanitim.mp4` (`18,6 MB`) ve web MP4 `docs/assets/dikte-tanitim.mp4` (`9,18 MB`, `h264 1920x1080 30fps + aac, 45.013s`), 15 kontrol karesi incelendi |
| GitHub Pages video & responsive | **Geçti:** Playwright `1440x900`, `768x1024`, `360x800` `overflow: False`, `#promoVideo` + `mp4_http=200` (2026-11-20) |
| Kurucu (build.ps1) | **Üretildi ve yayınlandı:** `installer\Output\Dikte-Setup-1.6.1.exe`, 178.553.401 bayt, SHA-256 `953e4f5c0f3599a09c8880efd546334e17a9535883938c0bf59967efe55f3dfd` |
| Paketli açılış | `dist\Dikte\Dikte.exe --selftest --cpu` başarıyla çalıştı (`PKG_EXIT=0`, Silero VAD + Whisper Small CPU) |
| GitHub Release & Pages | **Yayında:** `v1.6.1` (`Dikte-Setup-1.6.1.exe` + `latest.json`) ve `https://mete2012seker-lgtm.github.io/dikte/` (Playwright masaüstü/tablet/telefon `overflow: False`) |
| `--selftest` | **Çalışıyor:** `tests/data/test.wav` (16 kHz mono WAV) ve `test.txt` hazır; kod 0 ile geçti |
| Gerçek model aktifleştirme | large-v3 → tiny, GPU float16, ready |
| pywebview gerçek uygulama | Pencere + model + ready |
| Playwright arayüz | 4 sayfa + Karşılama Sihirbazı + HF Model modalı + Rollback + Wave Canvas (34 test) |
| llama.cpp gerçek GGUF (2026-11-03) | gemma3-4b GPU yükleme 1,7 sn; üretim ~60 tok/s; ilk çağrı ~50 sn CUDA ısınması |
| v1.4 efektler | Playwright: efekt anahtarı, `fx-on`, shine geçişi, liste gecikmeleri, bento, nokta deseni, kart ışığı — 6 test; ekran görüntüleri `design/v2/*.png` |
| Gerçek mikrofon / kısayol / pano | Kullanıcı test etti (2026-10-31) |
| Gerçek model indirme | tiny silindi + yeniden indirildi (78,2 MB) |
| v1.3 metin motoru (sahte sunucu) | 201 testin içinde: secrets 7, settings +10, openrouter 17, text_engine 27, controller AI 31, text_models 12, paste 5 |
| Metin modeli indirme (sahte HTTP sunucusu) | Range ile devam, duraklat, iptal, 404, silme — 10 test |
| Otomatik yapıştırma | Kendi pencereyi atlama, kapalı ayar, hata — 5 test |
| Tema | Playwright: düğme sınıf değişimi + Ayarlar segmenti; `artifacts/ui-tema-*.png` |
| Gerçek uygulama açılışı | Pencere `Dikte — VoxNote AI`, model GPU float16 hazır |
| v1.3 OpenRouter gerçek çağrı | 6 cümle geçti (gemma-3-4b-it, ~$0,0001); düzeltmeler `reports/2026-11-01-openrouter-gercek-test.md` |
| Derleme araçları | **Hazır:** PyInstaller 6.22.3 ve Inno Setup 6; `build.ps1` tek komutla kurucu derliyor |
| Kurulum / kaldırma | Kod + iss + spec hazır; `keep_models.flag` desteği; temiz VM kullanıcı testi bekliyor |
| Güncelleme (v1.6) | `updater.py` liste/rollback/sha256 desteği tam; `latest.json` güncellendi |

## Çalıştırma komutları
```powershell
.venv\Scripts\python.exe -m dikte                 # uygulamayı aç
.venv\Scripts\python.exe -m dikte --selftest      # motor testi
.venv\Scripts\python.exe -m dikte --kurulum       # GPU testi + varsayılan modelleri indir
.venv\Scripts\python.exe -m dikte --dikte-testi   # arayüzsüz kısayol/kayıt/pano testi
.venv\Scripts\python.exe -m pytest -q             # testler
```

## Maliyet günlüğü (OpenRouter Activity'den kullanıcı dolduracak)
| Tarih | Aşama | Toplam harcama |
| :--- | :--- | :--- |
| 2026-11-01 | 7a gerçek çağrı + model karşılaştırması (6 + 9 istek) | tahmini ~$0,001 — **OpenRouter Activity'den doğrula** |

