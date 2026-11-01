# Magic UI Kullanım Kılavuzu

Bu dosya `web/` altındaki Next.js denemesinde Magic UI bileşenlerinin nasıl kullanılacağını anlatır. `web/`, Dikte'nin pywebview arayüzüne bağlı değildir; ayrı bir deneme uygulamasıdır.

## 1. Temel bilgiler

- Framework: Next.js 16 (App Router), React 19, TypeScript.
- Stil: Tailwind CSS v4 + shadcn (`base-nova` stili).
- Bileşenler: `src/components/ui/` altında.
- Import yolu: `@/components/ui/<dosya-adı>` (`@/` = `src/`).
- Paket yöneticisi: npm (`package-lock.json` var). `pnpm dlx` yalnızca komutu çalıştırmak için kullanılabilir; kurulumlar npm tarafında kalır.

## 2. Çalıştırma

```powershell
cd web
npm run dev
```

- Geliştirme: `http://localhost:3000`
- Kontrol: `npm run lint` ve `npm run build`
- Üretim çalıştırma: `npm run build` sonrası `npm start`

## 3. Yeni Magic UI bileşeni ekleme

```powershell
cd web
npx shadcn@latest add @magicui/<bilesen-adı>
```

Örnekler:

```powershell
npx shadcn@latest add @magicui/animated-list
npx shadcn@latest add @magicui/bento-grid
npx shadcn@latest add @magicui/animated-theme-toggler
```

Kurulu bileşenler:

| Bileşen | Dosya | Ek bağımlılık |
| :--- | :--- | :--- |
| AnimatedList | `src/components/ui/animated-list.tsx` | `motion` |
| BentoGrid / BentoCard | `src/components/ui/bento-grid.tsx` | `@radix-ui/react-icons` |
| AnimatedThemeToggler | `src/components/ui/animated-theme-toggler.tsx` | `lucide-react` |

Bazı bileşenler ek paket ister. Komut çıktısında "Installing dependencies" görürsen paket otomatik kurulmuştur; kurulmadıysa:

```powershell
npm install <paket-adı>
```

## 4. Client component kuralı

Next.js App Router'da `src/app/page.tsx` bir **server component**'tir. `useState`, `useEffect`, `onClick` veya Magic UI'nin animasyonlu bileşenlerini doğrudan sayfaya koymak için ayrı bir **client component** gerekir.

```tsx
// src/components/ornek-demo.tsx
"use client"

import { AnimatedList } from "@/components/ui/animated-list"

export function OrnekDemo() {
  return (
    <AnimatedList delay={1000}>
      <p>Item 1</p>
      <p>Item 2</p>
      <p>Item 3</p>
    </AnimatedList>
  )
}
```

```tsx
// src/app/page.tsx
import { OrnekDemo } from "@/components/ornek-demo"

export default function Home() {
  return (
    <main className="p-8">
      <OrnekDemo />
    </main>
  )
}
```

Kural: etkileşim veya hook varsa dosyanın en üstüne `"use client"` yaz. Server component içinde client component kullanmak sorun değildir.

## 5. AnimatedList

```tsx
"use client"

import { AnimatedList } from "@/components/ui/animated-list"

export function GecmisAkisi() {
  return (
    <AnimatedList delay={800} className="max-w-md">
      <p>Birinci kayıt</p>
      <p>İkinci kayıt</p>
      <p>Üçüncü kayıt</p>
    </AnimatedList>
  )
}
```

- `delay`: iki öğe arasındaki süre (ms). Varsayılan `1000`.
- Öğeler tek tek görünür ve **en yeni öğe üstte** olacak şekilde ters sırada dizilir.
- Liste bir kez açılır; son öğeden sonra döngüye girmez.
- Her öğe `motion` ile ölçek/opaklık animasyonu alır.
- Öğelerin benzersiz olmasına dikkat et; aynı metni tekrarlamak anahtar çakışmasına yol açabilir.

## 6. BentoGrid ve BentoCard

