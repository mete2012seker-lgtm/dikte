"""Metin motoru testleri: prompt, temizleme ve hata eşlemesi (ağ yok)."""

import pytest

from dikte import text_engine
from dikte.openrouter import OpenRouterError
from dikte.text_engine import TextEngineError, build_messages, strip_response


def chat_reply(text: str):
    return {"choices": [{"message": {"content": text}}]}


def make_transport(text: str, captured: list | None = None):
    def transport(url, payload, api_key, timeout):
        if captured is not None:
            captured.append(payload)
        return chat_reply(text)

    return transport


def run(text="Merhaba dünya bugün", **kwargs):
    options = {
        "target_language": "en",
        "translate": True,
        "provider": "openrouter",
        "api_key": "sk-or-test",
        "model": "test/model",
        "transport": make_transport("Hello world today"),
    }
    options.update(kwargs)
    return text_engine.generate(text, **options)


def test_clean_only_prompt_forbids_translation():
    messages = build_messages("Merhaba", "en", translate=False)
    system = messages[0]["content"]
    assert "yalnızca düzelt" in system
    assert "başka dile çevirme" in system


def test_translate_prompt_names_target_language():
    system = build_messages("Merhaba", "de", translate=True)[0]["content"]
    assert "Almanca" in system
    assert "çevir" in system


def test_auto_translate_skips_two_words():
    assert text_engine.should_translate_auto("iki kelime") is False


def test_auto_translate_boundary_three_words():
    assert text_engine.should_translate_auto("üç kelime var") is True


def test_auto_translate_four_words():
    assert text_engine.should_translate_auto("dört kelime var burada") is True


def test_mandatory_instruction_comes_after_user_prompt():
    messages = build_messages("Metin", "en", True, system_prompt="Kendi komutum")
    system = messages[0]["content"]
    assert system.startswith("Kendi komutum")
    assert system.index("Zorunlu talimat") > system.index("Kendi komutum")
    assert messages[1] == {"role": "user", "content": "Metin"}


def test_strip_response_removes_fences_labels_and_quotes():
    assert strip_response('```text\nMerhaba dünya.\n```') == "Merhaba dünya."
    assert strip_response('İşte metin:\nMerhaba dünya.') == "Merhaba dünya."
    assert strip_response('"Merhaba dünya."') == "Merhaba dünya."
    assert strip_response("“Merhaba dünya.”") == "Merhaba dünya."


def test_provider_none_and_local_raise_expected_codes():
    with pytest.raises(TextEngineError) as err:
        run(provider="none")
    assert err.value.code == "provider_off"
    with pytest.raises(TextEngineError) as err:
        run(provider="local")
    assert err.value.code == "local_missing"


def test_missing_key_is_reported():
    with pytest.raises(TextEngineError) as err:
        run(api_key=None)
    assert err.value.code == "no_key"


def test_401_maps_to_code():
    def transport(url, payload, api_key, timeout):
        raise OpenRouterError("401", "OpenRouter HTTP 401")

    with pytest.raises(TextEngineError) as err:
        run(transport=transport)
    assert err.value.code == "401"


def test_402_maps_to_code():
    def transport(url, payload, api_key, timeout):
        raise OpenRouterError("402", "OpenRouter HTTP 402")

    with pytest.raises(TextEngineError) as err:
        run(transport=transport)
    assert err.value.code == "402"


def test_429_retries_once_then_succeeds(monkeypatch):
    monkeypatch.setattr(text_engine, "RETRY_DELAY", 0)
    calls = []

    def transport(url, payload, api_key, timeout):
        calls.append(1)
        if len(calls) == 1:
            raise OpenRouterError("429", "OpenRouter HTTP 429")
        return chat_reply("Tamam")

    result = run(transport=transport)
    assert result.text == "Tamam"
    assert len(calls) == 2


def test_429_twice_gives_rate_limit_code(monkeypatch):
    monkeypatch.setattr(text_engine, "RETRY_DELAY", 0)

    def transport(url, payload, api_key, timeout):
        raise OpenRouterError("429", "OpenRouter HTTP 429")

    with pytest.raises(TextEngineError) as err:
        run(transport=transport)
    assert err.value.code == "429"


def test_network_error_maps_to_net():
    def transport(url, payload, api_key, timeout):
        raise OpenRouterError("net", "Sunucuya ulaşılamadı.")

    with pytest.raises(TextEngineError) as err:
        run(transport=transport)
    assert err.value.code == "net"


