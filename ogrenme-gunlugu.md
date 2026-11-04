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
