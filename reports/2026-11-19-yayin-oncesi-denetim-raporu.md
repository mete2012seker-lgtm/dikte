# Dikte v1.6.1 — Yayın Öncesi Eksiklik, Hata ve İyileştirme Raporu

**Tarih:** 2026-11-19  
**İncelenen sürüm / commit:** `v1.6.1` (`57823d7`)  
**Kapsam:** Backend çekirdek, veri katmanı + tanılama, arayüz + JS↔Python köprüsü, paketleme/güncelleme/kaldırma ve doküman tutarlılığı  
**Yöntem:** `calisma-duzeni.md` — keşif → doküman okuma → 4 paralel salt-okunur swarm işçisi (`Gemini 4 Hydrogen Medium`) → sentez + satır düzeyinde çapraz doğrulama → doğrulama kontrolleri  
**Kısıt:** Salt okunur kod denetimi yapıldı; gerçek UAC ortamında kur/kaldır ve temiz Windows VM testi bu oturumda çalıştırılmadı.

---

## 0. Özet — Yayına Çıkmadan Önce Bunlar

| # | Önem | Sorun | Yer |
| :--- | :--- | :--- | :--- |
| 1 | **Blocker** | Otomatik güncelleme `WinError 740` ile çöker (admin kurucuyu UAC istemeden `Popen` ile açıyor) | `dikte/updater.py:325-329`, `installer/Dikte.iss:27` |
| 2 | **Blocker** | Uygulama içi kaldırma `WinError 740` ile çöker + `Dikte.exe` kendini kapatmaz | `dikte/uninstall.py:125-129`, `dikte/controller.py:1604-1611` |
| 3 | **Yüksek** | `download_installer(sha256=None)` SHA-256 kontrolünü sessizce atlıyor; rollback imzasız `.exe` çalıştırabiliyor | `dikte/updater.py:294-299`, `dikte/controller.py:1747-1748` |
| 4 | **Yüksek** | Karşılama Sihirbazı Adım 2 NVIDIA GPU'yu asla görmüyor (`has_gpu` vs `has_nvidia_gpu`) | `dikte/ui/app.js:2753`, `dikte/controller.py:1801` |
| 5 | **Yüksek** | Özel HF model eklemede `../` yol geçişi ve rastgele alan adı (host) engeli yok | `dikte/text_models.py:284-314`, `dikte/models.py:145-160` |
| 6 | **Yüksek** | `snapshot.ai` içinde `state` yok (test sahtesi bunu maskelemiş); buton kilitleri bozuluyor | `dikte/ui/app.js:1669`, `tests/test_ui.py:100` |
| 7 | **Yüksek** | `HotkeyListener` uyku/kilit ekranı ve otomatik yapıştırma sırasında takılı kalabiliyor | `dikte/hotkey.py:389-390`, `430-457` |
| 8 | **Yüksek** | `AudioRecorder` mikrofon çıkarıldığında hatayı yakalamıyor (`status.error` özelliği yok) | `dikte/audio.py:67-70` |
| 9 | **Yüksek** | Ses modelini `"auto"` moduna geri çevirmek bir sonraki yüklemede `WhisperModel("auto")` hatası verir | `dikte/controller.py:1472-1474`, `dikte/engine.py:48-55` |
| 10 | **Yüksek** | `updater.compare_versions` ön sürümleri (`1.6.1-rc1`) finalden büyük sanıyor; `list_releases` draft/prerelease ayırmıyor | `dikte/updater.py:44-61`, `121-174` |

---

## 1. Yayın Zinciri (Blocker ve Kritik Yayın Riskleri)

### 1.1. Otomatik güncelleme UAC (`WinError 740`) ile patlar — **Blocker**
- **Yer:** `dikte/updater.py:325-329` ve `installer/Dikte.iss:27`
- **Alıntı:**
  ```python
  subprocess.Popen(
      [str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
      cwd=str(path.parent),
      close_fds=True,
  )
  ```
