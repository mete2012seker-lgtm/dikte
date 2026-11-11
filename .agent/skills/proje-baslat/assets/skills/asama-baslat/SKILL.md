---
name: asama-baslat
description: Yeni sohbetin başında ya da yeni bir aşamaya başlarken kullan. Proje hafıza dosyalarını okur, durumu özetler, aşamanın bitti tanımını tekrar eder, kısa plan çıkarır ve kullanıcı onayını bekler. Kullanıcı "yeni oturum", "devam", "aşamaya başla" ya da "kaldığımız yerden devam" derse çağır.
---

# Oturum / aşama başlatma

Amaç: Hafızası olmayan yeni sohbet, projeyi dosyalardan toparlasın ve kullanıcı onay vermeden kod yazmasın.

## 1. Dosyaları oku
Sırayla oku (olmayanı atla ve söyle):
1. AGENTS.md
2. STIL.md (varsa bu tarzda konuş)
3. STATE.md
4. PLAN.md
5. architecture.md
6. ogrenme-gunlugu.md
7. reports/README.md (rapor dizini, raporları ihtiyaç olursa aç)
8. Arayüz işi varsa design/ui-spec.md

Dosyaları ezberleme, ihtiyaç olunca tekrar aç. Büyük dosyalarda ilgili bölüme bak.

## 2. Gerçek durumu kontrol et
```powershell
git status --short
git log --oneline -5
```
STATE.md ile çelişki varsa (commit edilmemiş değişiklik, STATE'te yazmayan dosya) kullanıcıya söyle.

## 3. Özet ver
- Projenin ne olduğunu ve hangi aşamada olduğumuzu 5 satırda yaz.
- STATE.md'deki "Sıradaki ilk adım"ı söyle.
- Açık sorunları ve kullanıcının yapması gereken bekleyen işleri (test, kurulum) say.
- Varsayımın ya da eksik bilgin varsa sor. Tahminle doldurma.

## 4. Aşamayı başlat
Kullanıcı bir aşama seçtiyse (ya da STATE.md'deki sıradaki adım onaylandıysa):
1. PLAN.md'deki bitti tanımını ve kanıtı kendi cümlenle tekrar et.
2. Kısa bir plan çıkar. Sonra planı sorgula: hangi varsayım yanlışsa plan çöker, nerede çöpe dönebilir?
3. Kullanıcının yapması gerekenleri "SENİN YAPACAĞIN ŞEY:" başlığıyla listele.
4. Kaba maliyet beklentisini tek cümleyle yaz (küçük, orta, büyük iş).

## 5. Onay bekle
Kullanıcı "devam" ya da "başla" demeden kod yazma, dosya değiştirme. Sadece okuma ve plan.

## 6. Bittiğinde hatırlat
İş bitince kullanıcıya `/asama-bitir` ile aşamayı kapatmasını öner.
