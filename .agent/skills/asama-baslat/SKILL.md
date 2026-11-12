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
Kullanıcı bir aşama seçtiyse (ya da "sıradaki aşama başlat", "devam", STATE.md'deki sıradaki adım onaylandıysa):
1. **Neler Yapılacak / Neler Yapılmayacak:** Bu aşamada ajanın tam olarak neleri yapacağını ve neleri kesinlikle yapmayacağını (kapsam dışı dosyalar, dokunulmayacak mantık) madde madde listele.
2. **Kullanılacak ve Kullanılmayacak Testler:** Bu aşamada hangi testlerin çalıştırılacağını (hangi pytest dosyaları, Playwright, manuel testler) ve hangilerinin neden çalıştırılmayacağını açıkça belirt.
3. **Swarm Koordinatör Sistemi (`swarm` aracı zorunlu):**
   - Ana model (Koordinatör) orta veya kolay zorluktaki hiçbir kodu kendisi yazmaz; yalnızca en zor mimari düğümlere veya bir işçinin 3 denemede çözemediği hatalara müdahale eder.
   - Kodlama, test ve doküman işleri `invoke_subagent` yerine doğrudan yerleşik **`swarm` aracı (`swarm{action:"add", model:"gemini-3.8-flash-medium", ...}`)** ile ortak mesaj panosu (Swarm Board) üzerinden yürütülür.
   - İşe başlamadan önce dosyalar çakışmayacak şekilde (her işçiye özel dosya sahipliği vererek) bölünür (ör. `icon-tray`, `data-layer`, `controller-api`, `ui-frontend`, `verifier`) ve aynı anda paralel başlatılır (`monitor` ile birlikte).
   - İşçiler işini bitirdiğinde `@verifier` ve `@coordinator`'ı etiketler; koordinatör `swarm_wait` ile bekler, `read_board` ile denetler ve iş bitince `swarm{action:"kill"}` ile işçileri kapatır.
   - Tüm işçiler istisnasız `gemini-3.8-flash-medium` (`Model: "flash"`) ile çalıştırılır.
4. PLAN.md veya uygulanacak plan.md'deki bitti tanımını ve kanıtını kendi cümlenle tekrar et.
5. Kısa bir uygulama planı çıkar (varsayımlar, TDD sırası).
6. Kullanıcının yapması gerekenleri "SENİN YAPACAĞIN ŞEY:" başlığıyla listele.
7. Kaba maliyet beklentisini tek cümleyle yaz (küçük, orta, büyük iş).

## 5. Onay bekle
Kullanıcı "devam" ya da "başla" demeden kod yazma, dosya değiştirme. Sadece okuma ve plan.

## 6. Bittiğinde hatırlat
İş bitince kullanıcıya `/asama-bitir` ile aşamayı kapatmasını öner.
