# STATE.md — Güncel Durum

Bu dosya yeni sohbette kaldığımız yerden devam etmek içindir. Her oturum sonunda güncellenir.

## Şu anki aşama
**v1.3 planlaması tamamlandı (2026-11-01); kod yazılmadı.** v1.2 çalışıyor; kullanıcı elle testlerini yaptığını bildirdi. Sıradaki adım v1.3 7a: metin motoru + OpenRouter + Temizle/Çevir.

## Biten (kanıtla)
- **v1.2 tamamlandı (2026-10-27):** Geçmiş, Modeller (6 ses modeli), Ayarlar ve "Transkripsiyonu Yenile" çalışıyor. Python 3.12.10; PyAV `>=11,<16`.
- **83 pytest testi geçti** (2026-11-01, 12,34 sn).
- **Gerçek GPU selftesti:** `large-v3 / cuda / float16`, model yükleme 7,3 sn; TTS test sesi çevrildi.
- **Gerçek model değiştirme ve indirme:** `large-v3 → tiny`, GPU float16; tiny silinip Hugging Face'ten yeniden indirildi (78.204.524 bayt).
- **Gerçek uygulama:** pywebview penceresi + model `ready`; çıkışta `%TEMP%\dikte\last.wav` silindi.
- **Arayüz:** 4 sayfa Playwright ile doğrulandı; `artifacts/ui-*.png`.
- **v1.2 elle testleri:** kullanıcı 2026-10-31'de "her şey çalışıyor" dedi (mikrofon, kısayol, geçmiş anahtarı).
- **Magic UI denemesi (2026-10-31):** `web/` altında Next.js 16 + shadcn + Magic UI (`AnimatedList`, `BentoGrid`, `AnimatedThemeToggler`); lint/build geçti, dev sunucu 200. Üretim arayüzü değil.
- **v1.3/v1.4/v1.5 kapsamları onaylandı (2026-11-01):** ayrıntı PLAN.md Aşama 7, 9, 10.

## Yarım kalan
- **v1.3 kodlanmadı:** 7a metin motoru, 7b GGUF indirme/llama.cpp, 7c bellek takası, 7d arka plan yapıştırma, 7e arayüz.
- **v1.4 ve v1.5 kodlanmadı:** Magic UI + karanlık mod; kurucu + kaldırma.

## Sıradaki ilk adım
v1.3 7a: `text_engine.py`, OpenRouter istemcisi (DPAPI anahtar, ucuz model filtresi, sistem promptu), Dikte sayfasında Çıktı Dili + Temizle/Çevir + Otomatik çevir. Kullanıcı "başla" dedikten sonra kod yazılır.

## Açık sorunlar
- **llama.cpp kurulumu:** Python 3.12 + Windows + CUDA için hazır wheel bulunamayabilir; önce CPU, sonra GPU denenecek.
- **VRAM takası:** 8 GB'de ses + metin modeli aynı anda tutulmaz; boşalt-yükle gecikmesi ölçülecek.
- **Whisper dil algılama:** otomatik algılama Türkçe doğruluğunu düşürebilir; gerekirse "Girdi dili: Türkçe" sabitlemesi eklenecek.
- **OpenRouter:** ücret ve gizlilik riski; yalnız ucuz modeller, harcama STATE.md'de izlenecek.
- **İndirme duraklatma anlık değil:** açık dosya parçası bitince durur; iptal Windows kilidi yüzünden gecikebilir.
- **Otomatik yapıştırma:** yönetici pencerelerine sentetik tuş gitmeyebilir; panodaki eski içerik geri yüklenmez.
- **Kurucu:** PyInstaller + CUDA paketi büyük (~1 GB) ve antivirüs yanlış uyarısı verebilir.
- **Kaldırma geri alınamaz:** modeller, geçmiş ve ayarlar silinir; ikinci onayda boyut gösterilecek.
- **Tepsi yok:** pencere kapanınca uygulama çıkar, kısayol da durur.

## Bu oturumda alınan kararlar (kullanıcı onaylı)
- Çıktı dili Türkçe/İngilizce/Almanca; "Otomatik çevir" kutusu dil seçicisinin yanında.
- "Yapay Zeka ile Temizle" ve "Çevir" butonları aynı satırda; aynı dilde yalnız temizlik, 3 kelimeden kısa metinde çeviri yok.
- Dil kararını metin modeli tek çağrıda verir; Whisper dili otomatik algılar.
- Metin modeli iki sağlayıcı: uygulama içi GGUF (llama.cpp) ve OpenRouter. Anahtar Ayarlar'da, DPAPI ile şifreli; ucuz/küçük modeller; sistem promptu düzenlenebilir.
- Ses ve metin modeli aynı anda bellekte tutulmaz; VRAM veya CPU/RAM'de takasla çalışır.
- Modeller sayfası Metin/Ses sekmeleri; her modelde "⋯" menüsü; indirmede duraklat/devam/iptal.
- Kısayol arka planda çalışır; sonuç panoya + etkin pencereye otomatik yapıştırılır.
- v1.4: Magic UI esintili CSS/JS uyarlaması; karanlık mod Sistem/Açık/Koyu.
- v1.5: PyInstaller + Inno Setup kurucu; veriler `%LOCALAPPDATA%\Dikte`; çift onaylı kaldırma.

## Test durumu
| Test | Sonuç |
| :--- | :--- |
| `pytest -q` | 83 passed (2026-11-01) |
| `--selftest` (geçici TTS wav) | GPU float16, metin üretildi |
| Gerçek model aktifleştirme | large-v3 → tiny, GPU float16, ready |
| pywebview gerçek uygulama | Pencere + model + ready |
| Playwright arayüz | 4 sayfa, geçmiş, modeller, ayarlar, yenile |
| Gerçek mikrofon / kısayol / pano | Kullanıcı test etti (2026-10-31) |
| Gerçek model indirme | tiny silindi + yeniden indirildi (78,2 MB) |
| v1.3 metin modeli / OpenRouter | Henüz yok |
| Kurulum / kaldırma | Henüz yok |

## Çalıştırma komutları
```powershell
.venv\Scripts\python.exe -m dikte                 # uygulamayı aç
.venv\Scripts\python.exe -m dikte --selftest      # motor testi
.venv\Scripts\python.exe -m dikte --kurulum       # GPU testi + varsayılan modelleri indir
.venv\Scripts\python.exe -m dikte --dikte-testi   # arayüzsüz kısayol/kayıt/pano testi
.venv\Scripts\python.exe -m pytest -q             # testler
```

## Maliyet günlüğü (OpenRouter Activity'den kullanıcı dolduracak)
| Tarih | Aşama | Toplam harcama |
| :--- | :--- | :--- |
| | | |
