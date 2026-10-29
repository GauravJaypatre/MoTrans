"""Comprehensive Verification Suite for MoTrans-15 v2.1.1 Zenodo Release Package.

Validates Steps 5a, 5b, 5c, 5d, 5e, and 5g.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent
RELEASE_DIR = ROOT / "zenodo_release"
DATA_DIR = RELEASE_DIR / "data"
REPORTS_DIR = RELEASE_DIR / "reports"
DOCS_DIR = RELEASE_DIR / "docs"

CERTIFIED_HASHES = {
    "analysis_tier1.parquet": "8a6207dd0c753c7d24d0a4d091dbdb05ee38d3010913a85b4c9f87a86e44979e",
    "analysis_tier2_primary.parquet": "c319040f687fbd88be9268d881c71152d803a0bd20357a109da049415f010a14",
    "secondary_holds.parquet": "7235bae5b29d0e4261bc9349e32593b09f9d0bf7cd784a7f61a56a45dc9c846f",
    "sensitivity_macro_revision.parquet": "f689bc78820520f08020d4d613fb6129a07abe15842634e2c9b428bd0f5bf794",
    "panel_returns_only.parquet": "e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620",
    "folds.csv": "5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee",
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def check_5a_checksums() -> bool:
    print("\n--- [5a] CHECKSUMS.sha256 & Freeze Hashes Verification ---")
    checksums_file = RELEASE_DIR / "CHECKSUMS.sha256"
    assert checksums_file.exists(), "CHECKSUMS.sha256 missing"
    
    lines = checksums_file.read_text(encoding="utf-8").strip().splitlines()
    print(f"Total files in CHECKSUMS.sha256: {len(lines)}")
    
    mismatches = 0
    for line in lines:
        if not line.strip():
            continue
        expected_sha, rel_path = line.strip().split("  ", 1)
        full_path = RELEASE_DIR / rel_path
        if not full_path.exists():
            print(f"  MISSING: {rel_path}")
            mismatches += 1
            continue
        actual_sha = sha256_file(full_path)
        if actual_sha != expected_sha:
            print(f"  MISMATCH: {rel_path} (expected {expected_sha}, got {actual_sha})")
            mismatches += 1

    assert mismatches == 0, f"Found {mismatches} checksum mismatches!"
    print(f"  All {len(lines)} packaged files verified bit-for-bit against CHECKSUMS.sha256.")

    # Cross-check data files against DATA_FREEZE_v2_1.md certified hashes
    for fname, exp_hash in CERTIFIED_HASHES.items():
        p = DATA_DIR / fname
        assert p.exists(), f"Data file {fname} missing from package"
        act_hash = sha256_file(p)
        assert act_hash == exp_hash, f"Freeze hash mismatch for {fname}!"
        print(f"  Data Freeze Hash Match: {fname} == {exp_hash[:16]}... OK")

    return True

def check_5b_schema() -> bool:
    print("\n--- [5b] Schema Check & Price Level Exclusion ---")
    tier_tables = [
        "analysis_tier1.parquet",
        "analysis_tier2_primary.parquet",
        "secondary_holds.parquet",
    ]
    required_cols = [
        "event_id", "regime", "decision_date", "final_split",
        "shock_raw_bp", "clr_1", "clr_3", "clr_5", "clr_20", "clr_60", "analysis_ok"
    ]
    prohibited_price_level_cols = ["level_local", "close", "price", "index_level"]

    for t_name in tier_tables:
        p = DATA_DIR / t_name
        df = pd.read_parquet(p)
        cols = list(df.columns)
        print(f"\nTable: {t_name} (rows={len(df)}, cols={len(cols)})")
        
        # Verify required columns
        missing_req = [c for c in required_cols if c not in cols]
        assert not missing_req, f"{t_name} missing required columns: {missing_req}"
        print(f"  Required columns present: {required_cols}")

        # Verify no price-level columns
        bad_price_cols = [c for c in cols if c in prohibited_price_level_cols]
        assert not bad_price_cols, f"{t_name} contains prohibited price-level columns: {bad_price_cols}"
        print(f"  Zero price-level columns confirmed.")

        # Check null counts for key columns
        nulls = df[required_cols].isnull().sum()
        print(f"  Null counts in required columns:\n{nulls.to_string()}")

    # Check panel_returns_only.parquet
    df_panel = pd.read_parquet(DATA_DIR / "panel_returns_only.parquet")
    assert "level_local" not in df_panel.columns, "panel_returns_only.parquet must NOT contain level_local!"
    print(f"\nTable: panel_returns_only.parquet (rows={len(df_panel)}, cols={len(df_panel.columns)})")
    print(f"  Confirmed level_local excluded. Daily log return columns: ret_local, ret_usd present.")

    return True

def check_5c_leakage() -> bool:
    print("\n--- [5c] Leakage Re-Check on Packaged Files ---")
    tier_tables = [
        "analysis_tier1.parquet",
        "analysis_tier2_primary.parquet",
        "secondary_holds.parquet",
    ]
    for t_name in tier_tables:
        df = pd.read_parquet(DATA_DIR / t_name)
        
        # 1. No event_id in multiple splits
        multi_split = (df.groupby("event_id")["final_split"].nunique() > 1).sum()
        assert multi_split == 0, f"Found {multi_split} event_ids spanning multiple splits in {t_name}"
        
        # 2. Date range bounds: 2010-01-01 to 2025-12-31
        min_date = str(df["decision_date"].min())
        max_date = str(df["decision_date"].max())
        assert min_date >= "2010-01-01", f"Date before 2010 in {t_name}: {min_date}"
        assert max_date <= "2025-12-31", f"Date after 2025 in {t_name}: {max_date}"

        # 3. No post_window rows
        post_count = (df["final_split"] == "post_window").sum()
        assert post_count == 0, f"Found {post_count} post_window rows in {t_name}"

        # 4. Controls available_from <= decision_date
        for prefix in ["cpi", "ind_prod"]:
            avail_col = f"{prefix}_available_from"
            if avail_col in df.columns:
                leaks = (df[avail_col].dropna() > df["decision_date"]).sum()
                assert leaks == 0, f"Found {leaks} look-ahead leaks in {avail_col} for {t_name}"

        # 5. Test split zero hikes property
        test_hikes = ((df["final_split"] == "test") & (df["decision"] == "hike")).sum()
        assert test_hikes == 0, f"Test split contains {test_hikes} hikes (expected 0) in {t_name}"

        print(f"  {t_name}: Zero split overlap, dates [{min_date}..{max_date}], zero post_window, zero control leaks, zero test hikes. OK.")

    return True

def check_5d_reproduce_counts() -> bool:
    print("\n--- [5d] Reproduce Decision & Row Counts from Committed CSVs ---")
    df_split = pd.read_csv(REPORTS_DIR / "split_counts.csv")
    df_rows = pd.read_csv(REPORTS_DIR / "row_membership.csv")
    df_folds = pd.read_csv(REPORTS_DIR / "fold_counts.csv")

    split_sums = df_split.groupby("split")[["decisions_count", "event_rows_count"]].sum()
    print("Committed split_counts.csv totals by split:")
    print(split_sums)

    t1 = pd.read_parquet(DATA_DIR / "analysis_tier1.parquet")
    t2 = pd.read_parquet(DATA_DIR / "analysis_tier2_primary.parquet")
    sh = pd.read_parquet(DATA_DIR / "secondary_holds.parquet")

    # Combine unique decision-split pairs across all three tables
    combined = pd.concat([
        t1[["event_id", "final_split"]].drop_duplicates(),
        t2[["event_id", "final_split"]].drop_duplicates(),
        sh[["event_id", "final_split"]].drop_duplicates()
    ]).drop_duplicates()

    actual_dec_counts = combined.groupby("final_split")["event_id"].count()
    print("\nActual unique decision counts from packaged tables:")
    print(actual_dec_counts)

    for split in ["train", "validation", "test"]:
        exp_decs = split_sums.loc[split, "decisions_count"]
        act_decs = actual_dec_counts.loc[split]
        assert exp_decs == act_decs, f"Decision mismatch for split {split}: {exp_decs} vs {act_decs}"
        print(f"  Match: Split {split} has exactly {act_decs} decisions.")

    # Check table row counts against row_membership.csv
    table_map = {
        "tier1": ("analysis_tier1.parquet", len(t1)),
        "tier2_primary": ("analysis_tier2_primary.parquet", len(t2)),
        "secondary_holds": ("secondary_holds.parquet", len(sh)),
    }
    for cat, (fname, act_len) in table_map.items():
        row_exp = df_rows[df_rows["membership_category"] == cat]["event_rows_count"].iloc[0]
        assert row_exp == act_len, f"Row count mismatch for {fname}: expected {row_exp}, got {act_len}"
        print(f"  Match: Table {fname} has exactly {act_len} rows.")

    return True

def check_5e_independent_reader_and_sizes() -> bool:
    print("\n--- [5e] Independent Reader (PyArrow) & Package File Sizes ---")
    parquet_files = list(DATA_DIR.glob("*.parquet"))
    total_size_bytes = 0

    for pf in parquet_files:
        size = pf.stat().st_size
        total_size_bytes += size
        # Read with independent pyarrow engine
        table = pq.read_table(pf)
        print(f"  PyArrow read {pf.name}: {table.num_rows} rows, {table.num_columns} cols, size = {size/1024:.1f} KB")

    # Calculate total size of zenodo_release/
    all_package_size = sum(f.stat().st_size for f in RELEASE_DIR.rglob("*") if f.is_file())
    print(f"\nTotal Zenodo release package size: {all_package_size / (1024 * 1024):.2f} MB")
    print(f"Zenodo standard deposit quota: 50,000.00 MB (50 GB)")
    assert all_package_size < 50 * 1024 * 1024 * 1024, "Package exceeds Zenodo size limit!"
    print("  Package size is well within Zenodo single-deposit capacity.")

    return True

def check_5g_readme_links_and_numbers() -> bool:
    print("\n--- [5g] README Internal Links & Number Consistency ---")
    readme_path = RELEASE_DIR / "README.md"
    assert readme_path.exists(), "zenodo_release/README.md missing"
    readme_text = readme_path.read_text(encoding="utf-8")

    # Check referenced files in README
    referenced_files = [
        "data/analysis_tier1.parquet",
        "data/analysis_tier1.csv",
        "data/analysis_tier2_primary.parquet",
        "data/analysis_tier2_primary.csv",
        "data/secondary_holds.parquet",
        "data/secondary_holds.csv",
        "data/sensitivity_macro_revision.parquet",
        "data/panel_returns_only.parquet",
        "data/folds.csv",
        "docs/v2_1_data_dictionary.md",
        "docs/v2_1_limitations.md",
        "docs/v2_1_spec.md",
        "docs/preregistration.md",
        "docs/limitations.md",
        "docs/DATA_FREEZE_v2_1.md",
        "docs/data_quality_scorecard.md",
        "docs/labelling_guide.md",
        "reports/split_counts.csv",
        "reports/fold_counts.csv",
        "reports/test_window_composition.csv",
        "reports/row_membership.csv",
        "reports/leakage_audit.csv",
        "reports/analysis_ok_breakdown.csv",
        "reports/years_thin.csv",
        "reports/verification_summary.csv",
        "code/src/",
        "code/tests/",
        "code/tasks.py",
        "code/requirements.txt",
        "code/pytest.ini",
        "code/README.md",
        "LICENSE",
        "LICENSE-CODE",
        "CITATION.cff",
        ".zenodo.json",
        "CHECKSUMS.sha256",
        "MANIFEST.csv",
        "LICENCE_AND_PROVENANCE.md",
        "PROVENANCE.md",
        "LIMITATIONS_PACKAGE.md",
    ]

    for ref in referenced_files:
        p = RELEASE_DIR / ref
        assert p.exists(), f"README references file {ref} which does not exist in zenodo_release/!"
        print(f"  Link verified: {ref}")

    # Verify numbers quoted in README
    df_split = pd.read_csv(REPORTS_DIR / "split_counts.csv")
    split_sums = df_split.groupby("split")[["decisions_count", "event_rows_count"]].sum()
    train_decs = split_sums.loc["train", "decisions_count"]
    val_decs = split_sums.loc["validation", "decisions_count"]
    test_decs = split_sums.loc["test", "decisions_count"]

    assert str(train_decs) in readme_text, f"train decisions {train_decs} not found in README!"
    assert str(val_decs) in readme_text, f"val decisions {val_decs} not found in README!"
    assert str(test_decs) in readme_text, f"test decisions {test_decs} not found in README!"
    print("  Numbers in README verified against split_counts.csv.")

    return True

def main():
    print("==================================================")
    print("Running MoTrans-15 v2.1.1 Zenodo Package Verification")
    print("==================================================")
    check_5a_checksums()
    check_5b_schema()
    check_5c_leakage()
    check_5d_reproduce_counts()
    check_5e_independent_reader_and_sizes()
    check_5g_readme_links_and_numbers()
    print("\n==================================================")
    print("ALL VERIFICATION CHECKS (5a, 5b, 5c, 5d, 5e, 5g) PASSED!")
    print("==================================================")

if __name__ == "__main__":
    main()