- **Neden yanlış:** `Dikte.iss:27` `PrivilegesRequired=admin` tanımladığı için `Dikte-Setup-1.6.1.exe` yönetici yetkisi (`requireAdministrator`) ister. Normal kullanıcı yetkisiyle çalışan `Dikte.exe` içinden `subprocess.Popen` (`CreateProcess`) çağrıldığında Windows UAC penceresi açmaz, doğrudan `OSError: [WinError 740]` fırlatır. Üstelik `updater.apply()` `OSError` yakalamadığı için `controller.py:1703` (`except updater.UpdaterError`) bu hatayı tutamaz.
- **Düzeltme:** Windows'ta `ctypes.windll.shell32.ShellExecuteW(None, "runas", str(path), "/SILENT /SUPPRESSMSGBOXES /NORESTART", str(path.parent), 1)` kullan (`rc <= 32` ise `UpdaterError` fırlat) ve `Popen` yolunu `try/except OSError` ile sar.

### 1.2. Uygulama içi kaldırma hem `WinError 740` verir hem uygulamayı kapatmaz — **Blocker**
- **Yer:** `dikte/uninstall.py:125-129` ve `dikte/controller.py:1604-1611`
- **Alıntı:** `subprocess.Popen([str(path), "/SILENT", ...])` ve `return {"ok": True, "message": "Kaldırıcı başlatıldı"}`
- **Neden yanlış:** `C:\Program Files\Dikte\unins000.exe` de yönetici yetkisi gerektirir (`WinError 740`). Ayrıca `controller.uninstall()` başarılı olsa bile `self._schedule_exit_after_apply()` çağırmadığı için `Dikte.exe` açık kalır ve `{app}` ile `logs\dikte.log` dosyalarını kilitleyerek temiz kaldırmayı engeller.
- **Düzeltme:** `uninstall.run_uninstaller()` içinde Windows'ta `ShellExecuteW(..., "runas", ...)` kullan; `controller.uninstall()` başarılı olunca `self._schedule_exit_after_apply()` çağır.

### 1.3. SHA-256 doğrulama açığı + Rollback doğrulamasız `.exe` — **Yüksek**
- **Yer:** `dikte/updater.py:294-299` ve `dikte/controller.py:1747-1748`
- **Alıntı:**
  ```python
  if sha256:
      ...
  elif sha256 == "" and not allow_missing_sha256:
  ```
- **Neden yanlış:** `download_installer()` parametresi varsayılan `sha256: str | None = None`. `sha256=None` geldiğinde her iki dal da atlanır ve özet kontrolü yapılmadan kurucu döner. `update_rollback()` de sürüm notunda özet bulamazsa `allow_missing_sha256=True` geçirerek doğrulanmamış `.exe` çalıştırır.
- **Düzeltme:** `elif sha256 == "" and not allow_missing_sha256:` satırını `elif not allow_missing_sha256:` yap; `update_rollback()` içinde geçerli 64 karakterlik SHA-256 zorunlu kıl.

### 1.4. Semver karşılaştırma ve draft/prerelease filtresi — **Yüksek**
- **Yer:** `dikte/updater.py:44-61` ve `121-174`
- **Neden yanlış:** `digits = "".join(ch for ch in piece if ch.isdigit())` yüzünden `1.6.1-rc1` → `[1, 6, 11]` olarak ayrışır ve final `1.6.1`'den büyük sayılır. `list_releases()` ayrıca `draft` veya `prerelease` GitHub sürümlerini filtrelemez.
- **Düzeltme:** `major.minor.patch` sayısal başlangıcını ayırıp ön sürümleri finalin altında sırala; `list_releases()` içinde `draft`, `prerelease` ve `installer_url` olmayan öğeleri atla.

### 1.5. Yayın zincirindeki diğer Orta eksikler
- **`dikte/updater.py:230-237`:** `_validate_download_host` GitHub'ın yeni `release-assets.githubusercontent.com` alan adını kapsamıyor; eklenmeli.
- **`dikte/config.py:13`:** `UNINSTALL_REG_KEY` `Dikte_is1` olarak kalmış; `Dikte.iss:19` `AppId={{FAACF175-562C-4213-8E04-3A90AEA600AA}` kullandığı için kayıt `{FAACF175-562C-4213-8E04-3A90AEA600AA}_is1` anahtarına yazılır.
- **`installer/Dikte.iss:17-39`:** Kod imzalama (`SignTool`) ve WebView2 Runtime kurulu mu kontrolü yok. İmzasız kurucu Windows SmartScreen'de "Bilinmeyen yayımcı" engeli çıkarır; eski Windows 10 makinelerde WebView2 yoksa pencere açılmaz.
- **GitHub Release `v1.6.1`:** Henüz yayımlanmadığı için `UPDATE_URL` şu an 404 döner (`STATE.md:88`).

