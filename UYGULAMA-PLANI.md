# UYGULAMA-PLANI.md — v1.3 → v1.6 tam uygulama planı

Bu dosya v1.3 → v1.6'nın **dosya düzeyi uygulama ayrıntısıdır**: ne yapılacak, hangi dosyaya, hangi sayfada nerede duracak, nasıl test edilecek, ne ters giderse ne yapılacak. **Güncel durum ve düzeltme sırası `uygulanacak plan.md` (2026-11-07) dosyasındadır.**

Okuma sırası ve çelişki çözümü: `olabilir.md` (davranış isteği) → `design/ui-spec.md` (ölçü/renk) → **bu dosya** (uygulama) → `PLAN.md` (aşama özeti).
`olabilir.md` §7.4'teki "tema düğmesi kenar çubuğunun altında" ifadesi **geçersizdir**; düğme sağ panelde, "Aktif model" kartının üstündedir (§5.1, §5.7).

Son kararlar: 2026-11-01 (soru-cevap turu), 2026-11-04 (GitHub Releases, karşılama sihirbazı) ve 2026-11-07 (Program Files + admin, sürüm 1.6.0, kaldırmada "Modelleri koru", PyInstaller + Inno kurulumu, sentetik TTS, 7e tam, `web/` notla, MIT, basit ikon, eski `data/` taşınmaz). Açık karar kalmadı.

---

## 1. Kapsam

**İçinde:** v1.3 (metin modeli, Temizle/Çevir, otomatik yapıştırma), Aşama 8 (sağlamlaştırma), v1.4 (Magic UI CSS + karanlık mod), v1.5 (kurucu + kaldırma), v1.6 (otomatik güncelleme).

**Dışında:** Next.js/React geçişi, sistem tepsisi, kod imzalama sertifikası, çok kullanıcılı destek, bulut senkronizasyon, yeni diller, mobil.

**Değişmez sınırlar:** Python 3.12.10 · PyAV `>=11,<16` · GPU'da `float16`, CPU'da `int8` · pywebview + düz HTML/CSS/JS · 8 GB VRAM · konuşma metni loga yazılmaz.

---

## 2. Kararlar

### 2.1 Onaylı
| Konu | Karar |
| :--- | :--- |
| Çıktı dili | `tr` / `en` / `de`; varsayılan `tr` |
| Otomatik çevir | Varsayılan **kapalı** |
| Aynı dil | Hedef dil = metnin dili → yalnız temizlik |
| Kısa metin | < 3 kelime: otomatik çeviri yok; elle buton serbest |
| Metin sağlayıcı | **Varsayılan `none` (kapalı).** Kullanıcı Ayarlar → Yapay Zeka'dan `Yerel` veya `OpenRouter` seçmeden Temizle/Çevir çalışmaz |
| Anahtar | `data/secrets.json`, DPAPI şifreli, ekranda son 4 hane, loga yazılmaz |
| Bellek | Ses + metin modeli aynı anda yüklenmez (takas) |
| İndirme | Tek seferde tek model; duraklat/devam/iptal |
| Yapıştırma | `auto_paste` varsayılan **açık**; Dikte penceresine yapıştırma atlanır |
| Tema | Sistem / Açık / Koyu; düğme sağ panelde aktif model kartının üstünde |
| Tema geçişi | View Transitions + circle clip-path, 400 ms (Magic UI davranışı) |
| Paketleme | PyInstaller `onedir` + Inno Setup 6, **Program Files + admin**, tek CPU kurucu |
| Veri yolu | Kurulu sürümde `%LOCALAPPDATA%\Dikte` (kurulum klasörü değil) |
| Kaldırma | Çift onay; kullanıcı "Modelleri koru" seçer; silmeyi Inno yapar |
| Güncelleme | GitHub Releases: `latest.json` → SHA-256 → sessiz kurulum → yeniden açılış |
| İmza | Yok; antivirüs/SmartScreen riski kabul |
| Alt ajanlar | Denetimde 4 salt-okunur alt ajan; plan/denetim dışında tek ajan |
| Test yaklaşımı | Sahte HTTP sunucusu + en sonda tek gerçek OpenRouter çağrısı |

### 2.2 Kararlar (2026-11-07)
| # | Soru | Karar |
| :--- | :--- | :--- |
| K2 | Güncelleme dosyaları nerede yayınlanacak? | **GitHub Releases**; `latest.json` + kurucu yüklemeyi kullanıcı yapar |
| K3 | Açık tema paleti onayı | Onaylandı (2026-11-01), uygulandı |
| K4 | Paketli sürümde GPU desteği | CUDA paketlenmez; sihirbaz yalnız NVIDIA GPU varsa isteğe bağlı indirir |

`UPDATE_URL = https://github.com/mete2012seker-lgtm/dikte/releases/latest/download/latest.json`; indirme yönlendirmelerinde `objects.githubusercontent.com` izinli olacak.

---

## 3. Dosya haritası