def test_max_tokens_is_bounded():
    captured = []
    long_text = " ".join(["kelime"] * 900)
    run(text=long_text, transport=make_transport("kısa", captured))
    assert 512 <= captured[0]["max_tokens"] <= 2048
    assert captured[0]["temperature"] == 0


def test_empty_first_response_retries_with_bigger_budget():
    budgets = []

    def transport(url, payload, api_key, timeout):
        budgets.append(payload["max_tokens"])
        if len(budgets) == 1:
            return {
                "choices": [
                    {
                        "message": {"content": None, "reasoning": "düşünüyorum"},
                        "finish_reason": "length",
                    }
                ]
            }
        return chat_reply("Merhaba dünya.")

    result = run(transport=transport)
    assert result.text == "Merhaba dünya."
    assert len(budgets) == 2
    assert budgets[1] > budgets[0]


def test_two_empty_responses_raise():
    calls = []

    def transport(url, payload, api_key, timeout):
        calls.append(1)
        return {"choices": [{"message": {"content": "   "}, "finish_reason": "stop"}]}

    with pytest.raises(TextEngineError) as err:
        run(transport=transport)
    assert err.value.code == "empty_result"
    assert len(calls) == 2


def test_content_list_is_joined():
    def transport(url, payload, api_key, timeout):
        return {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"type": "text", "text": "Mer"},
                            {"type": "text", "text": "haba"},
                        ]
                    },
                    "finish_reason": "stop",
                }
            ]
        }

    assert run(transport=transport).text == "Merhaba"


def test_empty_response_is_rejected():
    with pytest.raises(TextEngineError) as err:
        run(transport=make_transport("   "))
    assert err.value.code == "empty_result"


def test_empty_input_is_rejected():
    with pytest.raises(TextEngineError) as err:
        run(text="   ")
    assert err.value.code == "empty_text"


def test_missing_model_is_reported():
    with pytest.raises(TextEngineError) as err:
        run(model=None)
    assert err.value.code == "bad_response"


def test_explanation_response_extracts_quoted_text():
    raw = (
        "Here's the corrected and improved version of your text in English:\n\n"
        "\"I finally finished this report last night.\"\n\n"
        "Changes made:\n1. Removed filler words\n2. Fixed punctuation"
    )
    assert strip_response(raw) == "I finally finished this report last night."


def test_hallucination_guard_rejects_short_input_invention():
    invented = (
        "Here's the corrected and translated text:\n\n"
        "Original: \"ee, benim adım mehmet. ben türkçe konuşuyorum.\"\n\n"
        "Corrected and Translated: \"Hi, my name is Mehmet. I speak Turkish.\""
    )
    with pytest.raises(TextEngineError) as err:
        run(text="kısa", transport=make_transport(invented))
    assert err.value.code == "hallucination"


def test_unchanged_translation_is_reported_not_silent():
    text = "this sentence is already clean"
    result = run(text=text, transport=make_transport(text))
    assert result.unchanged is True
    assert result.translated is False


def test_wrong_output_language_is_rejected():
    turkish = "Yarın sabah saat onda toplantı var."
    with pytest.raises(TextEngineError) as err:
        run(text="yarın sabah saat dokuzda toplantı var", transport=make_transport(turkish))
    assert err.value.code == "not_translated"


def test_language_hint_recognises_three_languages():
    assert text_engine.language_hint("Yarın sabah saat onda toplantı var.") == "tr"
    assert text_engine.language_hint("This is an English sentence and it is fine.") == "en"
    assert text_engine.language_hint("Ich werde Ihnen heute Abend ein Angebot machen.") == "de"


def test_retry_uses_strict_prompt_after_bad_response():
    prompts = []

    def transport(url, payload, api_key, timeout):
        prompts.append(payload["messages"][0]["content"])
        if len(prompts) == 1:
            return chat_reply("Here is the corrected text.")
        return chat_reply("Merhaba dünya.")

    result = run(transport=transport)
    assert result.text == "Merhaba dünya."
    assert "DİKKAT" in prompts[1]


