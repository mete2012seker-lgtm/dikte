# olabilir.md — Dikte v1.3 / v1.4 / v1.5 istek ve davranış spesifikasyonu

Bu dosya, 2026-11-01 oturumunda konuşulan ve eklenmesi istenen her şeyi tek yerde toplar.
Amaç: yeni sohbette hiçbir şey sorulmadan "ne nerede olacak, nasıl görünecek, nasıl çalışacak" sorularının cevabını bulmak.
Bu bir kod dosyası değil, uygulama talimatıdır.

## 0. Mevcut durum ve varsayımlar

- v1.2 çalışıyor: Dikte, Geçmiş, Modeller (6 ses modeli), Ayarlar, Yenile. Kullanıcı elle testlerini yaptı.
- v1.3, v1.4 ve v1.5 henüz kodlanmadı.
- Cihaz: Windows, RTX 5060, 8 GB VRAM.
- Yazıya çevirme yerel faster-whisper ile yapılır.
- Metin temizleme/çeviri iki sağlayıcıyla yapılabilir: uygulama içi GGUF (llama.cpp) ve OpenRouter.
- Arayüz pywebview + mevcut HTML/CSS/JS. Next.js'e geçilmeyecek; Magic UI fikirleri CSS/JS olarak uyarlanacak.
- Pencere kapanınca uygulama çıkar; sistem tepsisi yok.

## 1. Genel kararlar

| Konu | Karar |
| :--- | :--- |
| Çıktı dilleri | Türkçe, İngilizce, Almanca |
| Varsayılan çıktı dili | Türkçe |
| Dil algılama | Whisper sesi yazar ve dilini tahmin eder; çeviri kararını metin modeli tek çağrıda verir |
| Aynı dil kuralı | Hedef dil = konuşulan dil ise çeviri yok, yalnız temizlik var |
| Kısa metin | 3 kelimeden kısa metinde otomatik çeviri yapılmaz; metin ham kalır |
| Temizleme | Manuel buton + "Otomatik çevir" kutusu |
| Metin sağlayıcıları | Uygulama içi GGUF ve OpenRouter; Ayarlar'dan seçilir |
| OpenRouter modeli | Yalnız ucuz/küçük modeller listelenir; tüm katalog gösterilmez |
| API anahtarı | Ayarlar'da girilir, Windows DPAPI ile şifrelenir, loglara yazılmaz |
| Bellek | Ses modeli ile metin modeli aynı anda bellekte tutulmaz; takas edilir |
| RAM/VRAM | Metin modeli VRAM'e sığmazsa CPU/RAM'de çalışır |
| İndirme | Tek seferde tek model; duraklat/devam/iptal vardır |
| Kısayol | Arka planda çalışır; sonuç panoya ve etkin pencereye yapıştırılır |
| Arayüz | Magic UI esintili CSS uyarlaması; React/Next.js yok |
| Karanlık mod | Sistem / Açık / Koyu |
| Kurulum | PyInstaller + Inno Setup, kullanıcı bazlı, yönetici izni istemez |
| Kaldırma | Ayarlar'da büyük kırmızı buton, çift onay, tüm verileri siler |

## 2. v1.3 — Dikte sayfası

### 2.1 Yerleşim

Metin kutusunun başlık satırı, sağ taraf:

```text
[belge ikonu] Metin çıktısı        [dünya ikonu] Çıktı Dili: [Türkçe ▼]   [ ] Otomatik çevir
```

- "Çıktı Dili" etiketi ve açılır liste, eski pasif "Türkçe" yazısının yerine geçer.
- Açılır listede yalnız üç seçenek: Türkçe, İngilizce, Almanca.
- "Otomatik çevir" tıklanabilir bir kutucuktur; dil listesinin hemen sağında durur.
- Seçim anında `settings.json`'a yazılır; uygulama yeniden açılınca korunur.

Metin kutusunun altındaki buton satırı, soldan sağa:

```text
[Kopyala] [Geri Al] [Transkripsiyonu Yenile] [Yapay Zeka ile Temizle] [Çevir]
```

