# ui-spec.md — VoxNote AI Arayüz Spesifikasyonu

Bu dosya `design/` klasöründeki iki görselin (Dikte Çalışma Alanı, Model Yönetim Paneli) ölçü ve kural dökümüdür.
Kaynak görseller 1600 × 1000 px referans alınmıştır. `prototype.html` bu değerlerle yazılmıştır.

Bilinçli farklar (PLAN.md ile aynı):
- Aktif model kartında **"İşleme hızı" satırı yok**.
- Modeller sayfası **Ses Modelleri** ve **Metin Modelleri** olmak üzere iki sekmedir. **Görsel kategorisi yok**.
- Model adları, boyutlar ve bellek rakamları **sahte örnek veridir**.

---

## 1. Renkler

### Zemin ve yüzeyler
| Rol | Hex | Kullanım |
| :--- | :--- | :--- |
| Pencere zemini | `#060A14` | En dış arka plan, başlık çubuğu |
| Uygulama zemini | `#080D1A` | Ana içerik alanı |
| Kenar çubuğu | `#070B16` | Sol menü |
| Kart | `#0C1322` | Metin kutusu, model kartı, panel |
| Kart iç yüzey | `#0A1120` | Kart içindeki alanlar, arama kutusu |
| Durum çubuğu | `#070C18` | Alt çubuk |
| Kenarlık | `#1B2740` | Kart ve bileşen kenarları (1 px) |
| Yumuşak kenarlık | `#141E33` | Ayırıcı çizgiler |
| Güçlü kenarlık | `#2A3A5C` | Seçili kart, vurgulu kenar |
| Vurgu dolgusu | `rgba(76, 107, 255, 0.14)` | Seçili satır, rozet zemini |

### Vurgu
| Rol | Hex | Kullanım |
| :--- | :--- | :--- |
| Vurgu (ana) | `#4C6BFF` | Birincil buton, aktif menü, ilerleme çubuğu |
| Vurgu (açık uç) | `#6C5DF7` | Buton/menü gradyanının ikinci rengi |
| Vurgu metni | `#9DB2FF` | Bağlantı benzeri yazılar, ikon vurgusu |
| Mikrofon halkası | `#8FB4FF` | Mikrofon çevresi ince halka |
| Parlama | `rgba(76, 107, 255, 0.45)` | Mikrofon ve dalga formu ışıması |

### Yazı
| Rol | Hex | Kullanım |
| :--- | :--- | :--- |
| Ana yazı | `#E9EEF9` | Başlık, metin çıktısı, buton yazısı |
| İkincil yazı | `#A7B2C9` | Açıklama, alt başlık |
| Soluk yazı | `#6E7B96` | Etiket, zaman, ipucu |
| Ters yazı | `#FFFFFF` | Vurgu butonu üzerindeki yazı |

### Durum renkleri
| Durum | Hex | Nokta/ikon | Metin |
| :--- | :--- | :--- | :--- |
| Hazır | `#2ED47A` | Dolu yeşil nokta, hafif yeşil parlama | "Dinlemeye hazır" |
| Dinliyor | `#4C9BFF` | Nabız atan mavi nokta + mavi halkalar | "Dinleniyor…" |
| İşleniyor | `#F2B23E` | Dönen halka / amber nokta | "İşleniyor…" |
| Hata | `#EF5B5B` | Kırmızı nokta | "Hata: mikrofon bulunamadı" |
| Devre dışı | `#3A4660` | Soluk nokta | `#6E7B96` yazı |

### Model durum rozetleri
| Rozet | Renk | Zemin |
| :--- | :--- | :--- |
| Aktif | `#2ED47A` | `rgba(46, 212, 122, 0.12)` |
| İndirildi | `#2ED47A` | `rgba(46, 212, 122, 0.10)` |
| İndirilmedi | `#8A97B0` | `rgba(138, 151, 176, 0.10)` |
| Yerel | `#A7B2C9` | `rgba(167, 178, 201, 0.10)` |

