# uygulanacak plan.md — Kalan işler için güncel uygulama planı

Oluşturma: 2026-11-04 · **Yeniden yazıldı: 2026-11-12**  
Kaynaklar: `Dikte-Denetim-Raporu.md`, Faz 1 ve Faz 2 tamamlanma kanıtları (263 passed test), `design/dikte-ai.html`, `design/mikrofon_morph_animasyonu.html`, AGENTS.md kararları ve 2026-11-12 kullanıcı istekleri.

Bu dosya **uygulama yol haritası**dır. Kodlama ayrı oturumda TDD ve Swarm kurallarına uygun olarak yürütülecektir.

---

## 0. Mevcut Doğrulanmış Durum (2026-11-12)

| Konu | Durum | Kanıt |
| :--- | :--- | :--- |
| Testler | **303 passed, 1 skipped** (40.68 sn) | `pytest -q` |
| Faz 1 (Yayın) | Tamamlandı | `config.APP_VERSION = "1.6.0"`, sha256 akışı, Inno kurucu `Dikte-Setup-1.6.0.exe` |
| Faz 2 (11 Hata) | Tamamlandı | Pano koruması, GGUF/Whisper bütünlük kontrolü, RLock/fsync, yetim dosya temizliği |
| Faz 3 (Tasarım/UX) | Tamamlandı | Yeni logo, sade Dikte.AI ve klasik tasarım dili, mikrofon morfizmi, sidebar aç/kapa, anında ayar kaydı |
| Faz 4 (Sistem/HF) | Tamamlandı | 1-3 tuşlu serbest kısayol, sistem tepsisi (pystray), Hugging Face model modalı ve "⋯" menüsü, Karşılama Sihirbazı |
| Faz 5 (Güncelleme/Kurucu) | Tamamlandı | Rollback desteği, sentetik test sesi (`test.wav`), güncel Inno kurucu (177.4 MB, SHA256 güncel) |
| Çalışma Ağacı | Temiz | `design/v2/` temiz, tüm testler yeşil |

---

## 1. Çalışma ve Mimari Kuralları (2026-11-12 Kararları)

1. **Model ve Rol Dağılımı (Swarm):**
   - **Ana Model:** Yalnızca en zor mimari kararlar, kritik kilitler/algoritmalar ve üst düzey koordinasyon için kullanılır.
   - **Alt Ajanlar (`/swarm` & Sub-agents):** Kolay/uzun kodlama işleri, arayüz/CSS uyarlamaları, belge güncellemeleri, test koşturma ve denetim görevleri için daima `gemini-3.8-flash-medium` (`Model: "flash"`) kullanılır. Çoklu işlerde paralel 2 veya daha fazla alt ajan devreye alınır.
