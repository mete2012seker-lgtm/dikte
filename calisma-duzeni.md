# Çalışma Düzeni — Alt Ajanlı Kod Denetimi

**Amaç:** Bir kod projesini "eksikler, yarım kalanlar ve hatalar" açısından hızlı ama kanıtlı biçimde denetlemek için kullandığım çalışma düzeni.
**Ne zaman:** Yeni bir projeyi devraldığımda, "projede ne eksik / ne bozuk" sorusu geldiğinde, yayın öncesi kontrol gerektiğinde.
**Çıktı:** Tek bir denetim raporu (`.md`) + öncelikli düzeltme planı.
**Zorunluluk:** 2026-11-07'den itibaren plan ve denetimlerde bu düzen zorunludur (AGENTS.md → "Plan ve denetim düzeni").

> Bu dosya "çalışma düzeni"dir: yeni bir oturumda bu dosyayı açıp aşağıdaki **Başlatma Promptu**'nu yapıştırmak yeterlidir.

---

## 0. Düzenin Özeti (tek bakışta)

```
Keşif (workspace + proje kökü)
   ↓
Doküman okuma (STATE / PLAN / README / architecture)
   ↓
4 PARALEL ALT AJAN  ── backend ── veri katmanı ── arayüz ── paketleme
   ↓
Sentez + çapraz doğrulama (iddia → dosya:satır kanıtı)
   ↓
Rapor (blocker → yüksek → orta → düşük → plan)
   ↓
Doğrulama (git taraması, sözdizimi, test kısıtı notu)
```

**Temel kural:** Her bulgu **dosya:satır + kısa kod alıntısı + neden yanlış + somut düzeltme** içermeli. Kanıtsız iddia rapora girmez.

---

## 1. Aşama 0 — Keşif

1. Çalışma alanını listele; boşsa projeyi çevrede ara (Masaüstü, Documents, source/repos).
2. Proje kökünü **git varlığı + kaynak klasörü + doküman** üçlüsüyle doğrula.
3. Şunları not et: dil/teknoloji, son commit, dal, takip edilmeyen dosyalar.

```powershell
Get-ChildItem -Force | Select-Object Mode,Length,LastWriteTime,Name
# adaylar:
Get-ChildItem -Directory C:\Users\<kullanıcı>\Desktop, C:\Users\<kullanıcı>\Documents |
  Select-Object FullName, LastWriteTime
```

```powershell
# proje kökünde:
git status --short
git log --oneline -10
git ls-files | Measure-Object
```

**Karar:** Birden çok proje varsa en kapsamlı olanı (git + test + kaynak) seç; kullanıcıya tek cümleyle varsayımı bildir.

---

## 2. Aşama 1 — Doküman Okuma (10 dk)

Önce projenin **kendi anlattığı durumu** oku, sonra kodla karşılaştır. Sıra:

| Dosya | Ne alınır |
|---|---|
| `README.md` | Kurulum, çalıştırma, kapsam |
| `STATE.md` / `STATUS.md` | "Bitti / yarım / açık sorun" iddiaları |
| `PLAN.md` / `ROADMAP.md` | İşaretli/işaretsiz maddeler |
| `architecture.md` | Modül haritası, bilinen sorunlar |
| `AGENTS.md` | Proje kuralları, komutlar |
| `reports/` | Önceki ölçüm ve test kanıtları |
| `requirements*.txt`, `*.spec`, `installer/` | Yayın zinciri |

**Not:** Dokümanlar **iddiadır**, kanıt değildir. Çelişki bulduğunda ikisini de rapora yaz.

---

## 3. Aşama 2 — Dört Paralel Alt Ajan

Alt ajanlar **aynı anda** başlatılır (tek mesajda 4 `subagent` çağrısı). Her biri **salt okunur** çalışır ve yalnız kendi dosya kümesine bakar; böylece bağlam bölünür ve hız artar.

| # | Rol | Kapsam | Aranan |
|---|---|---|---|
| A | **Backend çekirdek** | controller/engine/audio/hotkey/paste/state | thread yarışı, kilit, durum makinesi, kaynak sızıntısı |
| B | **Veri katmanı** | config/settings/history/models/text_models/openrouter/text_engine/secrets/diagnostics | atomik yazma, indirme bütünlüğü, hata eşlemesi |
| C | **Arayüz + köprü** | bridge.py, index.html, app.js, style.css, test_ui.py | JS↔Python uyuşmazlığı, ölü handler, yarış, XSS |
| D | **Paketleme + doküman** | __main__, updater, uninstall, spec, iss, requirements, docs | sürüm tutarlılığı, kur/kaldır, build, doküman kayması |

### Ortak alt ajan kuralları (her promptta tekrar et)