---

## 2. Tipografi

Yazı tipi: `Inter`, yoksa `Segoe UI` / `system-ui`. Tek dosya prototipte internet yok; sistem yazı tipi kullanılır.

| Öğe | Boyut | Ağırlık | Satır yüksekliği | Harf aralığı |
| :--- | :--- | :--- | :--- | :--- |
| Sayfa başlığı ("Dikte çalışma alanı") | 32 px | 600 | 1.2 | −0.5 px |
| Sayfa alt başlığı | 15 px | 400 | 1.5 | 0 |
| Marka adı ("VoxNote AI") | 23 px | 600 | 1.2 | −0.3 px |
| Marka sloganı | 12.5 px | 400 | 1.4 | 0 |
| Kart başlığı | 15 px | 600 | 1.3 | 0 |
| Metin çıktısı | 15.5 px | 400 | 1.8 | 0 |
| Model adı (kart) | 17 px | 600 | 1.3 | 0 |
| Model açıklaması | 12.5 px | 400 | 1.5 | 0 |
| Gövde / buton | 13.5 px | 500 | 1.2 | 0 |
| Küçük yazı (etiket, zaman, ipucu) | 11.5–12 px | 400–500 | 1.4 | 0 |
| Mikro üstü yazı (rozet) | 10.5 px | 500 | 1 | 0.2 px |

Kural: Başlık dışında hiçbir yerde 17 px üzerine çıkılmaz; panel içi hiyerarşi ağırlıkla kurulur.

---

## 3. Boşluk, köşe, gölge, parlama

- **Boşluk ölçeği:** 4 / 8 / 12 / 16 / 20 / 24 / 32 px.
- **Yerleşim:** Sol kenar çubuğu 264 px; içerik yan boşluğu 36 px; üst boşluk 40 px; kartlar arası 22 px.
- **Sağ panel genişliği:** 372 px (Dikte ve Modeller).
- **Köşe yuvarlaklığı:** kart 16 px · iç alan/model kartı 12 px · buton 12 px · küçük buton/rozet 8 px · hap (pill) 999 px · durum noktası 50%.
- **Kart gölgesi:** `0 18px 40px rgba(0, 0, 0, 0.35)` + 1 px `#1B2740` kenarlık.
- **Seçili kart parlaması:** `0 0 0 1px #4C6BFF, 0 0 28px rgba(76, 107, 255, 0.22)`.
- **Mikrofon parlaması (3 katman):**
  1. İç halka: `0 0 0 2px #8FB4FF`
  2. Orta ışıma: `0 0 42px rgba(76, 107, 255, 0.55)`
  3. Dış hale: 200 px çapında `radial-gradient` + iki adet nabız atan ince halka (`animation: 2.8s`).
- **Dinleme sırasında:** halkalar 1.6 s'de nabız atar, ışıma %40 artar, dalga formu hızlanır.
- **Buton geçişi:** 150 ms `ease`; hover'da zemin +%6 aydınlanır, 1 px yukarı kalkmaz (hareket sadece renkte).

---

## 4. Yerleşim iskeleti

