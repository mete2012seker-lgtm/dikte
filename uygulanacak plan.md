# uygulanacak plan.md — Kalan işler için uygulama planı

Oluşturma: 2026-11-04 · **Yeniden yazıldı: 2026-11-07**
Kaynaklar: `Dikte-Denetim-Raporu.md` (2026-11-06), kodun satır satır doğrulanması, `pytest` koşumu, AGENTS.md kararları.
Bu dosya **plan**dır; onay olmadan kod yazılmaz. 2026-11-07 oturumunda yalnız doküman güncellendi, kod değişmedi.

## Yöntem (`calisma-duzeni.md` — zorunlu)
Bu plan `calisma-duzeni.md` sırasıyla hazırlandı; aşamalar atlanmadı:
1. **Keşif:** proje kökü, `git status`/`git log`, izlenen dosyalar, derleme araçlarının varlığı.
2. **Doküman okuma:** AGENTS, STIL, STATE, PLAN, architecture, reports, `Dikte.spec`, `installer/Dikte.iss`.
3. **Dört paralel salt-okunur iş kolu:** backend çekirdek, veri katmanı, arayüz+köprü, paketleme+doküman.
4. **Sentez:** tekrar ayıklama, doküman–kod çelişkileri, test maskeleri.
5. **Çapraz doğrulama:** en kritik 3 iddia kod satırından doğrulandı: (a) `sha256` akışı, (b) `UPDATE_URL`/sürüm, (c) kaldırma verisi.
6. **Rapor + fazlı plan + doğrulanamayanlar:** §0 durum tablosu, Faz 1–4, §10.

---

## 0. Doğrulanan mevcut durum (2026-11-07)

| Konu | Gerçek durum | Kanıt |
| :--- | :--- | :--- |
| Testler | **220 passed, 1 skipped** (41,08 sn) | `.venv\Scripts\python.exe -m pytest -q` |
| Selftest | Çalıştırılamıyor | `tests/data/test.wav` ve `test.txt` yok |
| Sürüm | **1.3.0** | `dikte/config.py:12`, `dikte/__init__.py:3`, `installer/Dikte.iss:7` |
| Güncelleme | **Her zaman başarısız** | `controller.py:1302-1309` `sha256` döndürmüyor; `:1312` yeniden denetliyor; `:1325` boş özetle karşılaştırıp dosyayı siliyor |
| Yayın adresi | Boş | `config.py:17` `UPDATE_URL = ""`; `latest.json` örnek değerlerde |
| Kaldırma | Veriyi ve autostart kaydını silmiyor | `uninstall.py:108-121`; `Dikte.iss` `[UninstallDelete]` ve `[Registry]` boş |
| Kurucu | Hiç derlenmemiş | `dist/` yok; PyInstaller ve Inno Setup kurulu değil; `.venv` içinde `PyInstaller` yok |
| Spec | Giriş betiği hatalı, `llama_cpp` eksik | `Dikte.spec:15` `dikte\__main__.py`; `hiddenimports` listesinde `llama_cpp` yok |
| Karşılama sihirbazı | **Yok** | `setup_done`, `#sayfa-kurulum`, 5 ekran kodda yok; yalnız `design/v2/karsilama-sihirbazi-taslak.html` var |
| v1.4 efektleri | Kullanıcı gözle onayladı (2026-11-04) | `uygulanacak plan` eski sürümü ve kullanıcı kararı |
| 7e kalite tablosu | **Kısmen** | 10/10 OK var; tam girdi/çıktı çiftleri ve VRAM takas ölçümü yok (`reports/2026-11-04-7e-kalite-tablosu.md`) |

**Sonuç:** "v1.6 kodu tamamlandı" ifadesi yanlış. Kodun büyük kısmı var; **yayın zinciri (kurulum + güncelleme + kaldırma) çalışmıyor**.

---

## 1. Kararlar

