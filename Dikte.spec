# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller yapılandırması: Dikte onedir paketi.

Kullanım: .venv\\Scripts\\python.exe -m PyInstaller Dikte.spec --noconfirm
Çıktı  : dist\\Dikte\\Dikte.exe
Giriş  : run_dikte.py (göreli import sorunu yok)
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
ROOT = Path(SPECPATH)

# llama-cpp-python: DLL'ler (llama.dll, ggml*.dll) ve modüller birlikte toplanır.
llama_datas, llama_binaries, llama_hidden = collect_all("llama_cpp")

a = Analysis(
    [str(ROOT / "run_dikte.py")],
    pathex=[str(ROOT)],
    binaries=llama_binaries,
    datas=[
        (str(ROOT / "dikte" / "ui"), "dikte/ui"),
        *llama_datas,
    ],
    hiddenimports=[
        "ctranslate2",
        "faster_whisper",
        "pynput",
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "sounddevice",
        "webview",
        "pyperclip",
        "psutil",
        "winreg",
        *llama_hidden,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "torch",
        "matplotlib",
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "IPython",
        "jupyter",
        "pytest",
        "playwright",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# console=False: paketli sürümde pencere açılmaz; --selftest çıktısı görünmez (bilinçli).
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Dikte",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "installer" / "Dikte.ico") if (ROOT / "installer" / "Dikte.ico").exists() else None,
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="Dikte",
)
