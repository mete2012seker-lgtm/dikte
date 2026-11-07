---
name: belirsizleri-sor
description: Plan uygulamasına başlamadan ya da bir işe koyulmadan önce kullan. Plan/dokümanlardaki tüm açık kararları, boşlukları ve belirsiz noktaları çıkarır, doğrulanabilecekleri kendin doğrular, kalanları tek seferde kullanıcıya `question` aracıyla sorar ve cevapları plana işler. Kullanıcı "uygula", "tek seferde uygula", "başla", "uygulamadan önce sor" ya da "açıkları sor" derse çağır.
---

# Belirsizlikleri toplu sorma

Amaç: Uygulama sırasında ani sorular ve varsayım hataları olmasın; tüm kullanıcı kararları tek turda netleşsin.

## 1. Açık noktaları çıkar
1. Plan dosyalarını (`uygulanacak plan.md`, `PLAN.md`, `UYGULAMA-PLANI.md`) baştan sona tara; şu kalıpları ara: "açık karar", "karar bekliyor", "netleşmeli", "onay bekleyen", "?", "belirsiz", "değerlendirilir", "karar verilir".
2. `STATE.md` → "Açık sorunlar" ve "Sıradaki ilk adım" bölümlerini oku.
3. `AGENTS.md` → "Teyit bekleyen varsayımlar" ve "Öneriler (onaylanmadı)" bölümlerini oku.
4. `olabilir.md` ve `Dikte-Denetim-Raporu.md` gibi kaynak dokümanlarda "karar", "açık", "belirsiz" geçen satırlara bak.
5. Her açık noktayı listeye yaz: `# | konu | seçenekler | kim karar verir (kullanıcı / ajan)`.

## 2. Kendin doğrulayabileceklerini doğrula
- Bilgiyi kullanıcıya sormadan önce makineden/depo'dan okunabilir mi bak: `git remote -v`, kurulu araçlar (`Test-Path`, `Get-Command`), dosya varlığı, API/durum sorgusu (örn. GitHub repo görünürlüğü).
- Bu şekilde netleşen maddeleri "çözüldü" olarak işaretle ve kanıtını (komut + çıktı) plana yaz.
- Yalnızca gerçekten kullanıcının tercihi olan şeyleri soru listesinde bırak: ürün davranışı, maliyet/tolerans, hukuki tercih (lisans), sistem değişikliği izni, kim ne yapacak.

## 3. Soruları tek turda sor
- `question` aracını **tek çağrıda** kullan; her açık karar için ayrı soru.
- Soru kuralları:
  - `header` 30 karakteri geçmesin.
  - Önerilen seçenek en başta ve etiketinde "(Önerilen)" olsun; gerekçesi `description` içinde.
  - Her soru bağımsız olsun; iki kararı tek soruda birleştirme.
  - Kullanıcının serbest yazabileceği yerlerde `custom` açık kalsın (varsayılan).
- Soru sayısı çoksa önce en kritik (blocker) kararları sor; küçük/hijyen kararlarını ajan kendi seçip plana "ajan kararı" olarak yazabilir.
- Soru sormadan kod yazma. Cevap gelene kadar yalnız okuma ve hazırlık.

## 4. Cevapları işle
1. Her cevabı plan dosyasının karar bölümüne yaz (örn. `uygulanacak plan.md` §1.2); eski "açık karar" başlığını "verilen kararlar" olarak değiştir.
2. Plan içindeki çapraz referansları güncelle ("karar 1.2/3" gibi).
3. Karar dokümanları etkileniyorsa senkronla: `STATE.md` (kararlar + sıradaki adım), `AGENTS.md` (Kararlar + Teyit bekleyen varsayımlar), `architecture.md` (karar geçmişi), `UYGULAMA-PLANI.md` (ilgili tablolar).
4. Yeni bilgi gerektiren maddeleri plana madde olarak ekle (örn. ikon üretimi, fixture üretimi).
5. Kullanıcı istediyse commit + push; istemediyse bekle.

## 5. Bitti tanımı
- Plan dosyasında "açık karar" başlığı kalmamış; her kararın sahibi ve değeri yazılı.
- Ajanın kendi aldığı kararlar ayrı işaretli ("ajan kararı") ve gerekçeli.
- Kullanıcıya "artık açık soru yok" bilgisi verilmiş; uygulama tek seferde başlayabilir.
