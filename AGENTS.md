# AGENTS.md — Dikte projesi

Bu dosya projenin kalıcı hafızasıdır. Her oturumun başında `/asama-baslat` skill'ini çalıştır (olmazsa bu dosyayı, STIL.md, STATE.md ve PLAN.md'yi oku).

## Proje
Dikte: Windows masaüstü sesli dikte uygulaması. Sağ Ctrl basılı tutulur, konuşma kaydedilir, bırakılınca faster-whisper ile yazıya çevrilir; metin isteğe bağlı olarak temizlenip Türkçe/İngilizce/Almanca çıktıya çevrilir. Arayüz: pywebview + HTML/CSS/JS.
Hedef: design/ klasöründeki tasarıma uygun 4 sayfalı uygulama (Dikte, Dikte Geçmişi, Modeller, Ayarlar). v1–v1.6.0 tamamlandı; 2026-11-18'de **v1.6.1** (OpenWhispr analizi, `error_reporter.py` gömülü hata tespit/log kopyalama aracı, Faz A/B stabilite sertleştirmesi ve `Dikte.spec` `faster_whisper` paketleme düzeltmesi) tamamlandı (**369 passed, 1 skipped**). Kurucu `installer\Output\Dikte-Setup-1.6.1.exe` derlendi ve paketli selftest çıkış kodu 0 ile doğrulandı.

