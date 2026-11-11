# STATE.md — Güncel Durum

Bu dosya yeni sohbette kaldığımız yerden devam etmek içindir. Her oturum sonunda güncellenir.

## Şu anki aşama
**Faz 2 (veri kaybı ve çökme hataları — 11 madde) tamamlandı (2026-11-11):** pano hatasında yapıştırma iptali, bloklamayan kısayol kuyruğu, tekil Whisper yükleme kilidi (`_engine_lock`), `history_open` geçmiş kimliği senkronu, yarışsız GGUF indirme jetonu, GGUF sihirli bayt + Whisper snapshot bütünlük doğrulaması, `finish_reason == "length"` ve ≥3 kelime halüsinasyon/eksiltme koruması, tek satırlı diktelerde `strip_response` koruması, `audio.stop()` hata sarmalama, `SettingsStore`/`HistoryStore`/`SecretStore` için `RLock` + `uuid` `.tmp` + `fsync` + `OSError` koruması ve `shutdown()` içinde thread `join` + `kayit-*.wav` temizliği uygulandı ve `Model: "flash"` alt ajanıyla denetlendi. Masaüstüne `Dikte.lnk` kısayolu eklendi. **263 pytest + 1 skip geçiyor.** Sıradaki aşama: **Faz 3 (karşılama sihirbazı, sistem tepsisi/arka plan, ürün eksikleri, güncelleme/kaldırma iyileştirmeleri)**. Ayrıntı: `uygulanacak plan.md`.

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
- **Denetim + doküman senkronu (2026-11-07):** `Dikte-Denetim-Raporu.md` kod satırlarıyla doğrulandı; testler **220 passed, 1 skipped** (41,08 sn); `uygulanacak plan.md` yeniden yazıldı; STATE/PLAN/AGENTS/architecture gerçek duruma çekildi. Kod değişmedi.
- **Faz 1 yayın hazırlığı tamamlandı (2026-11-09):** `config.APP_VERSION = "1.6.0"`, `sha256` akışı, `UPDATE_URL`, kaldırma temizliği ve `installer\Output\Dikte-Setup-1.6.0.exe` (172 MB) üretildi; 245 pytest geçti.
- **Faz 2 veri kaybı ve çökme hataları tamamlandı (2026-11-11):** `uygulanacak plan.md` §4'teki 11 maddenin tamamı TDD ile uygulandı; 18 yeni regresyon testi eklendi (**263 passed, 1 skipped**); `Model: "flash"` alt ajanıyla kod ve testler satır satır denetlendi. Masaüstüne `C:\Users\aksek\Desktop\Dikte.lnk` kısayolu oluşturuldu.

## Yarım kalan
- **v1.3 / 7c:** Bellek takası + Metin/Ses sekmeleri var; "⋯" model menüsü yok. PLAN'da işaretsiz.
- **v1.3 / 7e:** Arayüz + Playwright var; kalite tablosu **kısmen** (10/10 OK var, tam girdi/çıktı çiftleri ve VRAM takas ölçümü yok).
- **v1.4:** Efektler + `design/v2/` hazır; kullanıcı gözle onayladı (2026-11-04) → kapalı.
- **v1.5:** Kaldırma + kurucu **derlendi (2026-11-09)**; kur/kaldır kullanıcı testi bekliyor. Karşılama sihirbazı kapsamı Faz 3'te.
- **v1.6:** Sürüm, sha256 akışı ve `UPDATE_URL` düzeltildi (2026-11-09). İlk GitHub Release yayınlanmadı; `latest.json` şu an 404 veriyor.
- **Karşılama sihirbazı (5 ekran):** Hiç yazılmadı; yalnız taslak HTML var. 2026-11-04'te kapsama alındı.

## Sıradaki ilk adım
1. **Faz 1 kullanıcı testi:** kurulumu kur, kaldır (modeller korunur/silinir), bir sonraki sürümde gerçek Release ile güncellemeyi dene.
2. **Faz 2 (veri kaybı ve çökme hataları):** `uygulanacak plan.md` §4. Ayrı goal olarak başlat.
3. Faz 3 (karşılama sihirbazı, ürün eksikleri) ve Faz 4 (test/hijyen/kapanış) sırayla.

