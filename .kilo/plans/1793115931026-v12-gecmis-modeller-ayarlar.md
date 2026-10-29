# v1.2 Planı — Dikte Geçmişi, Modeller, Ayarlar, Yenile

Hedef: Uygulamanın dört menüsü de çalışsın. Geçmiş kalıcı ve yönetilebilir, ses modelleri indirilip aktifleştirilebilir/silinebilir, ayarlarda kısayol ve "geçmişi kaydet" değiştirilebilir, Dikte ekranındaki "Transkripsiyonu Yenile" gerçekten çalışır. Dil seçici pasif kalır. Metin modelleri ve "Yapay Zeka ile Temizle" kapsam dışı.

## Kullanıcı onaylı kararlar

1. Python 3.12'ye bu sürümün işlerinden **önce** geçilecek.
2. Ayarlar kapsamı: **"Geçmişi kaydet" anahtarı + kısayol tuşu**. Dil ve mikrofon seçimi yok; dil pasif.
3. Kısayol **hazır listeden** seçilir, serbest tuş yakalama yok.
4. "Geçmişi kaydet" kapalıyken eski kayıtlar **gizlenir, arşivde durur**; anahtar açılınca geri gelir.
5. Model listesi **6 model**: Tiny, Base, Small, Medium, Large-v3, Large-v3 Turbo. Yalnız ses modelleri.
6. "Transkripsiyonu Yenile" için son kayıt **geçici dosyada** tutulur; uygulama kapanınca silinir.
7. Yenile sonucu **son paragrafı değiştirir** ve geçmişteki son kaydı günceller.

## Aşama 0 — Python 3.12 (özelliklerden önce)

1. `winget install -e --id Python.Python.3.12` (yönetici onayı gerekebilir). `py -0p` ile doğrula.
2. `.venv` → `.venv310-yedek` olarak yeniden adlandır; `py -3.12 -m venv .venv`.
3. `.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`.
4. Doğrulama: `python --version` = 3.12.x, `pytest -q` tüm testler geçer, `python -m dikte --selftest` GPU/float16 ile metin üretir.
5. Hepsi geçerse `.venv310-yedek` silinir. Geçmezse yedek geri alınır, STATE.md'ye hata yazılır ve durulur.
6. `models/` klasörüne dokunulmaz.

Kabul: 3.12 aktif venv + testler + gerçek GPU selftest. Bu adım geçmeden özellik kodu yazılmaz.

## Aşama 1 — Veri katmanı: ayarlar ve geçmiş

### `dikte/config.py`
- `DATA_DIR = ROOT_DIR / "data"` (`DIKTE_DATA_DIR` ile değiştirilebilir).
- `SETTINGS_FILE = DATA_DIR / "settings.json"`, `HISTORY_FILE = DATA_DIR / "history.json"`.
- `LAST_RECORDING = TEMP_DIR / "last.wav"`, `HISTORY_LIMIT = 500`.
- `ensure_runtime_dirs()` içine `DATA_DIR` eklenir.
- `.gitignore`'a `data/` satırı eklenir (konuşma metinleri ve ayarlar git'e girmez).

### `dikte/settings.py` (yeni)
- Şema: `{"version": 1, "save_history": true, "hotkey": "right_ctrl", "active_model": "auto"}`.
- `load()` bozuk/eksik alanları varsayılanla tamamlar; bozuk dosyayı `settings.bozuk-<zaman>.json` olarak kenara alır.
- `save(**changes)` atomik yazar (`.tmp` + `os.replace`).
- `HOTKEY_CHOICES`: `right_ctrl` "Sağ Ctrl", `left_ctrl` "Sol Ctrl", `right_alt` "Sağ Alt", `left_alt` "Sol Alt", `f8`, `f9`, `f10`.

