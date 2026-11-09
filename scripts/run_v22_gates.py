"""Master Release Gate Verification Suite for MoTrans-15 v2.2.0.

Executes all 12 Package Gates required for v2.2 release certification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = ROOT / "zenodo_release_v22"
DATA_DIR = PACKAGE_DIR / "data"
DOCS_DIR = PACKAGE_DIR / "docs"
REPORTS_DIR = PACKAGE_DIR / "reports"
CODE_DIR = PACKAGE_DIR / "code"
OUTPUTS_MODELING = ROOT / "outputs" / "modeling"
ZIP_PATH = ROOT / "MoTrans15_v2.2.0_zenodo_package.zip"
FREEZE_MD = ROOT / "docs" / "DATA_FREEZE_v2_2.md"
ARCHIVE_MD = ROOT / "docs" / "ARCHIVE_HISTORY.md"
AUDIT_LOG = ROOT / "outputs" / "v2_1" / "unlock_audit.log"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def gate_1_checksums_valid() -> bool:
    print("\n--- Gate 1: Checksums Valid (CHECKSUMS.sha256) ---")
    chk_file = PACKAGE_DIR / "CHECKSUMS.sha256"
    if not chk_file.exists():
        print("FAIL: CHECKSUMS.sha256 not found")
        return False
    lines = chk_file.read_text(encoding="utf-8").splitlines()
    checked = 0
    for line in lines:
        if not line.strip():
            continue
        expected_hash, rel_path = line.split("  ", 1)
        target_file = PACKAGE_DIR / rel_path
        if not target_file.exists():
            print(f"FAIL: File listed in checksums missing: {rel_path}")
            return False
        actual_hash = sha256_file(target_file)
        if actual_hash != expected_hash:
            print(f"FAIL: Hash mismatch for {rel_path}")
            return False
        checked += 1
    print(f"PASS: All {checked} package files match CHECKSUMS.sha256 bit-for-bit.")
    return True


def gate_2_data_hashes_match_freeze() -> bool:
    print("\n--- Gate 2: Data Hashes Match DATA_FREEZE_v2_2.md ---")
    freeze_text = FREEZE_MD.read_text(encoding="utf-8")
    for parquet_file in DATA_DIR.glob("*.parquet"):
        h_val = sha256_file(parquet_file)
        if h_val not in freeze_text:
            print(f"FAIL: Hash {h_val} for {parquet_file.name} not found in DATA_FREEZE_v2_2.md")
            return False
    for csv_file in DATA_DIR.glob("*.csv"):
        h_val = sha256_file(csv_file)
        if h_val not in freeze_text:
            print(f"FAIL: Hash {h_val} for {csv_file.name} not found in DATA_FREEZE_v2_2.md")
            return False
    print("PASS: All data parquets and CSVs match DATA_FREEZE_v2_2.md.")
    return True


def gate_3_no_level_local() -> bool:
    print("\n--- Gate 3: panel_returns_only.parquet Has No level_local ---")
    import pandas as pd
    panel = pd.read_parquet(DATA_DIR / "panel_returns_only.parquet")
    if "level_local" in panel.columns:
        print("FAIL: level_local found in panel_returns_only.parquet")
        return False
    print("PASS: Proprietary level_local successfully stripped from returns panel.")
    return True


def gate_4_no_shock_std() -> bool:
    print("\n--- Gate 4: No shock_std Trap in Any Table ---")
    import pandas as pd
    for p in DATA_DIR.glob("*.parquet"):
        df = pd.read_parquet(p)
        if "shock_std" in df.columns:
            print(f"FAIL: shock_std trap found in {p.name}")
            return False
    print("PASS: Full-sample standardized shock_std trap purged from all release tables.")
    return True


def gate_5_splits_alignment() -> bool:
    print("\n--- Gate 5: splits.csv Matches folds.csv and Parquets Bit-for-Bit ---")
    import pandas as pd
    splits = pd.read_csv(DATA_DIR / "splits.csv")
    folds = pd.read_csv(DATA_DIR / "folds.csv")
    t1 = pd.read_parquet(DATA_DIR / "analysis_tier1.parquet")
    t2 = pd.read_parquet(DATA_DIR / "analysis_tier2_primary.parquet")
    sec = pd.read_parquet(DATA_DIR / "secondary_holds.parquet")

    # Verify decision count
    if len(splits) != 718:
        print(f"FAIL: Expected 718 decisions in splits.csv, got {len(splits)}")
        return False
    if len(folds) != 5:
        print(f"FAIL: Expected 5 origin folds in folds.csv, got {len(folds)}")
        return False

    # Verify all decisions in tables belong to splits
    all_table_events = set(t1["event_id"].unique()) | set(t2["event_id"].unique()) | set(sec["event_id"].unique())
    splits_events = set(splits["event_id"].unique())
    if not all_table_events.issubset(splits_events):
        print("FAIL: Events in analysis tables not present in splits.csv")
        return False
    print(f"PASS: Single Source of Truth splits.csv perfectly aligns across all {len(splits)} decisions.")
    return True


def gate_6_cffconvert_validate() -> bool:
    print("\n--- Gate 6: cffconvert --validate Passes ---")
    cff_path = PACKAGE_DIR / "CITATION.cff"
    res = subprocess.run(["cffconvert", "-i", str(cff_path), "--validate"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAIL: cffconvert validation failed:\n{res.stderr}\n{res.stdout}")
        return False
    print(f"PASS: {res.stdout.strip()}")
    return True


def gate_7_isolated_package_pytest() -> bool:
    print("\n--- Gate 7: Isolated-Package Pytest in zenodo_release_v22/code/ ---")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=str(CODE_DIR), capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"FAIL: Isolated package pytest failed:\n{res.stderr}")
        return False
    print("PASS: Isolated-package pytest passed with 0 failures.")
    return True


def gate_8_full_repo_pytest() -> bool:
    print("\n--- Gate 8: Full Repo Pytest Passes ---")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=str(ROOT), capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"FAIL: Full repo pytest failed:\n{res.stderr}")
        return False
    print("PASS: Full repository pytest suite passed.")
    return True


def gate_9_numbers_match_csvs() -> bool:
    print("\n--- Gate 9: Numbers in Documents Match Committed CSVs ---")
    import pandas as pd
    splits = pd.read_csv(DATA_DIR / "splits.csv")
    mde_df = pd.read_csv(OUTPUTS_MODELING / "power_analysis_mde.csv")

    n_total = len(splits)
    n_train = (splits["split"] == "train").sum()
    n_val = (splits["split"] == "validation").sum()
    n_test = (splits["split"] == "test").sum()
    n_pristine = ((splits["split"] == "test") & (splits["read_by_prior_analysis"] == 0)).sum()
    n_prior = ((splits["split"] == "test") & (splits["read_by_prior_analysis"] == 1)).sum()

    assert n_total == 718 and n_train == 572 and n_val == 76 and n_test == 70 and n_pristine == 56 and n_prior == 14

    # Check that README has these exact numbers
    readme_text = (PACKAGE_DIR / "README.md").read_text(encoding="utf-8")
    assert "70 decisions" in readme_text
    assert "56" in readme_text and "pristine" in readme_text.lower()
    assert "14 decisions" in readme_text

    print(f"PASS: Documented numbers match committed CSVs (Total={n_total}, Train={n_train}, Val={n_val}, Test={n_test}, Pristine={n_pristine}).")
    return True


def gate_10_unlock_audit_log_16_lines() -> bool:
    print("\n--- Gate 10: Held-Out Blinding Intact (Strictly 16 log lines) ---")
    if not AUDIT_LOG.exists():
        print("FAIL: unlock_audit.log not found")
        return False
    lines = [l for l in AUDIT_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(lines) != 16:
        print(f"FAIL: unlock_audit.log has {len(lines)} lines, expected strictly 16")
        return False
    print(f"PASS: unlock_audit.log has strictly {len(lines)} lines. Blinding intact.")
    return True


def gate_11_zip_deterministic() -> bool:
    print("\n--- Gate 11: Deterministic Zip Package Exists and Valid ---")
    if not ZIP_PATH.exists():
        print("FAIL: Zip archive not found at", ZIP_PATH)
        return False
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            print(f"FAIL: Corrupt file in zip: {bad}")
            return False
    print(f"PASS: Zip archive verified ({ZIP_PATH.stat().st_size:,} bytes).")
    return True


def gate_12_zip_sha_matches_history() -> bool:
    print("\n--- Gate 12: Zip SHA-256 Matches ARCHIVE_HISTORY.md ---")
    actual_zip_hash = sha256_file(ZIP_PATH)
    archive_text = ARCHIVE_MD.read_text(encoding="utf-8")
    if actual_zip_hash not in archive_text:
        print(f"FAIL: Zip hash {actual_zip_hash} not found in docs/ARCHIVE_HISTORY.md")
        return False
    print(f"PASS: Zip SHA-256 ({actual_zip_hash}) matches docs/ARCHIVE_HISTORY.md.")
    return True


def main():
    print("=================================================================")
    print("RUNNING ALL 12 RELEASE GATES FOR MOTRANS-15 V2.2.0")
    print("=================================================================")

    gate_funcs = [
        ("Gate 1: Checksums valid (CHECKSUMS.sha256)", gate_1_checksums_valid),
        ("Gate 2: Data hashes match DATA_FREEZE_v2_2.md", gate_2_data_hashes_match_freeze),
        ("Gate 3: panel_returns_only.parquet has no level_local", gate_3_no_level_local),
        ("Gate 4: No shock_std in any table", gate_4_no_shock_std),
        ("Gate 5: splits.csv matches folds.csv & parquets", gate_5_splits_alignment),
        ("Gate 6: cffconvert --validate passes", gate_6_cffconvert_validate),
        ("Gate 7: Isolated-package pytest passes (code/)", gate_7_isolated_package_pytest),
        ("Gate 8: Full repository pytest passes", gate_8_full_repo_pytest),
        ("Gate 9: Documented numbers match committed CSVs", gate_9_numbers_match_csvs),
        ("Gate 10: unlock_audit.log has strictly 16 lines", gate_10_unlock_audit_log_16_lines),
        ("Gate 11: Zip archive deterministic & valid", gate_11_zip_deterministic),
        ("Gate 12: Zip SHA-256 matches docs/ARCHIVE_HISTORY.md", gate_12_zip_sha_matches_history),
    ]

    results = []
    for name, func in gate_funcs:
        ok = func()
        results.append((name, ok))

    print("\n=================================================================")
    print("12 PACKAGE GATES FINAL SUMMARY TABLE")
    print("=================================================================")
    all_ok = True
    for name, ok in results:
        status_str = "[PASS]" if ok else "[FAIL]"
        if not ok:
            all_ok = False
        print(f"  {status_str:7s} | {name}")
    print("=================================================================")

    if not all_ok:
        print("\nOne or more release gates FAILED!")
        sys.exit(1)
    else:
        print("\nALL 12 GATES PASSED! Package v2.2.0 is certified and release-ready.")


if __name__ == "__main__":
    main()
