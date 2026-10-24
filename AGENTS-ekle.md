# AGENTS.md'nin sonuna eklenecek bölümler

Bu dosyanın içindekileri AGENTS.md'nin en altına yapıştır. Daha önce eklediğin bir bölüm varsa tekrar ekleme. Sonra bu dosyayı silebilirsin.

---

## Tasarım
- design/ klasörü tasarımın tek kaynağıdır: görseller, ui-spec.md, prototype.html.
- Arayüzü tasarıma birebir uydur. Tasarımdan sapman gerekiyorsa önce sor.
- Bilinçli farklar PLAN.md'nin başında yazıyor, onlara uy.

## Test kuralları
- Kod yazdıktan sonra çalıştır, çıktıyı oku, hata varsa düzelt. En fazla 3 deneme yap, çözülmezse dur, durumu STATE.md'ye yaz ve bana sor.
- Mantık için pytest, motor için `python -m dikte --selftest`, arayüz için Playwright ekran görüntüsü ve DOM testi kullan. Testler tests/ klasöründe durur.
- Arayüzde ekran görüntüsünü design/ ile karşılaştır. Görüntü okuyamıyorsan ui-spec.md'deki metin, renk ve boyutları DOM testiyle kontrol et.
- Mikrofon, kısayol ve başka pencereye yapıştırma gibi ajanın doğrulayamadığı şeyleri "SENİN YAPACAĞIN TEST:" başlığıyla adım adım yaz. Ben test etmeden "çalışıyor" deme.
- Gerçek mikrofon veya GPU gerektirmeyen mantığı sahte (mock) veriyle test et.

## Oturum protokolü
- Oturum başında: AGENTS.md, STATE.md, PLAN.md ve architecture.md dosyalarını oku, kendi cümlenle özetle, sıradaki adımı söyle, ben "devam" demeden kod yazma.
- Oturum sonunda (ben istediğimde ya da sohbet çok uzadığında sen önerirsin):
  1. STATE.md güncelle.
  2. architecture.md güncelle.
  3. Sadece benim onayladığım kararları AGENTS.md Kararlar bölümüne ekle.
  4. PLAN.md'de biten maddeleri işaretle.
  5. ogrenme-gunlugu.md dosyasına bugün öğrendiklerimi 3-5 maddeyle ekle.
  6. git add . ve git commit.
- Sohbet çok uzadıysa bana şunu söyle: "Yeni sohbete geçelim, önce oturum sonu adımlarını yapayım." Her aşama için ayrı sohbet açılması tercih edilir.

## Maliyet kuralları
- Gereksiz yere büyük dosyaları ya da uzun logları baştan sona okuma, ilgili satırlara bak.
- Aynı dosyayı gereksiz tekrar tekrar okuma.
- Bir sorun 3 denemede çözülmezse dur ve bana söyle. Daha güçlü model gerekiyorsa söyle.

## Öğretme kuralları
- Her adımdan önce 2-3 cümleyle ne yapacağını ve nedenini açıkla.
- Yeni bir terim kullanırsan bir cümleyle ne olduğunu söyle.
- Bir komut çalıştırırsan komutun ne yaptığını söyle.
- Önemli kod bloklarının başına Türkçe, kısa bir yorum yaz.
- Benim yapmam gereken bir şey varsa "SENİN YAPACAĞIN ŞEY:" başlığıyla, adım adım yaz.
- Her adım sonunda "Kendin dene" bölümü ekle: kodda tek bir değeri kendi elimle değiştirip sonucu görebileceğim küçük bir deney öner.
- Açıklamaları kısa tut, uzun ders anlatma.
