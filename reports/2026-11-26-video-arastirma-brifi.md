# Dikte Tanıtım Videoları — Araştırma ve Prodüksiyon Brifi (4 Video)

**Tarih:** 2026-11-26  
**Hazırlayan:** `video-arastirma` (alt ekip: `arastirma-trend` + `arastirma-senaryo`)  
**Hedef Ekip:** `@video-uretim` (HyperFrames prodüksiyon lideri)  
**Kapsam:** 2 Yatay (`1920x1080`, 16:9, 50.0 sn) + 2 Dikey/Shorts (`1080x1920`, 9:16, 30.0 sn), Türkçe ve İngilizce toplam 4 tanıtım videosu.

---

## 1. 2025–2026 Trend Araştırması Özeti ve Prodüksiyon Kuralları

Masaüstü üretkenlik, açık kaynak yazılım ve sesli dikte (Wispr Flow, Superwhisper, MacWhisper, Linear/Raycast tarzı) tanıtım videoları üzerine yapılan 2025–2026 araştırmasının doğrudan prodüksiyona giren kararları:

1. **İlk 3 Saniye Kancası (Frame 0 Kuralı):**
   - Yavaş fade-in, boş arka plan veya selamlama ("Merhaba") **yasaktır**. İzleyicilerin %30–50'si ilk 1.5–3.0 saniyede videoyu terk eder.
   - **Frame 0** doğrudan yüksek kontrastlı kısa başlık + aksiyonun ortasıyla (`Sağ Ctrl` / `Right Ctrl` basışı + canlanan 48 bar mikrofon dalgası) açılır.
   - **En yüksek dönüşüm veren 4 sesli dikte kancası:** (a) Klavye sürtünmesi vs tek tuşla anında akan metin, (b) Dolgu kelimeli ham konuşma → temiz metin dönüşümü, (c) `%100 yerel / internetsiz / aboneliksiz` gizlilik zıtlığı, (d) İmleç → hotkey → hedef uygulamaya anında yapışma.
2. **Görsel Tempo ve 3-Second Rule:**
   - **16:9 Yatay (50.0 sn):** 7 ana sahne; sahne içi her 2–3 saniyede mikro hareket (hafif 3D tilt, zoom-in, kart sırası, dalga tepkisi, spotlight). Asıl "aha!" anları (otomatik yapıştırma, AI temizleme, dairesel tema geçişi) `1x` net hızda gösterilir.
   - **9:16 Shorts (30.0 sn):** En yüksek tutma penceresi 21–35 sn (hedef APV %65–85+). Her `1.5–3.0 sn`'de bir görsel katman/ölçek değişimi uygulanır; ölü boşluk bırakılmaz.
3. **Title-Safe ve Metin Yoğunluğu:**
   - **16:9 (`1920x1080`):** Merkezdeki **%80 title-safe** alanı (`x: 192..1728`, `y: 108..972`).
   - **9:16 Shorts (`1080x1920`):** Platform arayüzü çakışmasını önlemek için **üstten 220 px, alttan 440 px, sağdan 170 px (beğen/yorum/paylaş sütunu), soldan 60 px** güvenli kenar boşluğu bırakılır (güvenli alan: `x: 60..910`, `y: 220..1480`).
   - **Okuma Hızı:** Ekranda 2.5–3.5 kelime/sn sınırı. Kısa etiketler en az `0.8 sn`, başlıklar kelime başına `~0.3 sn` (min `1.2 sn`) ekranda sabit (**settled**) kalır. Kural: *Hızlı gir (`0.3–0.5 sn`), bekle, temiz çık.*
4. **Ses Tasarımı, Ritim ve Sessiz İzleme (Muted Autoplay):**
   - **BPM:** `120–128 BPM` (minimalist modern elektronik / Linear-Raycast ritmi).
   - **Seviyeler (HyperFrames):** Arka plan müziği `data-volume="0.32–0.38"` (asla `>0.50` değil); SFX `0.55–0.85` ve tetiklediği görsel animasyondan `0.0–0.1 sn` önce hizalanır.
   - **Beat-Grid:** 1–3 ana sahne geçişi güçlü vuruşlara (`±0.15 sn`), art arda gelen rozet/uygulama kartları `±0.10 sn` içinde ritme oturtulur.
   - **Sessiz İzleme:** Web hero ve mobil feed izlemelerinin ~%85'i sessiz olduğundan hikâye **%100 görsel + ekrandaki metinle** eksiksiz anlaşılır.
