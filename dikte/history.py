"""Dikte geçmişi: yerel JSON dosyasında kayıt listesi."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path

from . import config, fsutil

logger = logging.getLogger(__name__)

_TR_FOLD = str.maketrans(
    {
        "İ": "i",
        "I": "i",
        "ı": "i",
        "Ş": "ş",
        "Ğ": "ğ",
        "Ç": "ç",
        "Ö": "ö",
        "Ü": "ü",
    }
)


def fold(text: str) -> str:
    """Türkçe arama için büyük/küçük harf ve noktalı/noktasız i farkını kaldırır."""
    return (text or "").translate(_TR_FOLD).casefold()


class HistoryError(RuntimeError):
    pass


class HistoryStore:
    """Geçmiş kayıtlarını tutar. Bozuk dosyada veriyi silmez, kenara alır."""

    def __init__(
        self,
        path: Path | None = None,
        limit: int = config.HISTORY_LIMIT,
        now_provider=None,
    ) -> None:
        self.path = Path(path or config.HISTORY_FILE)
        self.limit = max(1, int(limit))
        self._now = now_provider or datetime.now
        self._lock = threading.RLock()
        self._items: list[dict] = []
        self._counter = 0
        self.load()

    # ---------- okuma/yazma ----------

    def load(self) -> list[dict]:
        with self._lock:
            items: list[dict] = []
            if self.path.exists():
                try:
                    raw = json.loads(self.path.read_text(encoding="utf-8"))
                    if not isinstance(raw, list):
                        raise ValueError("Geçmiş bir liste değil")
                    items = [self._clean(item) for item in raw]
                    items = [item for item in items if item is not None]
                except (json.JSONDecodeError, ValueError, TypeError) as exc:
                    logger.warning("Geçmiş okunamadı (%s), yedekleniyor", exc)
                    self._backup()
                    items = []
                except OSError as exc:
                    logger.warning("Geçmiş dosyasına erişilemedi (%s), mevcut kayıtlar korunuyor", exc)
                    return [dict(item) for item in self._items]
            items.sort(key=lambda item: item["created_at"], reverse=True)
            self._items = items[: self.limit]
            self._counter = len(self._items)
            return [dict(item) for item in self._items]

    def _backup(self) -> None:
        try:
            self.path.rename(fsutil.backup_corrupt_path(self.path))
        except Exception as exc:
            logger.warning("Bozuk geçmiş dosyası yedeklenemedi: %s", exc)

    @staticmethod
    def _clean(item) -> dict | None:
        if not isinstance(item, dict):
            return None
        text = str(item.get("text", "")).strip()
        if not text:
            return None
        record_id = str(item.get("id", "")).strip()
        if not record_id:
            record_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        created_at = str(item.get("created_at", "")).strip()
        if not created_at:
            created_at = datetime.now().isoformat(timespec="seconds")
        try:
            duration = max(0.0, float(item.get("duration", 0) or 0))
        except (TypeError, ValueError):
            duration = 0.0
        try:
            words = max(0, int(item.get("words", 0) or 0))
        except (TypeError, ValueError):
            words = len(text.split())
        return {
            "id": record_id,
            "created_at": created_at,
            "duration": round(duration, 2),
            "words": words or len(text.split()),
            "model": str(item.get("model", "") or ""),
            "text": text,
        }

    def _save(self, items: list[dict] | None = None) -> None:
        target = self._items if items is None else items
        try:
            fsutil.atomic_write_json(self.path, target)
        except Exception as exc:
            raise HistoryError("Geçmiş kaydedilemedi.") from exc

    def _next_id(self, now: datetime) -> str:
        base = now.strftime("%Y%m%d-%H%M%S")
        existing = {item["id"] for item in self._items}
        candidate = f"{base}-{self._counter + 1}"
        while candidate in existing:
            self._counter += 1
            candidate = f"{base}-{self._counter + 1}"
        return candidate

    # ---------- işlemler ----------

    def add(self, text: str, duration: float, words: int, model: str = "") -> dict:
        text = (text or "").strip()
        if not text:
            raise HistoryError("Boş metin kaydedilmez.")
        now = self._now()
        with self._lock:
            counter = self._counter + 1
            base = now.strftime("%Y%m%d-%H%M%S")
            existing = {item["id"] for item in self._items}
            record_id = f"{base}-{counter}"
            while record_id in existing:
                counter += 1
                record_id = f"{base}-{counter}"
            record = {
                "id": record_id,
                "created_at": now.isoformat(timespec="seconds"),
                "duration": round(max(0.0, float(duration)), 2),
                "words": max(1, int(words or len(text.split()))),
                "model": str(model or ""),
                "text": text,
            }
            candidate_items = [record, *self._items][: self.limit]
            self._save(candidate_items)
            self._counter = counter
            self._items = candidate_items
            return dict(record)

    def list(self, query: str = "", period: str = "all") -> list[dict]:
        with self._lock:
            items = [dict(item) for item in self._items]
        needle = fold(query.strip())
        if needle:
            items = [item for item in items if needle in fold(item["text"])]
        if period in ("today", "week"):
            start = self._period_start(period)
            filtered = []
            for item in items:
                try:
                    created = datetime.fromisoformat(item["created_at"])
                except ValueError:
                    continue
                if created.tzinfo is not None and start.tzinfo is None:
                    created = created.replace(tzinfo=None)
                if created >= start:
                    filtered.append(item)
            items = filtered
        return items

    def _period_start(self, period: str) -> datetime:
        now = self._now()
        today = datetime(now.year, now.month, now.day)
        if period == "week":
            return today - timedelta(days=today.weekday())
        return today

    def get(self, record_id: str) -> dict | None:
        with self._lock:
            for item in self._items:
                if item["id"] == record_id:
                    return dict(item)
        return None

    def delete(self, record_id: str) -> bool:
        with self._lock:
            candidate_items = [item for item in self._items if item["id"] != record_id]
            if len(candidate_items) == len(self._items):
                return False
            self._save(candidate_items)
            self._items = candidate_items
            return True

    def update_last(self, text: str) -> bool:
        with self._lock:
            if not self._items:
                return False
            return self.update_text(self._items[0]["id"], text)

    def update_text(self, record_id: str, text: str) -> bool:
        text = (text or "").strip()
        if not text:
            return False
        with self._lock:
            idx = next((i for i, r in enumerate(self._items) if r["id"] == record_id), None)
            if idx is None:
                return False
            candidate_items = [dict(item) for item in self._items]
            candidate_items[idx]["text"] = text
            candidate_items[idx]["words"] = max(1, len(text.split()))
            self._save(candidate_items)
            self._items = candidate_items
            return True

    def clear(self) -> None:
        with self._lock:
            self._save([])
            self._items = []
            self._counter = 0

    def count(self) -> int:
        with self._lock:
            return len(self._items)