### 1.1 Kesinleşen kararlar
- **GitHub Releases** güncelleme yayın yeri olarak seçildi (2026-11-04). `UPDATE_URL` buna göre doldurulacak.
- **v1.4 efektleri** kullanıcı tarafından gözle onaylandı (2026-11-04); aşama kapalı.
- **Karşılama sihirbazı** (5 ekran) kurucu kapsamına dahil; tasarım `design/v2/karsilama-sihirbazi-taslak.html` onaylı.
- **Tek kurucu exe**, çift tıkla kurulum; PyInstaller Python'u içinde taşır (Yol A). Yol B (Python'u sessiz kurma) yalnız Yol A patlarsa devreye girer.
- **Metin sağlayıcısı varsayılanı `none`**, otomatik yapıştırma varsayılan açık (2026-11-01).

### 1.2 2026-11-07'de verilen kararlar (uygulama için bağlayıcı)
1. **Kurulum yeri:** `C:\Program Files\Dikte`; Inno `PrivilegesRequired=admin`. Kurulum ve sessiz güncelleme UAC onayı ister.
2. **Hedef sürüm:** **1.6.0**. Tek kaynak `config.APP_VERSION`; `installer/latest.json` ve Inno `AppVersion` bununla uyumlu olacak.
3. **Kaldırmada veri:** kullanıcı seçecek. İkinci onay ekranında **"Modelleri koru"** kutusu (varsayılan işaretli) gösterilecek; geçmiş, ayarlar, loglar ve geçici dosyalar her durumda silinecek.
4. **Veri silme katmanı:** Inno `[UninstallDelete]` silecek. "Modelleri koru" seçilirse uygulama kaldırıcıyı başlatmadan önce bir bayrak yazacak; Inno `[Code]` bu bayrağa göre `models\` klasörünü atlayacak. Uygulama içi `rmtree` kullanılmayacak.
5. **Depo ve yayın:** depo **public** (`github.com/mete2012seker-lgtm/dikte`). Güncelleme GitHub Releases üzerinden; kurucu ve `latest.json` upload'ını **kullanıcı** yapacak. `UPDATE_URL = https://github.com/mete2012seker-lgtm/dikte/releases/latest/download/latest.json`; indirme yönlendirmeleri için `objects.githubusercontent.com` izinli olacak.
6. **Derleme araçları:** PyInstaller ve Inno Setup bu makineye kurulacak.
7. **CUDA sihirbazı:** yalnız NVIDIA GPU varsa gösterilecek; indirme isteğe bağlı ve atlanabilir.
8. **Selftest sesi:** sentetik TTS ile `tests/data/test.wav` + `test.txt` üretilecek.
9. **7e kalite tablosu:** tamamlanacak (10 girdi/çıktı çifti + VRAM takas ölçümü).
10. **`web/`:** tutulacak; README'de "deneme, üretim arayüzü değil" notu olacak.
11. **Lisans:** MIT.
12. **İkon:** basit bir `.ico` üretilip `Dikte.spec` ve `Dikte.iss`'e bağlanacak.
13. **Eski `data/` taşıma:** **yapılmayacak**; kurulu sürüm temiz başlayacak.

### 1.3 2026-11-11'de verilen kararlar (kullanıcı onaylı)
14. **Sıradaki aşama ve kod başlangıcı:** Kodlama doğrudan başlamayacak; kullanıcı önce `installer\Output\Dikte-Setup-1.6.0.exe` ile kurulum/kaldırma testini yapacak. Yeni oturumda `/asama-baslat` komutuyla model neyi yapacağını/yapmayacağını, hangi testleri koşturacağını ve alt ajan kurallarını madde madde listeleyecek, kullanıcı onay verene kadar kod yazmayacaktır.
15. **Faz 2 uygulama düzeni:** Faz 2'deki 11 veri kaybı ve çökme maddesi tek seferde arka arkaya uygulanacaktır.
16. **Karşılama sihirbazında CUDA:** İsteğe bağlı sunulacak; "İndir" yanında "CPU ile devam et (Atla)" seçeneği bulunacaktır.
17. **Ses modeli indirme kontrolleri:** faster-whisper yapısının kararlılığı için yalnızca "İptal" butonu sunulacaktır.
18. **Selftest ses fixture'ı:** 3 saniyelik sentetik Türkçe ses ("Dikte test kaydı başarılı.") ve `test.txt` üretilecektir.