5. **Kapanış CTA ve Shorts Seamless Loop:**
   - **16:9:** Son 5 sn'de `icon.png` + `mete2012seker-lgtm.github.io/dikte` + `GitHub • Ücretsiz (MIT)` rozetleri net sabitlenir.
   - **9:16 Shorts:** Klasik "Abone ol" yerine son `0.5 sn` görsel/ses akışı ilk kareye bağlanır (seamless loop) ve kısa görsel etiketle sabitlenmiş yorum / profil linkine yönlendirilir (`Link sabitlenmiş yorumda` / `Link in pinned comment`).
6. **TR vs EN Mesaj Farkı:**
   - **Türkçe (TR):** Pratiklik, zaman tasarrufu, ücretsiz/internetsiz çalışma, aboneliksiz kullanım ve Türkçe karakter (`ı, İ, ğ, ş, ç, ö, ü`) doğruluğu öne çıkar.
   - **İngilizce (EN):** Abonelik yorgunluğu ("No Subscription"), veri egemenliği ("Zero Cloud • 100% Local") ve MIT açık kaynak şeffaflığı en yüksek dönüşümü sağlar.

---

## 2. Doğrulanmış Ürün Özellikleri ve Gerçek Varlık Envanteri

### 2.1. Kesin Gerçek Özellikler (Uydurma Özellik Yasak)
- **Dikte:** Ücretsiz, açık kaynak (**MIT**), Windows 10 / 11 masaüstü uygulaması.
- **Ses Tanıma:** %100 yerel ve çevrimdışı `faster-whisper` motoru (NVIDIA CUDA GPU veya CPU). Ses kaydı buluta gönderilmez, çeviriden sonra silinir.
- **Kısayol ve Modlar:** Basılı Tut (**Push-to-Talk**) veya Bas-Bırak (**Toggle**) modu; özelleştirilebilir 1–3 tuşlu global kısayol (varsayılan `Sağ Ctrl` / `Right Ctrl`, ör. `Ctrl+Shift+D`).
- **Mikrofon ve Tepsi Göstergesi:** Uygulama içinden mikrofon seçimi + pencere sistem tepsisinde gizliyken ekranda beliren küçük yüzen **"Dinliyor / Yazıyor"** (**"Listening / Writing"**) durum göstergesi.
- **Evrensel Otomatik Yapıştırma:** Aktif penceredeki imlecin olduğu yere (WhatsApp Web, Microsoft Word, Notlar, ChatGPT vb.) anında yapıştırma.
- **İsteğe Bağlı AI Metin Temizleme ve Çeviri:** TR / EN / DE çıktı dili; yerel GGUF modelleri (`llama.cpp`) veya OpenRouter desteği.
- **Arayüz ve Tema:** Koyu / Açık tema (400 ms dairesel geçiş animasyonu), Sade **Dikte.AI** ve **Magic UI** görünüm seçenekleri.

### 2.2. Doğrulanmış Disk Varlıkları (`docs/assets/` ve `design/`)
> **KRİTİK NOT (`@video-uretim` için):** Diskte `ss-dikte-dark.png`, `ss-dikte-light.png`, `ss-modeller.png`, `ss-ayarlar.png` isimleri **yoktur**; mevcut gerçek ekran görüntüleri `ekran-*.png` ön ekiyle kayıtlıdır. Tüm dosyalar `composition/assets/` içine kopyalanıp göreli yolla (`./assets/...`) kullanılmalıdır (harici URL yasak).

| Brif Rolü | Doğrulanmış Gerçek Dosya Yolu | Kullanım Notu |
| :--- | :--- | :--- |
| Koyu Tema Ana Ekran | `docs/assets/ekran-dikte-koyu.png` | Ana ürün vitrini, koyu tema ve tema geçişi başlangıcı |
| Açık Tema Ana Ekran | `docs/assets/ekran-dikte-acik.png` | 400 ms dairesel clip-path tema geçişi hedefi |
| Modeller Ekranı | `docs/assets/ekran-modeller.png` | Ses (Whisper) + Metin (GGUF / OpenRouter) modelleri sahnesi |
| Uygulama Logosu | `docs/assets/icon.png` | Açılış aksanı ve kapanış CTA logosu |
| 48 Bar Mikrofon Dalgası | `design/mikrofon_morph_animasyonu.html` & `video/src/components/MicMorphWave.tsx` | 48 barlık (`2x24`) ses dalgası + halo halkaları + idle→dinliyor morph küresi |
| Ayarlar / Tepsi Göstergesi | *(Diskte `ss-ayarlar.png` yok)* | Temiz HTML/CSS ürün UI maketi olarak üret (Basılı Tut/Bas-Bırak anahtarı, kısayol kapsülü, mikrofon seçici, yüzen `Dinliyor... / Yazıyor...` kapsülü) |

