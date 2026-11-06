# Dikte (VoxNote AI) — Eksiklik, Yarım İş ve Hata Raporu

**Tarih:** 6 Kasım 2026
**İncelenen proje:** `C:\Users\aksek\Desktop\dikte projesi` (git: `main`, son commit `c725a0e`)
**Kapsam:** `dikte/` Python paketi (17 modül), `dikte/ui/` (HTML/CSS/JS), testler, `Dikte.spec`, `installer/`, dokümantasyon.
**Yöntem:** Statik kod incelemesi (tüm modüller okundu), çapraz referans kontrolü (JS ↔ Python köprüsü, ayarlar ↔ motor), doküman–kod karşılaştırması, git deposu taraması, test koşumu.
**Kısıt:** Bu oturumun dosya sandbox'ı proje dışına yazmayı engellediği için `pytest` tam koşulamadı (68 test geçti, 152'si sandbox'ın geçici klasör kısıtı yüzünden `PermissionError` verdi — kod hatası değil). Kalan sonuçlar STATE.md'deki 220 test iddiasına dayanıyor; **kurulum/güncelleme hiçbir zaman gerçekten çalıştırılmadı.**

> **Önemli:** Proje "v1.6 kod tarafı tamamlandı" diyor; gerçekte **v1.5 kurulum ve v1.6 güncelleme zinciri çalışmıyor**, karşılama sihirbazı hiç yazılmamış ve sürüm numarası hâlâ **1.3.0**. Aşağıdaki 1–8 numaralı maddeler yayınlanmayı doğrudan engelliyor.

---

## 0. Özet — Önce Bunlar

| # | Önem | Sorun | Yer |
|---|------|-------|-----|
| 1 | **Blocker** | Güncelleme indirilen kurucuyu her seferinde siliyor: `update_check()` `sha256` alanını döndürmüyor, `update_apply()` boş özetle karşılaştırıyor → her zaman "özet uyuşmuyor" | `controller.py:1302-1325` |
| 2 | **Blocker** | `UPDATE_URL` boş; güncelleme özelliği hiç çalışmıyor, hata mesajı da yanıltıcı ("Sunucuya ulaşılamadı") | `config.py:17`, `controller.py:1291` |
| 3 | **Blocker** | Sürüm her yerde `1.3.0`; v1.4–v1.6 kodu ve `latest.json` (1.6.1) ile çelişiyor | `config.py:12`, `dikte/__init__.py:3`, `Dikte.iss:7` |
| 4 | **Blocker** | Kaldırma veriyi silmiyor: yalnız `unins000.exe` çalıştırılıyor; modeller/geçmiş/ayarlar/loglar `%LOCALAPPDATA%\Dikte` altında kalıyor (UI ve PLAN aksini söylüyor) | `uninstall.py:108-121`, `Dikte.iss:47-49` |
| 5 | **Blocker** | Kurucu hiç derlenmemiş: PyInstaller ve Inno Setup bu makinede kurulu değil, `dist/` yok; spec ayrıca `llama_cpp`'yi paketlemiyor | `Dikte.spec:21-27` |
| 6 | **Blocker** | Onaylanan (2026-11-04) 5 ekranlı karşılama sihirbazı hiç yok: `setup_done`, `#sayfa-kurulum`, adımlar, CUDA/model indirme yok | `dikte/ui/`, `controller.py` |
| 7 | **Blocker** | Kaldırma, otomatik başlatma kayıt defteri girdisini silmiyor; açılışta silinmiş exe çağrılır | `uninstall.py:76-121`, `Dikte.iss:39-41` |
| 8 | **Blocker** | PyInstaller giriş betiği `dikte\__main__.py`; göreli importlar (`from . import`) pakette "no known parent package" hatası verir | `Dikte.spec:15`, `dikte/__main__.py:18` |

**Sayısal özet:** 8 blocker, ~16 yüksek, ~22 orta, ~18 düşük/hijyen maddesi.

---

## 1. Yayın Zinciri (v1.5 / v1.6) — Çalışmıyor

### 1.1 [KRİTİK] Güncelleme her zaman başarısız, dosyayı siliyor
`controller.update_check()` iki dönüş dalında da `sha256` alanını düşürüyor:

```python
# controller.py:1294-1309
return {"ok": True, "update_available": True, "version": ..., "notes": ..., "url": ...}
```

`updater.check()` ise `sha256` üretiyor (`updater.py:107-113`). `update_apply()` tekrar denetim yapıp (`controller.py:1312`) şu satırı çalıştırıyor:

```python
if not updater.verify_sha256(path, check.get("sha256", "")):   # controller.py:1325
    return {"ok": False, "code": "sha_mismatch", ...}
```

