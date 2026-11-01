# Magic UI — AnimatedThemeToggler incelemesi (2026-11-01)

Kaynak: https://magicui.design/docs/components/animated-theme-toggler
Yerel referans: `web/src/components/ui/animated-theme-toggler.tsx` (React sürümü)
Amaç: Dikte'nin düz HTML/CSS/JS arayüzünde bu bileşenin davranışını yeniden yazmak.

## Bileşen ne yapıyor

- Tek bir düğme; tıklayınca `<html>` üzerindeki `dark` sınıfını değiştiriyor.
- Görsel geçiş **View Transitions API** ile: yeni tema, düğme merkezinden büyüyen bir `clip-path` şekliyle açılıyor.
- Varsayılan: `circle`, `duration = 400 ms`, `fromCenter = false` (düğme merkezi).
- İkon: koyu temada `Sun`, açık temada `Moon` (lucide). Erişilebilirlik için `sr-only` "Toggle theme" yazısı.
- `localStorage["theme"]` yazar; `theme` prop'u verilirse kontrollü moda geçip yazmayı ebeveyne bırakır.
- Sınıf değişimi `startViewTransition` callback'i içinde **senkron** yapılıyor; aksi halde API eski temayı yakalar.

## Props

| Prop | Tip | Varsayılan |
| :--- | :--- | :--- |
| `duration` | number | 400 |
| `variant` | circle / square / triangle / diamond / hexagon / rectangle / star | circle |
| `fromCenter` | boolean | false |
| `theme` / `onThemeChange` | `"light" \| "dark"` / callback | — (kontrolsüz) |

## Uygulama algoritması (React'siz)

1. Düğme `getBoundingClientRect()` → merkez `cx, cy` (veya `fromCenter` ise ekran merkezi).
2. `maxRadius = hypot(max(cx, W-cx), max(cy, H-cy))`.
3. Kapanmış hal: `circle(0% at cx% cy%)`; açık hal: `circle(R% at cx% cy%)`.
   - Yarıçap yüzdesi şu tabana göre: `MAXR = hypot(W,H)/√2`.
4. `document.startViewTransition(() => documentElement.classList.toggle("dark"))`.
5. `transition.ready` sonrası:
   ```js
   document.documentElement.animate(
     { clipPath: [kapanmis, acik] },
     { duration, easing: "ease-in-out", fill: "forwards",
       pseudoElement: "::view-transition-new(root)" }
   )
   ```
6. CSS'te varsayılan view-transition animasyonları kapatılmalı:
   ```css
   ::view-transition-old(root), ::view-transition-new(root) { animation: none; mix-blend-mode: normal; }
   ```
7. `startViewTransition` yoksa: yalnız sınıfı değiştir (anlık geçiş).

## Dikkat edilecek noktalar

- Yüzdeler `window.innerWidth/innerHeight` üzerinden hesaplanıyor; scrollbar dahil edilsin diye `visualViewport` kullanılmıyor.
- Çift tıklama koruması: geçiş sürerken (`isTransitioning`) tekrar tetiklenmiyor.
- Şekil koordinatları yüzde olarak veriliyor: Chrome, Windows %150 ölçekte px değerlerini kaydırabiliyor.
- `transition.finished` sonrası geçici CSS değişkenleri ve dataset temizleniyor.
- Python tarafında tema `settings.theme` (`system`/`light`/`dark`) ile saklanmalı; React sürümü yalnız `light/dark` yazıyor. `system` modunda düğme mevcut çözünürlüğü tersine çevirir ve `system` modundan çıkar.

## Dikte'ye uyarlama kararı

- Düğme yeri: sağ panelde "Aktif model" kartının **hemen üstünde**, kartla aynı hizada sağa yaslı küçük yuvarlak düğme (36–40 px).
- `variant="circle"`, `duration=400`, `fromCenter=false` (site ilk örnekle aynı).
- Açık tema paleti `design/` içinde yok; ayrı bir karar gerekiyor (bkz. UYGULAMA-PLANI §11.6).
- `prefers-reduced-motion` açıksa geçiş animasyonsuz yapılır.