### 2.3. Marka Renk Paleti ve Tipografi
- **Koyu Tema:** Zemin `#0B0F1A`, yüzey `#121829`, kenarlık `rgba(255,255,255,0.10)`, ana metin `#F2F5FC`, ikincil metin `#94A3B8`, vurgu `#4F6DFF`.
- **Açık Tema:** Zemin `#F7F9FD`, yüzey `#FFFFFF`, ana metin `#101828`, vurgu `#3D5BF5`.
- **Durum Renkleri:** Kayıt/dinleme parlaması `#4F6DFF` → `#6366F1`, başarı/yapıştırma onayı `#22C55E` / `#16A34A`.
- **Font:** Yerel `Inter` (`woff2`, Türkçe karakter seti `latin-ext` tam destekli: `ı, İ, ğ, ş, ç, ö, ü`).
- **Çıktı Hedef Dosya Adları (öneri):**
  - Video 1 (16:9 TR): `dikte-tanitim-tr.mp4` + `dikte-tanitim-poster-tr.png` (frame 0 bake)
  - Video 2 (16:9 EN): `dikte-tanitim-en.mp4` + `dikte-tanitim-poster-en.png` (frame 0 bake)
  - Video 3 (9:16 TR): `dikte-shorts-tr.mp4`
  - Video 4 (9:16 EN): `dikte-shorts-en.mp4`

---

## 3. Video 1 — Yatay Türkçe (`1920x1080`, 16:9, 50.0 sn, 30 fps)
**Hedef:** YouTube ana tanıtım + Türkçe web sitesi hero oynatıcı.  
**Ton:** Modern, net, güven verici, yüksek tempolu (`polished` + Linear/Raycast ritmi).  
**Müzik:** 124 BPM minimalist elektronik, `data-volume="0.34"`, 45.0s sonrası yumuşak fade-out.