`verify_sha256` boş özetle eşleşmeyeceği için **indirilen kurucu siliniyor** (`updater.py:170-172`). Yani `UPDATE_URL` doldurulsa bile güncelleme asla kurulamaz. Testler bunu görmüyor çünkü `test_ui.py` sahte `update_check` yanıtına `sha256` koyuyor ve `update_apply`'ı köprüde taklit ediyor (`tests/test_ui.py`, sahte API).

**Düzeltme:** `sha256`'yı her iki dönüşe ekle; `update_apply` yeniden denetim yapmak yerine aynı sonucu kullansın; `sha_mismatch`/`incomplete` için Türkçe mesaj ekle.

### 1.2 [KRİTİK] `UPDATE_URL` boş ve hata mesajı yanlış
`config.py:17` `UPDATE_URL = ""`. `updater.check(force=False)` bu durumda `None` dönüyor, `controller.update_check` bunu `code="net"` + **"Sunucuya ulaşılamadı."** olarak raporluyor (`controller.py:1291-1292`). Doğrusu "güncelleme sunucusu yapılandırılmamış" olmalı; ayrıca özellik tamamen ölü.

### 1.3 [KRİTİK] Sürüm numarası 1.3.0'da kalmış
- `dikte/config.py:12`, `dikte/__init__.py:3`, `installer/Dikte.iss:7` → `1.3.0`
- `installer/latest.json` → `1.6.1` (örnek)
- `text_models.py:22` ve `openrouter.py` User-Agent → `Dikte/1.3`

Sonuç: 1.6 kurulduğunda bile uygulama kendini 1.3 sanıp her açılışta aynı güncellemeyi önerir. Sürüm tek kaynaktan (`config.APP_VERSION`) okunmalı, iss/spec bunu `#define` ile almalı.

### 1.4 [KRİTİK] Kaldırma kullanıcı verisini silmiyor
`uninstall.run_uninstaller()` yalnız Inno kaldırıcısını başlatıyor (`uninstall.py:108-121`). Inno `[UninstallDelete]` bölümü boş (`Dikte.iss:47-49`) ve kodda `MODELS_DIR`/`DATA_DIR`/`LOG_DIR` silen hiçbir çağrı yok. Oysa:

- `app.js:1716-1718`: "modeller, geçmiş, ayarlar ve günlükler" silinecek diyor,
- `PLAN.md` Aşama 10: aynısını vaat ediyor,
- `STATE.md:52`: "modeller, geçmiş ve ayarlar silinecek" diyor.

**Düzeltme:** Kaldırıcıya `[UninstallDelete]` ile `{localappdata}\Dikte` ekle **veya** uygulama içinde onay sonrası `shutil.rmtree` yap; UI metnini buna göre düzelt.

### 1.5 [KRİTİK] Kurulum hiç denenmemiş, spec eksik
- Bu makinede `PyInstaller` **yok**, Inno Setup **yok**, `dist/` **yok** → `STATE.md:6` "kurulum/derleme kullanıcı testi bekliyor" doğru ama "kod tamam" iddiası kanıtsız. `requirements-dev.txt`'te de PyInstaller yok; `build.ps1` gibi bir derleme betiği hiç yok.
- **Giriş betiği hatası:** `Dikte.spec:15` doğrudan `dikte\__main__.py`'yi gösteriyor. PyInstaller betiği `__main__` olarak çalıştırdığı için dosyadaki `from . import config, diagnostics` (`dikte/__main__.py:18-20`) "attempted relative import with no known parent package" ile patlar. Üst düzey bir `run_dikte.py` (`from dikte.__main__ import main`) eklenip `Analysis` ona yönlendirilmeli.
- `Dikte.spec:21-27` `hiddenimports` listesinde `llama_cpp` yok. `text_models.py:281` importu fonksiyon içinde (lazy) olduğu için PyInstaller onu **paketlemez** → kurulu sürümde "Yerel model" sağlayıcısı "motor kurulu değil" hatası verir. `llama_cpp\lib` altındaki `llama.dll`, `ggml*.dll` dinamik yüklendiği için `collect_all("llama_cpp")` gerekir.
- `icon=None` (`Dikte.spec:55`), sürüm bilgisi yok, `console=False` → paketli sürümde `--selftest`/`--kurulum` çıktısı görünmez, hatta `print` çağrıları sorun çıkarabilir.
- `datas` hedefi `"dikte\\ui"` ters bölü ile verilmiş; platformdan bağımsız yol beklenir.
- CUDA DLL'leri paketlenmiyor (bilinçli "CPU paketi"), ancak sihirbazda vaat edilen "CUDA bileşenini indir" akışı hiç yok.

