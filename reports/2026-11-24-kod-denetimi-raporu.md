# Dikte — Kod Denetimi Raporu (hata, çelişki, çökme, kısaltma)

| Tarih | Commit | Kapsam | Yöntem | Kısıt |
|---|---|---|---|---|
| 2026-11-24 | `102cfc6` (temiz çalışma alanı) | `dikte/` (25 .py + ui), `installer/`, `Dikte.spec`, `tests/`, STATE/PLAN/architecture/README | `calisma-duzeni.md`: 4 paralel salt-okunur swarm işçisi (Gemini 4 Hydrogen Medium) + koordinatör sentezi + satır doğrulaması | Kod değiştirilmedi; uygulama/kurucu çalıştırılmadı |

**Başlangıç ölçüsü:** AST 25/25 dosya OK · `pytest -q` → **413 passed, 1 skipped** (100,4 sn).
**Koordinatörün bizzat satırdan doğruladıkları (✔):** Y1, Y2, Y3, Y4, Y6, O1, O2.

---

## 0. Özet — Önce Bunlar

| # | Önem | Sorun | Yer |
|---|---|---|---|
| Y1 ✔ | Yüksek | Yenileme sırasında ses modeli yeniden yüklenirse durum `READY` olur → işlem sürerken yeni kayıt başlatılabilir | `controller.py:287` |
| Y2 ✔ | Yüksek | Takılı tuş kurtarma, Sağ Ctrl dahil hiçbir özel tuşta çalışmıyor (`vk` hep `None`) | `hotkey.py:392` + `_canonical_key_id` |
| Y3 ✔ | Yüksek | Özel GGUF modelinde yarım inen dosya "tamamlandı" kabul ediliyor | `text_models.py:568-573` |
| Y4 ✔ | Yüksek | Ayarlar otomatik kaydı başarısız olsa da "kaydedildi" gibi davranıyor | `ui/app.js:2211-2218` |
| Y5 | Yüksek | 5 `await api.*` çağrısında try/catch veya `ok` kontrolü yok → yanlış "başarılı" mesajı / yakalanmamış hata | `ui/app.js:1115,1301,1352,1998,2022` |
| Y6 ✔ | Yüksek | Kaldırıcı `%TEMP%\dikte`'yi silmiyor (`{tmp}` Inno'nun kendi geçici klasörü); ~178 MB güncelleme kurucuları ve olası `last.wav` kalır | `installer/Dikte.iss:73` |
| O1 ✔ | Orta | `except TypeError` ikinci kez `run_app` çağırıyor; gerçek başlangıç hatasını gizliyor | `__main__.py:188-191` |
| O3 | Orta | Windows "Yüklü uygulamalar"dan kaldırmada modeller sorulmadan siliniyor (README aksini ima ediyor) | `Dikte.iss:93-94`, `README.md:80` |
| O4 | Orta | Uygulama tepsideyken arayüz 250 ms'de bir `snapshot()` ve 60 fps dalga animasyonu çalıştırmaya devam ediyor | `ui/app.js:726-735, 227-302` |

Blocker bulunamadı.

---

## 1. Yüksek Önemli Hatalar

**Y1 ✔ — Yenileme sırasında durum makinesi `READY`'ye kaçıyor**
`controller.py:283-287`
```python
with self._lock:
    self._info = info
    self._whisper_loaded = True
    self._error = None
    self._set_state(READY)
```
*Neden yanlış:* `refresh_last()` durumu `CLEANING` yapar (`:685`) ve `_transcribe_path()` → `_prepare_whisper()` → `load_engine()` zincirini çağırır. Yerel metin modeli kullanıldıysa ses modeli boşaltılmıştır (`:2152 _unload_whisper()`), bu yüzden yeniden yüklenir ve `load_engine` koşulsuz `READY` yazar. İşlem sürerken kullanıcı yeni kayıt başlatabilir. Ardından `_refresh_worker`'ın `finally` bloğu (`:741`) yeni kaydın `PROCESSING` durumunu da `READY`'ye çevirebilir.
*Düzeltme:* `:287`'de yalnız `if self._machine.state == LOADING: self._set_state(READY)`. `:741`'i `== CLEANING` yapıp yenileme görev jetonuyla koru.

