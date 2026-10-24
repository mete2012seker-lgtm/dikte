"""Pano işlemleri."""

from __future__ import annotations

import logging

from . import diagnostics

logger = logging.getLogger(__name__)


class ClipboardError(RuntimeError):
    pass


def copy_text(text: str) -> None:
    """Metni Windows panosuna yazar."""
    try:
        import pyperclip

        pyperclip.copy(text)
    except Exception as exc:
        logger.exception("Panoya kopyalanamadı")
        raise ClipboardError(diagnostics.MSG_CLIPBOARD_FAILED) from exc