---

## 2. Hiç Yazılmamış / Yarım Kalan Özellikler

| Özellik | Durum | Yer |
| :--- | :--- | :--- |
| Asenkron AI temizleme/çeviri + İptal düğmesi | Köprüde (`clean_text_async`, `ai_cancel`) var ama `app.js:1772` hâlâ bloklayan senkron çağrı yapıyor | `dikte/ui/bridge.py:54-67`, `dikte/ui/app.js:1772` |
| Güncelleme ilerleme çubuğu ve İptal düğmesi | `update_cancel` köprüde var, `update_apply` senkron çalışıyor ve arayüzde iptal/ilerleme yok | `dikte/controller.py:1672`, `dikte/ui/bridge.py:195` |
| Güncelleme sürüm notları (`#updateNotes`) | HTML elemanı var ama `result.notes` hiç yazılmıyor | `dikte/ui/index.html:531` |
| `HotkeyListener.reset_state()` | Takılı tuş kurtarma fonksiyonu yazılmış ama yalnız `stop()`'ta çağrılıyor | `dikte/hotkey.py:430-446` |
| `text_engine.generate(provider="local")` | Hâlâ stub (`raise TextEngineError("local_missing")`); mantık `controller.py:2111`'de kopyalanmış | `dikte/text_engine.py:331-333` |
| Ayarları Sıfırla (`#resetSettingsBtn`) | Yalnız `hotkey` ve `save_history`'yi sıfırlıyor; tema, tasarım, AI ayarları kalıyor | `dikte/ui/app.js:2232` |
| Klasik alt çubuk düğmeleri (`data-coming`) | Mikrofon/Dil/İşleme Modu düğmeleri hâlâ "yakında" toast'u veriyor | `dikte/ui/index.html:631-635` |
| CI/CD iş akışı | `.github/workflows/` yok; her commit/PR'da otomatik `pytest` koşmuyor | Proje kökü |

---

## 3. Kritik / Yüksek Kod Hataları

### 3.1. Karşılama Sihirbazı Adım 2 NVIDIA GPU'yu hiç algılamıyor — **Yüksek**
- **Yer:** `dikte/ui/app.js:2753` vs `dikte/controller.py:1801`
- **Alıntı:** `const hasGpu = Boolean(st.has_gpu || st.device === "GPU");`
- **Neden yanlış:** Backend `has_nvidia_gpu` ve `cuda_ready` döndürüyor. JS `has_gpu` aradığı için RTX/NVIDIA kartlı kullanıcılara bile "NVIDIA ekran kartı bulunamadı" diyor.
- **Düzeltme:** `Boolean(st.has_nvidia_gpu || st.cuda_ready || st.has_gpu || st.device === "GPU")` yap.

### 3.2. `snapshot.ai.state` eksikliği (ve test maskesi) — **Yüksek**
- **Yer:** `dikte/ui/app.js:1669` ve `dikte/controller.py:779,1520`
- **Neden yanlış:** `Controller.snapshot()` içindeki `ai` sözlüğü `"state"` içermiyor. İlk açılışta `aiState.state` `"ready"` varsayıldığı için model yüklenirken veya kayıt/işleme sürerken Temizle/Çevir butonları açık kalabiliyor.
- **Düzeltme:** `applyAi(snapshot.ai, snapshot.state)` ile durum geçir veya `_ai_payload()` içine `"state"` ekle; `tests/test_ui.py:100`'deki yapay `copy.ai.state = copy.state` enjeksiyonunu kaldır.