### 1.6 [YÜKSEK] Güncelleme uygulaması UI'yı donduruyor, uygulamayı kapatmıyor
- `update_apply()` ~200 MB kurucuyu **senkron** indiriyor (`controller.py:1321`), ilerleme yok, iptal yok; pywebview çağrısı boyunca pencere donar.
- `updater.apply()` kurucuyu başlatıp dönüyor (`updater.py:176-185`); uygulama kapanmıyor, pencere yok edilmiyor, yeniden başlatma yok. Inno `/SILENT` çalışırken `Dikte.exe` hâlâ açık olduğu için dosya kilidi/kurulum hatası çok olası.
- `app.js:1811-1829` başarısızlıkta "Uygulamayı Güncelle" düğmesini yeniden etkinleştirmiyor; sürüm notları (`#updateNotes`) hiç gösterilmiyor.

### 1.7 [YÜKSEK] Kurulum yeri kararı çelişkili
2026-11-04 kararı: "Program Files'a, yönetici izinli normal kurulum" (`uygulanacak plan.md` §2c). `Dikte.iss:15-17` ise hâlâ `{localappdata}\Programs\Dikte` + `PrivilegesRequired=lowest` (eski karar). Hangisinin geçerli olduğu netleşmeli; kod eski kararda.

### 1.8 [ORTA] Inno `AppId` geçersiz karakter içeriyor
`Dikte.iss:11` `{{8A5D2C61-1D46-4E25-9A0B-DIKTE0000000}` — `DIKTE` onaltılık değil. Inno bunu opak kimlik olarak kabul eder ama gerçek GUID değildir; yükseltme kimliği karışabilir. Geçerli bir sabit GUID kullan.

### 1.9 [ORTA] Kaldırma/otomatik başlatma geliştirme modunda bozuk
`uninstall.set_autostart(True)` `sys.executable`'ı yazıyor (`uninstall.py:83`). Geliştirme modunda bu `python.exe`'dir ve argümansız çalışır → açılışta hiçbir şey olmaz. UI'daki anahtar dev modda kapatılmıyor (`app.js:1722-1737` sadece kaldırma düğmesini devre dışı bırakıyor).

### 1.10 [KRİTİK] Kaldırma otomatik başlatma kaydını bırakıyor
`set_autostart()` `HKCU\...\Run\Dikte` değerini yazıyor (`uninstall.py:76-84`); ne `run_uninstaller()` ne `Dikte.iss` bu değeri siliyor (`[Registry]` boş, `Dikte.iss:39-41`). Kaldırma sonrası Windows her açılışta silinmiş exe'yi çalıştırmaya çalışır. Kaldırıcıya `[UninstallRun]`/`[Registry]` ile silme ekle veya uygulama içi onayda `set_autostart(False)` çağır.

### 1.11 [YÜKSEK] Eski `data/` klasörü taşınmıyor
Onaylı plan (`uygulanacak plan.md:58-60`) ilk paketli açılışta proje klasöründeki `data/`'nın `%LOCALAPPDATA%\Dikte`'ye yedekli taşınmasını istiyor. Kodda böyle bir fonksiyon yok; mevcut kullanıcı paketli sürüme geçince ayarlar/geçmiş boş görünür.

### 1.12 [ORTA] `compare_versions` semver değil
`updater.py:40-47` her parçadaki rakamları topluyor: `1.6.1-beta` → `[1,6,11]`, yani `1.6.1`'den **büyük** sayılır. Ön sürüm yayınlanırsa kararlı istemciler beta'ya "güncellenir". `packaging.version.Version` kullanılmalı veya ön sürüm önceliği açıkça yazılmalı.

### 1.13 [ORTA] `data_bytes()` çift sayıyor
`uninstall.py:50-53` paketli sürümde `MODELS_DIR`+`DATA_DIR`+`LOG_DIR`+`TEMP_DIR` üstüne bir de tüm `exe_dir()`'i ekliyor; modeller/loglar `_internal` altında olduğu için aynı baytlar iki kez sayılıyor. "Silinecek veri" olduğundan büyük görünür ve kurulu ikili dosyaları da kapsar. Yollar tekilleştirilmeli.

---

## 2. Hiç Yazılmamış / Yarım Kalan Özellikler

