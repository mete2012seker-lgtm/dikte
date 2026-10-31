# Araştırmacı ajanını "sunum hazırlama" klasörüne kurma

## Durum
- `@arastirmaci` alt ajanı dikte projesinde `.kilo/agents/arastirmaci.md` olarak tanımlı (model: openai/gpt-6-luna, provider openrouter, Exa ile araştırma yapar).
- Sunum klasörü: `C:\Users\aksek\Desktop\sunum hazırlama` (içinde yalnız kilo.jsonc var; PowerPoint MCP kurulu).
- Exa MCP global config'de, her klasörde erişilebilir; ayrıca kuruluma gerek yok.

## Adımlar
1. `C:\Users\aksek\Desktop\sunum hazırlama\.kilo\agents\` klasörlerini oluştur.
2. `arastirmaci.md` dosyasını dikte projesinden olduğu gibi kopyala (tek değişiklik: `reports/` kuralı yerine `reports/` klasörünü sunum klasörü altında kullanması zaten aynı yolu gösterir; metin değiştirilmez — ajan ilk kullanımda klasörü oluşturur).
3. Doğrulama: kopyalanan dosya mevcut ve içeriği kaynakla aynı (`diff`).

## Notlar
- Sadece `arastirmaci.md` kopyalanır; gozden-gecirici ve testci istenmedi, kopyalanmaz.
- Diğer ajanlar sonra istenirse aynı yöntemle eklenir.

## Doğrulama
- Sunum klasöründe yeni oturum açıldığında `@arastirmaci`'nin agent listesinde görünmesi (kullanıcı testi).

## Kaldırma
- `C:\Users\aksek\Desktop\sunum hazırlama\.kilo\agents\arastirmaci.md` dosyasını sil.
