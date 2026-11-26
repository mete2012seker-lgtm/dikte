"""Ortak dosya sistemi ve süreç yardımcıları: atomik yazma, yedekleme, HF doğrulama, yükseltme."""

from __future__ import annotations

import ctypes
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import uuid
from pathlib import Path
from typing import Any

ALLOWED_HF_HOSTS = {"huggingface.co", "www.huggingface.co"}
_REPO_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Metni geçici dosyaya fsync ile yazıp atomik olarak hedefe taşır."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_name(
        f"{target.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        with open(tmp_path, "w", encoding=encoding) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def atomic_write_json(path: Path, payload: Any, indent: int = 2) -> None:
    """JSON verisini atomik olarak diske yazar."""
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=indent))


def backup_corrupt_path(path: Path) -> Path:
    """Bozuk dosya yedeklemesi için benzersiz `.bozuk-<zaman>` yolu üretir."""
    target = Path(path)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    candidate = target.with_name(f"{target.stem}.bozuk-{stamp}{target.suffix}")
    counter = 1
    while candidate.exists():
        candidate = target.with_name(f"{target.stem}.bozuk-{stamp}-{counter}{target.suffix}")
        counter += 1
    return candidate


def _validate_repo_segments(
    owner: str,
    repo_name: str,
    error_cls: type[Exception],
    invalid_msg: str,
) -> str:
    for seg in (owner, repo_name):
        if seg in {".", ".."} or not _REPO_SEGMENT_RE.match(seg):
            raise error_cls(invalid_msg)
    return f"{owner}/{repo_name}"


def normalize_hf_repo(
    repo_or_url: str,
    *,
    allow_extra_path: bool = False,
    error_cls: type[Exception] = ValueError,
    invalid_msg: str = "Geçerli bir Hugging Face repo kimliği girin (ör. kullanici/model).",
    host_msg: str = "Yalnızca huggingface.co adresleri desteklenir.",
) -> tuple[str, list[str]]:
    """Hugging Face repo kimliğini veya URL'sini doğrular ve `(owner/repo, kalan_parçalar)` döndürür."""
    if not repo_or_url or not isinstance(repo_or_url, str):
        raise error_cls(invalid_msg)
    val = repo_or_url.strip()
    if val.lower().startswith("http://") or val.lower().startswith("https://"):
        parsed = urllib.parse.urlparse(val)
        if parsed.netloc.lower() not in ALLOWED_HF_HOSTS:
            raise error_cls(host_msg)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) < 2:
            raise error_cls(invalid_msg)
        repo = _validate_repo_segments(parts[0], parts[1], error_cls, invalid_msg)
        return repo, parts[2:]

    parts = [p.strip() for p in val.split("/") if p.strip()]
    if len(parts) == 2 or (allow_extra_path and len(parts) >= 3):
        repo = _validate_repo_segments(parts[0], parts[1], error_cls, invalid_msg)
        return repo, parts[2:]
    raise error_cls(invalid_msg)


def launch_elevated(
    path: Path,
    args: list[str],
    *,
    error_cls: type[Exception] = RuntimeError,
    win32_error_fn=None,
    popen_error_fn=None,
) -> None:
    """Windows'ta UAC yükseltmesiyle, diğer platformlarda Popen ile çalıştırır."""
    target = Path(path)
    if sys.platform == "win32":
        rc = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            str(target),
            subprocess.list2cmdline(args),
            str(target.parent),
            1,
        )
        if rc <= 32:
            if win32_error_fn is not None:
                raise win32_error_fn(rc)
            raise error_cls(f"İşlem yönetici yetkisiyle başlatılamadı (kod {rc}).")
        return
    try:
        subprocess.Popen(
            [str(target), *args],
            cwd=str(target.parent),
            close_fds=True,
        )
    except OSError as exc:
        if popen_error_fn is not None:
            raise popen_error_fn(exc) from exc
        raise error_cls(str(exc)) from exc
