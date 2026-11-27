# Öğrenme Günlüğü

Bu dosyaya her oturumda öğrendiklerimi 3-5 maddeyle ekliyorum.

## 2026-10-24 — v1: çekirdek dikte + Dikte ekranı

1. **Sanal ortam (venv):** Projeye özel bir Python kutusu. Kurulan kütüphaneler bilgisayarın geri kalanını etkilemez; `.venv` klasörü silinip yeniden kurulabilir.
2. **GPU ve CUDA kütüphaneleri:** Ekran kartıyla çalışmak için sadece sürücü yetmiyor; `cublas` ve `cudnn` DLL'leri de gerekiyor. Bunlar venv'e kurulunca uygulama yollarını kendisi ekliyor; GPU yine çalışmazsa CPU'ya düşülüyor.
3. **pywebview:** Python uygulamasının içinde HTML/CSS/JS arayüzü açmayı sağlıyor. Arayüz, Python'a 250 ms'de bir sorarak durumu öğreniyor; böylece thread karışıklığı olmuyor.
4. **Gizlilik:** Ses kaydı geçici bir `.wav` dosyasına yazılıyor, çeviriden sonra siliniyor. Konuşulan metin log dosyasına yazılmıyor.
5. **Commit:** Bir aşama bitince `git add .` + `git commit` ile kaydediyoruz. Böylece yeni sohbette ajan dosyalardan devam edebiliyor.

## 2026-10-25 — Oturum protokolü ve doküman temizliği

1. **Skill:** Tekrar eden bir iş akışını (test → dosyaları güncelle → commit) tek bir `SKILL.md` dosyasına yazmak, her sohbette aynı adımların unutulmadan uygulanmasını sağlıyor.
2. **Commit ve push farkı:** Commit yalnızca bilgisayardaki yerel kaydı oluşturur; GitHub'da görmek için `git push` gerekir.
3. **Tek kaynak:** Aynı kuralı iki ayrı dosyada tutmak karışıklık yaratıyor. Protokol skill'e taşındıktan sonra eski `oturum-sonu.md` ve yardımcı not dosyaları silindi.
4. **STIL.md:** Ajanın nasıl konuşacağını (ton, yapı, hata anlatımı) yazılı hale getirmek, yeni sohbette tarzın değişmemesini sağlıyor.
5. **Güvenli commit:** Commit öncesi `git status`, sahne (staged) listesi ve gizli bilgi taraması yapmak; model/venv/log gibi büyük veya özel dosyaların yanlışlıkla git'e girmesini engelliyor.

## 2026-10-27 — v1.2: Geçmiş, Modeller, Ayarlar, Yenile

1. **Python sürümü ve paket uyumu:** Python 3.12'ye geçmek tek başına yetmiyor; kütüphanelerin birbirine uyan sürümlerini seçmek gerekiyor. PyAV 19 ile faster-whisper 1.2 çakıştı; `av<16` sabitleyince çeviri düzeldi.
2. **Kalıcı veri:** Ayar ve geçmiş gibi veriler `data/` klasöründe JSON olarak tutuluyor. Bozuk dosya uygulamayı çökertmiyor; `.bozuk-*` adıyla kenara alınıp boş listeyle devam ediliyor.
3. **Model yönetimi:** Bir modeli değiştirmek "eski modeli bellekten boşalt + yenisini yükle" demek. Aktif model silinemiyor; aksi halde uygulama açılışta modelsiz kalırdı.
4. **Gizlilik ve Yenile:** Ses, çeviriden sonra silinse de "Yenile" için son kayıt geçici olarak tutuluyor. Bu bilinçli bir ödünleşim: dosya uygulama kapanınca siliniyor, yeni diktede üzerine yazılıyor.
5. **Test katmanları:** Saf mantık pytest ile, arayüz Playwright ile, gerçek motor `--selftest` ile test ediliyor. Ağ, mikrofon ve kısayol gibi ajanın doğrulayamadığı şeyler kullanıcı testine bırakılıyor.

## 2026-11-01 — v1.3 planı: yapay zeka ile temizle/çevir