```
┌───────────────┬─────────────────────────────────────────────┬───────────────┐
│ Kenar çubuğu  │ Başlık + alt başlık                         │ Sağ panel     │
│ 264 px        │                                             │ 372 px        │
│               │ Ana kart (metin çıktısı + butonlar)         │ Aktif model   │
│               │                                             │               │
│               │ Mikrofon sahnesi + dalga formu              │ Son etkinlik  │
│               │                                             │               │
├───────────────┴─────────────────────────────────────────────┴───────────────┤
│ Alt çubuk 56 px: Mikrofon · Dil · İşleme modu                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

- Pencere kontrol düğmeleri (küçült / büyüt / kapat) sağ üstte, 44 px yüksekliğinde şeffaf şeritte.
- Kenar çubuğu dikeyde: marka → menü → en altta "Yerel sistem hazır".
- Sayfalar arası geçişte yalnız orta alan değişir; kenar çubuğu ve alt çubuk sabittir.
- İçerik 1180 px'in altına inerse sağ panel alta kayar (tek sütun).

---

## 5. Bileşenler

### 5.1 Sol kenar çubuğu
- 264 px, zemin `#070B16`, sağ kenar 1 px `#121B2E`, iç boşluk 20/16 px.
- Marka: 52 px yuvarlak kutu, mavi-mor gradyan, içinde çizgi dalga ikonu; yanında 23 px marka adı ve 12.5 px slogan (`#6E7B96`).
- Menü öğesi: 48 px yükseklik, 12 px köşe, 14 px ikon, 13.5 px/500 yazı, öğeler arası 6 px.
- Aktif öğe: soldan sağa `rgba(76,107,255,.55) → rgba(76,107,255,.18)` gradyan, 1 px `rgba(118,148,255,.45)` kenar, hafif dış ışıma.
- Alt bilgi: 8 px yeşil nokta + 12.5 px `#A7B2C9` "Yerel sistem hazır".

| Durum | Görünüm |
| :--- | :--- |
| Normal | Şeffaf zemin, `#A7B2C9` ikon/yazı |
| Üzerine gelince | `rgba(255,255,255,.04)` zemin, yazı `#E9EEF9` |
| Seçili | Mavi gradyan zemin, beyaz yazı, soluk mavi ikon |
| Devre dışı | %40 saydamlık, tıklanamaz |
| Odak (klavye) | 2 px `#4C6BFF` dış halka |

### 5.2 Mikrofon düğmesi (sahne ortası)
- Sahne yüksekliği 330 px; düğme 156 px çapında, iç yüzey `radial-gradient(#20346B, #0D1730)`.
- İç ikon 42 px beyaz mikrofon; çevresinde 200 px çaplı yumuşak hale.
- Sağında ve solunda 28 çubuklu dalga formu; çubuk genişliği 3 px, aralık 4 px, yükseklik 8–64 px.
- Çubuk rengi: `linear-gradient(180deg, #7C9CFF, #2C4BFF)`; mikrofon yakınında uzun, uçlara doğru kısa.
- Düğmenin altında 24 px boşlukla durum satırı: 9 px nokta + 13.5 px yazı; altında 12 px boşlukla kısayol hapı ("Ctrl + Alt + Space").
- Kısayol hapı: `#0A1120` zemin, 1 px `#1B2740`, 8 px köşe, 11.5 px `#A7B2C9`.

| Durum | Düğme | Halkalar | Dalga | Durum yazısı |
| :--- | :--- | :--- | :--- | :--- |
| Hazır | Normal | Statik, hafif ışıma | Yavaş nefes (3 s) | Yeşil nokta + "Dinlemeye hazır" |
| Dinliyor | Işıma güçlü, ikon parlak | 1.6 s nabız, iki halka | Hızlı (0.45 s), genlik büyük | Mavi nabızlı nokta + "Dinleniyor…" |
| İşleniyor | Işıma sabit, ikon %70 | Tek yavaş halka | Donuk, düşük genlik | Amber nokta + "İşleniyor…" |
| Hata | Kırmızı kenar ışıması | Yok | Durur | Kırmızı nokta + hata metni |
| Devre dışı | %35 saydamlık | Yok | Durur | "Mikrofon kullanılamıyor" |

Üzerine gelince: dış hale %15 büyür, imleç `pointer`. Basılıyken: düğme %2 küçülür.

