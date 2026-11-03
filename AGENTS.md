# AGENTS.md — Dikte projesi

Bu dosya projenin kalıcı hafızasıdır. Her oturumun başında `/asama-baslat` skill'ini çalıştır (olmazsa bu dosyayı, STIL.md, STATE.md ve PLAN.md'yi oku).

## Proje
Dikte: Windows masaüstü sesli dikte uygulaması. Sağ Ctrl basılı tutulur, konuşma kaydedilir, bırakılınca faster-whisper ile yazıya çevrilir; metin isteğe bağlı olarak temizlenip Türkçe/İngilizce/Almanca çıktıya çevrilir. Arayüz: pywebview + HTML/CSS/JS.
Hedef: design/ klasöründeki tasarıma uygun 4 sayfalı uygulama (Dikte, Dikte Geçmişi, Modeller, Ayarlar). v1 ve v1.2 (Dikte + Geçmiş + Modeller + Ayarlar + Yenile) tamamlandı. v1.3 kapsamı 2026-11-01'de onaylandı (yapay zeka ile temizle/çevir); kod henüz yazılmadı. Sırada v1.4 (Magic UI + karanlık mod), v1.5 (kurucu + kaldırma) ve v1.6 (otomatik güncelleme) var.

## Dosyalar
| Dosya | Ne için |
| :--- | :--- |
| AGENTS.md | Kurallar ve onaylı kararlar (bu dosya) |
| PLAN.md | Yol haritası |
| UYGULAMA-PLANI.md | v1.3–v1.6 için dosya/sayfa düzeyinde uygulama sırası (olabilir.md'yi koda eşler) |
| STATE.md | Güncel durum, sıradaki adım, çalıştırma komutları |
| architecture.md | Kod haritası |
| ogrenme-gunlugu.md | Kullanıcının öğrendikleri |
| STIL.md | Ajanın konuşma tarzı |
| design/ | Tasarımın tek kaynağı (görseller, ui-spec.md, prototype.html) |
| reports/ | Araştırma raporları (README.md dizin) |
| .kilo/skills/ | `asama-baslat` ve `asama-bitir` skill'leri |
| promptlar.md | Kullanıcının istem notları (ajan okumaz) |
| olabilir.md | v1.3-v1.5 ayrıntılı istek ve davranış spesifikasyonu (ne nerede, nasıl çalışır) |
| web/ | Next.js 16 + shadcn + Magic UI denemesi (AnimatedList, BentoGrid, AnimatedThemeToggler); yalnız referans, üretim arayüzü değil |

## Kullanıcı
- Kodlamaya yeni başlıyor. Sade Türkçe ile konuş, terimi bir cümleyle açıkla.
- Önce çalışan araç istiyor, öğrenmeyi zamanla ekliyor.

## Ortam ve bütçe
- Windows, proje Masaüstü\dikte projesi klasöründe (OneDrive dışı). Laptop: RTX 5060, 8 GB VRAM.
- `.venv` Python 3.12.10 ile çalışıyor (2026-10-27'de geçildi).
- Bütçe yaklaşık 10 dolar (OpenRouter). Yazıya çevirme kendi bilgisayarında yapılır; metin temizleme/çeviri için OpenRouter isteğe bağlı ve ücretlidir.

## Çalışma kuralları
- Kod yazmadan önce kısa plan çıkar ve planı sorgula: hangi varsayım yanlışsa plan çöker? Kullanıcı onaylamadan kod yazma.
- Küçük adımlarla ilerle. Bir seferde tek şey yap.
- Araştırmayı Exa ile yalnızca gerektiğinde yap. Ham sonucu reports/ altına kaydet, sohbete kısa özet ver, reports/README.md'ye tek satır ekle.
- API anahtarı koda, nota ya da rapora yazılmaz. OpenRouter anahtarı Ayarlar'da girilir ve Windows DPAPI ile şifrelenmiş saklanır; `.env` yalnız geliştirme sırları içindir.
- Model dosyaları models\ klasörüne iner (git dışı).
- Karar ile öneriyi ayır. Kararlar'a yalnızca kullanıcının onayladığı şeyler girer.
- Hata olursa aynı komutu tekrarlama. Eksik bilgiyi bul, ekle, öyle yeniden dene.
- Commit ve push yalnızca `/asama-bitir` çağrıldığında ya da kullanıcı açıkça isterse yapılır.

## Soru sorma
- Soru sormak için `question` aracını kullan.
- Süreci kolaylaştırmak için bana her türlü soruyu sormaktan çekinme. İHTİYACIN OLAN HER ŞEYİ SOR! Netliğe ulaşmak için gerektiği kadar takip sorusu sor.

## Test ve bitti tanımı
- Kod yazınca çalıştır, çıktıyı oku, düzelt. En fazla 3 deneme. Çözülmezse dur, STATE.md'ye yaz, kullanıcıya sor.
- Mantık için pytest, motor için `python -m dikte --selftest`, arayüz için Playwright (ekran görüntüsü + DOM testi). Testler tests/ altında.
- Ekran görüntüsünü design/ ile karşılaştır. Görüntü okuyamıyorsan ui-spec.md'deki değerleri DOM testiyle kontrol et.
- Mikrofon, kısayol ve başka pencereye yapıştırma gibi ajanın doğrulayamadığı şeyleri "SENİN YAPACAĞIN TEST:" başlığıyla yaz. Kullanıcı test etmeden "çalışıyor" deme.
- Görev şu üçü olmadan bitmiş sayılmaz: çalışan sonuç, kanıt (çıktı/test/dosya), kullanıcı için 5 maddelik sade özet.

## Teknik dikkat noktaları
- GPU'da compute_type="auto" RTX 5060'ta çöküyor, float16 kullan. Mod (GPU/CPU) ekranda yazsın. GPU çökerse aynı model CPU/int8, o da olmazsa small + int8.
- CUDA için nvidia-cublas-cu12 ve nvidia-cudnn-cu12 kurulu, DLL yolu `diagnostics` içinde eklenir.
- **PyAV `>=11,<16` sabit.** PyAV 16+ `av.open(metadata_errors=...)` parametresini kaldırdı; faster-whisper 1.2 çevirisi bu yüzden çöküyordu.
- Türkçe karakterleri (ı, ğ, ş, ç, ö, ü) her testte dene. Konsol UTF-8.
- Sessiz kayıtta Whisper sahte cümle üretebilir: vad_filter açık, 0,4 sn altı kayıt atlanır.
- Gizlilik: kaynak .wav çeviriden sonra silinir. Son kayıt, "Transkripsiyonu Yenile" için `%TEMP%\dikte\last.wav` olarak tutulur; yeni diktede üzerine yazılır, uygulama kapanınca silinir. Konuşulan metin loga yazılmaz; metin yalnız `data/history.json` içinde ve "Geçmişi kaydet" açıksa durur.
- Kısayol pynput ile dinlenir. Varsayılan Sağ Ctrl. Başka tuş basılıyken kayıt sürer (kabul edilmiş sınırlama).
- GPU belleğini kullanan başka program (LM Studio gibi) açıkken test etme.

## Maliyet
- Büyük dosya ya da uzun log baştan sona okunmaz, ilgili satırlara bakılır.
- Sorun 3 denemede çözülmezse dur ve söyle. Daha güçlü model gerekiyorsa öner.

## Öğretme kuralları
- Her adımdan önce 2-3 cümleyle ne yapacağını ve nedenini söyle. Yeni terimi bir cümleyle aç, komutun ne yaptığını söyle.
- Benim yapmam gereken bir şey varsa "SENİN YAPACAĞIN ŞEY:" başlığıyla adım adım yaz.
- Adım sonunda "Kendin dene" ekle: kodda tek değeri değiştirip sonucu görebileceğim küçük bir deney.
- Açıklamalar kısa olsun.

## Kararlar (kullanıcı onaylı)
- Dil: Python 3.12.10. Yazıya çevirme: faster-whisper, yerel.
- Model: GPU çalışırsa seçili model + float16, çökerse aynı model CPU/int8, olmazsa small + int8.
- Ses modeli listesi (6 adet): tiny, base, small, medium, large-v3, large-v3-turbo. İndirme, aktifleştirme ve silme uygulama içinden yapılır; aktif model `settings.json`'da saklanır. v1.3'te Metin Modelleri ayrı sekme olarak eklenir.
- Metin modeli listesi (4 adet): `qwen3-1.7b`, `qwen3-4b` (varsayılan), `gemma3-4b`, `llama32-3b`; Hugging Face'ten `.part` + Range ile indirilir, duraklat/devam/iptal vardır; çalıştırmak için `llama-cpp-python` gerekir.
- Kısayol: varsayılan Sağ Ctrl; ayarlardan hazır listeden seçilir (Sağ/Sol Ctrl, Sağ/Sol Alt, F8/F9/F10). v1.2'de çıktı yalnızca panoya; v1.3'te panoya + etkin pencereye otomatik yapıştırma.
- Geçmiş: son 500 kayıt `data/history.json`; ayarlarda kapatılınca yeni kayıt yazılmaz, eski kayıtlar gizlenir (arşivde kalır). Arama/filtre/Aç/Kopyala/Sil vardır.
- "Transkripsiyonu Yenile" son kaydın sesini tekrar çevirir, son paragrafı değiştirir. Ses `%TEMP%\dikte\last.wav` olarak yalnız uygulama açıkken tutulur.
- Kod yazan model: OpenRouter üzerinden (seçim ve gerekçe STATE.md'de, değişirse orada güncelle).
- Hafıza: Obsidian vault = proje klasörü. Yedek: özel GitHub deposu.
- Tasarım: design/ tek kaynak. Aktif model kartında işleme hızı yok. Görsel model kategorisi yok.
- v1.2 kapsamı: Geçmiş (tam), Modeller (ses, tam), Ayarlar (kısayol + geçmiş anahtarı), Yenile. Dil ve mikrofon seçimi yok.
- Arayüz: pywebview + prototype.html'den türetilen HTML/CSS/JS.
- **v1.3 kapsamı (2026-11-01 onaylı):** Çıktı dili Türkçe/İngilizce/Almanca; "Otomatik çevir" kutusu dil seçicisinin yanında; "Yapay Zeka ile Temizle" ve "Çevir" butonları aynı satırda.
- Aynı dilde yalnız temizlik yapılır, çeviri yapılmaz. 3 kelimeden kısa metinde çeviri yapılmaz, ham metin kalır.
- Dil kararını metin modeli tek çağrıda verir; Whisper dili otomatik algılar. Türkçe doğruluğu düşerse girdi dili Türkçe'ye sabitlenebilir.
- Metin modeli iki sağlayıcı: uygulama içi GGUF (llama.cpp) ve OpenRouter. OpenRouter anahtarı **Ayarlar sayfasındaki ayrı bir "OpenRouter API anahtarı" alanından** girilir (gizli yazı, Kaydet/Sil/Test et), Windows DPAPI ile şifrelenir; varsayılan liste ucuz/küçük modellerdir, "Tüm modelleri göster" açılınca katalogdaki herhangi bir model aranıp seçilebilir; sistem promptu düzenlenebilir.
- Ses ve metin modeli aynı anda bellekte tutulmaz: VRAM'den boşaltıp takas edilir; gerekirse CPU/RAM kullanılır.
- Modeller sayfası Metin/Ses sekmeleri; her modelde "⋯" menüsü; indirmede duraklat/devam/iptal.
- **v1.4 kapsamı (onaylı):** Magic UI esintili yeni arayüz, Next.js'e geçmeden mevcut HTML/CSS/JS içinde CSS uyarlaması. Karanlık mod: Sistem/Açık/Koyu. Tema düğmesi sağ panelde "Aktif model" kartının hemen üstünde; Magic UI AnimatedThemeToggler davranışı (View Transitions API + circle clip-path, 400 ms). Ayrıntı `UYGULAMA-PLANI.md` §11.
- **v1.5 kapsamı (onaylı):** PyInstaller + Inno Setup kurucu; veriler `%LOCALAPPDATA%\Dikte`; kısayollar; isteğe bağlı otomatik başlatma. Ayarlar'da büyük kırmızı "Uygulamayı Kaldır" butonu, çift onay, tüm verileri siler.
- **v1.6 kapsamı (2026-11-01 onaylı):** Otomatik güncelleme. Açılışta sessiz sürüm denetimi (kapatılabilir); Ayarlar'da "Güncelleme" kartı ve "Uygulamayı Güncelle" butonu; `latest.json` (sürüm, kurucu bağlantısı, SHA-256) → indirme → özet doğrulama → Inno Setup kurucusunu sessiz çalıştırma → yeniden açılış. Ağ/indirme hatasında Türkçe uyarı, uygulama çalışmaya devam eder. Depo özel olduğu için yayın yerinin (herkese açık Releases ya da statik sunucu) 11. aşama başında seçilmesi gerekiyor.
- **Metin sağlayıcısı varsayılanı `none` (2026-11-01 onaylı):** İlk açılışta Temizle/Çevir kapalı; kullanıcı Ayarlar → Yapay Zeka'dan Yerel veya OpenRouter seçmeden çalışmaz. Otomatik yapıştırma varsayılan açık.
- **Açık tema (2026-11-01 onaylı):** Zemin `#F7F9FD`, kart `#FFFFFF`, ana yazı `#101828`, vurgu `#3D5BF5`; tema düğmesi `Aktif model` kartının üstünde, View Transitions + circle clip-path (400 ms).
- **Kurucu paketi (2026-11-01 onaylı):** Tek CPU kurucu; CUDA bileşeni paketlenmez (GPU isteğe bağlı ayrı iş).
- **Goal bölünmesi (2026-11-01 onaylı):** İlk koşu parti 1–5, sonra 6–10, sonra 11–13; her koşu sonunda test kanıtı ve kullanıcı testi.

## Öneriler (onaylanmadı)
- Metin modelleri: LM Studio/Ollama yerel sunucusuna bağlanmak, uygulama içi GGUF'a alternatif olarak değerlendirildi; 2026-11-01'de seçilmedi.
- Arayüz modernizasyonu (2026-10-31): iki yol değerlendirildi.
  - **Next.js'e taşıma:** Magic UI bileşenleri birebir kullanılır; ama çalışan arayüzü baştan yazdırır, `window.pywebview.api` köprüsü + build/paketleme + Playwright testlerinin yenilenmesi gerekir. Riskli ve masraflı.
  - **CSS/JS'e uyarlama:** Mevcut `index.html` + `style.css` + `app.js` korunur; animasyonlar CSS `@keyframes`/`transition` ve az JS ile elle yazılır. Hızlı, düşük riskli, çevrimdışı ve testler bozulmaz; ama Magic UI kodu birebir kullanılmaz, karmaşık animasyonlar zorlaşır.
  - **Seçim (2026-11-01):** CSS/JS uyarlaması. Next.js geçişi gerekirse ayrı aşama olarak ele alınır.

## Teyit bekleyen varsayımlar
- Pencere kapanınca uygulama çıkar, sistem tepsisi yok. Windows'un normal pencere çerçevesi kullanılır.
- Her dikte yeni paragraf ekler; Yenile son paragrafı değiştirir. Kopyala tüm metni, Geri Al son paragrafı alır.
- 0,4 sn'den kısa kayıt "Ses algılanamadı" diye atlanır.
- Geçmişte en fazla 500 kayıt tutulur; sınır aşılınca en eski kayıt düşer.
- İndirme duraklatma anlık değil: açık dosya parçası bitince durur. İptal, Windows dosya kilidi yüzünden gecikebilir.
- Girdi dili otomatik algılanır; Türkçe doğruluğu düşerse Ayarlar'a "Girdi dili: Türkçe" sabitleme eklenecek.
- Kurulum kullanıcı bazlıdır, yönetici izni istemez; kaldırma tüm verileri (modeller dahil) siler.

## Kod yazma ilkeleri (Karpathy)
- Kodlamadan önce varsayımlarını açıkça söyle. Emin değilsen sor, sessizce seçme.
- İstenmeyen özellik, gereksiz soyutlama, "belki lazım olur" kodu yazma.
- Sadece istenen yeri değiştir. Yakındaki kodu/yorumları "düzelteyim" deme.
- Hedefi doğrulanabilir yap: "hatayı düzelt" → "hatayı üreten testi yaz, geçene kadar çalış".