1. **Dil algılama iki ayrı iş:** Whisper sesi doğru yazmak için dili algılar; metin modeli ise yazılmış metne bakıp "çeviri gerekli mi" kararını verir. İkisi karıştırılırsa yanlış dilde yazılmış metin kurtarılamaz.
2. **Aynı dil kuralı:** Hedef dil ile konuşulan dil aynıysa çeviri yapılmaz, yalnızca yazım düzeltilir. Bu, gereksiz çeviri ve maliyeti önler.
3. **VRAM/RAM takası:** İki model aynı anda bellekte tutulmaz. Ses modeli boşaltılır, metin modeli yüklenir; iş bitince geri takas edilir.
4. **API anahtarı güvenliği:** Anahtar düz metin dosyada durmaz; Windows DPAPI ile şifrelenir. Böylece başka kullanıcı veya kopya bilgisayar anahtarı okuyamaz.
5. **İndirme duraklatma:** HTTP `Range` ve `.part` dosyası ile indirme kaldığı yerden devam eder. Bu yüzden "iptal" ile "duraklat" farklıdır: iptal yarım dosyayı siler.

## 2026-11-01 — metin modelleri, otomatik yapıştırma ve tema

1. **"Boş yanıt" hatası modelde değil ayarda olabilir:** Düşünen (reasoning) modeller muhakemeye token harcayıp metni boş bırakır. Token sınırını büyütmek ve yönlendirici (`openrouter/auto`) kimlikleri listeden çıkarmak sorunu çözdü.
2. **Modelin çıktısına güvenilmez:** Bazı modeller metnin başına "İşte çeviri:" gibi açıklama ekler. Kod, tırnak içindeki son metni çıkarır; ikinci denemede daha sert bir talimat gönderir.
3. **Çeviri kontrolü:** Çıktının hedef dilde olup olmadığı basit kelime ipuçlarıyla (tr/en/de) denetlenir. Yanlış dilde kalan yanıt kabul edilmez, tekrar denenir.
4. **`.part` + `Range`:** İndirmeyi duraklatmak, dosyayı kapatıp son baytı hatırlamak demektir; devam ederken sunucuya "buradan devam et" denir. Boyut uyuşmazsa dosya baştan indirilir.
5. **Tema geçişi:** `document.startViewTransition` + `clip-path: circle()` ile yeni tema düğmeden büyüyen daireyle açılır. Tarayıcı desteklemezse sınıf anında değişir; `prefers-reduced-motion` açıksa animasyon yapılmaz.
## 2026-11-04
- **Kalite tablosu:** Modelin kalitesini ölçmek için hazır sorularla toplu test yapıp tabloya geçmek demek; bugün Gemma 3 4B ile 10 cümlede 10/10 aldık.
- **Kurucu (installer):** Uygulamayı tek tıkla kurulan program yapan paket demek; PyInstaller kodu exe'ye topluyor, Inno Setup ise kurulum sihirbazı yapıyor.
- **Kaldırıcı (uninstaller):** Programı ve verilerini silen ayrı küçük program demek; Inno Setup bunu otomatik üretiyor.
- **Otomatik güncelleme:** Uygulama açılışta bir küçük dosyaya (latest.json) bakıp yeni sürüm var mı diye kontrol eder; indirilen dosyanın özeti (SHA-256) doğrulanmadan kurulmaz.
- **Kullanıcı testi:** Ajan kodu yazıp test edebilir ama kur/kaldır ve gerçek güncelleme ancak gerçek bilgisayarda senin denemenle kanıtlanır.

## 2026-11-09 — Faz 1: yayın hazırlığı (kurucu ve güncelleme)

