# architecture.md — Proje Haritası

Bu dosya projenin güncel yapısını gösterir. Her görev sonunda güncellenir.

## Genel bakış
Dikte, kısayol tuşuyla çalışan bir Türkçe dikte uygulamasıdır. v1 (çekirdek + Dikte ekranı) 2026-10-24'te, v1.2 (Geçmiş + Modeller + Ayarlar + Yenile) 2026-10-27'de tamamlandı. v1.3'ün ilk partisi (7a: metin motoru, OpenRouter, Temizle/Çevir, Ayarlar kartları) 2026-11-01'de tamamlandı; GGUF/llama.cpp, bellek takası ve otomatik yapıştırma sırada.

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
| `dikte/state.py` | Durum makinesi: loading/ready/recording/processing/cleaning/error | Hazır |
| `dikte/settings.py` | `data/settings.json`: model, kısayol, geçmiş, çıktı/girdi dili, otomatik çevir/yapıştırma, sağlayıcı, tema | Hazır |
| `dikte/secrets.py` | OpenRouter anahtarını DPAPI ile şifreli `data/secrets.json`'da saklar | Hazır |
| `dikte/openrouter.py` | Tüm model kataloğunu 24 saat önbellekler; varsayılan ucuz filtre, "tüm modeller" seçeneği ve arama | Hazır |
| `dikte/text_engine.py` | Prompt kurma, tek çağrıda temizle/çevir, yanıt temizleme, çıktı dili ve halüsinasyon denetimi, Türkçe hata kodları | Hazır (OpenRouter; GGUF 7b) |
| `dikte/history.py` | `data/history.json`: ekle/listele/ara/sil/temizle, 500 sınırı, bozuk dosya yedeği | Hazır |
| `dikte/models.py` | 6 ses modeli kataloğu, disk taraması, indirme, silme, boyut biçimleme | Hazır |
| `dikte/paste.py` | Etkin pencereye Ctrl+V; Dikte penceresini atlar, hata sessiz | Hazır |
| `dikte/text_models.py` | 4 GGUF modeli kataloğu, `.part` + HTTP Range indirme (duraklat/devam/iptal), boyut doğrulama, llama.cpp sarmalayıcısı | Hazır (llama.cpp paketi isteğe bağlı) |
| `dikte/engine.py` | Cihaz seçimi, seçili modeli yükleme/boşaltma, çeviri, GPU→CPU düşüşü | Hazır |
| `dikte/audio.py` | sounddevice kaydı, geçici wav, temizlik | Hazır |
| `dikte/hotkey.py` | pynput ile seçilebilir kısayol dinleyicisi (7 hazır tuş) | Hazır |
| `dikte/clipboard.py` | pyperclip ile panoya kopyalama | Hazır |
| `dikte/controller.py` | Durum geçişleri, worker thread, geçmiş, model yönetimi, ayarlar, yenile, snapshot | Hazır |
| `dikte/diagnostics.py` | UTF-8 konsol, CUDA DLL yolu, VRAM/RAM, Türkçe hata metinleri, log | Hazır |
| `dikte/ui/bridge.py` | pywebview penceresi ve JS API (snapshot, kayıt, geçmiş, ses/metin modelleri, ayarlar, yenile, temizle/çevir, anahtar) | Hazır |
| `dikte/ui/index.html` | Dört sayfa + tema düğmesi; Ayarlar: Yapay Zeka, Yapıştırma/Dil, Görünüm | Hazır |
| `dikte/ui/style.css` | Tasarım token'ları (koyu + açık tema), sayfa yönlendirici, Magic UI geçiş sınıfları | Hazır |
| `dikte/ui/style.css` | Tasarım token'ları, sayfa yönlendirici ve bileşen stilleri | Hazır |
| `dikte/ui/app.js` | Sayfa yönlendirici, durum yansıtma, geçmiş/modeller/ayarlar, yenile, temizle/çevir, tema geçişi, model sekmeleri | Hazır |
| `tests/test_state.py` | Durum geçişleri (cleaning dahil) | 201 test geçti |
| `tests/test_controller.py` | Sahte bileşenlerle dikte, geçmiş, model, ayar, yenile akışı | 201 test geçti |
| `tests/test_controller_ai.py` | Temizle/Çevir, sağlayıcı kapalı, otomatik çevir, anahtar durumu | 201 test geçti |
| `tests/test_engine_plan.py` | GPU/CPU ve seçili model sırası | 201 test geçti |
| `tests/test_settings.py` | Ayar okuma/yazma, bozuk dosya, atomik yazma, v1.3 alanları | 201 test geçti |
| `tests/test_secrets.py` | DPAPI gidiş-dönüş, bozuk blob, maskeleme | 201 test geçti |
| `tests/test_openrouter.py` | Ucuz filtre, önbellek, çevrimdışı düşüş | 201 test geçti |
| `tests/test_text_engine.py` | Prompt sırası, yanıt temizleme, 401/402/429/ağ, dil denetimi | 201 test geçti |
| `tests/test_text_models.py` | Katalog, Range ile devam, duraklat/iptal, 404, silme | 201 test geçti |
| `tests/test_history.py` | Kayıt, Türkçe arama, filtre, silme, sınır, bozuk JSON | 201 test geçti |
| `tests/test_models.py` | Katalog, boyut, kısmi indirme, silme, indirme hatası | 201 test geçti |
| `tests/test_ui.py` | Playwright + sahte köprü: dört sayfa, çıktı dili, Yapay Zeka kartı, tema, model sekmeleri | 201 test geçti |
| `tests/test_paste.py` | Kendi pencereyi atlama, kapalı ayar, hata | 201 test geçti |
| `.kilo/skills/` | `asama-baslat`, `asama-bitir`, `proje-baslat` skill'leri | Hazır |
| `AGENTS.md`, `STATE.md`, `PLAN.md`, `architecture.md`, `STIL.md`, `ogrenme-gunlugu.md` | Proje hafızası, yol haritası ve ajan tarzı | Hazır |
| `olabilir.md` | v1.3-v1.5 ayrıntılı istek ve davranış spesifikasyonu | Hazır (uygulanmadı) |
| `design/` | Tasarım kaynağı (görseller, ui-spec, prototype) | Hazır |
| `web/` | Next.js 16 + shadcn + Magic UI denemesi (AnimatedList, BentoGrid); Dikte arayüzüne bağlı değil | Deneme |
| `Dikte.bat` | Çift tıklayarak uygulamayı açan Windows başlatıcı | Hazır |
| `models/` | İndirilen Whisper modelleri (git dışı) | large-v3 + small + tiny indirildi |

