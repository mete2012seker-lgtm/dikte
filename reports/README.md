# reports/README.md — Rapor Dizini

Araştırma raporlarının tek satırlık dizini. Yeni bir rapor eklendiğinde buraya bir satır eklenir.
Ajan, bir rapora ihtiyacı olursa önce bu dizine bakar, sadece ilgili raporu açar. Böylece klasör şişse bile token harcanmaz.

Format: `tarih | dosya adı | konu | tek cümlelik sonuç`

| Tarih | Dosya | Konu | Sonuç |
| :--- | :--- | :--- | :--- |
| 2026-10-23 | 2026-10-23-gpu-uyum.md | RTX 5060 + CTranslate2 | INT8 bu kartta çöküyor; GPU'da float16, CPU'da int8 kullanılmalı |
| 2026-11-01 | 2026-11-01-magicui-theme-toggler.md | Magic UI AnimatedThemeToggler | View Transitions + circle clip-path; React'siz 6 adımda uyarlanır |
| 2026-11-01 | 2026-11-01-openrouter-gercek-test.md | OpenRouter gerçek çağrı testi | Boş yanıt, açıklama ekleme ve çevirisizlik düzeltildi; varsayılan model gemma-3-4b |
| 2026-11-04 | 2026-11-04-7e-kalite-tablosu.md | 7e yerel GGUF kalite tablosu | Gemma 3 4B GPU: 10/10 cümle geçti, temizlik/çeviri doğrulu, cümle başı 0,2–1,5 sn |
| 2026-11-06 | ../Dikte-Denetim-Raporu.md | Kod denetimi (eksik/yarım/hata) | 8 yayın blockerı: güncelleme `sha256`, boş `UPDATE_URL`, sürüm 1.3.0, kaldırma verisi, derlenmemiş kurucu, eksik sihirbaz |
| 2026-11-18 | 2026-11-18-openwhispr-tanilama-ve-stabilite-raporu.md | OpenWhispr, gömülü hata tespit aracı ve stabilite denetimi | 4 swarm ajanı (Gemini 4 Hydrogen Medium) ile OpenWhispr dersleri, `error_reporter.py` tasarımı, 16 mimari/mantıksal bulgu ve 4 fazlı stabilite planı çıkarıldı |
| 2026-11-19 | 2026-11-19-yayin-oncesi-denetim-raporu.md | v1.6.1 yayın öncesi denetim | 4 paralel swarm ajanı ile 2 UAC blockerı, 8 yüksek hata ve 2 test maskesi bulundu; Faz 1–3 düzeltmeleri tek turda uygulanıp 410 testle doğrulandı |
| 2026-11-24 | 2026-11-24-kod-denetimi-raporu.md | v1.6.1 tam kod denetimi (hata/çelişki/çökme/kısaltma) | 4 paralel Gemini 4 Hydrogen işçisi; blocker yok, 6 yüksek (durum makinesi READY kaçağı, Sağ Ctrl takılı tuş kurtarma ölü, yarım GGUF kabulü, gizlenen ayar kaydı hatası, korumasız köprü çağrıları, kaldırıcı {tmp}), ~40 orta, 7 test maskesi, ~500 satır kısaltma fırsatı |
| 2026-11-25 | 2026-11-25-yayin-ve-buyume-raporu.md | Genele hitap etme ve basit tanıtım fikirleri (~1.000 kişi, zamansız) | Süre sınırı ve büyük kampanya olmadan uygulamayı genele yaklaştıran 5 ufak dokunuş (bas-bırak, dinliyor göstergesi, mikrofon seçimi, sade dil, pürüz temizliği), link önizleme güzelleştirmesi ve basit YouTube/Shorts/forum fikirleri |
| 2026-11-26 | 2026-11-26-video-arastirma-brifi.md | 4 HyperFrames tanıtım videosu araştırma ve senaryo brifi | 16:9 (50s) ve 9:16 Shorts (30s) TR/EN videoları için trend kuralları, 80% title-safe, SFX seviyeleri ve sahne-sahne prodüksiyon brifi çıkarıldı |
