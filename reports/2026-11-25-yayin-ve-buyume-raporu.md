# Dikte — Genele Hitap Etme ve Basit Tanıtım Fikirleri (Zamansız, Sıfır Bütçe)

**Tarih:** 2026-11-25  
**Amaç:** Acele etmeden, büyük hedefler ya da ağır planlar koymadan, sıfır bütçeyle Dikte'yi daha çok normal kullanıcıya ulaştırmak (~1.000 kişi civarı yeterli).

---

## 1. Uygulamayı Daha Genele Hitap Eder Hale Getirecek Basit Dokunuşlar

Sıradan bir Windows kullanıcısının (sadece yazılımcı değil; öğrenci, ofis çalışanı, günlük kullanıcı) uygulamayı ilk açtığında sevmesi için küçük ama etkili iyileştirmeler:

1. **Bas-Bırak (tek tıkla başlat/durdur) seçeneği:** Uzun cümlelerde tuşa basılı tutmak yorucu olabiliyor; "bir kez bas konuş, tekrar bas bitsin" seçeneği herkesin işini kolaylaştırır.
2. **Ekranda küçük bir "Dinliyor…" göstergesi:** Uygulama tepside gizliyken konuşmaya başlayınca ekranda ufak bir işaret çıkmaması insanı tereddütte bırakıyor; ekranın altında beliren küçük bir "Dinliyor / Yazıyor" kutucuğu uygulamayı çok daha anlaşılır ve şık hissettirir.
3. **Mikrofon seçimi:** Kulaklık veya harici mikrofon takanların yanlış mikrofonda takılıp "çalışmıyor" dememesi için Ayarlar'a basit mikrofon listesi.
4. **Teknik terimleri arka plana almak:** İlk açılışta `CUDA`, `GGUF`, `OpenRouter`, `VAD` gibi terimler yerine sadece **"Konuş → Yapıştır"** akışını öne çıkarmak; teknik ayarları "Gelişmiş" altında tutmak.
5. **Ufak pürüzleri temizlemek:** 2026-11-24 denetimindeki takılı tuş kurtarma (`hotkey.py:392`) ve tepsideyken pil/CPU harcama (`app.js:726`) gibi göze çarpmayan ama kullanıcıyı yorabilecek pürüzleri düzeltmek.

---

## 2. Site ve İndirme Tarafında Küçük Güzelleştirmeler

1. **Link önizleme kartı (`docs/index.html`):** Linki WhatsApp, Discord, YouTube veya forumda paylaştığında düz yazı yerine kapak görseli ve kısa özet çıksın (`og:image`, `og:title`).
2. **Günlük dilden örnekler:** Sitede teknik özelliklerden önce herkesin anladığı 3–4 örnek (*WhatsApp Web, Word, ödev/not, ChatGPT*).
3. **SmartScreen açıklaması:** İndirme butonunun yanında mavi Windows uyarısının normal olduğunu tek satırla, sakin ve net anlatmak (ileride istenirse ücretsiz Microsoft Store veya `winget` düşünülebilir, acelesi yok).
4. **GitHub etiketleri:** Depoya bir kerelik `turkish`, `windows`, `whisper`, `voice-typing`, `offline`, `free` etiketlerini eklemek.

---

## 3. Sıfır Bütçeyle Basit Tanıtım Fikirleri (Canın İstedikçe, Süre Sınırı Yok)

1. **YouTube'a 1 tane kısa kurulum/kullanım videosu (1–2 dk):** *"Windows'ta Ücretsiz ve İnternetsiz Sesle Yazma — Dikte"* başlığıyla yükleyip bırakmak. Arama yapan insanlar zamanla kendiliğinden bulur.
2. **Basit kısa videolar (YouTube Shorts / Reels / TikTok):** Süslü kurgu gerekmez; 20–30 saniyelik gerçek ekran kaydıyla:
   - WhatsApp veya Word'de tuşa basıp konuşarak anında yazma,
   - İnternet (Wi-Fi) kapalıyken yazma,
   - Türkçe konuşup İngilizce metin çıkarma,
   - ChatGPT'ye klavyesiz prompt söyleme.
3. **1–2 foruma/topluluğa samimi paylaşım:** Ne zaman uygun olursan Technopat Sosyal, DonanımHaber veya Reddit'te (`r/Turkey` vb.) *"Ücretsiz, reklamsız, internetsiz Türkçe sesle yazma aracı yaptım, işinize yararsa buyurun"* şeklinde tek bir paylaşım.
4. **Bir kere ekleyip unutmalık dizin:** AlternativeTo'ya eklemek (10–15 dk, sonra kendi kendine trafik getirir).

---

## 4. Benzer Ücretsiz Projelerden Çıkan 4 Sade Ders (Araştırma Özeti)

2025–2026'da ücretsiz/açık kaynak sesli dikte uygulamaları (`Handy`, `Buzz`, `OpenWhispr`, `Vibe`, `Whispering`, `HoldToSpeak`, `LocalFlow`, `PieFlow`) incelendiğinde sıradan kullanıcıyı çeken ortak noktalar şunlar:

1. **Sadelik ve tek iş:** İnsanlar çok ayarlı karmaşık araçlardan çok *"kısayola bas, konuş, nereye yazıyorsan oraya düşsün"* diye çalışan sade araçları tutuyor (`Handy` bununla büyüdü).
2. **Ekranda ufak geri bildirim:** Tepside çalışırken ekran altında küçük bir "Dinliyor / Yazıyor" göstergesi ve tek tıkla başlat/durdur (bas-bırak) seçeneği, günlük kullanımda en çok övülen iki küçük detay.
3. **Günlük kullanım senaryoları:** Yazılımcıların ChatGPT/Claude'a konuşarak soru sormasının yanında; öğrenciler (ödev/not), hızlı mesaj yazanlar ve klavyede yorulan/bileği ağrıyan kullanıcılar bu tür araçları en çok paylaşan gruplar.
4. **Kısa gerçek ekran videosu:** Stüdyo reklamından çok, bilgisayarda canlı konuşup metnin anında ekrana düşmesini gösteren 20–30 saniyelik basit videolar (YouTube Shorts / Reels / TikTok) ve 1–2 dakikalık bir YouTube kurulum videosu sıfır bütçeyle en doğal kullanıcı akışını sağlıyor.

## 5. Kaynaklar (Exa Araştırması — 2026-11-25)
- `https://github.com/cjpais/Handy` & WIRED incelemesi (`https://www.wired.com/story/handy-free-speech-to-text-app/`)
- `https://github.com/OpenWhispr/openwhispr`
- `https://github.com/chidiwilliams/buzz`
- `https://github.com/thewh1teagle/vibe`
- `https://holdtospeak.com/`, `https://github.com/nexos-1/localflow`, `https://github.com/shivankoctupie/pieflow`, `https://github.com/ahmedhmam1994/voxscribe-ai-voice-dictation`
- Microsoft Store ücretsiz bireysel geliştirici kaydı (`https://blogs.windows.com/windowsdeveloper/2025/09/10/free-developer-registration-for-individual-developers-on-microsoft-store/`) ve masaüstü uygulama organik keşif notları (`https://zeroraised.com/blog/how-to-market-a-desktop-app`, `https://dev.to/vidur_saini/how-to-get-your-first-1000-app-installs-without-paid-ads-f0c`)