**Y2 ✔ — Takılı tuş kurtarma modifiye tuşlarda ölü kod**
`hotkey.py` `_canonical_key_id`: `vk = getattr(key, "vk", None)`. pynput `Key.ctrl_r` gibi enum üyelerinde `vk` yoktur (`key.value.vk`'dedir), sonuç `("key", None, "ctrl_r")`.
`hotkey.py:392`: `if existing_id[0] == "key" and isinstance(existing_id[1], int):` hiçbir zaman doğru olmaz.
*Neden yanlış:* v1.6.1'de eklenen `GetAsyncKeyState` kurtarması varsayılan kısayol (Sağ Ctrl) ve tüm Alt/Shift/F tuşları için hiç çalışmıyor. "Kayıt bırakınca durmuyor" türü takılmalar geri gelebilir.
*Düzeltme:* `vk = getattr(key, "vk", None) or getattr(getattr(key, "value", None), "vk", None)`. Aynısını `key_to_tokens` için de yap. Gerçek `pynput.keyboard.Key` ile birim testi ekle.

**Y3 ✔ — Özel GGUF indirmesi yarım dosyayı kabul ediyor**
`text_models.py:516` `effective_total` sunucudan öğreniliyor, ama `:568` hâlâ eski `spec.size_bytes` (özel modelde 0) ile karşılaştırıyor:
```python
if spec.size_bytes > 0 and written != spec.size_bytes:
```
*Neden yanlış:* Bağlantı koparsa 1 KB'tan büyük, GGUF başlıklı yarım dosya son dosyanın yerine geçer. `.part` silindiği için devam ettirilemez, model yüklenince bozuk çıkar.
*Düzeltme:* `if effective_total > 0 and written != effective_total: raise ...` (`.part`'ı koru).

**Y4 ✔ — Ayarlar kaydı hatası gizleniyor**
`ui/app.js:2212-2217`: `settingsDirty = false` ve `#settingsDirty.hidden = true` `if (result.ok)` bloğunun **dışında**.
*Neden yanlış:* Kayıt/işleme sırasında backend `{ok:false}` döner. Kullanıcı ayarın kaydedildiğini sanır, değişiklik kaybolur.
*Düzeltme:* İki satırı `if` içine al, `else`'te `toast(result.message || "Ayarlar kaydedilemedi.", "warn")`.
*Test maskesi:* `tests/test_ui.py:174-178` stub'ı `settings_save` için her zaman `{ok:true}` döndürüyor.

**Y5 — Korumasız köprü çağrıları**
`ui/app.js:1115` (`text_models_remove_custom`), `:1301` (`models_cancel_download`), `:1352` (`models_remove_custom`), `:1998` (`openrouter_key_save`), `:2022` (`openrouter_key_delete`).
*Neden yanlış:* İlk üçü `res.ok`'a bakmadan "kaldırıldı/iptal edildi" toast'ı gösteriyor. Hiçbirinde try/catch yok, Python hatası `unhandledrejection` olarak tanılama bandına düşüyor.
*Düzeltme:* Ortak `callApi(name, ...args)` yardımcısı: try/catch + `ok` kontrolü + hata toast'ı.

**Y6 ✔ — Kaldırmada geçici klasör kalıyor**
`installer/Dikte.iss:73`: `Type: filesandordirs; Name: "{tmp}\dikte"`
*Neden yanlış:* Inno'da `{tmp}` kurulum/kaldırıcının kendi `is-XXXX.tmp` klasörüdür, Windows `%TEMP%` değildir. `updater` indirmeleri (`%TEMP%\dikte\guncelleme\Dikte-Setup-*.exe`, ~178 MB) ve çökme sonrası kalan `last.wav` hiç silinmez. Bu, gizlilik vaadiyle çelişiyor.
*Düzeltme:* `Name: "{%TEMP}\dikte"` (veya `{localappdata}\Temp\dikte`).

---

## 2. Orta Önemli Bulgular

### Çekirdek (controller / hotkey / audio / paste / instance)
- **orta ✔ | `__main__.py:188-191`** | `except TypeError: return run_app(controller, debug=debug)` | Başlangıçtaki her TypeError'ı yutup arayüzü ikinci kez başlatıyor; kök neden kayboluyor | Fallback'i kaldır (imza zaten `start_in_tray` içeriyor).
- **orta | `controller.py:1966`** | `ai_cancel()` `CLEANING`'i sahibine bakmadan `READY` yapıyor; `refresh_last` de `CLEANING` kullanıyor | `CLEANING` sahibini (`ai`/`refresh`) tut. Not: `ai_cancel` şu an arayüzden çağrılmıyor, yani hata gizli duruyor.
- **orta | `controller.py:485-507`** | `recorder.start/stop` ve `winsound.Beep(…, 80)` `self._lock` tutulurken çalışıyor | Her basışta snapshot/poll ~80 ms bloklanıyor | Bip'i kilidin dışına (veya daemon thread'e) taşı.
- **orta | `hotkey.py:345`** | `set_key()` dinleyici çalışmıyorken de `self.start()` çağırıyor (`:350`'deki `was_running` mantığıyla çelişkili) | `if was_running:` koşulu ekle.
- **orta | `controller.py:913`** | Ses modeli indirmesi iptal edilip hemen yeniden başlatılırsa ikinci `_download_worker` aynı klasöre yazar | Metin indirmesindeki gibi jeton + eski thread'i `join`.
- **orta | `controller.py:2160`** | `_local_process_text` denemeler arasında `_ai_cancel_event`'e bakmıyor | Her denemeden önce kontrol et.
- **orta | `controller.py:1847`** | `wizard_complete()` kısayolu kaydetmeden uyguluyor, kayıt hatasında geri almıyor (`settings_save` alıyor) | `settings_save`'deki geri alma desenini kullan.
- **orta | `controller.py:1347`** | `_text_runtime.model_name` kilitsiz okunuyor; `text_model_delete` yükleme sırasında aynı dosyayı silebilir | `LOADING` iken silmeyi reddet.
- **orta | `audio.py` / `controller.py:358`** | `shutdown()` `recorder.cancel()`'ı kilitsiz çağırıyor; `AudioRecorder`'ın start/stop/cancel'ında iç kilit yok | `AudioRecorder` içine `threading.Lock`.
- **orta | `paste.py:33`** | `_is_pasting` kilitsiz global; eşzamanlı iki yapıştırma Ctrl+V'leri karıştırabilir | Modül kilidi.
- **orta | `instance.py:84`** | `CreateMutexW` sonrası `kernel32.GetLastError()` güvenilir değil, tek kopya algılaması nadiren kaçabilir | `WinDLL("kernel32", use_last_error=True)` + `ctypes.get_last_error()`.

### Veri katmanı
- **orta | `models.py:337-380`, `text_models.py:339-384`** | `_CUSTOM_MODELS_LOCK` load ve save'de ayrı ayrı alınıyor, oku-değiştir-yaz bütün değil → eşzamanlı ekle/sil/boyut güncellemesinde kayıp | Kilidi tüm sıra boyunca tut (RLock).
- **orta | `models.py:114-116, 307`** | `custom_models.json`'da liste olmayan değer veya `name`'siz kayıt → `KeyError` ile model listesi çöker | Kayıtları doğrula, bozukları atla. Bozuk dosyayı yedekle (`low`, `:118`).
- **orta | `history.py:173-175` (+delete/update/clear)** | Önce `self._items` değişiyor, sonra `_save()`. Kayıt hata verirse bellek ile disk ayrışıyor | `SettingsStore.save` gibi önce aday listeyi kaydet, sonra işle.
- **orta | `text_models.py:534-552`** | İndirme döngüsünde `TimeoutError/ConnectionResetError/IncompleteRead` yakalanmıyor, ham hata yükseliyor | `TextModelError`'a çevir, `.part`'ı koru.
- **orta | `text_models.py:599-622`** | `LocalTextModel.load()` önce `unload()` çağırmıyor; iki model kısa süre VRAM'de kalabilir (8 GB'de OOM riski) | Başta `self.unload()`.
- **orta | `text_models.py:624-640`** | `create_chat_completion` hataları ham yükseliyor | `TextModelError`'a sar.
- **orta | `models.py:502-526`, `text_models.py:680-713`** | Eşzamanlı ikinci `download()` `_cancel_event/_pause_event`'i eziyor | Model başına olay veya "indirme sürüyor" reddi.
- **orta | `openrouter.py:45-48`** | 403 (iptal edilmiş anahtar) ve 400/404 (geçersiz model) "Sunucuya ulaşılamadı" olarak gösteriliyor | 403 → yetki, 400/404 → `bad_response`.
- **orta | `openrouter.py:188`** | Önbellek atomik yazılmıyor | Ortak atomik yazma yardımcısı (bkz. §4).
- **orta | `error_reporter.py:46`** | Kullanıcı adı maskesi tek `\` bekliyor; JSON/repr içindeki `C:\\Users\\ad` biçiminde **kullanıcı adı rapora sızıyor** | `\\+Users\\+` ile bir veya daha fazla ters bölü eşle.
- **orta | `error_reporter.py:593-604`** | "gguf" + "error" kelimeleri log kuyruğunun herhangi bir yerinde geçince kural 5 tetikleniyor, daha doğru kuralları (OOM, ağ, mikrofon) gölgeliyor | Aynı satırda eşle veya `llama_oom_or_missing`'i öne al.
- **orta | `error_reporter.py:143`** | `native_crash.log` sınırsız büyüyor | Açılışta 512 KB üstündeyse kırp.
- **orta | `diagnostics.py:25-29`** | `_cuda_prepared` kontrol-sonra-ata kilitsiz | `threading.Lock`.

### Arayüz
- **orta | `ui/app.js:2388, 2503`** | `#autostartSwitch` ve `#updateAutoSwitch` `saveAi()`'yi atlayıp doğrudan `api.ai_settings_save` çağırıyor; polling yarışı koruması devre dışı ve `aiState` güncellenmiyor | `saveAi(...)` üzerinden geçir.
- **orta | `ui/app.js:2865-2885`** | Sihirbaz bitişinde `settings_save` ve `wizard_complete` aynı anda `settings.json`'a yazıyor; hata `.catch(()=>{})` ile yutuluyor, pencere sonuç beklenmeden kapanıyor | `setDesignStyle(v,false)`, `await wizard_complete` + `ok` kontrolü.
- **orta | `ui/app.js:726-735, 227-302`** | Tepsideyken 250 ms poll + `requestAnimationFrame` sürüyor (pil/CPU) | `document.hidden`/`visibilitychange` ile durdur.
- **orta | `ui/app.js:1123-1127, 1360-1364`** | "⋯" menüsü dışarı tıklama veya Escape ile kapanmıyor | Tek `document` tıklama/Escape dinleyicisi.
- **orta | `ui/app.js:2529-2595`** | Özel model penceresi eski girdileri temizlemiyor, Escape veya arka plan tıklamasıyla kapanmıyor | Açılışta temizle, `#diagModal` gibi kapat.
- **orta | `ui/app.js:2259-2266`** | Genel "Sıfırla" düğmesi yalnız kısayol ve geçmiş anahtarını sıfırlıyor | Ya tümünü sıfırla ya da etiketi değiştir.
- **orta | `ui/app.js:1178-1181`** | Ses modeli aramasında seçim `visible` yerine `items` ile kontrol ediliyor; gizlenen model detayda kalıyor | `visible.some(...)`.
- **orta | `ui/app.js:1331-1341`** | Ses modeli "⋯ → Dosyayı Sil" aktif veya inen modelde devre dışı değil | `disabled = item.active \|\| item.downloading`.
- **orta | `ui/app.js:866-884`** | Geçmiş silmede 200 ms animasyon boyunca çift tıklama iki kez siliyor | Girişte `removing` kontrolü.
- **orta | `ui/app.js:2449-2496`** | Güncelleme notları (`#updateNotes`) hiç doldurulmuyor; başarıda da düğme etiketi sıfırlanıyor | Notları yaz, etiketi yalnız hatada sıfırla.
- **orta | `ui/app.js:2602-2612`** | `formatKeyLabel` Sağ/Sol Ctrl ayrımını kaybediyor | "Sağ Ctrl"/"Sol Ctrl" eşlemesi.

### Paketleme / güncelleme
- **orta | `Dikte.iss:93-94`, `README.md:80`** | Windows'tan kaldırmada `keep_models.flag` yazılmadığı için modeller (GB'larca) sorulmadan siliniyor | Inno `[Code]`'a soru ekle veya README'yi düzelt.
- **orta | `controller.py:1627-1639`** | `UPDATE_MESSAGES`'ta `cancelled`/`launch_failed` yok; iptal edince "Bağlantını kontrol et" çıkıyor | İki mesajı ekle.
- **orta | `controller.py:1708-1713, 1764-1774`** | `updater.download` zaten SHA-256 doğruluyor; controller 178 MB'ı ikinci kez hash'liyor | Gereksiz çağrıyı kaldır.
- **orta | `updater.py:249-262`** | `UPDATE_URL` boşsa host denetimi atlanıyor | Boş host'ta reddet (şu an URL dolu, risk düşük).
- **orta | `uninstall.py:86`** | Geliştirme modunda (`python -m dikte`) otomatik başlatma `python.exe --tray` yazıyor, bu geçersiz | `is_packaged()` değilse `-m dikte` ekle.
- **orta | `Dikte.iss:27, 58-62`** | `PrivilegesRequired=admin` + `HKCU`/`{localappdata}`: ayrı yönetici hesabıyla yükseltilirse yanlış profile yazılır | Varsayımı belgele veya otomatik başlatmayı uygulamaya bırak.