| Dosya | Durum | İçerik |
| :--- | :--- | :--- |
| `dikte/secrets.py` | Yeni | `save_key`, `load_key`, `delete_key`, `masked`; `ctypes` + `CryptProtectData`/`CryptUnprotectData` |
| `dikte/openrouter.py` | Yeni | `fetch_models()`, `filter_cheap()`, önbellek `data/openrouter_models.json`, 24 saat TTL |
| `dikte/text_engine.py` | Yeni | `build_prompt()`, `clean(text, target, translate, provider)`, yanıt temizleme, hata kodları |
| `dikte/text_models.py` | Yeni | GGUF kataloğu, `download/pause/resume/cancel`, `.part` + `Range`, `LlamaRuntime` |
| `dikte/paste.py` | Yeni | `send_ctrl_v()`, `active_window_is_self()`, `paste_if_allowed()` |
| `dikte/updater.py` | Yeni | `check()`, `compare_versions()`, `download()`, `verify_sha256()`, `apply()` |
| `dikte/settings.py` | Değişir | Yeni anahtarlar + `_validate` (§4.1) |
| `dikte/state.py` | Değişir | `cleaning` durumu |
| `dikte/config.py` | Değişir | `APP_VERSION`, `TEXT_MODELS_DIR`, `SECRETS_FILE`, `OPENROUTER_MODELS_FILE`, `UPDATE_URL`, veri kökü |
| `dikte/controller.py` | Değişir | `clean_text`, `translate_text`, otomatik çevir, takas, anahtar eylemleri, güncelleme, kaldırma |
| `dikte/ui/bridge.py` | Değişir | §3.1 metotları |
| `dikte/ui/index.html` | Değişir | Başlık/butonlar, Ayarlar kartları, Modeller sekmeleri, tema düğmesi, head tema betiği |
| `dikte/ui/style.css` | Değişir | Token'lar (açık/koyu), Magic UI efektleri, yeni bileşenler |
| `dikte/ui/app.js` | Değişir | Kontroller, tema modülü, indirme, güncelleme/kaldırma, `data-testid` |
| `Dikte.spec` | Yeni (v1.5) | PyInstaller `onedir`; `web/`, `models/`, `data/`, `.venv/` dışlanır |
| `installer/Dikte.iss` | Yeni (v1.5) | Inno Setup: kullanıcı bazlı, kısayollar, sessiz kaldırma |
| `installer/latest.json` | Yeni (v1.6) | Sürüm bildirimi örneği |

### 3.1 Köprüye eklenecek metotlar
```text
clean_text() / translate_text()                 ai_settings() / ai_settings_save(payload)
openrouter_key_save(key) / key_delete() / key_test()      openrouter_models(refresh=False)
text_models_list() / text_model_download / pause / resume / cancel / activate / delete / open_folder
update_check(force=False) / update_apply()      uninstall_info() / uninstall()      theme_set(mode)
```

---

## 4. Veri modeli

### 4.1 `data/settings.json`
| Anahtar | Değer | Varsayılan |
| :--- | :--- | :--- |
| `output_language` | `tr`/`en`/`de` | `tr` |
| `auto_translate` | bool | `false` |
| `input_language` | `auto`/`tr` | `auto` |
| `auto_paste` | bool | `true` |
| `text_provider` | **`none`/`local`/`openrouter`** | **`none`** |
| `text_model` | katalog kimliği | `qwen3-4b` |
| `system_prompt` | metin | §4.2 |
| `theme` | `system`/`light`/`dark` | `system` |
| `autostart` | bool | `false` |
| `update_check_on_start` | bool | `true` |
| `update_last_check` | ISO zaman | `null` |
| `effects` | bool | `true` |
| mevcut | `active_model`, `hotkey`, `save_history`, `version` | — |

`_validate` tip + izinli değer denetler; geçersiz değer varsayılana döner (bilinmeyen `text_provider` → `none`).

**`text_provider=none` davranışı:** Temizle ve Çevir butonları pasif, `title="Ayarlar → Yapay Zeka'dan sağlayıcı seç"`. Otomatik çevir açık olsa bile işlem yapılmaz; etkinlik satırı "Metin sağlayıcısı kapalı, işlem atlandı".

### 4.2 Varsayılan sistem promptu
```text
Sen bir dikte düzeltme asistanısın. Sana verilen metni anlamını bozmadan düzelt:
noktalama, büyük harf, tekrarlar ve dolgu kelimeleri (ee, yani, hmm) temizle.
Çeviri istenmişse hedef dile doğal ve akıcı biçimde çevir.
Metne bilgi ekleme, yorum yapma, açıklama yazma. Yalnızca son metni döndür.
```
Zorunlu talimat (hedef dil + görev) sistem tarafından promptun **arkasına** eklenir; kullanıcı promptu ezemez.

### 4.3 Dosyalar
| Yol | İçerik |
| :--- | :--- |
| `data/secrets.json` | `{"openrouter": {"blob": "<base64 DPAPI>"}}` |
| `data/openrouter_models.json` | `{"fetched": ISO, "models": [...]}` |
| `models/` | Whisper modelleri |
| `models/text/` | GGUF + `.part` |
| `logs/dikte.log` | durum/hata; metin ve anahtar yok |
| `%TEMP%\dikte\last.wav` | son kayıt (yalnız uygulama açıkken) |
| `%TEMP%\dikte\guncelleme\` | kurucu indirmesi (v1.6) |

### 4.4 `latest.json`
```json
{ "version": "1.6.1", "url": "https://.../Dikte-1.6.1-kurulum.exe",
  "sha256": "<64 hex>", "notes": "Kısa not", "published": "2026-11-15T10:00:00Z" }
```

### 4.5 Kataloglar
- Ses (6): tiny, base, small, medium, large-v3, large-v3-turbo.
- Metin (4): Qwen3 1.7B (~1,2 GB), **Qwen3 4B (~2,5 GB, varsayılan)**, Gemma 3 4B (~2,5 GB), Llama 3.2 3B (~2,0 GB).
- OpenRouter filtresi: varsayılan liste girdi < 0,30 $, çıktı < 0,60 $/1M, bağlam ≥ 8K, en fazla 12 model (fiyata göre artan). "Tüm modelleri göster" açıkken bu filtre uygulanmaz; katalogdaki her model ada/kimliğe göre aranabilir (en fazla 400 satır).

### 4.6 İndirme durumları
`İndirilmedi` · `İndiriliyor` · `Duraklatıldı` · `İndirildi` · `Aktif` · `Hata`
`.part` varsa `Duraklatıldı`; boyut eşleşirse `İndirildi`.

---

## 5. Arayüz sözleşmesi

### 5.1 Dikte — sağ panel üstü (tema düğmesi)
| Öğe | Kimlik | Yer | Davranış |
| :--- | :--- | :--- | :--- |
| Tema düğmesi | `#themeToggle` | Sağ panelde "Aktif model" kartının **12 px üstü**, sağa yaslı | §5.7 |

