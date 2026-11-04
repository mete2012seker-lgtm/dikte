# Impeccable Kurulum Planı

Kaynak: https://impeccable.style/#downloads ve https://impeccable.style/tutorials/getting-started

## Amaç
"Dikte projesi" (C:\Users\aksek\Desktop\dikte projesi) içine Impeccable agent skill'ini kurmak; Kilo Code'un `.kilo/skills/` dizininden `/impeccable` komutlarıyla erişmesini sağlamak.

## Karar
- Yöntem: `npx impeccable install` (kullanıcı onayladı, önerilen yöntem).
- Impeccable otomatik algılama Kilo Code'u hedeflemiyor; skill dosyaları muhtemelen `.claude/skills/` vb. dizinlere yazılacak. Kurulum sonrası dosyalar `.kilo/skills/impeccable/` altına kopyalanacak.
- Ön koşul: Node.js 22.12+ (`node --version` ile doğrulanmalı; bu planlama oturumunda çalıştırma izni yoktu).

## Adımlar
1. `node --version` ile Node ≥ 22.12 doğrula. Değilse Node'u güncelle (kurulumdan önce kullanıcıya sor).
2. Proje kökünde `npx impeccable install` çalıştır; interaktif istemleri takip et. Skill dosyalarının nereye yazıldığını not et (varsayılan: `.claude/skills/impeccable/` veya benzeri).
3. Yüklenen skill dizinini bul (ör. `Get-ChildItem -Recurse -Directory -Filter "impeccable"` proje kökünde).
4. Skill klasörünü `C:\Users\aksek\Desktop\dikte projesi\.kilo\skills\impeccable\` altına kopyala (SKILL.md + referans dosyaları yapısı korunarak).
5. Kilo Code oturumunu yeniden başlat; `/impeccable` komutunun skill listesinde göründüğünü doğrula.
6. `/impeccable init` çalıştır → proje kökünde `PRODUCT.md` ve `DESIGN.md` oluşturulur (kategori: dikte uygulaması; hedef kitle ve tasarım tercihleri kullanıcıdan sorulur).
7. Doğrulama: `/impeccable` komutunu tek başına çalıştır; skill projeyi inceler ve öneri vermelidir.

## Riskler
- `npx impeccable install` Kilo'yu algılamayıp bilinmeyen araç hatası verebilir → fallback: `npx skills add pbakaus/impeccable` veya GitHub repo `pbakaus/impeccable` üzerinden manuel kopyalama.
- `npx impeccable install` interaktif prompt isteyebilir → PowerShell'de çalıştırırken kullanıcı etkileşimi gerekir.
- `.kilo/skills/.gitignore` içinde kopyalanan dosyalar hariç tutulabilir → git status ile kontrol et.
- Skill dosyaları Claude Code formatına özel başlıklar içerebilir → Kilo uyumluluğunu SKILL.md yapısından teyit et.

## Doğrulama
- `Test-Path .kilo\skills\impeccable\SKILL.md` → True.
- Kilo'da `/impeccable` autocomplete'te görünüyor.
- `/impeccable init` çalışıp `PRODUCT.md` + `DESIGN.md` üretiyor.
- İsteğe bağlı: `npx impeccable detect src/` ile 59 kuralın CI çıktısı çalışıyor.

## Kapsam Dışı
- Chrome extension ve CI (detect) kurulumu — istenirse ayrı plan.
- PRODUCT.md / DESIGN.md içerik doldurma — init sonrası ayrı oturum.
