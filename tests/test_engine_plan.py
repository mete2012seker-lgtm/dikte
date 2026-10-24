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
