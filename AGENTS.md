\# AGENTS.md — Çalışma Kuralları ve Kararlar



Bu dosya projenin hafızasıdır. Her oturumun başında ilk bunu oku.



\## Proje

Dikte: Türkçe çalışan Windows masaüstü sesli dikte uygulaması.

Kısayol tuşu basılı tutulunca mikrofonu kaydeder, bırakılınca konuşmayı yazıya çevirir ve panoya kopyalar.

Hedef: design/ klasöründeki tasarıma uygun, 4 sayfalı bir uygulama (Dikte, Dikte Geçmişi, Modeller, Ayarlar).

Yol haritası PLAN.md'de, güncel durum STATE.md'de.



\## Kullanıcı

\- Kodlamaya yeni başlıyor, daha önce hiç kod yazmadı.

\- Sade Türkçe ile konuş. Teknik bir terim kullanırsan bir cümleyle açıkla.

\- Önce çalışan araç istiyor, öğrenmeyi zamanla ekliyor.



\## Ortam ve bütçe

\- Windows. Çalışma klasörü C:\\projeler\\dikte (OneDrive dışında).

\- Laptopta RTX 5060 (8 GB VRAM) var. Bu kart yeni olduğu için CUDA uyum sorunu çıkabilir. GPU çalışmazsa otomatik olarak CPU'ya düş.

\- Bilgisayarda şu an yalnızca Python 3.10.11 kurulu. Python 3.12 kurulacak.

\- Aylık bütçe yaklaşık 10 dolar (OpenRouter). Gereksiz uzun işlem, gereksiz Exa araması ve gereksiz paralel ajan kullanma.

\- Yazıya çevirme kullanıcının kendi bilgisayarında yapılır, ücretli API kullanılmaz.



\## Çalışma kuralları

\- Kod yazmadan önce kısa bir plan çıkar. Sonra planı kendin sorgula: hangi varsayım yanlışsa plan çöker, nerede çöpe dönebilir? Gerekirse planı değiştir. Plan kutsal metin değildir.

\- Kullanıcı planı onaylamadan kod yazma.

\- Küçük adımlarla ilerle. Bir seferde tek bir şey yap.

\- Araştırmayı Exa ile yap, ama yalnızca gerçekten gerektiğinde. Ham sonuçları reports/ klasörüne dosya olarak kaydet, sohbete sadece kısa özet ver. Her rapor için reports/README.md'ye tek satır ekle.

\- API anahtarlarını asla koda, nota ya da rapora yazma. Anahtarlar .env dosyasında durur.

