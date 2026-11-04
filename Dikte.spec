# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller yapilandirmasi: Dikte onedir kurulumu.

Kullanim: .venv\\Scripts\\pyinstaller.exe Dikte.spec --noconfirm
Cikti: dist\\Dikte\\Dikte.exe
"""

import os
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH)

a = Analysis(
    ["dikte\\__main__.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "dikte" / "ui"), "dikte\\ui"),
    ],
    hiddenimports=[
        "ctranslate2",
        "faster_whisper",
        "pynput",
        "sounddevice",
        "webview",
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Dikte",
    console=False,
    icon=None,
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
