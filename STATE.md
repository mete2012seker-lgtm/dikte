# STATE.md — Güncel Durum

Bu dosya yeni sohbette kaldığımız yerden devam etmek içindir. Her oturum sonunda güncellenir.

## Şu anki aşama
**v1.2 tamamlandı (2026-10-27):** Dikte Geçmişi, Modeller, Ayarlar ve "Transkripsiyonu Yenile" çalışıyor. Python 3.12.10'a geçildi. Sıradaki: kullanıcı elle testleri, sonra v1.3 (metin modelleri + "Yapay Zeka ile Temizle").

## Biten (kanıtla)
- **Python 3.12.10 kuruldu** (winget, kullanıcı kapsamı); `.venv` 3.12 ile yeniden oluşturuldu. Eski 3.10 venv'i doğrulamadan sonra silindi.
- **PyAV uyumsuzluğu bulundu ve çözüldü:** PyAV 19, `av.open(metadata_errors=...)` parametresini kaldırdığı için faster-whisper 1.2 çöküyordu. `requirements.txt` içine `av>=11,<16` eklendi (15.1.0 kurulu).
- **83 pytest testi geçti** (`83 passed`): state, controller, engine plan, settings, history, models, UI.
- **Gerçek GPU selftesti:** `large-v3 / cuda / float16`, model yükleme 7,3 sn; TTS test sesi çevrildi ("Herkese merhaba, bu bir lokal diktasyon testi.").
- **Gerçek model değiştirme:** `large-v3 → tiny` aktifleştirildi; durum `ready`, cihaz `GPU / float16`, ayar `tiny` yazıldı; test sonunda `auto`'ya döndürüldü.
- **Gerçek uygulama açıldı:** pywebview penceresi + model `ready` (`Whisper Large / GPU`); çıkışta `%TEMP%\dikte\last.wav` silindi.
- **Gerçek model indirme:** tiny silindi ve Hugging Face'ten yeniden indirildi (78.204.524 bayt); disk durumu doğrulandı.
- **Arayüz:** 4 sayfa Playwright ile doğrulandı; `artifacts/ui-dikte.png`, `ui-gecmis.png`, `ui-modeller.png`, `ui-ayarlar.png`.
- **Yeni modüller:** `dikte/settings.py`, `dikte/history.py`, `dikte/models.py`.
- Geçmiş: son 500 kayıt, Türkçe arama (i/ı duyarsız), Tümü/Bugün/Bu hafta, Aç/Kopyala/Sil, bozuk JSON yedeği.
- Ayarlar: kısayol hazır listesi, "geçmişi kaydet" anahtarı (kapalıyken gizli arşiv), geçmişi temizle, `data/settings.json`.
- Modeller: 6 ses modeli, gerçek disk boyutu, indirme ilerlemesi, aktifleştirme, silme koruması.
- Yenile: son kayıt `last.wav` olarak tutuluyor, tekrar çeviriyor, son paragrafı ve geçmiş kaydını güncelliyor.

## Yarım kalan / kullanıcı testi bekleyen
- Gerçek mikrofonla dikte ve panoya yapıştırma (v1.2 sonrası).
- Kısayol değiştirme: F9 seçip Not Defteri'nde basılı tutma testi.
- Geçmiş anahtarını kapatıp yeni dikte etme, sayfada "Geçmiş kaydedilmiyor" görme.
- `tests/data/test.wav` repoda yok; selftest geçici TTS sesiyle yapıldı.

## Sıradaki ilk adım
Kullanıcı yukarıdaki elle testleri yapsın. Sonra v1.3 planlaması: metin modelleri ve "Yapay Zeka ile Temizle" (PLAN Aşama 7). Yeni sohbette AGENTS.md, STATE.md, PLAN.md, architecture.md okunmalı; kullanıcı onayı olmadan kod yazılmamalı.

