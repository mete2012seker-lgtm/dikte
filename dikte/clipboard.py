"""Pano işlemleri."""

from __future__ import annotations

import logging
import time

from . import diagnostics

logger = logging.getLogger(__name__)


class ClipboardError(RuntimeError):
    pass


def copy_text(text: str) -> None:
    """Metni Windows panosuna yazar."""
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            import pyperclip

            pyperclip.copy(text)
            return
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(0.025)
    logger.exception("Panoya kopyalanamadı", exc_info=last_exc)
    raise ClipboardError(diagnostics.MSG_CLIPBOARD_FAILED) from last_exc
