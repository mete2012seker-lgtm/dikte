"""Metin temizleme/çeviri motoru. Sağlayıcıdan bağımsız; ağ yalnız burada."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from . import config, openrouter

logger = logging.getLogger(__name__)

# 429'da tek deneme öncesi beklenecek süre; testlerde sıfırlanır.
RETRY_DELAY = 1.0


class TextEngineError(RuntimeError):
    """Metin işlemi başarısız. `code` arayüzde Türkçe mesaja çevrilir."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or CODE_MESSAGES.get(code, "Metin işlenemedi."))
        self.code = code


CODE_MESSAGES = {
    "provider_off": "Metin sağlayıcısı kapalı. Ayarlar → Yapay Zeka'dan seç.",
    "no_key": "OpenRouter anahtarı yok. Ayarlar'dan ekle.",
    "401": "OpenRouter anahtarı geçersiz. Ayarlar'dan kontrol et.",
    "402": "OpenRouter bakiyesi yetersiz.",
    "429": "Çok fazla istek. Biraz bekleyip tekrar dene.",
    "net": "Sunucuya ulaşılamadı; metin değişmedi.",
    "local_missing": "Metin modeli yüklü değil. Modeller sayfasından indir.",
    "local_load": "Metin modeli yüklenemedi; metin değişmedi.",
    "bad_response": "Model geçerli yanıt vermedi; metin değişmedi.",
    "not_translated": "Model çeviri yapmadı; farklı bir model seçmeyi dene.",
    "hallucination": "Model metne bilgi ekledi; farklı bir model seçmeyi dene.",
    "empty_result": "Model boş yanıt verdi; metin değişmedi. Farklı bir model seçmeyi dene.",
    "empty_text": "İşlenecek metin yok.",
}


@dataclass
class TextResult:
    text: str
    translated: bool
    usage: dict | None = None
    unchanged: bool = False


def count_words(text: str) -> int:
    return len((text or "").split())


def should_translate_auto(text: str) -> bool:
    """Otomatik çeviride 3 kelimeden kısa metin dokunulmadan bırakılır."""
    return count_words(text) >= config.MIN_AUTO_TRANSLATE_WORDS


def mandatory_instruction(target_language: str, translate: bool) -> str:
    label = config.OUTPUT_LANGUAGES.get(target_language, config.OUTPUT_LANGUAGES["tr"])
    task = "düzelt ve hedef dile çevir" if translate else "yalnızca düzelt"
    same = (
        "Metin zaten hedef dildeyse yalnızca düzelt ve çeviri yapma."
        if translate
        else "Metni başka dile çevirme; yalnızca aynı dilde düzelt."
    )
    return (
        f"Zorunlu talimat: Hedef dil {label}. Görev: {task}. {same} "
        "Yanıt olarak yalnızca son metni döndür; açıklama, başlık, tırnak veya kod bloğu ekleme."
    )


def build_messages(
    text: str,
    target_language: str = "tr",
    translate: bool = True,
    system_prompt: str | None = None,
    strict: bool = False,
) -> list[dict]:
    base = (system_prompt or config.DEFAULT_SYSTEM_PROMPT).strip()
    system = base + "\n\n" + mandatory_instruction(target_language, translate)
    if strict:
        system += (
            "\n\nDİKKAT: Yanıtın SADECE son metin olacak. Açıklama, değişiklik listesi,"
            " 'İşte', 'Here is', 'Changes made', 'Original' gibi ifadeler, tırnak veya"
            " kod bloğu yazma. Kaynakta olmayan bilgi ekleme."
        )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]


def _strip_label(line: str) -> bool:
    # "İ".lower() birleşik nokta üretir (i̇); onu atarak karşılaştırırız.
    lowered = line.strip().lower().replace("\u0307", "")
    labels = ("işte metin:", "işte çeviri:", "işte:", "metin:", "çeviri:",
              "düzeltilmiş metin:", "son metin:")
    return any(lowered.startswith(label) for label in labels)