```tsx
import { BentoGrid, BentoCard } from "@/components/ui/bento-grid"
import { Mic } from "lucide-react"

export function ModelKartlari() {
  return (
    <BentoGrid>
      <BentoCard
        name="large-v3-turbo"
        className="col-span-3 lg:col-span-1"
        background={
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-transparent" />
        }
        Icon={Mic}
        description="Hızlı ve dengeli Türkçe dikte modeli."
        href="/modeller"
        cta="Modeli aç"
      />
    </BentoGrid>
  )
}
```

- `BentoGrid`: 3 sütunlu ızgara; `className` ile sütun sayısı değiştirilebilir.
- `BentoCard` zorunlu alanları: `name`, `className`, `background`, `Icon`, `description`, `href`, `cta`.
- `className` ile kartın kaç sütun kaplayacağını belirle: `col-span-3`, `lg:col-span-1` gibi.
- `background` alanı kartın arkasına mutlak konumla yerleşir; `absolute inset-0` kullan.
- `Icon` bir React bileşeni olmalıdır (`lucide-react` ikonları uygundur).
- Kart hover'ında açıklama yukarı kayar ve `cta` bağlantısı görünür.

## 7. AnimatedThemeToggler

```tsx
"use client"

import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler"

export function TemaDugmesi() {
  return (
    <AnimatedThemeToggler
      variant="circle"
      duration={400}
      className="rounded-md p-2"
    />
  )
}
```

- `variant`: `circle` (varsayılan), `square`, `triangle`, `diamond`, `hexagon`, `rectangle`, `star`.
- `duration`: geçiş süresi (ms).
- `fromCenter`: `true` ise geçiş ekranın ortasından başlar.
- Bileşen `<html>` üzerindeki `dark` sınıfını değiştirir ve temayı `localStorage` içinde `theme` anahtarında saklar.
- View Transitions API desteklenmeyen tarayıcılarda animasyonsuz geçiş yapar.
- Tema renkleri `src/app/globals.css` içindeki CSS değişkenlerinden gelir; yeni renk için `:root` ve `.dark` bloklarını düzenle.

## 8. shadcn ve Base UI notu

Bu proje shadcn'in `base-nova` stiliyle kuruldu; butonlar Base UI tabanlıdır. Magic UI dokümanlarındaki bazı örnekler Radix'e özgü `asChild` kullanabilir. Bu projede karşılığı `render` prop'udur:

```tsx
<Button render={<a href="/modeller" />} nativeButton={false}>
  Modeli aç
</Button>
```

Kod kopyalarken `asChild` görürsen doğrudan yapıştırma; mevcut `button.tsx` imzasına uyarla.

## 9. Sık yapılan hatalar

| Hata | Çözüm |
| :--- | :--- |
| `useState` / `onClick` derleme hatası | Dosyanın en üstüne `"use client"` ekle |
| `@/components/ui/...` bulunamadı | Dosya `src/components/ui/` altında mı kontrol et; `tsconfig.json` alias'ı `@/*` → `src/*` |
| Animasyon çalışmıyor | `motion` kurulu mu bak; bileşen client component mi kontrol et |
| Bento kartları üst üste biniyor | `BentoCard` için `className` vermeyi unutma; `col-span` değerlerini ayarla |
| Tema değişmiyor | `globals.css` içinde `.dark` bloğu var mı ve kök `<html>` mi kontrol et |
| `asChild` hatası | Base UI'de `render` prop'unu kullan |
| `next build` başarılı ama sayfada bileşen yok | Bileşeni `page.tsx` içine import edip render ettiğinden emin ol |

## 10. Dikte ile ilişki

`web/` şu an yalnızca deneme ortamıdır. Dikte'nin gerçek arayüzü `dikte/ui/index.html`, `style.css` ve `app.js` dosyalarıdır. Bu bileşenleri Dikte'de kullanmak için iki yol vardır:

1. Arayüzü Next.js'e taşımak ve pywebview'ı buna bağlamak (js_api köprüsü, build/paketleme ve test yenileme gerekir).
2. Yalnızca görsel fikri alıp mevcut HTML/CSS/JS içinde CSS animasyonu olarak yeniden yazmak.

Ayrıntılı karşılaştırma ve öneri: kök `AGENTS.md` > Öneriler (onaylanmadı).