Ölçü: 38×38 px, `border-radius: 999px`, zemin `#0C1322`, 1 px `#1B273F`, ikon 17 px (koyu: güneş, açık: ay). Dikte ve Modeller'de görünür.

### 5.2 Dikte — metin kartı başlığı
```text
[belge ikonu] Metin çıktısı        [dünya] Çıktı Dili: [#outputLang ▼]  [#autoTranslate ☐] Otomatik çevir
```

### 5.3 Dikte — buton satırı
```text
[Kopyala] [Geri Al] [Transkripsiyonu Yenile] [Yapay Zeka ile Temizle] [Çevir]
```
| Öğe | Kimlik | Pasif olduğu durumlar |
| :--- | :--- | :--- |
| Kopyala | `#copyBtn` | metin boş |
| Geri Al | `#undoBtn` | paragraf yok |
| Yenile | `#refreshBtn` | son kayıt yok / geçmişten açılmış |
| Temizle | `#cleanBtn` | metin boş · `processing` · `cleaning` · `error` · **`text_provider=none`** · sağlayıcı hazır değil |
| Çevir | `#translateBtn` | aynı |

`#cleanBtn` üzerindeki `title="Sonraki sürümde gelecek"` ve `<span class="soon">v1.3</span>` kaldırılır. Sağlayıcı kapalıysa `title` uyarı metnine döner.

### 5.4 Dikte — durum ve sağ panel
| Öğe | Kimlik | Kural |
| :--- | :--- | :--- |
| Durum | `#statusText` | `loading/ready/recording/processing/cleaning/error` |
| Metin modeli | `#textModelRow` | Ad + `Yüklü` / `Yüklü değil` / `Yükleniyor…` / `Sağlayıcı kapalı` |
| Bellek | `#memText` | takas sırasında "Takas ediliyor…" |
| Etkinlikler | `#activityList` | AI olayları `kind=ai` |

`cleaning` metni: "Metin düzenleniyor…", nokta amber.

### 5.5 Ayarlar — kart sırası
1. Kısayol Tuşu · 2. Geçmiş · 3. Yapay Zeka · 4. Yapıştırma ve Dil · 5. Görünüm (v1.4) · 6. Güncelleme (v1.6) · 7. Uygulama / Kaldırma (v1.5)

#### 5.5.1 Yapay Zeka kartı
| Sıra | Öğe | Kimlik | Kural |
| :--- | :--- | :--- | :--- |
| 1 | Sağlayıcı | `#textProvider` | `Kapalı` / `Yerel model` / `OpenRouter`; varsayılan **Kapalı** |
| 2 | Bilgi satırı | `#aiOffNote` | Yalnız Kapalı iken: "Metin temizleme/çeviri kapalı. Açmak için sağlayıcı seç." |
| 3 | API anahtarı | `#orKeyInput` | `type=password`; odakta boş; placeholder `sk-or-…abcd` |
| 4 | Kaydet | `#orKeySave` | Boş/anlamsız anahtarı reddeder |
| 5 | Sil | `#orKeyDelete` | Onay ister |
| 6 | Test et | `#orKeyTest` | Tek küçük istek; sonuç `#orKeyStatus` |
| 7 | Model | `#orModelSelect` | Varsayılan ucuz liste; "Tüm modeller" ile katalog |
| 7b | Model ara | `#orModelSearch` | 300 ms gecikmeli arama (ad/kimlik) |
| 7c | Tüm modeller | `#orShowAll` | `openrouter_show_all`; fiyat sınırını kaldırır |
| 8 | Yenile | `#orModelRefresh` | Önbelleği zorlar |
| 9 | Sistem promptu | `#systemPrompt` | Çok satırlı |
| 10 | Varsayılana dön | `#systemPromptReset` | Onay istemez |
| 11 | Gizlilik notu | `#orPrivacyNote` | Yalnız OpenRouter seçiliyken |
| 12 | Yerel bölüm | `#localAiSection` | Aktif model + "Modeller sayfasına git" + model yoksa uyarı |

#### 5.5.2 Yapıştırma ve Dil kartı
| Öğe | Kimlik | Ayar |
| :--- | :--- | :--- |
| Girdi dili | `#inputLang` | `input_language` |
| Otomatik yapıştırma | `#autoPasteSwitch` | `auto_paste` (varsayılan açık) |
| Çıktı dili | `#outputLangSettings` | `output_language` (Dikte ile aynı) |
| Otomatik çevir | `#autoTranslateSettings` | `auto_translate` (Dikte ile aynı) |

#### 5.5.3 Uygulama / Kaldırma kartı (v1.5)
| Öğe | Kimlik | Kural |
| :--- | :--- | :--- |
| Kaldır | `#uninstallBtn` | Büyük kırmızı; kurulu değilse pasif + "Bu sürüm kurulumla gelmedi" |
| 1. onay | `#confirmUninstall1` | "Dikte ve tüm verileri kaldırılsın mı?" |
| 2. onay | `#confirmUninstall2` | `#uninstallSize` boyut gösterir |
| Sonuç | `#uninstallStatus` | "Kaldırıcı başlatıldı" / Türkçe hata |