| Sahne | Süre | Kesin Ekranda Başlık & Alt Metin (TR) | Görsel Yönlendirme & Gerçek Varlıklar | Ses / SFX & Ritim |
| :--- | :--- | :--- | :--- | :--- |
| **S1 — Kanca (Hook)** | `0.0s - 4.0s` | **Başlık:** `Klavyeyle yazmayı bırak.`<br>**Alt metin:** `Konuş. Windows'ta anında yazıya dönüşsün.` | **Frame 0 hazır!** `#0B0F1A` koyu zemin, merkezde 48 bar mikrofon dalgası + morflayan mikrofon küresi (`MicMorphWave`). `0.6s`'de `Sağ Ctrl` tuş kapsülü basılır, dalgalar canlanır. | `0.55s`: mekanik tuş tıkı (`click_002`, 0.70) + `0.70s`: yumuşak sub-bass açılış (`impactSoft_medium_001`, 0.75). |
| **S2 — %100 Yerel & Gizli** | `4.0s - 12.0s` | **Başlık:** `%100 Yerel. İnternetsiz. Ücretsiz.`<br>**Alt metin:** `faster-whisper (GPU veya CPU) ile sesin bilgisayarından çıkmaz.` | Solda `docs/assets/ekran-dikte-koyu.png` hafif 3D perspektifle girer (`0.45s`). Sağda 3 rozet beat-grid ile iner: `Bulut yok`, `Kayıt sonrası silinir`, `Açık kaynak (MIT)`. | `4.0s` ana vuruş geçişi; `5.2s / 6.2s / 7.2s`: 3 kart düşüşü (`drop_001–003`, 0.60). |
| **S3 — Kısayol, Modlar & Mini Gösterge** | `12.0s - 21.0s` | **Başlık:** `Basılı Tut ya da Bas-Bırak.`<br>**Alt metin:** `Kısayolunu ve mikrofonunu seç; tepside gizliyken bile takip et.` | Temiz UI bileşeni: `Sağ Ctrl` → `Ctrl+Shift+D` kısayol değişimi, `Basılı Tut / Bas-Bırak (Toggle)` anahtarı ve mikrofon seçici. `16.5s`'de pencere küçülür, altta küçük yüzen `Dinliyor... → Yazıyor...` kapsülü belirir. | `13.5s` & `15.0s`: anahtar geçiş sesi (`switch_001`, 0.65); `16.5s`: yumuşak kayıt onay bip'i (0.60). |
| **S4 — Her Uygulamaya Yapıştır** | `21.0s - 31.0s` | **Başlık:** `Her Uygulamaya Anında Yapıştır.`<br>**Alt metin:** `WhatsApp Web, Word, Notlar veya ChatGPT — imlecin olduğu yere düşer.` | 2x2 temiz uygulama penceresi grid'i: **WhatsApp Web**, **Word**, **Notlar**, **ChatGPT**. Her birinde imleç yanıp söner ve Türkçe karakterli (`ı, İ, ğ, ş, ç, ö, ü`) cümleler sırayla anında yapışır. | `22.2s / 24.4s / 26.6s / 28.8s`: kısa yapıştırma/onay tınıları (`keypress` + `select_008`, 0.65). |
| **S5 — AI Temizle & Çevir** | `31.0s - 40.0s` | **Başlık:** `İsteğe Bağlı AI Temizle ve Çevir.`<br>**Alt metin:** `TR / EN / DE • Yerel GGUF (llama.cpp) veya OpenRouter.` | Üstte `docs/assets/ekran-modeller.png` kartı belirir. Altta canlı dönüşüm: *"Ee, yani yarın toplantıyı saat üçte yapalım şey..."* → *"Yarın toplantıyı saat 15.00'te yapalım."* → `[EN] Let's hold tomorrow's meeting at 3:00 PM.` / `[DE] ...` | `31.0s`: airy whoosh; `34.5s`: dolgu silme tıkı (`drop_002`, 0.65); `37.0s`: çeviri onay çanı (0.60). |
| **S6 — Tema & Arayüz** | `40.0s - 45.0s` | **Başlık:** `Sade Dikte.AI ve Magic UI.`<br>**Alt metin:** `Tek tıkla Koyu ve Açık tema.` | `docs/assets/ekran-dikte-koyu.png` tam merkezde görünür; `42.0s`'de sağ üstteki tema düğmesinden **400 ms dairesel clip-path** açılımıyla `docs/assets/ekran-dikte-acik.png` yüzeyine dönüşür. | `41.95s`: pürüzsüz tema geçiş whoosh/switch (`ui/switch1`, 0.70). |
| **S7 — Kapanış CTA** | `45.0s - 50.0s` | **Başlık:** `Dikte — Ücretsiz ve Açık Kaynak`<br>**Alt metin:** `mete2012seker-lgtm.github.io/dikte  •  GitHub'dan Ücretsiz İndir` | `#0B0F1A` zemin, merkezde parlayan `docs/assets/icon.png` + `Dikte` logosu + mavi `Ücretsiz İndir` hap butonu + altında `Windows 10 / 11 • MIT Lisansı • Abonelik Yok` şeridi. | `45.0s`: kapanış çanı (`impactBell_heavy_000`, 0.70) + müzik `47.5s–50.0s` yumuşak fade-out. |

---

## 4. Video 2 — Yatay İngilizce (`1920x1080`, 16:9, 50.0 sn, 30 fps)
**Hedef:** Global YouTube tanıtım + İngilizce web sitesi hero oynatıcı.  
**Ton:** Keskin, abonelik karşıtı, gizlilik odaklı (`Zero Cloud • Own Your Tool`).  
**Müzik:** Video 1 ile aynı 124 BPM müzik & zamanlama ızgarası (çift dilde ortak prodüksiyon kolaylığı).

