# architecture.md — Proje Haritası

Bu dosya projenin güncel yapısını gösterir. Her görev sonunda güncellenir.

## Genel bakış
Dikte, kısayol tuşuyla çalışan bir Türkçe dikte uygulamasıdır. v1 (çekirdek + Dikte ekranı) 2026-10-24'te, v1.2 (Geçmiş + Modeller + Ayarlar + Yenile) 2026-10-27'de tamamlandı.

Akış:
1. Kullanıcı seçili kısayolu (varsayılan Sağ Ctrl) basılı tutar veya mikrofon düğmesine basar.
2. `AudioRecorder` 16 kHz mono kaydı belleğe alır.
3. Tuş bırakılınca kayıt geçici `.wav` dosyasına yazılır.
4. `TranscriptionEngine` (faster-whisper) kaydı Türkçe yazıya çevirir.
5. Metin panoya kopyalanır; "Geçmişi kaydet" açıksa `HistoryStore`'a eklenir.
6. Kaynak wav silinir; son kayıt `%TEMP%\dikte\last.wav` olarak "Yenile" için tutulur.
7. Arayüz 250 ms'de bir `snapshot()` çağırarak durumu, metni ve etkinlikleri gösterir; Geçmiş/Modeller/Ayarlar sayfaları kendi API'lerini yoklar.

## Dosya haritası
| Dosya | Görevi | Durum |
| :--- | :--- | :--- |
| `dikte/__main__.py` | CLI: normal açılış, `--kurulum`, `--selftest`, `--dikte-testi`, `--cpu`, `--debug` | Hazır |
| `dikte/config.py` | Sabitler, yollar, model adları, pencere ölçüleri | Hazır |
| `dikte/state.py` | Durum makinesi: loading/ready/recording/processing/error | Hazır |
| `dikte/settings.py` | `data/settings.json`: aktif model, kısayol, geçmiş tercihi; hazır kısayol listesi | Hazır |
| `dikte/history.py` | `data/history.json`: ekle/listele/ara/sil/temizle, 500 sınırı, bozuk dosya yedeği | Hazır |
| `dikte/models.py` | 6 ses modeli kataloğu, disk taraması, indirme, silme, boyut biçimleme | Hazır |
| `dikte/engine.py` | Cihaz seçimi, seçili modeli yükleme/boşaltma, çeviri, GPU→CPU düşüşü | Hazır |
| `dikte/audio.py` | sounddevice kaydı, geçici wav, temizlik | Hazır |
| `dikte/hotkey.py` | pynput ile seçilebilir kısayol dinleyicisi (7 hazır tuş) | Hazır |
| `dikte/clipboard.py` | pyperclip ile panoya kopyalama | Hazır |
| `dikte/controller.py` | Durum geçişleri, worker thread, geçmiş, model yönetimi, ayarlar, yenile, snapshot | Hazır |
| `dikte/diagnostics.py` | UTF-8 konsol, CUDA DLL yolu, VRAM/RAM, Türkçe hata metinleri, log | Hazır |
| `dikte/ui/bridge.py` | pywebview penceresi ve JS API (snapshot, kayıt, geçmiş, modeller, ayarlar, yenile) | Hazır |
| `dikte/ui/index.html` | Dört sayfa: Dikte, Geçmiş, Modeller, Ayarlar | Hazır |
| `dikte/ui/style.css` | Tasarım token'ları, sayfa yönlendirici ve bileşen stilleri | Hazır |
| `dikte/ui/app.js` | Sayfa yönlendirici, durum yansıtma, geçmiş/modeller/ayarlar, yenile | Hazır |
| `tests/test_state.py` | Durum geçişleri | 83 test geçti |
| `tests/test_controller.py` | Sahte bileşenlerle dikte, geçmiş, model, ayar, yenile akışı | 83 test geçti |
| `tests/test_engine_plan.py` | GPU/CPU ve seçili model sırası | 83 test geçti |
| `tests/test_settings.py` | Ayar okuma/yazma, bozuk dosya, atomik yazma | 83 test geçti |
| `tests/test_history.py` | Kayıt, Türkçe arama, filtre, silme, sınır, bozuk JSON | 83 test geçti |
| `tests/test_models.py` | Katalog, boyut, kısmi indirme, silme, indirme hatası | 83 test geçti |
| `tests/test_ui.py` | Playwright + sahte köprü ile dört sayfa | 83 test geçti |
| `.kilo/skills/` | `asama-baslat`, `asama-bitir`, `proje-baslat` skill'leri | Hazır |
| `AGENTS.md`, `STATE.md`, `PLAN.md`, `architecture.md`, `STIL.md`, `ogrenme-gunlugu.md` | Proje hafızası, yol haritası ve ajan tarzı | Hazır |
| `design/` | Tasarım kaynağı (görseller, ui-spec, prototype) | Hazır |
| `Dikte.bat` | Çift tıklayarak uygulamayı açan Windows başlatıcı | Hazır |
| `models/` | İndirilen Whisper modelleri (git dışı) | large-v3 + small + tiny indirildi |