### 5.3 Metin kutusu (Metin çıktısı)
- Kart 16 px köşe, 20 px iç boşluk; başlık satırı 44 px.
- Başlık: 18 px belge ikonu + "Metin çıktısı" (15 px/600). Sağda dil seçici.
- Gövde alanı: `#0A1120` zemin, 1 px `#141E33`, 12 px köşe, 18 px iç boşluk, en az 300 px yükseklik.
- Metin 15.5 px/1.8, paragraflar arası 14 px; imleç 1 px `#8FB4FF`.
- Uzun metinde alan içi kaydırma; dış kart büyümez.
- Butonlar metin alanının altında, 14 px boşlukla, 4'lü sıra; aralarında 10 px.
- Dil seçici: 36 px yükseklik, `#0A1120` zemin, 1 px `#2A3A5C`, 10 px köşe; solda 16 px dünya ikonu, sağda küçük ok. Seçenekler: Türkçe, İngilizce, Almanca, Otomatik algıla.

| Durum | Görünüm |
| :--- | :--- |
| Normal | `#141E33` kenarlık |
| Üzerine gelince | `#2A3A5C` kenarlık |
| Odak | `#4C6BFF` kenarlık + `0 0 0 3px rgba(76,107,255,.15)` |
| Boş | Ortada `#6E7B96` "Konuşmaya başlamak için mikrofon düğmesine bas." |
| Hata | `#EF5B5B` kenarlık + altta 12 px hata metni |

### 5.4 Butonlar (eylem satırı)
Ortak: 40 px yükseklik, 12 px köşe, 12 px yatay iç boşluk, 14 px ikon + 6 px aralık + 13 px/500 yazı, 1 px `#2A3A5C`, zemin `#0C1526`.

| Buton | İkon | Vurgu davranışı |
| :--- | :--- | :--- |
| Kopyala | Üst üste iki kare | Tıklayınca 1.6 s "Kopyalandı" yazısı + yeşil ikon |
| Geri Al | Geri ok | Metin geçmişi yoksa devre dışı (%40) |
| Transkripsiyonu Yenile | Dairesel ok | Tıklayınca "İşleniyor…" durumuna geçer |
| Yapay Zeka ile Temizle | Parıltı | Mor-mavi gradyan kenarlık, `#9DB2FF` ikon; işlem sırasında ikon döner |

Durumlar tüm butonlarda ortak: normal / üzerine gelince (`#111C33` zemin) / basılı (%2 küçülme) / devre dışı (%40 saydam, `not-allowed`) / yükleniyor (solda 14 px dönen halka, yazı "İşleniyor…").

### 5.5 Dil seçici
Metin kutusu başlığında ve alt çubukta iki biçimi var. Başlıktaki hap biçimi 5.3'te; alt çubuktaki düz biçim 5.10'da. Ortak durumlar: normal, üzerine gelince (kenarlık `#2A3A5C`), odak (`#4C6BFF` halka), açık (ok 180° döner), devre dışı (%40).

### 5.6 Sağ panel — Aktif model kartı
- 372 px genişlik, 16 px köşe, 20 px iç boşluk, 1 px `#1B2740`.
- Başlık: 20 px çip ikonu + "Aktif model" (15 px/600).
- İç kart: 12 px köşe, `#0A1120`, 14 px iç boşluk.
  - 54 px model ikonu (mavi-mor gradyan) + model adı 17 px/600 + alt açıklama 11.5 px; sağda "Yerel" rozeti.
  - Bilgi satırları: ikon 14 px, etiket 12 px `#A7B2C9`, değer 12.5 px `#E9EEF9`, satır arası 10 px. Satırlar: **Dil**, **İşleme cihazı**. ("İşleme hızı" yok.)
  - 1 px `#141E33` ayırıcı.
  - "Model hazır" satırı: yeşil onay ikonu + sağda yeşil nokta + "Evet".
  - "Bellek kullanımı" satırı: 76 px ilerleme çubuğu (6 px yükseklik, 999 px köşe, `#4C6BFF` dolgu, `#1B2740` zemin) + "4.8 GB / 12 GB" (11.5 px).
