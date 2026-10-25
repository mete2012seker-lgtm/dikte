# architecture.md — Proje Haritası

Bu dosya projenin güncel yapısını gösterir. Her görev sonunda güncellenir.

## Genel bakış
Dikte, kısayol tuşuyla çalışan bir Türkçe dikte uygulamasıdır. v1 kapsamı: çalışan çekirdek + Dikte ekranı. **v1 kullanıcı tarafından çalışır olarak onaylandı (2026-10-24).**

Akış:
1. Kullanıcı Sağ Ctrl tuşunu basılı tutar (veya arayüzdeki mikrofon düğmesine basar).
2. `AudioRecorder` 16 kHz mono kaydı belleğe alır.
3. Tuş bırakılınca kayıt geçici `.wav` dosyasına yazılır.
4. `TranscriptionEngine` (faster-whisper) kaydı Türkçe yazıya çevirir.
5. Metin panoya kopyalanır ve geçici `.wav` silinir.
6. Arayüz 250 ms'de bir `snapshot()` çağırarak durumu, metni ve etkinlikleri gösterir.

## Dosya haritası
| Dosya | Görevi | Durum |
| :--- | :--- | :--- |
| `dikte/__main__.py` | CLI: normal açılış, `--kurulum`, `--selftest`, `--dikte-testi`, `--cpu`, `--debug` | Hazır |
| `dikte/config.py` | Sabitler, yollar, model adları, pencere ölçüleri | Hazır |
| `dikte/state.py` | Durum makinesi: loading/ready/recording/processing/error | Hazır |
| `dikte/engine.py` | Cihaz seçimi, model yükleme/indirme, çeviri, GPU→CPU düşüşü | Hazır |
| `dikte/audio.py` | sounddevice kaydı, geçici wav, temizlik | Hazır |
| `dikte/hotkey.py` | pynput ile global Sağ Ctrl dinleyicisi | Hazır |
| `dikte/clipboard.py` | pyperclip ile panoya kopyalama | Hazır |
| `dikte/controller.py` | Durum geçişleri, worker thread, etkinlikler, snapshot | Hazır |
| `dikte/diagnostics.py` | UTF-8 konsol, CUDA DLL yolu, VRAM/RAM, Türkçe hata metinleri, log | Hazır |
| `dikte/ui/bridge.py` | pywebview penceresi ve JS API (`snapshot`, `toggle_record`, `copy`) | Hazır |
| `dikte/ui/index.html` | Dikte ekranı iskeleti | Hazır |
| `dikte/ui/style.css` | Tasarım token'ları ve bileşen stilleri | Hazır |
| `dikte/ui/app.js` | Durum yansıtma, metin ekleme, kopyala/geri al, bildirimler | Hazır |
| `tests/test_state.py` | Durum geçişleri | 34 test geçti |
| `tests/test_controller.py` | Sahte bileşenlerle akış, hata ve GPU düşüşü | 34 test geçti |
| `tests/test_engine_plan.py` | GPU/CPU seçim sırası | 34 test geçti |
| `tests/test_ui.py` | Playwright + sahte köprü ile arayüz | 34 test geçti |
| `.kilo/skills/` | `asama-baslat`, `asama-bitir`, `proje-baslat` skill'leri | Hazır |
| `AGENTS.md`, `STATE.md`, `PLAN.md`, `architecture.md`, `STIL.md`, `ogrenme-gunlugu.md` | Proje hafızası, yol haritası ve ajan tarzı | Hazır |
| `design/` | Tasarım kaynağı (görseller, ui-spec, prototype) | Hazır |
| `Dikte.bat` | Çift tıklayarak uygulamayı açan Windows başlatıcı | Hazır |
| `models/` | İndirilen Whisper modelleri (git dışı) | large-v3 + small indirildi |

## Bileşenler ve bağlantıları
| Bileşen | Neye bağlı | Değişirse neler etkilenir |
| :--- | :--- | :--- |
| `AudioRecorder` | sounddevice, `config` | `Controller` kayıt akışı, geçici dosya temizliği |
| `TranscriptionEngine` | faster-whisper, ctranslate2, CUDA DLL'leri, `models/` | `Controller._transcribe`, selftest, GPU/CPU bilgisi |
| `HotkeyListener` | pynput, `Controller.on_hotkey_press/release` | Kısayolla kayıt başlatma/durdurma |
| `Controller` | recorder, engine, hotkey, clipboard, diagnostics | Arayüz snapshot'ı, durum metinleri, etkinlikler |
| `Api` (bridge) | `Controller`, pywebview | Arayüzün tüm veri ve eylemleri |
| `app.js` | `Api`, `index.html`, `style.css` | Ekrandaki durum, metin ve düğmeler |
| `diagnostics` | pynvml, psutil, ctypes, logging | Bellek satırı, Türkçe hatalar, CUDA DLL yüklemesi |

## İş parçacıkları (thread) modeli
- **Ana thread:** pywebview arayüzü.
- **Kısayol thread'i:** pynput dinleyicisi; `Controller`'ı kilit altında çağırır.
- **Motor yükleme thread'i:** açılışta modeli yükler, durumu `loading → ready/error` yapar.
- **Çeviri thread'i:** kayıt bitince çalışır; sonuç/etkinlik güncellemesi kilit altındadır.
- **Arayüz:** Python'dan JS'e push yok; `app.js` 250 ms'de bir `snapshot()` yoklar. Bu, pywebview thread sorunlarını önler.

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
- Geçici `.wav` çeviriden sonra `finally` bloğunda silinir (`%TEMP%\dikte`).
- `logs/`, `models/`, `.venv/`, `artifacts/` git dışındadır.

## Bilinen sorunlar
- Python 3.12 henüz kurulu değil; `.venv` 3.10.11 ile çalışıyor.
- İlk çeviri yavaş (CUDA ısınması + model yükleme). v1'de kabul edildi, v1.1'de ölçülecek.
- GPU çevirisi çökerse controller bir kez CPU'ya (`small/int8`) düşer; bu durum arayüzde etkinlik olarak görünür.
- Dikte Geçmişi, Modeller ve Ayarlar sayfaları v1'de yok; menüde "v1.1" bilgisi verir.
- "Transkripsiyonu Yenile" ve "Yapay Zeka ile Temizle" v1'de pasif.

## Karar geçmişi
- 2026-10-22: Proje başlatıldı. Python, faster-whisper, deepseek-v4-flash.
- 2026-10-24: v1 kapsamı "çekirdek + Dikte ekranı" olarak onaylandı.
- 2026-10-24: Arayüz pywebview + mevcut HTML/CSS/JS olarak onaylandı.
- 2026-10-24: CUDA eksikliği pip `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` ve otomatik DLL yolu ile çözüldü.
- 2026-10-24: Model indirme `--kurulum`, Türkçe-only, normal pencere çerçevesi varsayıldı (kullanıcı teyidi bekliyor).
- 2026-10-25: Oturum sonu protokolü `asama-bitir` skill'ine taşındı; AGENTS.md sadeleştirildi, STIL.md eklendi, eski yardımcı dosyalar silindi.