## Bileşenler ve bağlantıları
| Bileşen | Neye bağlı | Değişirse neler etkilenir |
| :--- | :--- | :--- |
| `AudioRecorder` | sounddevice, `config` | `Controller` kayıt akışı, geçici dosya temizliği |
| `TranscriptionEngine` | faster-whisper, ctranslate2, CUDA DLL'leri, `models/` | `Controller._transcribe_path`, selftest, GPU/CPU bilgisi |
| `HotkeyListener` | pynput, `settings.HOTKEY_CHOICES` | Kısayolla kayıt başlatma/durdurma, ayar değişimi |
| `SettingsStore` | `data/settings.json`, `config` | Aktif model, kısayol, geçmiş tercihi |
| `HistoryStore` | `data/history.json`, `config` | Geçmiş listesi, arama, silme |
| `ModelManager` | `dikte.models`, `models/` | Model taraması, indirme, silme |
| `Controller` | recorder, engine, hotkey, clipboard, diagnostics, stores | Arayüz snapshot'ı, durum, geçmiş, model, ayar, yenile |
| `Api` (bridge) | `Controller`, pywebview | Arayüzün tüm veri ve eylemleri |
| `app.js` | `Api`, `index.html`, `style.css` | Dört sayfa, durum, metin, geçmiş, modeller, ayarlar |
| `diagnostics` | pynvml, psutil, ctypes, logging | Bellek satırı, Türkçe hatalar, CUDA DLL yüklemesi |

## İş parçacıkları (thread) modeli
- **Ana thread:** pywebview arayüzü.
- **Kısayol thread'i:** pynput dinleyicisi; `Controller`'ı kilit altında çağırır.
- **Motor yükleme thread'i:** açılışta veya model değişiminde modeli yükler, durumu `loading → ready/error` yapar.
- **Çeviri thread'i:** kayıt bitince veya Yenile'de çalışır; sonuç/etkinlik güncellemesi kilit altındadır.
- **Model indirme thread'i:** klasör boyutunu 500 ms'de bir okuyup ilerleme yüzdesi üretir; tek seferde tek indirme.
- **Arayüz:** Python'dan JS'e push yok; `app.js` 250 ms'de bir `snapshot()`, Modeller açıkken 700 ms'de bir `models_list()` yoklar. Bu, pywebview thread sorunlarını önler.

## Durumlar
| Durum | Anlamı |
| :--- | :--- |
| `loading` | Model belleğe yükleniyor |
| `ready` | Dikteye hazır |
| `recording` | Mikrofon açık |
| `processing` | Çeviri sürüyor |
| `error` | Model/mikrofon/çeviri hatası; ayrıntı `snapshot.error` |

## Hata ve gizlilik
- Hata mesajları Türkçe ve kullanıcıya gösterilir; ayrıntı `logs/dikte.log` dosyasına yazılır.
- **Konuşulan metin loga yazılmaz.** Log'da yalnız durum, model, cihaz, süre ve hata bilgisi vardır.
- Kaynak `.wav` çeviriden sonra `finally` bloğunda silinir. Son kayıt `%TEMP%\dikte\last.wav` olarak yalnız uygulama açıkken tutulur; yeni diktede üzerine yazılır, açılışta ve kapanışta silinir.
- Konuşma metni yalnız `data/history.json` içinde ve "Geçmişi kaydet" açıksa durur. Anahtar kapatılınca API kayıt döndürmez; arşiv dosyası silinmez.
- `data/`, `logs/`, `models/`, `.venv/`, `artifacts/` git dışındadır.

## Bilinen sorunlar
- İlk çeviri yavaş (CUDA ısınması + model yükleme ~7 sn). Sonraki dikteler daha hızlı.
- GPU çevirisi çökerse controller aynı modeli CPU/int8 ile, o da olmazsa `small/int8` ile dener; arayüzde etkinlik olarak görünür.
- Model indirme iptal/duraklat desteklemez; yarım indirme "Yarım indirme" olarak gösterilir.
- Aktif model silinemez; Windows dosya kilidi silmeyi engellerse Türkçe hata gösterilir.
- Geçmişten bir kayıt açıldıktan sonra Yenile pasif olur (son dikte olmadığı için).
- Geçmiş kapalıyken yapılan dikteden sonra anahtar açılıp Yenile yapılırsa sonuç kayıtlara yazılmaz (ses korunur, pano güncellenir).
- "Yapay Zeka ile Temizle" ve metin modelleri v1.3'te; dil/mikrofon seçimi yok.

## Karar geçmişi
- 2026-10-22: Proje başlatıldı. Python, faster-whisper, deepseek-v4-flash.
- 2026-10-24: v1 kapsamı "çekirdek + Dikte ekranı" olarak onaylandı.
- 2026-10-24: Arayüz pywebview + mevcut HTML/CSS/JS olarak onaylandı.
- 2026-10-24: CUDA eksikliği pip `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` ve otomatik DLL yolu ile çözüldü.
- 2026-10-24: Model indirme `--kurulum`, Türkçe-only, normal pencere çerçevesi varsayıldı (kullanıcı teyidi bekliyor).
- 2026-10-25: Oturum sonu protokolü `asama-bitir` skill'ine taşındı; AGENTS.md sadeleştirildi, STIL.md eklendi, eski yardımcı dosyalar silindi.
- 2026-10-27: Python 3.12.10'a geçildi; PyAV `>=11,<16` sabitlendi.
- 2026-10-27: v1.2 kapsamı onaylandı: Geçmiş, Modeller (ses), Ayarlar (kısayol + geçmiş anahtarı), Yenile. Dil/mikrofon ve metin modelleri sonraki sürümlere bırakıldı.
- 2026-10-27: Geçmiş kapalıyken eski kayıtlar gizlenir; son ses Yenile için geçici dosyada tutulur.
