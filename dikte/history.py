"""Dikte geçmişi: yerel JSON dosyasında kayıt listesi."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from . import config

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


def _backup_path(path: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.stem}.bozuk-{stamp}{path.suffix}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}.bozuk-{stamp}-{counter}{path.suffix}")
        counter += 1
    return candidate


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
            self.path.rename(_backup_path(self.path))
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

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(
            f"{self.path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
        )
        try:
            payload = json.dumps(self._items, ensure_ascii=False, indent=2)
            with open(temp, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self.path)
        except Exception as exc:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                pass
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
            self._counter += 1
            record = {
                "id": self._next_id(now),
                "created_at": now.isoformat(timespec="seconds"),
                "duration": round(max(0.0, float(duration)), 2),
                "words": max(1, int(words or len(text.split()))),
                "model": str(model or ""),
                "text": text,
            }
            self._items.insert(0, record)
            del self._items[self.limit :]
            self._save()
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
            before = len(self._items)
            self._items = [item for item in self._items if item["id"] != record_id]
            if len(self._items) == before:
                return False
            self._save()
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
            for record in self._items:
                if record["id"] == record_id:
                    record["text"] = text
                    record["words"] = max(1, len(text.split()))
                    self._save()
                    return True
        return False

    def clear(self) -> None:
        with self._lock:
            self._items = []
            self._counter = 0
            self._save()

    def count(self) -> int:
        with self._lock:
            return len(self._items)