### 3.3. Özel Hugging Face model eklemede Path Traversal ve Host açığı — **Yüksek**
- **Yer:** `dikte/text_models.py:284-314` (`text_model_path:108-109`) ve `dikte/models.py:145-160`
- **Neden yanlış:** `parsed.netloc` kontrol edilmiyor (herhangi bir sunucudan dosya indirilebilir) ve `filename` içinde `../`, `..\`, sürücü harfi engellenmiyor (`models_dir() / filename` ile klasör dışına yazma/silme riski).
- **Düzeltme:** Alan adını `huggingface.co` / `www.huggingface.co` ile sınırla; `repo` parçalarını `^[A-Za-z0-9_.-]+$` ile doğrula; `filename` içinde `/`, `\`, `:`, `..` reddet.

### 3.4. `AudioRecorder` mikrofon çıkarılmasını yakalamıyor — **Yüksek**
- **Yer:** `dikte/audio.py:67-70`
- **Alıntı:** `if getattr(status, "error", False):`
- **Neden yanlış:** `sounddevice.CallbackFlags` nesnesinin `.error` özelliği yoktur. Mikrofon çekildiğinde veya ses sürücüsü koptuğunda `_stream_error` hiç set edilmez, kayıt sessizce donar.
- **Düzeltme:** `status` bayraklarını doğru kontrol et ve son callback zaman damgasını (`_last_callback_at`) izleyerek akış donmasını yakala.

### 3.5. `HotkeyListener` takılı kalma ve `on_release` düşürme — **Yüksek**
- **Yer:** `dikte/hotkey.py:389-390` ve `430-457`
- **Neden yanlış:** (1) `send_ctrl_v()` ~100–300 ms sürerken kullanıcı kısayol tuşunu bırakırsa `_is_pasting()` filtresi gerçek `on_release`'i yutar, `_pressed` `True` kalır. (2) Windows uyku/uyanma, `Win+L` veya UAC ekranı `WM_KEYUP` olayını düşürür; `reset_state()` hiç çağrılmadığı için kısayol kilitlenir.
- **Düzeltme:** `self._pressed_keys` içindeki kullanıcı tuşlarının `on_release`'ini bastırma; yeni basışta `GetAsyncKeyState` ile fiziksel olarak basılı olmayan tuşları `_pressed_keys`'ten temizle.

### 3.6. `AUTO_MODEL` (`"auto"`) seçimi bir sonraki yüklemeyi bozar — **Yüksek**
- **Yer:** `dikte/controller.py:1472-1474` ve `dikte/engine.py:48-55`
- **Neden yanlış:** `engine.set_model("auto")` çağrıldığında `"auto"` truthy bir model adı gibi `select_plan()`'a gider ve sonraki yüklemede `WhisperModel("auto", ...)` çağrılıp hata verir.
- **Düzeltme:** `set_model()` ve `select_plan()` içinde `"auto"` değerini `None`'a çevir; `"auto"` seçilince yeniden yüklemeyi tetikle.

### 3.7. `ai_cancel()` kilit bırakmadan `READY` yapıyor — **Yüksek**
- **Yer:** `dikte/controller.py:1941-1948` ve `2128-2142`
- **Neden yanlış:** Yerel GGUF üretimi sürerken `ai_cancel()` durumu hemen `READY` yapar ama arka plan iş parçacığı `_engine_lock` + `_local_ai_lock` tutmaya devam eder; yeni dikte kilitlenir.
- **Düzeltme:** `LocalTextModel.generate()` içine iptal bayrağı (stopping criteria) aktar.

### 3.8. Windows'ta indirme iptali sırasında açık dosya kilidi yarışı — **Yüksek**
- **Yer:** `dikte/text_models.py:649-657` ve `dikte/models.py:505-515`
- **Neden yanlış:** `cancel_download()` çağrılan thread'de `.part`/klasörü silmeye çalışırken indirme thread'i dosyayı hâlâ açık tutuyor; Windows `PermissionError` yutulur ve yarım dosyalar diskte kalır.
- **Düzeltme:** Dosya/klasör temizliğini indirme thread'inin `finally` bloğuna (handle kapandıktan sonraya) taşı ve her indirme için ayrı `Event` kullan.

---

## 4. Orta ve Düşük Bulgular

### Orta
- **UIPI (Yönetici penceresine yapıştırma):** `dikte/paste.py:103-129,247-258` — Hedef pencere yöneticiyse `SendInput` sessizce başarısız olur ama uygulama `"Etkin pencereye yapıştırıldı"` yazar. Dönüş değerini/yükseltmeyi kontrol edip `"Yönetici penceresine yapıştırılamadı (Ctrl+V kullanın)"` bildir.
- **Pano kilidi tek atış:** `dikte/clipboard.py:16-24` — Windows Pano Geçmişi (`Win+V`) veya başka uygulama panoyu kilitlediğinde tek seferlik `pyperclip.copy` başarısız olur. 20–30 ms aralıkla 3 deneme ekle.
- **Native crash logu raporda görünmüyor:** `dikte/error_reporter.py:814-825` — `native_crash.log` okunuyor ama metin raporuna yazılmıyor (C++/CUDA/llama.cpp çökmeleri raporda kaybolur).
- **Log handler çakışması:** `dikte/diagnostics.py:114-116` — `if root.handlers: return` başka bir kütüphane önceden handler eklediyse `dikte.log` dosyasının hiç açılmamasına yol açar.
- **Başarısız güncellemede buton kilitli kalıyor:** `dikte/ui/app.js:2450-2464` — `#updateApplyBtn` hata/iptal dalında `btn.disabled = false` yapılmıyor.
- **Açılışta tema/tasarım/sidebar senkronu:** `dikte/ui/app.js:661-674` — `localStorage` boşsa (temiz kurulum) Ayarlar sayfası açılana kadar `settings.json`'daki `design_style`, `sidebar_collapsed`, `theme` uygulanmıyor.
- **Kısayol kaydedici (`Escape` ve hata kontrolü):** `dikte/ui/app.js:2592-2604,2644-2648` — `Escape` iptal etmek yerine kısayol olarak kaydediyor; `settings_save` başarısız olsa bile başarı toast'u gösteriliyor.
- **Metin modeli aktivasyonu UI thread'ini blokluyor:** `dikte/controller.py:1296-1333` — Çok GB'lık GGUF yüklemesi arka plan thread'ine alınmalı.
- **HTTP 206 `Content-Range` uyuşmazlığı:** `dikte/text_models.py:458-459` — `resume_from = 0` yapıp aynı 206 gövdesini `"wb"` ile yazmak `.part` dosyasını bozar; bağlantıyı kapatıp `Range`'siz yeniden başlatmalı.
- **Diğer orta bulgular:** `dikte/controller.py:1071-1085` (iptal edilen ses indirmesi `"error"` diye eziliyor), `dikte/controller.py:532` vs `1530` (`input_language` varsayılanı `"tr"` vs `"auto"`), `dikte/instance.py:303-336` (`HICON` GDI handle sızıntısı), `dikte/tray.py:69,85` (Pillow dosya kilidi), `dikte/history.py:173-175,189-192` (`_save` öncesi bellek mutasyonu ve tz-aware tarih), `dikte/text_engine.py:163-172` (`"değişiklik"` kelimesi çok satırlı diktede meta temizleyiciyi tetikleyebiliyor), `dikte/error_reporter.py:81-86` (sabit `.tmp` adı + `fsync` eksik), `dikte/ui/app.js:1037,1067,1305` (aktif model silme koruması eksik), `dikte/ui/app.js:2694-2714` (rollback hatasında `"info"` toast).