- "Yapay Zeka ile Temizle" zaten var; v1.3'te çalışır hale gelir, "v1.3" etiketi kaldırılır.
- "Çevir" butonu hemen sağına eklenir; aynı satırda, aynı yükseklikte.
- Butonlar metin yoksa, işlem sürerken veya hata durumunda pasif olur.

### 2.2 Davranış

| Eylem | Ne yapar | Sonuç |
| :--- | :--- | :--- |
| Kopyala | Tüm metni panoya kopyalar | Panoda güncel metin |
| Geri Al | Son paragrafı kaldırır | Metin kısalır |
| Transkripsiyonu Yenile | Son kaydın sesini tekrar çevirir | Son paragraf değişir |
| Yapay Zeka ile Temizle | Metni konuşulan dilde düzeltir; çevirmez | Metin kutusu, pano ve geçmiş güncellenir |
| Çevir | Metni temizler ve seçili çıktı diline çevirir | Metin kutusu, pano ve geçmiş güncellenir |
| Otomatik çevir açık | Her dikteden sonra Çevir davranışını kendiliğinden uygular | Kullanıcı butona basmaz |
| Otomatik çevir kapalı | Dikte metni ham haliyle kalır | Kullanıcı butonlarla işlem yapar |

Kurallar:

- Hedef dil ile konuşulan dil aynıysa **çeviri yapılmaz**; yalnızca yazım/noktalama temizliği yapılır.
- 3 kelimeden kısa metinde otomatik çeviri yapılmaz; metin ham kalır. Kullanıcı elle Temizle/Çevir'e basarsa işlem yapılabilir.
- Metin modeli yoksa, bağlantı kopuksa veya anahtar geçersizse metin bozulmaz; Türkçe hata gösterilir ve ham metin kalır.
- Temizlik/çeviri sırasında metin kutusu kilitlenmez; yalnız ilgili butonlar "İşleniyor…" durumuna geçer.
- İşlem bitince metin kutusu, pano ve geçmiş kaydı aynı metni gösterir.
- Otomatik çeviri açıkken her dikte metin modeline gider; kullanıcı bunu Ayarlar'daki uyarıdan bilir.
- "Transkripsiyonu Yenile" sonrası otomatik çevir açıksa temizlik/çeviri yeniden çalışır; sonuç son paragrafı değiştirir.

### 2.3 Dikte sonrası akış

```text
Kısayol bırakılır
  → Whisper: metin + dil tahmini
  → Metin hemen kutuya yazılır, panoya kopyalanır
  → Otomatik çevir kapalıysa: bekle
  → Otomatik çevir açıksa:
       3 kelimeden kısaysa: ham metin bırak
       değilse: metin modeli → dil algıla → temizle → gerekirse çevir
  → Son metin kutuya, panoya ve geçmişe yazılır
  → Otomatik yapıştırma açıksa etkin pencereye Ctrl+V gönderilir
```

### 2.4 Dil kararı

- Ayrı bir "dil algıla" çağrısı yoktur.
- Metin modeline tek istekte şu bilgiler verilir: metin, hedef dil, "temizle" veya "temizle+çevir" görevi.
- Model metnin dilini kendisi belirler:
  - Metin hedef dildeyse yalnızca düzeltir.
  - Farklı dildeyse düzeltir ve hedef dile çevirir.
- Whisper'ın dil tahmini yalnız yedek bilgidir; metin modeli yoksa çeviri yapılmaz.
- Türkçe doğruluğu düşerse Ayarlar'a "Girdi dili: Otomatik / Türkçe" seçeneği eklenir; varsayılan Otomatik.

### 2.5 Buton durumları

| Durum | Görünüm |
| :--- | :--- |
| Metin yok | Temizle ve Çevir pasif (%40) |
| İşlem sürüyor | Butonda küçük dönen halka + "İşleniyor…" |
| Başarılı | Butonlar normale döner; etkinlik listesine kayıt düşer |
| Hata | Kırmızı kenar + Türkçe mesaj; metin değişmez |

## 3. v1.3 — Ayarlar sayfası

### 3.1 Kart sırası

