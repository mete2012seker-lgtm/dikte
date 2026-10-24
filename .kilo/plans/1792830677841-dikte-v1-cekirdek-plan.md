# Dikte v1 — Çekirdek + Dikte Ekranı Uygulama Planı

## 1. Hedef
Kullanıcının kendi bilgisayarında çalışan, Sağ Ctrl ile konuşup bırakınca Türkçe metni panoya kopyalayan ve sonucu tasarımlı Dikte ekranında gösteren ilk sürüm.

**v1 bittiğinde:** `python -m dikte` çalışır, pencere açılır, GPU/CPU modu görünür, Sağ Ctrl ile dikte yapılır, metin hem ekranda hem panoda olur.

Kapsam kararı: **Aşama 0–4** (Ortam, motor, kayıt/kısayol/pano, arayüz kabuğu, Dikte entegrasyonu).

## 2. Kapsam

### v1'de çalışacak
- Python 3.12 + `.venv`, Windows'ta çalıştırma.
- faster-whisper ile yerel çeviri: GPU varsa `large-v3` + `float16`, GPU çalışmazsa `small` + `int8` (CPU). Hangi modda çalıştığı ekranda yazar.
- Sağ Ctrl **basılı tut → kayıt**, bırak → çeviri, sonuç panoya.
- Arayüzdeki mikrofon düğmesi: tıkla başlat, tıkla durdur (aynı durum makinesi).
- Dikte ekranı: canlı durum (Model yükleniyor / Dinlemeye hazır / Dinleniyor / İşleniyor / Hata), dalga formu animasyonu, metin kutusu, Kopyala, Geri Al.
- Sağ panel: gerçek aktif model, gerçek cihaz (GPU/CPU), gerçek bellek kullanımı, bellekte tutulan gerçek "Son etkinlikler".
- Başlangıç ve bitişte kısa ses tonu; geçici `.wav` çeviriden sonra silinir.

### v1'de kapsam dışı (v1.1+)
- Dikte Geçmişi sayfası ve kalıcı geçmiş (Aşama 5).
- Ayarlar sayfası, kısayol değiştirme, mikrofon seçimi (Aşama 5).
- Modeller sayfası, model indirme/silme/aktifleştirme (Aşama 6).
- "Yapay Zeka ile Temizle" ve metin modelleri (Aşama 7).
- "Transkripsiyonu Yenile" (ses dosyası gizlilik gereği silindiği için yeniden çevrilemez).
- Sistem tepsisi, arka planda pencere kapalı çalışma, tek `.exe` paketleme (Aşama 8).
- Türkçe dışı diller; dil seçici yalnızca "Türkçe" gösterir ve pasiftir.
- Özel (frameless) pencere çerçevesi; v1'de Windows'un normal pencere çerçevesi kullanılır.

## 3. Onaylanan ve varsayılan kararlar

| # | Karar | Durum |
| :--- | :--- | :--- |
| 1 | Python 3.12, faster-whisper, tamamen yerel | Onaylı (AGENTS.md) |
| 2 | GPU: large-v3 + float16; CPU: small + int8 | Onaylı |
| 3 | Kısayol varsayılan Sağ Ctrl, basılı tut-bırak | Onaylı |
| 4 | Çıktı yalnızca panoya (otomatik yapıştırma yok) | Onaylı |
| 5 | Arayüz pywebview + mevcut HTML/CSS/JS | Onaylı (bu oturum) |
| 6 | v1 kapsamı: çekirdek + Dikte ekranı | Onaylı (bu oturum) |
| 7 | Model indirme: `python -m dikte --kurulum` komutu (konsolda ilerleme); uygulama model yoksa Türkçe uyarı verir | **Varsayılan** — soru yarıda kaldı, uygulamaya başlarken teyit alınmalı |
| 8 | Metin ekleme: her kayıt yeni paragraf olarak eklenir; Kopyala tüm metni, Geri Al son paragrafı alır | Varsayılan |
| 9 | Pencere kapatılınca uygulama çıkar; tepsi yok | Varsayılan |
| 10 | Diğer sayfalar menüde görünür ama "v1.1'de gelecek" bilgisi verir | Varsayılan |

## 4. Mimari

### Akış
```
Sağ Ctrl basılı ──▶ AudioRecorder (16 kHz, mono, int16, bellekte)
Sağ Ctrl bırak ──▶ Controller: processing
                ──▶ Engine.transcribe(wav)  (worker thread)
                ──▶ pano (pyperclip)
                ──▶ geçici wav sil
                ──▶ UI: yeni paragraf + etkinlik
```

