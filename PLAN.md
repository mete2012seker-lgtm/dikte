# PLAN.md — Dikte Uygulaması Aşamalı Plan

Bu dosya projenin yol haritasıdır. Her aşama bitince maddeler işaretlenir ([x]). Şu anki durum için STATE.md'ye bak.

## Hedef
Windows'ta çalışan, design/ klasöründeki tasarıma uygun bir Türkçe dikte uygulaması.
Sayfalar: Dikte, Dikte Geçmişi, Modeller, Ayarlar.

## Tasarımdan bilinçli farklar (kararlı)
- Sağ paneldeki aktif model kartında "İşleme hızı" satırı YOK.
- Modeller sayfası iki bölüme ayrılır:
  - Ses Modelleri: konuşmayı yazıya çevirir (Whisper).
  - Metin Modelleri: "Yapay Zeka ile Temizle" özelliği için, metindeki kusurları düzeltir.
- "Görsel" model kategorisi YOK.
- Tasarımdaki model adları, boyutlar ve bellek rakamları örnektir. Gerçek değerler uygulamadan ölçülür.
- Kısayol varsayılanı Sağ Ctrl. Ayarlardan değiştirilebilir olacak.

## Teknoloji (öneri, Aşama 0'da doğrulanır)
- Python 3.12, faster-whisper, pywebview + HTML/CSS/JS arayüz.
- Metin modelleri: önce LM Studio veya Ollama'nın yerel sunucusuna bağlanarak (OpenAI uyumlu API). Uygulamanın içinde GGUF modeli kendisi çalıştırması Aşama 7'de denenir, riskli sayılır.
- Bellek (VRAM) sınırı: laptop kartı 8 GB. Ses modeli ve metin modeli aynı anda belleğe sığmayabilir, bu yüzden "yükle, kullan, boşalt" düzeni ya da küçük model kullanılır. Aşama 7'de ölçülür.

## Aşamalar
Her aşama bittiğinde: kanıt gösterilir, STATE.md güncellenir, git commit atılır.

### Aşama 0 — Ortam
- [x] Python 3.12.10 kuruldu (winget, kullanıcı kapsamı); `.venv` 3.12 ile yeniden oluşturuldu.
- [x] `.venv` + `requirements.txt` + `requirements-dev.txt` hazır; CUDA kütüphaneleri dahil.
- [x] PyAV `>=11,<16` sabitlendi: PyAV 16+ `av.open(metadata_errors=...)` parametresini kaldırdığı için faster-whisper 1.2 çeviri yapamıyordu.
- Kanıt: `python --version` = 3.12.10, 83 test geçti, `--selftest` GPU float16 ile metin üretti.
- Python 3.10 yedeği doğrulamadan sonra silindi.

### Aşama 1 — Çeviri motoru
- [x] faster-whisper ile bir ses dosyasından Türkçe metin alınıyor.
- [x] Önce GPU (cuda + float16), olmazsa CPU (int8). Hangi modda çalıştığı ekrana yazılıyor.
- [x] `python -m dikte --selftest` komutu: test sesini çevirir, süreyi ve modu yazar.
- Kanıt: GPU float16 ile `large-v3` 6,4 sn'de yüklendi; 9,82 sn TTS sesi çevrildi. (TTS İngilizce aksanlı olduğu için metin kusurlu; kullanıcı kaydı bekleniyor.)
- Senin yapacağın: 5–10 saniyelik Türkçe bir cümleyi kaydedip `tests/data/test.wav` olarak koy, cümlenin yazısını `tests/data/test.txt` dosyasına yaz.

### Aşama 2 — Mikrofon, kısayol ve pano (henüz arayüz yok)
- [x] Kısayola basılı tutunca kayıt, bırakınca çeviri, sonuç panoya.
- [x] Kayıt başı ve sonu için kısa ses tonu.
- [x] Geçici `.wav` çeviri sonrası siliniyor.
- Kanıt: Gerçek mikrofonla 1,15 sn kayıt (18.400 kare), pano Türkçe karakter testi, Sağ Ctrl press/release testi.
- Senin yapacağın: Not Defteri'nde gerçek konuşma testi.

