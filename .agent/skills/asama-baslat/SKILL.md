---
name: asama-baslat
description: Yeni sohbetin başında ya da yeni bir aşamaya başlarken kullan. Proje hafıza dosyalarını ve Obsidian kişisel hafıza kasasını okur, durumu özetler, aşamanın bitti tanımını tekrar eder, kısa plan çıkarır ve kullanıcı onayını bekler. Kullanıcı "yeni oturum", "devam", "aşamaya başla" ya da "kaldığımız yerden devam" derse çağır.
---

# Oturum / aşama başlatma

Amaç: Hafızası olmayan yeni sohbet, projeyi dosyalardan ve Obsidian hafızasından toparlasın ve kullanıcı onay vermeden kod yazmasın.

## 1. Dosyaları ve Obsidian hafızasını oku
Sırayla oku (olmayanı atla ve söyle):
1. AGENTS.md
2. STIL.md (varsa bu tarzda konuş)
3. STATE.md
4. PLAN.md
5. architecture.md
6. ogrenme-gunlugu.md
7. reports/README.md (rapor dizini, raporları ihtiyaç olursa aç)
8. Arayüz işi varsa design/ui-spec.md
9. **Obsidian Hafıza Kontrolü (`obsidian` MCP):** Önceki oturumlarda yapılan işlere, kararlara ve kullanıcı tercihlerine bakmak için `obsidian` MCP araçlarıyla (`list_directory`, `search_notes`, `read_note`) ilgili proje klasörünü (ör. `02-Projeler/dikte-projesi/`) ve gerekirse `04-Kararlar-ve-Dersler/` klasörünü kontrol et. Tüm kasayı okuma; sadece ilgili notları ve bağlantıları (`[[wikilink]]`) aç.

Dosyaları ezberleme, ihtiyaç olunca tekrar aç. Büyük dosyalarda ilgili bölüme bak.

## 2. Gerçek durumu kontrol et
```powershell
git status --short
git log --oneline -5
```
STATE.md veya Obsidian notlarıyla çelişki varsa (commit edilmemiş değişiklik, STATE'te yazmayan dosya) kullanıcıya söyle.

## 3. Özet ver
- Projenin ne olduğunu ve hangi aşamada olduğumuzu 5 satırda yaz.
- STATE.md'deki "Sıradaki ilk adım"ı ve Obsidian'daki son oturum/karar notlarını kısaca söyle.
- Açık sorunları ve kullanıcının yapması gereken bekleyen işleri (test, kurulum) say.
- Varsayımın ya da eksik bilgin varsa sor. Tahminle doldurma.

## 4. Aşamayı başlat
Kullanıcı bir aşama seçtiyse (ya da "sıradaki aşama başlat", "devam", STATE.md'deki sıradaki adım onaylandıysa):
1. **Neler Yapılacak / Neler Yapılmayacak:** Bu aşamada ajanın tam olarak neleri yapacağını ve neleri kesinlikle yapmayacağını (kapsam dışı dosyalar, dokunulmayacak mantık) madde madde listele.
2. **Kullanılacak ve Kullanılmayacak Testler:** Bu aşamada hangi testlerin çalıştırılacağını (hangi pytest dosyaları, Playwright, manuel testler) ve hangilerinin neden çalıştırılmayacağını açıkça belirt.
3. **Tek Ajan Önceliği ve Swarm Koordinatör Sistemi (`Gemini 4 Hydrogen`):**
   - **Tek Ajan Önceliği:** İş dallanmıyorsa, kolaysa veya tek ajanın yapması daha uygunsa alt ajan/swarm çağrılmaz; ana ajan görevi doğrudan kendisi tamamlar.
   - **Paralel İş Bölümü (`swarm`):** İş gerçekten bağımsız kollara ayrıldığında yerleşik **`swarm` aracı** ile ortak mesaj panosu (Swarm Board) üzerinden yürütülür. Başlamadan önce dosyalar çakışmayacak şekilde bölünür (her işçiye özel dosya sahipliği); iki işçinin aynı anda aynı dosyayı düzenlemesine izin verilmez.
   - **Alt Aşama / İşçi Modeli ve Değiştirilebilir Düşünme Seviyesi:** Alt ajanlar ve swarm işçileri **Gemini 4 Hydrogen** (`gemini-4-hydrogen-low`, `gemini-4-hydrogen-medium`, `gemini-4-hydrogen-high`, `gemini-4-hydrogen-xhigh`) ile çalıştırılır. Düşünme seviyesi sabit değildir; alt aşamanın veya görevin zorluğuna göre serbestçe seçilir ve gerektiğinde değiştirilebilir (`low`: basit tarama/doküman, `medium`: standart kodlama/test/denetim, `high`/`xhigh`: zor mimari, kritik hata ayıklama veya kapsamlı doğrulama). Zorunlu olmadıkça başka model seçilmez.
   - **Kritik Hata Danışmanı:** Ana ajanın çözemediği aşırı kritik bir düğüm çıkarsa `claude-opus-5-5-medium` yalnızca hatanın nasıl çözüleceğini söylemesi için çağrılabilir (kod yazmaz, uzun dosya analiz etmez).
   - **Pano ve Yaşam Döngüsü:** İşçiler işini bitirdiğinde `@verifier` ve `@coordinator`'ı etiketler; koordinatör `swarm_wait` ile bekler, `read_board` ile denetler ve iş bitince `swarm{action:"kill"}` ile işçileri kapatır.
4. PLAN.md veya ilgili rapor/plan dosyasındaki bitti tanımını ve kanıtını kendi cümlenle tekrar et.
5. Kısa bir uygulama planı çıkar (varsayımlar, TDD sırası).
6. Kullanıcının yapması gerekenleri "SENİN YAPACAĞIN ŞEY:" başlığıyla listele.
7. Kaba maliyet beklentisini tek cümleyle yaz (küçük, orta, büyük iş).

## 5. Onay bekle
Kullanıcı "devam" ya da "başla" demeden kod yazma, dosya değiştirme. Sadece okuma ve plan.

## 6. Bittiğinde hatırlat
İş bitince kullanıcıya `/asama-bitir` ile aşamayı kapatmasını öner.
