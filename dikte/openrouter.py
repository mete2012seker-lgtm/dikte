"""OpenRouter model listesi: ucuz/küçük modelleri süzer ve günlük önbellekler."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

USER_AGENT = "Dikte/1.3"


class OpenRouterError(RuntimeError):
    """OpenRouter çağrısı başarısız. `code` Türkçe mesaj seçiminde kullanılır."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _request_json(
    url: str,
    payload: dict | None = None,
    api_key: str | None = None,
    timeout: float | None = None,
) -> dict:
    data = None
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout or config.OPENROUTER_TIMEOUT) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        code = str(exc.code)
        if code not in {"401", "402", "429"}:
            code = "net"
        raise OpenRouterError(code, f"OpenRouter HTTP {exc.code}") from exc
    except Exception as exc:
        raise OpenRouterError("net", "Sunucuya ulaşılamadı.") from exc
    try:
        parsed = json.loads(body)
    except Exception as exc:
        raise OpenRouterError("bad_response", "OpenRouter geçersiz yanıt verdi.") from exc
    if not isinstance(parsed, dict):
        raise OpenRouterError("bad_response", "OpenRouter geçersiz yanıt verdi.")
    return parsed


def _per_million(value) -> float:
    try:
        return float(value) * 1_000_000
    except (TypeError, ValueError):
        return 0.0


def normalize(item: dict) -> dict:
    pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
    return {
        "id": str(item.get("id") or ""),
        "name": str(item.get("name") or item.get("id") or ""),
        "input_price": _per_million(pricing.get("prompt")),
        "output_price": _per_million(pricing.get("completion")),
        "context": int(item.get("context_length") or 0),
    }


REASONING_MARKERS = ("thinking", "reasoning", "deepseek-r1", "/r1", "-r1")
NON_CHAT_MARKERS = (
    "code", "coder", "embed", "lyria", "whisper", "tts",
    "guard", "moderation", "rerank", "classifier",
)
PREFERRED_FAMILIES = (
    "gemma", "qwen", "llama", "mistral", "phi", "deepseek-chat",
    "gpt-3", "gpt-4", "gpt-5", "claude", "command", "gemini",
)

def _probe(model: dict) -> str:
    return (str(model.get("id", "")) + " " + str(model.get("name", ""))).lower()


def is_reasoning_model(model: dict) -> bool:
    """Ucuz öneri listesinde muhakeme modellerini ayıklar (boş yanıt riski)."""
    probe = _probe(model)
    return any(marker in probe for marker in REASONING_MARKERS)


def is_non_chat_model(model: dict) -> bool:
    """Kod/gömme/ses gibi dikte düzeltmeye uygun olmayan modeller."""
    probe = _probe(model)
    return any(marker in probe for marker in NON_CHAT_MARKERS)


def is_router_model(model: dict) -> bool:
    """OpenRouter'ın kendi yönlendirici kimlikleri gerçek model değildir."""
    return str(model.get("id", "")).startswith("openrouter/")


def has_valid_price(model: dict) -> bool:
    """Negatif fiyat 'değişken/bilinmiyor' demektir; listeye alınmaz."""
    return model.get("input_price", 0) >= 0 and model.get("output_price", 0) >= 0


def family_rank(model: dict) -> int:
    """Genel sohbet ailelerini tercih sırasına göre öne alır (gemma ilk)."""
    probe = _probe(model)
    for index, marker in enumerate(PREFERRED_FAMILIES):
        if marker in probe:
            return index
    return len(PREFERRED_FAMILIES)


def filter_cheap(models: list[dict]) -> list[dict]:
    """Genel sohbet modeli + fiyat/bağlam sınırına uyan en fazla 12 model."""
    selected = [
        model
        for model in models
        if model.get("id")
        and not is_reasoning_model(model)
        and not is_non_chat_model(model)
        and not is_router_model(model)
        and has_valid_price(model)
        and model["input_price"] < config.OPENROUTER_MAX_INPUT_PRICE
        and model["output_price"] < config.OPENROUTER_MAX_OUTPUT_PRICE
        and model["context"] >= config.OPENROUTER_MIN_CONTEXT
    ]
    selected.sort(
        key=lambda model: (
            family_rank(model),
            1 if (model["input_price"] == 0 and model["output_price"] == 0) else 0,
            model["input_price"] + model["output_price"],
            model["name"],
        )
    )
    return selected[: config.OPENROUTER_MAX_MODELS]


def cache_file() -> Path:
    return Path(config.OPENROUTER_MODELS_FILE)


def read_cache() -> dict | None:
    path = cache_file()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Model önbelleği okunamadı: %s", exc)
        return None
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        return None
    return data


def cache_is_fresh(cached: dict | None) -> bool:
    if not cached or not cached.get("fetched"):
        return False
    try:
        when = datetime.fromisoformat(cached["fetched"])
    except Exception:
        return False
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - when
    return age.total_seconds() < config.OPENROUTER_CACHE_HOURS * 3600


def write_cache(models: list[dict]) -> None:
    path = cache_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scope": "all",
            "models": models,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("Model önbelleği yazılamadı: %s", exc)


def fetch_models(api_key: str | None = None, timeout: float | None = None) -> list[dict]:
    data = _request_json(config.OPENROUTER_MODELS_URL, None, api_key, timeout)
    raw = data.get("data")
    if not isinstance(raw, list):
        raise OpenRouterError("bad_response", "Model listesi anlaşılamadı.")
    return [normalize(item) for item in raw if isinstance(item, dict)]


def list_models(
    refresh: bool = False,
    all_models: bool = False,
    transport=None,
) -> list[dict]:
    """Model listesi. `all_models=False` ise yalnız ucuz/küçük modeller döner.

    Önbellek tüm kataloğu tutar; her istekte tazeyse ağa çıkılmaz.
    """
    cached = read_cache()
    fresh_all = bool(cached and cached.get("scope") == "all" and cache_is_fresh(cached))
    if fresh_all and not refresh:
        models = list(cached["models"])
    else:
        fetch = transport or fetch_models
        try:
            models = fetch()
        except OpenRouterError:
            if cached and cached.get("models"):
                models = list(cached["models"])
            else:
                raise
        else:
            write_cache(models)
    return models if all_models else filter_cheap(models)


def search(models: list[dict], query: str) -> list[dict]:
    """Ada/kimliğe göre basit arama; boş sorgu hepsini döndürür."""
    query = (query or "").strip().lower()
    if not query:
        return models
    return [
        model
        for model in models
        if query in str(model.get("id", "")).lower() or query in str(model.get("name", "")).lower()
    ]