### `dikte/history.py` (yeni)
- Kayıt: `id` (`YYYYMMDD-HHMMSS-<sayaç>`), `created_at` ISO, `duration` (sn), `words`, `model`, `text`.
- `add(text, duration, words, model)`, `list(query="", period="all")` (yeni → eski), `get(id)`, `delete(id)`, `clear()`, `update_last(text)`.
- Filtreler: `today`, `week` (pazartesi başlangıçlı).
- Arama: Türkçe küçük harfe çevirme (I/İ/ı/i) + `casefold`; metin ve tarih üzerinde.
- `HISTORY_LIMIT` aşılırsa en eski kayıtlar atılır.
- Bozuk JSON: dosya `history.bozuk-<zaman>.json` olarak kenara alınır, boş listeyle devam edilir; hiçbir kayıt sessizce silinmez.
- Atomik yazma; tüm dosya işlemleri kısa süreli kilit altında, controller kilidi dışında çağrılır.

## Aşama 2 — Kısayol ve motor

### `dikte/hotkey.py`
- `HotkeyListener(press_cb, release_cb, key="right_ctrl")`; tuş eşlemesi modül içinde (`Key.ctrl_r`, `Key.ctrl_l`, `Key.alt_r`, `Key.alt_l`, `Key.f8/f9/f10`).
- `set_key(key_id)` mevcut dinleyiciyi durdurup yenisini başlatır; başarısızsa eski tuşa geri döner ve `HotkeyError` fırlatır.
- Kısayol kaydı sürerken değiştirilemez (controller engeller).

### `dikte/engine.py`
- `TranscriptionEngine(model_name=None)`; `set_model(name)` / `unload()`.
- Plan: seçili model varsa `[(model, gpu/cpu, compute)]`; GPU hatasında **aynı model CPU/int8**, o da olmazsa mevcut `small/int8` yedeği.
- Seçili model diskte yoksa `auto` plana (large-v3 → small) düşer, `warnings`'e Türkçe not ekler.
- `load()` mevcut kilitli controller akışını bozmayacak şekilde yalnız worker thread'den çağrılır.

## Aşama 3 — Model yöneticisi `dikte/models.py` (yeni)

- `SPEECH_MODELS`: name, label, açıklama, yaklaşık indirme boyutu, etiketler (doğruluk/hız), sıralama.
  - tiny, base, small, medium, large-v3, large-v3-turbo.
- `installed_size(name)`: `models--Systran--faster-whisper-<name>/snapshots/*/model.bin` gerçek boyutu; eksik/yarım indirme `partial` sayılır.
- `download(name, progress_cb, cancel_event)`: `faster_whisper.utils.download_model` worker thread'de; ilerleme klasör boyutu 500 ms'de bir okunarak `{downloaded_bytes, total_bytes, percent}` üretilir.
- `delete(name)`: `models--Systran--faster-whisper-<name>` klasörünü ve `.locks` girdisini siler; hata Türkçe mesaja çevrilir.
- CLI `--kurulum` bu modülü kullanacak şekilde sadeleştirilir (davranış aynı kalır).

## Aşama 4 — Controller ve köprü