## Açık sorunlar
- **Güncelleme:** GitHub'da henüz Release yok; `latest.json` 404. Kullanıcı yükleyince test edilecek.
- **Test yan etkisi:** `tests/test_ui.py` `design/v2/*.png` dosyalarının üzerine yazar. Commit'e girmemeli; her koşudan sonra `git restore design/v2/` gerekir. Faz 4'te `artifacts/`'a taşınacak.
- **Kurulum/kaldırma:** Admin kurulumda HKCU Run kaydı kurulumu yapan kullanıcıya yazılır. Gerçek UAC testi yapılmadı.
- **Karşılama sihirbazı:** hiç yazılmadı (Faz 3).
- **Inno uyarısı:** `UsedUserAreasWarning` derleme uyarısı veriyor (HKCU + admin); bilinçli bırakıldı.
- **`bin\` klasörü:** `%LOCALAPPDATA%\Dikte\bin` (27 Ağustos) Dikte kodunun dışında; kaldırmaya dahil değil.
- **`data/`, `models/` boş:** paketli sürüm ilk açılışta model bulamıyor; kullanıcı Modeller sayfasından indirmeli.
- **Karşılama sihirbazı (blocker):** 5 ekranlı akış hiç yok; `setup_done` ayarı yok.
- **Inno AppId:** `Dikte.iss:11` geçersiz GUID (`DIKTE` onaltılık değil).
- **Kurulum yeri:** **Program Files** seçildi (2026-11-07); `Dikte.iss` hâlâ `%LOCALAPPDATA%` + `lowest`, Faz 1'de güncellenecek. Kurulum/güncelleme UAC onayı ister.
- **Veri kaybı riski (Faz 2'de giderildi 2026-11-11):** Pano hatasında yapıştırma iptali, `history_open` kimlik senkronu, GGUF indirme jetonu, `finish_reason == "length"` ve `strip_response` tek satır koruması, `RLock` + `uuid` `.tmp` + `fsync` + `OSError` koruması ve temiz `shutdown()` eklendi.
- **VRAM takası:** 8 GB'de ses + metin modeli aynı anda tutulmaz; kod hazır, gerçek GGUF ile ölçüm Faz 4'te yapılacak.
- **Whisper dil algılama:** otomatik algılama Türkçe doğruluğunu düşürebilir; `input_language` ayarı var ama motora Faz 3.2'de bağlanacak.
- **llama.cpp GPU hızı:** ilk üretim çağrısı CUDA başlatma yüzünden ~50 sn; sonraki çağrılar ~60 tok/s.
- **OpenRouter:** ücret ve gizlilik riski; yalnız ucuz modeller önerilir, harcama STATE.md'de izlenir.
- **İndirme duraklatma anlık değil:** açık dosya parçası bitince durur; ses modelinde iptal butonu Faz 3.2'de eklenecek.
- **Otomatik yapıştırma:** yönetici pencerelerine sentetik tuş gitmeyebilir; panodaki eski içerik geri yüklenmez.
- **Kaldırma geri alınamaz:** modeller, geçmiş ve ayarlar silinecek; ikinci onayda boyut gösterilecek.
- **Sistem tepsisi (System Tray):** şu an pencere kapanınca uygulama çıkar; Faz 3.2'de sistem tepsisine küçültme ve pencere kapalıyken arka planda çalışma eklenecek.

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
- Denetimde 4 salt-okunur alt ajan ana ajanla aynı modeli kullanır; plan/denetim dışında tek ajan çalışır.
- Goal bölünmesi: parti 1–5, sonra 6–10, sonra 11–13.
- OpenRouter'da "Tüm modelleri göster" açılınca katalogdaki herhangi bir model aranıp seçilebilir; varsayılan liste ucuz/küçük modellerdir.
- v1.6 yayın yeri **GitHub Releases** olarak seçildi (2026-11-04); `UPDATE_URL` henüz doldurulmadı. Açık tema paleti 2026-11-01'de onaylandı.
- Metin modelleri: 4 GGUF modeli (`qwen3-1.7b`, `qwen3-4b`, `gemma3-4b`, `llama32-3b`), Hugging Face'ten `.part` + Range ile indirme, duraklat/devam/iptal, disk kontrolü.
- Modeller sayfası Metin/Ses sekmeleri; metin modelinde indir/duraklat/iptal/aktifleştir/sil.
- Bellek takası: dikte başlarken metin modeli boşaltılır, ses modeli geri yüklenir.
- Otomatik yapıştırma: etkin pencereye Ctrl+V; Dikte penceresi etkinse atlanır; varsayılan açık.
- Tema: düğme sağ panelde "Aktif model" kartının üstünde; Ayarlar → Görünüm (Sistem/Açık/Koyu); açık tema paleti onaylandı.
- 2026-11-03: AGENTS.md'den alt ajanlar bölümü silindi (artık tek ajan çalışır).
- 2026-11-07: **Plan/denetim düzeni zorunlu:** `calisma-duzeni.md` sırası (keşif → doküman → 4 paralel salt-okunur alt ajan → sentez → rapor → doğrulama) uygulanır; bulgular `dosya:satır` kanıtıyla yazılır. Denetim dışında tek ajan çalışır.
- 2026-11-04: v1.4 efektleri kullanıcı tarafından gözle onaylandı; v1.5 karşılama sihirbazı kurucu kapsamına alındı.
- 2026-11-07: Bu oturumda **yalnız doküman/plan** yapıldı; eski `uygulanacak plan.md` silinip denetim + doğrulanmış kod durumuna göre yeniden yazıldı. Kod değişmedi.
- 2026-11-07: **Kurulum:** Program Files + `PrivilegesRequired=admin`; **sürüm 1.6.0**; kaldırmada kullanıcı seçer (Inno `[UninstallDelete]` + "Modelleri koru" bayrağı); PyInstaller + Inno Setup kurulacak.
- 2026-11-07: **Yayın:** GitHub Releases; `latest.json` + kurucu yüklemeyi kullanıcı yapar; `UPDATE_URL` Releases `latest/download` yolu. **Sihirbaz:** CUDA yalnız GPU varsa. **Selftest:** sentetik TTS. **7e:** tamamlanacak. **web/:** notla tutulur. **Lisans:** MIT. **İkon:** basit `.ico` üretilir. **Eski `data/`:** taşınmaz, temiz başlangıç.
- 2026-11-11: **Faz 1 testi:** Kullanıcı önce `installer\Output\Dikte-Setup-1.6.0.exe` ile kurulum ve kaldırma testini yapacak. Yeni sekmede `/asama-baslat` ile başlanacak; model ne yapacağını/yapmayacağını, testleri ve alt ajan kurallarını detaylı listeleyecek, kullanıcı onay vermeden kod yazmayacak.
- 2026-11-11: **Faz 2 düzeni:** 11 veri kaybı ve çökme maddesi tek seferde arka arkaya uygulanacak.
- 2026-11-11: **Karşılama sihirbazı CUDA:** İsteğe bağlı olacak ("İndir" veya "CPU ile devam et / Atla").
- 2026-11-11: **Ses modeli indirme:** faster-whisper için yalnız "İptal" butonu eklenecek.
- 2026-11-11: **Selftest sesi:** 3 saniyelik sentetik Türkçe ses ("Dikte test kaydı başarılı.") ve `test.txt` üretilecek.
- 2026-11-11: **Alt ajan (sub-agent) kuralı:** Alt ajanlar daima `gemini-3.8-flash-medium` (`Model: "flash"`) ile çağrılacak. Kolay ama uzun kodlama görevlerinde ve test koşumlarında kullanılacak; aşama bitiminde modellerin yaptıklarını/yapmadıklarını denetleyip ana ajana raporlayacak.
- 2026-11-11: **Faz 2 tamamlandı:** 11 veri kaybı ve çökme maddesi TDD ile tek seferde uygulandı ve `Model: "flash"` alt ajanıyla denetlendi (**263 passed, 1 skipped**).
- 2026-11-11: **Masaüstü kısayolu ve sistem tepsisi:** Masaüstüne `Dikte.lnk` kısayolu eklendi; uygulamanın sistem tepsisine (System Tray) küçültülmesi ve pencere kapalıyken arka planda çalışması Faz 3.2 kapsamına alındı.

## Test durumu
| Test | Sonuç |
| :--- | :--- |
| `pytest -q` | **263 passed, 1 skipped** (2026-11-11, Faz 2 regresyon testleri dahil) |
| Kurucu (build.ps1) | **Üretildi:** dist\Dikte + installer\Output\Dikte-Setup-1.6.0.exe, 172.888.124 bayt, SHA-256 65a0fa042eb7eba25b70d179d346f11a366b6eb51f415c76cc2ed460177da44d |
| Paketli açılış | dist\Dikte\Dikte.exe 25 sn çalıştı; güncelleme denetimi 404 (yayın henüz yok), model yok (beklenen) |
| `--selftest` | **Çalıştırılamıyor:** `tests/data/test.wav` ve `test.txt` yok |
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
| Derleme araçları | **Yok:** PyInstaller ve Inno Setup kurulu değil; `dist/` yok |
| Kurulum / kaldırma | **Hiç denenmedi:** kod + iss + spec hazır değil (spec giriş hatası); kaldırma veriyi/autostart kaydını silmiyor |
| Güncelleme (v1.6) | test_updater 12 test geçti; `sha256` akışı ve `UPDATE_URL` nedeniyle **gerçek akış çalışmıyor** |

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