### 5.6 Güncelleme kartı (v1.6)
| Öğe | Kimlik | Kural |
| :--- | :--- | :--- |
| Sürüm | `#updateVersion` | `config.APP_VERSION` |
| Son denetim | `#updateLastCheck` | `update_last_check` |
| Denetle | `#updateCheckBtn` | "Denetleniyor…" → sonuç |
| Güncelle | `#updateApplyBtn` | Yeni sürüm yoksa pasif; indirme yüzdesi buton içinde |
| Açılışta denetle | `#updateAutoSwitch` | `update_check_on_start` |
| Durum | `#updateStatus` | "Güncel" / "Yeni sürüm: x.y.z" / "Sunucuya ulaşılamadı" |
| Notlar | `#updateNotes` | `latest.json.notes`, düz metin |

### 5.7 Tema (v1.4)
#### 5.7.1 Davranış
1. Tıkla → `getBoundingClientRect()` merkez `cx, cy`; `W=innerWidth`, `H=innerHeight`.
2. `maxRadius = hypot(max(cx, W-cx), max(cy, H-cy))`; yüzde tabanı `hypot(W,H)/√2`.
3. `startViewTransition(() => root.classList.toggle("dark"))`; sınıf **senkron** değişir.
4. `transition.ready` → `root.animate({clipPath:[kapanmış, açık]}, {duration:400, easing:"ease-in-out", fill:"forwards", pseudoElement:"::view-transition-new(root)"})`.
5. Geçiş sürerken ikinci tıklama yok sayılır; `finished` sonrası geçici CSS değişkenleri silinir.
6. `startViewTransition` yok → anlık sınıf değişimi.
7. `prefers-reduced-motion: reduce` → animasyonsuz.

CSS şartı: `::view-transition-old(root), ::view-transition-new(root) { animation: none; mix-blend-mode: normal; }`

#### 5.7.2 Kalıcılık
- `<head>` betiği: `localStorage["theme"]`; `system` ise `matchMedia`; `<html class="dark">` (titremesiz ilk boyama).
- `setTheme(mode)` → sınıf + `localStorage` + `settings.theme`.
- `system` modunda düğme çözülen temanın tersine geçer ve modu `light`/`dark` yapar.

#### 5.7.3 Açık tema token'ları (K3: önce görsel onayı)
| Rol | Koyu (bugünkü) | Açık (öneri) |
| :--- | :--- | :--- |
| Zemin | `#080D1A` | `#F7F9FD` |
| Kart | `#0C1322` | `#FFFFFF` |
| Kart iç | `#0A1120` | `#F2F5FB` |
| Kenarlık | `#1B2740` | `#DFE6F3` |
| Ana yazı | `#E9EEF9` | `#101828` |
| İkincil | `#A7B2C9` | `#4A5670` |
| Soluk | `#6E7B96` | `#77839B` |
| Vurgu | `#4C6BFF` | `#3D5BF5` |
| Hata | `#EF5B5B` | `#D93A3A` |

**Onay kapısı:** Parti 11'de önce açık temanın 4 sayfa önizlemesi (statik HTML ekran görüntüsü) gösterilir; onay gelmeden `style.css` token'ları değiştirilmez. Ret gelirse palet revize edilir.

#### 5.7.4 Magic UI efektleri
| Efekt | Yer | Teknik |
| :--- | :--- | :--- |
| MagicCard | Metin kartı, sağ panel, model kartları | `pointermove` → `rAF` ile `--mx/--my`; `::before` radial-gradient + `mask ... content-box exclude` |
| ShineBorder | Metin kartı, yalnız kayıt/işleme | `::after` conic-gradient + `@property --a`; sınıf yoksa kapalı |
| AnimatedList | Etkinlikler, geçmiş | `.is-new` + `@keyframes rise`, `calc(var(--i)*45ms)`; silmede `.is-leaving` |
| BentoGrid | Modeller üstü 3 kutu | `repeat(3,minmax(0,1fr))`, bir kutu `span 2`; <1180 px tek sütun |
| DotPattern | Dikte zemini | `radial-gradient` 22 px + `mask-image`; `pointer-events:none` |

`effects=false` veya `prefers-reduced-motion` → tüm efektler kapanır.

### 5.8 Modeller sayfası
- Sekmeler `#tabText` / `#tabAudio`; sıra `Metin (4)` `Ses (6)`; varsayılan Metin.
- Arama `#modelSearch` ortak.
- Kart: ikon, ad, açıklama, etiketler, boyut, durum rozeti, yüzde, eylemler.
- Eylemler: `İndir` · `Duraklat`+`İptal` · `Devam et`+`İptal` · `Aktifleştir`+`⋯`.
- Menü `#modelMenu`: Aktifleştir (aktifse pasif), Yeniden indir (onay), Klasörü aç, Detaylar, Sil (kırmızı, onay, aktif korumalı).
- Bento: Aktif model · Disk kullanımı · Katalog sayısı.

### 5.9 Geçmiş sayfası
İşlev değişmez; yalnız liste animasyonu (v1.4).

---

## 6. Metin akışı ve eşzamanlılık

### 6.1 Dikte sonrası
```text
kısayol bırakılır
 → Whisper: metin + dil ipucu
 → metin kutuya + panoya
 → auto_translate kapalı → dur
 → auto_translate açık:
      provider = none  → "Metin sağlayıcısı kapalı, işlem atlandı"
      kelime < 3       → ham metin kalır ("Kısa metin, çeviri atlandı")
      değilse          → metin modeli (tek çağrı: temizle | temizle+çevir)
 → sonuç kutu + pano + geçmiş
 → auto_paste açık ve etkin pencere Dikte değilse Ctrl+V
```
Hata → metin **değişmez**, `ready`'ye dönülür, etkinlikte kırmızı kayıt.