### `dikte/controller.py`
Yeni enjeksiyonlar: `settings_store`, `history_store`, `model_manager` (testlerde sahte).
- Açılış: ayarları yükle; `save_history` ve `hotkey` uygula; son model adı diskte varsa onu yükle; eski `last.wav` varsa sil.
- Dikte başarılıysa: metin panoya, `settings.save_history` açıksa geçmişe kaydet, `last.wav` olarak sakla (önceki silinir), `seq += 1`.
- `shutdown()`: `last.wav` silinir.
- Geçmiş kapalıyken `history_list` `{"disabled": true, "items": []}` döner; mevcut dosya okunmaz/gösterilmez, silinmez.
- `history_open(id)`: kayıt metnini `latest_text` + `seq += 1` ile Dikte ekranına yeni paragraf olarak verir.
- `history_delete`, `history_clear`.
- `models_list`: ad, etiket, gerçek boyut, `installed`, `active`, `downloading`.
- `model_download(name)`: tek eşzamanlı indirme; durum `snapshot()["download"]` içinde (`name`, `percent`, `state`, `error`).
- `model_activate(name)`: kayıt/işleme sırasında reddedilir; `LOADING` durumuna geçer, eski modeli boşaltır, yeni modeli thread'de yükler, başarıda `active_model` ayarını yazar ve etkinlik ekler; hatada eski modelle `READY`'ye döner.
- `model_delete(name)`: aktif veya indirilmekte olan model silinemez; onay UI'da alınır.
- `set_hotkey(key_id)`: kayıt sürerken reddedilir; dinleyici yeniden başlatılır, ayar yazılır, hata halinde geri alınır.
- `settings_save({save_history, hotkey})`: tek atomik yazma; hotkey değiştiyse önce uygula.
- `refresh_last()`: `READY` + `last.wav` varsa `PROCESSING`; aynı sesi çevirir, metni panoya yazar, `seq += 1` + `replace_last: true`, geçmiş açıksa son kaydı `update_last` ile günceller; seste yoksa `{ok: false, message: "Yenilenecek kayıt yok."}`.
- `snapshot()` ek alanları: `save_history`, `hotkey`, `can_refresh`, `download`.

### `dikte/ui/bridge.py`
JS'e açılan yeni metotlar:
`history_list(query, period)`, `history_open(id)`, `history_delete(id)`, `history_clear()`, `models_list()`, `model_download(name)`, `model_activate(name)`, `model_delete(name)`, `settings_get()`, `settings_save(payload)`, `refresh_last()`.

## Aşama 5 — Arayüz

### `dikte/ui/index.html`
- Menü düğmelerine `data-page` (`page-dikte`, `page-gecmis`, `page-modeller`, `page-ayarlar`) ve `aria-current`.
- Dikte içeriği `<section class="page is-active" id="page-dikte">` içine alınır; sağ panel ve alt çubuk yalnız Dikte'de görünür.
- **Geçmiş sayfası** (`ui-spec.md` 5.11): arama, Tümü/Bugün/Bu hafta, kayıt sayısı, satırlar (tarih/saat, süre, kelime, önizleme, Aç/Kopyala/Sil). Kapalıyken tek bilgi kartı: "Geçmiş kaydedilmiyor" + "Ayarlara git" düğmesi.
- **Modeller sayfası** (5.8–5.9): yalnız "Ses Modelleri (6)"; sekme yok, "Model Ekle" yok. Kartta ad, açıklama, etiket, boyut, durum, İndir/Aktifleştir düğmesi ve Sil. Sağda Model Detayları + Model Açıklaması panelleri.
- **Ayarlar sayfası** (5.12, 900 px): iki kart.
  - Kısayol Tuşu: hazır liste (7 seçenek) + "Bir tuşa basın…" yerine açılır liste; kayıt sürerken pasif.
  - Geçmiş: "Dikte geçmişini kaydet" anahtarı + "Geçmişi temizle" (onaylı).
  - Alt satır: "Kaydet" (birincil), "Varsayılana dön"; değişiklik varsa "Kaydedilmedi" ipucu.
- "Transkripsiyonu Yenile" düğmesinden `v1.1` etiketi ve `disabled` kaldırılır; `can_refresh` false ise pasif.
- Dil seçici ve "Yapay Zeka ile Temizle" pasif kalır; `span.soon` etiketleri güncellenir.

### `dikte/ui/style.css`
- Sayfa yönlendirici (`.page{display:none}` / `.page.is-active`), Geçmiş, Modeller, Ayarlar stilleri `design/prototype.html` ve `ui-spec.md` değerlerinden port edilir.
- Bilgi şeridi, boş durum, indirme ilerleme çubuğu, silme onayı, pasif düğme durumları.