- **Salt okunur:** dosya oluşturma/değiştirme/silme yok; uygulamayı çalıştırma yok.
- Büyük dosyaları `read` ile **parça parça** oku (`offset`/`limit`).
- Her bulgu: `önem (critical/high/medium/low) | dosya:satır | kısa alıntı | neden | düzeltme`.
- Çapraz referansı **gerçekten** doğrula (JS'te çağrılan fonksiyon Python'da var mı?).
- Spekülasyon yok; okuduğun satıra dayan.
- Sonunda "yarım kalmış / hiç bağlanmamış" özellikleri ayrıca listele.
- Yanıt: kompakt markdown liste, giriş cümlesi yok.

### Prompt şablonları

**A — Backend çekirdek**
```
You are auditing <PROJE> for BUGS and INCOMPLETE code. Root: <KÖK>
READ-ONLY: do not modify/create/delete files; do not run the app.
Read fully (chunked): <DOSYALAR>
Look for: thread-safety/races, state machine errors (stuck states),
resource leaks (wav/model/locks/listeners), swallowed exceptions,
dead/unreachable paths, blocking calls on UI thread, TODO/pass stubs.
For each finding: severity, file:line, short quote, why wrong, concrete fix.
Verify by reading surrounding code; no speculation.
Return compact markdown list. No preamble.
```

**B — Veri katmanı**
```
... Root: <KÖK>. READ-ONLY.
Read fully: config.py settings.py history.py models.py text_models.py
openrouter.py text_engine.py secrets.py diagnostics.py
Look for: path/data_root bugs, atomic write (temp+fsync+replace), JSON
corruption handling, download Range/resume/pause races, size/hash
validation, DPAPI errors/key leakage, prompt parsing + language checks,
cache/pagination/timeout, duplicated constants, stubs.
Same output format.
```

**C — Arayüz + köprü**
```
... Root: <KÖK>. READ-ONLY.
Read fully: ui/bridge.py, ui/index.html, ui/app.js (chunked), style.css
selectors, tests/test_ui.py.
Look for: JS calls missing in bridge (and vice versa), wrong arg shapes,
DOM ids missing/duplicated, listener leaks, poll vs user-action races,
unhandled promise rejections, innerHTML injection, dead buttons,
settings fields not persisted, half-implemented UI.
Verify cross-file references by grepping/reading both sides.
Same output format + "test coverage gaps" section.
```

**D — Paketleme + doküman**
```
... Root: <KÖK>. READ-ONLY; do not build/install.
Read: __main__.py, updater.py, uninstall.py, *.spec, installer/*,
requirements*.txt, launcher scripts, reports/*; compare with PLAN/STATE.
Look for: version mismatch, semver compare, SHA-256 flow, silent install,
restart, uninstall data/registry cleanup, PyInstaller hiddenimports/datas,
Inno paths/privileges, missing deps, missing README/LICENSE/CI,
doc drift (claims contradicting code).
Same output format.
```

**İpucu:** 4 ajanı da **aynı mesajda** başlat; sonuçları beklerken sen bağımsız olarak `config.py`, `uninstall.py`, `.iss`, `.spec` gibi küçük dosyaları kendin oku. Böylece sentez sırasında iddiaları doğrulayabilirsin.

---

## 4. Aşama 3 — Sentez ve Çapraz Doğrulama

Alt ajan raporlarını **olduğu gibi** birleştirme. Uygula:

1. **Tekrar ayıkla:** Aynı hata iki ajanda farklı satırla geçebilir; tek maddeye indir.
2. **En kritik iddiayı kendin doğrula:** Örn. "sha256 düşürülüyor" → ilgili iki satırı aç, gör.
3. **Çelişkiyi işaretle:** Bir ajan "tamam" derken diğeri "eksik" diyorsa dosyayı aç, karar ver.
4. **Önem ölçeği:**
   - **Blocker:** Yayını/kurulumu/güncellemeyi fiilen imkânsız kılar veya veri kaybettirir.
   - **Yüksek:** Kullanıcıyı doğrudan etkileyen hata/çökme/yanlış sonuç.
   - **Orta:** Belirli koşulda bozulma, donma, yanlış mesaj.
   - **Düşük:** Hijyen, ölü kod, doküman kayması.
5. **Kanıtı olmayanı at:** "Muhtemelen", "olabilir" rapora girmez; girerse "doğrulanamadı" başlığı altına.
6. **Test maskesini ara:** Test sahtesi hatayı gizliyorsa bunu ayrıca yaz (örn. sahte yanıta eksik alan eklenmiş).

---

## 5. Aşama 4 — Rapor İskeleti

```markdown
# <Proje> — Eksiklik, Yarım İş ve Hata Raporu
Tarih | İncelenen proje/commit | Kapsam | Yöntem | Kısıt

## 0. Özet — Önce Bunlar
| # | Önem | Sorun | Yer |
(tablo: blocker'lar önce, en fazla 8-10 satır)

## 1. Yayın Zinciri
## 2. Hiç Yazılmamış / Yarım Kalan Özellikler (tablo)
## 3. Kritik / Yüksek Kod Hataları
## 4. Orta ve Düşük Bulgular
## 5. Depo Hijyeni ve Doküman Çelişkileri
## 6. Test Durumu
## 7. Öncelikli Düzeltme Planı (Faz 1-4)
## 8. Doğrulanamayanlar / Notlar
```