| Özellik | Durum | Kanıt |
|---|---|---|
| **Karşılama sihirbazı (5 ekran)** | **Yok** | `setup_done`, `#sayfa-kurulum`, "sihirbaz" aramaları boş; `design/v2/karsilama-sihirbazi-taslak.html` yalnız tasarım |
| **CUDA bileşeni indirme** | Yok | Sihirbaz olmadığı için hiç yok; spec CUDA paketlemiyor |
| **Girdi dili (input_language)** | Ölü ayar | `engine.py:157` `language=config.LANGUAGE` ("tr") sabit; `settings`/UI'da değer var ama motora bağlı değil |
| **Sistem tepsisi** | Yok | Kapanınca uygulama çıkıyor, kısayol duruyor (bilinen sınırlama) |
| **7c "⋯" model menüsü** | Yok | PLAN'da işaretsiz; eylemler kart üstünde |
| **Ses modeli indirmede duraklat/iptal** | Yok | `models.py:205-239` yalnız ilerleme; metin modelinde var |
| **Güncelleme yayını** | Yok | `latest.json` örnek değerlerle; GitHub Release yok, `UPDATE_URL` boş |
| **README / LICENSE / CI** | Yok | Public repo olmasına rağmen kökte yok |
| **Karşılama sonrası ilk kurulum akışı** | Yok | `setup_done` diye bir ayar bile yok |

Ek olarak `text_engine.generate(provider="local")` kalıcı bir stub (`text_engine.py:275-277`) — "GGUF desteği sonraki partide" diyor; oysa yerel GGUF `controller._local_process_text` içinde ayrı ve **kopyalanmış** bir yoldan çalışıyor. İki ayrı yerel metin akışı var; biri diğerinin geliştirmelerini almıyor.

---

## 3. Kritik / Yüksek Kod Hataları

### 3.1 [YÜKSEK] Kopyalama başarısızsa eski pano içeriği yapıştırılıyor
`_process` içinde `copy_ok=False` olsa bile yapıştırma koşulsuz çalışıyor (`controller.py:432-448`). Panoya yazma hatasından sonra kullanıcının önceki panosu etkin pencereye yapıştırılır. Aynı sorun otomatik çeviride: çevrilmiş metin panoya yazılamazsa ham metin yapıştırılır, geçmiş/arayüz ise çevrilmiş metni gösterir (`controller.py:1570-1573`).

**Düzeltme:** `if copy_ok and auto_paste` koşulu; AI kopyalama hatasını da `copy_ok=False` yap.

### 3.2 [YÜKSEK] Kısayol işleyicisi saniyelerce bloke oluyor
`on_hotkey_press → toggle_record → _prepare_whisper → load_engine` zinciri pynput dinleyici thread'inde **senkron** çalışıyor (`controller.py:295-335`, `218-250`). Model yeniden yüklenirken (~7 sn) bas-bırak olayları kuyruğa girer; bırakma gecikince kayıt 0,4 sn eşiğinin altında kalıp sessizce atılır. UI mikrofon düğmesi de aynı süre donar.

### 3.3 [YÜKSEK] Aynı anda iki Whisper modeli yüklenebiliyor
`load_engine` `_whisper_loaded` kontrolünü kilit altında yapıp kilidi bırakıyor, bayrağı ancak yükleme bitince set ediyor (`controller.py:218-235`). `_prepare_whisper` da bayrağı kilit dışında okuyor (`261-271`). Mikrofon düğmesi + kısayol aynı anda (veya metin modeli boşaltmasından hemen sonra iki hızlı basış) iki `WhisperModel` yükler → 8 GB VRAM'de OOM riski.

### 3.4 [YÜKSEK] Temizle/Çevir yanlış geçmiş kaydını güncelliyor
`_last_history_id` yalnız yeni diktede set ediliyor (`controller.py:470`); `history_open` onu değiştirmiyor (`637-647`). Akış: A dikte et (id X) → Geçmiş'ten eski B kaydını aç → Çevir/Temizle → ekranda B var ama **X kaydı B'nin metniyle ezilir** (`_run_text → _update_history_text`, `1466, 1578-1584`).

### 3.5 [YÜKSEK] Metin modeli indirmede iptal/duraklat yarışı `.part` dosyasını bozuyor
- `text_model_cancel` durumu hemen "cancelled" yapıp dönüyor; worker hâlâ `read()` içinde olabilir (`controller.py:1008-1026`).
- `text_model_resume` `_text_pause.clear()` yapıp **yeni thread** başlatıyor (`994-1006`); eski thread duraklamayı görmezse iki thread aynı `.part` dosyasına yazar.
- İptal edilen eski worker daha sonra `delete_part(name)` çağırıp **yeni indirmenin** verisini silebilir (`controller.py:978-982`).

**Düzeltme:** İndirme başına jeton/thread kimliği; eski worker bitmeden yenisini başlatma; silmeyi yalnız açık iptalde ve worker durduktan sonra yap.

