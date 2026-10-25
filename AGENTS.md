# AGENTS.md — Dikte projesi

Bu dosya projenin kalıcı hafızasıdır. Her oturumun başında `/asama-baslat` skill'ini çalıştır (olmazsa bu dosyayı, STIL.md, STATE.md ve PLAN.md'yi oku).

## Proje
Dikte: Türkçe çalışan Windows masaüstü sesli dikte uygulaması. Sağ Ctrl basılı tutulur, konuşma kaydedilir, bırakılınca faster-whisper ile yazıya çevrilip panoya kopyalanır. Arayüz: pywebview + HTML/CSS/JS.
Hedef: design/ klasöründeki tasarıma uygun 4 sayfalı uygulama (Dikte, Dikte Geçmişi, Modeller, Ayarlar). v1 (Dikte ekranı) tamamlandı, sıradaki v1.1.

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
- `.venv` şu an Python 3.10.11 ile çalışıyor. Python 3.12 kurulunca yeniden oluşturulacak.
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
- GPU'da compute_type="auto" RTX 5060'ta çöküyor, float16 kullan. Mod (GPU/CPU) ekranda yazsın. GPU çökerse small + int8 CPU.
- CUDA için nvidia-cublas-cu12 ve nvidia-cudnn-cu12 kurulu, DLL yolu `diagnostics` içinde eklenir.
- Türkçe karakterleri (ı, ğ, ş, ç, ö, ü) her testte dene. Konsol UTF-8.
- Sessiz kayıtta Whisper sahte cümle üretebilir: vad_filter açık, 0,4 sn altı kayıt atlanır.
- Gizlilik: geçici .wav çeviriden sonra silinir, konuşulan metin loga yazılmaz.
- Kısayol pynput ile dinlenir. Sağ Ctrl + başka tuş basılıysa kayıt sürer (kabul edilmiş sınırlama).
- GPU belleğini kullanan başka program (LM Studio gibi) açıkken test etme.

## Maliyet
- Büyük dosya ya da uzun log baştan sona okunmaz, ilgili satırlara bakılır.
- Sorun 3 denemede çözülmezse dur ve söyle. Daha güçlü model gerekiyorsa öner.
- Alt ajanlar (@arastirmaci, @gozden-gecirici) yalnızca .kilo/agents altında tanımlıysa kullanılır. En fazla 2 tane, aynı dosyaya dokunan işler paralel yapılmaz.

## Öğretme kuralları
- Her adımdan önce 2-3 cümleyle ne yapacağını ve nedenini söyle. Yeni terimi bir cümleyle aç, komutun ne yaptığını söyle.
- Benim yapmam gereken bir şey varsa "SENİN YAPACAĞIN ŞEY:" başlığıyla adım adım yaz.
- Adım sonunda "Kendin dene" ekle: kodda tek değeri değiştirip sonucu görebileceğim küçük bir deney.
- Açıklamalar kısa olsun.

## Kararlar (kullanıcı onaylı)
- Dil: Python 3.12 (kurulum bekliyor). Yazıya çevirme: faster-whisper, yerel.
- Model: GPU çalışırsa large-v3 + float16, çökerse small + int8 (CPU).
- Kısayol: varsayılan Sağ Ctrl, ayarlardan değişebilir. Çıktı: yalnızca panoya kopyalama.
- Kod yazan model: OpenRouter üzerinden (seçim ve gerekçe STATE.md'de, değişirse orada güncelle).
- Hafıza: Obsidian vault = proje klasörü. Yedek: özel GitHub deposu.
- Tasarım: design/ tek kaynak. Aktif model kartında işleme hızı yok. Modeller sayfasında Ses Modelleri ve Metin Modelleri ayrı bölüm, görsel kategori yok.
- v1 kapsamı: çekirdek + Dikte ekranı. Geçmiş, Modeller, Ayarlar v1.1'de.
- Arayüz: pywebview + prototype.html'den türetilen HTML/CSS/JS.

## Öneriler (onaylanmadı)
- Metin modelleri: önce LM Studio veya Ollama yerel sunucusuna bağlanarak.

## Teyit bekleyen varsayımlar
- Model indirme `python -m dikte --kurulum` ile (uygulama içi indirme v1.1).
- Pencere kapanınca uygulama çıkar, sistem tepsisi yok. Windows'un normal pencere çerçevesi kullanılır.
- v1'de dil yalnızca Türkçe (seçici pasif). Her dikte yeni paragraf ekler, Kopyala tüm metni, Geri Al son paragrafı alır.
- 0,4 sn'den kısa kayıt "Ses algılanamadı" diye atlanır.
