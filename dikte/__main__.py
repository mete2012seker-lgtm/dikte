"""Komut satırı giriş noktası.

Kullanım:
    python -m dikte                 # uygulamayı aç
    python -m dikte --kurulum       # GPU testi + model indirme
    python -m dikte --selftest      # test sesini çevir
    python -m dikte --dikte-testi   # arayüzsüz kısayol/kayıt/pano testi
"""

from __future__ import annotations

import argparse
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

from . import __version__, config, diagnostics
from .engine import EngineError, TranscriptionEngine, select_plan
from .state import ERROR, PROCESSING, RECORDING, READY, STATE_LABELS


def _print_header() -> None:
    print(f"Dikte {__version__} — Python {sys.version.split()[0]}")


def cmd_install(force_device: str | None) -> int:
    _print_header()
    config.ensure_runtime_dirs()
    cuda_count = diagnostics.cuda_device_count()
    print(f"CUDA cihaz sayısı: {cuda_count}")
    plan = select_plan(force_device, cuda_count > 0)
    print("Plan:")
    for model_name, device, compute in plan:
        print(f"  - {config.model_label(model_name)} ({model_name}) / {device} / {compute}")
    print(f"Model klasörü: {config.MODELS_DIR}")
    print("İndirme başlıyor. İlk kurulumda birkaç GB indirilebilir.")

    engine = TranscriptionEngine(force_device=force_device, allow_download=True)
    try:
        engine.download_models(progress=print)
        print("Modeller indirildi, yükleme deneniyor…")
        engine = TranscriptionEngine(force_device=force_device, allow_download=False)
        info = engine.load()
    except EngineError as exc:
        print(f"HATA: {exc}")
        return 1
    except Exception as exc:
        print(f"HATA: Beklenmeyen sorun: {exc}")
        return 1

    print("Kurulum tamam.")
    print(f"  Model : {info.model_label} ({info.model_name})")
    print(f"  Cihaz : {info.device} / {info.compute_type}")
    print(f"  Süre  : {info.load_seconds} sn")
    if info.device == "CPU" and cuda_count > 0:
        print(f"UYARI: {diagnostics.MSG_GPU_FALLBACK}")
    print("Şimdi 'python -m dikte' ile uygulamayı açabilirsin.")
    return 0


def cmd_selftest(force_device: str | None, wav_path: Path) -> int:
    _print_header()
    config.ensure_runtime_dirs()
    if not wav_path.exists():
        print(f"Test sesi bulunamadı: {wav_path}")
        print("Lütfen 5-10 saniyelik Türkçe bir kaydı bu yola koy:")
        print(f"  {config.SELFTEST_WAV}")
        print("Metnini de şu dosyaya yaz (isteğe bağlı):")
        print(f"  {config.SELFTEST_TEXT}")
        return 1

    engine = TranscriptionEngine(force_device=force_device, allow_download=False)
    try:
        print("Model yükleniyor…")
        info = engine.load()
        print(f"Cihaz : {info.device} / {info.compute_type}")
        print(f"Model : {info.model_label} ({info.model_name})")
        print(f"Yükleme: {info.load_seconds} sn")
        started = time.perf_counter()
        try:
            result = engine.transcribe(wav_path)
        except EngineError:
            if info.device != "GPU":
                raise
            print("GPU çeviri yapamadı, CPU yedeğine geçiliyor…")
            info = engine.use_cpu_fallback()
            print(f"Yeni cihaz: {info.device} / {info.compute_type}")
            result = engine.transcribe(wav_path)
        total = time.perf_counter() - started
    except EngineError as exc:
        print(f"HATA: {exc}")
        return 1

    print(f"Çeviri süresi: {total:.2f} sn (ses süresi: {result.duration:.2f} sn)")
    print(f"Metin: {result.text or '(boş)'}")
    print(f"Kelime sayısı: {len(result.text.split())}")

    if config.SELFTEST_TEXT.exists():
        expected = config.SELFTEST_TEXT.read_text(encoding="utf-8").strip()
        ratio = SequenceMatcher(None, expected.lower(), result.text.lower()).ratio()
        print(f"Beklenen: {expected}")
        print(f"Benzerlik: %{ratio * 100:.0f}")
    return 0


def cmd_console_test(force_device: str | None) -> int:
    from .controller import Controller

    _print_header()
    config.ensure_runtime_dirs()
    engine = TranscriptionEngine(force_device=force_device, allow_download=False)
    controller = Controller(engine=engine)
    print("Konsol dikte testi başlıyor.")
    print("Sağ Ctrl tuşunu basılı tutup konuş, bırak. Çıkmak için Ctrl+C.")
    print("Metin panoya kopyalanır; Not Defteri'nde Ctrl+V ile kontrol et.")

    controller.start()
    last_state = None
    last_seq = 0
    last_activity = None
    exit_code = 0
    try:
        while True:
            snapshot = controller.snapshot()
            state = snapshot["state"]
            if state != last_state:
                if state == READY and snapshot["model"]:
                    print(
                        f"Durum: {STATE_LABELS[state]} | "
                        f"{snapshot['model']} · {snapshot['device']} · {snapshot['compute']}"
                    )
                else:
                    print(f"Durum: {STATE_LABELS.get(state, state)}")
                last_state = state

            if snapshot["seq"] != last_seq:
                last_seq = snapshot["seq"]
                print(f"Yeni dikte panoya kopyalandı ({len(snapshot['latest_text'].split())} kelime).")

            activity = snapshot["activity"]
            if activity:
                top = activity[0]
                key = (top["time"], top["title"], top["sub"])
                if key != last_activity:
                    last_activity = key
                    print(f"Olay: {top['title']} — {top['sub']}")

            if state == ERROR and snapshot["error"]:
                print(f"HATA: {snapshot['error']}")
                break
            time.sleep(0.15)
    except KeyboardInterrupt:
        print("\nKapatılıyor…")
    finally:
        controller.shutdown()
    return exit_code


def cmd_ui(force_device: str | None, debug: bool) -> int:
    from .controller import Controller
    from .ui.bridge import run_app

    _print_header()
    config.ensure_runtime_dirs()
    engine = TranscriptionEngine(force_device=force_device)
    return run_app(Controller(engine=engine), debug=debug)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dikte",
        description="Türkçe masaüstü dikte uygulaması (yerel faster-whisper).",
    )
    parser.add_argument("--kurulum", action="store_true", help="GPU testi yap ve modelleri indir")
    parser.add_argument("--selftest", action="store_true", help="test sesini yazıya çevir")
    parser.add_argument("--dikte-testi", action="store_true", help="arayüzsüz dikte testi")
    parser.add_argument("--cpu", action="store_true", help="CPU modunu zorla")
    parser.add_argument("--debug", action="store_true", help="arayüz geliştirici araçlarını aç")
    parser.add_argument(
        "--selftest-dosya",
        type=Path,
        default=config.SELFTEST_WAV,
        help="selftest için wav dosyası",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    diagnostics.configure_console()
    diagnostics.setup_logging()
    args = build_parser().parse_args(argv)
    force_device = "cpu" if args.cpu else None

    warning = diagnostics.python_version_warning()
    if warning:
        print(warning)

    if args.kurulum:
        return cmd_install(force_device)
    if args.selftest:
        return cmd_selftest(force_device, args.selftest_dosya)
    if args.dikte_testi:
        return cmd_console_test(force_device)
    return cmd_ui(force_device, args.debug)


if __name__ == "__main__":
    raise SystemExit(main())