---

## 2. Faz 0 — Doküman senkronu (bu oturumda yapıldı)

- [x] `uygulanacak plan.md` denetim ve doğrulanmış kod durumuna göre yeniden yazıldı.
- [x] `STATE.md` "Yarım kalan", "Sıradaki ilk adım", "Açık sorunlar" ve test tablosu gerçek duruma çekildi.
- [x] `PLAN.md` 7c/7e/10/11 maddeleri "kod var, doğrulanmadı" olarak işaretlendi.
- [x] `AGENTS.md` proje durumu ve v1.6 yayın yeri notu güncellendi.
- [x] `architecture.md` "Bilinen sorunlar" gelecek zamandan gerçek duruma çevrildi.
- [x] `reports/README.md` denetim raporu satırı eklendi.

**Kanıt:** değişen dosyaların `git diff` çıktısı.

---

## 3. Faz 1 — Yayın blockerları (orta iş, 1–2 oturum)

Amaç: `dist\Dikte` + `Dikte-Setup.exe` üretmek, kur/kaldır ve güncelleme akışını gerçekten çalıştırmak.

### 1.1 Sürümü tek kaynağa indir
- [x] `config.APP_VERSION` **1.6.0**'a çekildi (karar 1.2/2).
- [x] `dikte/__init__.py` sürümü `config.APP_VERSION`'dan türetildi.
- [x] `installer/Dikte.iss` `AppVersion` aynı değeri kullanıyor.
- [x] `installer/latest.json` örnek sürümü aynı değere çekildi.
- [x] `text_models.py` ve `openrouter.py` User-Agent sürümü `config.APP_VERSION`'dan geliyor.
- [x] Test: dört yerde sürüm aynı mı (`tests/test_version.py` geçti).

### 1.2 Güncelleme `sha256` akışını düzelt
- [x] `controller.update_check()` her iki başarı dalında da `sha256` döndürüyor.
- [x] `controller.update_apply()` yeniden denetim yapmak yerine aynı sonucu kullanıyor.
- [x] `sha_mismatch`, `incomplete`, `bad_url` için Türkçe mesaj eklendi.
- [x] Boş `sha256` ile doğrulama reddediliyor (`code="missing_hash"`).
- [x] Test: sahte `latest.json` + sahte kurucu ile başarılı akış; bozuk özet; eksik indirme (`tests/test_updater.py` geçti).

### 1.3 `UPDATE_URL` ve hata mesajı
- [x] GitHub Releases URL'si `config.UPDATE_URL`'e yazıldı: `https://github.com/mete2012seker-lgtm/dikte/releases/latest/download/latest.json`.
- [x] `updater.check()` `None` döndüğünde `update_check` `code="no_url"` ve "Güncelleme sunucusu yapılandırılmamış." diyor.
- [x] `latest.json` gerçek sürüm şablonuyla hazırlandı.

