import json
from datetime import datetime

from dikte.history import HistoryStore, fold


def make_store(tmp_path, now=None, limit=500):
    current = now or datetime(2026, 10, 27, 16, 0, 0)
    return HistoryStore(
        tmp_path / "history.json",
        limit=limit,
        now_provider=lambda: current,
    )


def test_add_orders_newest_first(tmp_path):
    store = make_store(tmp_path)
    first = store.add("Birinci cümle.", 2.0, 2, "small")
    second = store.add("İkinci cümle.", 3.5, 2, "large-v3")

    items = store.list()
    assert [item["id"] for item in items] == [second["id"], first["id"]]
    assert items[0]["duration"] == 3.5
    assert items[0]["model"] == "large-v3"
    assert items[0]["created_at"].startswith("2026-10-27T16:00")


def test_turkish_search_folding(tmp_path):
    store = make_store(tmp_path)
    store.add("Isparta'da ılık bir gün.", 1.0, 4)
    store.add("İzmir'e gidiyoruz.", 1.0, 2)

    assert len(store.list("ISPARTA")) == 1
    assert len(store.list("ısparta")) == 1
    assert len(store.list("ılık")) == 1
    assert len(store.list("izmir")) == 1
    assert len(store.list("İZMİR")) == 1
    assert len(store.list("ankara")) == 0
    assert fold("IĞDIR") == "iğdir"


def test_period_filters(tmp_path):
    older_day = datetime(2026, 10, 20, 9, 0, 0)
    monday = datetime(2026, 10, 26, 9, 0, 0)
    tuesday = datetime(2026, 10, 27, 16, 0, 0)

    store = make_store(tmp_path, now=older_day)
    older = store.add("Geçen hafta kaydı.", 1.0, 2)
    store._now = lambda: monday
    week_start = store.add("Pazartesi kaydı.", 1.0, 2)
    store._now = lambda: tuesday
    today = store.add("Salı kaydı.", 1.0, 2)

    item_ids = {item["id"] for item in store.list(period="today")}
    assert item_ids == {today["id"]}

    week_ids = {item["id"] for item in store.list(period="week")}
    assert week_ids == {today["id"], week_start["id"]}
    assert older["id"] not in week_ids


def test_delete_and_clear(tmp_path):
    store = make_store(tmp_path)
    record = store.add("Silinecek.", 1.0, 1)
    assert store.delete("yok") is False
    assert store.delete(record["id"]) is True
    assert store.count() == 0

    store.add("Bir.", 1.0, 1)
    store.add("İki.", 1.0, 1)
    store.clear()
    assert store.count() == 0
    assert json.loads((tmp_path / "history.json").read_text(encoding="utf-8")) == []


def test_update_last_changes_only_newest(tmp_path):
    store = make_store(tmp_path)
    old = store.add("Eski.", 1.0, 1)
    new = store.add("Yeni.", 1.0, 1)

    assert store.update_last("Düzeltilmiş metin.") is True
    items = store.list()
    assert len(items) == 2
    assert items[0]["text"] == "Düzeltilmiş metin."
    assert items[0]["words"] == 2
    assert items[0]["id"] == new["id"]
    assert items[1]["text"] == old["text"]


def test_limit_drops_oldest(tmp_path):
    store = make_store(tmp_path, limit=3)
    for index in range(5):
        store.add(f"Kayıt {index}.", 1.0, 2)
    items = store.list()
    assert len(items) == 3
    assert items[0]["text"] == "Kayıt 4."
    assert items[-1]["text"] == "Kayıt 2."


def test_corrupt_file_is_backed_up(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{bozuk", encoding="utf-8")
    store = HistoryStore(path)
    assert store.count() == 0
    assert list(tmp_path.glob("history.bozuk-*.json"))


def test_reload_keeps_records(tmp_path):
    path = tmp_path / "history.json"
    first = HistoryStore(path, now_provider=lambda: datetime(2026, 10, 27, 16, 0, 0))
    record = first.add("Kalıcı kayıt.", 2.0, 2)
    second = HistoryStore(path)
    assert second.count() == 1
    assert second.get(record["id"])["text"] == "Kalıcı kayıt."


def test_empty_text_is_rejected(tmp_path):
    import pytest

    store = make_store(tmp_path)
    with pytest.raises(Exception):
        store.add("   ", 1.0, 0)


def test_history_load_oserror_does_not_backup_or_wipe(tmp_path, monkeypatch):
    from pathlib import Path

    path = tmp_path / "history.json"
    store = make_store(tmp_path)
    rec = store.add("Korunacak kayıt.", 1.5, 2)

    def broken_read_text(self, *args, **kwargs):
        raise PermissionError("Dosya kilitli")

    monkeypatch.setattr(Path, "read_text", broken_read_text)
    items = store.load()
    assert len(items) == 1
    assert items[0]["id"] == rec["id"]
    assert path.exists()
    assert not list(tmp_path.glob("history.bozuk-*.json"))


def test_history_save_uses_unique_tmp_and_fsync(tmp_path, monkeypatch):
    import os
    from pathlib import Path

    store = make_store(tmp_path)
    fsync_calls = []
    real_fsync = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (fsync_calls.append(fd), real_fsync(fd))[1])

    seen_temps = []
    real_replace = os.replace

    def track_replace(src, dst):
        seen_temps.append(Path(src).name)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", track_replace)
    store.add("Bir.", 1.0, 1)
    store.add("İki.", 1.0, 1)

    assert len(fsync_calls) >= 2
    assert len(seen_temps) == 2
    assert seen_temps[0] != "history.json.tmp"
    assert seen_temps[0] != seen_temps[1]