| Sahne | Süre | Kesin Ekranda Başlık & Alt Metin (EN) | Görsel Yönlendirme & Gerçek Varlıklar | Ses / SFX & Ritim |
| :--- | :--- | :--- | :--- | :--- |
| **S1 — Hook** | `0.0s - 4.0s` | **Başlık:** `Stop typing everything by hand.`<br>**Alt metin:** `Speak naturally. Instant text anywhere on Windows.` | **Frame 0 ready!** `#0B0F1A` dark canvas, centered 48-bar wave + morphing mic orb (`MicMorphWave`). At `0.6s`, `Right Ctrl` keycap presses down and waveform springs alive. | `0.55s`: mechanical click (`click_002`, 0.70) + `0.70s`: soft sub-bass hit (`impactSoft_medium_001`, 0.75). |
| **S2 — 100% Local & Private** | `4.0s - 12.0s` | **Başlık:** `100% Local. Offline. Free Forever.`<br>**Alt metin:** `Powered by faster-whisper (NVIDIA GPU or CPU). Zero cloud.` | Left: `docs/assets/ekran-dikte-koyu.png` enters with subtle 3D tilt. Right: 3 badges drop on beat: `No Subscription`, `Audio Deleted Locally`, `MIT Open Source`. | `4.0s` beat cut; `5.2s / 6.2s / 7.2s`: 3 badge drops (`drop_001–003`, 0.60). |
| **S3 — Modes, Shortcuts & Overlay** | `12.0s - 21.0s` | **Başlık:** `Push-to-Talk or Toggle Mode.`<br>**Alt metin:** `Pick your mic, bind any shortcut, track via the tray "Listening / Writing" pill.` | Clean UI mockup: `Right Ctrl` → `Ctrl+Shift+D` binding, Hold/Toggle switch, microphone picker. At `16.5s`, window minimizes to tray and compact floating `Listening… → Writing…` pill appears. | `13.5s` & `15.0s`: toggle clicks (`switch_001`, 0.65); `16.5s`: soft chime (0.60). |
| **S4 — Auto-Paste Everywhere** | `21.0s - 31.0s` | **Başlık:** `Auto-Paste Into Any Window.`<br>**Alt metin:** `WhatsApp Web, Word, Notes, or ChatGPT — lands right at your cursor.` | 2x2 app window grid (**WhatsApp Web**, **Word**, **Notes**, **ChatGPT**). Cursor blinks and dictated text pastes cleanly into each window in sequence. | `22.2s / 24.4s / 26.6s / 28.8s`: crisp paste pops (`keypress` + `select_008`, 0.65). |
| **S5 — Optional AI Cleanup & Translate** | `31.0s - 40.0s` | **Başlık:** `AI Cleanup & Translate (TR / EN / DE).`<br>**Alt metin:** `Local GGUF via llama.cpp or OpenRouter — your choice.` | Top: `docs/assets/ekran-modeller.png` slides in. Bottom: live before/after transformation stripping *"um, so basically..."* into crisp English, Turkish, or German text. | `31.0s`: whoosh; `34.5s`: cleanup snap (`drop_002`, 0.65); `37.0s`: translate chime (0.60). |
| **S6 — Themes & UI Modes** | `40.0s - 45.0s` | **Başlık:** `Minimal Dikte.AI & Magic UI.`<br>**Alt metin:** `Switch Dark and Light themes in one click.` | `docs/assets/ekran-dikte-koyu.png` centered; at `42.0s`, a **400 ms circular clip-path** reveal transforms it into `docs/assets/ekran-dikte-acik.png`. | `41.95s`: smooth switch/whoosh (`ui/switch1`, 0.70). |
| **S7 — Outro CTA** | `45.0s - 50.0s` | **Başlık:** `Dikte — Free & Open Source (MIT)`<br>**Alt metin:** `mete2012seker-lgtm.github.io/dikte  •  Download Free on GitHub` | `#0B0F1A` canvas, glowing `docs/assets/icon.png` + `Dikte` title + crisp `Download Free` pill + `Windows 10 / 11 • Zero Cloud • MIT License` bar. | `45.0s`: bell hit (`impactBell_heavy_000`, 0.70) + music fade-out `47.5s–50.0s`. |

---

## 5. Video 3 — Dikey / Shorts Türkçe (`1080x1920`, 9:16, 30.0 sn, 30 fps)
**Hedef:** YouTube Shorts (TR kitle, mobil dikey izleme).  
**Safe Zone:** Tüm metin ve önemli UI `x: 60..910`, `y: 220..1480` içinde (üst 220 px, alt 440 px, sağ 170 px boş).  
**Müzik:** 128 BPM yüksek enerjili minimalist elektronik, `data-volume="0.36"`, **seamless loop** (30.0s sonu 0.0s başına kesintisiz bağlanır).

