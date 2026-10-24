# promptlar.md — Hazır istemler

Bu dosya senin içindir, ajan okumaz. İstediğin istemi kopyalayıp yapıştır.

---

## 1) Gemini veya GPT'ye (ücretsiz kota): tasarım belgesi ve prototip üret
Önce iki tasarım görselini sohbete ekle, sonra şunu yapıştır. Çıkan iki dosyayı design\ klasörüne koy (ui-spec.md ve prototype.html). Görselleri de oraya koy.

```
Ekteki iki görsel (Dikte sayfası ve Modeller sayfası) bir masaüstü dikte uygulamasının tasarımı. İki çıktı üret:

1) ui-spec.md: renk kodları (hex), yazı tipleri ve boyutları, boşluklar, köşe yuvarlaklıkları, gölge ve parlama efektleri, bileşen listesi (kenar çubuğu, mikrofon düğmesi, dalga formu, metin kutusu, butonlar, kartlar, sağ panel, alt çubuk) ve her bileşenin durumları (hazır, dinliyor, işleniyor, hata).

2) prototype.html: tek dosya, harici kütüphane olmadan, görsele olabildiğince birebir. Sayfalar arası geçiş (Dikte, Dikte Geçmişi, Modeller, Ayarlar) JavaScript ile çalışsın, sahte verilerle dolu olsun.

Değişiklikler:
- Sağ paneldeki aktif model kartında "İşleme hızı" satırı olmasın.
- Modeller sayfasında "Ses Modelleri" ve "Metin Modelleri" iki ayrı bölüm (sekme) olsun. "Görsel" kategorisi olmasın. Ses modelleri konuşmayı yazıya çevirir, metin modelleri "Yapay Zeka ile Temizle" için metindeki kusurları düzeltir.
- Dikte Geçmişi ve Ayarlar sayfalarını da aynı stilde tasarla. Ayarlar: kısayol, dil, mikrofon seçimi.
- Bütün metinler Türkçe olsun.
```

---

## 2) Kilo'ya: oturum sonu (yedekle)
Yeni sohbete geçmeden önce eski sohbette yapıştır.

```
Oturumu kapatıyoruz, yeni sohbete geçeceğim. Hiçbir şey sohbet hafızasında kalmasın, hepsi dosyalara yazılsın:

1. STATE.md: şu anki aşama, bitenler (kanıtla), yarım kalanlar, sıradaki ilk adım, açık sorunlar ve denediğin çözümler, bu oturumda aldığımız kararlar, test durumu, çalıştırma komutları.
2. architecture.md: yeni veya değişen dosyalar ve bağlantıları.
3. AGENTS.md: sadece benim onayladığım yeni kararları Kararlar bölümüne ekle.
4. PLAN.md: biten maddeleri işaretle.
5. ogrenme-gunlugu.md: bugün öğrendiklerimi 3-5 maddeyle ekle.
6. Maliyet günlüğünü boş bırak, ben dolduracağım.
7. git add . ve git commit (mesaja aşamayı ve durumu yaz).

Bitince değiştirdiğin dosyaların listesini ve STATE.md'nin ilk 15 satırını göster.
```

---

## 3) Kilo'ya: yeni sohbetin ilk mesajı
```
Yeni oturum. Önce AGENTS.md, STATE.md, PLAN.md ve architecture.md dosyalarını oku (design/ ve reports/README.md de var). Sonra:
1) Projenin ne olduğunu ve hangi aşamada olduğumuzu 5 satırda özetle.
2) STATE.md'deki sıradaki adımı söyle.
3) Varsayımın ya da eksik bilgin varsa sor.
Ben "devam" demeden kod yazma.
```

---

## 4) Kilo'ya: bir aşamayı başlatma şablonu
Aşama numarasını değiştir.

```
PLAN.md'deki Aşama 3'e başlıyoruz. Önce o aşamanın bitti tanımını ve kanıtını kendi cümlenle tekrar et. Sonra kısa bir plan çıkar ve planı sorgula: hangi varsayım yanlışsa plan çöker? Ben onaylamadan kod yazma. Kod bittikten sonra testleri çalıştır, kanıtı göster, "SENİN YAPACAĞIN TEST" varsa listele.
```
