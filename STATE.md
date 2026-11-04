# STATE.md — Güncel Durum

Bu dosya yeni sohbette kaldığımız yerden devam etmek içindir. Her oturum sonunda güncellenir.

## Şu anki aşama
**v1.3 (7e dahil) + v1.4 + v1.5 + v1.6 kod tarafı tamamlandı (2026-11-04):** 7e kalite tablosu Gemma 3 4B ile 10/10 geçti (rapor: reports/2026-11-04-7e-kalite-tablosu.md); v1.5'te `dikte/uninstall.py` (kaldırma kartı, çift onay, boyut, otomatik başlatma), `Dikte.spec` ve `installer/Dikte.iss` yazıldı; v1.6'da `dikte/updater.py` (latest.json → SHA-256 → sessiz kurulum), Ayarlar'da Güncelleme kartı ve açılışta sessiz denetim eklendi. **220 pytest + 25 Playwright testi geçiyor (1 skip).** Kurulum/derleme ve gerçek güncelleme kullanıcı testi bekliyor; yayın yeri (K2) kararı açık.

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
- **v1.3 / 7a tamamlandı (2026-11-01):** `secrets.py` (DPAPI), `openrouter.py` (ucuz filtre + önbellek), `text_engine.py` (prompt, yanıt temizleme, hata kodları), `cleaning` durumu, controller `clean_text`/`translate_text` + otomatik çevir, Dikte sayfasında çıktı dili/otomatik çevir/Temizle/Çevir, Ayarlar'da Yapay Zeka + Yapıştırma/Dil kartları.
- **Otomatik çeviri sağlamlaştırıldı (2026-11-01):** boş yanıtta token bütçesi büyütülüp tekrar, açıklama/tırnak temizleme, çıktı dili denetimi (tr/en/de), kısa metin halüsinasyon koruması; yönlendirici/muhakeme/negatif fiyatlı modeller öneri listesinden çıkarıldı. Gerçek test: 6/6 cümle geçti, ~$0,0001.
- **Metin modelleri eklendi (2026-11-01):** `text_models.py` ile 4 GGUF modeli (Qwen3 1.7B/4B, Gemma 3 4B, Llama 3.2 3B), `.part` + Range ile duraklat/devam/iptal, disk alanı kontrolü, Modeller sayfasında **Metin/Ses sekmeleri**, indirme/duraklat/iptal/aktifleştir/sil eylemleri ve ses↔metin bellek takası.
- **186 test geçti**; Playwright 15 test.
- **Otomatik yapıştırma eklendi (2026-11-01):** `paste.py` etkin pencereye Ctrl+V gönderir; Dikte penceresi etkinse atlar; `auto_paste` kapatılabilir.
- **Tema eklendi (2026-11-01):** sağ panelde "Aktif model" kartının üstünde yuvarlak düğme; AnimatedThemeToggler davranışı (View Transitions + circle clip-path, 400 ms); Ayarlar → Görünüm kartı (Sistem/Açık/Koyu); açık tema paleti. `artifacts/ui-tema-*.png`.
- **201 test geçti**; Playwright 17 test (alt ajanla doğrulandı, skip yok).
- **llama-cpp-python kuruldu (2026-11-03):** GPU whl (cu124) + `nvidia-cuda-runtime-cu12`; `cudart64_12.dll` eksiği `diagnostics` yoluna eklenerek çözüldü. Gemma 3 4B GGUF ile GPU yükleme 1,7 sn; üretim ~60 tok/s. `text_models.py` yükleme öncesi `prepare_cuda_dlls()` çağırıyor.
- **v1.4 Magic UI efektleri tamamlandı (2026-11-03):** MagicCard (fareyi izleyen kart ışığı), ShineBorder (işleme sırasında dönen kenar), AnimatedList (geçmiş/etkinlik satırlarının kademeli girişi), BentoGrid (Modeller sayfası üstünde 3'lü özet), DotPattern (Dikte zemininde nokta deseni). Ayarlar → Görünüm'de "Arayüz efektleri" anahtarı; prefers-reduced-motion desteği. Ekran görüntüleri design/v2/ altında (10 PNG).
- **206 test geçti** (2026-11-03); Playwright 23 test.
- **Gözden geçirme düzeltmeleri (2026-11-01):** tema ayarı AI yükünde döndürülüyor (Ayarlar'da sıfırlanmıyor), `refresh_last` ses modelini geri yüklüyor, ses modeli değiştirilirken yüklü metin modeli boşaltılıyor, OpenRouter'da model seçilmemişse açık hata, `.part` boyutu büyükse baştan indirme, `Content-Range` başlangıcı doğrulanıyor, açık tema sekme seçicisi düzeltildi.
- **Uygulama açılışı doğrulandı (2026-11-01):** `python -m dikte` penceresi açıldı (başlık `Dikte — VoxNote AI`), log: `Model hazır: Whisper Large | GPU | float16`; kapatınca süreç kapandı.

## Yarım kalan
- **v1.3:** 7e 10 cümle kalite tablosu (llama.cpp kuruldu, model inmiş; ölçüm bekliyor).
- **v1.4 tamamlandı:** efektler + `design/v2/` hazır; kullanıcı gözle onayı bekleniyor.
- **v1.5 kodlanmadı:** kurucu + kaldırma.
- **v1.6 kodlanmadı:** otomatik güncelleme.

## Sıradaki ilk adım
1. **SENİN YAPACAĞIN ŞEY:** v1.4 efektlerini uygulamada gözle onayla; `/asama-bitir` ile aşamayı kapat.
2. v1.5 kurucu derlemesi: PyInstaller + Inno Setup kur (`Dikte.spec` → `dist\Dikte`, `ISCC installer\Dikte.iss`); kur/kaldır kullanıcı testi.
3. v1.6 yayın yeri kararı (K2): herkese açık Releases ya da statik sunucu; seçilince `config.UPDATE_URL` tek sabit doldurulur, gerçek güncelleme testi yapılır.

## Açık sorunlar
- **llama.cpp GPU hızı:** ilk üretim çağrısı CUDA başlatma yüzünden ~50 sn sürüyor; sonraki çağrılar hızlı (~60 tok/s). UI çağrılarında tek seferlik ısınma kabul edilebilir; gerekirse ön ısınma çağrısı eklenir.
- **Efekt kullanıcı onayı yok:** efektler testlerle doğrulandı; kullanıcı gözle onaylamadı.

- **VRAM takası:** 8 GB'de ses + metin modeli aynı anda tutulmaz; kod hazır, gerçek GGUF ile ölçüm yapılmadı.
- **Whisper dil algılama:** otomatik algılama Türkçe doğruluğunu düşürebilir; `input_language` ayarı var ama motora henüz bağlanmadı.
- **OpenRouter:** ücret ve gizlilik riski; yalnız ucuz modeller önerilir, harcama STATE.md'de izlenir.
- **İndirme duraklatma anlık değil:** açık dosya parçası bitince durur; iptal Windows kilidi yüzünden gecikebilir.
- **Otomatik yapıştırma:** yönetici pencerelerine sentetik tuş gitmeyebilir; panodaki eski içerik geri yüklenmez.
- **Kurucu:** PyInstaller + paket henüz yok; antivirüs yanlış uyarısı verebilir.
- **Kaldırma geri alınamaz:** modeller, geçmiş ve ayarlar silinecek; ikinci onayda boyut gösterilecek.
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
- v1.6: Otomatik güncelleme (açılışta sessiz denetim + Ayarlar'da "Uygulamayı Güncelle"); `latest.json` → SHA-256 doğrulama → sessiz kurulum → yeniden açılış.
- OpenRouter API anahtarı Ayarlar sayfasında ayrı alan (gizli yazı, Kaydet/Sil/Test et), DPAPI ile şifreli.
- Metin sağlayıcısı varsayılanı `none` (kapalı); kullanıcı seçmeden Temizle/Çevir çalışmaz.
- Otomatik yapıştırma varsayılan açık; kurucu tek CPU paketi.
- Tema düğmesi sağ panelde "Aktif model" kartının 12 px üstünde; AnimatedThemeToggler (circle, 400 ms).
- Üç alt ajan da ana ajanla aynı modeli kullanır: `deepseek/deepseek-v4.1-flash-1017`.
- Goal bölünmesi: parti 1–5, sonra 6–10, sonra 11–13.
- OpenRouter'da "Tüm modelleri göster" açılınca katalogdaki herhangi bir model aranıp seçilebilir; varsayılan liste ucuz/küçük modellerdir.
- v1.6 yayın yeri ve açık tema paleti henüz onaylanmadı (sırasıyla parti 13 ve 11).
- Metin modelleri: 4 GGUF modeli (`qwen3-1.7b`, `qwen3-4b`, `gemma3-4b`, `llama32-3b`), Hugging Face'ten `.part` + Range ile indirme, duraklat/devam/iptal, disk kontrolü.
- Modeller sayfası Metin/Ses sekmeleri; metin modelinde indir/duraklat/iptal/aktifleştir/sil.
- Bellek takası: dikte başlarken metin modeli boşaltılır, ses modeli geri yüklenir.
- Otomatik yapıştırma: etkin pencereye Ctrl+V; Dikte penceresi etkinse atlanır; varsayılan açık.
- Tema: düğme sağ panelde "Aktif model" kartının üstünde; Ayarlar → Görünüm (Sistem/Açık/Koyu); açık tema paleti onaylandı.
- 2026-11-03: AGENTS.md'den alt ajanlar bölümü silindi (artık tek ajan çalışır).

## Test durumu
| Test | Sonuç |
| :--- | :--- |
| `pytest -q` | **220 passed, 1 skipped** (2026-11-04, 37,8 sn; +12 updater, +2 Playwright guncelleme) |
| `--selftest` (geçici TTS wav) | GPU float16, metin üretildi (v1.2); **2026-11-01'de çalıştırılamadı: `tests/data/test.wav` yok** |
| Gerçek model aktifleştirme | large-v3 → tiny, GPU float16, ready |
| pywebview gerçek uygulama | Pencere + model + ready |
| Playwright arayüz | 4 sayfa, geçmiş, modeller, ayarlar, yenile, efektler, guncelleme kartı (25 test) |
| llama.cpp gerçek GGUF (2026-11-03) | gemma3-4b GPU yükleme 1,7 sn; üretim ~60 tok/s; ilk çağrı ~50 sn CUDA ısınması |
| v1.4 efektler | Playwright: efekt anahtarı, `fx-on`, shine geçişi, liste gecikmeleri, bento, nokta deseni, kart ışığı — 6 test; ekran görüntüleri `design/v2/*.png` |
| Gerçek mikrofon / kısayol / pano | Kullanıcı test etti (2026-10-31) |
| Gerçek model indirme | tiny silindi + yeniden indirildi (78,2 MB) |
| v1.3 metin motoru (sahte sunucu) | 201 testin içinde: secrets 7, settings +10, openrouter 17, text_engine 27, controller AI 31, text_models 12, paste 5 |
| Metin modeli indirme (sahte HTTP sunucusu) | Range ile devam, duraklat, iptal, 404, silme — 10 test |
| Otomatik yapıştırma | Kendi pencereyi atlama, kapalı ayar, hata — 5 test |
| Tema | Playwright: düğme sınıf değişimi + Ayarlar segmenti; `artifacts/ui-tema-*.png` |
| Gerçek uygulama açılışı | Pencere `Dikte — VoxNote AI`, model GPU float16 hazır |
| v1.3 OpenRouter gerçek çağrı | 6 cümle geçti (gemma-3-4b-it, ~$0,0001); düzeltmeler `reports/2026-11-01-openrouter-gercek-test.md` |
| Kurulum / kaldırma | Derleme + kur/kaldır kullanıcı testi bekliyor (kod + iss + spec hazır) |
| Güncelleme (v1.6) | test_updater 12 test geçti; gerçek yükseltme kullanıcı testi bekliyor |

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
| 2026-11-01 | 7a gerçek çağrı + model karşılaştırması (6 + 9 istek) | tahmini ~$0,001 — **OpenRouter Activity'den doğrula** |