1. Kısayol Tuşu (mevcut)
2. Geçmiş (mevcut)
3. **Yapay Zeka** (yeni)
4. **Yapıştırma ve Dil** (yeni)
5. Görünüm (v1.4'te eklenecek)
6. Uygulama / Kaldırma (v1.5'te eklenecek)

### 3.2 Yapay Zeka kartı

İçerik sırası:

1. **Sağlayıcı** açılır listesi: `Yerel model (uygulama içi)` / `OpenRouter`.
2. **OpenRouter bölümü** (yalnız sağlayıcı OpenRouter ise görünür):
   - **API anahtarı:** gizli yazı alanı, `sk-or-…abcd` gibi maskeli gösterim.
   - **Kaydet** ve **Sil** düğmeleri.
   - **Bağlantıyı test et** düğmesi; kısa bir istek atar.
   - **Model** açılır listesi: yalnız ucuz/küçük modeller; her satırda yaklaşık fiyat.
   - **Model listesini yenile** bağlantısı.
   - **Sistem promptu:** çok satırlı kutu; varsayılan metin hazır gelir.
   - **Varsayılana dön** düğmesi.
3. **Yerel model bölümü** (yalnız sağlayıcı Yerel ise görünür):
   - Aktif metin modeli adı.
   - **Modeller sayfasına git** bağlantısı.
   - Model yüklü değilse "Metin modeli indir" uyarısı.
4. **Gizlilik uyarısı:** OpenRouter seçiliyken metnin internete gideceği açıkça yazar.

### 3.3 API anahtarı güvenliği

- Anahtar `data/secrets.json` içinde Windows DPAPI ile şifrelenmiş saklanır.
- Dosyada düz metin anahtar bulunmaz.
- Anahtar hiçbir log, hata mesajı, rapor veya commit içine yazılmaz.
- Ekranda yalnız son 4 karakter görünür.
- DPAPI çözümü yalnız aynı Windows kullanıcısında çalışır; başka bilgisayarda anahtar yeniden girilir.

### 3.4 OpenRouter model filtresi

- Model listesi `https://openrouter.ai/api/v1/models` adresinden çekilir.
- Filtre:
  - Girdi fiyatı 1M token başına yaklaşık 0,30 $ altı.
  - Çıktı fiyatı 1M token başına yaklaşık 0,60 $ altı.
  - Bağlam en az 8K.
- En fazla 12 model gösterilir; fiyata göre sıralanır.
- Liste `data/openrouter_models.json` içinde günde bir önbelleğe alınır.
- Çevrimdışıysa son önbellek kullanılır; yoksa "Model listesi alınamadı" yazar.

### 3.5 Varsayılan sistem promptu

```text
Sen bir dikte düzeltme asistanısın. Sana verilen metni anlamını bozmadan düzelt:
noktalama, büyük harf, tekrarlar ve dolgu kelimeleri (ee, yani, hmm) temizle.
Çeviri istenmişse hedef dile doğal ve akıcı biçimde çevir.
Metne bilgi ekleme, yorum yapma, açıklama yazma. Yalnızca son metni döndür.
```

- Hedef dil ve görev (temizle / temizle+çevir) sistem tarafından prompta ayrıca eklenir.
- Kullanıcı promptu bu zorunlu talimatları ezemez.
- Model açıklama veya tırnak eklerse yanıt temizlenir.

### 3.6 Yapıştırma ve Dil kartı

- **Girdi dili:** Otomatik / Türkçe. Varsayılan Otomatik.
- **Otomatik yapıştırma:** açık/kapalı. Varsayılan açık.
- **Çıktı dili:** Dikte sayfasındaki seçiciyle aynı ayar (tek kaynak).
- **Otomatik çevir:** Dikte sayfasındaki kutuyla aynı ayar.

## 4. v1.3 — Modeller sayfası

### 4.1 Üst bölüm

Sayfanın en üstünde iki sekme:

```text
[ Metin Modelleri (4) ] [ Ses Modelleri (6) ]
```

- Varsayılan açık sekme: Metin Modelleri.
- Sekme altında arama kutusu.
- Sekme sayıları diskteki model sayısını değil, katalogdaki toplam model sayısını gösterir.

### 4.2 Metin modeli kartları

Önerilen katalog:

| Model | Yaklaşık boyut | Not |
| :--- | :--- | :--- |
| Qwen3 1.7B Instruct (Q4_K_M) | ~1,2 GB | Hızlı, düşük bellek |
| Qwen3 4B Instruct (Q4_K_M) | ~2,5 GB | Dengeli, önerilen varsayılan |
| Gemma 3 4B IT (Q4_K_M) | ~2,5 GB | Hugging Face lisans kabulü gerekebilir |
| Llama 3.2 3B Instruct (Q4_K_M) | ~2,0 GB | Lisans kabulü gerekebilir |

Kart içeriği:

- Sol: metin modeli ikonu.
- Model adı + kısa açıklama.
- Etiketler: hız, bellek, dil desteği.
- Sağ: durum rozeti (İndirilmedi / İndiriliyor / Duraklatıldı / İndirildi / Aktif).
- Alt satır: boyut, ilerleme yüzdesi ve eylem butonları.
- İndirme sırasında: **Duraklat** ve **İptal**.
- Duraklatıldığında: **Devam et** ve **İptal**.
- İndirildiğinde: **Aktifleştir** ve **⋯** menüsü.

### 4.3 Ses modeli kartları

- Mevcut 6 model korunur: tiny, base, small, medium, large-v3, large-v3-turbo.
- Kart düzeni metin modeliyle aynı.
- İndirme kontrolü burada da geçerli: Duraklat / Devam et / İptal.

### 4.4 "⋯" menüsü

Her model kartında (ses ve metin) aynı menü:

- **Aktifleştir** (zaten aktifse pasif).
- **Yeniden indir** (önce onay ister).
- **Klasörü aç** (Windows Gezgini'nde model klasörü).
- **Detaylar** (boyut, yol, durum, dil desteği).
- **Sil** (kırmızı; onay ister; aktif model silinemez).

### 4.5 İndirme durumları

| Durum | Anlamı |
| :--- | :--- |
| İndirilmedi | Klasör yok veya boş |
| İndiriliyor | Aktif indirme; ilerleme yüzdesi |
| Duraklatıldı | `.part` dosyası duruyor; devam edilebilir |
| İndirildi | Dosya bütünlüğü doğrulandı |
| Aktif | Motorun kullandığı model |
| Hata | İndirme başarısız; tekrar dene |

### 4.6 Duraklat / devam / iptal

- Duraklat: indirme akışı durur, `.part` dosyası saklanır.
- Devam: HTTP `Range` ile kaldığı bayttan sürer.
- İptal: `.part` silinir, model "İndirilmedi" durumuna döner.
- Aynı anda yalnız bir indirme çalışır.
- Duraklatma anında değil, açık dosya parçası bitince gerçekleşir.
- Windows dosya kilidi iptali geciktirebilir; kullanıcıya Türkçe bilgi gösterilir.

### 4.7 Bellek göstergesi

- Sağ panelde ses modeli ve metin modeli için ayrı satır.
- Aynı anda yalnız biri "Yüklü" olur.
- Takas sırasında "Metin modeli yükleniyor…" veya "Ses modeli yükleniyor…" yazar.

## 5. Metin motoru ve bellek yönetimi

### 5.1 Sağlayıcı seçimi

- `settings.json` içinde `text_provider`: `local` veya `openrouter`.
- Sağlayıcı değişince bir sonraki temizlik yeni sağlayıcıyla yapılır.
- İki sağlayıcı da aynı arayüzü kullanır: `clean(text, target_language, translate=True/False)`.

### 5.2 OpenRouter isteği

- OpenAI uyumlu `chat/completions` uç noktası.
- Düşük sıcaklık (0-0.2), kısa `max_tokens`.
- Zaman aşımı ve tek deneme; hata Türkçe gösterilir.
- 401: anahtar geçersiz.
- 402: bakiye yetersiz.
- 429: çok fazla istek; biraz bekle.
- Ağ hatası: "Sunucuya ulaşılamadı; metin değişmedi."

### 5.3 Yerel GGUF ve llama.cpp

- Model dosyaları `models/text/` altında durur.
- llama.cpp modeli GPU'da `n_gpu_layers` ile, sığmazsa CPU'da çalıştırır.
- Model yüklenirken arayüz "Metin modeli yükleniyor…" gösterir.
- Model iş bitince boşaltılır; RAM/VRAM serbest bırakılır.

### 5.4 Bellek takası

- Ses modeli ve metin modeli aynı anda yüklenmez.
- Akış:
  1. Ses modeli yüklü, dikte yapılır.
  2. Temizlik/çeviri gerekiyorsa ses modeli boşaltılır.
  3. Metin modeli yüklenir, iş yapılır.
  4. Metin modeli boşaltılır.
  5. Ses modeli geri yüklenir.
- Takas süresi ilk seferde birkaç saniye olabilir; durum yazısı gösterilir.
- VRAM yetersizse metin modeli CPU/RAM'de çalışır; ses modeli GPU'da kalabilir.

## 6. Arka planda kısayol ve otomatik yapıştırma

- Kısayol dinleyicisi zaten global çalışır; pencere arkada veya simge durumunda olsa da kayıt başlar.
- Kayıt bırakılınca Whisper çevirir; otomatik çevir açıksa metin modeli çalışır.
- Son metin panoya yazılır.
- Otomatik yapıştırma açıksa etkin pencereye `Ctrl+V` gönderilir.
- Etkin pencere Dikte'nin kendi penceresiyse yapıştırma atlanır; metin yalnız kutuya yazılır.
- Yönetici olarak açılmış pencerelere sentetik tuş Windows tarafından engellenebilir; bu bilinen sınırlamadır.
- Pano eski içeriği geri yüklenmez; son metin panoda kalır.
- Pencere tamamen kapatılırsa uygulama çıkar ve kısayol durur.

## 7. v1.4 — Magic UI arayüzü ve karanlık mod

### 7.1 Yaklaşım

- Next.js/React kullanılmaz.
- Mevcut `dikte/ui/index.html`, `style.css`, `app.js` korunur.
- Magic UI bileşenlerinin görsel fikri CSS `@keyframes`, `transition` ve az JS ile uyarlanır.
- `web/` altındaki Next.js denemesi yalnız referanstır; üretim arayüzü değildir.

### 7.2 Uyarlanacak bileşenler

| Magic UI | Dikte'de kullanım |
| :--- | :--- |
| AnimatedThemeToggler | Kenar çubuğunda güneş/ay düğmesi; daire geçişi |
| MagicCard | Kartlarda fareyi izleyen gradyan kenar |
| ShineBorder | Kayıt sırasında metin panelinde dönen ışıklı kenar |
| AnimatedList | Son etkinlikler ve geçmiş listesinde sıralı giriş |
| BentoGrid | Modeller sayfasında üstte özet kartları |
| DotPattern | Arka planda çok hafif nokta deseni |

### 7.3 Karanlık mod

- Üç seçenek: **Sistem / Açık / Koyu**. Varsayılan Sistem.
- Tema `<html>` üzerindeki `dark` sınıfı ile değişir.
- Renkler CSS değişkenleriyle tanımlanır: `--background`, `--foreground`, `--card`, `--border`, `--primary`, `--muted`, `--accent`, `--destructive`.
- Seçim `localStorage["theme"]` ve `settings.json` içinde saklanır.
- İlk açılışta tema titremesini önlemek için `<head>` içinde küçük bir betik çalışır.
- Koyu temada saf siyah (`#000`) ve saf beyaz (`#fff`) kullanılmaz.
- Metin/arka plan kontrastı WCAG AA olmalı.

### 7.4 Yerleşim

- Sol kenar çubuğu korunur: Dikte, Dikte Geçmişi, Modeller, Ayarlar.
- Kenar çubuğunun altında tema düğmesi.
- Sayfa geçişlerinde yumuşak geçiş; `prefers-reduced-motion` açıksa animasyon kapalı.
- Canvas, partikül veya ağır efekt yok; WebView2 performansı korunur.

### 7.5 Tasarım kaynağı

- Yeni görünüm `design/v2/` altında spec ve ekran görüntüleriyle belgelenir.
- Eski `design/` silinmez; karşılaştırma için kalır.

## 8. v1.5 — Kurucu ve kaldırma

### 8.1 Paketleme

- **PyInstaller `onedir`** ile paket (tek dosya her açılışta açılır, yavaş).
- **Inno Setup 6** ile kurulum.
- Kurulum kullanıcı bazlıdır; yönetici izni istemez.
- Program: `%LOCALAPPDATA%\Programs\Dikte`.
- Veriler: `%LOCALAPPDATA%\Dikte` (modeller, geçmiş, ayarlar, loglar).
- Program klasörüne veri yazılmaz.
- Masaüstü ve Başlat menüsü kısayolları kurulumda seçilebilir.
- Windows açılışında başlatma isteğe bağlı; varsayılan kapalı; Ayarlar'dan değiştirilebilir.

### 8.2 Ayarlar'da kaldırma

- Ayarlar'ın en altında **"Uygulamayı Kaldır"** bölümü.
- Büyük, kırmızı, gradyan kenarlı buton.
- Butona basınca **iki ayrı onay**:
  1. "Dikte ve tüm verileri kaldırmak istiyor musun?" → Vazgeç / Devam
  2. "Modeller, geçmiş ve ayarlar kalıcı olarak silinecek. Emin misin?" → Vazgeç / Evet, kaldır
- İkinci onayda silinecek toplam boyut gösterilir (ör. "3,2 GB model + 12 MB veri").
- Onaylanınca:
  1. Uygulama kapanır.
  2. Inno Setup kaldırıcısı sessiz çalışır.
  3. exe, kısayollar, otomatik başlatma girdisi, modeller, geçmiş, ayarlar, loglar ve `%TEMP%\dikte` silinir.
- Geliştirme modunda (kurulu değilken) buton pasiftir; "Bu sürüm kurulumla gelmedi" yazar.
- Kaldırma geri alınamaz; onay metni bunu açıkça söyler.

## 9. Dosya ve veri düzeni

| Yol | İçerik |
| :--- | :--- |
| `data/settings.json` | Aktif ses modeli, kısayol, geçmiş anahtarı, çıktı dili, otomatik çevir, sağlayıcı, metin modeli, sistem promptu, tema, otomatik yapıştırma |
| `data/secrets.json` | DPAPI ile şifrelenmiş OpenRouter anahtarı |
| `data/history.json` | Son 500 dikte kaydı |
| `models/` | Whisper ses modelleri |
| `models/text/` | GGUF metin modelleri ve `.part` dosyaları |
| `logs/dikte.log` | Durum ve hata logları; konuşulan metin yazılmaz |
| `%TEMP%\dikte\last.wav` | Son kayıt; uygulama kapanınca silinir |

Kurulu sürümde `data/`, `models/`, `logs/` yolları `%LOCALAPPDATA%\Dikte` altına taşınır.
İlk paketli açılışta eski proje klasöründeki veriler tek seferlik taşınır; taşınmadan önce yedek alınır.

## 10. Ayar anahtarları

| Anahtar | Değer | Varsayılan |
| :--- | :--- | :--- |
| `output_language` | `tr` / `en` / `de` | `tr` |
| `auto_translate` | `true` / `false` | `false` |
| `input_language` | `auto` / `tr` | `auto` |
| `auto_paste` | `true` / `false` | `true` |
| `text_provider` | `local` / `openrouter` | `local` |
| `text_model` | model kimliği | `qwen3-4b` |
| `system_prompt` | metin | Varsayılan prompt |
| `theme` | `system` / `light` / `dark` | `system` |
| `autostart` | `true` / `false` | `false` |
| `active_model` | Whisper modeli | `auto` |
| `hotkey` | hazır tuş kimliği | `right_ctrl` |
| `save_history` | `true` / `false` | `true` |

## 11. Durumlar ve mesajlar

Durum makinesine `cleaning` eklenir:

| Durum | Ekranda |
| :--- | :--- |
| `loading` | Model yükleniyor… |
| `ready` | Dinlemeye hazır |
| `recording` | Dinliyor… |
| `processing` | İşleniyor… |
| `cleaning` | Metin düzenleniyor… |
| `error` | Hata mesajı |

Türkçe hata örnekleri:

- "Metin modeli yüklü değil. Modeller sayfasından indir."
- "OpenRouter anahtarı geçersiz. Ayarlar'dan kontrol et."
- "OpenRouter bakiyesi yetersiz."
- "Sunucuya ulaşılamadı; metin değişmedi."
- "Model indirilemedi. İnternet bağlantısını kontrol et."
- "İndirme iptal edilemedi; dosya başka bir işlem tarafından kullanılıyor."
- "Uygulama kaldırılamadı. Kurulum kaydı bulunamadı."

## 12. Test ve kabul ölçütleri

### 12.1 v1.3

- pytest: dil kararı, aynı dilde çeviri yok, 3 kelimeden kısa metin, prompt üretimi, OpenRouter sahte sunucu, DPAPI gidiş-dönüş, indirme Range/duraklat/devam/iptal, ayar doğrulama.
- Playwright: Çıktı Dili, Otomatik çevir, Temizle/Çevir butonları, Ayarlar kartları, Modeller sekmeleri, indirme kontrolleri.
- Gerçek: OpenRouter ile 10 cümle önce/sonra tablosu; GGUF model indirme; VRAM takas ölçümü.
- Kullanıcı testi: mikrofon, kısayol, başka pencereye yapıştırma.

### 12.2 v1.4

- Açık/koyu 4 sayfa ekran görüntüsü.
- Kontrast kontrolü.
- `prefers-reduced-motion` testi.
- DOM testleri güncel.

### 12.3 v1.5

- Kurulum → çalıştırma → kaldırma.
- Kaldırma sonrası program, kısayol, otomatik başlatma ve veri klasörlerinin silindiğinin kontrolü.
- Kurulumda antivirüs uyarısı çıkarsa kullanıcıya bilgi.

## 13. Riskler ve sınırlar

| Risk | Etki | Önlem |
| :--- | :--- | :--- |
| 8 GB VRAM | Ses + metin modeli aynı anda sığmaz | Takas; gerekirse CPU/RAM |
| llama.cpp kurulumu | Python 3.12 + CUDA wheel bulunamayabilir | Önce CPU, sonra GPU; olmazsa CPU'da kal |
| Türkçe dil doğruluğu | Whisper otomatik algılamada düşebilir | Ölçüm; gerekirse girdi dili Türkçe'ye sabitlenir |
| Kısa cümle | Dil algılama yanılabilir | 3 kelimeden kısa metinde çeviri yok |
| OpenRouter | Ücret ve gizlilik | Ucuz model filtresi, açık uyarı, harcama takibi |
| İndirme | Yarıda kalan dosya | `.part` + Range + boyut doğrulama |
| Otomatik yapıştırma | Yönetici penceresine gitmeyebilir; yanlış pencereye gidebilir | Etkin pencere kontrolü, ayardan kapatma |
| Kurucu | Antivirüs yanlış uyarısı, büyük paket | CPU-only küçük paketle başlama, boyut bilgisi |
| Kaldırma | Geri alınamaz | Çift onay + silinecek boyut |
| Tepsi yok | Pencere kapanınca kısayol durur | Bilinen sınırlama; istenirse sonra eklenir |

## 14. Uygulama sırası

1. **7a:** `text_engine.py`, OpenRouter, DPAPI anahtar, ucuz model filtresi, sistem promptu, Temizle/Çevir.
2. **7b:** GGUF kataloğu, HTTP Range indirme, duraklat/devam/iptal, llama.cpp.
3. **7c:** Bellek takası, Modeller sekmeleri ve "⋯" menüsü.
4. **7d:** Arka plan kısayolu + otomatik yapıştırma.
5. **7e:** Dikte sayfası seçicileri, Playwright, kalite ve VRAM testleri.
6. **8:** Sağlamlaştırma ve Türkçe hata mesajları.
7. **9 (v1.4):** Magic UI CSS uyarlaması + karanlık mod + `design/v2/`.
8. **10 (v1.5):** PyInstaller + Inno Setup + çift onaylı kaldırma.

Her adımda: çalışan sonuç, test/çıktı kanıtı ve kullanıcı için 5 maddelik sade özet.

## 15. Teyit bekleyen küçük varsayımlar

- Otomatik yapıştırma varsayılan açık.
- Otomatik çevir varsayılan kapalı.
- Varsayılan metin modeli Qwen3 4B.
- Windows açılışında başlatma varsayılan kapalı.
- Kaldırma tüm verileri siler.
- Pencere kapanınca uygulama çıkar; tepsi yok.
- Kısa metinde otomatik çeviri yok; elle Temizle/Çevir çalışabilir.
