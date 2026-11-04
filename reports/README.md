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
