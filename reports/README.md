# reports/README.md — Rapor Dizini

Araştırma raporlarının tek satırlık dizini. Yeni bir rapor eklendiğinde buraya bir satır eklenir.
Ajan, bir rapora ihtiyacı olursa önce bu dizine bakar, sadece ilgili raporu açar. Böylece klasör şişse bile token harcanmaz.

Format: `tarih | dosya adı | konu | tek cümlelik sonuç`

| Tarih | Dosya | Konu | Sonuç |
| :--- | :--- | :--- | :--- |
| 2026-10-23 | 2026-10-23-gpu-uyum.md | RTX 5060 + CTranslate2 | INT8 bu kartta çöküyor; GPU'da float16, CPU'da int8 kullanılmalı |
