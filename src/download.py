"""Download helper — enforces write-once raw data and manifest tracking.

Every file saved to data/raw/ MUST go through save_raw_file() so that:
  1. An existing file is never silently overwritten.
  2. A provenance row is appended to data/raw/MANIFEST.csv.
"""

from __future__ import annotations

import csv
import datetime
import hashlib
from pathlib import Path

# Repository root (two levels up from src/download.py)
_REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = _REPO_ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "MANIFEST.csv"

_MANIFEST_FIELDS = [
    "file_path",
    "source",
    "url_or_api",
    "series_id",
    "retrieval_utc",
    "licence",
    "sha256",
    "notes",
]


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def save_raw_file(
    content: bytes,
    filename: str,
    *,
    source: str,
    url_or_api: str,
    series_id: str,
    licence: str,
    notes: str = "",
) -> Path:
    """Write *content* to ``data/raw/<filename>`` and append a manifest row.

    Raises
    ------
    FileExistsError
        If ``data/raw/<filename>`` already exists.  Raw data is write-once.
    """
    dest = RAW_DIR / filename
    if dest.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing raw file: {dest}\n"
            "Raw data is write-once. Delete the file manually if a "
            "re-download is intentional, then re-run."
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)

    row = {
        "file_path": str(Path("data/raw") / filename),
        "source": source,
        "url_or_api": url_or_api,
        "series_id": series_id,
        "retrieval_utc": datetime.datetime.now(datetime.UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "licence": licence,
        "sha256": _sha256(dest),
        "notes": notes,
    }

    # Append to manifest (create header if the file is missing/empty)
    write_header = not MANIFEST_PATH.exists() or MANIFEST_PATH.stat().st_size == 0
    with open(MANIFEST_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_MANIFEST_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    return dest