UI, Python'u **200 ms'de bir `snapshot()` çağrısıyla** yoklar. Böylece Python'dan arayüze thread'ler arası zorunlu `evaluate_js` çağrısı yapılmaz; ilk sürüm için en sağlam yol budur.

### Bileşenler
| Bileşen | Dosya | Görev | Bağımlılık |
| :--- | :--- | :--- | :--- |
| Giriş noktası | `dikte/__main__.py` | `--kurulum`, `--selftest`, normal başlatma | controller, engine |
| Ayarlar/sabitler | `dikte/config.py` | Yollar (`models/`, `%TEMP%\dikte`), sabitler (dil `tr`, kısayol, model adları) | — |
| Durum makinesi | `dikte/state.py` | loading/ready/recording/processing/error; geçiş kuralları; saf mantık | — |
| Motor | `dikte/engine.py` | Cihaz algılama, model yükleme, çeviri, GPU→CPU düşüşü | faster-whisper, ctranslate2 |
| Kayıt | `dikte/audio.py` | sounddevice ile kayıt, geçici wav yazma/silme, süre kontrolü | sounddevice, wave |
| Kısayol | `dikte/hotkey.py` | pynput ile Sağ Ctrl bas/bırak, tekrar tuşları yok say | pynput |
| Pano | `dikte/clipboard.py` | Metni panoya yaz | pyperclip |
| Orkestratör | `dikte/controller.py` | Kilit, durum geçişleri, worker thread, etkinlik listesi, snapshot | tümü |
| Teşhis | `dikte/diagnostics.py` | VRAM/RAM okuma, Türkçe hata metinleri, log | pynvml, psutil |
| Arayüz köprüsü | `dikte/ui/bridge.py` | `snapshot`, `toggle_record`, `copy` API'si; pywebview penceresi | pywebview |
| Arayüz | `dikte/ui/index.html`, `style.css`, `app.js` | Dikte ekranı; `design/prototype.html`'den türetilir | bridge |
| Testler | `tests/` | pytest + Playwright | pytest, playwright |
| Model dosyaları | `models/` | git'e girmez | — |

### Durum makinesi
| Durum | Anlamı | İzin verilen geçiş |
| :--- | :--- | :--- |
| `loading` | Model belleğe yükleniyor | ready, error |
| `ready` | Dikteye hazır | recording, error |
| `recording` | Mikrofon açık | processing (bırak), error |
| `processing` | Çeviri sürüyor | ready, error |
| `error` | Kurtarılamaz hata | ready (yeniden dene) |

Kurallar:
- `processing` sırasında yeni kayıt isteği yok sayılır; UI "İşleniyor, bitince tekrar dene" gösterir.
- 0,4 saniyeden kısa kayıt çevrilmez, "Ses algılanamadı" etkinliği düşer.
- Sessiz kayıtta `vad_filter=True`, `condition_on_previous_text=False`; boş sonuç metne eklenmez.
- Aynı anda tek kayıt; kilit `threading.Lock` ile korunur.