2. **Tasarım / Görünüm Dili Seçimi (belirsizleri-sor Kararı):**
   - Varsayılan arayüz tasarım modeli **Sade Dikte.AI + Mikrofon Morph** (`design_style = "dikte_ai"` varsayılan olarak gelir; Ayarlar → Görünüm'den `"classic"` Magic UI v1.4 seçilebilir).
   - Her iki modda da Dikte ana mikrofon alanında `design/mikrofon_morph_animasyonu.html`'deki canvas ses dalgası ve morflayan mikrofon animasyonu yer alır.
3. **Kısayol ve Sistem Tepsisi (Tray & Ajan Kararları):**
   - Sistem tepsisi entegrasyonu `pystray + Pillow` ile sağlanır; tepsi sağ tık menüsünde `Göster/Gizle | Durum | Çıkış` seçenekleri yer alır.
   - 1, 2 veya 3 tuşlu serbest kısayol kombinasyonu (ör. `Ctrl+Shift+D`, `Alt+Space`, `F8`).
   - Sistem tepsisinde arka planda çalışırken dahi kısayol dinlenir ve dikte yapılır.
   - Windows ile otomatik başlatıldığında pencere açılmaz, doğrudan tepside başlar.
4. **Hugging Face Model Ekleyebilme (belirsizleri-sor Kararı):**
   - Eklenen modeller `data/custom_models.json` dosyasında kalıcı saklanır.
   - Model kartında "Sil" dendiğinde diskteki model dosyası silinir ama kart listede kalır.
   - Kartın "⋯" menüsünde ayrıca modeli listeden tamamen kaldıran "Listeden Kaldır" seçeneği bulunur.
   - Modeller sayfasına (hem Ses hem Metin) kullanıcının harici Hugging Face repo kimliği (repo ID / model adı / GGUF linki) girerek doğrudan yeni model ekleyip indirebilmesi imkanı sağlanır.
5. **Otomatik Kaydetme & Geri Dönüş (Rollback):**
   - Ayarlar sayfasında herhangi bir girdi (kısayol, dil, model, tema vb.) değiştiği anda otomatik kaydetme.
   - Güncelleme kartında eski kararlı sürümlere tek tıkla geri dönebilme (downgrade).

---

## 2. Faz 3 — Tasarım, Kullanıcı Deneyimi ve Arayüz (Parti 1)

### 3.1 Yeni Logo & Görev Çubuğu & Kısayol Entegrasyonu
- [x] Kaynak olarak `design/download` (ses dalgalı mavi ikon) görselini al, `Pillow` ile `assets/icon.ico` (16x16 ... 256x256) ve `dikte/ui/assets/icon.png` olarak işle.
- [x] Windows görev çubuğunda Python logosu yerine uygulamanın kendi logosunun görünmesi için `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID` tanıt.
- [x] Masaüstündeki `Dikte.lnk` ve Inno Setup kurucu simgelerini yeni logo ile güncelle.

### 3.2 Yan Menü (Sidebar) Katlama / Açma Özelliği
- [x] Sol üstteki **VoxNote AI logosuna tıklandığında** yan menü (Dikte, Geçmiş, Modeller, Ayarlar) daralsın/açılsın (collapse/expand).
- [x] Kapatıldığında ana çalışma alanı genişlesin; logoya tekrar tıklandığında menü geri gelsin.

### 3.3 Arayüz Metin Temizliği (Minimalist Görünüm)
- [x] Sol üstteki *"Daha iyi fikirler, daha hızlı."* sloganı kaldırılacak.
- [x] Sol alttaki *"Yerel sistem hazır"* rozeti ve yazısı tamamen kaldırılacak.
- [x] Dikte sayfası başlığı yalnızca **"Dikte"** yapılacak; altındaki *"Konuşun, yapay zeka sizin için yazsın."* cümlesi silinecek.
- [x] Dikte Geçmişi sayfasındaki *"Kaydedilen dikte metinlerini görüntüle ve yönet."* alt yazısı silinecek.
- [x] Modeller sayfasındaki *"Konuşmayı yazıya çeviren yerel Whisper modellerini yönet."* alt yazısı silinecek.

### 3.4 Görünüm / Tasarım Dili Seçimi & Mikrofon Morfizmi
- [x] Ayarlar → Görünüm altına "Arayüz Tasarım Modeli" seçimi ekle: varsayılan **Sade Dikte.AI** (`design_style = "dikte_ai"`), alternatif **Klasik Magic UI v1.4** (`design_style = "classic"`).
- [x] Dikte sayfasına her iki modda da çalışacak şekilde `design/mikrofon_morph_animasyonu.html`'deki ses dalgası (wave canvas) ve durum geçişli (idle/recording/processing) buton morfizmini entegre et.

### 3.5 Ayarlar Menüsünde Anında / Otomatik Kaydetme
- [x] Ayarlar sayfasındaki tüm kontrollere `input`/`change` dinleyicileri bağlanarak anında `save_settings` çalıştırılsın.

---

## 3. Faz 4 — Sistem Entegrasyonu, Kısayollar ve Hugging Face (Parti 2)

### 4.1 Serbest Çoklu Tuş Kısayol Sistemi (1, 2 veya 3 Tuş)
- [x] Tek tuş sınırlaması kaldırılacak; kullanıcının klavyeden basacağı herhangi 1, 2 veya 3 tuş (`Ctrl + Shift + D`, `Alt + Space` vb.) pynput dinleyicisine kaydedilecek.
- [x] Ayarlar sayfasında tuş yakalama (Key Recorder) kutusu yapılacak.

### 4.2 Sistem Tepsisi (System Tray) ve Gizli Başlatma
- [x] `pystray + Pillow` ile Windows bildirim alanı (System Tray) entegrasyonu.
- [x] Tepsi sağ tık menüsünde `Göster/Gizle | Durum | Çıkış` seçenekleri.
- [x] Windows açılışında başlatıldığında doğrudan sistem tepsisine küçültülmüş başlama (`--minimized` / `--tray`).
- [x] Pencere `X` ile kapatıldığında uygulamadan çıkmak yerine sistem tepsisine gizlenme.
- [x] Sistem tepsisindeyken dahi global kısayolun çalışması ve metni yapıştırması.

### 4.3 Hugging Face'ten Özel Model Ekleme
- [x] Modeller sayfasına "Özel Model Ekle" (Hugging Face) butonu ve modalı.
- [x] Eklenen özel modellerin `data/custom_models.json` dosyasında kalıcı olarak saklanması.
- [x] Ses modelleri için uyumlu Whisper HF repo ID'si, metin modelleri için GGUF URL/HF repo ID'si girilip listeye dinamik eklenebilmesi.
- [x] Model kartında "Sil" tıklandığında diskteki ağırlık dosyalarının silinmesi ancak kartın listede kalması; "⋯" menüsünde ayrıca "Listeden Kaldır" seçeneği sunulması.

### 4.4 Kalan Arayüz / Motor Eksikleri
- [x] Karşılama sihirbazı (5 ekran - `#sayfa-kurulum`).
- [x] Modeller sayfasında "⋯" (üç nokta) işlem menüsü.
- [x] Ses modeli indirmesi için "İptal" butonu.
- [x] Girdi dili seçimi (`input_language` = TR / Auto) Whisper motoruna bağlanacak.
- [x] Temizle / Çevir işlemlerinin arka plan thread'ine alınıp iptal edilebilir yapılması.
- [x] Transkripsiyonu Yenile işleminde otomatik çeviri varsa çevrilmiş metnin üretilmesi.

---

## 4. Faz 5 — Güncelleme, Geri Dönüş (Rollback) ve Sanal Makine Testi (Parti 3)

### 5.1 Arka Planda Güncelleme ve Eski Sürüme Geri Dönüş (Rollback)
- [x] GitHub Releases API'den önceki sürümlerin çekilmesi.
- [x] Ayarlar → Güncelleme alanından istenen önceki sürüme tek tıkla geri dönüş (downgrade) butonu.
- [x] Güncellemenin indirilip sessizce Inno Setup ile uygulanması ve uygulamanın yeniden başlatılması.

### 5.2 Sanal Makinede Temiz Kurulum ve Dağıtım Doğrulaması (İş Bölümü)
- [x] Sentetik test sesi (`tests/data/test.wav` ve `test.txt`) üretilerek `python -m dikte --selftest`'in yeşile çekilmesi.
- [x] `build.ps1` çalıştırılarak güncel `installer\Output\Dikte-Setup-1.6.0.exe` paketinin derlenmesi ve paketli açılış testi yapılması.
- [ ] Kurucu exe'nin temiz Windows VM ortamında test edilmesi (UAC, kurulum, kısayol, kaldırma, modelleri koruma) — *Kullanıcı tarafından yapılacak*.
- [ ] GitHub Releases üzerine ilk resmi v1.6.0 sürümünün yayınlanması — *Kullanıcı tarafından yapılacak*.

---

## 5. Bitti Tanımı ve Kabul Ölçütleri

1. Tüm yeni tasarım ve animasyon öğeleri (`dikte-ai.html`, `mikrofon_morph_animasyonu.html`, logo, menü aç/kapa) arayüzde çalışır durumda olacak.
2. 1-3 tuşlu kısayol kombinasyonları sistem tepsisindeyken sorunsuz dikte yapacak.
3. Hugging Face'ten harici model eklenebilecek.
4. Ayarlar anında kaydedilecek, eski sürüme geri dönüş çalışacak.
5. `pytest` test takımı eksiksiz yeşil kalacak (≥263 passed).