### 6.2 Durum makinesi
`loading → ready → recording → processing → (cleaning) → ready`; `error` her yerden.

### 6.3 Takas ve eşzamanlılık
- Takas sırasında yeni dikte kayda alınır, çeviri takas bitince çalışır (1 kayıt kuyruğu).
- Kuyrukta 1'den fazla kayıt → ikincisi reddedilir: "Metin modeli hazır olunca tekrar deneyin."
- Temizle/Çevir sırasında ikinci istek yok sayılır.
- `text_provider=openrouter` → GGUF yüklenmez, ses modeli boşaltılmaz.
- `text_provider=none` → masaüstü işlem yok.

### 6.4 Hata mesajları
| Kod | Mesaj |
| :--- | :--- |
| `provider_off` | Metin sağlayıcısı kapalı. Ayarlar → Yapay Zeka'dan seç. |
| `no_key` | OpenRouter anahtarı yok. Ayarlar'dan ekle. |
| `401` | OpenRouter anahtarı geçersiz. Ayarlar'dan kontrol et. |
| `402` | OpenRouter bakiyesi yetersiz. |
| `429` | Çok fazla istek. Biraz bekleyip tekrar dene. |
| `net` | Sunucuya ulaşılamadı; metin değişmedi. |
| `local_missing` | Metin modeli yüklü değil. Modeller sayfasından indir. |
| `local_load` | Metin modeli yüklenemedi; metin değişmedi. |
| `bad_response` | Model geçerli yanıt vermedi; metin değişmedi. |
| `not_translated` | Model çeviri yapmadı; farklı bir model seçmeyi dene. |
| `hallucination` | Model metne bilgi ekledi; farklı bir model seçmeyi dene. |

---

## 7. Uygulama sırası (13 parti)

Her parti: kodu yaz → çalıştır → test → kanıt → 5 maddelik özet. Parti bitmeden sonraki başlamaz.

**Goal bölünmesi (kullanıcı kararı):** İlk goal **parti 1–5**. Testler geçince ikinci goal **6–13**.

### Parti 1 — Ayarlar, sırlar, durum
- [ ] `secrets.py` (DPAPI), `settings.py` yeni anahtarlar (`text_provider=none` varsayılan), `state.py` `cleaning`, `config.py` sabitleri.
- Kabul: DPAPI gidiş-dönüş; bozuk blob çökertmiyor; bilinmeyen `text_provider` → `none`.
- Kanıt: `pytest tests/test_secrets.py tests/test_settings.py -q`.

### Parti 2 — OpenRouter istemcisi
- [ ] `openrouter.py` listeleme/filtre/önbellek; `text_engine.py` prompt, çağrı, yanıt temizleme, hata kodu.
- Kabul: filtre eşikleri, 12 sınırı, TTL; fazla tümce/tırnak temizleniyor.
- Kanıt: sahte HTTP 200/401/402/429/ağ.

### Parti 3 — Controller: temizle/çevir
- [ ] `clean_text`, `translate_text`, otomatik çevir, `provider=none` kısa devre, 3 kelime + aynı dil kuralı, hata düşüşü, etkinlik, `cleaning`.
- Kabul: hata/`none` metni değiştirmiyor; kısa metin korunuyor; geçmiş son metinle güncelleniyor.
- Kanıt: `tests/test_controller.py` genişletilir.

### Parti 4 — Dikte arayüzü
- [ ] `#outputLang`, `#autoTranslate`, `#translateBtn`, `#cleanBtn`; pasiflik kuralları; `cleaning`; sağlayıcı kapalı ipucu.
- Kabul: seçim anında kaydediliyor; yeniden açılışta korunuyor; 1280×800'de taşma yok.
- Kanıt: Playwright + `artifacts/ui-dikte-v13.png`.

### Parti 5 — Ayarlar: Yapay Zeka + Yapıştırma/Dil
- [ ] §5.5.1, §5.5.2; varsayılan "Kapalı" + bilgi satırı; sağlayıcıya göre bölüm takası; gizlilik notu; anahtar maskesi.
- Kabul: kaydedilince maskeli; test düğmesi "Bağlantı çalışıyor"; sağlayıcı Kapalı iken Dikte butonları pasif.
- Kanıt: Playwright + sahte sunucu anahtar testi + **en sonda tek gerçek çağrı**.

### Parti 6 — Metin modelleri + indirme
- [ ] `text_models.py` katalog + `.part`/`Range`; indirme kontrolleri; disk alanı kontrolü.
- Kabul: duraklat→devam aynı bayttan; iptal `.part`'ı siliyor; boyut uyuşmazsa baştan.
- Kanıt: `tests/test_text_models.py`.

### Parti 7 — llama.cpp + takas
- [ ] `LlamaRuntime`; `n_gpu_layers` kademeli düşüş; takas + kuyruk.
- Kabul: 8 GB'de metin modeli CPU'ya düşerek çalışıyor; takas sonrası ses modeli geri yükleniyor.
- Kanıt: gerçek GGUF + VRAM ölçümü (SENİN TESTİN).

### Parti 8 — Modeller arayüzü
- [ ] Sekmeler, bento, `⋯` menüsü, indirme kontrolleri, iki bellek satırı.
- Kabul: sekme sayıları katalogla uyumlu; aktif modelde Sil pasif.
- Kanıt: Playwright + `artifacts/ui-modeller-v13.png`.

### Parti 9 — Arka plan + otomatik yapıştırma
- [ ] `paste.py`, controller kancası, `auto_paste`; Dikte penceresini atlama.
- Kabul: kendi penceresinde Ctrl+V yok; ayar kapalıyken hiç yok.
- Kanıt: pytest + SENİN TESTİN.