---

## 3. Düşük Önemli Bulgular
- `controller.py:1977` `ai_start_task` boş metni baştan reddetmiyor.
- `controller.py:849` `_models_cache/_memory_cache/_diag_cache` kilitsiz.
- `instance.py:305` `LoadImageW` HICON'ları `DestroyIcon` edilmiyor. `tray.py:256` `stop()` thread'i join etmiyor.
- `history.py:189-192` saat dilimli/dilimsiz tarih karşılaştırması TypeError verebilir.
- `text_models.py:355` `.GGUF` büyük harf uzantı etiketi bozuyor.
- `error_reporter.py:405,846` `hotkey_id` maskelenmiyor.
- `updater.py:291` bozuk `Content-Length` → yakalanmayan `ValueError`. `updater.py:131` varsayılan argüman import anında bağlanıyor.
- `__main__.py:118` `--selftest-dosya` özel WAV'da sabit `test.txt` ile karşılaştırıyor. `__main__.py:269` `sys.exit(0)` yerine `return 0`.
- `requirements.txt`: üst sınır yok; `onnxruntime` doğrudan import edildiği halde listede yok.
- `Dikte.spec:27` `tests/data` üretim kurucusuna giriyor (selftest için bilinçli; not edilmeli).
- `ui/index.html:194` sağ paneldeki "Dil: Türkçe" sabit yazılmış.
- `ui/app.js:1614` `handleDownloadNotice` `loadModels()`'u iki kez tetikliyor.

