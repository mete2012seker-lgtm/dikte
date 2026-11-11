# AGENTS.md — {{PROJE_ADI}}

Bu dosya projenin kalıcı hafızasıdır. Her oturumun başında `/asama-baslat` skill'ini çalıştır (olmazsa bu dosyayı, STATE.md ve PLAN.md'yi oku).

## Proje
{{PROJE_TANIMI}}
Dil/teknoloji: {{TEKNOLOJI}}

## Dosyalar
| Dosya | Ne için |
| :--- | :--- |
| AGENTS.md | Kurallar ve onaylı kararlar (bu dosya) |
| PLAN.md | Yol haritası |
| STATE.md | Güncel durum, sıradaki adım, çalıştırma komutları |
| architecture.md | Kod haritası |
| ogrenme-gunlugu.md | Kullanıcının öğrendikleri |
| reports/ | Araştırma raporları (README.md dizin) |
| .kilo/skills/ | asama-baslat, asama-bitir |

## Kullanıcı
- Seviye: {{SEVIYE}}. Sade Türkçe konuş, terimi bir cümleyle açıkla.
- Önce çalışan sonuç, öğrenme zamanla.

## Ortam ve bütçe
- Ortam: {{ORTAM}}
- Bütçe: {{BUTCE}}. Model/araç: {{MODEL}}

## Çalışma kuralları
- Kod yazmadan önce kısa plan çıkar ve planı sorgula. Kullanıcı onaylamadan kod yazma.
- Küçük adımlarla ilerle. Bir seferde tek şey yap.
- Araştırmayı yalnızca gerektiğinde yap, ham sonucu reports/ altına kaydet, sohbete kısa özet ver.
- API anahtarı koda, nota ya da rapora yazılmaz. Anahtarlar .env dosyasında durur.
- Karar ile öneriyi ayır. Kararlar'a yalnızca kullanıcının onayladığı şeyler girer.
- Hata olursa aynı komutu tekrarlama, eksik bilgiyi bul.
- Commit ve push yalnızca `/asama-bitir` çağrıldığında ya da kullanıcı açıkça isterse yapılır.

## Test ve bitti tanımı
- Kod yazınca çalıştır, çıktıyı oku, düzelt. En fazla 3 deneme, sonra dur ve sor.
- Ajanın doğrulayamadığı şeyleri "SENİN YAPACAĞIN TEST:" başlığıyla yaz. Kullanıcı test etmeden "çalışıyor" deme.
- Görev şu üçü olmadan bitmez: çalışan sonuç, kanıt, kullanıcı için 5 maddelik özet.

## Maliyet
- Büyük dosya ya da uzun log baştan sona okunmaz. Sorun 3 denemede çözülmezse dur ve söyle.

## Öğretme kuralları
- Adımdan önce 2-3 cümleyle ne ve neden. Yeni terimi aç.
- Kullanıcının yapacağı işi "SENİN YAPACAĞIN ŞEY:" başlığıyla yaz.
- Adım sonunda "Kendin dene" küçük deneyi ekle. Açıklamalar kısa olsun.

## Kararlar (kullanıcı onaylı)
- (henüz yok)

## Öneriler (onaylanmadı)
- (henüz yok)