1. **Tek kaynak ilkesi:** Sürüm numarası her yerde ayrı yazılınca (config, Inno, latest.json) birbirini tutmaz hâle geliyor. Bütün dosyalar tek bir değerden okunmalı; testler bu tutarlılığı kontrol eder.
2. **Özet (SHA-256) neden gerekli:** İndirilen dosyanın hash'i yayında yazılı değerle eşleşmezse yarım veya değiştirilmiş kurucu çalıştırılmaz. Boş özet bile reddedilir, çünkü "doğrulama yok" demek "güven yok" demektir.
3. **Kurucu ve geliştirme ortamı farkı:** PyInstaller uygulamayı tek klasöre toplar; giriş dosyasında göreli import (`from . import`) çalışmaz, bu yüzden küçük bir `run_dikte.py` başlatıcısı kullanılır.
4. **Kaldırmada veri ayrımı:** Program dosyaları (Program Files) ile kullanıcı verisi (%LOCALAPPDATA%) ayrı tutulur. Kaldırıcı programı siler; "Modelleri koru" bayrağı büyük modelleri (GB'lar) boşuna yeniden indirmeyi önler.
5. **Admin kurulum ve HKCU:** Yönetici izniyle kurulan programın kullanıcı kayıt defteri alanına (HKCU) yazması, kurulumu yapan hesapla aynı kişi değilse beklenmeyen yere düşer. Bu yüzden kayıt temizliği de kurulumu yapan kullanıcıyla test edilmeli.

## 2026-11-11 — Faz 2: veri kaybı, yarış durumları ve sağlamlaştırma

1. **Yarış durumu (race condition):** İki iş parçacığının (thread) aynı anda aynı veriye veya dosyaya dokunmasıdır. Örneğin aynı anda iki Whisper modelinin yüklenmesini ayrı bir motor kilidi (`_engine_lock`) ile, indirme çakışmalarını ise her indirmeye verilen sıra numarası (jeton) ile önledik.
2. **Bloklamayan kısayol kuyruğu:** Klavye dinleyicisi (`pynput`) içinde model yüklemek gibi saniyeler süren bir iş yapılırsa klavye kancası donar. Kısayol olaylarını (`press`/`release`) küçük bir kuyruğa alıp arka plan işçisinde çalıştırmak donmayı önler.
3. **Sihirli bayt (magic bytes) ve bütünlük:** Bir dosyanın sadece boyutunun tutması sağlam olduğu anlamına gelmez; GGUF model dosyalarının ilk 4 baytının `GGUF` olduğunu ve Whisper klasöründe `config.json` + `tokenizer` dosyalarının bulunduğunu kontrol ederek bozuk indirmeleri yakaladık.
4. **Atomik yazma ve `fsync`:** Dosyayı doğrudan ezmek yerine önce benzersiz adlı bir `.tmp` dosyasına yazıp `os.fsync` ile diske fiziksel olarak kaydedilmesini beklemek ve sonra `os.replace` ile yer değiştirmek, elektrik kesintisinde bile ayar/geçmiş dosyasının bozulmasını engeller.
5. **Kırpılan yanıt (`finish_reason == "length"`):** Yapay zeka modeli token sınırına çarpıp cümleyi yarıda kestiğinde yanıt boş olmasa bile eksiktir; bunu hata sayıp token bütçesini iki katına çıkararak yeniden denemek yarım cümlelerin metin kutusuna yazılmasını önler.

## 2026-11-12 — Faz 3, Faz 4 ve Faz 5: Sistem tepsisi, serbest kısayol, sihirbaz ve kurucu

1. **Sistem Tepsisi (System Tray) ve pystray:** Bir masaüstü uygulamasının arka planda sessizce çalışıp bildirim alanında ikon göstermesi için `pystray` ve `Pillow` kullanılır. Pencere `X` ile kapatıldığında kapanmak yerine tepsiye gizlenir (`toggle_visibility`), böylece kullanıcı arka planda istediği zaman kısayola basarak dikte yapmaya devam edebilir.
2. **Serbest Kısayol (Key Recorder) ve `pynput`:** Tek tuş sınırlaması yerine 1, 2 veya 3 tuşlu serbest kombinasyonlar (`Ctrl+Shift+D`, `Alt+Space` vb.) yakalanırken basılan sanal tuş kodları (vk) normalize edilir. Böylece sistem tepsisindeyken de global olarak tüm Windows ortamında bas-konuş kısayolu dinlenir.
3. **Anında Otomatik Kaydetme (Auto-Save):** Ayarlar sayfasında "Kaydet" butonu aramak yerine tüm `change` ve `input` olaylarının anında diske atomik yazılması kullanıcı deneyimini hızlandırır ve veri kaybını sıfıra indirir.
4. **Hugging Face Özel Model Desteği (`custom_models.json`):** Yalnızca yerleşik modellere bağlı kalmayıp kullanıcının harici Hugging Face repo ID'si (ses için Whisper reposu, metin için GGUF linki) eklemesine imkan tanındı. Model diskten silinse bile listede kalır; istenirse "⋯" menüsünden tamamen listeden kaldırılabilir.
5. **Kurucu Derleme (Build Pipeline):** PyInstaller tek klasör (onedir) çıktısı alınıp Inno Setup ile sıkıştırıldığında tek kurulum dosyası (`Dikte-Setup-1.6.0.exe`) elde edilir. Kurucunun SHA-256 özeti `latest.json` içine işlenerek otomatik güncelleme zinciri tam ve doğrulanmış hale getirildi.
6. **Swarm Koordinatör Sistemi (`swarm` aracı):** Ana modelin (koordinatör) kolay kodlarla vakit kaybetmeyip yalnızca en zor mimari kararlarla ilgilenmesi; kodlama, test ve doküman işlerinin bağımsız dosya sahipliğiyle birden fazla `gemini-3.8-flash-medium` alt işçisine paylaştırılıp paralel bitirilmesi geliştirme hızını ve kalitesini katlar.

## 2026-11-12 — 3. Oturum: Sistem Tepsisi, Otomatik Yapıştırma ve Arayüz Sağlamlaştırma

1. **Alt Tuşunun Menü Çubuğuna Odak Kaçırması (WM_SYSKEYUP):** Windows'ta yapıştırma öncesi tüm değiştirici tuşları bırakmak için rastgele `Alt` keyup göndermek, `Alt` tuşuna basılmamış olsa bile Windows tarafından menü çubuğunu açma emri (`SC_KEYMENU`) olarak algılanır ve hedef metin kutusundan odağı çalar. Yalnızca `GetAsyncKeyState` ile hâlâ basılı olduğu kanıtlanan tuşlara keyup göndermek bu odak hırsızlığını tamamen çözer.
2. **Yapay Olay Koruması (`is_pasting`):** Program kendisi klavyeye yapay `Ctrl+V` sinyali yolladığında, sistemdeki global klavye dinleyicisi (`pynput`) bu tuş basışını kullanıcının yeni bir kısayol basışı sanıp kaydı yeniden başlatabilir. Yapıştırma sırasında bir koruma bayrağı (`is_pasting = True`) açıp dinleyicide bu sinyalleri görmezden gelmek kısayolun kendi kendini tetiklemesini (feedback loop) engeller.
3. **Model Düşünce Blokları (`<think>...</think>`):** Qwen ve benzeri akıl yürütme (reasoning) modelleri bazen cevaptan önce iç ses veya muhakeme adımlarını `<think>` etiketleri içine yazar. Bu etiketler ve içerikleri temizlenmezse çıktı dili denetimi ve kelime sınırları çöker; regex ile açılıp kapanmamış bloklar dahi silinmelidir.
4. **Polling ve Arayüz Yarış Durumu:** Arayüz her 250 ms'de bir sunucudan güncel durumu yoklarken (polling), kullanıcının o sırada arayüzde tıkladığı bir checkbox veya dil seçimi henüz sunucuya kaydedilmeden gelen eski durumla üzerine yazılabilir. Bir `aiSaveInFlight` sayacı ve kısa bir koruma gecikmesi eklemek, kullanıcının yaptığı anlık ayarların eski verilerce ezilmesini önler.
5. **Whisper Türkçe İpuçları (Prompt & VAD):** Whisper modeline Türkçe için `initial_prompt` ("Türkçe sesli dikte kaydı...") vermek modelin Türkçe imla ve noktalama başarısını belirgin şekilde artırır. Ayrıca konuşma olmayan sessiz bölgeleri kırpan Silero VAD filtresinde eşik (`threshold: 0.35`) ve konuşma öncesi/sonrası tampon (`speech_pad_ms: 400`) değerlerini optimize etmek fısıltı veya nefes seslerinin sahte kelimeler üretmesini engeller.

## 2026-11-18 — v1.6.1: OpenWhispr Analizi, Gömülü Hata Tespit Aracı ve Stabilite Sertleştirmesi

1. **Windows Klavye Kancası (Hook) Süre Sınırı:** `pynput` dinleyicisi Windows'un düşük seviye klavye kancası (`WH_KEYBOARD_LL`) üzerinde çalışır; bu kancada kayıt başlatmak veya bip sesi çalmak gibi geciken işler yapılırsa Windows ~300 ms içinde kancayı sessizce düşürür. Olayı hemen bir arka plan kuyruğuna devretmek kısayolun kilitlenmesini önler.
2. **İki Model Arası Tek Kilit Sırası (`_engine_lock` → `_lock`):** Whisper ve yerel `llama.cpp` modelleri aynı GPU belleğini paylaştığı için ikisinin yükleme/boşaltma işlemlerini tek bir kilit sırasıyla korumak, eşzamanlı kullanımda C++ çökmesini (segfault) ve bellek taşmasını önler.
3. **Token İzolasyonu (`_ai_task_token`):** İptal edilen bir yapay zeka görevi arka planda hemen durmayabilir; her göreve artan bir sıra numarası (token) vermek, eski görevin `finally:` bloğunun yeni başlatılan görevin durumunu bozmasını engeller.
4. **Döndürmeli Log (`RotatingFileHandler`) ve Çökme İşaretçisi (`running.lock`):** Sınırsız büyüyen tek log dosyası yerine 2 MB × 3 döndürmeli log, `faulthandler` ve açılışta konup temiz kapanışta silinen `running.lock` dosyası sayesinde önceki oturumdaki ani çökmeler otomatik yakalanır.
5. **Gizlilik Korumalı Tanılama (Sanitizer):** Hata raporu üretirken konuşma geçmişi, ses dosyası ve API anahtarları kesinlikle rapora alınmaz; olası anahtar desenleri ve Windows kullanıcı adı maskelenip kullanıcıya sade Türkçe çözüm adımları sunulur.

## 2026-11-19 — Yayın Öncesi Denetim ve Faz 1–3 Sertleştirmesi

1. **Windows UAC ve `WinError 740`:** `PrivilegesRequired=admin` ile derlenen kurucu/kaldırıcıyı normal yetkili uygulamadan `subprocess.Popen` ile açmak Windows'ta `WinError 740` hatası verir; `ShellExecuteW(..., "runas", ...)` kullanmak standart UAC onay penceresini açar.
2. **Test Maskesi:** Sahte test köprüsü (`tests/test_ui.py`), gerçek uygulamanın göndermediği bir alanı (`copy.ai.state`) elle eklediğinde testler yeşil kalır ama gerçek uygulamada hata gizlenir; test sahteleri her zaman gerçek API şekline birebir uymalıdır.
3. **Yol Geçişi (Path Traversal) Koruması:** Kullanıcının girdiği özel model URL'sinde alan adını (`huggingface.co`) ve dosya adındaki `../` karakterlerini doğrulamamak, model klasörü dışındaki dosyaların üzerine yazılma riskini doğurur.
4. **Windows UIPI (Yönetici Penceresi İzolasyonu):** Normal yetkili bir uygulama, yönetici olarak açılmış bir pencereye `SendInput` ile tuş (Ctrl+V) gönderemez; `SendInput` dönüş değerini kontrol etmek sahte "yapıştırıldı" mesajını önler.
5. **Pano Kilidi Tekrarı:** Windows Pano Geçmişi (`Win+V`) panoyu anlık kilitleyebilir; tek atışlık kopyalama yerine 25 ms aralıkla 3 kez denemek geçici pano hatalarını sessizce aşar.

## 2026-11-19 (2. Oturum) — Canlı Yayın, `onnxruntime` DLL Hatası ve GitHub Pages

1. **Geç Yükleme (Lazy Import) ve Windows DLL Bellek Sınırı:** `faster-whisper`, sessizlik filtresi (`onnxruntime`) kütüphanesini ilk konuşma anında geç yüklüyordu; arayüz (`pywebview`) ve CUDA DLL'leri zaten belleğe yerleştiği için Windows bu sonradan yüklemeyi reddediyordu. Kütüphaneyi uygulamanın en başında erken yüklemek ve yine de hata olursa filtresiz çeviriye (`vad_filter=False`) düşmek sorunu kökten çözdü.
2. **Eski Logların Yanlış Alarm Üretmesi:** Hata tanılama aracı log dosyasının önceki günlerden kalan `"Model bulunamadı"` satırlarını okuduğu için, model sonradan kurulsa bile yanlış uyarı gösteriyordu. Son başarılı `"Model hazır"` satırından öncesini elemek tanıyı temizledi.
3. **GitHub Pages (`/docs`):** GitHub deposundaki tek bir `docs/index.html` dosyası, hiçbir sunucu kiralamadan ücretsiz bir indirme web sitesine dönüşebiliyor.
4. **Cihaza Göre Ölçekleme (Responsive Tasarım):** CSS'te `clamp()` fonksiyonu ve `@media` kırılımları (`960px` tablet, `640px` telefon) sayesinde aynı sayfa masaüstü, tablet ve telefonda taşma yapmadan otomatik ölçekleniyor.
5. **GitHub CLI (`gh`) ve Güvenli Giriş:** `gh auth login --web` ile şifre paylaşmadan tarayıcı üzerinden tek seferlik kodla giriş yapıldığında, Release yükleme ve güncelleme işlemleri tek komutla otomatikleştirilebiliyor.

## 2026-11-20 — Remotion Tanıtım Videosu ve Web Yayını

1. **Remotion (Kodla Video Üretimi):** Ekran kaydı alıp kesmek yerine React bileşenlerini kare kare render ederek piksel netliğinde tanıtım videosu (MP4) üretilebiliyor; yay fiziği (`spring`) ve kademeli girişler hazır şablon hissini ortadan kaldırıyor.
2. **Yerel Font (`@fontsource`) ve Türkçe Karakterler:** Render sırasında internet erişimi olmasa bile `latin-ext` alt kümesini içeren font paketlerini projeye gömmek, `ı, İ, ğ, ş, ç, ö, ü` harflerinin başka bir yedek fonta düşmeden net çıkmasını sağlıyor.
3. **Deterministik Ses Sentezi (WAV SFX):** Dışarıdan telifli ses aramak yerine küçük bir Node betiğiyle saf matematik kullanarak tıklama, geçiş ve arka plan tonları üretmek projeyi tek komutla yeniden üretilebilir kılıyor.
4. **Web İçin `faststart` ve CRF Sıkıştırma:** `ffmpeg` ile `-movflags +faststart` eklemek tarayıcının 9 MB'lık videoyu tamamen indirmeden ilk saniyeden oynatmaya başlamasını sağlar; `CRF 22` ise kaliteyi koruyarak dosya boyutunu yarıya düşürür.
5. **GitHub `README.md` vs GitHub Pages:** GitHub güvenlik/uyumluluk nedeniyle README içinde ham `<video>` etiketlerini doğrudan oynatmaz; bu yüzden README'de tıklanabilir kapak görseliyle videoyu doğrudan HTML5 `<video>` olarak sunan GitHub Pages sitesine (`#tanitim-videosu`) bağlamak en temiz çözümdür.

## 2026-11-21 — Çok Dilli Vitrin (README ve Web Sitesi i18n)

1. **Çok Dilli README Düzeni (`README.md` + `README.tr.md`):** GitHub depo ana sayfasında dosyaların altında otomatik olarak `README.md` dosyasını gösterir. Varsayılan dili İngilizce yapıp en üste `[English](README.md) | [Türkçe](README.tr.md)` bağlantıları koymak uluslararası kullanıcıların projeyi hemen anlamasını sağlar.
2. **İstemci Tarafı Çoklu Dil (`data-i18n`):** Tek bir statik HTML dosyasında her metne `data-i18n` anahtarı verip küçük bir JavaScript sözlüğüyle değiştirmek, ayrı sunucu veya iki farklı HTML dosyası bakımına gerek kalmadan anında dil geçişi sağlar.
3. **Varsayılan Dil ve Kalıcı Tercih (`localStorage` + `?lang=`):** HTML kaynak kodunu doğrudan varsayılan dilde (`lang="en"`) yazmak arama motorları ve ilk açılış için en sağlıklı yoldur; kullanıcının seçtiği dili `localStorage`'da saklamak ve `?lang=tr` parametresini desteklemek Türkçe README'den gelen ziyaretçiye doğrudan Türkçe deneyim sunar.
4. **Mobil Üst Çubukta Taşma Kontrolü:** Masaüstü bağlantıları mobilde gizlenirken dil seçici ve tema düğmesi gibi temel kontrollerin görünür kalması ve `360px` genişlikte yatay taşma (`scrollWidth > clientWidth`) yapmaması Playwright ile doğrulanır.

## 2026-11-24 — v1.6.1 Tam Kod Denetimi ve Protokol Güncellemesi

1. **Durum Makinesi Kaçağı:** Bir fonksiyonun mevcut durumu kontrol etmeden koşulsuz `READY` (hazır) durumuna geçmesi, arka planda hâlâ bir işlem sürerken yeni kayıt başlatılmasına yol açabilir; durum geçişleri her zaman hangi durumdan gelindiğine bakmalıdır.
2. **Enum İçindeki Özellik Farkı (`Key.value.vk`):** `pynput` kütüphanesinde normal karakter tuşlarında sanal tuş kodu (`vk`) doğrudan nesnenin üstündeyken, `Sağ Ctrl` gibi özel tuşlarda `key.value.vk` içinde tutulur; bunu atlamak takılı tuş kurtarma kodunun hiç çalışmamasına neden olur.
3. **Test Maskesi (Test Masking):** Üretim kodunun sahte test nesnesini (`Mock`) fark edip gerçek parametreleri atlaması veya test sahtesinin her zaman `ok: true` döndürmesi, gerçek hataların yeşil testlerin arkasında gizlenmesine yol açar.
4. **Kod Tekrarını Tek Yardımcıda Toplamak:** Aynı atomik dosya yazma mantığının 6 farklı dosyada kopyalanması yerine tek ortak yardımcıya taşınması hem hata riskini azaltır hem de kod tabanını yüzlerce satır kısaltır.
5. **Çapraz Oturum Hafızası (`asama-baslat` + Obsidian):** Yeni sohbet açıldığında yalnız proje içindeki metin dosyalarına değil, kişisel Obsidian hafıza kasasına da bakmak önceki oturumlardaki kararların ve alınan derslerin unutulmasını önler.

## 2026-11-25 — Genele Hitap Etme ve Sade Tanıtım Araştırması

1. **Open Graph (OG) Kartları:** Web sayfasına eklenen birkaç küçük HTML meta etiketi (`og:title`, `og:image`), site bağlantısı WhatsApp, Discord veya sosyal medyada paylaşıldığında düz link yerine kapak görselli zengin önizleme kartı görünmesini sağlar.
2. **Microsoft Store (MSIX) ve SmartScreen:** Microsoft Eylül 2025'te bireysel geliştirici kayıt ücretini kaldırdı; MSIX paketiyle mağazada yayınlanan uygulamalar Microsoft tarafından ücretsiz imzalandığı için mavi SmartScreen uyarısı çıkmıyor.
3. **Bas-Bırak (Toggle) ve Yüzen Gösterge (Overlay):** Basılı tutmanın yanında tek tıkla başlat/durdur seçeneği ve tepsideyken ekranın altında beliren küçük bir "Dinliyor…" işareti, sıradan kullanıcıların sesli dikteyi günlük alışkanlığa çevirmesinde en çok aradığı iki kolaylıktır.
4. **Gerçek Ekran Kaydı Etkisi:** Sıfır bütçeli tanıtımda karmaşık animasyonlar yerine 20–30 saniyelik gerçek ekran kaydında konuşarak metin yazdırmayı göstermek daha doğal güven ve indirme getirir.

## 2026-11-26 — Faz 1–4 Sağlamlaştırma, 5 Dokunuş ve HyperFrames Videoları

1. **Odak Çalmayan Pencere (`WS_EX_NOACTIVATE`):** Windows'ta ekranın üstünde beliren küçük bir durum kutusu ("Dinliyor…") varsayılan olarak etkin pencereden (Word, WhatsApp) odağı çalar ve yapıştırmayı bozar; pencereye `WS_EX_NOACTIVATE` bayrağı vermek kutunun görünür kalıp imleci bozmamasını sağlar.
2. **Görünürlük Olayı (`visibilitychange`) ile Pil Tasarrufu:** Uygulama sistem tepsisine gizlendiğinde arayüzün saniyede 60 kare animasyon çizmeye ve 250 ms'de bir sunucuyu yoklamaya devam etmesi gereksiz CPU tüketir; `document.hidden` olduğunda döngüyü durdurmak boşta tüketimi sıfıra yaklaştırır.
3. **HyperFrames ile HTML'den Video:** Tarayıcıdaki HTML/CSS/GSAP zaman çizelgesini kare kare yakalayarak (`check`, `snapshot`, `render`) hem 16:9 yatay hem 9:16 dikey (Shorts) videoları deterministik biçimde ve yerel Türkçe fontlarla üretmek mümkün.
4. **Ortak Yardımcı Modül (`fsutil.py`):** 6 ayrı dosyada tekrarlanan atomik JSON yazma ve bozuk dosya yedekleme mantığını tek modülde toplamak hem kod boyutunu küçültür hem de tek yerden hata düzeltmeyi kolaylaştırır.


## 2026-11-26 (Gece) — Karakterli YouTube Shorts (HyperFrames + Video Modeli) ve Oturum Devam Protokolü

1. **Hibrit Video Üretimi (Veo + HyperFrames):** Karakterin el/yüz hareketleri gibi doğal stop-motion animasyonlarını video modeliyle (`Image-to-Video`) üretip, üstündeki okunaklı Türkçe altyazı, ses miksajı ve YouTube Shorts güvenli alanını HyperFrames ile kodlamak hem sinematik hem hatasız sonuç verir.
2. **Shorts Güvenli Alanı (`--safe-zone shorts`) ve Kontrast Kontrolü:** HyperFrames'in `check --safe-zone shorts` komutu, YouTube Shorts'taki sağ buton sütunu ve alt açıklama alanıyla çakışan yazıları ve düşük kontrastlı metinleri render öncesi yakalar.
3. **Obsidian Kalıcı Oturum Devamı (`en-son-oturumda-kalinan-yer.md`):** Her oturum kapanışında tek bir sabit dosyaya kalınan noktayı yazıp her `/asama-baslat` çağrısında bunu okutmak, yeni sohbetlerin hiçbir bağlam kaybetmeden doğrudan sıradaki adımdan başlamasını sağlar.

## 2026-11-27 — Gemini Omni Uzatma Planı ve Video İşinin İptali

1. **Video Uzatma (Video Extension):** İki ayrı klibi sert kesmeyle (`hard cut`) birleştirmek yerine, mevcut bir klibi video modeline girdi olarak verip devamını ürettirmek karakter, ışık ve ortam tutarlılığını tek çekim gibi korur.
2. **Yerel API vs. Web Arayüzü:** Bir AI modelini doğrudan terminalden/koddan çağırmak için ilgili SDK (`google-genai`) ve `API anahtarı` gerekir; bunları kurmadan web arayüzünden üretip dosyayı projeye almak ek kurulum ve maliyet yönetimini basitleştirir.
3. **Erken İptal ve Temiz Kapanış:** Bir yan iş (karakterli Shorts) artık öncelik değilse dosyaları hemen silmeden iptal kararını hafızaya (`STATE.md`, `Obsidian`) işlemek, yeni oturumda ana ürüne (`v1.7.0`) temiz dönmeyi sağlar.