### 1.4 Kaldırmada veri + autostart temizliği
- [x] Inno `[UninstallDelete]` + "Modelleri koru" bayrağı (`[Code]`) uygulandı.
- [x] `%LOCALAPPDATA%\Dikte` altındaki `models\`, `data\`, `logs\` ve `%TEMP%\dikte` temizliği Inno'ya bağlandı.
- [x] HKCU `...\Run\Dikte` kaydı Inno `[Registry]` ve `uninstall.py` ile temizleniyor.
- [x] `data_bytes()` çift sayımı düzeltildi.
- [x] UI metni gerçek davranışla senkronize edildi (`app.js`).
- [x] Test: `tests/test_uninstall.py` eklendi (163 satır, hepsi geçti).

### 1.5 PyInstaller kurucusu
- [x] Üst düzey `run_dikte.py` eklendi; `Dikte.spec` girişi buna çevrildi.
- [x] `hiddenimports`/`collect_all("llama_cpp")` eklendi.
- [x] `datas` hedefini `"dikte/ui"` yapıldı.
- [x] İkon ve sürüm bilgisi bağlandı; `console=False`.
- [x] `requirements-dev.txt`'e PyInstaller eklendi; `build.ps1` yazıldı.
- [x] PyInstaller + Inno Setup çalıştırıldı; `dist\Dikte` ve `installer\Output\Dikte-Setup-1.6.0.exe` (172 MB) üretildi.
- [ ] Kurulu pakette canlı duman testleri: kullanıcı UAC kur/kaldır, model yükleme, kısayol onayı bekliyor.
- **Kanıt:** `installer\Output\Dikte-Setup-1.6.0.exe` (172.888.124 bayt).

### 1.6 Inno Setup düzeltmeleri
- [x] Geçerli sabit GUID kullanıldı (`Dikte.iss:11`).
- [x] `DefaultDirName={autopf}\Dikte` + `PrivilegesRequired=admin` yapıldı.
- [x] `[UninstallDelete]` ve `[Registry]` bölümleri dolduruldu.
- [x] Masaüstü/Başlat menüsü kısayolları ve otomatik başlatma parametreleri bağlandı.

### 1.7 Depo hijyeni (yayın öncesi)
- [x] `.gitignore`'a derleme ve geçici çıktı yolları eklendi.
- [x] `docs/` altındaki 8 adet 0 baytlık dosya silindi.
- [x] `mevcut tasarım/` kopyası silindi.
- [x] `README.md`, `LICENSE` (MIT) eklendi.
- [x] `web/` için not düşüldü.

**Faz 1 bitti tanımı:** Kod tamamlandı, 245 pytest geçti, kurucu derlendi. **Kullanıcı testi bekleniyor:** Kurulum (UAC), kaldırma (modeller korunur/silinir), ilk GitHub Release sonrası canlı güncelleme.

---

## 4. Faz 2 — Veri kaybı ve çökme hataları (2–3 oturum)

- [ ] **Pano hatasında yapıştırma iptal:** `_process` ve otomatik çeviri akışında `if copy_ok and auto_paste` (`controller.py:432-448`, `:1570-1573`).
- [ ] **Kısayol thread'i bloke olmasın:** `on_hotkey_press → toggle_record → load_engine` zincirini worker'a al; bas-bırak olayları kuyruklansın (`controller.py:295-335`, `:218-250`).
- [ ] **İki Whisper modeli yüklenmesin:** `_whisper_loaded` kontrolü ve set'i aynı kilit altında; `_prepare_whisper` bayrağı kilit içinde okusun (`:218-235`, `:261-271`).
- [ ] **Geçmiş kimliği:** `history_open` `_last_history_id`'yi güncellesin; Temizle/Çevir yanlış kaydı ezmesin (`:637-647`, `:1466`, `:1578-1584`).
- [ ] **GGUF indirme yarışı:** indirme başına jeton/thread kimliği; eski worker bitmeden yeni thread başlamasın; `delete_part` yalnız açık iptalde ve worker durduktan sonra çalışsın (`controller.py:978-1026`).
- [ ] **Bütünlük doğrulaması:** GGUF için SHA-256 veya GGUF sihirli baytları; Whisper snapshot için `model.bin` + `config.json` + tokenizer kontrolü (`text_models.py:104-106, 197-200`; `models.py:124-134`).
- [ ] **Kırpılan yanıt:** `finish_reason == "length"` başarı yolunda da hata sayılsın; ≥3 kelimede eksiltme/halüsinasyon koruması (`text_engine.py:202-216, 290-329`).
- [ ] **`strip_response`:** `"i corrected"`, `"note:"` gibi etiketler yalnız çok satırlı meta yanıtlarda temizlensin; gerçek dikte cümlesi silinmesin (`text_engine.py:102-160`).
- [ ] **`audio.stop()`:** `_write_wav` istisnası `AudioError`'a sarılsın; durum `RECORDING`'de kilitlenmesin (`audio.py:92, 101-106`; `controller.py:356-362`).
- [ ] **Ayar/geçmiş kilitleri:** `SettingsStore.save`, `HistoryStore`, `SecretStore` yazımlarına kilit + benzersiz temp + `fsync`; `history.load` yalnız `JSONDecodeError`'da sıfırlasın (`settings.py:178-199`, `history.py:78-82`).
- [ ] **Kapanış:** `_closed` gerçekten okunsun; worker/download thread'leri join edilsin; çıkışta `kayit-*.wav` kalmasın (`controller.py:122, 273-291`).

**Faz 2 bitti tanımı:** Her madde için hata üreten test önce yazılır (kırmızı), düzeltme sonrası yeşil; pano hatasında eski pano yapıştırılmıyor; iki model aynı anda yüklenmiyor.

---

## 5. Faz 3 — Ürün bütünlüğü (3–5 oturum)

### 3.1 Karşılama sihirbazı (5 ekran)
- [ ] `settings.json`'a `setup_done` ekle; ilk açılışta göster, bir kez çalıştır.
- [ ] `#sayfa-kurulum` + adım göstergesi + ileri/geri/atla.
- [ ] Ekranlar: hoş geldin, ses modeli seçimi/indirme, GPU/CUDA bileşeni (isteğe bağlı ve atlanabilir, karar 1.3/16), metin sağlayıcısı, bitiş.
- [ ] Sihirbaz sırasında kısayol dinleyicisi başlamasın; bitişte başlasın.
- [ ] Magic UI efektleri (MagicCard, ShineBorder, DotPattern) ve `prefers-reduced-motion` uyumu.
- [ ] Playwright: 5 ekran, atlama, karanlık mod, `setup_done` kalıcılığı.

