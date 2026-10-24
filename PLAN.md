# PLAN.md — Dikte Uygulaması Aşamalı Plan

Bu dosya projenin yol haritasıdır. Her aşama bitince maddeler işaretlenir ([x]). Şu anki durum için STATE.md'ye bak.

## Hedef
Windows'ta çalışan, design/ klasöründeki tasarıma uygun bir Türkçe dikte uygulaması.
Sayfalar: Dikte, Dikte Geçmişi, Modeller, Ayarlar.

## Tasarımdan bilinçli farklar (kararlı)
- Sağ paneldeki aktif model kartında "İşleme hızı" satırı YOK.
- Modeller sayfası iki bölüme ayrılır:
  - Ses Modelleri: konuşmayı yazıya çevirir (Whisper).
  - Metin Modelleri: "Yapay Zeka ile Temizle" özelliği için, metindeki kusurları düzeltir.
- "Görsel" model kategorisi YOK.
- Tasarımdaki model adları, boyutlar ve bellek rakamları örnektir. Gerçek değerler uygulamadan ölçülür.
- Kısayol varsayılanı Sağ Ctrl. Ayarlardan değiştirilebilir olacak.

## Teknoloji (öneri, Aşama 0'da doğrulanır)
- Python 3.12, faster-whisper, pywebview + HTML/CSS/JS arayüz.
- Metin modelleri: önce LM Studio veya Ollama'nın yerel sunucusuna bağlanarak (OpenAI uyumlu API). Uygulamanın içinde GGUF modeli kendisi çalıştırması Aşama 7'de denenir, riskli sayılır.
- Bellek (VRAM) sınırı: laptop kartı 8 GB. Ses modeli ve metin modeli aynı anda belleğe sığmayabilir, bu yüzden "yükle, kullan, boşalt" düzeni ya da küçük model kullanılır. Aşama 7'de ölçülür.

## Aşamalar
Her aşama bittiğinde: kanıt gösterilir, STATE.md güncellenir, git commit atılır.

### Aşama 0 — Ortam
- [ ] Python 3.12 kurulu, .venv oluşturuldu, requirements.txt yazıldı. → **Python 3.12 henüz yok; geçici .venv 3.10.11 ile kuruldu.**
- [x] `.venv` + `requirements.txt` + `requirements-dev.txt` hazır; CUDA kütüphaneleri dahil.
- Kanıt: `pip install` çıktısı, `python --version` = 3.10.11, 34 test.
- Senin yapacağın: Python 3.12'yi kur, sonra `.venv` klasörünü silip `py -3.12 -m venv .venv` ve `pip install -r requirements-dev.txt` çalıştır.

### Aşama 1 — Çeviri motoru
- [x] faster-whisper ile bir ses dosyasından Türkçe metin alınıyor.
- [x] Önce GPU (cuda + float16), olmazsa CPU (int8). Hangi modda çalıştığı ekrana yazılıyor.
- [x] `python -m dikte --selftest` komutu: test sesini çevirir, süreyi ve modu yazar.
- Kanıt: GPU float16 ile `large-v3` 6,4 sn'de yüklendi; 9,82 sn TTS sesi çevrildi. (TTS İngilizce aksanlı olduğu için metin kusurlu; kullanıcı kaydı bekleniyor.)
- Senin yapacağın: 5–10 saniyelik Türkçe bir cümleyi kaydedip `tests/data/test.wav` olarak koy, cümlenin yazısını `tests/data/test.txt` dosyasına yaz.

### Aşama 2 — Mikrofon, kısayol ve pano (henüz arayüz yok)
- [x] Kısayola basılı tutunca kayıt, bırakınca çeviri, sonuç panoya.
- [x] Kayıt başı ve sonu için kısa ses tonu.
- [x] Geçici `.wav` çeviri sonrası siliniyor.
- Kanıt: Gerçek mikrofonla 1,15 sn kayıt (18.400 kare), pano Türkçe karakter testi, Sağ Ctrl press/release testi.
- Senin yapacağın: Not Defteri'nde gerçek konuşma testi.

