# OpenRouter gerçek çağrı testi (2026-11-01)

- Model: `google/gemma-3-4b-it` (girdi $0.05/1M, çıktı $0.10/1M)
- Anahtar: DPAPI dosyasından okundu; hiçbir çıktıya veya dosyaya yazılmadı.
- Toplam yaklaşık maliyet: $0.0001

| # | Kaynak dil → hedef | Girdi | Çıktı | Süre | Maliyet |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | tr → en | merhaba bugün hava çok güzel | Hello, the weather is very nice today. | 0.65 sn | $0.000010 |
| 2 | tr → en | yarın sabah saat dokuzda toplantı var | Meeting at 9:00 AM tomorrow. | 0.77 sn | $0.000010 |
| 3 | tr → en | ben ee yani şey bu raporu dün akşam bitirdim | I finished this report yesterday evening. | 0.70 sn | $0.000010 |
| 4 | tr → de | bu akşam size bir teklif hazırlayacağım | Ich werde Ihnen heute Abend ein Angebot unterbreiten. | 0.68 sn | $0.000010 |
| 5 | en → en | this sentence is in english and should only be cleaned | This sentence is in English and should only be cleaned. | 1.02 sn | $0.000010 |
| 6 | tr → en | kısa | Short. | 0.69 sn | $0.000009 |

## Değerlendirme
- Aynı dilde (en→en) yalnız düzeltme yapıldı; metin başka dile çevrilmedi.
- 3 kelimeden kısa metin otomatik yolda atlanır; bu testte motor doğrudan çağrıldı ("kısa" → "Short.").

## Bulunan hatalar ve düzeltmeler (2026-11-01)

| Belirti | Kök neden | Düzeltme |
| :--- | :--- | :--- |
| "Model boş yanıt verdi" hatası | Düşünen (reasoning) modeller token bütçesini muhakemede harcıyor; ayrıca `openrouter/auto` gibi yönlendirici kimlikler model gibi seçiliyordu | Token tabanı 512'ye çıkarıldı, boş/`length` yanıtta bir kez daha geniş bütçeyle tekrar; `openrouter/*`, negatif fiyatlı ve muhakeme modelleri öneri listesinden çıkarıldı; eski yönlendirici seçimi açılışta temizleniyor |
| Model açıklama ve değişiklik listesi ekliyordu | Zayıf talimat takibi | Yanıttan tırnak içi son metin çıkarılıyor, açıklama satırları kesiliyor; ikinci denemede sert ("sadece son metin") prompt |
| Model çeviri yapmadan metni aynen bıraktı | Model hatası | Dil ipucu (tr/en/de) ile çıktı dili denetimi; uymazsa bir kez tekrar, olmazsa "model çeviri yapmadı" uyarısı |
| Çok kısa metinde uydurma cümle | Model halüsinasyonu | Kaynak ≤2 kelime ve çıktı beklenenden uzunsa yanıt reddedilir |

## Model karşılaştırması (3 cümle, aynı anahtar)

| Model | 9:00 korunumu | Almanca | Süre |
| :--- | :--- | :--- | :--- |
| `google/gemma-3-4b-it` | ✅ 9:00 | ✅ doğru | 0,6–1,2 sn |
| `meta-llama/llama-3.1-8b-instruct` | ✅ 9 am | ❌ "Bu abend" | 0,9–2,3 sn |
| `mistralai/mistral-nemo` | ❌ 8 o'clock | ✅ | 2,9–4,0 sn |

Varsayılan öneri sırası `gemma → qwen → llama → mistral ...` olarak değiştirildi; ücretli modeller ücretsizlerin önüne alındı (ücretsizler dakika sınırına takılıyor).