### 3.6 [YÜKSEK] Model dosyalarında bütünlük doğrulaması yok
- GGUF: `is_installed` yalnız **boyut** eşitliğine bakıyor (`text_models.py:104-106`); doğru boyutta bozuk dosya "kurulu" sayılıyor, `.part` doğrudan `.gguf`'a taşınıyor (`197-200`).
- Whisper: `model.bin` var ve >0 ise "kurulu" (`models.py:124-134`); `config.json`/tokenizer eksik snapshot da kurulu görünür.
- Hiçbir yerde SHA-256 yok.

### 3.7 [YÜKSEK] Sessizce kırpılan yanıtlar tam metin gibi kabul ediliyor
`finish_reason == "length"` yakalanıyor ama başarı yolunda **hiç kontrol edilmiyor** (`text_engine.py:290-329`). Uzun dikte/çeviride yarım cümle panoya ve geçmişe "tam" diye yazılır. Ayrıca ≥3 kelimelik metinde halüsinasyon/eksiltme koruması yok (`validate_output`, `202-216` — yalnız ≤2 kelimede oran kontrolü).

### 3.8 [ORTA-YÜKSEK] `strip_response` gerçek dikte metnini siliyor
`META_MARKERS` içinde `"i corrected"`, `"note:"` var; `strip_response` bunları görünce ilk satırı atıyor (`text_engine.py:102-112, 143-160`). "I corrected the report yesterday." cümlesi boş yanıta dönüşüp `empty_result` hatası verir.

### 3.9 [ORTA-YÜKSEK] WAV yazma hatası durumu RECORDING'de kilitliyor
`audio.stop()` içinde `_write_wav` istisnası `AudioError`'a sarılmıyor (`audio.py:92, 101-106`); `_stop_recording` yalnız `AudioError` yakalıyor (`controller.py:356-362`). Disk dolu/kilitli durumda uygulama "Dinleniyor…" durumunda kalır, yarım `kayit-*.wav` artığı oluşur.

### 3.10 [ORTA] Ayarlar kaydı thread-safe değil
`SettingsStore.save()` `_data`'yı okuyup birleştirip yazıyor, kilit yok (`settings.py:178-199`). Worker (otomatik çeviri) ile UI aynı anda kaydederse **son yazan diğerinin değişikliğini ezer**. Aynı sabit `.tmp` adı iki yazarın dosyasını karıştırabilir.

### 3.11 [ORTA] Geçici okuma hatası tüm geçmişi silebilir
`history.load()` herhangi bir istisnada (kilit/AV dahil) dosyayı yedeğe alıp boş listeyle devam ediyor (`history.py:78-82`); sonraki `add()` gerçek geçmişi tek kayıtla değiştirir. Yalnız `JSONDecodeError` için sıfırlama yapılmalı; `OSError`'da yazma reddedilmeli.

---

## 4. Orta ve Düşük Bulgular (seçilmiş)

### Performans / donma
- **Temizle/Çevir ve yerel model yükleme UI thread'inde senkron** (`controller.py:1040-1046`, `1517-1524`): 2 GB GGUF yüklenirken pencere donar, iptal yok.
- **Model silme durum koruması yok**: `model_delete` yalnız `_info` üzerinden kontrol ediyor (`878-887`); `LOADING` sırasında yüklenen modelin klasörü silinebilir. `text_model_delete` ayrıca `settings["text_model"]`'i temizlemiyor → sonraki temizlikte `local_missing`.
- **`_run_text` `_latest`'i güncelleyip `_seq`'i artırmıyor** (`1470-1476`); snapshot ile metin sırası tutarsız, ikinci bir renderer metni kaçırır.
- **Kapanış koruması ölü**: `_closed` set ediliyor ama hiç okunmuyor (`controller.py:122, 273-291`); worker/download thread'leri join edilmiyor, çeviri sürerken çıkışta `kayit-*.wav` kalıyor.
- **Kayıt süresi sınırsız**: `audio.py` tüm PCM'i RAM'de tutuyor (`_chunks`), uzun kayıtta bellek şişer.

