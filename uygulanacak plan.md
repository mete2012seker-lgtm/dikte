# uygulanacak plan.md — Kalan işler için güncel uygulama planı

Oluşturma: 2026-11-04 · **Yeniden yazıldı: 2026-11-12**  
Kaynaklar: `Dikte-Denetim-Raporu.md`, Faz 1 ve Faz 2 tamamlanma kanıtları (263 passed test), `design/dikte-ai.html`, `design/mikrofon_morph_animasyonu.html`, AGENTS.md kararları ve 2026-11-12 kullanıcı istekleri.

Bu dosya **uygulama yol haritası**dır. Kodlama ayrı oturumda TDD ve Swarm kurallarına uygun olarak yürütülecektir.

---

## 0. Mevcut Doğrulanmış Durum (2026-11-12)

| Konu | Durum | Kanıt |
| :--- | :--- | :--- |
| Testler | **263 passed, 1 skipped** (42.5 sn) | `pytest -q` |
| Faz 1 (Yayın) | Tamamlandı | `config.APP_VERSION = "1.6.0"`, sha256 akışı, Inno kurucu `Dikte-Setup-1.6.0.exe` (172 MB) |
| Faz 2 (11 Hata) | Tamamlandı | Pano koruması, GGUF/Whisper bütünlük kontrolü, RLock/fsync, yetim dosya temizliği |
| Çalışma Ağacı | Temiz | `git status` clean |

---

## 1. Çalışma ve Mimari Kuralları (2026-11-12 Kararları)

1. **Model ve Rol Dağılımı (Swarm):**
   - **Ana Model:** Yalnızca en zor mimari kararlar, kritik kilitler/algoritmalar ve üst düzey koordinasyon için kullanılır.
   - **Alt Ajanlar (`/swarm` & Sub-agents):** Kolay/uzun kodlama işleri, arayüz/CSS uyarlamaları, belge güncellemeleri, test koşturma ve denetim görevleri için daima `gemini-3.8-flash-medium` (`Model: "flash"`) kullanılır. Çoklu işlerde paralel 2 veya daha fazla alt ajan devreye alınır.
2. **Tasarım / Görünüm Dili Seçimi:**
   - Ayarlar → Görünüm alanında kullanıcının tasarım modelini seçebilmesi sağlanır:
     - **Klasik / Magic UI (v1.4)**
     - **Sade Dikte.AI Modeli (`design/dikte-ai.html`)**
   - Dikte ana alanında `design/mikrofon_morph_animasyonu.html`'deki canvas ses dalgası ve morflayan mikrofon animasyonu yer alır.
3. **Kısayol ve Sistem Tepsisi (Tray):**
   - 1, 2 veya 3 tuşlu serbest kısayol kombinasyonu (ör. `Ctrl+Shift+D`, `Alt+Space`, `F8`).
   - Sistem tepsisinde arka planda çalışırken dahi kısayol dinlenir ve dikte yapılır.
   - Windows ile otomatik başlatıldığında pencere açılmaz, doğrudan tepside başlar.
4. **Hugging Face Model Ekleyebilme:**
   - Modeller sayfasına (hem Ses hem Metin) kullanıcının harici Hugging Face repo kimliği (repo ID / model adı / GGUF linki) girerek doğrudan yeni model ekleyip indirebilmesi imkanı.
5. **Otomatik Kaydetme & Geri Dönüş (Rollback):**
   - Ayarlar sayfasında herhangi bir girdi (kısayol, dil, model, tema vb.) değiştiği anda otomatik kaydetme.
   - Güncelleme kartında eski kararlı sürümlere tek tıkla geri dönebilme (downgrade).

---

## 2. Faz 3 — Tasarım, Kullanıcı Deneyimi ve Arayüz (Parti 1)

### 3.1 Yeni Logo & Görev Çubuğu & Kısayol Entegrasyonu
- [ ] Kullanıcının gönderdiği ses dalgalı logoyu `assets/icon.ico` (16x16 ... 256x256) ve `dikte/ui/assets/icon.png` olarak işle.
- [ ] Windows görev çubuğunda Python logosu yerine uygulamanın kendi logosunun görünmesi için `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID` tanıt.
- [ ] Masaüstündeki `Dikte.lnk` ve Inno Setup kurucu simgelerini yeni logo ile güncelle.

### 3.2 Yan Menü (Sidebar) Katlama / Açma Özelliği
- [ ] Sol üstteki **VoxNote AI logosuna tıklandığında** yan menü (Dikte, Geçmiş, Modeller, Ayarlar) daralsın/açılsın (collapse/expand).
- [ ] Kapatıldığında ana çalışma alanı genişlesin; logoya tekrar tıklandığında menü geri gelsin.

