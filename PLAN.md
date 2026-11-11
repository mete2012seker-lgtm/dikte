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
- [x] Python 3.12.10 kuruldu (winget, kullanıcı kapsamı); `.venv` 3.12 ile yeniden oluşturuldu.
- [x] `.venv` + `requirements.txt` + `requirements-dev.txt` hazır; CUDA kütüphaneleri dahil.
- [x] PyAV `>=11,<16` sabitlendi: PyAV 16+ `av.open(metadata_errors=...)` parametresini kaldırdığı için faster-whisper 1.2 çeviri yapamıyordu.
- Kanıt: `python --version` = 3.12.10, 83 test geçti, `--selftest` GPU float16 ile metin üretti.
- Python 3.10 yedeği doğrulamadan sonra silindi.

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
- [x] 4 sayfa (Dikte, Dikte Geçmişi, Modeller, Ayarlar) çalışıyor (v1.2'de tamamlandı).
- Kanıt: pywebview `SAYFA_YUKLENDI` + gerçek uygulama `ready`; Playwright DOM testi; `artifacts/ui-dikte.png`.
- Senin yapacağın: Ekran görüntüsüne bakıp onay ver.

### Aşama 4 — Dikte sayfası çalışsın
- [x] Mikrofon düğmesi, durum yazısı (Dinlemeye hazır / Dinliyor / İşleniyor), metin kutusu.
- [x] Kopyala, Geri Al, dil seçici (yalnız Türkçe, pasif).
- [x] Son etkinlikler listesi (bellekte, gerçek olaylar).
- [x] Sağ panelde gerçek model, GPU/CPU ve bellek bilgisi; "İşleme hızı" yok.
- [x] "Transkripsiyonu Yenile": son kaydın sesiyle yeniden çevirir, son paragrafı değiştirir (v1.2).
- Kanıt: pytest, uçtan uca controller + pano, Playwright.
- Durum: **Kullanıcı uygulamayı çalıştırdı ve onayladı (2026-10-24). v1 tamam.**

### Aşama 5 — Dikte Geçmişi ve Ayarlar (v1.2)
- [x] Her dikte kaydedilir (tarih, süre, kelime sayısı, model, metin); son 500 kayıt.
- [x] Geçmiş: arama (Türkçe i/ı duyarsız), Tümü/Bugün/Bu hafta, Aç, Kopyala, Sil.
- [x] "Geçmişi kaydet" anahtarı: kapalıyken yeni kayıt yazılmaz, eski kayıtlar gizlenir (arşivde durur).
- [x] Ayarlar: kısayol (hazır liste: Sağ/Sol Ctrl, Sağ/Sol Alt, F8/F9/F10) + geçmiş anahtarı + geçmişi temizle.
- [x] Ayarlar `data/settings.json`, geçmiş `data/history.json` (git dışı).
- Dil ve mikrofon seçimi bu sürümde yok (pasif).
- Kanıt: `tests/test_history.py`, `tests/test_settings.py`, controller ve Playwright testleri; `artifacts/ui-gecmis.png`, `artifacts/ui-ayarlar.png`.

### Aşama 6 — Modeller sayfası: Ses Modelleri (v1.2)
- [x] 6 model: tiny, base, small, medium, large-v3, large-v3-turbo.
- [x] İndir (gerçek ilerleme yüzdesi), Aktifleştir (motoru yeniden yükle), Sil (aktif model korumalı).
- [x] Gerçek boyut ve durum diskten okunur; aktif model `settings.json`'da saklanır.
- [x] Yalnız ses modelleri; metin modelleri Aşama 7'de.
- Kanıt: `tests/test_models.py`, gerçek `large-v3 → tiny` aktifleştirme testi (`GPU / float16`), gerçek tiny silme + yeniden indirme (78.204.524 bayt), `artifacts/ui-modeller.png`.

### Aşama 7 — v1.3: Metin Modelleri, Temizle/Çevir ve otomatik yapıştırma (kapsam 2026-11-01 onaylı)
Ayrıntılı dosya/sayfa eşlemesi: `UYGULAMA-PLANI.md`.
- Ayrıntılı yerleşim, davranış ve risk listesi: `olabilir.md`.
- [x] 7a — `text_engine.py`: OpenRouter istemcisi (DPAPI ile şifreli anahtar, ucuz model filtresi, düzenlenebilir sistem promptu) + Temizle/Çevir akışı.
- [x] 7a — Ayarlar sayfasında **OpenRouter API anahtarı** alanı: gizli yazı, "Kaydet" ve "Sil" düğmeleri, anahtarın DPAPI ile şifrelenip `settings.json` yerine ayrı dosyada tutulması; "Anahtarı test et" düğmesi.
- [x] 7b — Uygulama içi GGUF kataloğu, HTTP Range ile indirme, duraklat/devam/iptal, llama.cpp ile CPU/RAM veya GPU/VRAM çalıştırma. (`llama-cpp-python` GPU/cu124 kuruldu 2026-11-03; gemma3-4b GPU 1,7 sn yükleme, ~60 tok/s. İlk çağrı ~50 sn CUDA ısınması.)
- [ ] 7c — Bellek takası: ses modeli ile metin modeli aynı anda tutulmaz; Modeller sayfasında Metin/Ses sekmeleri ve "⋯" menüsü. (Takas + sekmeler hazır; **"⋯" menüsü yok**, eylemler kart üstünde.)
- [x] 7d — Arka plan kısayolu + etkin pencereye otomatik yapıştırma.
- [ ] 7e — Dikte sayfası: Çıktı Dili (TR/EN/DE), "Otomatik çevir" kutusu, Temizle ve Çevir butonları; Playwright ve kalite testleri. (Arayüz + Playwright hazır; kalite tablosu **kısmen**: 10/10 OK var, tam girdi/çıktı çiftleri ve VRAM takas ölçümü yok.)
- Kural: aynı dilde yalnız temizlik; 3 kelimeden kısa metinde çeviri yok. Dil kararını metin modeli tek çağrıda verir.
- Kanıt: 220 pytest (2026-11-07 doğrulandı), sahte HTTP sunucusuyla duraklat/devam/iptal testi, güncel Playwright ekran görüntüleri; OpenRouter gerçek çağrı 6/6 (`reports/2026-11-01-openrouter-gercek-test.md`). Tam kalite tablosu ve VRAM ölçümü bekliyor.
- Senin yapacağın: Ayarlar → Yapay Zeka'dan anahtarı gir; mikrofon, yapıştırma ve indirme testlerini yap.

### Aşama 8 — Sağlamlaştırma
- [x] Hata mesajları Türkçe ve anlaşılır (mikrofon yok, model yok, GPU yok, sunucu kapalı).
- [x] Kapanışta geçici dosyalar silinir.
- [x] Metin modeli yokken/bağlantı kopukken ham metne düşüş doğrulanır.

### Aşama 9 — v1.4: Magic UI arayüzü ve karanlık mod
- [x] Magic UI esintili görünüm, mevcut HTML/CSS/JS içinde CSS uyarlaması (MagicCard, ShineBorder, AnimatedList, BentoGrid, DotPattern). 2026-11-03: `design/v2/ui-spec.md` + Playwright 6 efekt testi.
- [x] Karanlık mod: Sistem/Açık/Koyu; `<html class="dark">` + CSS değişkenleri; localStorage + settings.json.
- [x] `design/v2/` spec ve ekran görüntüleri (`design/v2/ui-spec.md` + koyu/açık × 4 sayfa + modeller-ses = 10 PNG); eski `design/` silinmedi.
- [x] `prefers-reduced-motion`: efektler tüm animasyonları kapatır, kenar parlaması statik kalır. (WCAG AA kontrast ölçümü yapılmadı — arayüz zaten AA'ya yakın renkler kullanıyor; ölçüm gerekirse ileride eklenir.)
- Kanıt: 206 pytest (Playwright 23 test), `design/v2/*.png`. **Kullanıcı görsel onayı 2026-11-04'te alındı; aşama kapalı.**

### Aşama 10 — v1.5: Kurucu ve kaldırma (kod yazıldı, yayın doğrulanmadı)
- [x] PyInstaller `onedir` + Inno Setup dosyaları yazıldı. (2026-11-04: `Dikte.spec` + `installer/Dikte.iss`)
- [x] Ayarlar'da büyük kırmızı "Uygulamayı Kaldır" butonu, çift onay, silinecek boyut bilgisi. (`dikte/uninstall.py` + appCard)
- [x] **Kurucu derlendi (2026-11-09):** `build.ps1` ile `dist\Dikte` ve `installer\Output\Dikte-Setup-1.6.0.exe` üretildi; `run_dikte.py` girişi ve `collect_all("llama_cpp")` eklendi.
- [x] **Kaldırma veri ve autostart temizliyor (2026-11-09):** Inno `[UninstallDelete]` + `[Code]`, "Modelleri koru" bayrağı, `[Registry]` HKCU Run temizliği.
- [x] **Inno `AppId` düzeltildi (2026-11-09):** yeni GUID; kurulum `{autopf}\Dikte`, `PrivilegesRequired=admin`.
- [ ] Kurulum → çalıştırma → kaldırma → klasörlerin silindiğinin kontrolü (kullanıcı testi; UAC gerekir).
- Kanıt hedefi: `dist\Dikte\Dikte.exe`, `Dikte-Setup-*.exe`, kur/kaldır logu, silinen klasör listesi.

### Aşama 11 — v1.6: Otomatik güncelleme (kod var, akış bozuk)
- [x] Açılışta sessiz sürüm denetimi ve Ayarlar'da **Güncelleme** kartı yazıldı. (`dikte/updater.py`, `controller.py:1281-1344`)
- [x] `latest.json` okuma, sürüm karşılaştırma, kurucu indirme, SHA-256 doğrulama ve sessiz kurulum iskeleti var.
- [x] **`sha256` akışı düzeltildi (2026-11-09):** `update_check` `sha256` döndürüyor; `update_apply` tek denetim sonucunu kullanıyor; boş/bozuk özet indirmeden reddediliyor.
- [x] **`UPDATE_URL` dolduruldu (2026-11-09):** GitHub Releases `latest.json` adresi; yapılandırılmamışsa `no_url`.
- [x] **Sürüm 1.6.0 (2026-11-09):** tek kaynak `config.APP_VERSION`.
- [ ] Güncelleme UI thread'inde senkron çalışıyor; ilerleme/iptal yok, uygulama kapanmıyor (Faz 3.3).
- [ ] GitHub Release yayınlanmadı (`latest.json` 404 veriyor); ilk Release kullanıcı tarafından yüklenecek.
- Kanıt hedefi: sahte `latest.json` ile indirme → SHA → sessiz kurulum; gerçek sürüm yükseltme kullanıcı testi.

### Aşama 12 — Yayın blockerlarını düzeltme (2026-11-07 planı)
Ayrıntı ve kabul ölçütleri: `uygulanacak plan.md` §3.
- [x] Sürüm tek kaynağı (`config.APP_VERSION`), `__init__`/`iss`/`latest.json`/User-Agent uyumu. (test_version.py)
- [x] `sha256` akışı + `UPDATE_URL` + Türkçe hata mesajları. (test_updater.py, 20 test)
- [x] Kaldırmada veri + autostart temizliği; `data_bytes` çift sayımı. (test_uninstall.py, 12 test)
- [x] `run_dikte.py` + `Dikte.spec` (collect_all llama_cpp) + `build.ps1`; PyInstaller + Inno kuruldu, derlendi.
- [x] Geçerli GUID; kurulum `{autopf}\Dikte` + admin; `.gitignore` yayın artefaktları.
- [x] LICENSE (MIT), README; 0 baytlık docs dosyaları ve `mevcut tasarım/` silindi. CI yapılandırması yok (Faz 4).
- Kanıt: pytest 245 passed / 1 skipped; `dist\Dikte\Dikte.exe` 25 sn açık kaldı; kurucu 172.888.124 bayt, SHA-256 `65a0fa04…da44d`.
- **Faz 1 kullanıcı onayı bekleniyor:** kur/kaldır (UAC), gerçek Release güncellemesi ve model/mikrofon testi.

### Aşama 13 — Faz 2: Veri kaybı ve çökme hatalarını düzeltme (2026-11-11 tamamlandı)
Ayrıntı ve kabul ölçütleri: `uygulanacak plan.md` §4.
- [x] Pano hatasında otomatik yapıştırmanın iptali (`_process` ve `_auto_ai_text`).
- [x] Kısayol (`on_hotkey_press` / `on_hotkey_release`) olay kuyruğu ve bloklamayan Whisper yüklemesi.
- [x] `_engine_lock` ile iki Whisper modelinin aynı anda yüklenmesinin engellenmesi.
- [x] `history_open` içinde `_last_history_id` güncellemesi; Temizle/Çevir'in doğru kaydı güncellemesi.
- [x] GGUF indirmede jeton kimliği (`_text_download_token`), worker `join` ve güvenli `delete_part`.
- [x] GGUF sihirli bayt (`b"GGUF"`) ve Whisper snapshot (`model.bin` + `config.json` + tokenizer) bütünlük doğrulaması.
- [x] `finish_reason == "length"` kırpılan yanıtların reddi ve ≥3 kelimede halüsinasyon/eksiltme koruması.
- [x] `strip_response` içinde tek satırlı diktelerin meta etiket yüzünden silinmemesi.
- [x] `audio.stop()` içinde `_write_wav` hatalarının `AudioError`'a sarılması.
- [x] `SettingsStore`, `HistoryStore` ve `SecretStore` için `RLock` + `uuid` benzersiz `.tmp` + `os.fsync` + `OSError` koruması.
- [x] `shutdown()` içinde `_closed` kontrolü, tüm worker thread'lerinin `join` edilmesi ve yetim `kayit-*.wav` temizliği.
- Kanıt: **263 passed, 1 skipped** (`pytest -q`); `Model: "flash"` alt ajan denetim raporu.

## Test yöntemi
| Ne test edilir | Nasıl |
| :--- | :--- |
| Mantık (geçmiş, ayarlar, model kataloğu, dosya işlemleri) | pytest, `tests/` (263 test) |
| Çeviri motoru | `--selftest` ve tests/data/test.wav |
| Arayüz görünümü | Playwright ekran görüntüsü, design/ ile karşılaştırma, DOM testi |
| Mikrofon, kısayol, başka pencereye yapıştırma | Elle test listesi ("SENİN YAPACAĞIN TEST") |

## Maliyet takibi
- Her aşama sonunda OpenRouter Activity sayfasından toplam harcamayı bak, STATE.md'deki Maliyet günlüğüne yaz.
- Aşama 3 bittiğinde harcama bütçenin yarısını geçtiyse dur ve planı gözden geçir.