---

## 4. Kısaltma Fırsatları (tahmini ~500 satır)

| Alan | Yer | Yapılacak | ~Satır |
|---|---|---|---|
| Model kartı + "⋯" menüsü kopyası | `ui/app.js:951-1140` ↔ `1195-1375` | `buildModelCard()` + `buildModelMenu()` | 110 |
| Detay paneli kopyası | `ui/app.js:1385-1579` | `renderDetailPanel()` | 60 |
| Atomik yazma 6 kopya | `settings.py:213`, `history.py:128`, `models.py:123`, `secrets.py:142`, `error_reporter.py:82`, `openrouter.py:179` | Tek `atomic_write_json/text` (ör. `dikte/fsutil.py`) + `_backup_path` | 70 |
| Yerel AI yeniden deneme döngüsü kopyası | `controller.py:2132-2190` ↔ `text_engine.py:342-389` | Döngüyü `text_engine`'de tek yerde topla, `provider="local"` dalını bağla (`text_engine.py:331-333` şu an ölü `local_missing`) | 45 |
| Yenile/İşle hattı | `controller.py:581-647` ↔ `695-743` | `_run_transcription_pipeline()` | 30 |
| Güncelle/Geri al | `controller.py:1684-1721` ↔ `1745-1785` | `_download_and_apply_installer()` | 25 |
| `_launch_elevated` iki kopya | `updater.py:344-365` ↔ `uninstall.py:111-132` | Ortak yardımcı | 20 |
| HF URL/repo doğrulama | `models.py:146-169` ↔ `text_models.py:281-321` | Ortak doğrulayıcı | 15 |
| Özel model ekle/kaldır kalıbı | `controller.py:1100-1131, 1372-1402` | Ortak sarmalayıcı | 15 |
| Dil puanlama | `text_engine.py:220-227` ↔ `258-265` | `_language_scores()` | 10 |
| Ölü kod | `bridge.py:332-337 toggle_window`; JS `#waveLeft/#waveRight/#topLang` (`app.js:455-470, 2354`); kullanılmayan CSS (`.brand-img .brand-tag .soon .mic-wrap .theme-row .mb-ai`); SVG `i-logo i-folder`; `config.HOTKEY_LABEL`, `config.UNINSTALL_REG_KEY`; `settings.py` `HOTKEY_CHOICES` importu; `controller.py:23 HistoryError`; `audio._last_callback_at`; `TextModelManager._models_dir`; `__main__`/`run_dikte` çift `onnxruntime` bloğu; `Dikte.iss` `MyAppExeName` | Sil | 45 |
| Kullanılmayan köprü uçları | `bridge.py`: `window_hide_to_tray, ai_cancel, clean_text_async, translate_text_async, ai_start_task, ai_state, text_model_open_folder, autostart_set, update_cancel` (JS'ten çağrılmıyor) | Ya bağla (ör. AI iptal düğmesi) ya da sil | 30–60 |

---

## 5. Yarım Kalan / Hiç Bağlanmamış
- `text_engine.generate(provider="local")` her zaman `local_missing` atıyor; yerel akış controller'da ayrı yazılmış (bkz. §4).
- AI iptali (`ai_cancel`, `*_async`) backend'de var, arayüzde düğmesi yok.
- Sihirbaz 2. adımındaki `#wizardCudaActions/#wizardCudaMsg` (`index.html:761-763`) hiç güncellenmiyor; CUDA indirme uç noktası yok (AGENTS kararıyla çelişiyor: "İndir veya CPU ile devam et").
- Güncelleme sonrası otomatik yeniden açılış yok (`Dikte.iss:65-66 skipifsilent` + `updater.py:4`), ama AGENTS/STATE "sessiz kurulum → yeniden açılış" diyor.
- Pano geri yükleme yok: dikte metni yapıştırmadan sonra panoda kalıyor (OpenWhispr raporunda önerilmişti).
- `audio._last_callback_at` yazılıyor ama mikrofon takılma bekçisi yok.

## 6. Test Maskeleri
- **`engine.py:171-175`:** Üretim kodu `Mock` nesnesini algılayıp (`_mock_return_value`) `vad_parameters`/`initial_prompt`'u atlıyor. Testler gerçek çağrı argümanlarını hiç görmüyor. Üretim kodunda test dalı olmamalı.
- **`tests/test_text_models.py:211-213`:** Hem `config.MODELS_DIR` yamalanıyor hem `models_dir=` veriliyor. `TextModelManager`'ın `models_dir`'i yok saydığı gizleniyor.
- **`tests/test_ui.py:174-178`:** `settings_save` stub'ı hep `ok:true` döndürüyor, Y4'ü gizliyor. Stub sürümü hâlâ `"1.3.0"`.
- **`tests/test_ui_fixes.py:112-117`:** Dosyada `api.ai_settings_save` metni geçiyor mu diye bakıyor. Fonksiyon aslında `settings_save` çağırıyor ama test başka bir yerdeki eşleşme yüzünden geçiyor.
- **`tests/test_updater.py:156-177`:** Sahte controller'da `_update_cancel_event` ve `_schedule_exit_after_apply` yok, iptal ve kapanış yolları test edilmiyor.
- **`tests/test_uninstall.py:70-94`:** `FakeWinreg.OpenKey` kök/yol/erişim bayrağını kontrol etmiyor.
- **Y2 için:** Hotkey testleri gerçek `pynput.keyboard.Key` enum'u ile `GetAsyncKeyState` yolunu sınamıyor (aksi halde Y2 yakalanırdı).

## 7. Doküman Çelişkileri
- `STATE.md:98-104` "Yarım kalan": "⋯ menüsü yok", "latest.json 404", "Karşılama sihirbazı hiç yazılmadı". Üçü de artık yanlış.
- `PLAN.md:103,112` başlıkları "akış bozuk / yayın doğrulanmadı" diyor, oysa v1.6.1 yayında.
- `architecture.md:150-151` "GitHub Release yok", ekran görüntüleri `design/v2/` diyor. Gerçekte `artifacts/`.
- `STATE.md` sonu "370 test" diyor, başı "413".
- AGENTS/STATE "güncelleme sonrası yeniden açılış" diyor, kod yapmıyor (§5).
- `asama-baslat` skill'i ve `calisma-duzeni.md §10` alt ajan modeli olarak `gemini-3.8-flash-medium` yazıyor; AGENTS.md (2026-11-13) **Gemini 4 Hydrogen** diyor.

---

## 8. Öncelikli Düzeltme Planı

| Faz | İçerik | Kabul ölçütü | Süre |
|---|---|---|---|
| **1 — Çökme ve durum makinesi** | Y1, Y2, Y3; `ai_cancel`/refresh sahipliği; bip kilit dışı; `set_key` koşulu; history önce-kaydet; özel model kilidi + doğrulama; indirme ağ hataları; `LocalTextModel.load` unload; ses indirme jetonu | Her madde için önce kırmızı regresyon testi; gerçek `pynput.Key` testi; tam süit yeşil | 1 gün |
| **2 — Arayüz doğruluğu** | Y4, Y5 (`callApi` yardımcısı), `saveAi` yönlendirmesi, sihirbaz bitişi, menü/modal kapanışı, gizliyken poll/animasyon durdurma, çift silme, arama seçimi, güncelleme notları | Playwright: `ok:false` stub senaryoları, Escape/dışarı tıklama, `visibilitychange` | 1 gün |
| **3 — Yayın, gizlilik, kurucu** | Y6, Windows kaldırmada model sorusu, O1 (`TypeError`), `UPDATE_MESSAGES`, çift SHA, host denetimi, `error_reporter` regex, OpenRouter 403/404, dev otomatik başlatma, `onnxruntime` requirements | Birim testleri + `build.ps1` + paketli `--selftest` exit 0 + kullanıcı VM kur/kaldır testi | 1 gün |
| **4 — Kısaltma + test maskeleri + doküman** | §4 tablosu (atomik yazma yardımcısı, model kartı birleştirme, yerel AI döngüsü, ölü kod), §6 maskeleri, §7 doküman senkronu | Davranış değişmeden süit yeşil; satır sayısı ~-500 | 1–2 gün |

## 9. Doğrulanamayanlar / Notlar
- `secrets.py:66-68` `_blob()` ctypes tampon ömrü (use-after-free riski) çalışma anında doğrulanmadı.
- `faster_whisper.utils.download_model`'in yarıda iptali destekleyip desteklemediği kaynakta doğrulanmadı.
- `text_engine.py:245` 1–2 kelimelik Türkçe girdide "hallucination" yanlış pozitifi: AGENTS kuralı 3 kelimeden kısa metni çevirmediği için pratikte tetiklenmeyebilir. Doğrulanmadı.
- WebView2'de `pystray.stop()` + `window.destroy()` thread davranışı, `navigator.clipboard` izinleri, gerçek UAC/VM kurulumu çalıştırılmadı.
- Ham işçi raporları: `brain/dbf825b7-…/scratch/audit-audit-{1..4}.md`.