### Arayüz (app.js)
- **`snapshot.ai` içinde `state` yok** (`controller.py:613, 1181-1208`); `app.js:1122` bunu eski değerle dolduruyor. Ayarlar model `loading` iken açılırsa Temizle/Çevir **sonsuza dek kapalı** kalır; `ready` iken kayıt sırasında **açık** kalır. Test bunu `test_ui.py:93`'te `copy.ai.state = copy.state` ile maskeliyor.
- **Kaydedilmemiş ayarlar sessizce kayboluyor**: sayfadan çıkıp dönünce `loadSettings()` her şeyi sıfırlıyor (`app.js:255, 1531-1555`).
- **250 ms poll kullanıcı seçimini geri alıyor**: `outputLang`/`autoTranslate` her snapshot'ta yazılıyor (`app.js:1123-1124`); kaydetme reddedilirse seçim görünür şekilde geri döner.
- **OpenRouter anahtar kaydet/sil handler'larında try/catch yok** (`app.js:1373-1389, 1402-1414`) → sessiz unhandled rejection.
- **Sırasız async yanıtlar**: `loadHistory`/`loadModels`/`loadOpenRouterModels` jeton kullanmıyor; yavaş eski yanıt yeni listeyi ezebilir.
- **"Yenile" durumu eski poll ile açılıyor** (`app.js:419-426, 1666-1684`).
- **Ölü kod**: `#topLang` dinleyicisi (`app.js:1692`) — HTML'de böyle bir id yok. `text_model_open_folder` köprüde var, UI'da hiç çağrılmıyor.
- **Metin modeli indirme bitişi bildirilmiyor**: `handleDownloadNotice` yalnız `result.download` için çağrılıyor (`app.js:1030`).
- **Model detay paneli kapanmıyor**: poll her yüzdede yeniden açıyor (`app.js:800, 990-992`).
- **"Varsayılana dön" yalnız kısayol + geçmişi sıfırlıyor** (`app.js:1600-1606`), AI/tema/efektler dokunulmuyor.

