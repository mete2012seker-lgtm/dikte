# Dikte — OpenWhispr Araştırması, Gömülü Hata Tespit Aracı ve Mimari/Stabilite Raporu

**Tarih:** 2026-11-18  
**Yöntem:** `/swarm` (4 paralel `Gemini 4 Hydrogen (Medium)` ajanı: `openwhispr-research`, `diagnostics-design`, `arch-auditor`, `stability-advisor` + `monitor`) — salt-okunur araştırma ve çapraz doğrulama  
**Kapsam:** `https://github.com/OpenWhispr/openwhispr` karşılaştırması, uygulama içi hata tespit/log kopyalama aracı tasarımı, `dikte/` ve `dikte/ui/` mimari/mantıksal denetimi, öncelikli stabilite yol haritası.

---

## 0. Özet — En Kritik Bulgular (Doğrulanmış)

| # | Önem | Sorun | Yer |
| :--- | :--- | :--- | :--- |
| 1 | **Blocker** | `_local_process_text` ve `_transcribe_path` `_engine_lock` almadan model yükleyip boşaltıyor; eşzamanlı diktede C++ segfault / VRAM OOM riski | `dikte/controller.py:504-531, 2022-2039` |
| 2 | **Blocker** | `ai_cancel()` eski `ai-task` thread'ini beklemeden durumu `READY` yapıyor; eski `finally:` yeni görevi bozuyor, `_seq` artmıyor | `dikte/controller.py:1851-1915, 1976` |
| 3 | **Blocker** | `uninstall.run_uninstaller()` `None` döndüğü için `--uninstall` her zaman çıkış kodu `1` veriyor | `dikte/__main__.py:240-243`, `dikte/uninstall.py:110` |
| 4 | **Blocker** | `RotatingFileHandler`, `sys/threading.excepthook`, `faulthandler` ve çökme işaretçisi (`running.lock`) yok; sessiz çökmeler kayboluyor | `dikte/diagnostics.py:109-126`, `dikte/__main__.py:222-256` |
| 5 | **Yüksek** | `WH_KEYBOARD_LL` hook thread'inde doğrudan `recorder.start()` / `winsound.Beep()` çağrısı (~300 ms Hook timeout riski) + raw `key` ile takılı tuş | `dikte/hotkey.py:244-338`, `dikte/controller.py:367, 464` |
| 6 | **Yüksek** | `updater.apply()` kurucuyu başlattıktan sonra Dikte sürecini kapatmıyor; mutex/DLL kilidi sessiz güncellemeyi bozabilir + `update_cancel` etkisiz | `dikte/updater.py:319-328`, `dikte/controller.py:1603-1683` |
| 7 | **Yüksek** | `checkWelcomeWizard()` yalnızca Ayarlar sekmesine girilince çağrılıyor; ilk açılışta sihirbaz hiç görünmüyor | `dikte/ui/app.js:2161, 2833-2851` |
| 8 | **Yüksek** | `audio.py` `self._chunks` kilitsiz + maksimum süre sınırı yok; `text_models.py` `__closure__` hack'i her 1 MB'da `TypeError` üretiyor | `dikte/audio.py:52-55, 81-82, 105`, `dikte/text_models.py:474-480, 498` |

---

## 1. OpenWhispr Araştırması ve Dikte İçin Dersler (`openwhispr-research`)

> **Not:** OpenWhispr bulguları `openwhispr-research` ajanının GitHub/web araştırmasına dayanır; Dikte karşılaştırma referansları yerel dosyalarla doğrulanmıştır.

### 1.1 OpenWhispr Mimarisi
- **Yığın:** Electron 41+ (Main/Renderer/Preload + ONNX Utility Process), React 19, TypeScript, Tailwind CSS v4, `shadcn/ui`, `better-sqlite3`, OS keyring (`safeStorage`).
- **Ses & VAD:** `AudioContext` + `AnalyserNode` RMS enerji ölçümüyle otomatik mikrofon seçimi ("Auto best input"), Silero VAD parametre profilleri (`minSpeechDurationMs`, `minSilenceDurationMs`, `speechPadMs`) ve kuyruk sessizliği kırpma.
- **STT & LLM:** `whisper.cpp` / `whisper-server` + `sherpa-onnx` + BYOK bulut sağlayıcıları; yerel LLM için tek paylaşılan `llama-server` süreci (`/slots` kontrolü); Özel Sözlük (*Custom Dictionary*) ile terimlerin STT'ye ipucu olarak verilmesi.
- **Pano & UX:** Yapıştırma öncesi panoyu yedekleyip (`saveClipboard`) yapıştırma sonrası geri yükleme (`restoreClipboard`); iki pencere (ana kontrol paneli + odak çalmayan yüzen *Dictation Pill*); dikte sırasında **Auto-Pause Media**; `app.whenReady()` sonrası `debugLogger`.