### Aşama 3 — Statik arayüz
- [x] design/prototype.html uygulama penceresinde (pywebview) açılıyor.
- [ ] 4 sayfa (Dikte, Dikte Geçmişi, Modeller, Ayarlar) sahte verilerle çalışıyor. → **v1 kapsamı yalnız Dikte; diğer 3 sayfa v1.1'e ertelendi.**
- Kanıt: pywebview `SAYFA_YUKLENDI` + gerçek uygulama `ready`; Playwright DOM testi; `artifacts/ui-dikte.png`.
- Senin yapacağın: Ekran görüntüsüne bakıp onay ver.

### Aşama 4 — Dikte sayfası çalışsın
- [x] Mikrofon düğmesi, durum yazısı (Dinlemeye hazır / Dinliyor / İşleniyor), metin kutusu.
- [x] Kopyala, Geri Al, dil seçici (v1'de yalnız Türkçe, pasif).
- [x] Son etkinlikler listesi (bellekte, gerçek olaylar).
- [x] Sağ panelde gerçek model, GPU/CPU ve bellek bilgisi; "İşleme hızı" yok.
- Kanıt: 34 pytest, uçtan uca controller + pano, Playwright.
- Durum: **Kullanıcı uygulamayı çalıştırdı ve onayladı (2026-10-24). v1 tamam.**
- Sıradaki: v1.1 (Aşama 5: Dikte Geçmişi + Ayarlar).

### Aşama 5 — Dikte Geçmişi ve Ayarlar
- [ ] Her dikte kaydedilir (tarih, süre, kelime sayısı, metin). Listele, aç, sil.
- [ ] Ayarlar: kısayol, dil, mikrofon seçimi. settings.json'da saklanır.
- Kanıt: pytest (kaydet, oku, sil), arayüz testi.

### Aşama 6 — Modeller sayfası: Ses Modelleri
- [ ] Whisper modelleri listelenir (tiny, base, small, medium, large-v3).
- [ ] İndir (ilerleme çubuğu), Aktifleştir, Sil.
- [ ] Gerçek boyut ve durum diskten okunur.
- Kanıt: küçük bir modeli indir, aktifleştir, sil testi. Büyük modelleri indirme.

### Aşama 7 — Modeller sayfası: Metin Modelleri ve "Yapay Zeka ile Temizle"
- [ ] Önce küçük deneme: LM Studio/Ollama sunucusuna bağlan, 10 bozuk örnek cümleyi temizlet, sonuçlara bakıp kalite karar ver.
- [ ] VRAM ölçümü: ses modeli ve metin modeli birlikte sığıyor mu?
- [ ] Sonra arayüz: Metin Modelleri bölümü, aktif model seçimi, "Yapay Zeka ile Temizle" düğmesi.
- Kanıt: 10 cümlelik önce/sonra tablosu, VRAM ölçümü.
- Senin yapacağın: LM Studio'da modeli sen yükle, temizleme sonuçlarını beğenip beğenmediğini söyle.

### Aşama 8 — Sağlamlaştırma ve paketleme
- [ ] Hata mesajları Türkçe ve anlaşılır (mikrofon yok, model yok, GPU yok).
- [ ] Kapanışta geçici dosyalar silinir.
- [ ] İsteğe bağlı: tek .exe paketi (PyInstaller). Antivirüs yanlış uyarı verebilir.

## Test yöntemi
| Ne test edilir | Nasıl |
| :--- | :--- |
| Mantık (geçmiş, ayarlar, dosya işlemleri) | pytest, tests/ klasöründe |
| Çeviri motoru | `--selftest` ve tests/data/test.wav |
| Arayüz görünümü | Playwright ekran görüntüsü, design/ ile karşılaştırma, DOM testi |
| Mikrofon, kısayol, başka pencereye yapıştırma | Elle test listesi ("SENİN YAPACAĞIN TEST") |

## Maliyet takibi
- Her aşama sonunda OpenRouter Activity sayfasından toplam harcamayı bak, STATE.md'deki Maliyet günlüğüne yaz.
- Aşama 3 bittiğinde harcama bütçenin yarısını geçtiyse dur ve planı gözden geçir.