### `dikte/ui/app.js`
- Sayfa yönlendirici: tıklamada sayfa değişir, `aria-current` güncellenir, o sayfanın verisi tazelenir; sayfa değişince toast temizlenir.
- Polling: Dikte için `snapshot()` 250 ms; Modeller açıkken `models_list()` 800 ms; indirme varken 500 ms.
- Geçmiş: arama 250 ms gecikmeli, filtre hapları, satır işlemleri; silmede 200 ms solma; "Aç" Dikte'ye geçer.
- Modeller: indir → ilerleme; aktifleştir → "Model yükleniyor"; sil → `confirm()`; hata toast'ı; aktif model kartında rozet.
- Ayarlar: kirli durum takibi, Kaydet → `settings_save`, hata halinde geri alma, Varsayılana dön → onay.
- Yenile: `refresh_last()`; `replace_last` gelince son paragraf değiştirilir, yoksa eklenir; düğme metni "Yenileniyor…" olur.
- `snapshot.seq` artışı `replace_last` bayrağına göre ekle/değiştir yapar.

## Aşama 6 — Test stratejisi

Test piramidi: çok sayıda hızlı birim testi, orta sayıda controller testi, az sayıda arayüz testi, en üstte gerçek uygulama doğrulaması. Her katman kendi hızında çalışır; ağ, GPU ve mikrofon üst katmanlara aittir.

### 6.1 Birim testleri (pytest, hızlı, ağ/GPU yok)

Tüm dosya testleri `tmp_path` ve ortam değişkenleriyle (`DIKTE_DATA_DIR`, `DIKTE_MODELS_DIR`, `DIKTE_TEMP_DIR`) gerçek proje klasöründen ayrılır; testler birbirinin verisini ezmez.

- `tests/test_settings.py`:
  - Dosya yoksa varsayılanlar (`save_history=true`, `hotkey=right_ctrl`, `active_model=auto`).
  - Kaydet → yeniden yükle aynı değerler.
  - Bozuk JSON → varsayılan + `.bozuk-*` yedeği; çökme yok.
  - Bilinmeyen alan korunur, bilinmeyen tuş reddedilir veya varsayılana döner.
  - `.tmp` dosyası yazımdan sonra kalmaz (atomik yazma).
- `tests/test_history.py`:
  - Ekleme sırası (yeniden eskiye), tarih formatı, süre/kelime alanları.
  - Türkçe arama: "ı", "İ", "I", "i" karışık; "ISPARTA" ↔ "ısparta" eşleşir.
  - `today` / `week` filtreleri sabit `now` enjekte edilerek (pazartesi sınırı dahil).
  - Silme, temizleme, olmayan id, 500 kayıt sınırında en eskinin düşmesi.
  - Bozuk JSON → boş liste + yedek dosya.
  - `update_last` yalnız son kaydı değiştirir, sayıyı artırmaz.
- `tests/test_models.py`:
  - Katalogda tam 6 model, adlar ve etiketler doğru.
  - Sahte `models--Systran--faster-whisper-small/snapshots/x/model.bin` ile kurulu boyut hesabı.
  - `model.bin` yoksa `partial`, hiç klasör yoksa `not_installed`.
  - Silme sahte klasörü kaldırır; olmayan modelde anlaşılır hata.
  - İlerleme hesabı: sahte boyut okuma dizisiyle yüzde 0 → 50 → 100.

### 6.2 Controller testleri (sahte bileşenler, gerçek thread yok)

Mevcut `tests/test_controller.py` deseni korunur: `FakeEngine`, `FakeRecorder`, `FakeHotkey`, `FakeClipper`. Motor yükleme/çeviri anında döner; `wait_until_ready()` ile beklenir. Yeni vakalar:

- Geçmiş açıkken başarılı dikte kayıt ekler; kapalıyken eklemez; kapalıyken `history_list` `disabled` döner ve dosya silinmez.
- `history_open` metni `latest_text` olarak verir, `seq` artar.
- `refresh_last`:
  - Ses yokken `ok=false`.
  - Ses varken motor ikinci kez çağrılır, `replace_last=true`, `seq++`, pano güncellenir.
  - Geçmiş açıksa son kaydın metni değişir; kapalıysa geçmiş dosyasına dokunulmaz.