def test_finish_reason_length_with_non_empty_content_is_rejected():
    calls = []

    def transport(url, payload, api_key, timeout):
        calls.append(payload["max_tokens"])
        return {
            "choices": [
                {
                    "message": {"content": "Hello world today this is cut"},
                    "finish_reason": "length",
                }
            ]
        }

    with pytest.raises(TextEngineError) as err:
        run(text="Merhaba dünya bugün bu cümle yarım", transport=transport)
    assert err.value.code == "bad_response"
    assert len(calls) == 2
    assert calls[1] > calls[0]


def test_hallucination_and_omission_guards_for_three_or_more_words():
    # 4 kelimelik girdiye 30 kelimelik uydurma yanıt -> hallucination
    long_invented = " ".join(["word"] * 30)
    with pytest.raises(TextEngineError) as err:
        run(text="bugün hava çok güzel", transport=make_transport(long_invented))
    assert err.value.code == "hallucination"

    # 8 kelimelik gerçek cümleye 1 kelimelik aşırı kırpılmış yanıt -> bad_response
    with pytest.raises(TextEngineError) as err2:
        run(
            text="yarın sabah saat dokuzda ekip ile toplantı yapacağız",
            transport=make_transport("Tomorrow"),
        )
    assert err2.value.code == "bad_response"


def test_strip_response_preserves_single_line_dictation_with_meta_words():
    assert (
        strip_response("I corrected the mistake in the report.")
        == "I corrected the mistake in the report."
    )
    assert (
        strip_response("Note: the meeting starts at nine.")
        == "Note: the meeting starts at nine."
    )
    res = run(
        text="rapordaki hatayı düzelttim",
        target_language="en",
        translate=True,
        transport=make_transport("I corrected the mistake in the report."),
    )
    assert res.text == "I corrected the mistake in the report."

    # Çok satırlı yanıtta ise meta satırlar temizlenmeye devam etmeli
    multi = "I corrected the grammar:\nI fixed the report.\nNote: removed filler."
    assert strip_response(multi) == "I fixed the report."


def test_strip_response_qwen3_thinking_tags():
    # 1. Standart <think>...</think> bloğu temizlenmeli
    qwen_raw = "<think>\nKullanıcı Türkçe metin vermiş, İngilizceye çevirmem gerekiyor.\nAdım adım çeviriyorum.\n</think>\n\nHello world, meeting is at ten."
    assert strip_response(qwen_raw) == "Hello world, meeting is at ten."

    # 2. <thought>...</thought> bloğu temizlenmeli
    thought_raw = "<thought>Thinking about punctuation.</thought>Bu doğru bir cümledir."
    assert strip_response(thought_raw) == "Bu doğru bir cümledir."

    # 3. Kapanmamış <think> bloğu (token sınırında kesilmiş) temizlenmeli
    unclosed_raw = "<think>Düşünüyorum ama yanıt henüz gelmedi"
    assert strip_response(unclosed_raw) == ""


def test_strip_response_preserves_multiline_user_quotes():
    # Kullanıcının konuşma içinde tırnak kullandığı çok satırlı dikte
    user_speech = 'Ahmet dedi ki:\n"Yarın erkenden geleceğim."\nBiz de bekleyeceğiz.'
    # İlk satır bir açıklama meta markörü ("Here is", "İşte", vb.) olmadığı için tırnak içini tek başına çekip kırpmamalı
    assert strip_response(user_speech) == user_speech


def test_validate_output_german_and_english_without_false_not_translated():
    # 1. Almanca çeviride sık kullanılan edat ve bağlaçlarla validasyon
    german_out = "Wir treffen uns morgen um zehn Uhr im Büro für das neue Projekt."
    # Hata atmamalı
    text_engine.validate_output(
        source="Yarın saat onda yeni proje için ofiste buluşalım.",
        output=german_out,
        translate=True,
        target_language="de",
    )

    # 2. İngilizce çeviride ortak kelimeler olsa bile hedef dilde skor yüksekse geçmeli
    english_out = "We will meet in the office at ten tomorrow for the new project."
    text_engine.validate_output(
        source="Yarın saat onda yeni proje için ofiste buluşalım.",
        output=english_out,
        translate=True,
        target_language="en",
    )

    # 3. Türkçe hedef dil validasyonu
    turkish_out = "Yarın saat onda yeni proje için ofiste buluşuyoruz."
    text_engine.validate_output(
        source="We will meet in the office at ten tomorrow for the new project.",
        output=turkish_out,
        translate=True,
        target_language="tr",
    )


