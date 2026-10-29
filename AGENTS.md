# AGENTS.md — Dikte projesi

Bu dosya projenin kalıcı hafızasıdır. Her oturumun başında `/asama-baslat` skill'ini çalıştır (olmazsa bu dosyayı, STIL.md, STATE.md ve PLAN.md'yi oku).

## Proje
Dikte: Türkçe çalışan Windows masaüstü sesli dikte uygulaması. Sağ Ctrl basılı tutulur, konuşma kaydedilir, bırakılınca faster-whisper ile yazıya çevrilip panoya kopyalanır. Arayüz: pywebview + HTML/CSS/JS.
Hedef: design/ klasöründeki tasarıma uygun 4 sayfalı uygulama (Dikte, Dikte Geçmişi, Modeller, Ayarlar). v1 ve v1.2 (Dikte + Geçmiş + Modeller + Ayarlar + Yenile) tamamlandı; sıradaki v1.3 (metin modelleri / yapay zeka ile temizle).

## Dosyalar
| Dosya | Ne için |
| :--- | :--- |
| AGENTS.md | Kurallar ve onaylı kararlar (bu dosya) |
| PLAN.md | Yol haritası |
| STATE.md | Güncel durum, sıradaki adım, çalıştırma komutları |
| architecture.md | Kod haritası |
| ogrenme-gunlugu.md | Kullanıcının öğrendikleri |
| STIL.md | Ajanın konuşma tarzı |
| design/ | Tasarımın tek kaynağı (görseller, ui-spec.md, prototype.html) |
| reports/ | Araştırma raporları (README.md dizin) |
| .kilo/skills/ | `asama-baslat` ve `asama-bitir` skill'leri |
| promptlar.md | Kullanıcının istem notları (ajan okumaz) |

## Kullanıcı
- Kodlamaya yeni başlıyor. Sade Türkçe ile konuş, terimi bir cümleyle açıkla.
- Önce çalışan araç istiyor, öğrenmeyi zamanla ekliyor.

## Ortam ve bütçe
- Windows, proje Masaüstü\dikte projesi klasöründe (OneDrive dışı). Laptop: RTX 5060, 8 GB VRAM.
- `.venv` Python 3.12.10 ile çalışıyor (2026-10-27'de geçildi).
- Bütçe yaklaşık 10 dolar (OpenRouter). Yazıya çevirme kendi bilgisayarında yapılır, ücretli API yok.

## Çalışma kuralları
- Kod yazmadan önce kısa plan çıkar ve planı sorgula: hangi varsayım yanlışsa plan çöker? Kullanıcı onaylamadan kod yazma.
- Küçük adımlarla ilerle. Bir seferde tek şey yap.
- Araştırmayı Exa ile yalnızca gerektiğinde yap. Ham sonucu reports/ altına kaydet, sohbete kısa özet ver, reports/README.md'ye tek satır ekle.
- API anahtarı koda, nota ya da rapora yazılmaz. Anahtarlar .env dosyasında durur.
- Model dosyaları models\ klasörüne iner (git dışı).
- Karar ile öneriyi ayır. Kararlar'a yalnızca kullanıcının onayladığı şeyler girer.
- Hata olursa aynı komutu tekrarlama. Eksik bilgiyi bul, ekle, öyle yeniden dene.
- Commit ve push yalnızca `/asama-bitir` çağrıldığında ya da kullanıcı açıkça isterse yapılır.

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
- Alt ajanlar (@arastirmaci, @gozden-gecirici, @testci) yalnızca .kilo/agents altında tanımlıysa kullanılır. En fazla 3 tane; aynı dosyaya dokunan işler paralel yapılmaz. Modeller (2026-10-29 kararı): araştırmacı GPT-6 Luna (medium, kritik işlerde high), gözden geçirici GPT-6.1 Terra (medium), testçi GLM 5.3 Flash. Batch (`:batch`) uçları etkileşimli ajan işlerinde kullanılmaz, yalnız tek seferlik toplu işlerde.

## Öğretme kuralları
- Her adımdan önce 2-3 cümleyle ne yapacağını ve nedenini söyle. Yeni terimi bir cümleyle aç, komutun ne yaptığını söyle.
- Benim yapmam gereken bir şey varsa "SENİN YAPACAĞIN ŞEY:" başlığıyla adım adım yaz.
- Adım sonunda "Kendin dene" ekle: kodda tek değeri değiştirip sonucu görebileceğim küçük bir deney.
- Açıklamalar kısa olsun.

## Kararlar (kullanıcı onaylı)
- Dil: Python 3.12.10. Yazıya çevirme: faster-whisper, yerel.
- Model: GPU çalışırsa seçili model + float16, çökerse aynı model CPU/int8, olmazsa small + int8.
- Model listesi (yalnız ses, 6 adet): tiny, base, small, medium, large-v3, large-v3-turbo. İndirme, aktifleştirme ve silme uygulama içinden yapılır; aktif model `settings.json`'da saklanır.
- Kısayol: varsayılan Sağ Ctrl; ayarlardan hazır listeden seçilir (Sağ/Sol Ctrl, Sağ/Sol Alt, F8/F9/F10). Çıktı: yalnızca panoya kopyalama.
- Geçmiş: son 500 kayıt `data/history.json`; ayarlarda kapatılınca yeni kayıt yazılmaz, eski kayıtlar gizlenir (arşivde kalır). Arama/filtre/Aç/Kopyala/Sil vardır.
- "Transkripsiyonu Yenile" son kaydın sesini tekrar çevirir, son paragrafı değiştirir. Ses `%TEMP%\dikte\last.wav` olarak yalnız uygulama açıkken tutulur.
- Kod yazan model: OpenRouter üzerinden (seçim ve gerekçe STATE.md'de, değişirse orada güncelle).
- Hafıza: Obsidian vault = proje klasörü. Yedek: özel GitHub deposu.
- Tasarım: design/ tek kaynak. Aktif model kartında işleme hızı yok. v1.2'de yalnız Ses Modelleri var; Metin Modelleri v1.3'te ayrı bölüm olacak, görsel kategori yok.
- v1.2 kapsamı: Geçmiş (tam), Modeller (ses, tam), Ayarlar (kısayol + geçmiş anahtarı), Yenile. Dil ve mikrofon seçimi yok.
- Arayüz: pywebview + prototype.html'den türetilen HTML/CSS/JS.

## Öneriler (onaylanmadı)
- Metin modelleri: önce LM Studio veya Ollama yerel sunucusuna bağlanarak.

## Teyit bekleyen varsayımlar
- Pencere kapanınca uygulama çıkar, sistem tepsisi yok. Windows'un normal pencere çerçevesi kullanılır.
- Dil yalnızca Türkçe (seçici pasif). Her dikte yeni paragraf ekler; Yenile son paragrafı değiştirir. Kopyala tüm metni, Geri Al son paragrafı alır.
- 0,4 sn'den kısa kayıt "Ses algılanamadı" diye atlanır.
- Geçmişte en fazla 500 kayıt tutulur; sınır aşılınca en eski kayıt düşer.
- Model indirme iptal/duraklat desteklemez; indirme sırasında başka indirme başlatılamaz.
