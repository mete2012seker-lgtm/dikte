"""Otomatik güncelleme (v1.6).

Akış: latest.json oku → sürüm karşılaştır → kurucuyu indir → SHA-256 doğrula →
Inno Setup kurucusunu sessiz kur → yeniden açılış kullanıcıya kalır.

Kurallar (UYGULAMA-PLANI §5.6, §12):
- Yalnız HTTPS; indirme adresi UPDATE_URL ile aynı alan adında olmalı.
- Ağ/bozuk dosya hatalarında uygulama çalışmaya devam eder; yarım dosya silinir.
- Sürüm tek kaynak: config.APP_VERSION. Yayın yeri henüz seçilmedi (K2):
  config.UPDATE_URL boşsa denetim "denetlenemedi" döner.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

DOWNLOAD_TIMEOUT = 60.0
CHECK_TIMEOUT = 10.0
CHUNK_SIZE = 262_144


class UpdaterError(RuntimeError):
    """Güncelleme akışında hata; kod ile birlikte taşınır."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code


def compare_versions(current: str, new: str) -> int:
    """Sayısal sürüm karşılaştırması: 1 = yeni sürüm daha büyük."""
    def parts(version: str):
        out = []
        for piece in str(version).split("."):
            digits = "".join(ch for ch in piece if ch.isdigit())
            out.append(int(digits) if digits else 0)
        return out

    cur, new = parts(current), parts(new)
    length = max(len(cur), len(new))
    cur += [0] * (length - len(cur))
    new += [0] * (length - len(new))
    if new > cur:
        return 1
    if new < cur:
        return -1
    return 0


def _fetch_json(url: str, timeout: float = CHECK_TIMEOUT) -> dict:
    if not url.lower().startswith("https://"):
        raise UpdaterError("http_rejected")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
    except UpdaterError:
        raise
    except urllib.error.HTTPError as exc:
        raise UpdaterError("http_" + str(exc.code)) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise UpdaterError("net") from exc
    except json.JSONDecodeError as exc:
        raise UpdaterError("bad_json") from exc
    if not isinstance(data, dict):
        raise UpdaterError("bad_json")
    return data


def check(force: bool = False, url: str | None = None) -> dict | None:
    """latest.json'u okur. Yeni sürüm varsa bilgi döndürür.

    force=False (açılışta sessiz denetim): ağ/sunucu hatalarında None döner,
    uygulama çalışmaya devam eder. force=True (denetle düğmesi): hata kodu fırlatır.
    """
    base = url or config.UPDATE_URL
    if not base:
        # Yapılandırılmamış yayın yeri her iki modda da açık hata (no_url).
        raise UpdaterError("no_url", "Güncelleme sunucusu yapılandırılmamış.")
    try:
        data = _fetch_json(base)
        version = str(data.get("version", "")).strip()
        download_url = str(data.get("url", "")).strip()
        sha256 = str(data.get("sha256", "")).strip().lower()
        notes = str(data.get("notes", ""))
    except UpdaterError as exc:
        if force:
            raise
        logger.info("Güncelleme denetimi başarısız (%s)", exc.code)
        return None
    if not version or not download_url:
        if force:
            raise UpdaterError("bad_json", "Güncelleme bildirimi eksik.")
        return None
    if compare_versions(config.APP_VERSION, version) <= 0:
        return {"update_available": False, "version": version, "notes": notes}
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        # Özet yoksa ya da biçimi bozuksa kurulum hiç başlamaz.
        if force:
            raise UpdaterError("bad_sha", "Güncelleme bildiriminde geçerli SHA-256 özeti yok.")
        return None
    return {
        "update_available": True,
        "version": version,
        "url": download_url,
        "sha256": sha256,
        "notes": notes,
    }


def _validate_download_host(url: str) -> str:
    """İndirme yalnız HTTPS ve yalnız UPDATE_URL ile aynı alan adına izin verir."""
    if not url.lower().startswith("https://"):
        raise UpdaterError("http_rejected")
    expected_host = urllib.parse.urlparse(config.UPDATE_URL or "").hostname
    url_host = urllib.parse.urlparse(url).hostname
    if not url_host:
        raise UpdaterError("bad_url")
    if expected_host and url_host != expected_host:
        raise UpdaterError("host_rejected")
    return url


def download(url: str, dest_dir: Path | None = None, progress=None) -> Path:
    """Kurucuyu indirir; yarım dosya .part olarak tutulur, bitince adı değişir."""
    url = _validate_download_host(url)
    dest_dir = Path(dest_dir or config.TEMP_DIR / "guncelleme")
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = Path(urllib.parse.urlparse(url).path).name or "kurulum.exe"
    final_path = dest_dir / name
    part_path = dest_dir / (name + ".part")
    if part_path.exists():
        part_path.unlink()
    request = urllib.request.Request(url, headers={"User-Agent": "Dikte-updater"})
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response, open(part_path, "wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(done, total)
    except (urllib.error.URLError, OSError) as exc:
        part_path.unlink(missing_ok=True)
        logger.info("Güncelleme indirilemedi: %s", exc)
        raise UpdaterError("net") from exc
    if total and done != total:
        part_path.unlink(missing_ok=True)
        raise UpdaterError("incomplete")
    part_path.replace(final_path)
    return final_path


def verify_sha256(path: Path, expected: str) -> bool:
    """Özeti doğrular; uyuşmazsa dosyayı siler ve False döner."""
    path = Path(path)
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    ok = digest.hexdigest().lower() == (expected or "").strip().lower()
    if not ok:
        path.unlink(missing_ok=True)
    return ok


def apply(installer_path: Path) -> None:
    """Kurucuyu sessiz kipte başlatır; uygulama kapanır, kurulum devam eder."""
    path = Path(installer_path)
    if not path.exists():
        raise UpdaterError("missing_installer")
    subprocess.Popen(
        [str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
        cwd=str(path.parent),
        close_fds=True,
    )