## Arayüz yönü (deneme)
`web/`, Dikte'nin pywebview arayüzünden bağımsız bir Next.js denemesidir (`cd web; npm run dev`). Mevcut uygulama hâlâ `dikte/ui/` altındaki HTML/CSS/JS'i kullanır. 2026-11-01'de Magic UI'ın CSS/JS uyarlaması seçildi; Next.js'e geçilmeyecek. Yeni görünüm v1.4'te `design/v2/` ile belgelenecek.

## Planlanan modüller (henüz yok)
| Dosya | Planlanan görev |
| :--- | :--- |
| `design/v2/` + Magic UI efektleri | MagicCard, ShineBorder, AnimatedList, Bento, DotPattern (v1.4) |
| `Dikte.spec`, `installer/Dikte.iss` | PyInstaller + Inno Setup kurucu, kaldırma (v1.5) |
| `dikte/updater.py` | Sürüm denetimi (`latest.json`), kurucu indirme, SHA-256 doğrulama, sessiz kurulum ve yeniden açılış (v1.6) |

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
- Ses modeli indirmesinde iptal/duraklat yok; yarım indirme "Yarım indirme" olarak gösterilir. Metin (GGUF) indirmesinde duraklat/devam/iptal vardır.
- Aktif model silinemez; Windows dosya kilidi silmeyi engellerse Türkçe hata gösterilir.
- Geçmişten bir kayıt açıldıktan sonra Yenile pasif olur (son dikte olmadığı için).
- Geçmiş kapalıyken yapılan dikteden sonra anahtar açılıp Yenile yapılırsa sonuç kayıtlara yazılmaz (ses korunur, pano güncellenir).
- Yerel metin modeli (GGUF) çalıştırmak için `llama-cpp-python` paketi gerekir; paket yokken arayüz "motor kurulu değil" bilgisini gösterir ve OpenRouter önerilir.
- `input_language` ayarı kaydediliyor ama Whisper'a henüz bağlanmadı; motor hâlâ otomatik dil algılar.
- Magic UI efektleri (MagicCard, ShineBorder, AnimatedList, Bento, DotPattern) henüz yok; tema düğmesi ve açık tema var.
- v1.5'te PyInstaller + Inno Setup kurucusu ve çift onaylı kaldırma eklenecek.
- v1.6'da otomatik güncelleme eklenecek: `latest.json` (sürüm, kurucu bağlantısı, SHA-256) → indirme → doğrulama → sessiz kurulum → yeniden açılış.

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
- 2026-11-01: v1.3 kapsamı onaylandı: çıktı dili TR/EN/DE, Temizle/Çevir butonları, otomatik çevir kutusu, metin modeliyle dil kararı, uygulama içi GGUF + OpenRouter, indirme duraklat/iptal, arka planda kısayol ve otomatik yapıştırma.
- 2026-11-01: v1.4 (Magic UI CSS uyarlaması + karanlık mod) ve v1.5 (kurucu + çift onaylı kaldırma) kapsamları onaylandı.
- 2026-11-01: Arayüz için Next.js'e geçiş seçilmedi; mevcut HTML/CSS/JS içinde CSS uyarlaması yapılacak.
- 2026-11-01: v1.6 (otomatik güncelleme) kapsamı onaylandı; OpenRouter API anahtarı Ayarlar sayfasında ayrı alanda tutulacak.
- 2026-11-01: Metin sağlayıcısı varsayılanı `none`; otomatik yapıştırma varsayılan açık; kurucu tek CPU paketi.
- 2026-11-01: OpenRouter'da "Tüm modelleri göster" + arama; öneri sırası gemma → qwen → llama → mistral, ücretli modeller ücretsizlerin önünde.
- 2026-11-01: 4 GGUF metin modeli kataloğu, Range ile duraklat/devam/iptal indirme, Modeller sayfasında Metin/Ses sekmeleri.
- 2026-11-01: Tema düğmesi "Aktif model" kartının üstünde; View Transitions + circle clip-path; Ayarlar → Görünüm.
- 2026-11-01: Alt ajanlar ana ajanla aynı modeli kullanır (`.kilo/agents` dosyalarında `DeepSeek V4.1 Flash 1017`); oturum içi model önbelleği için yeni oturum gerekir.
