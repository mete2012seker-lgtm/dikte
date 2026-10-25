# STATE.md — Güncel Durum

Bu dosya yeni sohbette kaldığımız yerden devam etmek içindir. Her oturum sonunda güncellenir.

## Şu anki aşama
v1 (Aşama 0–4: çekirdek + Dikte ekranı) tamamlandı ve kullanıcı tarafından onaylandı (uygulama çalışıyor). Sıradaki: v1.1 (Dikte Geçmişi, Ayarlar, Modeller).

## Biten (kanıtla)
- `design/ui-spec.md` ve `design/prototype.html` hazır; kullanıcı prototipi test etti.
- Python paketi yazıldı: `dikte/` (config, state, engine, audio, hotkey, clipboard, controller, diagnostics, ui).
- **34 pytest testi geçti** (`34 passed`), GPU'ya düşüş testi dahil.
- **Gerçek uygulama açıldı:** pywebview penceresi yüklendi, model yüklendi, durum `ready`, `Whisper Large / GPU`.
- **Gerçek GPU çevirisi:** `large-v3 / cuda / float16`, 6,4 sn yükleme; 9,82 sn test sesi çevrildi (TTS sesi, İngilizce aksan; metin bu yüzden kusurlu).
- **Uçtan uca:** Seq 1, metin panoya yazıldı (`Panoda aynı mı: True`), etkinlikler `Dikte tamamlandı` + `Model yüklendi`.
- **CUDA kütüphaneleri:** `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` venv'e kuruldu; DLL yolları otomatik ekleniyor (`cublas64_12.dll` ve `cudnn64_9.dll` yükleme testi OK).
- **Mikrofon:** 1,15 sn / 18.400 kare kayıt alındı (gerçek aygıt).
- **Pano:** `Dikte pano testi: ı, ğ, ş, ç, ö, ü` doğru kopyalandı.
- **Kısayol:** enjekte edilen Sağ Ctrl olayları `press` + `release` olarak yakalandı.
- **Arayüz:** Playwright DOM testi + `artifacts/ui-dikte.png` ekran görüntüsü.
- **Modeller:** `models/` içine `large-v3` ve CPU yedeği `small` indirildi (git dışı).
- **Kullanıcı onayı (2026-10-24):** Uygulama açıldı ve çalıştığı onaylandı.
- **Doküman/protokol temizliği (2026-10-25):** Oturum sonu akışı `asama-bitir` skill'ine taşındı; AGENTS.md sadeleştirildi (kararlar ve varsayımlar ayrıldı), STIL.md oluşturuldu, eski yardımcı dosyalar silindi. Testler: 34/34.

## Yarım kalan
- Python 3.12 kurulumu. Şu an `.venv` **Python 3.10.11** ile çalışıyor; 3.12 kurulunca yeniden oluşturulacak.
- v1.1 özellikleri: Dikte Geçmişi, Ayarlar, Modeller sayfası, "Yapay Zeka ile Temizle".

## Sıradaki ilk adım
Yeni sohbette v1.1 planlaması: önce **Dikte Geçmişi + Ayarlar** (PLAN Aşama 5), sonra Modeller sayfası. AGENTS.md, STATE.md, PLAN.md ve architecture.md okunup plan çıkarılmalı; kullanıcı onayı olmadan kod yazılmamalı.

## Açık sorunlar ve denenen çözümler
- **cublas/cuDNN eksikliği:** Model GPU'ya yükleniyor ama çeviri `cublas64_12.dll` hatası veriyordu. Pip ile CUDA 12 kütüphaneleri kuruldu; `prepare_cuda_dlls()` PATH ve `add_dll_directory` ekliyor; GPU çevirisi çalışıyor.
- **GPU çalışmazsa:** Motor yüklemede CPU'ya düşüyor; ayrıca çeviri sırasında GPU hatası olursa controller bir kez `small/int8` CPU'ya geçip tekrar deniyor.
- **Konsol Türkçe karakterleri:** Windows kod sayfası 65001'e alındı; CLI çıktısı düzeldi.
- **Performans:** İlk çeviri yavaş (model yükleme ~6–8 sn). Uygulamada model bir kez yükleniyor; ilk dikte CUDA ısınması nedeniyle yavaş olabilir. v1.1'de ölçülüp iyileştirilecek.
- **Python 3.12:** Kurulu değil; kod 3.10+ ile uyumlu yazıldı ve 3.10.11'de test edildi.

## Bu aşamada alınan kararlar (kullanıcı onaylı)
- v1 kapsamı: çekirdek + Dikte ekranı (Aşama 0–4).
- Arayüz: pywebview + mevcut HTML/CSS/JS.
- Sağ panelde "İşleme hızı" yok; Modeller sayfası v1 kapsamı dışı.
- Windows'un normal pencere çerçevesi kullanılıyor.

## Uygulanan varsayımlar (teyit bekliyor)
- Model indirme `python -m dikte --kurulum` komutuyla yapılıyor.
- Her dikte yeni paragraf ekliyor; Kopyala tüm metni, Geri Al son paragrafı alıyor.
- Pencere kapatılınca uygulama çıkıyor; tepsi yok.
- Dil yalnızca Türkçe; dil seçici pasif.

## Test durumu
| Test | Sonuç |
| :--- | :--- |
| `pytest -q` | 34 passed |
| `--selftest` (TTS wav) | GPU float16, metin üretildi |
| Uçtan uca controller + pano | Başarılı, pano eşleşti |
| pywebview gerçek uygulama | Pencere + model + ready |
| Playwright arayüz | Durumlar, metin, kopyala/geri al, pasif düğmeler |
| Mikrofon kaydı | 1,15 sn, 18.400 kare |
| Kısayol | Sağ Ctrl press/release yakalandı |
| Kullanıcı testi | **Onaylandı:** uygulama çalışıyor (2026-10-24) |

## Çalıştırma komutları
```powershell
.venv\Scripts\python.exe -m dikte                 # uygulamayı aç
.venv\Scripts\python.exe -m dikte --selftest      # tests/data/test.wav ile motor testi
.venv\Scripts\python.exe -m dikte --kurulum       # GPU testi + model indirme (tekrar çalıştırmak zarar vermez)
.venv\Scripts\python.exe -m dikte --dikte-testi   # arayüzsüz kısayol/kayıt/pano testi
.venv\Scripts\python.exe -m pytest -q             # testler
```

## Maliyet günlüğü (OpenRouter Activity'den ben dolduracağım)
| Tarih | Aşama | Toplam harcama |
| :--- | :--- | :--- |
| | | |
