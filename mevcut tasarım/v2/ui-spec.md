# design/v2/ui-spec.md — v1.4 Magic UI efektleri

Tema düğmesi, açık/koyu palet ve View Transitions (`400 ms` circle clip-path) önceki aşamada eklendi. Bu belge bu aşamadaki efektlerin tek kaynağıdır.

## Efekt listesi

| Efekt | Magic UI karşılığı | Nerede | Nasıl çalışır |
| :--- | :--- | :--- | :--- |
| Kart ışığı | MagicCard | Tüm `.card`, `.m-card`, `.h-item`, `.bento-card` | Fare kart üzerindeyken `--mx/--my` değişkenleriyle fareyi izleyen soluk radial ışık (`data-fx-glow`) |
| Parlayan kenar | ShineBorder | Dikte sayfası metin kartı | `processing / cleaning / loading` durumunda `--shine-angle` ile dönen conic-gradient kenar (2,4 sn tur) |
| Kademeli liste | AnimatedList | Etkinlik zaman çizelgesi, geçmiş satırları | Giriş animasyonu; satır başına 70 ms / 60 ms gecikme, en fazla 5 adım |
| Bento ızgara | BentoGrid | Modeller sayfası üstü, 3 kart | Ses modelleri / Metin modelleri / Metin sağlayıcısı özeti; kart üstünde soluk gradyan |
| Nokta deseni | DotPattern | Dikte sayfası zemini | `::before` radial-gradient noktalar; üstten maskeyle kaybolur |

## Anahtarlar ve sınırlar

- `effects` ayarı (varsayılan açık): Ayarlar → Görünüm → "Arayüz efektleri"; `ai_settings_save` ile kalıcı.
- `prefers-reduced-motion: reduce` → tüm efekt animasyonları kapalı, kenar parlaması statik soluk kalır.
- Efektler yalnız CSS + birkaç satır JS; `document.hidden`/boşta CPU kullanımı yok (animasyonlar CSS tarafında, kart ışığı yalnız pointermove'ta güncellenir).
- Renkler açık temada da ayarlı (ışık daha soluk `rgba(61,91,245,.14)`).

## Kanıt

- `design/v2/` altında 10 PNG: koyu/açık × (dikte, geçmiş, modeller, modeller-ses, ayarlar).
- Playwright 23 arayüz testi geçti: efekt anahtarı, `fx-on` sınıfı, shine geçişi, liste gecikmeleri (0 / 70 / 140 ms), bento içerikleri, nokta deseni, kart ışığı.