### 1.2 Alınacak Dersler ve Kaçınılacak Tuzaklar
- **Alınacaklar:**
  1. **Pano Yedekleme/Geri Yükleme (`restore_clipboard`):** Dikte şu an metni kalıcı olarak panoya yazıp kullanıcının önceki panosunu eziyor; yapıştırmadan ~150-200 ms sonra önceki metni geri yüklemek günlük kullanımda büyük fark yaratır.
  2. **Özel Sözlük (`custom_dictionary`):** `dikte/engine.py:166-167` sabit Türkçe `initial_prompt` kullanıyor; kullanıcının eklediği özel isim/teknik terimleri `initial_prompt` ve `text_engine.py` istemine eklemek doğruluğu artırır.
  3. **Tepsi Modu İçin Odak Çalmayan Floating Pill:** Pencere gizliyken yalnız bip sesi yerine `WS_EX_NOACTIVATE` + `TOPMOST` mini durum kapsülü.
  4. **Mikrofon Seçimi + Canlı RMS Seviyesi + Akıllı Medya Duraklatma:** `sounddevice.query_devices()` seçimi, `AudioRecorder` callback'inden wave canvas'a gerçek RMS ses seviyesi ve aktif ses oturumu varsa duraklatan medya kontrolü.
- **Kaçınılacaklar:**
  1. Electron + harici ikili (`ffmpeg-static`, `whisper-server`, `llama-server`, `nircmd.exe`, `better-sqlite3`) şişkinliği; Dikte'nin tek süreçli `pywebview` + `faster-whisper` + `SendInput` mimarisi Windows'ta daha hafif ve deterministiktir.
  2. Tarayıcı tarafı `AudioContext` sızıntıları (OpenWhispr PR #1125); Dikte'nin `sounddevice.RawInputStream` yapısı korunup kilit eklenmelidir.
  3. Toplantı kaydı, diarization, mobil eşlikçi gibi odak dağıtan özellikler kapsam dışı tutulmalıdır.

---

## 2. Gömülü Hata Tespit ve Log Kopyalama Aracı Tasarımı (`diagnostics-design`)

### 2.1 Mevcut Boşluklar (Doğrulanmış)
- `dikte/diagnostics.py:109-126`: `FileHandler` döndürmesiz (sınırsız büyür); `sys.excepthook`, `threading.excepthook` ve `faulthandler` yok.
- `dikte/ui/bridge.py:197-228, 341-347`: `--noconsole` paketli uygulamada WebView2/pencere açılış hataları `print()` ile yazıldığı için kullanıcıya hiç görünmeden uygulama kapanır.
- `dikte/controller.py:253-260` & `dikte/engine.py:141-148`: CUDA DLL / bozuk model / PyAV gibi farklı nedenler genel `MSG_MODEL_MISSING` mesajına indirgeniyor.
- `dikte/ui/app.js:695-712`: `window.onerror` / `unhandledrejection` yok; backend hataları yalnız 2.9 sn'lik `toast` ile görünüp kayboluyor.

### 2.2 Önerilen Tasarım: `dikte/error_reporter.py`
1. **Otomatik Yakalama & Çökme Tespiti:**
   - `RotatingFileHandler(maxBytes=2MB, backupCount=3)`, `faulthandler` (`logs/native_crash.log`), `sys.excepthook` ve `threading.excepthook` (`DATA_DIR/last_crash.json`).
   - `DATA_DIR/running.lock`: Açılışta yazılır, temiz `shutdown()`'da silinir. Sonraki açılışta hâlâ duruyorsa önceki oturumun çöktüğü otomatik algılanır.
   - Başsız UI açılış hatasında `write_emergency_report()` + Windows `MessageBoxW` ile kullanıcıya Türkçe hata ve dosya yolu gösterilir.
2. **Gizlilik Korumalı Veri Toplama (Sanitizer):**
   - `history.json`, `secrets.json`, `last.wav` ve `Controller._latest` **asla** okunmaz.
   - `sk-or-v1-...`, `Bearer ...`, `api_key=...` → `***MASKELENDI***`; Windows kullanıcı adları (`C:\Users\<ad>`) → `C:\Users\<KULLANICI>` olarak temizlenir.
   - Sistem özeti (APP_VERSION, CUDA/GPU, PyAV `>=11,<16`, llama_cpp, sounddevice, pynput, pystray, webview), güvenli ayar özeti (whitelist) ve son ~120 log satırı toplanır.
3. **Kural Tabanlı Türkçe Sınıflandırıcı (`analyze_errors`):**
   - 10+ bilinen deseni (`cuda_dll_missing`, `pyav_incompatible`, `model_missing_or_corrupt`, `network_hf_ssl`, `mic_permission_or_device`, `hotkey_hook_failed`, `paste_uipi_blocked`, `llama_oom_or_missing`, `openrouter_auth_quota`, `webview2_missing`, `previous_crash` / `js_error`) **Düz Türkçe Açıklama + Adım Adım Çözüm Önerisi** olarak üretir.
4. **Arayüz & Tepsi Entegrasyonu:**
   - **Kalıcı Hata Bandı (`#diagBanner`):** Açılışta çökme/hata varsa tüm sayfalarda üstte görünür (`[Çözüm Önerilerini Gör]`, `[Hata Raporunu Kopyala]`, `[Kapat]`).
   - **Tanılama Modalı (`#diagModal`) & Ayarlar Kartı:** Sade Türkçe açıklama, çözüm adımları, bileşen rozetleri, temizlenmiş log önizlemesi, tek tıkla **`[Raporu Panoya Kopyala]`** ve **`[.txt Olarak Kaydet]`**.
   - **Tepsi Menüsü:** `"Tanılama Raporu Kopyala"` öğesi; **JS Hata Köprüsü:** `window.onerror` / `unhandledrejection` → `api.diagnostics_log_js_error()`.

---

## 3. Mimari, Yapısal ve Mantıksal Hatalar (`arch-auditor`)

### Blocker
1. **`dikte/controller.py:504-531, 2022-2039` (`_transcribe_path`, `_local_process_text`):** `_engine_lock` alınmadan Whisper/Llama yükleme-boşaltma yapılıyor; kısayolla eşzamanlı tetiklenirse `_llm = None` / VRAM OOM / C++ segfault oluşabilir. **Düzeltme:** Tüm motor erişimlerini tek kilit sırasıyla (`_engine_lock` → `_lock`) koru.
2. **`dikte/controller.py:1851-1915, 1895, 1976` (`ai_cancel`, `ai_start_task`, `_run_text`):** `ai_cancel()` eski `ai-task` bitmeden `READY` yapıyor; eski thread'in `finally:` bloğu yeni görevin `CLEANING` durumunu sıfırlayabiliyor. Ayrıca `_latest` güncellenirken `_seq` artmadığı için asenkron AI sonucu UI'ya yansımıyor. **Düzeltme:** `_ai_task_token` ile `finally:` izolasyonu + `_seq += 1` ve `_replace_last = True`.
3. **`dikte/__main__.py:240-243`, `dikte/uninstall.py:110`:** `run_uninstaller()` `None` döndüğü için `0 if None else 1` daima `1` döner; `UninstallError` yakalanmaz. **Düzeltme:** `try/except UninstallError` ile `0`/`1` döndür.

### Yüksek
4. **`dikte/controller.py` (2158 satır) & `dikte/ui/app.js` (2852 satır):** God-Object birikimi (15+ sorumluluk tek sınıfta/IIFE'de). **Düzeltme:** Servis sınıflarına ve JS modüllerine böl.
5. **`dikte/ui/app.js:2161, 2833-2851` (`checkWelcomeWizard`):** Yalnız `loadSettings()` içinde çağrıldığı için açılışta (`page-dikte`) sihirbaz hiç tetiklenmiyor; Adım 2 henüz yüklenmemiş `modelsState.device`'ı okuyor. **Düzeltme:** İlk `snapshot()` içinde kontrol et ve `api.wizard_status()` kullan.
6. **`dikte/ui/app.js:2171-2214` & `dikte/controller.py:1521-1528`:** Anında ayar kaydetme peş peşe `ai_settings_save` + `settings_save` gönderip çift yazma yarışı oluşturuyor; `autostart_set` hata verse bile `settings.json` güncelleniyor. **Düzeltme:** Tek atomik uçta birleştir, yan etki başarısızsa kaydetme.
7. **`dikte/controller.py:1603-1683`, `dikte/updater.py:319-328`, `dikte/ui/bridge.py:181-194`:** `update_apply()`/`update_rollback()` UI köprüsünü senkron blokluyor; `update_apply()` `cancel_event` geçirmiyor; `updater.apply()` kurucuyu başlatıp Dikte'yi kapatmıyor. **Düzeltme:** Arka plan thread'i + `cancel_event` + `apply()` sonrası temiz `shutdown()`.
8. **`dikte/hotkey.py:244-338`:** `_pressed_keys` ham `pynput` `key` nesnesiyle indeksleniyor (modifier ile `char` değişince bırakma eşleşmeyip tuş takılı kalabiliyor); `set_key()` stop/start arasında kilitsiz boşluk bırakıyor; hook thread'inde doğrudan `_on_press()`/_on_release() çağrılıyor. **Düzeltme:** Kanonik `vk`/`Key.name` anahtarı + yaşam döngüsü kilidi + kuyruk/worker thread devri.
9. **`dikte/text_models.py:474-480, 498` & `dikte/controller.py:1156`:** `on_progress(written)` tek argümanlı olduğu için `progress(written, effective_total)` her 1 MB'da `TypeError` ile fallback'e düşüyor ve `__closure__` hack'i kullanılıyor; özel modelde (`size_bytes == 0`) tam `.part` varsa HTTP 416 hatası oluşuyor. **Düzeltme:** İmzayı `on_progress(written, total=0)` yap, `__closure__`'ı kaldır, HTTP 416'yı yönet.

### Orta ve Düşük
10. **`dikte/tray.py:218-264`:** `_runner()` içinde `_is_running = False`, `update_icon()` ve `notify()` `_tray_lock` olmadan erişiyor.
11. **`dikte/ui/bridge.py:248-283, 311-319`:** Tepsi thread'inden doğrudan `window.show()/hide()/destroy()` ve çift `shutdown()`/`stop()`.
12. **`dikte/audio.py:52-55, 81-82, 105`:** PortAudio `callback` ile `stop()`/`cancel()` `self._chunks`'a kilitsiz erişiyor; cihaz kopması yalnız `debug` loglanıyor; maksimum süre sınırı yok.
13. **`dikte/controller.py:232, 319-336, 648-655, 955, 1734-1759`:** `motor-yukle`/`model-yukle` thread'leri saklanmıyor/join edilmiyor; `wizard_complete()` `set_key()` başarısız olsa da ayar yazıyor; `settings_save()` `active_model` değişince motoru yenilemiyor; `toggle_record()` `_whisper_loaded`'ı kilitsiz okuyor.
14. **`dikte/text_models.py:554-556`:** CPU fallback `Llama(...)` çağrısı `try/except` ile `TextModelError`'a sarılmamış.
15. **`dikte/uninstall.py:101-105` & `dikte/instance.py:163, 305-340`:** `winreg.OpenKey` `with` ile kapatılmıyor; `LoadImageW` sonrası eski `HICON` `DestroyIcon` ile bırakılmıyor; `find_dikte_window()` yalnızca başlık ön ekine bakıyor.
16. **`dikte/ui/app.js:557, 1767-1800, 2702-2704`:** `applyModel()` `cleaning` durumunu unuttuğu için "Model hazır: Hayır" gösteriyor; `loadRollbackReleases()` yinelenen `change` dinleyicisi ekliyor; `runAi()` senkron `clean_text` çağırıyor; `#resetSettingsBtn` otomatik kaydetme ile çelişen uyarı veriyor.

---

## 4. Öncelikli Stabilite Yol Haritası (`stability-advisor` Sentezi)

1. **Faz A — Acil Çökme ve Kilit Düzeltmeleri (Blocker):**
   - Tek kilit sırası (`_engine_lock` → `_lock`) + `unload()` içinde `gc.collect()` + `use_cpu_fallback()` öncesi `unload()`.
   - `ai_cancel()` için `_ai_task_token` + `_seq += 1`.
   - `hotkey.py` kanonik tuş anahtarı + hook thread'inden worker kuyruğuna devir (300 ms Windows hook timeout koruması).
   - `updater.apply()` sonrası temiz `shutdown()` + arka plan indirme + `cancel_event` + `--uninstall` çıkış kodu düzeltmesi.
2. **Faz B — Gömülü Hata Tespit ve Dayanıklılık (Kısa Vade):**
   - `dikte/error_reporter.py` (`RotatingFileHandler`, `faulthandler`, `sys/threading.excepthook`, `running.lock`, gizlilik maskelemesi, 10+ Türkçe çözüm kuralı, `#diagBanner`/`#diagModal`, tepsi kopyalama, `MessageBoxW`).
   - `audio.py` `threading.Lock` + akış kopma/overflow tespiti + azami kayıt süresi sınırı.
   - `tray.py` & `bridge.py` tepsi kilit/kapanış tekilleştirme.
   - İlk açılış sihirbazı, atomik tekil ayar kaydı ve `text_models.py` progress/416 düzeltmesi.
3. **Faz C — Mimari Sadeleştirme ve Sızıntı Temizliği (Orta Vade):**
   - Thread `join`, `winreg`/`HICON` handle temizliği, CPU fallback `TextModelError` sarmalama, `app.js` `cleaning` durumu ve listener tekilleştirme.
   - `Controller` ve `app.js` parçalanması (mevcut `Api` sözleşmesi korunarak).
4. **Faz D — OpenWhispr Kaynaklı Seçici UX İyileştirmeleri (Uzun Vade):**
   - Opsiyonel `restore_clipboard`, Özel Sözlük (`custom_dictionary` → `initial_prompt` + LLM), tepsi modu odak çalmayan `Floating Pill`, mikrofon seçimi + canlı RMS dalgası ve aktif ses oturumu denetimli `auto_pause_media`.
