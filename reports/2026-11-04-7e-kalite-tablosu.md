# 7e — Yerel GGUF (Gemma 3 4B) 10 cümle kalite tablosu

Tarih: 2026-11-04 · Betik: geçici ölçüm betiği (`text_engine.build_messages` + `strip_response` + `validate_output` gerçek akışıyla)

## Ortam
- Model: `google_gemma-3-4b-it-Q4_K_M.gguf` (~2,49 GB), llama-cpp-python GPU (cu124)
- GPU yükleme süresi: 8,4 sn (yükte), cümle başı 0,2–1,5 sn
- Not: ilk üretim çağrısı yerine ikinci cümle 1,5 sn (CUDA ısınması ilk çağrıda beklenen ~50 sn bu koşuda görünmedi — model bellekte zaten ısınmış durumda açıldı)

## Sonuçlar

| # | Görev | Hedef | Sözcüğe düşen durum | Sonuç |
| :-- | :---- | :---- | :------------------ | :---- |
| 1 | Temizlik | tr | dolgu (ee, yani) silindi, noktalama eklendi | OK |
| 2 | Temizlik | tr | "hmm şey" silindi, saat biçimi düzeldi | OK |
| 3 | Temizlik | tr | dolgu silindi, anlam korundu | OK |
| 4 | Temizlik | tr | Türkçe karakter (ı ğ ş ç ö ü) doğru işlendi | OK |
| 5 | Temizlik | tr | "şeyyy / hani" temizlendi | OK |
| 6 | Çeviri | en | doğal İngilizce, anlam korundu | OK |
| 7 | Çeviri | en | teknik cümle çevrildi | OK |
| 8 | Çeviri | de | doğal Almanca | OK |
| 9 | Çeviri | de | teknik cümle çevrildi (Strg = Ctrl, yerel ayar) | OK |
| 10 | Çeviri | en | uzun cümle çevrildi | OK |

**Geçen: 10/10.** Örnek:

```
IN : ee yani ben bugün markete gittim ama hiçbir şey alamadım çünkü unutmuşum listeyi evde kalmış
OUT: Bugün markete gittim ama hiçbir şey alamadım çünkü listeyi evde unutmuşum.
```

## Yorum
- Temizlik: dolgu kelimeleri ve tekrarlar temiz, anlam bozulmadı.
- Çeviri: en/de hedeflerinde doğal çıktı; `validate_output` korumaları (halüsinasyon / aynı-metin / hedef-dil) tek tek tetiklenmedi.
- Hız: cümle başına 0,2–1,5 sn (GPU) — gerçek kullanımda kabul edilebilir.
- Kalan risk: ilk üretim çağrısında CUDA ısınması (STATE.md'deki açık sorun) bu ölçümde ölçülemedi; kullanıcı gerçek uygulamada ilk çağrıda yavaşlık görebilir.