### Düşük
- `dikte/config.py:29` (`LOCALAPPDATA=""` koruması), `dikte/error_reporter.py:45-46,129-131` (boşluklu Windows kullanıcı adı maskelemesi + `native_crash.log` boyut sınırı), `dikte/audio.py:79-86` (600 sn dolunca otomatik durdurma), `dikte/controller.py:1785-1787` (`nvmlShutdown()` eksik), `dikte/ui/style.css:538` (tanımsız `--card-hover`), `dikte/ui/app.js:446-461,2325` (ölü `#waveLeft`/`#topLang` kodu), `#customModelModal` `Escape`/backdrop kapanışı ve `.model-dropdown` dışarı tıklama kapanışı.

---

## 5. Depo Hijyeni ve Doküman Çelişkileri

- **Doküman kayması:** `architecture.md:6,69,139,144` hâlâ `"UPDATE_URL boş, sürüm 1.3.0"`, `".kilo/skills/"`, `"Ses modeli indirmesinde iptal yok"` ve `"input_language bağlanmadı"` yazıyor; `PLAN.md:118` `"uygulama kapanmıyor"` diyor (oysa `updater.apply` kapanışı eklendi).
- **Kök dizinde kalıntılar:** `.kilo/`, `.claude/`, `Dikte-Denetim-Raporu.md`, `uygulanacak plan.md` gibi geçmiş plan/ajan klasörleri yayına açılacak public repoda temizlenmeli veya arşivlenmeli.
- **Gizli bilgi & sözdizimi doğrulaması:** `git grep` taramasında gerçek API anahtarı sızıntısı **yok**. Tüm 25 `dikte/*.py` dosyası `ast.parse` ile hatasız doğrulandı (`AST_OK: 25 files`).

