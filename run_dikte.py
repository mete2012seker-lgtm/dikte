"""PyInstaller giriş noktası. Geliştirmede `python -m dikte` ile aynı işi yapar.

Göreli import (`from . import`) PyInstaller'ın ana betiğinde çalışmadığı için
dikte/__main__.py doğrudan hedeflenmez; bu dosya mutlak import kullanır.
"""

import sys

# Windows'ta pywebview (.NET/WebView2) ve CUDA DLL'leri yuklendikten sonra
# faster-whisper'in gec (lazy) onnxruntime import'u DLL bellek/TLS sinirina
# takilabiliyor (WinError 8: yeterli bellek kaynagi yok). En basta erken yukle.
try:
    import onnxruntime  # noqa: F401
except Exception:
    pass

from dikte.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