- Kart durumları: normal, üzerine gelince (kenarlık `#24345A`), model yükleniyor (başlıkta küçük dönen halka, bellek çubuğu animasyonlu), hata (kırmızı kenar + "Model yüklenemedi" satırı).

### 5.7 Sağ panel — Son etkinlikler
- Başlık: saat ikonu + "Son etkinlikler" + sağda katla/aç oku.
- Dikey zaman çizgisi: nokta 7 px; çizgi 1 px `#1B2740`; satır arası 16 px.
- Üst satır: 11.5 px saat (`#A7B2C9`) + 12.5 px olay adı (`#E9EEF9`).
- Alt satır: 11.5 px ayrıntı (`#6E7B96`), örn. "(2 dk 34 sn) · 248 kelime".
- Olay renkleri: tamamlandı yeşil, model işlemleri mavi, hata kırmızı.
- Hover'da satır zemini `rgba(255,255,255,.03)`, 8 px köşe.

### 5.8 Model kartları (Modeller sayfası)
- Tam genişlik, 12 px köşe, `#0C1322` zemin, 1 px `#1B2740`, 14 px iç boşluk; kartlar arası 10 px.
- Sol: 52 px ikon kutusu (12 px köşe, `#111C33`, 1 px `#233150`; ses modelleri mikrofon, metin modelleri metin ikonu, gradyan mavi).
- Orta: model adı 17 px/600; açıklama 12.5 px `#A7B2C9`; altında iki küçük hap: kategori + "Yerel" (10.5 px, 999 px köşe).
- Sağ blok: boyut "~ 769 MB" (12.5 px) + altında "(FP16)" (11 px `#6E7B96`).
- Durum: 8 px nokta + 11.5 px yazı (Aktif / İndirildi / İndirilmedi).
- Eylem: 108 px buton ("Ayarlar" / "Aktifleştir" / "İndir") + model indirildiyse 34 px çöp kutusu + her zaman 34 px üç nokta.
- Seçili kart: `#4C6BFF` 1 px kenar + `0 0 26px rgba(76,107,255,.20)` gölge + hafif `rgba(76,107,255,.06)` zemin.
- Hover: kenarlık `#2A3A5C`, zemin `#0E1728`.
- "Aktif" butonu mavi dolgulu (`#3E5BFA` → `#5B4DFF`), diğerleri koyu zemin.
- Üst araç çubuğu: arama kutusu (42 px, arama ikonu, `#0A1120`) + "Model Ekle" birincil buton.
- Sekmeler: 36 px hap, aktif olan `#3E5BFA` dolgu; pasif `#0C1322` + 1 px `#1B2740`; sayı parantez içinde.

### 5.9 Model Detayları paneli
- Başlık: model ikonu + "Model Detayları" + sağda kapat (X).
- Büyük model başlığı: 54 px ikon + ad + tür.
- Bilgi satırları (etiket solda `#A7B2C9`, değer sağda): Kategori, Boyut, Dil Desteği, Cihaz Desteği, Dosya Türü.
- 1 px ayırıcı; "Model Durumu" + yeşil nokta ve durum.
- Dolgulu birincil "Aktifleştir" butonu (42 px, ikonlu).
- Alt sıra: kırmızı kenarlı "Sil" + "Diğer İşlemler" açılır butonu.
- Altında ayrı "Model Açıklaması" kartı: 15 px/1.6 açıklama + yeşil onay ikonlu 4 madde.

### 5.10 Alt çubuk
- 56 px yükseklik, `#070C18` zemin, üstte 1 px `#17203A`.
- Üç bölüm: Mikrofon (sol), Dil (orta), İşleme modu (sağa yakın). Aralarında 1 px `#17203A` dikey ayırıcı.
- Her bölüm: 16 px ikon + etiket 12.5 px `#A7B2C9` + değer 12.5 px `#E9EEF9` + 14 px aşağı ok; 10 px yatay boşluk.
- Hover: yazı beyaza döner; tıklayınca değer bir sonraki seçeneğe geçer. Açılır liste zemin `#0C1322`, 1 px `#1B2740`, 10 px köşe.
- Değerler: Mikrofon "Varsayılan Aygıt", Dil "Türkçe", İşleme modu "Yerel".