### 3.3 Arayüz Metin Temizliği (Minimalist Görünüm)
- [ ] Sol üstteki *"Daha iyi fikirler, daha hızlı."* sloganı kaldırılacak.
- [ ] Sol alttaki *"Yerel sistem hazır"* rozeti ve yazısı tamamen kaldırılacak.
- [ ] Dikte sayfası başlığı yalnızca **"Dikte"** yapılacak; altındaki *"Konuşun, yapay zeka sizin için yazsın."* cümlesi silinecek.
- [ ] Dikte Geçmişi sayfasındaki *"Kaydedilen dikte metinlerini görüntüle ve yönet."* alt yazısı silinecek.
- [ ] Modeller sayfasındaki *"Konuşmayı yazıya çeviren yerel Whisper modellerini yönet."* alt yazısı silinecek.

### 3.4 Görünüm / Tasarım Dili Seçimi & Mikrofon Morfizmi
- [ ] Ayarlar → Görünüm altına "Arayüz Tasarım Modeli" seçimi ekle (`Klasik v1.4` vs `Sade Dikte.AI`).
- [ ] Dikte sayfasına `design/mikrofon_morph_animasyonu.html`'deki ses dalgası (wave canvas) ve durum geçişli (idle/recording/processing) buton morfizmini entegre et.

### 3.5 Ayarlar Menüsünde Anında / Otomatik Kaydetme
- [ ] Ayarlar sayfasındaki tüm kontrollere `input`/`change` dinleyicileri bağlanarak anında `save_settings` çalıştırılsın.

---

## 3. Faz 4 — Sistem Entegrasyonu, Kısayollar ve Hugging Face (Parti 2)

### 4.1 Serbest Çoklu Tuş Kısayol Sistemi (1, 2 veya 3 Tuş)
- [ ] Tek tuş sınırlaması kaldırılacak; kullanıcının klavyeden basacağı herhangi 1, 2 veya 3 tuş (`Ctrl + Shift + D`, `Alt + Space` vb.) pynput dinleyicisine kaydedilecek.
- [ ] Ayarlar sayfasında tuş yakalama (Key Recorder) kutusu yapılacak.

### 4.2 Sistem Tepsisi (System Tray) ve Gizli Başlatma
- [ ] `pystray` / Windows Shell bildirim alanı entegrasyonu.
- [ ] Windows açılışında başlatıldığında doğrudan sistem tepsisine küçültülmüş başlama (`--minimized` / `--tray`).
- [ ] Pencere `X` ile kapatıldığında uygulamadan çıkmak yerine sistem tepsisine gizlenme.
- [ ] Sistem tepsisindeyken dahi global kısayolun çalışması ve metni yapıştırması.

### 4.3 Hugging Face'ten Özel Model Ekleme
- [ ] Modeller sayfasına "Özel Model Ekle" (Hugging Face) butonu ve modalı.
- [ ] Ses modelleri için uyumlu Whisper HF repo ID'si, metin modelleri için GGUF URL/HF repo ID'si girilip listeye dinamik eklenebilmesi.

### 4.4 Kalan Arayüz / Motor Eksikleri
- [ ] Karşılama sihirbazı (5 ekran - `#sayfa-kurulum`).
- [ ] Modeller sayfasında "⋯" (üç nokta) işlem menüsü.
- [ ] Ses modeli indirmesi için "İptal" butonu.
- [ ] Girdi dili seçimi (`input_language` = TR / Auto) Whisper motoruna bağlanacak.
- [ ] Temizle / Çevir işlemlerinin arka plan thread'ine alınıp iptal edilebilir yapılması.
- [ ] Transkripsiyonu Yenile işleminde otomatik çeviri varsa çevrilmiş metnin üretilmesi.

---

## 4. Faz 5 — Güncelleme, Geri Dönüş (Rollback) ve Sanal Makine Testi (Parti 3)

### 5.1 Arka Planda Güncelleme ve Eski Sürüme Geri Dönüş (Rollback)
- [ ] GitHub Releases API'den önceki sürümlerin çekilmesi.
- [ ] Ayarlar → Güncelleme alanından istenen önceki sürüme tek tıkla geri dönüş (downgrade) butonu.
- [ ] Güncellemenin indirilip sessizce Inno Setup ile uygulanması ve uygulamanın yeniden başlatılması.

### 5.2 Sanal Makinede Temiz Kurulum ve Dağıtım Doğrulaması
- [ ] Sentetik test sesi (`tests/data/test.wav` ve `test.txt`) ile selftest'in yeşile çekilmesi.
- [ ] Kurucu exe'nin temiz Windows VM ortamında test edilmesi (UAC, kurulum, kısayol, kaldırma, modelleri koruma).
- [ ] GitHub Releases üzerine ilk resmi v1.6.0 sürümünün yayınlanması.

---

## 5. Bitti Tanımı ve Kabul Ölçütleri

1. Tüm yeni tasarım ve animasyon öğeleri (`dikte-ai.html`, `mikrofon_morph_animasyonu.html`, logo, menü aç/kapa) arayüzde çalışır durumda olacak.
2. 1-3 tuşlu kısayol kombinasyonları sistem tepsisindeyken sorunsuz dikte yapacak.
3. Hugging Face'ten harici model eklenebilecek.
4. Ayarlar anında kaydedilecek, eski sürüme geri dönüş çalışacak.
5. `pytest` test takımı eksiksiz yeşil kalacak (≥263 passed).