| Sahne | Süre | Kesin Ekranda Başlık & Alt Metin (TR) | Görsel Yönlendirme & Gerçek Varlıklar | Ses / SFX & Ritim |
| :--- | :--- | :--- | :--- | :--- |
| **S1 — Kanca (Hook)** | `0.0s - 3.0s` | **Başlık:** `Hâlâ klavyeyle mi yazıyorsun?`<br>**Alt metin:** `Sağ Ctrl'ye bas, konuş, yapışsın.` | **Frame 0:** Üstte dev yüksek kontrastlı başlık; merkezde 48 bar dalga + morflayan mikrofon (`MicMorphWave`) + basılan `Sağ Ctrl` kapsülü. | `0.0s` ritimle açılış + `0.4s` tuş tıkı (`click_002`, 0.75) + `impactSoft_medium_001` (0.80). |
| **S2 — %100 Yerel & Ücretsiz** | `3.0s - 8.5s` | **Başlık:** `%100 Yerel ve İnternetsiz`<br>**Alt metin:** `faster-whisper (GPU/CPU) • Abonelik yok` | `docs/assets/ekran-dikte-koyu.png` dikey kartta yakınlaşır (`scale 1.0 → 1.08`). `5.5s`'de `Sesin PC'den çıkmaz` + `Ücretsiz • MIT` hap rozetleri patlar (3-Second Rule). | `3.0s` beat cut + `5.45s` çift rozet sesi (`drop_001`, `drop_002`, 0.65). |
| **S3 — Modlar & Mini Gösterge** | `8.5s - 14.0s` | **Başlık:** `Basılı Tut veya Bas-Bırak`<br>**Alt metin:** `Mikrofon seç + "Dinliyor / Yazıyor" göstergesi` | Üstte `Basılı Tut ⇄ Bas-Bırak` anahtarı + kısayol (`Sağ Ctrl`). `11.2s`'de masaüstü kenarından yüzen mini `Dinliyor... → Yazıyor...` kapsülü öne çıkar. | `9.2s` `switch_001` (0.65) + `11.15s` kısa bildirim tınısı (0.65). |
| **S4 — Her Yere Yapıştır** | `14.0s - 20.0s` | **Başlık:** `Her Uygulamaya Yapıştır`<br>**Alt metin:** `WhatsApp, Word, Notlar, ChatGPT` | Dikey akan 4 kart (her biri `1.4 sn` ritmik vurgu): **WhatsApp Web** → **Word** → **Notlar** → **ChatGPT**; her karta Türkçe cümle anında düşer. | Her kartta ritme kilitli `card-slide` + `keypress` pop (0.70). |
| **S5 — AI Temizle & Tema** | `20.0s - 25.5s` | **Başlık:** `AI Temizle & Çevir`<br>**Alt metin:** `TR / EN / DE • Yerel GGUF • Koyu/Açık Tema` | `20.0s–22.8s`: `docs/assets/ekran-modeller.png` + dolgu kelimelerinin temizlenmesi. `22.8s–25.5s`: `ekran-dikte-koyu.png` → 400 ms dairesel geçişle `ekran-dikte-acik.png`. | `20.0s` `drop_002` + `22.75s` `ui/switch1` (0.75). |
| **S6 — CTA & Loop** | `25.5s - 30.0s` | **Başlık:** `Dikte'yi Ücretsiz İndir`<br>**Alt metin:** `mete2012seker-lgtm.github.io/dikte`<br>**Alt şerit:** `GitHub MIT • Link sabitlenmiş yorumda` | Merkezde `docs/assets/icon.png` + yüksek kontrastlı URL kapsülü. `29.4s`'de mikrofon dalgası S1 pozisyonuna geri morflayarak **kesintisiz loop** yapar. | `25.5s` onay çanı (`impactBell_heavy_000`, 0.70); `29.5s` müzik kesilmeden S1 vuruşuna bağlanır. |

---

## 6. Video 4 — Dikey / Shorts İngilizce (`1080x1920`, 9:16, 30.0 sn, 30 fps)
**Hedef:** Global YouTube Shorts (EN kitle, mobil dikey izleme).  
**Safe Zone:** Video 3 ile birebir (`x: 60..910`, `y: 220..1480`).  
**Müzik:** 128 BPM minimalist elektronik, `data-volume="0.36"`, **seamless loop**.

