"""PyInstaller giriş noktası. Geliştirmede `python -m dikte` ile aynı işi yapar.

Göreli import (`from . import`) PyInstaller'ın ana betiğinde çalışmadığı için
dikte/__main__.py doğrudan hedeflenmez; bu dosya mutlak import kullanır.
"""

import sys

from dikte.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