**Yazım kuralları**
- Her maddede `dosya:satır`; gerekiyorsa 3-5 satırlık kod bloğu.
- "Neden yanlış" + "Düzeltme" ayrı paragraf.
- Aynı konuyu iki başlıkta tekrar etme; çapraz referans ver (`(3.4)` gibi).
- Sonunda **kısa yol haritası**: 1-2 gün / 2-3 gün / 3-5 gün / 1 gün.

---

## 6. Aşama 5 — Doğrulama Kontrolleri

Raporu teslim etmeden önce:

```powershell
# 1) Gizli bilgi / büyük dosya taraması
git grep -n -I -E "sk-|api[_-]?key\s*=\s*.{8,}" -- .
git ls-files | Where-Object { (Get-Item $_).Length -eq 0 }   # boş dosyalar

# 2) Sözdizimi (yazmadan)
python -c "import ast,pathlib,sys; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('src').rglob('*.py')]; print('OK')"

# 3) Test — sandbox notu
# Proje dışına yazma engelliyse pytest'in tmp klasörü PermissionError verir.
# Bunu KOD HATASI gibi raporlama; "ortam kısıtı" olarak not düş.
```

- Derleme araçları (PyInstaller/Inno) gerçekten kurulu mu? `Test-Path` ile bak; yoksa "hiç denenmemiş" yaz.
- Test sayısı iddiası ile gerçek koşum farklıysa ikisini de yaz.

---

## 7. Sık Yapılan Hatalar (kaçın)

| Hata | Doğrusu |
|---|---|
| Alt ajan raporunu doğrulamadan aktarmak | En az 3 kritik iddiayı kendin satırdan doğrula |
| Sandbox `PermissionError`'ı proje hatası saymak | Ortam kısıtı olarak ayrı not düş |
| Doküman iddiasını kanıt saymak | Kodu aç, karşılaştır, çelişkiyi yaz |
| "Şu dosyada sorun olabilir" demek | Satır numarası + alıntı ver |
| Aynı bulguyu 3 başlıkta tekrarlamak | Tek yerde tut, çapraz referans ver |
| Yalnız hata listelemek | Öncelikli, uygulanabilir düzeltme planı ekle |

---

## 8. Başlatma Promptu (yeni oturumda kopyala-yapıştır)

```
"Açılma düzeni" ile kod denetimi yap: <PROJE YOLU>

1) Önce çalışma alanını ve proje kökünü doğrula; git durumunu/logunu al.
2) README/STATE/PLAN/architecture dosyalarını oku, iddiaları not et.
3) Aynı anda 4 salt-okunur alt ajan başlat: backend çekirdek, veri katmanı,
   arayüz+köprü, paketleme+doküman. Her birine dosya kümesini ve
   "severity | dosya:satır | alıntı | neden | düzeltme" formatını ver.
4) Sonuçları sentezle; en kritik 3 iddiayı kendin satırdan doğrula.
5) Blocker → yüksek → orta → düşük sırasıyla tek rapor yaz:
   özet tablo, yayın zinciri, yarım özellikler, kod hataları,
   depo hijyeni, test durumu, fazlı düzeltme planı.
6) Raporu `Dikte-Denetim-Raporu.md` benzeri tek dosyaya kaydet ve
   kısa bir özetle birlikte sun.
```

---

## 10. Model ve Görev Bölüşümü (Ana Model vs Swarm Alt Ajanları)

2026-11-12 kuralı uyarınca:
1. **Ana Model Rolü:** Ana model sadece en zor mimari kararlar, karmaşık kilitleme/algoritmalar, kritik köprü protokolleri ve genel koordinatörlük görevlerinde çalışır. Kolay/uzun kodları kendisi yazmaz, uzun belgeleri tek başına özetleyip vakit kaybetmez.
2. **Alt Ajanlar (`/swarm` & Sub-agents):**
   - Kolay ama uzun kodlama görevlerinde,
   - CSS/HTML arayüz uyarlamalarında (`design/dikte-ai.html`, `mikrofon_morph_animasyonu.html`),
   - Uzun belgelerin incelenmesi, özetlenmesi ve güncellenmesinde,
   - Test koşturma, hata denetimi ve doğrulama süreçlerinde
   **daima `gemini-3.8-flash-medium` (`Model: "flash"`)** ile çalıştırılır.
3. **Paralel Çalışma (`/swarm`):** Aynı anda yapılabilecek bağımsız işlerde (örneğin bir ajan arayüz animasyonunu entegre ederken diğerinin kısayol tuş dinleyicisini yazması gibi) 2 veya daha fazla alt ajan aynı anda çağrılarak işler paralel bitirilir.