- `model_activate`:
  - Kayıt/işleme sırasında reddedilir.
  - `LOADING → READY` geçişi, `active_model` ayarının yazılması, etkinlik kaydı.
  - Motor hatasında eski modelle `READY`'ye dönüş ve Türkçe hata.
- `model_delete`: aktif model ve indirilen model reddedilir.
- `set_hotkey`: kayıt sırasında reddedilir; `HotkeyError` alınınca ayar eski değerde kalır.
- İndirme: sahte `model_manager` ile aynı anda ikinci indirme reddedilir; durum `snapshot()["download"]` içinde görünür.

### 6.3 Arayüz testleri (Playwright + msedge, sahte köprü)

`tests/test_ui.py` içindeki `STUB` genişletilir; gerçek Python çalışmaz, ağ yok. Her test `page.goto()` ile temiz başlar, `wait_for_function` ile durum bekler.

- Sayfa yönlendirme: dört menü düğmesi doğru `section`'ı açar, `aria-current` taşınır, Dikte'ye dönünce metin korunur.
- Geçmiş: dolu liste (tarih, süre, kelime, önizleme), arama kutusu, filtre hapları, Aç → Dikte'ye geçiş ve paragraf, Kopyala → `window.__copied`, Sil → satır kaybolur, kapalıyken yalnız "Geçmiş kaydedilmiyor" kartı.
- Modeller: 6 kart, kurulu/kurulu değil/aktif rozetleri, indirme ilerleme çubuğu, aktifleştirme sırasında düğme kilidi, silme onayı reddedilince istek gitmemesi.
- Ayarlar: kısayol listesi, geçmiş anahtarı, Kaydet → `settings_save` çağrısı ve "Kaydedildi" bildirimi, hata → geri alma, Varsayılana dön.
- Yenile: `can_refresh=false` iken pasif; tıklanınca `refresh_last` çağrılır; `replace_last` snapshot'ı son paragrafı değiştirir, yenisini eklemez.
- Ekran görüntüleri 1600×1000: `artifacts/ui-gecmis.png`, `artifacts/ui-modeller.png`, `artifacts/ui-ayarlar.png`; görsel değerler `ui-spec.md` ile karşılaştırılır.
- Mevcut `test_v11_ozellikleri_pasif` güncellenir: Modeller artık toast değil gerçek sayfa açar; dil ve "Yapay Zeka ile Temizle" pasif kalır.

### 6.4 Motor testi (gerçek, ama kısa)

- `python -m dikte --selftest` gerçek `tests/data/test.wav` ile GPU/float16 çalışır; çıktıda cihaz, model, süre ve metin görülür.
- Model değiştirme testi için tiny modeli gerçek diskte kullanılır; iki modelin art arda yüklenip boşaltıldığı `--selftest` benzeri küçük bir betikle doğrulanır.

### 6.5 Ağ ve gerçek indirme

- Otomatik testlerde indirme **monkeypatch** ile sahtelenir; ağa çıkılmaz.
- Gerçek indirme yalnız elle doğrulamada: tiny silinir, yeniden indirilir (72 MB). Bu, Hugging Face bağlantısını ve klasör düzenini gerçek koşulda sınar.
- İndirme sırasında ilerleme yüzdeleri ve hata mesajı STATE.md'ye kanıt olarak yazılır.

### 6.6 Regresyon ve kanıt

- v1'den kalan tüm testler geçmeye devam eder; kırılan test güncellenirken nedeni commit/STATE notuna yazılır.
- Kanıt: `pytest -q` çıktısı (toplam test sayısı), `--selftest` çıktısı, üç ekran görüntüsü, gerçek indirme logu, uygulama açılışında `ready` durumu.
- Testler hızlı kalır: birim + controller < 10 sn; arayüz testleri tarayıcı açılışı nedeniyle daha yavaş, ayrı işaretlenir.