### Diğer
- **Otomatik çeviri `CLEANING` durumunu kullanmıyor**: `_process` içinde PROCESSING'de kalıyor (`controller.py:441`), kullanıcı "İşleniyor…" görüyor; `PROCESSING→CLEANING` geçişi tanımsız (`state.py:15-21`).
- **`refresh_last` otomatik çeviriyi atlıyor**: ham Whisper metni çevrilmiş metnin üzerine yazılıyor (`controller.py:530-573`).
- **`update_last_check` UTC kaydedilip yerel saat gibi gösteriliyor** (`controller.py:1293, 1210-1218`).
- **`_openrouter_key` ilk `snapshot()` çağrısında kilit altında DPAPI çözüyor** (`controller.py:613, 1171-1179`) — ilk poll gecikebilir.
- **OpenRouter hata eşlemesi**: 401/402/429 dışındaki tüm HTTP kodları `"net"` → 404 "Sunucuya ulaşılamadı" diye gösteriliyor (`openrouter.py:44-48`).
- **Önbellek yazımı atomik değil** (`openrouter.py:179-190`); bozuk JSON tüm katalogu kaybettirir.
- **Gelecek tarihli önbellek hiç eskimez** (`openrouter.py:166-176`).
- **`config.py` veri kökü bölünmüş**: paketli sürümde `DATA_DIR=%LOCALAPPDATA%\Dikte` ama `MODELS_DIR`/`LOG_DIR` hâlâ `ROOT_DIR` (PyInstaller'da `_internal`) altında (`config.py:27-30`). Modeller kurulum klasöründe kalır; kaldırma/taşıma/izin sorunları doğurur.
- **`ensure_runtime_dirs()` hatası açılışı durduruyor** (`config.py:119-122`); salt okunur klasörde uygulama hiç açılmaz.
- **`diagnostics.setup_logging`**: mevcut root handler varsa dosya logu hiç kurulmuyor; rotasyon yok, `dikte.log` sınırsız büyür (`diagnostics.py:102-119`).
- **`MSG_MODEL_MISSING`** son kullanıcıya `python -m dikte --kurulum` çalıştırmasını söylüyor (`diagnostics.py:87-90`) — kurulu sürümde bu komut yok.
- **`paste.py` docstring'i tersini söylüyor** ve `send_ctrl_v` her durumda `True` dönüyor (`paste.py:51-59`) → "Etkin pencereye yapıştırıldı" etkinliği yanlış pozitif.
- **`secrets.json` bozuk dosyayı sessizce eziyor** (`secrets.py:128-136, 154-162`); diğer ayarlar gibi yedeklemiyor.
- **`_cuda_prepared` iş başarısızken de set ediliyor** (`diagnostics.py:24-29`) → geçici hata tüm süreç boyunca CUDA'yı kapatır.
- **Ses modeli indirmede disk alanı ön kontrolü yok** (`models.py:205-239`).

---

## 5. Depo Hijyeni ve Dokümantasyon Çelişkileri

### Depo
1. **`README.md` yok** — depo public; ilk açan kişi ne kuracağını bilmiyor.
2. **`LICENSE` yok** — public repo için hukuki belirsizlik.
3. **CI yok** (`.github/` yok) — testler yalnız elle koşuluyor.
4. **`docs/` altında 7 adet 0 baytlık dosya** commit edilmiş (`docs/app/...`, `docs/rules/...`). Next.js doküman artığı; silinmeli.
5. **`mevcut tasarım/` klasörü `design/`'ın birebir kopyası** (4,8 MB, yalnız sihirbaz taslağı eksik, 2 PNG farklı) ve **untracked**. Yanlışlıkla commit edilirse depo ikiye katlanır; silinmeli.
6. **`uygulanacak plan.md` untracked** — son ve en güncel plan git'te yok.
7. **`design/v2/v2-acik-dikte.png` ve `v2-koyu-dikte.png` değişiklikleri commit edilmemiş.**
8. `web/` (Next.js denemesi, 25 takipli dosya) üretimle ilgisiz şekilde kökte duruyor; arşive taşınmalı veya README'de "deneme" olarak işaretlenmeli.
9. `.gitignore` çalışma zamanı dosyalarını iyi kapsıyor ve gizli anahtar taraması temiz: commit geçmişinde gerçek `sk-or-v1-` anahtarı yok, yalnız test sahteleri ve maskeleme örnekleri var. **Ancak** `dist/`, `build/`, `installer/Output/`, `*.log`, `web/.next/`, `web/node_modules/` girdileri yok — derleme sonrası `git add .` ile public depoya kurucu/binary sızabilir.
10. **`Dikte.bat` son kullanıcıya `requirements-dev.txt` kurduruyor** (`Dikte.bat:5-9`); bu dosya Playwright'ı da çeker. Geliştirici olmayan için `requirements.txt` yeterli.

### Dokümanlar
11. **PLAN.md ile STATE.md çelişiyor**: PLAN `7e` ve `7c`'yi işaretsiz ("kalite tablosu eksik") bırakıyor; STATE "7e 10/10 geçti" diyor. `reports/2026-11-04-7e-kalite-tablosu.md` var ama içinde istenen 10 girdi/çıktı çifti ve VRAM takas ölçümü yok, yalnız OK/FAIL durumları var → 7e "kısmen tamam" sayılmalı.
12. **STATE.md "Yarım kalan" bölümü eski** (`31-35`): "v1.5 kodlanmadı", "v1.6 kodlanmadı" yazıyor; oysa aynı dosyanın başı "tamamlandı" diyor. Bu bölüm silinip yeniden yazılmalı.
13. **`architecture.md` "Bilinen sorunlar"** hâlâ gelecek zaman ("v1.5'te eklenecek", "v1.6'da eklenecek") — kod yazılmış ama dosya güncellenmemiş.
14. **`config.py:16` yorumu** "v1.6: yayın yeri henüz seçilmedi (K2)" diyor; `uygulanacak plan.md` ise "GitHub Releases seçildi" diyor. Karar uygulanmamış.
15. **`olabilir.md` "uygulanmadı"** olarak işaretli ama içindeki maddelerin çoğu kodda var; arşivlenmeli.
16. **`promptlar.md`, `.kilo/plans/*`, `.kilo/skills/*`** üretim deposunda gereksiz gürültü; ayrı klasöre alınabilir.

---

## 6. Test Durumu

| Konu | Bulgu |
|---|---|
| Koşum | Bu ortamda 68 test geçti, 152'si sandbox'ın geçici klasör yazma engeli yüzünden `PermissionError` verdi (proje hatası değil). STATE iddiası: 220 passed, 1 skipped. |
| Kapsam boşluğu | `update_check` sahte yanıtı `sha256` içeriyor, `update_apply` köprüde taklit ediliyor → **1.1'deki kritik hata testle yakalanamaz**. |
| Kapsam boşluğu | `test_ui.py:93` `ai.state` enjekte ediyor → `snapshot.ai`'de state olmaması maskeleniyor. |
| Kapsam boşluğu | `history_list` sahtesi `period` parametresini yok sayıyor → Bugün/Bu hafta filtresi test edilmiyor. |
| Kapsam boşluğu | Kaldırma akışı, otomatik başlatma, güncelleme hatası sonrası toparlanma, kaydedilmemiş ayar gezinmesi, kayıt sırasında AI kontrolleri test edilmiyor. |
| Kapsam boşluğu | `tests/test_uninstall.py` **yok**: `is_installed`, `data_bytes`, `set_autostart`, `autostart_enabled`, `run_uninstaller` hiç test edilmiyor; STATE "kaldırma testleri hazır" diyor. |
| Eksik fixture | `tests/data/test.wav` ve `test.txt` yok → `--selftest` hiç çalıştırılamıyor (`config.py:64-65`). |
| Kurulum/güncelleme | Hiç uçtan uca denenmemiş; derleme araçları kurulu değil. |
| Playwright | 25 test var; gerçek tarayıcı koşumu bu makinede doğrulanmadı. |

---

## 7. Öncelikli Düzeltme Planı

### Faz 1 — Yayın blockerları (1–2 gün)
1. Sürümü tek kaynağa indir: `APP_VERSION = "1.6.0"`; `__init__`, `Dikte.iss`, `latest.json`, User-Agent bundan türesin.
2. `update_check` dönüşüne `sha256` ekle; `update_apply` aynı sonucu kullansın; `UPDATE_URL`'i gerçek GitHub Releases URL'siyle doldur; `latest.json`'u yayınla.
3. Güncellemeyi arka plan thread'ine al, ilerleme göster, kurulumdan önce uygulamayı kapat (`webview.windows[0].destroy()` / `os._exit`), kurulum sonrası yeniden başlat.
4. Kaldırmada veri silmeyi gerçekten yap **veya** UI/PLAN metnini "veriler korunur" olarak düzelt; HKCU `Run\Dikte` değerini de temizle.
5. `Dikte.spec`'e `run_dikte.py` giriş betiği, `collect_all("llama_cpp")`, ikon ve sürüm bilgisi ekle; PyInstaller + Inno Setup'ı kur, `build.ps1` yaz, derle, `dist/Dikte` ve `Dikte-Setup.exe` üret; kurulu pakette yerel GGUF'u duman testinden geçir.

### Faz 2 — Veri kaybı ve çökme hataları (2–3 gün)
6. Pano hatasında yapıştırmayı iptal et (3.1).
7. Kısayol işleyicisini kuyruğa al; model yüklemeyi worker'a taşı (3.2, 3.3).
8. `history_open` `_last_history_id`'yi güncellesin (3.4).
9. GGUF indirmede thread jetonu + join; iptalde yanlış dosya silmeyi engelle (3.5).
10. SHA-256 (veya GGUF sihirli bayt) doğrulaması ekle (3.6).
11. `finish_reason == "length"` kontrolü + eksiltme koruması (3.7); `strip_response` etiket temizliğini yalnız çok satırlı meta yanıtlara uygula (3.8).
12. `audio.stop()` istisnalarını `AudioError`'a sar (3.9).
13. `SettingsStore`/`HistoryStore`/`SecretStore` yazımlarına kilit + benzersiz temp + fsync (3.10, 3.11).

### Faz 3 — Ürün bütünlüğü (3–5 gün)
14. Karşılama sihirbazını yaz veya kapsamdan resmen çıkar (PLAN/STATE güncelle).
15. `input_language`'ı motora bağla (`language=None` otomatik, `"tr"` sabit); eski `data/` taşıma fonksiyonunu ekle.
16. `snapshot.ai`'ye `state` ekle; kaydedilmemiş ayar koruması, async jetonlar, düğme toparlanması (Bölüm 4).
17. Temizle/Çevir için arka plan işi + ilerleme; otomatik çeviride `CLEANING` durumu.
18. Kaldırma/otomatik başlatma dev modda düzgün davransın.

### Faz 4 — Hijyen ve sürdürülebilirlik (1 gün)
19. README (kurulum + geliştirme + ekran görüntüleri), LICENSE, basit GitHub Actions (pytest).
20. `docs/` boş dosyalarını, `mevcut tasarım/` kopyasını sil; `uygulanacak plan.md`'yi commit et; `.gitignore`'a `dist/`, `build/`, `installer/Output/`, `*.log` ekle.
21. PLAN/STATE/architecture senkronize et; "Yarım kalan" bölümünü gerçek durumla değiştir.
22. Test boşluklarını kapat: gerçek `update_check`+`update_apply` akışı, kaldırma, autostart, AI state, geçmiş dönem filtresi.

---

## 8. Doğrulanamayanlar / Notlar

- **Gerçek mikrofon, GPU, kurulum ve güncelleme** bu ortamda çalıştırılamadı; ilgili maddeler statik kanıta dayanıyor.
- **Llama.cpp ilk çağrı ~50 sn** ve **VRAM takası** ölçümleri STATE'de iddia; tekrar ölçülmedi.
- **7e kalite tablosu** raporu mevcut (`reports/2026-11-04-7e-kalite-tablosu.md`, 10/10); sentetik TTS ile üretildiği için "en iyi durum" ölçümü.
- OpenRouter gerçek çağrı maliyeti ~$0,001; `STATE.md` maliyet günlüğünde "doğrula" notu duruyor.

---

*Bu rapor salt okunur inceleme ile hazırlandı; proje dosyalarında değişiklik yapılmadı.*
