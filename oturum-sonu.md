# oturum-sonu.md — Oturum Sonu Protokolü

Bu dosya, her oturumun sonunda uygulanacak adımları tanımlar. Amaç: yeni sohbete geçen ajanın projeyi ve son durumu hiç sorguya gerek kalmadan anlaması.

## Ne zaman uygulanır?
- Kullanıcı "oturum sonu", "bitir", "kaydet" gibi bir şey derse.
- Bir aşama tamamlandığında (uygulama çalışıyor ve kanıt varsa).
- Sohbet uzadığında veya konu değiştiğinde.
- Aynı hata 2–3 denemede çözülemediğinde (durumu kaydedip kullanıcıya sorulur).

## Temel kural
**Commit ve push yalnızca kullanıcı açıkça isterse yapılır.** "Kaydet" veya "commit at" denmedikçe sadece dosyalar güncellenir, commit atılmaz. Push (GitHub'a gönderme) için ayrıca kullanıcının onayı ve bir uzak depo (remote) gerekir.

## Adımlar

### 0. Kanıtı topla
Kod değiştiyse önce çalıştır:
```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m dikte --selftest      # test wav varsa
```
Arayüz değiştiyse Playwright testini ve ekran görüntüsünü yenile (`artifacts/`).
Uygulama gerçekten açıldı mı? Açılmadıysa "bitti" denmez.

### 1. STATE.md güncelle
Şunları yaz:
- Şu anki aşama ve kullanıcı onayı.
- Biten işler **kanıtla** (test sayısı, komut çıktısı, ekran görüntüsü yolu).
- Yarım kalanlar.
- Sıradaki ilk adım.
- Açık sorunlar ve denenen çözümler.
- Test durumu tablosu.
- Çalıştırma komutları.

### 2. architecture.md güncelle
- Dosya haritasına yeni dosyaları ekle.
- Bileşen bağlantılarını ve thread modelini güncelle.
- Bilinen sorunları ve karar geçmişini yaz.
- Yeni bir dosya/klasör eklendiyse burada görünmeli.

### 3. AGENTS.md — Kararlar
- **Yalnızca kullanıcının onayladığı** kararları `Kararlar` bölümüne ekle.
- Onaylanmamış önerileri `Öneriler` bölümüne, uygulanan ama teyit bekleyenleri `Uygulanan varsayımlar` bölümüne yaz.
- Karar ile öneriyi karıştırma.

### 4. PLAN.md
- Biten maddeleri `[x]` yap.
- Kapsam değiştiyse ilgili maddeye kısa not düş (örn. "v1 kapsamı dışı, v1.1'e ertelendi").
- Tamamlanan aşamaya kanıt ve kullanıcı onayı satırı ekle.

### 5. ogrenme-gunlugu.md
- Bugün öğrenilenleri 3–5 maddeyle, sade Türkçe ekle.
- Teknik terimi bir cümleyle açıkla.
- Dosya yoksa oluştur.

### 6. Gözden geçirme
- `@gozden-gecirici` ajanı tanımlıysa commit'ten önce çağır; PLAN.md bitti tanımına ve `design/` klasörüne göre denetim iste, kod değiştirmesin.
- Ajan yoksa bunu rapora yaz; yerine testler + ekran görüntüsü + elle kontrol kullan.

### 7. Commit — yalnızca kullanıcı istediyse
Sırayla:
```powershell
git status --short
git diff --stat
# Gizli bilgi taraması: .env, API anahtarı, şifre
git add .
git diff --cached --stat
git commit -m "kisa ve aciklayici mesaj" -m "gerekirse ayrinti"
git log -1 --oneline
```
Kontroller:
- `models/`, `.venv/`, `logs/`, `artifacts/` sahneye eklenmemiş olmalı.
- API anahtarı, `.env`, şifre commit edilmemeli.
- Commit mesajı ne değiştiğini söylemeli.
- Kullanıcı istemediyse commit atma; sadece "değişiklikler hazır" de.

### 8. Push — yalnızca kullanıcı istediyse
```powershell
git remote -v
git push
```
Uzak depo yoksa önce GitHub'da repo oluşturulur (aşağıya bak). Push, commit'i GitHub hesabında görünür yapar.

### 9. Kullanıcıya rapor
Kısa ve sade:
1. Ne yapıldı? (5 madde)
2. Kanıt (test sayısı, çalıştırma çıktısı, ekran görüntüsü).
3. Commit/push yapıldı mı? Hash ve dal adı.
4. Kullanıcının yapacağı test varsa "SENİN YAPACAĞIN TEST" başlığıyla adım adım.
5. Yeni sohbet için hazır başlangıç mesajı.

## Yeni sohbet başlangıç mesajı (şablon)
> AGENTS.md, STATE.md, PLAN.md, architecture.md ve design/ui-spec.md dosyalarını oku, kendi cümlelerinle özetle, sıradaki adımı söyle. Kod yazma, önce plan.

## GitHub'a ilk kez gönderme (yalnızca kullanıcı isterse)
1. GitHub'da **New repository** → ad ver (örn. `dikte`) → **Private** seç → README/gitignore ekleme → Create.
2. HTTPS adresini kopyala: `https://github.com/KULLANICI/dikte.git`
3. Proje klasöründe:
```powershell
git remote add origin https://github.com/KULLANICI/dikte.git
git branch -M main
git push -u origin main
```
4. İlk push'ta Git Credential Manager tarayıcı açar; GitHub hesabıyla giriş yap ve izin ver. Şifre yerine tarayıcı girişi kullanılır.
5. GitHub'da repoyu aç → **Commits** (saat ikonu) → commit görünür. Bundan sonra her `git push` yeni commit'leri gönderir.

## Kısa kontrol listesi
- [ ] Testler çalıştı ve sonuç yazıldı.
- [ ] STATE.md güncel.
- [ ] architecture.md güncel.
- [ ] AGENTS.md kararları güncel (yalnız onaylılar).
- [ ] PLAN.md işaretlendi.
- [ ] ogrenme-gunlugu.md'ye 3–5 madde eklendi.
- [ ] Kullanıcı istediyse commit atıldı; istenmediyse atılmadı.
- [ ] Kullanıcı istediyse ve remote varsa push yapıldı.
- [ ] Kullanıcıya 5 maddelik özet + kanıt + sonraki adım verildi.