### 6.7 Ajanın doğrulayamadıkları (senin testin)

Aşağıdakiler "SENİN YAPACAĞIN TEST:" başlığıyla ayrıca verilir: gerçek mikrofonla kayıt, F9 kısayolunun Not Defteri'nde çalışması, panoya yapıştırma, indirme sırasında internet kesintisi, 8 GB VRAM'de large-v3 + tarayıcı birlikte.

## Aşama 7 — Gerçek doğrulama (elle + otomatik)

1. `pytest -q` tümü geçer.
2. `python -m dikte --selftest` GPU/float16.
3. Uygulama açılır; gerçek dikte → Geçmiş'te kayıt; arama/filtre/Aç/Kopyala/Sil.
4. Ayarlar → geçmişi kapat → Geçmiş sayfası "Geçmiş kaydedilmiyor"; yeni dikte kaydedilmez; aç → eski kayıtlar geri gelir.
5. Ayarlar → kısayolu F9 yap → Not Defteri'nde F9 ile dikte; uygulama yeniden açılınca F9 korunur.
6. Modeller → tiny'yi sil, yeniden indir (72 MB, gerçek ağ), aktifleştir, dikte et.
7. Dikte et → Yenile → son paragraf değişir, pano güncellenir, geçmiş son kaydı güncellenir.
8. Uygulama kapanınca `%TEMP%\dikte\last.wav` silinmiş olur.

## Doküman ve hafıza güncellemeleri (aşama sonunda)

- `AGENTS.md`: geçici wav kuralı güncellenir ("son kayıt, yenile için uygulama kapanana kadar tutulur; yeni diktede üzerine yazılır"), model listesi ve ayar kapsamı eklenir.
- `PLAN.md`: Aşama 5 kapsamı yeniden yazılır (geçmiş + ayarlar), Aşama 6 model yönetimi olarak işaretlenir; dil/mikrofon/metin modelleri sonraki sürüme taşınır.
- `STATE.md`, `architecture.md`, `ogrenme-gunlugu.md`: yeni modüller (`settings.py`, `history.py`, `models.py`), API metotları, test sayısı ve kararlar.
- `design/ui-spec.md`: yalnız gerçekten sapan değerler varsa güncellenir; tasarım kaynağı korunur.

## Riskler ve önlemler

- **Python 3.12 / CUDA:** venv yeniden kurulumu; yedek venv geri dönüş. Modeller etkilenmez.
- **Model indirme:** yarım indirme klasörü "eksik" sayılır, ilerleme boyuttan okunur; iptal yok. Disk alanı kontrolü hata mesajıyla bildirilir.
- **Windows dosya kilidi:** aktif model silinemez; silme hatası Türkçe mesaja çevrilir.
- **pynput yeniden başlatma:** hata halinde eski tuş geri yüklenir; kayıt sürerken değişiklik reddedilir.
- **Geçmiş gizliliği:** kapalıyken API kayıt döndürmez; arşiv dosyası silinmez. Wav yalnız son kayıt, uygulama kapanınca silinir.
- **Thread ve kilit:** dosya G/Ç kilit dışında; snapshot kısa kilitli. Model yükleme/indirme worker thread.
- **Playwright stub:** yeni API metotları eklenmezse testler kırılır; stub birlikte güncellenir.

## Kapsam dışı

- Dil seçimi ve mikrofon seçimi (pasif kalır).
- Metin modelleri ve "Yapay Zeka ile Temizle".
- Model indirmeyi iptal etme, duraklatma.
- Sistem tepsisi, otomatik güncelleme.
- Ayarların buluta yedeklenmesi.

## Açık nokta

- Python 3.12 kurulumu Windows yönetici onayı isteyebilir; kurulum başlatıldığında kullanıcı onayı gerekir. Onay verilmezse Aşama 0 durur ve özelliklere geçilmez.
