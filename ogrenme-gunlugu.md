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

