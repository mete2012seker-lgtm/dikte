# Dikte

Windows için Türkçe sesli dikte uygulaması. Sağ Ctrl tuşunu basılı tutup konuş; bırakınca
ses yerel Whisper modeliyle yazıya çevrilir ve panoya (isteğe bağlı olarak etkin pencereye) yapıştırılır.
İsteğe bağlı olarak metin Türkçe, İngilizce veya Almanca olarak temizlenip çevrilebilir.

## Çalıştırma (geliştirme)

```powershell
.venv\Scripts\python.exe -m dikte            # uygulamayı aç
.venv\Scripts\python.exe -m pytest -q        # testler
```

## Kurucu paketi

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Önce PyInstaller `dist\Dikte` klasörünü, sonra Inno Setup `installer\Output\Dikte-Setup-<sürüm>.exe`
kurucusunu üretir. Sürüm tek kaynaktan (`dikte/config.py` → `APP_VERSION`) okunur.

Kurulum `C:\Program Files\Dikte` altına yapılır ve yönetici izni ister. Kullanıcı verisi
(ayarlar, geçmiş, modeller, günlükler) `%LOCALAPPDATA%\Dikte` altındadır.

## Güncelleme

Uygulama `config.UPDATE_URL` adresindeki `latest.json` dosyasını denetler
(GitHub Releases: `latest/download/latest.json`). Dosya sürüm, kurucu bağlantısı ve SHA-256 özeti içerir.
Yeni sürüm bulunursa kurucu indirilir, özeti doğrulanır ve sessiz kurulum başlatılır.

Yeni sürüm yayınlamak için: `build.ps1` çıktısındaki kurucuyu ve SHA-256 değerini
`installer/latest.json` içine yaz, sonra kurucuyu ve `latest.json` dosyasını GitHub Release olarak yükle.

## Kaldırma

Ayarlar → Uygulamayı Kaldır. İki onay ister; "Modelleri koru" seçeneği varsayılan olarak işaretlidir.
Ayarlar, geçmiş, günlükler ve otomatik başlatma kaydı her durumda silinir.

## Lisans

MIT. Ayrıntı için `LICENSE`.

## Notlar

- `web/` klasörü Next.js + Magic UI ile yapılmış bir denemedir; üretim arayüzü değildir.
- Ses ve metin modelleri uygulama içinden indirilir; repoya dahil değildir.
