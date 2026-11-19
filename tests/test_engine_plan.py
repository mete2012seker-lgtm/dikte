from dikte.engine import select_plan


def test_gpu_available_uses_large_then_cpu_fallback():
    plan = select_plan(None, True)
    assert plan[0] == ("large-v3", "cuda", "float16")
    assert plan[1] == ("small", "cpu", "int8")


def test_no_gpu_uses_small_cpu():
    assert select_plan(None, False) == [("small", "cpu", "int8")]


def test_forced_cpu_ignores_gpu():
    assert select_plan("cpu", True) == [("small", "cpu", "int8")]


def test_forced_cuda_keeps_fallback():
    plan = select_plan("cuda", False)
    assert plan[0][1] == "cuda"
    assert plan[-1][1] == "cpu"


def test_selected_model_is_tried_first_then_cpu_then_small():
    plan = select_plan(None, True, "medium")
    assert plan[0] == ("medium", "cuda", "float16")
    assert ("medium", "cpu", "int8") in plan
    assert plan[-1] == ("small", "cpu", "int8")


def test_selected_small_model_has_no_duplicate():
    plan = select_plan(None, False, "small")
    assert plan == [("small", "cpu", "int8")]


def test_selected_model_forced_cpu():
    plan = select_plan("cpu", True, "tiny")
    assert plan == [("tiny", "cpu", "int8"), ("small", "cpu", "int8")]


def test_engine_transcribe_language_mapping(tmp_path):
    from unittest.mock import MagicMock
    from dikte.engine import TranscriptionEngine

    engine = TranscriptionEngine(model_dir=tmp_path)
    mock_model = MagicMock()
    fake_segment = MagicMock()
    fake_segment.text = "Hello world"
    mock_model.transcribe.return_value = ([fake_segment], MagicMock(duration=1.5))
    engine._model = mock_model

    wav = tmp_path / "test.wav"
    wav.write_bytes(b"dummy")

    # 1. language="auto" -> faster-whisper gets language=None
    res = engine.transcribe(wav, language="auto")
    assert res.text == "Hello world"
    mock_model.transcribe.assert_called_with(
        str(wav),
        language=None,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )

    # 2. language="tr" -> faster-whisper gets language="tr"
    engine.transcribe(wav, language="tr")
    mock_model.transcribe.assert_called_with(
        str(wav),
        language="tr",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )

    # 3. language="en" -> faster-whisper gets language="en"
    engine.transcribe(wav, language="en")
    mock_model.transcribe.assert_called_with(
        str(wav),
        language="en",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )


def test_transcribe_falls_back_without_vad_when_onnxruntime_fails(tmp_path):
    from types import SimpleNamespace
    from dikte.engine import TranscriptionEngine

    calls = []

    class FakeModel:
        def transcribe(self, path, **kwargs):
            calls.append(dict(kwargs))
            if kwargs.get("vad_filter"):
                raise RuntimeError("Applying the VAD filter requires the onnxruntime package")
            return [SimpleNamespace(text="Merhaba dünya")], SimpleNamespace(duration=1.5)

    engine = TranscriptionEngine()
    engine._model = FakeModel()
    wav = tmp_path / "sample.wav"
    wav.write_bytes(b"RIFF")

    res = engine.transcribe(wav, language="tr")
    assert res.text == "Merhaba dünya"
    assert len(calls) == 2
    assert calls[0]["vad_filter"] is True
    assert calls[1]["vad_filter"] is False
    assert "vad_parameters" not in calls[1]