### Parti 10 — Sağlamlaştırma
- [ ] Tüm hata mesajları Türkçe; kapanışta geçici dosya temizliği; ham metne düşüş.
- Kabul: her kodun tek Türkçe metni var; log'da metin yok.
- Kanıt: `tests/test_errors.py` + log taraması.

### Parti 11 — v1.4 tema
- [ ] Önce **açık tema önizleme görseli** (K3 onayı). Onaydan sonra: token'lar, `<head>` betiği, `#themeToggle`, Görünüm kartı, Magic UI efektleri, `design/v2/`.
- Kabul: daire geçişi 400 ms; `prefers-reduced-motion` kapatıyor; kontrast AA.
- Kanıt: açık/koyu 4 sayfa görüntüsü + kontrast testi.

### Parti 12 — v1.5 kurucu + kaldırma
- [ ] `Dikte.spec`, `installer/Dikte.iss`, veri göçü, kısayollar, otomatik başlatma, kaldırma kartı. **Tek CPU kurucu.**
- Kabul: yönetici izni istemiyor; veri `%LOCALAPPDATA%\Dikte`; çift onay + boyut.
- Kanıt: SENİN TESTİN + dosya listesi.
- Not: paketli sürümde GPU/CUDA bileşeni yok (K4); istenirse ayrı iş olarak eklenir.

### Parti 13 — v1.6 güncelleme
- [ ] `updater.py`, Güncelleme kartı, açılışta sessiz denetim. `UPDATE_URL` tek sabit (K2 bekliyor).
- Kabul: 4 senaryo (var/yok/bozuk/ağ); HTTPS zorunlu; sürüm döngüsü yok.
- Kanıt: `tests/test_updater.py` + gerçek yükseltme.

---