## Dosyalar
| Dosya              | Ne için                                                                                                                        |
| :----------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| AGENTS.md          | Kurallar ve onaylı kararlar (bu dosya)                                                                                         |
| PLAN.md            | Yol haritası                                                                                                                   |
| UYGULAMA-PLANI.md  | v1.3–v1.6 için dosya/sayfa düzeyinde uygulama sırası (olabilir.md'yi koda eşler)                                               |
| STATE.md           | Güncel durum, sıradaki adım, çalıştırma komutları                                                                              |
| architecture.md    | Kod haritası                                                                                                                   |
| ogrenme-gunlugu.md | Kullanıcının öğrendikleri                                                                                                      |
| STIL.md            | Ajanın konuşma tarzı                                                                                                           |
| design/            | Tasarımın tek kaynağı (görseller, ui-spec.md, prototype.html)                                                                  |
| reports/           | Araştırma raporları (README.md dizin)                                                                                          |
| .agent/skills/     | `asama-baslat`, `asama-bitir`, `proje-baslat`, `belirsizleri-sor` vb. Antigravity yetenekleri                                  |
| promptlar.md       | Kullanıcının istem notları (ajan okumaz)                                                                                       |
| olabilir.md        | v1.3-v1.5 ayrıntılı istek ve davranış spesifikasyonu (ne nerede, nasıl çalışır)                                                |
| calisma-duzeni.md  | **Zorunlu plan/denetim düzeni:** keşif → doküman → 4 paralel salt-okunur alt ajan → sentez → rapor → doğrulama                 |
| web/               | Next.js 16 + shadcn + Magic UI denemesi (AnimatedList, BentoGrid, AnimatedThemeToggler); yalnız referans, üretim arayüzü değil |
| video/             | Remotion tanıtım videosu kaynak projesi (45 sn, 1080p, 7 sahne + sentezlenen WAV ses kiti)                                     |

## Kullanıcı
- Kodlamaya yeni başlıyor. Sade Türkçe ile konuş, terimi bir cümleyle açıkla.
- Önce çalışan araç istiyor, öğrenmeyi zamanla ekliyor.

## Ortam ve bütçe
- Windows, proje Masaüstü\dikte projesi klasöründe (OneDrive dışı). Laptop: RTX 5060, 8 GB VRAM.
- `.venv` Python 3.12.10 ile çalışıyor (2026-10-27'de geçildi).
- Bütçe yaklaşık 10 dolar (OpenRouter). Yazıya çevirme kendi bilgisayarında yapılır; metin temizleme/çeviri için OpenRouter isteğe bağlı ve ücretlidir.

## Çalışma kuralları
- Kod yazmadan önce kısa plan çıkar ve planı sorgula: hangi varsayım yanlışsa plan çöker? Kullanıcı onaylamadan kod yazma.
- Küçük adımlarla ilerle. Bir seferde tek şey yap.
- Araştırmayı Exa ile yalnızca gerektiğinde yap. Ham sonucu reports/ altına kaydet, sohbete kısa özet ver, reports/README.md'ye tek satır ekle.
- API anahtarı koda, nota ya da rapora yazılmaz. OpenRouter anahtarı Ayarlar'da girilir ve Windows DPAPI ile şifrelenmiş saklanır; `.env` yalnız geliştirme sırları içindir.
- Model dosyaları models\ klasörüne iner (git dışı).
- Karar ile öneriyi ayır. Kararlar'a yalnızca kullanıcının onayladığı şeyler girer.
- Hata olursa aynı komutu tekrarlama. Eksik bilgiyi bul, ekle, öyle yeniden dene.
- Commit ve push yalnızca `/asama-bitir` çağrıldığında ya da kullanıcı açıkça isterse yapılır.

## Plan ve denetim düzeni (zorunlu)
- Plan, denetim veya "eksik / yarım / hata" çıkarımı yaparken **`calisma-duzeni.md` zorunludur**; aşamalar atlanmaz: keşif → doküman okuma → paralel salt-okunur swarm işçileri → sentez + çapraz doğrulama → rapor → doğrulama.
- Her bulgu `önem | dosya:satır | kısa alıntı | neden yanlış | somut düzeltme` biçiminde yazılır. Kanıtsız iddia rapora veya plana girmez; doğrulanamayanlar ayrı başlıkta toplanır.
- Doküman iddiası kanıt sayılmaz. En kritik 3 iddia kod satırından bizzat doğrulanır; test sahtesi bir hatayı gizliyorsa bu ayrıca "test maskesi" olarak yazılır.
- Çıktı sırası: blocker → yüksek → orta → düşük; sonunda fazlı düzeltme planı, kabul ölçütleri ve doğrulanamayanlar bölümü.

## Ajan ve Swarm Çalışma Düzeni
- **Tek Ajan Önceliği:** İş dallanmıyorsa, kolaysa veya tek bir ajanın yapması daha uygunsa alt ajan ya da swarm çağrılmaz; ana ajan görevi doğrudan kendisi tamamlar.
- **Paralel İş Bölümü (`swarm`):** İş gerçekten bağımsız kollara ayrılıyorsa yerleşik `swarm` aracı ile ortak mesaj panosu (Swarm Board) üzerinden yürütülür. Başlamadan önce dosyalar çakışmayacak şekilde bölünür (her işçiye özel dosya sahipliği); iki ajanın aynı anda aynı dosyayı düzenlemesine izin verilmez.
- **Alt Ajan / İşçi Modeli:** Alt ajanlar ve swarm işçileri **Gemini 4 Hydrogen** (`gemini-4-hydrogen-low` / `medium` / `high` / `xhigh`) ile çalıştırılır; düşünme seviyesi işin zorluğuna göre serbestçe belirlenir. Zorunlu olmadıkça başka model seçilmez.
- **Kritik Hata Danışmanı (`Claude Opus 5.5 Medium`):** Ana ajanın kendi başına çözemediği aşırı kritik bir hata veya düğüm çıkarsa `claude-opus-5-5-medium` alt ajan olarak çağrılabilir. **Kesin sınır:** Opus 5.5 Medium asla kod yazmaz, uzun dosyaları analiz etmez; yalnızca söz konusu kritik hatanın nasıl çözüleceğini söyler, başka bir şey söylemez.
- **Pano ve Yaşam Döngüsü:** Swarm kullanıldığında işçiler işini bitirince `@verifier` ve `@coordinator`'ı etiketler. Koordinatör `swarm_wait` ile bekler, `read_board` ile denetler, doğrulama sonrası `swarm{action:"kill"}` ile işçileri kapatır. Plan dosyası, swarm kullanıldıysa bunu başında yazar.

## Soru sorma
- Soru sormak için `question` aracını kullan.
- Süreci kolaylaştırmak için bana her türlü soruyu sormaktan çekinme. İHTİYACIN OLAN HER ŞEYİ SOR! Netliğe ulaşmak için gerektiği kadar takip sorusu sor.

## Test ve bitti tanımı
- Kod yazınca çalıştır, çıktıyı oku, düzelt. En fazla 3 deneme. Çözülmezse dur, STATE.md'ye yaz, kullanıcıya sor.
- Mantık için pytest, motor için `python -m dikte --selftest`, arayüz için Playwright (ekran görüntüsü + DOM testi). Testler tests/ altında.
- Ekran görüntüsünü design/ ile karşılaştır. Görüntü okuyamıyorsan ui-spec.md'deki değerleri DOM testiyle kontrol et.
- Mikrofon, kısayol ve başka pencereye yapıştırma gibi ajanın doğrulayamadığı şeyleri "SENİN YAPACAĞIN TEST:" başlığıyla yaz. Kullanıcı test etmeden "çalışıyor" deme.
- Görev şu üçü olmadan bitmiş sayılmaz: çalışan sonuç, kanıt (çıktı/test/dosya), kullanıcı için 5 maddelik sade özet.

## Teknik dikkat noktaları
- GPU'da compute_type="auto" RTX 5060'ta çöküyor, float16 kullan. Mod (GPU/CPU) ekranda yazsın. GPU çökerse aynı model CPU/int8, o da olmazsa small + int8.
- CUDA için nvidia-cublas-cu12 ve nvidia-cudnn-cu12 kurulu, DLL yolu `diagnostics` içinde eklenir.
- **PyAV `>=11,<16` sabit.** PyAV 16+ `av.open(metadata_errors=...)` parametresini kaldırdı; faster-whisper 1.2 çevirisi bu yüzden çöküyordu.
- Türkçe karakterleri (ı, ğ, ş, ç, ö, ü) her testte dene. Konsol UTF-8.
- Sessiz kayıtta Whisper sahte cümle üretebilir: vad_filter açık, 0,4 sn altı kayıt atlanır.
- Gizlilik: kaynak .wav çeviriden sonra silinir. Son kayıt, "Transkripsiyonu Yenile" için `%TEMP%\dikte\last.wav` olarak tutulur; yeni diktede üzerine yazılır, uygulama kapanınca silinir. Konuşulan metin loga yazılmaz; metin yalnız `data/history.json` içinde ve "Geçmişi kaydet" açıksa durur.
- Kısayol pynput ile dinlenir. Varsayılan Sağ Ctrl. Başka tuş basılıyken kayıt sürer (kabul edilmiş sınırlama).
- GPU belleğini kullanan başka program (LM Studio gibi) açıkken test etme.

## Maliyet
- Büyük dosya ya da uzun log baştan sona okunmaz, ilgili satırlara bakılır.
- Sorun 3 denemede çözülmezse dur ve söyle. Daha güçlü model gerekiyorsa öner.

## Öğretme kuralları
- Her adımdan önce 2-3 cümleyle ne yapacağını ve nedenini söyle. Yeni terimi bir cümleyle aç, komutun ne yaptığını söyle.
- Benim yapmam gereken bir şey varsa "SENİN YAPACAĞIN ŞEY:" başlığıyla adım adım yaz.
- Adım sonunda "Kendin dene" ekle: kodda tek değeri değiştirip sonucu görebileceğim küçük bir deney.
- Açıklamalar kısa olsun.

## Kararlar (kullanıcı onaylı)
- Dil: Python 3.12.10. Yazıya çevirme: faster-whisper, yerel.
- Model: GPU çalışırsa seçili model + float16, çökerse aynı model CPU/int8, olmazsa small + int8.
- Ses modeli listesi (6 adet): tiny, base, small, medium, large-v3, large-v3-turbo. İndirme, aktifleştirme ve silme uygulama içinden yapılır; aktif model `settings.json`'da saklanır. v1.3'te Metin Modelleri ayrı sekme olarak eklenir.
- Metin modeli listesi (4 adet): `qwen3-1.7b`, `qwen3-4b` (varsayılan), `gemma3-4b`, `llama32-3b`; Hugging Face'ten `.part` + Range ile indirilir, duraklat/devam/iptal vardır; çalıştırmak için `llama-cpp-python` gerekir.
- Kısayol: varsayılan Sağ Ctrl; ayarlardan hazır listeden seçilir (Sağ/Sol Ctrl, Sağ/Sol Alt, F8/F9/F10). v1.2'de çıktı yalnızca panoya; v1.3'te panoya + etkin pencereye otomatik yapıştırma.
- Geçmiş: son 500 kayıt `data/history.json`; ayarlarda kapatılınca yeni kayıt yazılmaz, eski kayıtlar gizlenir (arşivde kalır). Arama/filtre/Aç/Kopyala/Sil vardır.
- "Transkripsiyonu Yenile" son kaydın sesini tekrar çevirir, son paragrafı değiştirir. Ses `%TEMP%\dikte\last.wav` olarak yalnız uygulama açıkken tutulur.
- Kod yazan model: OpenRouter üzerinden (seçim ve gerekçe STATE.md'de, değişirse orada güncelle).
- Hafıza: Obsidian vault = proje klasörü. Yedek: özel GitHub deposu.
- Tasarım: design/ tek kaynak. Aktif model kartında işleme hızı yok. Görsel model kategorisi yok.
- v1.2 kapsamı: Geçmiş (tam), Modeller (ses, tam), Ayarlar (kısayol + geçmiş anahtarı), Yenile. Dil ve mikrofon seçimi yok.
- Arayüz: pywebview + prototype.html'den türetilen HTML/CSS/JS.
- **v1.3 kapsamı (2026-11-01 onaylı):** Çıktı dili Türkçe/İngilizce/Almanca; "Otomatik çevir" kutusu dil seçicisinin yanında; "Yapay Zeka ile Temizle" ve "Çevir" butonları aynı satırda.
- Aynı dilde yalnız temizlik yapılır, çeviri yapılmaz. 3 kelimeden kısa metinde çeviri yapılmaz, ham metin kalır.
- Dil kararını metin modeli tek çağrıda verir; Whisper dili otomatik algılar. Türkçe doğruluğu düşerse girdi dili Türkçe'ye sabitlenebilir.
- Metin modeli iki sağlayıcı: uygulama içi GGUF (llama.cpp) ve OpenRouter. OpenRouter anahtarı **Ayarlar sayfasındaki ayrı bir "OpenRouter API anahtarı" alanından** girilir (gizli yazı, Kaydet/Sil/Test et), Windows DPAPI ile şifrelenir; varsayılan liste ucuz/küçük modellerdir, "Tüm modelleri göster" açılınca katalogdaki herhangi bir model aranıp seçilebilir; sistem promptu düzenlenebilir.
- Ses ve metin modeli aynı anda bellekte tutulmaz: VRAM'den boşaltıp takas edilir; gerekirse CPU/RAM kullanılır.
- Modeller sayfası Metin/Ses sekmeleri; her modelde "⋯" menüsü; indirmede duraklat/devam/iptal.
- **v1.4 kapsamı (onaylı):** Magic UI esintili yeni arayüz, Next.js'e geçmeden mevcut HTML/CSS/JS içinde CSS uyarlaması. Karanlık mod: Sistem/Açık/Koyu. Tema düğmesi sağ panelde "Aktif model" kartının hemen üstünde; Magic UI AnimatedThemeToggler davranışı (View Transitions API + circle clip-path, 400 ms). Ayrıntı `UYGULAMA-PLANI.md` §11.
- **v1.5 kapsamı (onaylı):** PyInstaller + Inno Setup kurucu; veriler `%LOCALAPPDATA%\Dikte`; kısayollar; isteğe bağlı otomatik başlatma. Ayarlar'da büyük kırmızı "Uygulamayı Kaldır" butonu, çift onay, tüm verileri siler.
- **v1.6 kapsamı (2026-11-01 onaylı):** Otomatik güncelleme. Açılışta sessiz sürüm denetimi (kapatılabilir); Ayarlar'da "Güncelleme" kartı ve "Uygulamayı Güncelle" butonu; `latest.json` (sürüm, kurucu bağlantısı, SHA-256) → indirme → özet doğrulama → Inno Setup kurucusunu sessiz çalıştırma → yeniden açılış. Ağ/indirme hatasında Türkçe uyarı, uygulama çalışmaya devam eder. **Yayın yeri 2026-11-04'te GitHub Releases olarak seçildi; `config.UPDATE_URL` henüz doldurulmadı.**
- **Metin sağlayıcısı varsayılanı `none` (2026-11-01 onaylı):** İlk açılışta Temizle/Çevir kapalı; kullanıcı Ayarlar → Yapay Zeka'dan Yerel veya OpenRouter seçmeden çalışmaz. Otomatik yapıştırma varsayılan açık.
- **Açık tema (2026-11-01 onaylı):** Zemin `#F7F9FD`, kart `#FFFFFF`, ana yazı `#101828`, vurgu `#3D5BF5`; tema düğmesi `Aktif model` kartının üstünde, View Transitions + circle clip-path (400 ms).
- **Kurucu paketi (2026-11-01 onaylı):** Tek CPU kurucu; CUDA bileşeni paketlenmez. Karşılama sihirbazı yalnız NVIDIA GPU varsa CUDA bileşenini isteğe bağlı indirir (2026-11-07).
- **Goal bölünmesi (2026-11-01 onaylı):** İlk koşu parti 1–5, sonra 6–10, sonra 11–13; her koşu sonunda test kanıtı ve kullanıcı testi.
- **llama-cpp-python (2026-11-03 onaylı):** GPU whl (cu124) kuruldu; CUDA DLL yolları `diagnostics.prepare_cuda_dlls()` ile llama yüklemeden önce tanıtılır (`nvidia-cuda-runtime-cu12` requirements'a eklendi).
- **v1.4 efektleri (2026-11-03):** MagicCard/ShineBorder/AnimatedList/BentoGrid/DotPattern CSS+JS uyarlaması; Ayarlar → Görünüm'de "Arayüz efektleri" anahtarı (varsayılan açık); `prefers-reduced-motion` animasyonları kapatır. Ayrıntı `design/v2/ui-spec.md`.
- **Doküman senkronu (2026-11-07):** Yalnız plan/doküman güncellendi, kod değişmedi. Eski `uygulanacak plan.md` silinip denetim + doğrulanmış kod durumuna göre yeniden yazıldı.
- **Plan/denetim düzeni (2026-11-07 onaylı):** `calisma-duzeni.md` zorunlu; plan ve denetimler keşif → doküman → 4 paralel salt-okunur alt ajan → sentez → rapor → doğrulama sırasıyla yapılır.
- **Uygulama kararları (2026-11-07 onaylı):** Kurulum `C:\Program Files\Dikte` + admin; sürüm **1.6.0**; kaldırmada "Modelleri koru" seçeneği (Inno `[UninstallDelete]` + bayrak); PyInstaller + Inno Setup kurulacak; güncelleme GitHub Releases (yüklemeyi kullanıcı yapar); CUDA yalnız GPU varsa; selftest sentetik TTS; 7e tamamlanacak; `web/` notla tutulur; lisans MIT; basit `.ico` üretilir; eski `data/` taşınmaz.
- **Faz 1 uygulama onayı (2026-11-09):** `uygulanacak plan.md` Faz 1 kullanıcı tarafından onaylanıp uygulandı.
- **belirsizleri-sor skill'i (2026-11-07):** Uygulamadan önce plan/dokümanlardaki tüm açık kararlar tek turda kullanıcıya sorulur; doğrulanabilir bilgiler ajan kendin doğrular; cevaplar plana işlenir.
- **2026-11-11 kararları (kullanıcı onaylı):**
  - Faz 1 testi: Kullanıcı önce `installer\Output\Dikte-Setup-1.6.0.exe` kurulum/kaldırma testini yapacak. Yeni oturumda `/asama-baslat` ile başlanacak; model ne yapacağını/yapmayacağını, testleri ve alt ajan kurallarını detaylı listeleyecek, kullanıcı onay vermeden kod yazmayacak.
  - Faz 2 düzeni: 11 veri kaybı ve çökme maddesi tek seferde arka arkaya uygulanacak.
  - Karşılama sihirbazı CUDA: İsteğe bağlı olacak ("İndir" veya "CPU ile devam et / Atla").
  - Ses modeli indirme: faster-whisper yapısı için yalnız "İptal" butonu sunulacak.
  - Selftest sesi: 3 saniyelik sentetik Türkçe ses ("Dikte test kaydı başarılı.") ve `test.txt` üretilecek.
  - Alt ajan (sub-agent) kuralı: Alt ajanlar her zaman `gemini-3.8-flash-medium` (`Model: "flash"`) ile çağrılır. Kolay ama uzun kodlama görevlerinde ve çeşitli test koşumlarında bu alt ajan kullanılır. Aşama sonunda tüm işler bitince yine aynı alt ajan çağrılarak modellerin/kodun neleri yapıp neleri yapmadığı denetlenir ve ana ajana raporlanır.
  - Faz 2 tamamlandı (2026-11-11): 11 veri kaybı ve çökme maddesi TDD ile uygulandı (**263 passed, 1 skipped**) ve `Model: "flash"` alt ajanıyla denetlendi.
  - Masaüstü kısayolu ve sistem tepsisi (2026-11-11): Masaüstüne `Dikte.lnk` kısayolu eklendi; uygulamanın sistem tepsisine (System Tray) küçültülmesi ve pencere kapalıyken arka planda çalışmaya devam etmesi Faz 3.2 kapsamına alındı.
- **2026-11-12 kararları (kullanıcı onaylı):**
  - **Model/Ajan İş Bölümü:** Ana model yalnızca en zor mimari kararlar, kritik kilitler/algoritmalar ve üst düzey koordinasyon için çalışır; kolay ama uzun kodlar ve doküman özetleme/değiştirme işleri daima `/swarm` veya alt ajanlar (`gemini-3.8-flash-medium` / `Model: "flash"`) ile yürütülür. Gerekli durumlarda çoklu alt ajan aynı anda paralel çağrılır.
  - **Tasarım Dili Seçimi:** Ayarlar → Görünüm'de kullanıcının Klasik Magic UI (v1.4) veya Sade Dikte.AI (`design/dikte-ai.html`) tasarım dilini seçebilmesi sağlanır.
  - **Animasyon & Morfizm:** Dikte alanına `design/mikrofon_morph_animasyonu.html`'deki ses dalgası ve morflayan mikrofon animasyonu entegre edilir.
  - **Serbest Kısayol:** Bas-konuş için 1, 2 veya 3 tuşlu serbest kombinasyon (ör. `Ctrl+Shift+D`, `Alt+Space`) atanabilir; uygulama sistem tepsisindeyken de global olarak çalışır.
  - **Sistem Tepsisi & Gizli Başlangıç:** Windows ile başladığında sessizce tepside başlar; `X` butonuna basıldığında tepsiye küçülür.
  - **Hugging Face Desteği:** Modeller sayfasına hem ses hem metin için harici Hugging Face modeli ekleme/indirme alanı eklenir.
  - **Ayarları Otomatik Kaydetme & Rollback:** Ayarlar menüsündeki tüm değişiklikler anında kaydedilir; Güncelleme kartında eski sürümlere tek tıkla geri dönülebilir.
  - **belirsizleri-sor Nihai Kararları:**
    - **Varsayılan Tasarım Modeli:** Varsayılan arayüz tasarım modeli `Sade Dikte.AI + Mikrofon Morph` (`design_style = "dikte_ai"` varsayılan; Ayarlar → Görünüm'den `"classic"` Magic UI v1.4 seçilebilir; her iki modda da Dikte ana mikrofon alanında `design/mikrofon_morph_animasyonu.html` canvas dalga + morphing mikrofon yer alır).
    - **Hugging Face Özel Modeller Saklama ve Yönetimi:** Eklenen özel modeller `data/custom_models.json` dosyasında kalıcı saklanır; model kartında "Sil" dendiğinde diskteki dosya silinir ama kart listede kalır; kartın "⋯" menüsünde ayrıca "Listeden Kaldır" seçeneği bulunur.
    - **Faz 5.2 Kapsamı, Selftest ve Dağıtım Sınırları:** Bu oturumda Faz 3, Faz 4 ve Faz 5.1 kodlarının tamamı yazılıp `build.ps1` ile güncel `Dikte-Setup-1.6.0.exe` derlenecek; sentetik test sesi (`tests/data/test.wav` + `test.txt`) ile otomatik selftest ve paketli açılış testi doğrulanacak. Gerçek VM testi ve GitHub Release yüklemesi kullanıcıya bırakılacak.
    - **Logo, Sistem Tepsisi ve Menü Yapısı (Ajan Kararları):** Yeni logo kaynağı `design/download` (ses dalgalı mavi ikon) alınarak `.ico` ve `.png` üretilir; sistem tepsisi `pystray + Pillow` ile kurulur; tepsi menüsü `Göster/Gizle | Durum | Çıkış` olur.
    - **Tek Kopya Kilidi ve Win32 Pencere İkonu (2026-11-12, 2. Oturum):** Uygulamanın birden fazla kopyasının çalışması ve çift sistem tepsisi ikonu oluşması `dikte/instance.py` içindeki Windows Named Mutex (`Local\DikteSingleInstanceMutex`) ile engellenir; ikinci kopya ilk pencereyi öne getirir. Görev çubuğu ve pencere başlığında Python logosu yerine `assets/icon.ico` görünmesi için Win32 `SetCurrentProcessExplicitAppUserModelID` ve `WM_SETICON` kullanılır.
    - **Birebir Mikrofon Morph Animasyonu & Tasarım Modları (2026-11-12, 2. Oturum):** Dikte ekranında `design/mikrofon_morph_animasyonu.html`'deki 48 barlık canvas dalgası, halo halkaları ve morph animasyonu birebir korunur; `dikte_ai` (tek sütun ferah) ve `classic` (2 sütunlu sağ panel, alt çubuk) görünümleri Ayarlar → Görünüm'den dinamik olarak değiştirilebilir.
- **2026-11-13 kararları (kullanıcı onaylı):**
  - **Tek Ajan Önceliği:** İş dallanmıyorsa, kolaysa veya tek ajanın yapması daha uygunsa alt ajan/swarm çağrılmaz; ana ajan işi kendisi tamamlar.
  - **Alt Ajan Modeli (Gemini 4 Hydrogen):** Alt ajan ve swarm işçileri artık `gemini-3.8-flash-medium` yerine **Gemini 4 Hydrogen** (`gemini-4-hydrogen-low`/`medium`/`high`/`xhigh`) kullanır; düşünme seviyesini ajan/koordinatör belirler.
  - **Kritik Hata Danışmanı (Opus 5.5 Medium):** Ana ajanın çözemediği aşırı kritik hatalarda `claude-opus-5-5-medium` çağrılabilir; asla kod yazmaz, uzun dosya analiz etmez, yalnızca hatanın nasıl çözüleceğini söyler.
- **2026-11-18 kararları (v1.6.1, kullanıcı onaylı):**
  - **Gömülü Hata Tespit Aracı & Faz A/B Stabilite:** `dikte/error_reporter.py` + `RotatingFileHandler` + `faulthandler` + `running.lock` + gizlilik maskelemesi + arayüz/tepsi entegrasyonu ve Faz A/B kilit/hook/ses/güncelleme düzeltmeleri uygulandı; sürüm `1.6.1`'e çıkarılıp kurucu (`Dikte-Setup-1.6.1.exe`) derlendi.
- **2026-11-19 kararları (v1.6.1 canlı yayın, kullanıcı onaylı):**
  - **Vitrin & GitHub Pages:** `README.md` yenilendi; `docs/index.html` üzerinden mobil/tablet/masaüstü uyumlu ücretsiz indirme sitesi (`https://mete2012seker-lgtm.github.io/dikte/`) açıldı.
  - **GitHub CLI (`gh`) Yayını:** Bilgisayara `GitHub.cli` kuruldu; bundan sonraki sürümlerde ajan kullanıcı onayıyla `gh release` üzerinden doğrudan yayın yapabilir.
  - **`onnxruntime` Erken Yükleme & VAD Yedeği:** Paketli uygulamada Windows DLL bellek sınırını aşmak için `onnxruntime` giriş noktasında erken yüklenir; yine de hata olursa `engine.py` otomatik `vad_filter=False` ile devam eder.
- **2026-11-20 kararları (tanıtım videosu, kullanıcı onaylı):**
  - **Remotion Tanıtım Videosu (`video/`):** Klavyeyle yazmanın zorluğuna karşı sesle daha hızlı/akıcı ifade etmeyi, bas-konuş mikrofon morfizmini, AI temizle/çevir ve Magic UI geçişlerini anlatan 45 sn 1080p video üretildi; web için optimize MP4 (`docs/assets/dikte-tanitim.mp4`) GitHub Pages (`docs/index.html`) ve `README.md` alt bölümüne eklendi.
- **2026-11-21 kararları (çok dilli vitrin, kullanıcı onaylı):**
  - **İngilizce Varsayılan README ve Web Sitesi:** `README.md` varsayılan İngilizce, `README.tr.md` Türkçe olup üstlerinde tıklanabilir `English | Türkçe` bağlantıları bulunur; `docs/index.html` varsayılan İngilizce açılır ve üst çubukta `EN | TR` dil seçici sunar.
- **2026-11-24 kararları (kod denetimi ve protokol güncellemesi, kullanıcı onaylı):**
  - **`asama-baslat` Güncellemesi:** Oturum başında önceki işlere ve kararlara bakmak için **Obsidian hafıza kasasını (`obsidian` MCP)** kontrol etmek zorunludur; alt aşamalar/alt ajanlar **Gemini 4 Hydrogen** ile çalıştırılır ve düşünme seviyesi (`low`/`medium`/`high`/`xhigh`) işin zorluğuna göre değiştirilebilir.
  - **v1.6.1 Tam Kod Denetimi:** Salt-okunur denetim tamamlandı (`reports/2026-11-24-kod-denetimi-raporu.md`); kod değişikliği yapılmadı, 4 fazlı düzeltme/kısaltma planı bir sonraki oturumda kullanıcı onayıyla başlatılacak.
- **2026-11-25 kararları (yayın/tanıtım yönü, kullanıcı onaylı):**
  - **Hedef ve Kapsam:** Gelir amacı yok; ~1.000 kullanıcı/indirme yeterli, süre sınırı ve abartılı büyüme kampanyaları yok. Odak, genele hitap eden basit dokunuşlar ve sıfır bütçeli sade tanıtım fikirleri (`reports/2026-11-25-yayin-ve-buyume-raporu.md`). Bu oturumda yalnızca araştırma ve kayıt yapıldı.


## Öneriler (onaylanmadı)
- Metin modelleri: LM Studio/Ollama yerel sunucusuna bağlanmak, uygulama içi GGUF'a alternatif olarak değerlendirildi; 2026-11-01'de seçilmedi.
- Arayüz modernizasyonu (2026-10-31): iki yol değerlendirildi.
  - **Next.js'e taşıma:** Magic UI bileşenleri birebir kullanılır; ama çalışan arayüzü baştan yazdırır, `window.pywebview.api` köprüsü + build/paketleme + Playwright testlerinin yenilenmesi gerekir. Riskli ve masraflı.
  - **CSS/JS'e uyarlama:** Mevcut `index.html` + `style.css` + `app.js` korunur; animasyonlar CSS `@keyframes`/`transition` ve az JS ile elle yazılır. Hızlı, düşük riskli, çevrimdışı ve testler bozulmaz; ama Magic UI kodu birebir kullanılmaz, karmaşık animasyonlar zorlaşır.
  - **Seçim (2026-11-01):** CSS/JS uyarlaması. Next.js geçişi gerekirse ayrı aşama olarak ele alınır.

## Teyit bekleyen varsayımlar
- Pencere kapanınca uygulama çıkar, sistem tepsisi yok. Windows'un normal pencere çerçevesi kullanılır.
- Her dikte yeni paragraf ekler; Yenile son paragrafı değiştirir. Kopyala tüm metni, Geri Al son paragrafı alır.
- 0,4 sn'den kısa kayıt "Ses algılanamadı" diye atlanır.
- Geçmişte en fazla 500 kayıt tutulur; sınır aşılınca en eski kayıt düşer.
- İndirme duraklatma anlık değil: açık dosya parçası bitince durur. İptal, Windows dosya kilidi yüzünden gecikebilir.
- Girdi dili otomatik algılanır; Türkçe doğruluğu düşerse Ayarlar'a "Girdi dili: Türkçe" sabitleme eklenecek.
- Kurulum **Program Files**'a yapılır ve yönetici izni ister. Kaldırmada geçmiş/ayarlar/loglar/geçici dosyalar silinir; kullanıcı "Modelleri koru" seçeneğiyle modelleri bırakabilir.
- v1.4 efektleri kod tarafında tamamlandı (2026-11-03) ve kullanıcı tarafından gözle onaylandı (2026-11-04).
- llama.cpp ilk üretim çağrısı ~50 sn CUDA ısınması sürer; kabul edildi, gerekirse ön ısınma çağrısı eklenir.

## Kod yazma ilkeleri (Karpathy)
- Kodlamadan önce varsayımlarını açıkça söyle. Emin değilsen sor, sessizce seçme.
- İstenmeyen özellik, gereksiz soyutlama, "belki lazım olur" kodu yazma.
- Sadece istenen yeri değiştir. Yakındaki kodu/yorumları "düzelteyim" deme.
- Hedefi doğrulanabilir yap: "hatayı düzelt" → "hatayı üreten testi yaz, geçene kadar çalış".