### 5.11 Dikte Geçmişi
- Başlık + alt başlık; altında tek büyük kart.
- Üstte arama kutusu ve "Tümü / Bugün / Bu hafta" filtre hapları.
- Kayıt satırı: 64 px yükseklik, 12 px köşe, 1 px `#141E33`, 14 px iç boşluk.
  - Sol: 34 px takvim/saat ikonu.
  - Orta: tarih-saat (13 px/600) + süre ve kelime sayısı (11.5 px `#6E7B96`).
  - Alt satır: metin önizlemesi tek satır, taşan kısım üç nokta (12.5 px `#A7B2C9`).
  - Sağ: "Aç", "Kopyala", "Sil" butonları; "Sil" kırmızı kenarlı.
- Hover: zemin `#0E1728`; silinen satır 200 ms solarak kalkar.

### 5.12 Ayarlar
- En fazla 900 px genişlikte üç kart: **Kısayol Tuşu**, **Dil ve Mikrofon**, **Kaydet** alanı.
- Ayar satırı: 64 px yükseklik, 16/0 px iç boşluk, altta 1 px `#141E33`; solda başlık 13.5 px + açıklama 11.5 px `#6E7B96`; sağda kontrol.
- Kısayol hapı: 40 px, `#0A1120`, 1 px `#2A3A5C`; tuş yakalama sırasında `#4C6BFF` kenar + "Bir tuşa basın…" yazısı.
- Mikrofon seviye çubuğu: 120 px × 6 px, yeşil dolgu, mikrofon testinde hareket eder.
- "Kaydet" birincil buton, "Varsayılana dön" ikincil buton.

---

## 6. Ortak durum kuralları

| Durum | Kural |
| :--- | :--- |
| Üzerine gelince | Yalnız zemin/kenarlık değişir; boyut değişmez. 150 ms geçiş. |
| Seçili | 1 px vurgu kenarı + düşük yoğunluklu mavi zemin; yazı beyaz. |
| Devre dışı | %40 saydamlık, `cursor: not-allowed`, hover efekti yok. |
| Odak | 2 px `#4C6BFF` dış halka, 2 px ofset; klavye ile gezilebilir. |
| Hata | `#EF5B5B` kenar/ikon; hata metni 11.5 px, aynı satırda ikonla. |
| Yükleniyor | 14 px dönen halka + kısa fiil ("İşleniyor…", "İndiriliyor…"). |

## 7. Sahte veri (prototipte kullanılan)

- **Ses modelleri:** Whisper Large (~1.5 GB, FP16, Aktif), Whisper Small (~769 MB, FP16, İndirildi), Whisper Base (~494 MB, FP16, İndirilmedi), Whisper Medium (~3.1 GB, FP16, İndirildi).
- **Metin modelleri:** Qwen3 8B (~4.7 GB, Q4_K_M, İndirildi), Llama 3.2 3B (~2.0 GB, Q4_K_M, İndirildi), Gemma 3 4B (~2.5 GB, Q4_K_M, İndirilmedi).
- **Bellek:** 4.8 GB / 12 GB.
- **Etkinlikler:** 10:42 Dikte tamamlandı (2 dk 34 sn · 248 kelime), 10:38 Model yüklendi (Whisper Large), 10:25 Dikte tamamlandı (1 dk 12 sn · 132 kelime), 10:18 Model değiştirildi (Whisper Large), 10:12 Dikte tamamlandı (3 dk 07 sn · 401 kelime).
- **Geçmiş:** 6 kayıt, 24 Ekim 2026 ve öncesi tarihler.

Tüm rakamlar örnektir; gerçek değerler uygulamada ölçülür.