---

## 6. Test Durumu ve Test Maskeleri

- **Mevcut testler (`STATE.md`):** 369 passed, 1 skipped (2026-11-18).
- **Tespit edilen test maskeleri (gerçek hataları gizleyen test sahteleri):**
  1. `tests/test_ui.py:100`: `snapshotCopy()` elle `copy.ai.state = copy.state` ekliyor → gerçek uygulamada `snapshot.ai` içinde `state` olmamasını gizliyor.
  2. `tests/test_ui.py:270`: `wizard_status` sahtesi `has_nvidia_gpu`/`cuda_ready` döndürmüyor ve Adım 2 GPU metnini doğrulamıyor → `app.js:2753` hatasını gizliyor.
- **Eksik test kapsamı:** Playwright testlerinde `#diagBanner`, `#diagModal`, `window.onerror` köprüsü, `#updateApplyBtn` hata sonrası kurtarma ve `customModelKind === "text"` akışı test edilmiyor.

---

## 7. Öncelikli Düzeltme ve Yayın Planı

| Faz | Süre | Kapsam | Kabul Ölçütü |
| :--- | :--- | :--- | :--- |
| **Faz 1 — Yayın Blockerları** | 1 gün | `updater.apply()` + `uninstall.run_uninstaller()` UAC (`ShellExecuteW "runas"`), `controller.uninstall()` kapanış, `download_installer` SHA-256 `None` düzeltmesi + rollback hash zorunluluğu, `UNINSTALL_REG_KEY` ve `release-assets.githubusercontent.com` | Normal kullanıcıdan güncelleme ve kaldırma UAC penceresiyle sorunsuz çalışır; `sha256=None` reddedilir |
| **Faz 2 — Yüksek Hatalar & Güvenlik** | 1–2 gün | Sihirbaz GPU anahtarı (`app.js:2753`), `snapshot.ai.state` + test maskesi temizliği, HF `netloc` + path traversal koruması, `hotkey.py` stuck-key/`on_release` düzeltmesi, `audio.py` akış hatası, `AUTO_MODEL` düzeltmesi, indirme iptal dosya kilidi | Tüm regresyon testleri geçer; NVIDIA GPU sihirbazda görünür; `../` URL/dosya reddedilir |
| **Faz 3 — Kullanıcı Deneyimi & Tanılama** | 1–2 gün | `paste.py` UIPI uyarısı, `clipboard.py` 3x yeniden deneme, `error_reporter.py` `native_crash_tail` + `diagnostics.py` handler kontrolü, `app.js` `#updateApplyBtn` + açılış tema/tasarım senkronu + `Escape` iptali | Yönetici penceresinde net uyarı; `native_crash.log` raporda görünür; temiz kurulumda ayarlar ilk açılışta uygulanır |
| **Faz 4 — Yayın & Dağıtım Hazırlığı** | 1 gün | `Dikte.iss` WebView2 kontrolü + isteğe bağlı `SignTool`, `.github/workflows/ci.yml`, `architecture.md`/`PLAN.md` senkronu, temiz Windows VM'de kur/güncelle/kaldır testi, GitHub Release `v1.6.2` yayını | Temiz Windows'ta kur→çalıştır→güncelle→kaldır testi 0 hata; GitHub Releases `latest.json` 200 OK |

---

## 8. Doğrulanamayanlar / Senin Test Etmen Gerekenler

- Gerçek UAC ortamında (standart kullanıcı → yönetici onayı) `Dikte-Setup-*.exe` kurulumu, uygulama içi otomatik güncelleme ve "Modelleri koru" açık/kapalı kaldırma testi.
- Temiz Windows 10/11 makinesinde (Edge WebView2, SmartScreen uyarısı, NVIDIA sürücülü ve sürücüsüz) ilk açılış ve Karşılama Sihirbazı testi.
- Gerçek mikrofonun kayıt sırasında çıkarılıp takılması, bilgisayar uyku/uyanma sonrası kısayol ve Yönetici olarak açılmış bir uygulamaya (örn. Yönetici Not Defteri / PowerShell) otomatik yapıştırma testi.