### Aşama 3 — Statik arayüz
- [x] design/prototype.html uygulama penceresinde (pywebview) açılıyor.
- [x] 4 sayfa (Dikte, Dikte Geçmişi, Modeller, Ayarlar) çalışıyor (v1.2'de tamamlandı).
- Kanıt: pywebview `SAYFA_YUKLENDI` + gerçek uygulama `ready`; Playwright DOM testi; `artifacts/ui-dikte.png`.
- Senin yapacağın: Ekran görüntüsüne bakıp onay ver.

### Aşama 4 — Dikte sayfası çalışsın
- [x] Mikrofon düğmesi, durum yazısı (Dinlemeye hazır / Dinliyor / İşleniyor), metin kutusu.
- [x] Kopyala, Geri Al, dil seçici (yalnız Türkçe, pasif).
- [x] Son etkinlikler listesi (bellekte, gerçek olaylar).
- [x] Sağ panelde gerçek model, GPU/CPU ve bellek bilgisi; "İşleme hızı" yok.
- [x] "Transkripsiyonu Yenile": son kaydın sesiyle yeniden çevirir, son paragrafı değiştirir (v1.2).
- Kanıt: pytest, uçtan uca controller + pano, Playwright.
- Durum: **Kullanıcı uygulamayı çalıştırdı ve onayladı (2026-10-24). v1 tamam.**

### Aşama 5 — Dikte Geçmişi ve Ayarlar (v1.2)
- [x] Her dikte kaydedilir (tarih, süre, kelime sayısı, model, metin); son 500 kayıt.
- [x] Geçmiş: arama (Türkçe i/ı duyarsız), Tümü/Bugün/Bu hafta, Aç, Kopyala, Sil.
- [x] "Geçmişi kaydet" anahtarı: kapalıyken yeni kayıt yazılmaz, eski kayıtlar gizlenir (arşivde durur).
- [x] Ayarlar: kısayol (hazır liste: Sağ/Sol Ctrl, Sağ/Sol Alt, F8/F9/F10) + geçmiş anahtarı + geçmişi temizle.
- [x] Ayarlar `data/settings.json`, geçmiş `data/history.json` (git dışı).
- Dil ve mikrofon seçimi bu sürümde yok (pasif).
- Kanıt: `tests/test_history.py`, `tests/test_settings.py`, controller ve Playwright testleri; `artifacts/ui-gecmis.png`, `artifacts/ui-ayarlar.png`.

### Aşama 6 — Modeller sayfası: Ses Modelleri (v1.2)
- [x] 6 model: tiny, base, small, medium, large-v3, large-v3-turbo.
- [x] İndir (gerçek ilerleme yüzdesi), Aktifleştir (motoru yeniden yükle), Sil (aktif model korumalı).
- [x] Gerçek boyut ve durum diskten okunur; aktif model `settings.json`'da saklanır.
- [x] Yalnız ses modelleri; metin modelleri Aşama 7'de.
- Kanıt: `tests/test_models.py`, gerçek `large-v3 → tiny` aktifleştirme testi (`GPU / float16`), gerçek tiny silme + yeniden indirme (78.204.524 bayt), `artifacts/ui-modeller.png`.

### Aşama 7 — v1.3: Metin Modelleri, Temizle/Çevir ve otomatik yapıştırma (kapsam 2026-11-01 onaylı)
Ayrıntılı dosya/sayfa eşlemesi: `UYGULAMA-PLANI.md`.
- Ayrıntılı yerleşim, davranış ve risk listesi: `olabilir.md`.
- [x] 7a — `text_engine.py`: OpenRouter istemcisi (DPAPI ile şifreli anahtar, ucuz model filtresi, düzenlenebilir sistem promptu) + Temizle/Çevir akışı.
- [x] 7a — Ayarlar sayfasında **OpenRouter API anahtarı** alanı: gizli yazı, "Kaydet" ve "Sil" düğmeleri, anahtarın DPAPI ile şifrelenip `settings.json` yerine ayrı dosyada tutulması; "Anahtarı test et" düğmesi.
- [x] 7b — Uygulama içi GGUF kataloğu, HTTP Range ile indirme, duraklat/devam/iptal, llama.cpp ile CPU/RAM veya GPU/VRAM çalıştırma. (`llama-cpp-python` GPU/cu124 kuruldu 2026-11-03; gemma3-4b GPU 1,7 sn yükleme, ~60 tok/s. İlk çağrı ~50 sn CUDA ısınması.)
- [ ] 7c — Bellek takası: ses modeli ile metin modeli aynı anda tutulmaz; Modeller sayfasında Metin/Ses sekmeleri ve "⋯" menüsü. (Takas + sekmeler hazır; "⋯" menüsü yok, eylemler kart üstünde.)
- [x] 7d — Arka plan kısayolu + etkin pencereye otomatik yapıştırma.
- [ ] 7e — Dikte sayfası: Çıktı Dili (TR/EN/DE), "Otomatik çevir" kutusu, Temizle ve Çevir butonları; Playwright ve kalite testleri. (Arayüz + Playwright hazır; 10 cümle kalite tablosu eksik.)
- Kural: aynı dilde yalnız temizlik; 3 kelimeden kısa metinde çeviri yok. Dil kararını metin modeli tek çağrıda verir.
- Kanıt: 201 pytest, sahte HTTP sunucusuyla duraklat/devam/iptal testi, güncel Playwright ekran görüntüleri; OpenRouter gerçek çağrı 6/6 (`reports/2026-11-01-openrouter-gercek-test.md`). 10 cümle kalite tablosu ve VRAM ölçümü bekliyor.
- Senin yapacağın: Ayarlar → Yapay Zeka'dan anahtarı gir; mikrofon, yapıştırma ve indirme testlerini yap.

### Aşama 8 — Sağlamlaştırma
- [x] Hata mesajları Türkçe ve anlaşılır (mikrofon yok, model yok, GPU yok, sunucu kapalı).
- [x] Kapanışta geçici dosyalar silinir.
- [x] Metin modeli yokken/bağlantı kopukken ham metne düşüş doğrulanır.

### Aşama 9 — v1.4: Magic UI arayüzü ve karanlık mod
- [x] Magic UI esintili görünüm, mevcut HTML/CSS/JS içinde CSS uyarlaması (MagicCard, ShineBorder, AnimatedList, BentoGrid, DotPattern). 2026-11-03: `design/v2/ui-spec.md` + Playwright 6 efekt testi.
- [x] Karanlık mod: Sistem/Açık/Koyu; `<html class="dark">` + CSS değişkenleri; localStorage + settings.json.
- [x] `design/v2/` spec ve ekran görüntüleri (`design/v2/ui-spec.md` + koyu/açık × 4 sayfa + modeller-ses = 10 PNG); eski `design/` silinmedi.
- [x] `prefers-reduced-motion`: efektler tüm animasyonları kapatır, kenar parlaması statik kalır. (WCAG AA kontrast ölçümü yapılmadı — arayüz zaten AA'ya yakın renkler kullanıyor; ölçüm gerekirse ileride eklenir.)
- Kanıt: 206 pytest (Playwright 23 test), `design/v2/*.png`. Kullanıcı görsel onayı bekleniyor.

### Aşama 10 — v1.5: Kurucu ve kaldırma
- [ ] PyInstaller `onedir` + Inno Setup; kullanıcı bazlı kurulum, `%LOCALAPPDATA%\Dikte` verisi.
- [ ] Masaüstü/Başlat menüsü kısayolları; isteğe bağlı Windows açılışında başlatma.
- [ ] Ayarlar'da büyük kırmızı "Uygulamayı Kaldır" butonu, çift onay, silinecek boyut bilgisi.
- [ ] Kaldırma: exe, kısayol, otomatik başlatma, modeller, geçmiş, ayarlar, loglar ve `%TEMP%\dikte` silinir.
- Kanıt: kurulum → çalıştırma → kaldırma → klasörlerin silindiğinin kontrolü (kullanıcı testi).

### Aşama 11 — v1.6: Otomatik güncelleme (kapsam 2026-11-01 onaylı)
- [ ] Açılışta sessiz sürüm denetimi (Ayarlar'dan kapatılabilir); yeni sürüm varsa Dikte/Ayarlar sayfasında "Güncelleme hazır" bildirimi.
- [ ] Ayarlar'da **Güncelleme** kartı: "Uygulamayı Güncelle" birincil butonu (yeni sürüm yoksa devre dışı), sürüm numarası, son denetim zamanı, "Şimdi denetle" düğmesi.
- [ ] Güncelleme akışı: küçük bir `latest.json` dosyası okunur (sürüm, kurucu bağlantısı, SHA-256, sürüm notu); yeni sürüm varsa kurucu indirilir, SHA-256 doğrulanır, Inno Setup kurucusu sessiz çalıştırılır, uygulama yeniden açılır.
- [ ] Düşüş: ağ yok / indirme yarıda kaldı / özet uyuşmadı durumlarında Türkçe uyarı; uygulama çalışmaya devam eder, yarım dosya silinir.
- [ ] Sürüm numarası tek kaynaktan (`dikte/config.py`) okunur; kurucu ve güncelleme denetimi aynı değeri kullanır.
- Kanıt: sahte güncelleme sunucusuyla "yeni sürüm var / yok / bozuk dosya / ağ yok" pytest testleri; gerçek sürüm yükseltme kullanıcı testi.
- Açık karar: depo özel olduğu için `latest.json` ve kurucunun kimlik doğrulamasız erişilebilir bir yerde durması gerekir (herkese açık GitHub Releases ya da basit statik sunucu). Bu seçim 11. aşama başında sorulacak.
- Senin yapacağın: güncelleme dosyalarının yayınlanacağı yeri seçmek; ilk Release'i yayınlamak.

## Test yöntemi
| Ne test edilir | Nasıl |
| :--- | :--- |
| Mantık (geçmiş, ayarlar, model kataloğu, dosya işlemleri) | pytest, `tests/` (201 test) |
| Çeviri motoru | `--selftest` ve tests/data/test.wav |
| Arayüz görünümü | Playwright ekran görüntüsü, design/ ile karşılaştırma, DOM testi |
| Mikrofon, kısayol, başka pencereye yapıştırma | Elle test listesi ("SENİN YAPACAĞIN TEST") |

## Maliyet takibi
- Her aşama sonunda OpenRouter Activity sayfasından toplam harcamayı bak, STATE.md'deki Maliyet günlüğüne yaz.
- Aşama 3 bittiğinde harcama bütçenin yarısını geçtiyse dur ve planı gözden geçir.
