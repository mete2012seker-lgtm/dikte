---
name: asama-bitir
description: Bir aşamayı ya da oturumu bitirirken kullan. Testleri çalıştırır, STATE.md, architecture.md, PLAN.md, AGENTS.md ve ogrenme-gunlugu.md dosyalarını günceller, commit atıp GitHub'a gönderir, yeni sohbet için başlangıç mesajı verir. Kullanıcı "aşamayı bitir", "oturum sonu", "kaydet", "yedekle" ya da "yeni sohbete geçelim" derse çağır.
---

# Aşama / oturum sonu protokolü

Amaç: Yeni sohbete geçen ajan projeyi hiçbir şey sormadan anlasın, iş GitHub'da yedekte olsun.

Kurallar:
- Bu skill çağrıldıysa commit ve push istenmiş sayılır. Çağrılmadıkça commit ya da push yapma.
- Her adımın sonunda kanıt göster (komut çıktısı, değişen dosya). Yapılamayan adımı sessizce atlama, nedenini rapora yaz.
- Sade Türkçe konuş. STIL.md varsa o tarzda yaz.
- Gizli bilgiyi (API anahtarı, parola, .env) hiçbir dosyaya yazma.

## 0. Kanıtı topla
- Kod değiştiyse STATE.md'deki "Çalıştırma komutları" bölümünde yazan test komutlarını çalıştır, çıktıyı oku.
- Arayüz değiştiyse ekran görüntüsü testini yenile.
- Uygulama gerçekten açıldı mı? Açılmadıysa "bitti" deme.
- Başarısız test varsa dur: durumu STATE.md'ye yaz, kullanıcıya sor, commit atma.

## 1. STATE.md
Şu bölümleri güncelle: şu anki aşama ve kullanıcı onayı, biten işler (kanıtla), yarım kalanlar, sıradaki ilk adım, açık sorunlar ve denenen çözümler, bu oturumda alınan kararlar, test durumu tablosu, çalıştırma komutları. Dosyadaki bilgiyle gerçek durum çelişiyorsa gerçeği yaz ve kullanıcıya söyle.

## 2. architecture.md
Yeni ve değişen dosyaları dosya haritasına ekle, bileşen bağlantılarını, bilinen sorunları ve karar geçmişini güncelle. Projede olup haritada olmayan dosya kalmasın.

## 3. PLAN.md
Biten maddeleri [x] yap. Kapsam değiştiyse maddeye kısa not düş. Tamamlanan aşamaya kanıt ve kullanıcı onayı satırı ekle.

## 4. AGENTS.md
- Yalnızca kullanıcının onayladığı kararları "Kararlar" bölümüne ekle. Onaylanmamışları "Öneriler"e, uygulanan ama teyit bekleyenleri "Teyit bekleyen varsayımlar"a yaz.
- Dosyayı kısa tut (yaklaşık 100 satır). Aşamaya özel ayrıntılar büyürse PLAN.md'ye taşımayı öner.

## 5. ogrenme-gunlugu.md
Kullanıcının bugün öğrendiklerini sade Türkçe, 3-5 madde yaz. Teknik terimi bir cümleyle aç. Dosya yoksa oluştur.

## 6. STIL.md
Kullanıcı konuşma tarzında bir değişiklik istediyse güncelle. İstemediyse dokunma.

## 7. Gözden geçirme ve Swarm Kapanışı
Aşama sonunda tüm işlemler tamamlandığında `swarm` aracı ile `gemini-3.8-flash-medium` (`Model: "flash"`) modeline sahip `@verifier` veya `@docs-finisher` gibi işçiler devreye girer:
1. Plandaki maddeleri ve bitti tanımını kodla karşılaştırarak modellerin/kodun neleri yapıp neleri yapmadığı denetlenir.
2. Testler koşturulup sonuçlar (`pytest`, selftest, derleme) doğrulanır.
3. Bulgular panoya ve ana ajana raporlanır; koordinatör `swarm_wait` ve `read_board` ile süreci denetler, doğrulama tamamlanınca `swarm{action:"kill"}` ile işçileri temizler. Bu denetim ve doğrulama olmadan oturum kapatılmaz.

## 8. Maliyet günlüğü
STATE.md'deki Maliyet günlüğünü kendin doldurma. Kullanıcıdan OpenRouter Activity sayfasındaki toplam harcamayı iste. Verirse tarih ve aşamayla yaz, vermezse boş bırak.

## 9. Commit
PowerShell'de sırayla:
```powershell
git status --short
git diff --stat
git add .
git diff --cached --name-only
git diff --cached | Select-String -Pattern "sk-or-|api[_-]?key|secret|password|token"
```
- `.env`, `.venv/`, `models/`, `logs/`, `artifacts/` sahneye girmemiş olmalı. Girdiyse `git restore --staged <yol>` ile çıkar ve .gitignore'u düzelt.
- Gizli bilgi eşleşmesi çıkarsa dosyayı kullanıcıya göster, onay almadan commit atma. (Yanlış alarm olabilir, kullanıcıyla birlikte bak.)
- Sonra:
```powershell
git commit -m "kisa ve aciklayici mesaj" -m "gerekirse ayrinti"
git log -1 --oneline
```
Mesaj ne değiştiğini söylesin (aşama, ana değişiklik).

## 10. Push (GitHub yedeği)
```powershell
git remote -v
```
- Uzak depo yoksa ya da adreste `KULLANICI` gibi yer tutucu varsa push etme. Kullanıcıya aşağıdaki "İlk kurulum"u anlat ve dur.
- Adres gerçekse:
```powershell
git push
```
İlk push'ta upstream yoksa `git push -u origin main`. Hata olursa çıktıyı kullanıcıya sade Türkçe açıkla, tekrar tekrar deneme.

### İlk kurulum (yalnızca remote yoksa ya da yer tutucuysa)
1. GitHub'da New repository, ad ver (örneğin `dikte`), **Private** seç, README ve .gitignore ekleme, Create.
2. HTTPS adresini kopyala.
3. Proje klasöründe (kullanıcı çalıştırır):
```powershell
git remote set-url origin https://github.com/KULLANICI_ADIN/dikte.git
git push -u origin main
```
Remote hiç yoksa `set-url` yerine `git remote add origin <adres>` kullan.
4. İlk push'ta tarayıcı açılıp GitHub girişi ister. Giriş yap ve izin ver. Şifre yerine tarayıcı girişi kullanılır.

## 11. Rapor
Kısa ve sade yaz:
1. Ne yapıldı (5 madde).
2. Kanıt (test sayısı, çıktı, ekran görüntüsü yolu).
3. Commit hash'i ve dal adı. Push yapıldı mı, yapılmadıysa neden.
4. Kullanıcının yapacağı test varsa "SENİN YAPACAĞIN TEST:" başlığıyla adım adım.
5. Atlanan adımlar ve nedenleri.
6. Yeni sohbet için mesaj: "Yeni sohbette `/asama-baslat` yaz."
