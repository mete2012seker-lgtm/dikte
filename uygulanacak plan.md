# uygulanacak plan.md — Kalan işler için uygulama planı

Oluşturma: 2026-11-04. Kaynak: `olabilir.md` (yapılmayan maddeler), AGENTS.md kararları ve 2026-11-04 kullanıcı kararları.
Bu plan kod yazılmadan önce kullanıcı onayına sunulmuştur; onay alındıktan sonra sırayla uygulanır.

## Kullanıcı kararları (2026-11-04)

| Konu | Karar |
| :--- | :--- |
| Depo görünürlüğü | GitHub deposu herkese açık yapıldı → v1.6 için GitHub Releases kullanılabilir |
| 7e kalite seti | Sentetik TTS sesleri ile 10 cümle ölçümü |
| v1.6 yayın yeri | GitHub Releases (`latest.json` + kurucu + SHA-256) |
| v1.4 efektleri | Kullanıcı gözle onayladı → v1.4 kapatılmış sayılır |
| Yeni kapsam | Kurucuya ilk açılış karşılama sihirbazı eklenir; 5 ekranlı Magic UI taslağı kullanıcı tarafından onaylandı (açık + karanlık hal), kaynak `design/v2/karsilama-sihirbazi-taslak.html` |
| Sihirbazda animasyon | Magic UI animasyonları sihirbazda da çalışır (MagicCard fare ışığı, ShineBorder, DotPattern, adım geçiş animasyonu); Ayarlar'daki "Arayüz efektleri" anahtarı sihirbazı da kapatır |
| Kurulum davranışı (2026-11-04) | Tek kurucu exe çift tıkla kurulur, normal bir Windows programı gibi Program Files altına kurulur |
| Python gereksinimi (2026-11-04) | Kurucu, bilgisayarda Python yoksa gerekli ortamı kendisi kurar (aşağıda 2c'de iki yol tanımlı) |

**Kurulum ve Python notu (önemli):** PyInstaller ile paketlenen kurucu, Python'u **zaten kendi içinde taşır** — kullanıcının Python kurması gerekmez; bu yol "Python otomatik kurulumu"nu gereksiz kılar. Kullanıcının istediği "Python yoksa kurucu kursun" ihtiyacı iki yolla sağlanır; 2c'de ikisi de planlıdır ve uygulama sırasında karar verilir:

- **Yol A (önerilen, büyük olasılıkla yeterli):** Tek exe içinde Python gömülü gelir (PyInstaller onedir). Kurucu hiçbir şeye muhtaç değildir; çift tık → Program Files'a kur → çalışır.
- **Yol B (yedek):** Python gömülmediğinde (ör. antivirüs boyut kısıtı ya da PyInstaller patlaması), kurucu açılışta Python 3.12'yi denetler; yoksa resmi kurulum paketini sessiz indirip kurar, sonra ortamı hazırlar. Bu yolda internet gereklidir ve kurucu küçülür.

## Kapsam dışı / onay bekleyen

- Kod imzalama (antivirüs uyarısı) — şimdilik yok; gerekirse ayrı aşama.
- Sistem tepsisi — bilinen sınırlama olarak kalır.
- Whisper girdi dili sabitleme motora bağlanacak mı — v1.5 sırasında değerlendirilir.

---

## Adım 0 — Public depo güvenlik kontrolü (küçük iş)

Repo artık herkese açık; git geçmişinde ve izlenen dosyalarda gizli bilgi olmadığını doğrula.

- [ ] `git ls-files` ile izlenen dosyalarda anahtar/e-posta/kişisel yol taraması (API anahtarı, `sk-or-`, DPAPI verisi).
- [ ] `.gitignore` kontrolü: `.env`, `data/` (secrets + history), `models/`, `logs/`, `artifacts/` dışarıda mı?
- [ ] Geçmiş taraması: `git log -p` üzerinde "sk-or", "api_key" araması; temizse bitti, kirliyse kullanıcıya bildir (tarih değiştirme kararı kullanıcıya ait).
- **Kanıt:** tarama çıktısı özeti, STATE.md'ye tek satır.

## Adım 1 — 7e kalite tablosu (orta iş, ~1 oturum)

Gerçek gemma3-4b GGUF ile sentetik seslerden üretilen metinler üzerinde ölçüm.

- [ ] 10 cümlelik Türkçe test seti yaz (günlük konuşma dili, dolgu kelimeleri, Türkçe özel karakterler: ı ğ ş ç ö ü). TTS ile 10 wav üret.
- [ ] Akış: sentetik wav → Whisper → ham metin → (a) temizle, (b) tr→en çevir, (c) tr→de çevir.
- [ ] VRAM takas ölçümü: ses modeli yüklüyken temizlik isteği → boşaltma + metin modeli yükleme + iş + geri yükleme süreleri.
- [ ] İlk çağrı CUDA ısınma süresi (~50 sn) tekrar ölçülür; ısınma çağrısı eklenip eklenmeyeceğine ölçüm sonrası karar verilir.
- [ ] Rapor: `reports/2026-11-XX-7e-kalite.md` (önce/sonra tablosu, süreler), `reports/README.md`'ye satır ekle.
- [ ] STATE.md güncelle.
- **Kanıt:** rapor dosyası + pytest bozulmadan geçiyor.
- **Zayıf nokta:** sentetik TTS sesi gerçek konuşmadan daha temiz olduğundan Whisper ham metni az hatalı çıkar; tablo "en iyi durum" ölçümü olarak yorumlanır (rapora not düşülür).

## Adım 2 — v1.5 kurucu + kaldırma + karşılama sihirbazı (büyük iş, 2–3 oturum)

### 2a. Veri yolları taşınması

- [ ] Veri kökünü `data_root()` fonksiyonuna topla: geliştirmede proje klasörü, kurulu sürümde `%LOCALAPPDATA%\Dikte` (ayrım: `--gelistirme` bayrağı veya paket göstergesi).
- [ ] İlk paketli açılışta eski proje klasöründeki `data/` tek seferlik taşınır; taşınmadan önce yedek klasörü alınır.
- [ ] pytest: yol çözümleme, taşıma, yedek.

### 2b. İlk açılış karşılama sihirbazı (yeni kapsam, 2026-11-04 kararı; tasarım kullanıcı onaylı)

**Tasarım kaynağı (kullanıcı onaylı, 2026-11-04):** `design/v2/karsilama-sihirbazi-taslak.html` — 5 ekranın açık temalı taslağı; dosyanın içinden `html.dark` sınıfıyla karanlık hali de denenir. Uygulama bu taslağa sadık yapılır; Magic UI fikirleri: DotPattern zemin, MagicCard fare ışığı, ShineBorder indirme çerçevesi, üstte adım göstergesi (dolgu çizgili stepper).

Geliştirme modunda ilk açılışta da gösterilir; `settings.json`'da `setup_done` işaretiyle bir kez çalışır.

Ekranlar (tek pencere içinde adım adım, ileri/geri butonları; taslaktaki metinler kullanılır). **Animasyonlar:** taslaktaki tüm Magic UI animasyonları sihirbazda da aktiftir — kartlarda fareyi izleyen MagicCard ışığı, indirme çerçevesinde kayan ShineBorder, zeminde DotPattern ve adımlar arası yumuşak geçiş; `prefers-reduced-motion` ve Ayarlar → Görünüm'deki "Arayüz efektleri" anahtarı sihirbazda da geçerlidir.

1. **Hoş geldiniz:** "Dikte'ye hoş geldin" — Sağ Ctrl kısayolu tanıtımı, 3 kısa bilgi (çevirme yerel olur, veri çıkmaz, kurulum ~3 dk), ShineBorder bilgi çerçevesi, "Başla" + "Atla".
2. **Ses modeli seçimi:** "Hangi model dinlesin?" — 6 model kartı (tiny önerilen rozetli: ~75 MB çok hızlı; base, small, medium, large-v3, large-v3-turbo). İndirme sihirbazın içinde başlar, ilerleme gösterilir; "sonra indir" ile atlanabilir.
3. **GPU / CUDA bileşeni:** "NVIDIA kartı bulundu" — GPU tespit edilir; varsa CUDA bileşenleri (~600 MB) ShineBorder + ilerleme çubuğuyla isteğe bağlı indirilir (duraklat/iptal dahil); CPU modu alternatifi "daha az indirme" rozetiyle listelenir. Atlanabilir; Ayarlar'dan sonra da kurulabilir.
4. **Metin sağlayıcı seçimi:** "Metni kim düzenlesin?" — Yok (önerilen, tam gizlilik) / Yerel GGUF / OpenRouter (ücretli rozeti). OpenRouter seçilirse maskeli anahtar alanı + "metin internete gider" uyarısı; Yerel seçilirse metin modeli seçimi + indirme. Hepsi atlanabilir — sonra Ayarlar'dan seçilir.
5. **Bitiş:** "Her şey hazır" — seçim özeti (model, CUDA, sağlayıcı, kısayol) + "SENİN YAPACAĞIN TEST" kartı (Sağ Ctrl denemesi) + "Dikteye başla".

Davranış kuralları:

- Sihirbaz sırasında kısayol dinleyicisi çalışmaya başlamaz; bitişte başlar.
- Her adım atlanabilir; iptal/geri desteklenir; kapatırsa uygulama varsayılanlarla devam eder (`setup_done` yine yazılır).
- Arayüz: mevcut HTML/CSS/JS içinde yeni `#sayfa-kurulum`; tasarım `design/v2/ui-spec.md`'ye ek bölüm olarak yazılır (MagicCard/DotPattern uyumlu, karanlık mod destekli).

### 2c. Tek kurucu exe: çift tıkla Program Files'a kurulum

Kullanıcı kararı (2026-11-04): kurulum normal bir Windows programı gibi olmalı — tek exe çift tıklanır, Program Files altına kurulur, Python yoksa kurucu gerekli ortamı kendisi kurar. Bunu sağlayan iki yol yukarıdaki "Kurulum ve Python notu"nda tanımlıdır (A: Python gömülü tek exe; B: Python'suz kurucu + otomatik Python kurulumu). Uygulama sırasında önce Yol A denenir, patlarsa Yol B'ye geçilir.

- [ ] `dikte.spec` (PyInstaller onedir; Yol A — Python gömülü, CPU-only; CUDA bileşenleri paketlenmez — kullanıcı isterse sihirbazdan indirir).
- [ ] `installer/dikte.iss` (Inno Setup 6): tek exe, çift tıkla kurulur; varsayılan kurulum yeri `C:\Program Files\Dikte` (x64 sistemde `Program Files`), değiştirilebilir; yalnız yönetici hakları isteyen kurulumda Inno'nun `PrivilegesRequired=admin` ayarı kullanılır, güncelleme akışı sessiz çalışır.
- [ ] **Yol B yedeği:** kurucu açılışta Python 3.12 varlığını denetler; yoksa resmi kurulumu sessiz indirip kurar, sonra paketi açar. Yalnız Yol A başarısız olursa devreye alınır.
- [ ] Kurucu çıktısı: `dist/Dikte-Setup-vX.Y.Z.exe`; boyut ve SHA-256 yazılır.
- [ ] Ayarlar sayfasına büyük kırmızı "Uygulamayı Kaldır" bölümü: çift onay, ikinci onayda silinecek boyut, Inno kaldırıcıyı sessiz çalıştırma; geliştirme modunda pasif ("Bu sürüm kurulumla gelmedi").
- [ ] pytest: kaldırma onay akışı, boyut hesabı. Playwright: sihirbaz ekranları + Ayarlar butonu.
- **SENİN YAPACAĞIN TEST:** kurucuyu çalıştır → uygulama %LOCALAPPDATA%'ya kurulur → kaldır; kısayol ve modeller klasörünün silindiğini gözle kontrol et.
- **Zayıf nokta:** PyInstaller'da pywebview + faster-whisper yolları patlayabilir; çözülmezse v1.5 "kurucu önce, kaldırma sonra" diye bölünür.

**Dikkat — eski karar çelişkisi:** AGENTS.md'de 2026-11-01'de onaylanan "kurulum kullanıcı bazlıdır, yönetici izni istemez" kararı ile yeni karar (Program Files'a kurulum) çelişiyor. Program Files'a yazma genelde yönetici izni ister. Bu oturumda yalnız plan yazıldığından karar değişikliği AGENTS.md'ye henüz işlenmedi; uygulama oturumunda kullanıcıya netleştirilir: Program Files (yönetici ister, standart program) mi, yoksa eski karar (`%LOCALAPPDATA%\Programs\Dikte`, izin istemez) mi? İkisi de Inno Setup'ta tek satır değişikliği.

## Adım 3 — v1.6 otomatik güncelleme (orta iş, 1–2 oturum)

- [ ] GitHub Releases akışı: sürüm etiketi `vX.Y.Z`, varlıklar = kurucu exe + `latest.json` (sürüm, exe bağlantısı, SHA-256, yayın tarihi) + SHA-256 checksum dosyası.
- [ ] `update.py`: açılışta sessiz sürüm denetimi (Kara yoksa 30 sn gecikmeli; `check_updates` ayarı ile kapatılabilir) → yeni sürüm varsa Ayarlar'da rozet.
- [ ] Ayarlar'da "Güncelleme" kartı: güncel sürüm, mevcut sürüm, "Uygulamayı Güncelle" butonu.
- [ ] Güncelleme akışı: kurucuyu indir (ilerleme) → SHA-256 doğrula → Inno `/SILENT` çalıştır → uygulama kapanır → kurulum bitince yeniden açılır.
- [ ] Hata durumları: ağ hatası, SHA uyuşmazlığı, indirme yarıda kesilme → Türkçe uyarı; uygulama çalışmaya devam eder; yarım indirme `%TEMP%\dikte\` altında tutulur ve silinebilir.
- [ ] pytest: sürüm karşılaştırma, SHA doğrulama (sahte dosya), akış durum makinesi. Playwright: kart ve buton durumları.
- **SENİN YAPACAĞIN TEST:** gerçek güncelleme turu (eski kurucudan yenisine) — ben sahte `latest.json` ile uygulanabilir akışı test ederim, gerçek indirmeyi sen onaylarsın.
- **Zayıf nokta:** kurucu boyutu (kurucu ~200 MB) her güncellemede indirilir; artımlı yama şimdilik yok — rapora/uyarıya boyut bilgisi eklenir.

## Adım 4 — Bitiş

- [ ] Tüm testler: `pytest -q` + `python -m dikte --selftest` + Playwright.
- [ ] `/asama-bitir`: STATE.md, architecture.md, PLAN.md, AGENTS.md, ogrenme-gunlugu.md güncelle; commit + push (repo public → push öncesi gizli bilgi son kontrolü).
- [ ] Kullanıcıya 5 maddelik sade özet.

## Sıralama ve maliyet özeti

| Adım | İş | Bağımlılık |
| :--- | :--- | :--- |
| 0. Public kontrol | Küçük | — (depo zaten public) |
| 1. 7e kalite tablosu | Orta | — |
| 2. v1.5 kurucu + sihirbaz + kaldırma | Büyük | 0 |
| 3. v1.6 güncelleme | Orta | 2 (kurucu dosyası gerekir) |
| 4. Bitiş | Küçük | hepsi |

Para maliyeti: yok (tümü yerel; OpenRouter kullanılmaz).
