# Dikte v1.6.1

Windows için ücretsiz, açık kaynak ve tamamen yerel Türkçe sesli dikte uygulaması.

## Bu Sürümdeki Yenilikler

- **Gömülü Hata Tespit ve Log Kopyalama Aracı:** Ayarlar → *Sorun Giderme ve Tanılama* kartı ve sistem tepsisi menüsünden tek tıkla gizlilik maskeli tanılama raporu kopyalanabilir (konuşma geçmişi, ses kaydı ve API anahtarları rapora kesinlikle girmez).
- **UAC Uyumlu Güncelleme ve Kaldırma:** Kurucu ve kaldırıcı artık Windows yönetici onayı (UAC) ile sorunsuz başlatılır; uygulama güncelleme/kaldırma öncesi temizce kapanır.
- **Güvenlik ve Bütünlük Sertleştirmesi:** Kurucu ve sürüm geri alma (rollback) akışlarında SHA-256 özet doğrulaması zorunlu hale getirildi; özel Hugging Face model eklemede alan adı ve yol güvenliği eklendi.
- **Kısayol, Ses ve Pano Kararlılığı:** Takılı tuş kurtarma, klavye kancası (hook) donma koruması, pano kilidi için 3x tekrar, yönetici penceresi (UIPI) tespiti ve Whisper / yerel LLM arasında GPU bellek kilit izolasyonu eklendi.
- **Paketleme Düzeltmesi:** `faster-whisper` Silero VAD varlıkları kurucuya eksiksiz dahil edildi (`410 passed, 1 skipped`).

## İndirme ve Doğrulama

- **Kurucu:** `Dikte-Setup-1.6.1.exe` (Windows 10 / 11, 64-bit)
- **SHA-256:** `953e4f5c0f3599a09c8880efd546334e17a9535883938c0bf59967efe55f3dfd`

PowerShell ile doğrulamak için:
```powershell
Get-FileHash .\Dikte-Setup-1.6.1.exe -Algorithm SHA256
```

> **Windows SmartScreen notu:** Uygulama henüz ücretli bir kod imzalama sertifikasıyla imzalanmadığı için ilk çalıştırmada Windows "Kişisel bilgisayarınızı korudu" uyarısı gösterebilir. **Ek bilgi → Yine de çalıştır** seçeneğiyle devam edebilirsiniz. Kaynak kodun tamamı bu depoda açıktır (MIT).