def _is_meta_line(line: str) -> bool:
    lowered = line.strip().lower().replace("\u0307", "")
    return any(lowered.startswith(marker) for marker in META_MARKERS)


META_MARKERS = (
    "changes made", "here is the", "here's the", "here is your", "here's your",
    "i corrected", "explanation", "note:", "corrected and", "translated:",
    "değişiklik", "işte metin", "işte çeviri", "açıklama:", "orijinal metin",
    "original:", "düzeltilmiş metin",
)


def _first_quote(text: str) -> str | None:
    import re

    lowered = text.lower().replace("\u0307", "")
    for marker in ("corrected and translated", "corrected and", "corrected:",
                   "translated:", "çeviri:", "düzeltilmiş:"):
        index = lowered.find(marker)
        if index == -1:
            continue
        match = re.search(r'["“«]([^"“”«»]{2,})["”»]', text[index:], re.DOTALL)
        if match:
            return match.group(1).strip() or None
    match = re.search(r'["“«]([^"“”«»]{2,})["”»]', text, re.DOTALL)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def strip_response(raw: str) -> str:
    """Modelin eklediği tırnak, başlık, açıklama ve kod bloğu işaretlerini temizler."""
    text = _strip_fences(raw or "")
    lowered = text.lower()
    if any(marker in lowered for marker in META_MARKERS):
        quoted = _first_quote(text)
        if quoted:
            return quoted
        cut = len(text)
        for marker in ("changes made", "değişiklikler", "explanation:", "açıklama:"):
            index = lowered.find(marker)
            if index != -1:
                cut = min(cut, index)
        text = text[:cut].strip()
        lines = text.splitlines()
        while lines and _is_meta_line(lines[0]):
            lines = lines[1:]
        text = "\n".join(lines).strip()

    lines = text.splitlines()
    if lines and _strip_label(lines[0]):
        lines = lines[1:]
    text = "\n".join(lines).strip()
    for left, right in (('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"), ("`", "`")):
        if len(text) >= 2 and text.startswith(left) and text.endswith(right):
            text = text[1:-1].strip()
    return text


TR_WORDS = {
    "ve", "bir", "bu", "için", "çok", "var", "ile", "şey", "daha", "gibi",
    "değil", "de", "da", "ama", "ben", "sen", "saat", "bugün", "yarın",
}
EN_WORDS = {
    "the", "and", "is", "are", "was", "were", "this", "that", "to", "of",
    "in", "a", "an", "i", "you", "it", "we", "they", "my", "for", "with",
}
DE_WORDS = {
    "der", "die", "das", "und", "ist", "ich", "nicht", "ein", "eine", "zu",
    "sie", "wir", "mit", "für", "auf", "einem", "einen", "werde",
}


def language_hint(text: str) -> str | None:
    """Kaba dil tahmini (tr/en/de). Emin değilse None döner."""
    import re

    lowered = (text or "").lower()
    tokens = re.findall(r"[a-zçğıöşü]+", lowered)
    turkish_chars = sum(1 for char in lowered if char in "çğıöşü")
    scores = {
        "tr": sum(1 for token in tokens if token in TR_WORDS) + (1 if turkish_chars >= 2 else 0),
        "en": sum(1 for token in tokens if token in EN_WORDS),
        "de": sum(1 for token in tokens if token in DE_WORDS),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None


def validate_output(source: str, output: str, translate: bool, target_language: str = "tr") -> None:
    """Modelin uydurduğu, çevirmediği veya yanlış dilde bıraktığı yanıtları yakalar."""
    if not output.strip():
        raise TextEngineError("empty_result")
    source_words = count_words(source)
    output_words = count_words(output)
    if output_words > 3 + source_words * 2 and source_words <= 2:
        raise TextEngineError("hallucination")
    lowered = output.lower()
    if any(marker in lowered for marker in META_MARKERS):
        raise TextEngineError("bad_response")
    if translate and source_words >= 3:
        hint = language_hint(output)
        if hint and hint != target_language:
            raise TextEngineError("not_translated")


def _max_tokens(text: str) -> int:
    """Düşünen modeller muhakemeye token harcar; taban yüksek tutulur."""
    return max(512, min(config.TEXT_REQUEST_MAX_TOKENS, count_words(text) * 8 + 128))


def _openrouter_call(payload: dict, api_key: str, transport, timeout: float | None):
    call = transport or openrouter._request_json
    try:
        return call(config.OPENROUTER_CHAT_URL, payload, api_key, timeout)
    except openrouter.OpenRouterError as exc:
        if exc.code == "429":
            time.sleep(RETRY_DELAY)
            try:
                return call(config.OPENROUTER_CHAT_URL, payload, api_key, timeout)
            except openrouter.OpenRouterError as retry_exc:
                raise TextEngineError(retry_exc.code, str(retry_exc)) from retry_exc
        raise TextEngineError(exc.code, str(exc)) from exc


def _extract(data: dict) -> tuple[str, str | None]:
    """Yanıttan metni ve bitiş nedenini çıkarır. Boş yanıt da döndürür, karar çağırana aittir."""
    choices = data.get("choices") if isinstance(data, dict) else None
    if not isinstance(choices, list) or not choices:
        return "", None
    first = choices[0] if isinstance(choices[0], dict) else {}
    finish = first.get("finish_reason")
    message = first.get("message") if isinstance(first.get("message"), dict) else {}
    content = message.get("content")
    if content is None:
        content = first.get("text") or ""
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    if not isinstance(content, str):
        content = ""
    return content, finish if isinstance(finish, str) else None


def generate(
    text: str,
    *,
    target_language: str = "tr",
    translate: bool = True,
    provider: str = "openrouter",
    api_key: str | None = None,
    model: str | None = None,
    system_prompt: str | None = None,
    transport=None,
    timeout: float | None = None,
) -> TextResult:
    """Metni temizler (ve gerekirse çevirir). Hata durumunda istisna fırlatır."""
    text = (text or "").strip()
    if not text:
        raise TextEngineError("empty_text")

    if provider == "none":
        raise TextEngineError("provider_off")
    if provider == "local":
        # GGUF desteği sonraki partide bağlanır (UYGULAMA-PLANI parti 7).
        raise TextEngineError("local_missing")
    if provider != "openrouter":
        raise TextEngineError("provider_off")

    if not api_key:
        raise TextEngineError("no_key")
    if not model:
        raise TextEngineError("bad_response", "Metin modeli seçilmemiş.")

    messages = build_messages(text, target_language, translate, system_prompt)
    budget = _max_tokens(text)
    last_finish = None
    last_error: TextEngineError | None = None
    for attempt in range(2):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": budget,
        }
        data = _openrouter_call(payload, api_key, transport, timeout)
        content, last_finish = _extract(data)
        candidate = strip_response(content)
        try:
            validate_output(text, candidate, translate, target_language)
        except TextEngineError as exc:
            last_error = exc
            logger.info("Yanıt doğrulanamadı (%s, finish=%s)", exc.code, last_finish)
            if attempt == 0:
                messages = build_messages(
                    text, target_language, translate, system_prompt, strict=True
                )
                if exc.code == "empty_result" or last_finish == "length":
                    budget = min(config.TEXT_REQUEST_MAX_TOKENS, budget * 2)
                continue
            raise
        same = (
            translate
            and count_words(text) >= 3
            and candidate.strip().lower() == text.strip().lower()
        )
        if same and attempt == 0:
            messages = build_messages(
                text, target_language, translate, system_prompt, strict=True
            )
            continue
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else None
        return TextResult(
            text=candidate,
            translated=bool(translate) and not same,
            usage=usage,
            unchanged=same,
        )
    raise last_error or TextEngineError("bad_response")
