---
name: proje-baslat
description: Yeni bir proje (uygulama, oyun, araç) başlatırken kullan. Kullanıcıya birkaç kısa soru sorar, sonra klasör yapısını, git'i, .gitignore'u ve hafıza dosyalarını (AGENTS, PLAN, STATE, architecture, ogrenme-gunlugu, reports) şablonlardan kurar ve asama-baslat ile asama-bitir skill'lerini projeye ekler. Kullanıcı "yeni proje", "projeyi başlat" ya da "sıfırdan proje kur" derse çağır.
---

# Yeni proje başlatma

Şablonlar bu skill'in `assets/` klasöründedir:
`%USERPROFILE%\.kilo\skills\proje-baslat\assets\`
Dosyaları buradan oku, proje klasörüne kopyalayıp yer tutucuları doldur. Şablonu doğrudan değiştirme.

Kurallar: Sade Türkçe konuş. Gizli bilgi (API anahtarı) dosyalara yazılmaz. Kullanıcı onaylamadan commit/push yapma, ilk commit hariç (bu skill'in sonunda kullanıcıya sorarak).

## 1. Klasörü kontrol et
- Mevcut klasör boş ya da yeni mi? Dolu bir projenin içindeyse dur ve kullanıcıya sor.
- Yolda OneDrive varsa uyar (senkronizasyon git ve Obsidian'ı bozabilir). Yolda Türkçe karakter ya da boşluk varsa uyar (bazı araçlar sorun çıkarır).

## 2. Kullanıcıya kısa sorular sor (tek mesajda)
1. Proje adı ve ne yapacak (1-2 cümle)?
2. Dil/teknoloji tercihin var mı? (Bilmiyorsa öner ve nedenini söyle.)
3. Aylık maliyet bütçesi ve hangi model/araçla çalışıyor?
4. Kod bilgin ne seviyede? (Cevaba göre öğretme kurallarını ayarla.)
5. Tasarım ya da referans görsel var mı? (Varsa design/ klasörü açılır.)
Cevapları AGENTS.md'ye yaz.

## 3. Dosyaları kur
Şablonlardan oluştur ve doldur:
- `AGENTS.md` (assets/AGENTS.sablon.md)
- `PLAN.md` (assets/PLAN.sablon.md): kullanıcının hedefine göre 4-6 aşama öner, bitti tanımlarını yaz, kullanıcıya onaylat.
- `STATE.md` (assets/STATE.sablon.md)
- `architecture.md` (assets/architecture.sablon.md)
- `ogrenme-gunlugu.md` (assets/ogrenme-gunlugu.sablon.md)
- `.gitignore` (assets/gitignore.sablon): projenin diline göre ekle/çıkar.
- Klasörler: `reports/` (içine kısa bir README.md: "tarih | dosya | konu | sonuç" tablosu), `tests/`, gerekiyorsa `design/`.
- `.kilo/skills/asama-baslat/SKILL.md` ve `.kilo/skills/asama-bitir/SKILL.md`: assets/skills/ altındaki kopyaları projeye al. Proje test komutlarını STATE.md "Çalıştırma komutları"na yazılacağını `asama-bitir` zaten bekler.
- STIL.md: kullanıcı başka bir projeden kopyalamak isterse yardım et, yoksa atla.

## 4. Git
```powershell
git init
git config user.name
git config user.email
```
- Ad ve e-posta boşsa kullanıcıya söyle (`git config --global user.name "..."`). Uydurma e-posta yazılabilir, GitHub'a yüklenecek e-posta herkese açık olabilir.
- `.env` ve model dosyalarının .gitignore'da olduğunu doğrula.
- Kullanıcıya sor, sonra: `git add .` ve `git commit -m "proje iskeleti"`.

## 5. GitHub yedeği (isteğe bağlı)
Kullanıcı isterse `asama-bitir` skill'indeki "İlk kurulum" bölümünü anlat (özel depo, remote, ilk push).

## 6. Rapor
Oluşan klasör yapısını göster. Kullanıcıya sıradaki adımı söyle: yeni sohbette `/asama-baslat` yazması ve PLAN.md'deki ilk aşamayı onaylaması.