\- Model dosyaları proje içindeki models\\ klasörüne insin (git'e girmez).

\- Karar ile öneriyi ayır. "Kararlar" bölümüne yalnızca kullanıcının onayladığı şeyleri yaz. Öneriler "Öneriler" bölümüne gider.

\- Hata olursa aynı talimatı tekrarlama. Eksik bilginin ne olduğunu bul, ekle ve öyle yeniden dene.



\## Teknik dikkat noktaları

\- GPU'da compute\_type="auto" RTX 5060'ta çöküyor. Çalışan ayar float16.

\- Hangi modda (GPU/CPU) çalıştığı ekrana yazılsın. Sessizce CPU'ya düşme.

\- GPU belleğini kullanan başka programlar (örneğin LM Studio) açıkken test etme, bellek dolabilir.

\- Türkçe karakterleri (ı, ğ, ş, ç, ö, ü) her testte dene. Konsol kodlaması yazıyı bozabilir.

\- Sessiz kayıtta Whisper sahte cümleler üretebilir. Sessizlik filtresini (vad\_filter) aç, çok kısa kayıtları atla.

\- Mikrofon gizliliği: geçici .wav dosyası çeviriden sonra silinsin, konuşulan metin log dosyasına yazılmasın.

\- Kısayol kütüphanesi (keyboard) yönetici izni isteyebilir. Sorun çıkarsa pynput'a geç. Antivirüs yanlış uyarı verebilir.

\- Sağ Ctrl basılıyken başka tuşa basılırsa (örneğin Sağ Ctrl + C) kayıt devam eder. Kabul edilmiş sınırlama.

\- İlk çalıştırmada large-v3 modeli yaklaşık 3 GB iner, internet gerekir.



\## Tasarım

\- design/ klasörü tasarımın tek kaynağıdır: görseller, ui-spec.md, prototype.html.

\- Arayüzü tasarıma birebir uydur. Tasarımdan sapman gerekiyorsa önce sor.

\- Bilinçli farklar PLAN.md'nin başında yazıyor, onlara uy (işleme hızı yok, ses ve metin modelleri ayrı bölümler, görsel kategori yok).



\## Test kuralları

\- Kod yazdıktan sonra çalıştır, çıktıyı oku, hata varsa düzelt. En fazla 3 deneme yap, çözülmezse dur, durumu STATE.md'ye yaz ve bana sor.

\- Mantık için pytest, motor için `python -m dikte --selftest`, arayüz için Playwright ekran görüntüsü ve DOM testi kullan. Testler tests/ klasöründe durur.

\- Arayüzde ekran görüntüsünü design/ ile karşılaştır. Görüntü okuyamıyorsan ui-spec.md'deki metin, renk ve boyutları DOM testiyle kontrol et.

\- Mikrofon, kısayol ve başka pencereye yapıştırma gibi ajanın doğrulayamadığı şeyleri "SENİN YAPACAĞIN TEST:" başlığıyla adım adım yaz. Ben test etmeden "çalışıyor" deme.

\- Gerçek mikrofon veya GPU gerektirmeyen mantığı sahte (mock) veriyle test et.



\## Bitti tanımı

Bir görev şu üç şey olmadan bitmiş sayılmaz:

1\. Çalışan sonuç: uygulama gerçekten çalıştırıldı.

2\. Kanıt: çalıştırma çıktısı, test sonucu ya da dosya gösterildi.

3\. Kullanıcı için özet: "Bu kod ne yapıyor" sorusunun 5 maddede, sade Türkçe cevabı.



Kanıt yoksa görev bitmemiştir.



\## Oturum protokolü

\- Oturum başında: AGENTS.md, STATE.md, PLAN.md ve architecture.md dosyalarını oku (design/ ve reports/README.md de var), kendi cümlenle özetle, sıradaki adımı söyle, ben "devam" demeden kod yazma.

\- Oturum sonunda (ben istediğimde ya da sohbet çok uzadığında sen önerirsin):

&#x20; 1. STATE.md güncelle.

&#x20; 2. architecture.md güncelle.

&#x20; 3. Sadece benim onayladığım kararları bu dosyadaki Kararlar bölümüne ekle.

&#x20; 4. PLAN.md'de biten maddeleri işaretle.

&#x20; 5. ogrenme-gunlugu.md dosyasına bugün öğrendiklerimi 3-5 maddeyle ekle.

&#x20; 6. git add . ve git commit ile kısa bir not yazarak kaydet.

\- Sohbet çok uzadıysa bana şunu söyle: "Yeni sohbete geçelim, önce oturum sonu adımlarını yapayım." Her aşama için ayrı sohbet açılması tercih edilir.



\## Maliyet kuralları

\- Gereksiz yere büyük dosyaları ya da uzun logları baştan sona okuma, ilgili satırlara bak.

\- Aynı dosyayı gereksiz tekrar tekrar okuma.

\- Bir sorun 3 denemede çözülmezse dur ve bana söyle. Daha güçlü model gerekiyorsa söyle.



\## Alt ajanlar

\- Aşama 0, 1 ve 2'de alt ajan kullanma.

\- Araştırma gerekirse @arastirmaci'yı çağır. Ham sonuç reports/ altına yazılsın, bana 5 satır özet ver.

\- Bir aşamanın sonunda commit'ten önce @gozden-gecirici'yi çağır. PLAN.md'deki bitti tanımına ve design/ klasörüne göre kodu denetlesin, sorun listesi versin, kod değiştirmesin.

\- Alt ajanları aynı anda en fazla 2 çalıştır. Aynı dosyayı değiştiren işleri paralel yaptırma.



\## Öğretme kuralları

\- Her adımdan önce 2-3 cümleyle ne yapacağını ve nedenini açıkla.

\- Yeni bir terim kullanırsan bir cümleyle ne olduğunu söyle.

\- Bir komut çalıştırırsan komutun ne yaptığını söyle.

\- Önemli kod bloklarının başına Türkçe, kısa bir yorum yaz.

\- Benim yapmam gereken bir şey varsa "SENİN YAPACAĞIN ŞEY:" başlığıyla, adım adım yaz.

\- Her adım sonunda "Kendin dene" bölümü ekle: kodda tek bir değeri kendi elimle değiştirip sonucu görebileceğim küçük bir deney öner.

\- Açıklamaları kısa tut, uzun ders anlatma.



\## Kararlar (kullanıcı onaylı)

\- Dil: Python 3.12

\- Yazıya çevirme: faster-whisper, kullanıcının kendi bilgisayarında

\- Model: GPU çalışırsa large-v3 + float16, GPU çökerse small + int8 (CPU)

\- Kısayol: varsayılan Sağ Ctrl, ayarlardan değiştirilebilir

\- Çıktı: sadece panoya kopyalama (otomatik yapıştırma yok)

\- Kod yazan model: deepseek-v4-flash (OpenRouter üzerinden)

\- Hafıza: Obsidian vault olarak açılmış bu proje klasörü

\- Tasarım: design/ klasörü tek kaynak. Aktif model kartında işleme hızı yok. Modeller sayfasında Ses Modelleri ve Metin Modelleri ayrı bölümler.

\- v1 kapsamı: çekirdek (Sağ Ctrl, kayıt, faster-whisper, pano) + yalnız Dikte ekranı. Geçmiş, Modeller ve Ayarlar v1.1'e bırakıldı.

\- Arayüz: pywebview + mevcut HTML/CSS/JS (design/prototype.html'den türetildi).



\## Öneriler (henüz onaylanmadı)

\- Metin modelleri: önce LM Studio veya Ollama'nın yerel sunucusuna bağlanarak çalıştırmak.



\## Uygulanan varsayımlar (teyit bekliyor)

\- Model indirme `python -m dikte --kurulum` komutuyla yapılır; uygulama içi indirme v1.1'e kaldı.

\- Pencere kapatılınca uygulama çıkar; sistem tepsisi v1'de yok.

\- Windows'un normal pencere çerçevesi kullanılır (tasarımdaki sahte pencere düğmeleri kaldırıldı).

\- v1'de dil yalnızca Türkçe; dil seçici pasif.

\- Her dikte yeni paragraf ekler; Kopyala tüm metni, Geri Al son paragrafı alır.

\- 0,4 saniyeden kısa kayıtlar "Ses algılanamadı" olarak atlanır.