| Sahne | Süre | Kesin Ekranda Başlık & Alt Metin (EN) | Görsel Yönlendirme & Gerçek Varlıklar | Ses / SFX & Ritim |
| :--- | :--- | :--- | :--- | :--- |
| **S1 — Hook** | `0.0s - 3.0s` | **Başlık:** `Still typing everything manually?`<br>**Alt metin:** `Hold Right Ctrl. Speak. Done.` | **Frame 0:** Bold high-contrast hook at top; centered 48-bar wave + morphing mic orb (`MicMorphWave`) + `Right Ctrl` press animation. | `0.0s` beat start + `0.4s` `click_002` (0.75) + `impactSoft_medium_001` (0.80). |
| **S2 — 100% Local & Free** | `3.0s - 8.5s` | **Başlık:** `100% Local & Offline`<br>**Alt metin:** `faster-whisper (GPU/CPU) • No subscription` | `docs/assets/ekran-dikte-koyu.png` vertical zoom card (`1.0 → 1.08`). At `5.5s`, `Zero Cloud` + `Free MIT Open Source` pills pop in. | `3.0s` beat cut + `5.45s` `drop_001`, `drop_002` (0.65). |
| **S3 — Modes & Mini Pill** | `8.5s - 14.0s` | **Başlık:** `Hold or Toggle Mode`<br>**Alt metin:** `Mic picker + "Listening / Writing" pill` | `Hold ⇄ Toggle` switch + custom hotkey pill. At `11.2s`, tray-hidden floating `Listening… → Writing…` indicator zooms cleanly into focus. | `9.2s` `switch_001` (0.65) + `11.15s` soft chime (0.65). |
| **S4 — Auto-Paste Everywhere** | `14.0s - 20.0s` | **Başlık:** `Auto-Paste Into Any App`<br>**Alt metin:** `WhatsApp Web, Word, Notes, ChatGPT` | 4 stacked app cards cycling every `1.4s` on beat: **WhatsApp Web** → **Word** → **Notes** → **ChatGPT** with instant pasted text. | Beat-synced `card-slide` + crisp `keypress` pops (0.70). |
| **S5 — AI Cleanup & Themes** | `20.0s - 25.5s` | **Başlık:** `AI Cleanup & Translate`<br>**Alt metin:** `TR / EN / DE • Local GGUF • Dark / Light` | `20.0s–22.8s`: `docs/assets/ekran-modeller.png` + filler removal. `22.8s–25.5s`: `ekran-dikte-koyu.png` → 400 ms circular reveal to `ekran-dikte-acik.png`. | `20.0s` `drop_002` + `22.75s` `ui/switch1` (0.75). |
| **S6 — CTA & Loop** | `25.5s - 30.0s` | **Başlık:** `Get Dikte Free`<br>**Alt metin:** `mete2012seker-lgtm.github.io/dikte`<br>**Alt şerit:** `GitHub MIT • Link in pinned comment` | Centered `docs/assets/icon.png` + bold URL pill. At `29.4s`, mic wave morphs back to S1 frame for a **seamless loop**. | `25.5s` `impactBell_heavy_000` (0.70); `29.5s` loops seamlessly into `0.0s`. |

---

## 7. HyperFrames Prodüksiyon ve Kalite Kontrol Listesi (`@video-uretim` İçin)

1. **Çözünürlük ve FPS:** Yatay `1920x1080 @ 30fps`, Dikey `1080x1920 @ 30fps`.
2. **Türkçe Karakter Doğrulaması:** `ı, İ, ğ, ş, ç, ö, ü` karakterleri yerel `Inter` (`latin-ext`) fontu ile eksiksiz render edilmeli; fallback font kayması olmamalı.
3. **Poster Frame (Yatay Videolar):** `dikte-tanitim-tr.mp4` ve `dikte-tanitim-en.mp4` için en vurucu kare (mikrofon dalgası + başlık veya ürün ekranı) seçilip `dikte-tanitim-poster-tr.png` / `dikte-tanitim-poster-en.png` olarak çıkarılmalı ve mümkünse Frame 0'a gömülmeli.
4. **HyperFrames Gate:** Render öncesi her kompozisyonda `npx hyperframes check` sıfır hata ile geçmeli; görsel taşma, kesilen başlık veya eksik asset olmamalı.
5. **Shorts Safe Zone Kontrolü:** Video 3 ve Video 4'te `1080x1920` çıktının üst 220 px, alt 440 px ve sağ 170 px şeridinde kritik metin/URL kalmadığı kare incelemesiyle doğrulanmalı.
6. **Ses Denge Kontrolü:** Müzik `0.32–0.38`, SFX `0.55–0.85`, kırpılma (clipping) sıfır. Video tamamen sessize alındığında da (muted autoplay) tüm hikâye ve CTA %100 okunabilir olmalı.
