"""OpenRouter model listesi ve ucuz filtre testleri (ağ yok)."""

import pytest

from dikte import config, openrouter


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OPENROUTER_MODELS_FILE", tmp_path / "openrouter_models.json")


def make_model(name, input_price, output_price, context=32000):
    return {
        "id": name,
        "name": name,
        "input_price": input_price,
        "output_price": output_price,
        "context": context,
    }


def test_filter_keeps_cheap_models():
    cheap = make_model("ucuz/model", 0.10, 0.20)
    assert openrouter.filter_cheap([cheap]) == [cheap]


def test_filter_drops_expensive_models():
    models = [
        make_model("pahali/girdi", 0.90, 0.10),
        make_model("pahali/cikti", 0.10, 2.50),
        make_model("uygun/model", 0.05, 0.05),
    ]
    ids = [model["id"] for model in openrouter.filter_cheap(models)]
    assert ids == ["uygun/model"]


def test_filter_drops_small_context():
    models = [
        make_model("kucuk/baglam", 0.01, 0.01, context=4000),
        make_model("buyuk/baglam", 0.01, 0.01, context=32000),
    ]
    ids = [model["id"] for model in openrouter.filter_cheap(models)]
    assert ids == ["buyuk/baglam"]


def test_filter_sorts_and_limits_to_twelve():
    models = [
        make_model(f"m/{index}", 0.01 * index, 0.01 * index)
        for index in range(1, 21)
    ]
    result = openrouter.filter_cheap(models)
    assert len(result) == config.OPENROUTER_MAX_MODELS
    prices = [model["input_price"] + model["output_price"] for model in result]
    assert prices == sorted(prices)


def test_list_models_writes_cache():
    models = [make_model("a/b", 0.01, 0.02)]
    result = openrouter.list_models(transport=lambda: models)
    assert [model["id"] for model in result] == ["a/b"]
    cached = openrouter.read_cache()
    assert cached["models"][0]["id"] == "a/b"
    assert openrouter.cache_is_fresh(cached)


def test_fresh_cache_skips_network():
    models = [make_model("a/b", 0.01, 0.02)]
    openrouter.list_models(transport=lambda: models)

    def boom():
        raise AssertionError("Önbellek tazeyken ağa çıkılmamalı")

    assert [m["id"] for m in openrouter.list_models(transport=boom)] == ["a/b"]


def test_refresh_bypasses_cache_and_offline_falls_back():
    openrouter.list_models(transport=lambda: [make_model("eski/model", 0.01, 0.01)])

    def offline():
        raise openrouter.OpenRouterError("net", "Sunucuya ulaşılamadı.")

    # Taze önbellek varken hata yutulur, eski liste döner.
    assert [m["id"] for m in openrouter.list_models(refresh=True, transport=offline)] == [
        "eski/model"
    ]


def test_filter_excludes_reasoning_models():
    models = [
        make_model("deepseek/deepseek-r1", 0.01, 0.02),
        make_model("qwen/qwen3-thinking", 0.01, 0.02),
        make_model("qwen/ucuz", 0.01, 0.02),
    ]
    ids = [model["id"] for model in openrouter.filter_cheap(models)]
    assert ids == ["qwen/ucuz"]


def test_filter_excludes_router_and_negative_prices():
    models = [
        make_model("openrouter/auto", -1, -1),
        make_model("openrouter/fusion", 0.01, 0.01),
        make_model("vendor/negatif", -1, 0.01),
        make_model("vendor/uygun", 0.01, 0.01),
    ]
    ids = [model["id"] for model in openrouter.filter_cheap(models)]
    assert ids == ["vendor/uygun"]


def test_free_models_are_kept():
    models = [make_model("vendor/ucretsiz", 0, 0)]
    assert [model["id"] for model in openrouter.filter_cheap(models)] == ["vendor/ucretsiz"]


def test_non_chat_models_are_excluded():
    models = [
        make_model("cohere/north-mini-code:free", 0, 0),
        make_model("vendor/embed-large", 0, 0),
        make_model("vendor/qwen3-4b", 0.02, 0.03),
    ]
    assert [model["id"] for model in openrouter.filter_cheap(models)] == ["vendor/qwen3-4b"]


def test_preferred_family_comes_first():
    models = [
        make_model("zzz/tiny-free", 0, 0),
        make_model("google/gemma-4-26b-it:free", 0, 0),
        make_model("qwen/qwen3-4b", 0, 0),
    ]
    ids = [model["id"] for model in openrouter.filter_cheap(models)]
    assert ids[0] == "google/gemma-4-26b-it:free"
    assert ids[1] == "qwen/qwen3-4b"


def test_paid_models_rank_before_free():
    models = [
        make_model("vendor/ucretsiz", 0, 0),
        make_model("vendor/ucuz-ucretli", 0.03, 0.03),
    ]
    ids = [model["id"] for model in openrouter.filter_cheap(models)]
    assert ids[0] == "vendor/ucuz-ucretli"


def test_normalize_converts_token_prices_to_million():
    item = {
        "id": "x/y",
        "name": "X",
        "pricing": {"prompt": "0.0000005", "completion": "0.0000015"},
        "context_length": 16000,
    }
    model = openrouter.normalize(item)
    assert model["input_price"] == pytest.approx(0.5)
    assert model["output_price"] == pytest.approx(1.5)
    assert model["context"] == 16000


def test_all_models_includes_expensive():
    models = [
        make_model("ucuz/model", 0.05, 0.10),
        make_model("pahali/model", 5.0, 15.0),
    ]
    assert openrouter.list_models(
        all_models=True, transport=lambda: models
    ) == models
    assert [m["id"] for m in openrouter.list_models(transport=lambda: models)] == ["ucuz/model"]


def test_cache_stores_full_catalog():
    models = [make_model("pahali/model", 5.0, 15.0), make_model("ucuz/model", 0.05, 0.1)]
    openrouter.list_models(all_models=True, transport=lambda: models)
    cached = openrouter.read_cache()
    assert cached["scope"] == "all"
    assert len(cached["models"]) == 2


def test_search_matches_id_and_name():
    models = [
        make_model("qwen/qwen3-4b", 0.05, 0.1),
        make_model("openai/gpt-x", 5.0, 15.0),
    ]
    by_id = openrouter.search(models, "qwen")
    assert [m["id"] for m in by_id] == ["qwen/qwen3-4b"]
    assert openrouter.search(models, "GPT")[0]["id"] == "openai/gpt-x"
    assert openrouter.search(models, "") == models