## Açık sorunlar ve notlar
- **Model indirme iptali yok:** indirme sırasında başka indirme reddedilir; pencere kapanırsa yarım klasör "Yarım indirme" olarak görünür.
- **İlk çeviri yavaş:** CUDA ısınması + model yükleme (~7 sn). Sonraki dikte teklileri daha hızlı.
- **large-v3 + tarayıcı/oyun:** 8 GB VRAM'de başka GPU programı açıkken test edilmemeli.
- **Silme kilidi:** aktif model silinemez; Windows dosya kilidi olursa Türkçe hata gösterilir.
- **Yenile sınırı:** geçmişten bir kayıt açıldıktan sonra Yenile pasif olur (son dikte olmadığı için).
- **TTS sesi:** Windows'ta yalnız İngilizce Zira sesi var; Türkçe selftest için kullanıcı kaydı gerekli.
- **Geçmiş kapalıyken dikte, sonra açıp Yenile:** o dikte geçmişe eklenmemişse Yenile sonucu kayıtlara yazılmaz (ekran değişir, pano güncellenir). Bilinen davranış.
- **Gözden geçirme (2026-10-29):** kritik bulgu yok. İncelemeci; kilit altında disk taraması ve küçük yarış durumlarını "önemli", ölü kodu "küçük" sınıfında verdi. Kilit altındaki tarama ve ölü `beforeunload` kodu bu oturumda düzeltildi; diğerleri kabul edildi.

## Bu sürümde alınan kararlar (kullanıcı onaylı)
- Python 3.12'ye özelliklerden önce geçildi.
- Modeller sayfası tam işlevsel: indir, aktifleştir, sil; yalnız ses modelleri.
- Model listesi 6 adet: tiny, base, small, medium, large-v3, large-v3-turbo.
- Ayarlar: "geçmişi kaydet" anahtarı + hazır listeden kısayol. Dil ve mikrofon seçimi yok.
- Kısayol için serbest tuş yakalama yok; güvenli hazır liste kullanılıyor.
- Geçmiş kapalıyken eski kayıtlar gizlenir, arşivde durur; açılınca geri gelir.
- Yenile için son ses geçici dosyada tutulur; uygulama kapanınca silinir.
- Yenile sonucu son paragrafı değiştirir; yeni paragraf eklemez.

## Uygulanan varsayımlar (teyit bekliyor)
- Pencere kapanınca uygulama çıkar; sistem tepsisi yok.
- Her dikte yeni paragraf ekler; Kopyala tüm metni, Geri Al son paragrafı alır.
- Geçmişte en fazla 500 kayıt tutulur; sınır aşılınca en eski düşer.
- 0,4 sn'den kısa kayıt "Ses algılanamadı" diye atlanır.

## Test durumu
| Test | Sonuç |
| :--- | :--- |
| `pytest -q` | 83 passed |
| `--selftest` (geçici TTS wav) | GPU float16, metin üretildi |
| Gerçek model aktifleştirme | large-v3 → tiny, GPU float16, ready |
| pywebview gerçek uygulama | Pencere + model + ready |
| Playwright arayüz | 4 sayfa, geçmiş, modeller, ayarlar, yenile |
| Gerçek mikrofon / kısayol / pano | **Kullanıcı testi bekliyor** |
| Gerçek model indirme | tiny silindi + yeniden indirildi (78,2 MB) |

## Çalıştırma komutları
```powershell
.venv\Scripts\python.exe -m dikte                 # uygulamayı aç
.venv\Scripts\python.exe -m dikte --selftest      # motor testi (tests/data/test.wav)
.venv\Scripts\python.exe -m dikte --kurulum       # GPU testi + varsayılan modelleri indir
.venv\Scripts\python.exe -m dikte --dikte-testi   # arayüzsüz kısayol/kayıt/pano testi
.venv\Scripts\python.exe -m pytest -q             # testler
```

## Maliyet günlüğü (OpenRouter Activity'den ben dolduracağım)
| Tarih | Aşama | Toplam harcama |
| :--- | :--- | :--- |
| | | |