### 3.2 Diğer ürün eksikleri
- [ ] `input_language` motora bağlansın: `auto` → `language=None`, `tr` → `"tr"` (`engine.py:157`).
- [ ] `snapshot.ai` içine `state` eklensin; Temizle/Çevir düğmeleri loading/recording durumunda doğru kapansın (`controller.py:613`, `:1181-1208`; `app.js:1122`).
- [ ] 7c "⋯" model menüsü ekle (eylemler kart üstünde dağınık kalmasın).
- [ ] Ses modeli indirmesinde iptal butonu ekle (karar 1.3/17).
- [ ] Temizle/Çevir'i arka plan thread'ine al; ilerleme/iptal; otomatik çeviride `CLEANING` durumunu kullan (`state.py:15-21`).
- [ ] `refresh_last` otomatik çeviriyi de uygulasın; ham Whisper metni çevrilmiş metnin üzerine yazılmasın (`controller.py:530-573`).
- [ ] UI yarışları: kaydedilmemiş ayar koruması, `outputLang`/`autoTranslate` poll ezmesi, async jetonlar, düğme toparlanması, `updateNotes` gösterimi (`app.js:255, 1123-1124, 1373-1414, 1811-1829`).
- [ ] Kaldırma/otomatik başlatma geliştirme modunda düzgün davransın (`uninstall.py:83`; `app.js:1722-1737`).

### 3.3 Yayın kararları
- [ ] Güncellemeyi arka plan thread'ine al; ilerleme göster; kurulumdan önce uygulamayı kapat; kurulum sonrası yeniden aç.
- [ ] `compare_versions` ön sürüm (beta/rc) önceliğini doğru ele alsın (`updater.py:40-47`).
- [ ] `update_last_check` UTC kaydedilip yerel saat gösterilsin (`controller.py:1293, 1210-1218`).

---

## 6. Faz 4 — Test, hijyen ve kapanış (1 oturum)