### Arayüz köprüsü (pywebview `js_api`)
| Metot | Dönüş | Açıklama |
| :--- | :--- | :--- |
| `snapshot()` | `{state, seq, latest_text, device, model, memory:{used,total,unit}, activity:[], error}` | JS 200 ms'de bir çağırır |
| `toggle_record()` | `{ok, state}` | Mikrofon düğmesi; kısayolla aynı yolu kullanır |
| `copy(text)` | `{ok}` | Panoya yaz; `navigator.clipboard` kullanılmaz (file:// güven kısıtı) |
| `open_folder()` | `{ok}` | v1'de yok; modele tıklama pasif |

JS tarafı:
- `seq` değişince `latest_text` yeni paragraf olarak eklenir (kullanıcı düzenlemeleri korunur).
- Kopyala, kutudaki güncel metni `copy()`'ye gönderir.
- Geri Al, en son eklenen paragrafı kaldırır.
- `state` sınıfları mevcut prototipteki `is-listening` / `is-processing` ile eşlenir.

## 5. Teknik ayrıntılar

### Motor ve model
- Cihaz algılama: `ctranslate2.get_cuda_device_count() > 0`.
- GPU denemesi: `WhisperModel("large-v3", device="cuda", compute_type="float16", download_root="models")`.
- Hata olursa logla ve `WhisperModel("small", device="cpu", compute_type="int8", ...)` ile devam et; ekranda "CPU modu (small, int8)" yaz.
- Model yükleme uygulama açılışında **arka plan thread'inde** yapılır; bu sırada durum `loading`.
- `--kurulum`: GPU varsa `large-v3` + yedek `small`, yoksa yalnız `small` indirir; indirme öncesi boyutları yazar. Ağ hatasında anlaşılır Türkçe mesaj + tekrar komut.
- `--selftest`: `tests/data/test.wav` dosyasını çevirir; cihaz, model, süre ve metni yazar. Dosya yoksa nasıl ekleneceğini söyler.
- Çeviri parametreleri: `language="tr"`, `beam_size=5`, `vad_filter=True`, `condition_on_previous_text=False`.

### Kayıt
- `sounddevice.RawInputStream(samplerate=16000, channels=1, dtype="int16", blocksize=800)`; callback parçaları listeye ekler.
- Durdurunca `wave` ile `%TEMP%\dikte\kayit-<zaman>.wav`.
- Çeviri `try/finally` içinde; wav her durumda silinir. Metin hiçbir log dosyasına yazılmaz.
- Başlangıç/bitiş tonu: `winsound.Beep` (kısa, düşük ses); hata olsa bile uygulamayı düşürmez.
- Mikrofon yoksa/izin yoksa: "Mikrofon bulunamadı. Windows Ayarlar > Gizlilik > Mikrofon iznini kontrol et."

### Kısayol
- `pynput.keyboard.Listener`; yalnız `Key.ctrl_r`.
- `pressed` bayrağı ile tuş tekrarı yok sayılır; basılıyken başka tuşa basmak kaydı durdurmaz (kabul edilen sınırlama).
- Listener daemon thread; kapanışta `stop()`.
- Antivirüs uyarısı olursa kullanıcıya bilgi verilir; `keyboard` kütüphanesine dönülmez (AGENTS kararı).

### Bellek ve etkinlik
- GPU modunda `pynvml` ile kullanılan/toplam VRAM (GB, 1 ondalık).
- CPU modunda `psutil.Process().memory_info().rss` / toplam RAM.
- Etkinlikler bellekte en fazla 7 kayıt: "Model yüklendi", "Dikte tamamlandı (süre · kelime)", "Ses algılanamadı", "Hata".
- Kelime sayısı boşlukla ayrılmış parça sayısı; süre kayıt süresi.

### Arayüz
- `design/prototype.html` temel alınır; `dikte/ui/index.html` olarak sadeleştirilir:
  - Yalnız Dikte sayfası çalışır; diğer menü öğeleri tıklanınca "Bu bölüm v1.1'de gelecek" bildirimi.
  - Sahte pencere düğmeleri kaldırılır (Windows çerçevesi kullanılır).
  - Metin kutusu boş başlar; sahte metin ve sahte etkinlikler kaldırılır.
  - `Transkripsiyonu Yenile` ve `Yapay Zeka ile Temizle` devre dışı; üzerlerinde "v1.1" ipucu.
  - Dil seçici yalnız "Türkçe", pasif.
  - Alt çubuk gerçek cihaz/dil/mode bilgisini gösterir; tıklama v1'de bilgi verir.
  - Mikrofon düğmesi ve kısayol ipucu: "Sağ Ctrl (basılı tut)".
  - Durum renkleri: loading amber, ready yeşil, recording mavi, processing amber, error kırmızı.
- Pencere: 1440×900, en küçük 1180×760, `background_color="#060A14"`, yeniden boyutlandırılabilir.
- Kapanışta controller kapatılır, listener ve ses akışı durur, geçici dosyalar silinir.

### Dosya yapısı
```
dikte/
  __init__.py
  __main__.py
  config.py
  state.py
  engine.py
  audio.py
  hotkey.py
  clipboard.py
  controller.py
  diagnostics.py
  ui/
    bridge.py
    index.html
    style.css
    app.js
tests/
  test_state.py
  test_controller.py
  test_config.py
  data/test.wav        # kullanıcı ekleyecek
models/                # git dışı
requirements.txt
requirements-dev.txt
```

## 6. Uygulama adımları

### Adım 0 — Ortam (Aşama 0)
1. Python 3.12 kurulumunu doğrula, `.venv` oluştur, `requirements*.txt` yaz.
2. `.gitignore`: `.venv/`, `models/`, `__pycache__/`, `logs/`, `*.wav` (tests/data hariç).
3. WebView2 çalışma zamanının kurulu olduğunu kontrol et; yoksa Evergreen kurulum bağlantısını kullanıcıya ver.
4. Boş paket iskeletini ve `python -m dikte --selftest` iskeletini oluştur.
- **Kanıt:** `python --version`, `pip list`, `python -m dikte --selftest` çıktısı.
- **Senin yapacağın:** Python 3.12 kurulumu (ajan yönlendirecek).

### Adım 1 — Motor ve kurulum komutu (Aşama 1)
1. `config.py`, `engine.py`, `diagnostics.py`.
2. `--kurulum`: cihaz testi + model indirme + boyut/mode raporu.
3. `--selftest`: wav → metin, cihaz/süre yazdır.
4. GPU'da `float16`, CPU'da `int8` yolunu ayrı ayrı dene.
- **Kanıt:** `--selftest` çıktısı (GPU veya CPU), Türkçe karakter testi, pytest motor mock testi.
- **Senin yapacağın:** 5–10 sn Türkçe kaydı `tests/data/test.wav`, metnini `tests/data/test.txt` olarak koy.
- **Durma noktası:** GPU float16 çalışmazsa CPU'ya düş ve durumu bildir; 3 denemeden fazla zorlama.

### Adım 2 — Kayıt, kısayol, pano, durum makinesi (Aşama 2, arayüzsüz)
1. `state.py` + `controller.py` (saf mantık, enjekte edilebilir recorder/engine/clipboard).
2. `audio.py`, `hotkey.py`, `clipboard.py`, `diagnostics.py` hata metinleri.
3. Tonlar, kısa kayıt/sessizlik filtresi, geçici dosya silme.
4. `--selftest` yanına `--dikte-testi` (konsol): kısayolu bekle, kaydı çevir, panoya yaz, "panoya kopyalandı" yaz. Metni konsola basma.
- **Kanıt:** pytest (durum geçişleri, kısa kayıt, hata yolları), Not Defteri'nde elle yapıştırma testi.
- **Senin yapacağın:** Sağ Ctrl ile cümle söyle, Not Defteri'ne Ctrl+V yap; Türkçe karakterleri kontrol et.

### Adım 3 — Arayüz kabuğu (Aşama 3)
1. `design/prototype.html` → `dikte/ui/` (HTML/CSS/JS ayrıştırılmış).
2. `bridge.py`: `snapshot`, `toggle_record`, `copy`; pencere ayarları.
3. JS: `pywebviewready` sonrası 200 ms yoklama, durum sınıfları, bildirimler.
4. Diğer sayfaları devre dışı bırak; sahte verileri temizle.
5. Playwright ile sahte köprü (`window.pywebview` stub) üzerinden DOM testi ve ekran görüntüsü.
- **Kanıt:** `design/` ile karşılaştırılmış ekran görüntüsü, DOM testi (durum metinleri, düğme durumları).
- **Senin yapacağın:** Ekran görüntüsüne bakıp tasarıma uygunluk onayı.

### Adım 4 — Dikte ekranı entegrasyonu (Aşama 4)
1. Gerçek snapshot → durum, model, cihaz, bellek, etkinlik, metin.
2. Mikrofon düğmesi ↔ kısayol aynı controller.
3. Kopyala / Geri Al; "Yenile" ve "AI Temizle" pasif.
4. Hata durumları: model yok, mikrofon yok, çeviri hatası, sessiz kayıt.
5. Etkinlik listesi gerçek olaylarla; sağ panelde "İşleme hızı" yok.
- **Kanıt:** uçtan uca elle test (kısayol + düğme + pano), Playwright durum simülasyonu, ekran görüntüsü.

### Adım 5 — Sağlamlaştırma ve kapanış
1. Tüm hata mesajlarını Türkçeleştir; loglarda metin olmadığını doğrula.
2. `pytest` tamamını çalıştır; en az 3 kez tekrarla (kilit/thread kararlılığı).
3. `STATE.md`, `architecture.md`, `PLAN.md` güncelle (uygulama ajanı yapar).
4. "@gozden-gecirici" ile PLAN.md bitti tanımına göre denetim; kod değiştirmesin.
5. Kullanıcı onayı sonrası commit.
- **Kanıt:** test çıktıları, ekran görüntüsü, 5 maddelik kullanıcı özeti, temiz `git status`.

## 7. Doğrulama

### Otomatik
| Test | Kapsam |
| :--- | :--- |
| `pytest tests/test_state.py` | Tüm durum geçişleri, geçersiz geçişler, kısa kayıt |
| `pytest tests/test_controller.py` | Sahte recorder/engine/clipboard ile uçtan uca akış, kilit, hata |
| `pytest tests/test_config.py` | Yol ve sabitler, model seçimi |
| `python -m dikte --selftest` | Gerçek motor; cihaz ve Türkçe metin |
| Playwright + stub | Durum sınıfları, metin ekleme, kopyala/geri al, pasif düğmeler |
| Ekran görüntüsü | `design/VoxNote AI Dikte Çalışma Alanı.png` ile karşılaştırma |

### Elle (kullanıcı)
1. `python -m dikte` → pencere açılır, mod yazar, durum "Dinlemeye hazır".
2. Sağ Ctrl basılı tut → "Dinleniyor", dalga hızlanır; bırak → "İşleniyor" → metin.
3. Metni Not Defteri'ne yapıştır → Türkçe karakterler (ı, ğ, ş, ç, ö, ü) doğru.
4. Arayüz mikrofon düğmesiyle aynı akışı dene.
5. 5 saniye sessiz kayıt → sahte cümle eklenmemeli.
6. Kopyala ve Geri Al.
7. `%TEMP%\dikte` klasöründe kayıt kalmadığını doğrula.
8. Uygulamayı kapat, tekrar aç → çökme yok.

### v1 kabul ölçütleri
- [ ] `python -m dikte` hatasız açılıyor ve çalışılan mod (GPU/CPU) ekranda.
- [ ] Sağ Ctrl ile Türkçe dikte panoya kopyalanıyor.
- [ ] Arayüzdeki metin, durum ve etkinlikler gerçek; sahte veri yok.
- [ ] Geçici ses dosyası ve transkript logu kalmıyor.
- [ ] pytest yeşil, Playwright testi geçiyor, ekran görüntüsü onaylı.
- [ ] Pasif özellikler (Yenile, AI Temizle, diğer sayfalar) açıkça "v1.1" diyor.

## 8. Riskler ve önlemler
| Risk | Etki | Önlem |
| :--- | :--- | :--- |
| RTX 5060 + CTranslate2 uyumsuzluğu | GPU çalışmaz | Yalnız `float16` dene, olmazsa `small/int8` CPU; Adım 1'de karar ver, arayüze geçmeden çöz |
| CUDA/cuDNN DLL eksikliği | GPU başlatılamaz | Gerekli `nvidia-*-cu12` paketlerini kur; kurulum çıktısında eksik DLL'i Türkçe söyle; yedek CPU |
| WebView2 yok | Pencere açılmaz | Kurulumda kontrol; Evergreen Runtime bağlantısı; alternatif PySide6'ya sessizce geçme, kullanıcıya sor |
| pywebview + thread | Donma/çökme | v1'de Python→JS push yok; JS 200 ms yoklama kullanır; köprüde kilit |
| pynput antivirüs uyarısı | Kısayol çalışmaz | Kullanıcıya bilgi; istisna ekleme; `keyboard`'a dönme |
| Model indirme boyutu (~3,8 GB) | Uzun bekleme | `--kurulum` öncesi boyut ve süre tahmini yaz; indirme tek seferlik, `models/` git dışı |
| Uzun model yükleme | İlk kullanım gecikir | Arka planda yükle, `loading` durumu göster |
| Kullanıcı metni elle düzenler | Geri Al uyumsuzluğu | Geri Al yalnız uygulamanın eklediği son paragrafı kaldırır; JS metin sahibi |
| Sessiz kayıtta halüsinasyon | Yanlış metin | `vad_filter`, kısa kayıt eşiği, boş sonucu yoksay |
| Bellek ölçümü GPU yokken | Yanlış "VRAM" | CPU modunda RAM göster, birim ve etiket değişsin |

## 9. Açık varsayımlar (uygulamaya başlarken teyit)
1. **Model indirme** `--kurulum` komutuyla yapılacak (yarıda kalan sorunun önerilen cevabı). Uygulama içi indirme v1.1'e kalır.
2. Windows'un **normal pencere çerçevesi** kullanılacak; tasarımdaki sahte küçült/büyüt/kapat düğmeleri kaldırılacak.
3. v1 yalnız **Dikte sayfası**; diğer menü öğeleri bilgilendirme gösterir.
4. **Tepsi yok**; pencere kapatılınca uygulama çıkar.
5. Her kayıt **yeni paragraf** ekler; kopyalama tüm metni alır.
6. Dil yalnızca **Türkçe**; seçici pasif.

## 10. Çalışma kuralları (uygulama ajanı için)
- Aşama 0–2'de alt ajan kullanma; aynı anda en fazla 2.
- Kod yazmadan önce kısa plan; her adımda çalıştır, çıktıyı oku, en fazla 3 deneme.
- API anahtarı yok; ücretli servis yok; transkript loga yazılmaz.
- Mikrofon/kısayol/pano gibi doğrulanamayanlar "SENİN YAPACAĞIN TEST" başlığıyla verilir.
- Commit yalnız kullanıcı onayıyla; öncesinde @gozden-gecirici denetimi.
- Her adım sonunda STATE.md ve architecture.md güncellenir.
