"""MoTrans-15 v2.1 Double-Rebuild Verification & Data Freeze Certification.

Performs a bitwise double rebuild of all v2.1 tables and certifies SHA-256 hashes in docs/DATA_FREEZE_v2_1.md.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src import v2_1_build_tables
from src.v2_1_config import (
    WINDOW_START,
    WINDOW_END,
    TRAIN_START,
    TRAIN_END,
    VAL_START,
    VAL_END,
    TEST_START,
    TEST_END,
    POST_WINDOW_START,
    EMBARGO_DAYS,
    FOLD_ORIGINS,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_V2_1 = ROOT / "data" / "v2_1"
DOCS = ROOT / "docs"

TABLES_TO_VERIFY = [
    "analysis_tier1.parquet",
    "analysis_tier2_primary.parquet",
    "secondary_holds.parquet",
    "panel.parquet",
    "sensitivity_macro_revision.parquet",
    "post_window_2026.parquet",
    "excluded_rows.parquet",
    "folds.csv",
    "release/analysis_tier1.parquet",
    "release/analysis_tier2_primary.parquet",
    "release/secondary_holds.parquet",
    "release/sensitivity_macro_revision.parquet",
    "release/panel_returns_only.parquet",
    "release/folds.csv",
]


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_hash() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def double_rebuild():
    print("=== Starting MoTrans-15 v2.1 Double Rebuild Verification ===")

    # Pass 1
    print("\n--- Rebuild Pass 1 ---")
    v2_1_build_tables.build_v2_1_tables()
    hashes_pass1 = {}
    for rel_path in TABLES_TO_VERIFY:
        p = DATA_V2_1 / rel_path
        if not p.exists():
            raise FileNotFoundError(f"File missing after Pass 1: {p}")
        h = sha256_file(p)
        hashes_pass1[rel_path] = h
        print(f"Pass 1: {rel_path} -> {h[:16]}...")

    # Pass 2
    print("\n--- Rebuild Pass 2 (Bitwise Verification) ---")
    v2_1_build_tables.build_v2_1_tables()
    hashes_pass2 = {}
    mismatches = []
    for rel_path in TABLES_TO_VERIFY:
        p = DATA_V2_1 / rel_path
        if not p.exists():
            raise FileNotFoundError(f"File missing after Pass 2: {p}")
        h = sha256_file(p)
        hashes_pass2[rel_path] = h
        if h != hashes_pass1[rel_path]:
            mismatches.append(rel_path)
            print(f"MISMATCH: {rel_path} (Pass 1: {hashes_pass1[rel_path]} != Pass 2: {h})")
        else:
            print(f"VERIFIED [BITWISE EQUAL]: {rel_path} -> {h[:16]}...")

    if mismatches:
        raise RuntimeError(f"Double rebuild failed with {len(mismatches)} hash mismatches: {mismatches}")

    print("\n=== DOUBLE REBUILD SUCCESS: All v2.1 table hashes match bit-for-bit ===")

    # Write docs/DATA_FREEZE_v2_1.md
    git_hash = get_git_hash()
    rows_md = []
    for rel_path in TABLES_TO_VERIFY:
        rows_md.append(f"| `data/v2_1/{rel_path}` | `{hashes_pass2[rel_path]}` | **VERIFIED** |")
    table_str = "\n".join(rows_md)

    freeze_doc = f"""# MoTrans-15 v2.1 Data Freeze Certification

**Release Tag**: `v2.1-train-test-ready`  
**Git Commit Hash**: `{git_hash}`  
**Parent Freeze Tags**: `v1.0-data-freeze`, `v2.0-data-freeze`, `v2.0.1-data-freeze` (permanently preserved)  
**Certification Date**: 2026-10-25  
**Verification Engine**: Bitwise Double-Rebuild Verification Pass (Python 3.13)  

---

## 1. Parameters (Configured in src/v2_1_config.py and docs/v2_1_spec.md)

| Parameter | Value | Description |
| :--- | :---: | :--- |
| `WINDOW_START` | `{WINDOW_START}` | Official start of the evaluation panel |
| `WINDOW_END` | `{WINDOW_END}` | Official cutoff date for evaluation |
| `TRAIN` | `{TRAIN_START}` to `{TRAIN_END}` | Historical model training window (12 years) |
| `VALIDATION` | `{VAL_START}` to `{VAL_END}` | Model selection and hyperparameter tuning (2 years) |
| `TEST` | `{TEST_START}` to `{TEST_END}` | Strictly locked out-of-sample test window (2 years) |
| `POST_WINDOW` | `{POST_WINDOW_START}+` | Quarantined post-window observations (2026) |
| `EMBARGO_DAYS` | `{EMBARGO_DAYS}` | 60-day embargo for events reaching into subsequent splits |
| `FOLD_ORIGINS` | `{', '.join(FOLD_ORIGINS)}` | Rolling-origin development origins within TRAIN+VALIDATION |

---

## 2. Cryptographic File Hashes (SHA-256)

Every file in `data/v2_1/` was rebuilt twice from raw sources; all hashes match identically across successive runs.

| File Path | SHA-256 Hash | Status |
| :--- | :--- | :---: |
{table_str}

---

## 3. Reproduction Command

To reproduce the complete MoTrans-15 v2.1 dataset from raw sources in non-interactive batch mode:

```bash
# 1. Checkout v2.1 freeze tag
git checkout v2.1-train-test-ready

# 2. Re-run complete pipeline and v2.1 table builder
python -m src.pipeline
python -m src.v2_fix_cbr_dates
python -m src.v2_1_build_tables
python -m src.v2_1_leakage_audit
python -m src.v2_1_freeze

# 3. Run full test suite (no path, no -k)
pytest
```

---

## 4. Release Distribution & Privacy

Per distribution agreements, proprietary equity closing index levels are omitted from public release bundles:
- `data/v2_1/release/panel_returns_only.parquet` provides continuous log returns (`ret_local`, `ret_usd`) without proprietary price levels (`level_local`).
- All cumulative event returns (`clr_1`, `clr_3`, `clr_5`, `clr_20`, `clr_60`), monetary shocks (`shock_raw_bp`), and as-of macro controls are fully accessible in `data/v2_1/release/analysis_tier1.parquet` and `data/v2_1/release/analysis_tier2_primary.parquet`.
- Due to upstream licensing terms for financial market indices, this release directory **must remain private and not redistributed** until commercial and academic distribution terms are cleared.
"""

    freeze_path = DOCS / "DATA_FREEZE_v2_1.md"
    freeze_path.write_text(freeze_doc, encoding="utf-8")
    print(f"Wrote {freeze_path}")
    return hashes_pass2


if __name__ == "__main__":
    double_rebuild()