- [ ] `tests/data/test.wav` + `test.txt` ekle (3 sn sentetik Türkçe TTS, karar 1.3/18); `--selftest` gerçekten çalışsın.
- [ ] Test boşlukları: gerçek `update_check` + `update_apply`, kaldırma, autostart, `snapshot.ai.state`, geçmiş dönem filtresi.
- [ ] Playwright'ı gerçek tarayıcıda koştur; ekran görüntülerini `design/v2/` ile karşılaştır.
- [ ] `reports/2026-11-04-7e-kalite-tablosu.md` tamamlanacaksa 10 girdi/çıktı çifti + VRAM takas ölçümü ekle; yoksa PLAN'da "kısmen" olarak kalsın.
- [ ] README/LICENSE/CI tamamla; `web/` kararını uygula.
- [ ] `/asama-bitir` ile STATE, PLAN, AGENTS, architecture, ogrenme-gunlugu güncelle; commit + push.

---

## 7. Sıra, bağımlılık ve maliyet

| Faz | İş | Bağımlılık | Büyüklük |
| :--- | :--- | :--- | :--- |
| 0 | Doküman senkronu | — | Küçük (bu oturum) |
| 1 | Yayın blockerları | Kararlar 1.2/1–4 | Orta (1–2 oturum) |
| 2 | Veri kaybı/çökme | Faz 1 (yeşil test tabanı) | Orta-büyük (2–3 oturum) |
| 3 | Ürün bütünlüğü | Faz 1 + 2 | Büyük (3–5 oturum) |
| 4 | Test/hijyen/kapanış | Hepsi | Küçük (1 oturum) |

Para maliyeti: **yok** (tüm iş yerel; OpenRouter yalnız isteğe bağlı testlerde, ~$0,001).

## 8. Riskler ve zayıf noktalar
- **PyInstaller + pywebview + faster-whisper** paketlemesi patlayabilir; Yol A başarısızsa Yol B (Python'u sessiz kurma) devreye girer ve internet gerekir.
- **Kurucu ~200 MB**; her güncellemede tam indirme yapılır (artımlı yama yok).
- **Antivirüs** imzasız kurucuya uyarı verebilir; kod imzalama kapsam dışı.
- **Program Files seçildi** (karar 1.2/1); kurulum ve sessiz güncelleme UAC onayı isteyecek. Güncelleme testi bu onayla yapılmalı.
- **Sentetik TTS** kalite tablosu gerçek konuşmadan daha iyi sonuç verir; ölçüm "en iyi durum" olarak yorumlanır.

## 9. Bitti tanımı (her faz için)
1. Çalışan sonuç (komut/çıktı).
2. Kanıt: pytest çıktısı, ekran görüntüsü, dosya yolu veya kurulum logu.
3. Kullanıcı için 5 maddelik sade özet.
4. Kullanıcının doğrulaması gerekenler "SENİN YAPACAĞIN TEST:" başlığıyla ayrı yazılır.

## 10. Doğrulanamayanlar ve test maskeleri (`calisma-duzeni.md` §4–8)
- **Gerçek mikrofon, GPU, kurulum ve güncelleme** bu ortamda çalıştırılamadı; ilgili maddeler statik kanıt + kullanıcı testine dayanıyor.
- **Test maskesi — güncelleme:** `test_ui.py` sahte `update_check` yanıtına `sha256` koyuyor ve `update_apply`'ı köprüde taklit ediyor; gerçek `sha256` hatası bu testle yakalanamıyor.
- **Test maskesi — AI durumu:** `test_ui.py:93` `ai.state` enjekte ediyor; `snapshot.ai` içinde `state` olmaması maskeleniyor.
- **Test maskesi — geçmiş filtresi:** `history_list` sahtesi `period` parametresini yok sayıyor; Bugün/Bu hafta filtresi test edilmiyor.
- **Eksik test dosyası:** `tests/test_uninstall.py` yok; `is_installed`, `data_bytes`, `set_autostart`, `autostart_enabled`, `run_uninstaller` test edilmiyor.
- **Eksik fixture:** `tests/data/test.wav` ve `test.txt` yok; `--selftest` hiç çalıştırılamıyor.
- **Playwright:** 25 test var; gerçek tarayıcı koşumu bu makinede doğrulanmadı.
- **7e kalite tablosu:** sentetik TTS ile üretildiği için "en iyi durum" ölçümü; gerçek konuşma performansı ölçülmedi.