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

## 2026-11-12 — 2. Oturum: Hata Ayıklama, Tek Kopya Kilidi ve Görsel Doğrulama

1. **Single Instance Mutex (Tek Kopya Kilidi):** Bir programın aynı anda iki kez açılıp çakışmasını veya çift sistem tepsisi ikonu oluşturmasını önlemek için işletim sistemi düzeyinde tutulan isimlendirilmiş kilit (`CreateMutexW`). İkinci kopya açıldığında kilit olduğunu anlar, mevcut açık pencereyi (`SW_RESTORE` + `SetForegroundWindow`) öne getirir ve kendisi sessizce kapanır.
2. **WM_SETICON ve AppUserModelID:** Windows'ta `python.exe` üzerinden çalışan bir masaüstü penceresi görev çubuğunda ve pencere sol üstünde varsayılan Python logosunu gösterebilir. İşletim sistemine `SetCurrentProcessExplicitAppUserModelID` ile özel kimlik tanımlamak ve pencere tutamacına (HWND) Win32 `WM_SETICON` mesajıyla `LoadImageW` üzerinden `.ico` dosyasını basmak, uygulamanın kendi profesyonel logosunu göstermesini sağlar.
3. **Cubic-Bezier & Newton-Raphson Easing:** CSS animasyonları (`cubic-bezier(0.4, 0.0, 0.2, 1)`) ile HTML5 Canvas üzerinde çizilen ses dalgalarının ve halkaların milisaniyesi milisaniyesine aynı hız eğrisiyle genişleyip sönümlenmesi için Newton-Raphson iterasyonuyla zaman eğrisi örneklendi. Böylece DOM elemanları ile canvas çizimi kusursuz senkronize oldu.
4. **ResizeObserver & Canvas Buffer:** `display: none` olan gizli bir sekmede (örneğin Ayarlar veya Geçmiş açıkken) canvas elemanının genişlik ve yüksekliği 0 piksele düşer. Dikte sekmesine geri dönüldüğünde dalga çiziminin bozulmaması için `ResizeObserver` ve sekme geçişi dinleyicisi (`resizeWaveCanvas`) ile canvas buffer boyutu fiziksel piksel oranına (DPR) göre anında güncellenir.