## 8. Test planı

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m pytest tests/test_text_engine.py -q
.venv\Scripts\python.exe -m dikte --selftest
.venv\Scripts\python.exe -m pytest tests/test_ui.py -q
```
Mevcut **83 test**; hedef **≥ 155**.

### 8.1 `test_secrets.py` (6)
Kaydet→oku · dosyada düz metin yok · bozuk blob → `None` · dosya yok · `masked` son 4 hane · sil (ikinci silme hatasız).

### 8.2 `test_settings.py` (+11)
Her yeni anahtar: geçerli korunur · geçersiz varsayılana döner · bilinmeyen anahtar korunur · atomik yazma · bozuk JSON yedeklenir · `text_provider` geçersiz değeri `none`'a döner.

### 8.3 `test_text_engine.py` (14)
Aynı dil→yalnız temizlik · farklı dil→çevir · 2 kelime atlanır · 3 kelime sınırı · 4 kelime işlenir · prompt sırası · yanıt temizleme · sağlayıcı yönlendirme · 401 · 402 · 429 · zaman aşımı · `max_tokens` kesme uyarısı · boş yanıt.

### 8.4 `test_openrouter.py` (7)
Filtre alt/üst sınır · 12 sınırı · sıralama · önbellek yazma · TTL yenileme · çevrimdışı eski önbellek.

### 8.5 `test_text_models.py` (12)
Katalog · boyut · `.part`→Duraklatıldı · duraklat baytı · `Range` başlığı · devam · iptal siler · boyut uyuşmazlığı · tek indirme kilidi · disk yetersiz · aktif model silinemez · kimlik doğrulama.

### 8.6 `test_takeover.py` (6)
Ses boşalt→metin yükle · hata → ses geri · `openrouter` seçiliyken takas yok · takas sırasında kuyruk · kuyruk 2. kaydı reddeder · süre ölçülür.

### 8.7 `test_paste.py` (6)
Kendi pencere→gönderilmez · başka pencere→gönderilir · ayar kapalı · pencere yok→sessiz · Ctrl+V baytları · hata mesajı.

### 8.8 `test_updater.py` (11)
`1.6.10 > 1.6.9` · eşit sürüm · `http` reddi · alan adı reddi · SHA uyuşmaz → sil · 404 sessiz · ağ yok sessiz · ilerleme · `apply()` subprocess mock · açılış denetimi kapalı · `notes` düz metin.

### 8.9 `test_ui.py` (+17 Playwright)
Dil seçenekleri · otomatik çevir kaydı · buton pasifliği · v1.3 etiketi yok · kart sırası · sağlayıcı "Kapalı" bilgi satırı · bölüm takası · anahtar maskesi · sekmeler · `⋯` menü · tema sınıf değişimi · kontrast · reduced-motion · güncelleme durumu · güncelle pasifliği · kaldırma 1. onay · kurulu değilse kaldırma pasif.

### 8.10 Elle/gerçek
OpenRouter 10 cümle tablosu (ajan + tek gerçek çağrı) · GGUF indirme (ajan) · VRAM takası (kullanıcı) · mikrofon/kısayol (kullanıcı) · yapıştırma (kullanıcı) · kur/kaldır (kullanıcı) · güncelleme yükseltme (kullanıcı).

---

## 9. Risk kaydı

| # | Risk | Parti | Etki | Olasılık | Önlem | Düşüş |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| R1 | llama.cpp wheel yok | 7 | Y | O | Önce CPU wheel, sürüm sabitleme | Yalnız OpenRouter |
| R2 | 8 GB VRAM yetmez | 7 | Y | Y | Takas + kademeli `n_gpu_layers` | Metin modeli CPU'da |
| R3 | OpenRouter ücreti | 2,3 | O | O | Ucuz filtre, `max_tokens`, otomatik çevir kapalı | Yalnız yerel |
| R4 | 429/5xx/ağ | 2,3 | O | O | Tek deneme + 1 geri çekilme | Ham metin |
| R5 | DPAPI çözülmez | 1 | O | D | Hata yakalama | Sağlayıcı `local` |
| R6 | Anahtar sızar | 1,2 | Y | D | Tek modül, log filtresi | Anahtar iptal |
| R7 | Antivirüs | 12 | Y | O | Uyarı metni, küçük kurucu, SHA | Defender istisnası |
| R8 | İptal kilidi | 6 | D | O | 3×250 ms deneme | Sonraki deneme |
| R9 | Bozuk `.part` | 6 | O | O | `Content-Range` + boyut | Baştan indir |
| R10 | Yönetici penceresi | 9 | O | O | Etkin pencere kontrolü | Elle Ctrl+V |
| R11 | Yanlış pencere | 9 | Y | D | Ayar + pencere kontrolü | `auto_paste=false` |
| R12 | Whisper dil | 4,7 | O | O | 10 cümle ölçümü | Girdi dili `tr` |
| R13 | 3 kelime/aynı dil | 3 | O | D | Sınır testleri | Eşik tek sabitten |
| R14 | Model açıklama ekler | 3 | O | O | Prompt + temizleme | Sıcaklık 0 |
| R15 | `startViewTransition` yok | 11 | D | O | Özellik algılama | Anlık değişim |
| R16 | Boşta CPU | 11 | O | O | transform/opacity, `document.hidden` | `effects=false` |
| R17 | Açık palet onayı | 11 | O | Y | Önce önizleme görseli | Palet revize |
| R18 | Paket boyutu | 12 | O | O | `onedir`, CPU-only | — |
| R19 | CUDA DLL (paketli) | 12 | O | O | Paketli sürüm CPU/int8 (K4) | GPU isteğe bağlı ayrı iş |
| R20 | Veri göçü | 12 | Y | O | Önce yedek, tek seferlik | Eski yol |
| R21 | Yarım kaldırma | 12 | O | O | Kapat→kaldırıcı→kalanlar | Kalan dosya raporu |
| R22 | Yayın yeri (K2) | 13 | Y | Y | `UPDATE_URL` tek sabit | Kart pasif |
| R23 | Bozuk güncelleme | 13 | Y | D | SHA + alan adı | Dosya silinir |
| R24 | Açılmayan sürüm | 13 | Y | D | Ayar yedeği, `/NORESTART` | Önceki link + yedek |
| R25 | Disk dolar | 6,8 | O | O | `boyut × 1,1` kontrolü | İndirme engellenir |
| R26 | Playwright farkı | 4,5,8,11 | O | O | Sahte köprü | `data-testid` |
| R27 | Goal bütçesi | tümü | Y | O | 1–5 / 6–13 bölünmesi | Partiler ayrı oturum |
| R28 | Aynı model → tek bakış | tümü | O | O | Sabit kontrol listesi | Onayla farklı model |
| R29 | Sağlayıcı kapalıyken kullanıcı şaşırır | 3,4,5 | O | O | Bilgi satırı + buton `title` + etkinlik satırı | Varsayılan sağlayıcı sorulur |

---

## 10. Senaryo kütüphanesi ("şöyle olursa → çözüm böyle")

| # | Belirti | Kök neden | Çözüm | Doğrulama |
| :--- | :--- | :--- | :--- | :--- |
| S1 | `cublas64_12.dll` hatası | CUDA DLL yolda değil | `diagnostics` DLL yolu; CPU/int8 düşüş | `--selftest` CPU |
| S2 | GPU `auto` çöküyor | RTX 5060 + CTranslate2 | GPU'da daima `float16` | `test_engine_plan` |
| S3 | Hata olduğu halde metin değişti | Erken yazma | Yalnız başarılı yanıtta yaz | `test_controller` |
| S4 | Temizle/Çevir'e basınca hiçbir şey olmuyor | `provider=none` | Bilgi satırı + `title` + etkinlik "sağlayıcı kapalı" | `test_ui` |
| S5 | 3 kelime çevrilmiyor | Kural sessiz | "Kısa metin, çeviri atlandı"; elle Çevir çalışır | `test_text_engine` |
| S6 | Otomatik çevir yavaşlatıyor | Her dikte + takas | "Metin düzenleniyor…" + Ayarlar uyarısı | elle |
| S7 | Takas sırasında kısayol | Eşzamanlılık | Kayıt kuyruğa girer; ikinci ret | `test_takeover` |
| S8 | İndirme %99'da takıldı | Son bayt gelmiyor | 30 sn bayt yoksa boyut kontrolü | sahte gecikmeli paket |
| S9 | İptal silmiyor | Dosya kilidi | 3 deneme + "dosya başka işlemde" | `test_text_models` |
| S10 | Devam bozuk | Sunucu `Range` yok saydı | `Content-Range` kontrolü, uymazsa baştan | sahte Range'siz sunucu |
| S11 | Anahtar kaydedilemiyor | DPAPI hatası | "Kaydedilemedi"; bellekte tutulmaz | `test_secrets` |
| S12 | 401 | Anahtar geçersiz | Türkçe mesaj, metin aynı | sahte 401 |
| S13 | Temizle, model yok | GGUF indirilmemiş | `local_missing` + Modeller bağlantısı | `test_controller` |
| S14 | Aynı dilde çeviri | Yanlış seçim | Model "aynı dil" der, yalnız temizler | `test_text_engine` |
| S15 | Yanıt tırnak/açıklama | Zayıf prompt | Temizleme + sıcaklık 0 | `test_text_engine` |
| S16 | Ayarlar bozuk | Kesinti | `.bozuk-*` yedek + varsayılan | `test_settings` |
| S17 | Model dosyası silinmiş | Kullanıcı sildi | "Model bulunamadı", seçim ilk modele döner | `test_text_models` |
| S18 | Kendi penceresine yapıştı | Pencere yarışı | Yapıştırma öncesi pencere tekrar okunur | `test_paste` |
| S19 | Yönetici penceresine gitmiyor | UIPI | "Bu pencere yönetici; elle yapıştır" | elle |
| S20 | Tema düğmesi tepki yok | `startViewTransition` yok | Algılama + try/catch; sınıf değişir | Playwright |
| S21 | Tema geçişinde titreme | Varsayılan VT animasyonu | `::view-transition-*{animation:none}` | elle |
| S22 | Hızlı iki tık | Çift geçiş | Geçişte yok say | Playwright |
| S23 | Açık temada okunmuyor | Kontrast | Token revizyonu; K3 onayı | kontrast testi |
| S24 | Efektler kasıyor | Her olayda stil | `rAF`, `document.hidden` | elle |
| S25 | Kurulum sonrası model yok | `models/` paketlenmedi | İlk açılışta indirme akışı | elle |
| S26 | SmartScreen uyarısı | İmzasız exe | "Ek bilgi → Yine de çalıştır" | elle |
| S27 | Kaldırmadan sonra klasör kaldı | Model kilidi | Kapat, 2 sn, tekrar sil, listele | elle |
| S28 | Güncelleme yarıda | Ağ | Yeniden indir; `.part` silinir | `test_updater` |
| S29 | `latest.json` bozuk | Yayın hatası | Hatayı yut, "denetlenemedi" | `test_updater` |
| S30 | Sürüm yanlış kıyas | Metin karşılaştırma | `compare_versions` sayısal | `test_updater` |
| S31 | Güncelleme döngüsü | Kurulum sürümü güncellenmiyor | Tek kaynak `APP_VERSION` | `test_updater` |
| S32 | Güncelleme sonrası ayarlar gitti | Kurucu veriye dokundu | Inno veri klasörüne dokunmaz | elle |
| S33 | Playwright kırıldı | Kimlik değişti | `data-testid` sabit | testler |
| S34 | GPU meşgul | Başka program | GPU testleri `-m gpu` | `pytest -m "not gpu"` |
| S35 | Yanıt çok uzun | `max_tokens` yok | Uzunluğa göre sınır | `test_text_engine` |
| S36 | `last.wav` kaldı | Kapanış kancası | `shutdown` + `atexit` + açılışta temizlik | `test_controller` |

---

## 11. Kullanıcı testleri

**Metin modeli:** Ayarlar → Yapay Zeka → sağlayıcı **OpenRouter** (varsayılan Kapalı) → anahtarı gir → Test et → model seç → Dikte'de Çıktı Dili İngilizce + otomatik çevir açık → Türkçe cümle → İngilizce gelmeli; tekrar dikte → yalnız düzeltme.

**Sağlayıcı kapalı kontrolü:** Ayarlar'da sağlayıcıyı **Kapalı** yap → Dikte'de Temizle/Çevir pasif olmalı ve ipucu görünmeli.

**Yapıştırma:** Not Defteri'nde imleç → kısayolla konuş → metin yapışmalı; pencere küçültülmüşken de.

**Tema:** kart üstündeki yuvarlak düğme → daire geçişi; kapat/aç → korunur; Ayarlar → Görünüm → Sistem → Windows teması takip edilir.

**Kurulum:** kurucu (SmartScreen) → aç → model indir → dikte → Kaldır → iki onay → `%LOCALAPPDATA%\Dikte` ve `Programs\Dikte` silinmiş.

---

## 12. Yayın ve geri alma

| Adım | Kural |
| :--- | :--- |
| Sürüm | Tek kaynak `config.APP_VERSION`; kurucu ve `latest.json` aynı |
| Release | `Dikte-x.y.z-kurulum.exe` + `.sha256` + `latest.json` |
| Güncelleme | Yalnız HTTPS, alan adı kontrolü, SHA-256 zorunlu |
| Geri alma | Önceki kurucu Releases'te kalır; ayarlar `%LOCALAPPDATA%`'da |
| Veri göçü | v1.5 ilk açılışta proje klasöründen taşıma; önce yedek |
| Log | sürüm, mod, cihaz, süre; metin ve anahtar yok |

---

## 13. Alt ajanlar

| Ajan | Model | Görev | Sınır |
| :--- | :--- | :--- | :--- |
| `@arastirmaci` | `deepseek/deepseek-v4.1-flash-1017` | Web/GitHub araştırması, `reports/` | Kod yazmaz |
| `@gozden-gecirici` | aynı | Kod incelemesi, `dosya:satır` | Kod değiştirmez |
| `@testci` | aynı | pytest/selftest/Playwright | Özellik yazmaz, 3 deneme |

Aynı anda en fazla 3; aynı dosyaya dokunan işler paralel değil; arayüz dosyaları tek şerit; kanıtsız bulgu kabul edilmez.

---

## 14. Bitti tanımı ve goal

Bir parti üçü tamamlanmadan kapanmaz: **çalışan sonuç**, **kanıt** (test sayısı/çıktı/görüntü yolu), **5 maddelik sade özet**. `STATE.md` + `architecture.md` güncellenir; commit yalnız `/asama-bitir` veya açık istek.

**Goal 1 (şimdi):** parti 1–5. Bitişte dur, kullanıcı anahtarı girer ve gerçek çağrıyı onaylar.
**Goal 2:** parti 6–10. Bitişte VRAM ve yapıştırma kullanıcı testi.
**Goal 3:** parti 11–13. Parti 11 başında açık tema önizlemesi (K3), parti 13 başında yayın yeri (K2), parti 12 kur/kaldır kullanıcı testi.
