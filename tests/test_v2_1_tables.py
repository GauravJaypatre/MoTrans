"""Tests for MoTrans-15 v2.1 Dataset, Folds, and Model Guardrail Enforcement."""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
import pytest

from src.model_guard import (
    assert_no_test_or_post,
    load_v2_1_table,
)
from src.v2_1_leakage_audit import run_leakage_audit

ROOT = Path(__file__).resolve().parent.parent
DATA_V2_1 = ROOT / "data" / "v2_1"

V2_1_ANALYSIS_TABLES = [
    "analysis_tier1.parquet",
    "analysis_tier2_primary.parquet",
    "secondary_holds.parquet",
    "sensitivity_macro_revision.parquet",
]


def test_v2_1_table_existence():
    """Verify that all v2.1 tables and companion files exist on disk."""
    required_files = [
        "analysis_tier1.parquet",
        "analysis_tier2_primary.parquet",
        "secondary_holds.parquet",
        "panel.parquet",
        "sensitivity_macro_revision.parquet",
        "post_window_2026.parquet",
        "excluded_rows.parquet",
        "folds.csv",
    ]
    for fname in required_files:
        p = DATA_V2_1 / fname
        assert p.exists(), f"Required v2.1 file missing: {p}"
        assert p.stat().st_size > 0, f"File is empty: {p}"


def test_v2_1_decision_level_fold_consistency():
    """Rule 3c: All rows of one decision must have identical split and fold assignments."""
    for fname in V2_1_ANALYSIS_TABLES:
        df = pd.read_parquet(DATA_V2_1 / fname)
        for col in ["final_split", "fold_1", "fold_2", "fold_3", "fold_4", "embargo_dropped"]:
            assert col in df.columns, f"{col} missing from {fname}"
            # Group by decision_date; nunique must be strictly 1
            n_uniques = df.groupby("decision_date")[col].nunique()
            assert (n_uniques == 1).all(), (
                f"Inconsistent {col} within single decision in {fname}: "
                f"{n_uniques[n_uniques > 1].head().to_dict()}"
            )


def test_v2_1_analysis_tables_only_clean_rows():
    """Verify that only analysis_ok == 1 rows are included in the three analysis tables."""
    for fname in ["analysis_tier1.parquet", "analysis_tier2_primary.parquet", "secondary_holds.parquet"]:
        df = pd.read_parquet(DATA_V2_1 / fname)
        assert (df["analysis_ok"] == 1).all(), f"Found analysis_ok != 1 in {fname}"
        assert (df["embargo_dropped"] == 0).all(), f"Found embargo_dropped == 1 in {fname}"


def test_v2_1_unscaled_shock_raw_bp_present():
    """Verify shock_raw_bp (unscaled) exists in every analysis table."""
    for fname in V2_1_ANALYSIS_TABLES:
        df = pd.read_parquet(DATA_V2_1 / fname)
        assert "shock_raw_bp" in df.columns, f"shock_raw_bp missing in {fname}"
        assert df["shock_raw_bp"].notna().any(), f"shock_raw_bp all null in {fname}"
        assert "shock_std" in df.columns
        assert "shock_std_legacy" in df.columns


def test_v2_1_model_guard_test_lock_enforcement(monkeypatch):
    """Confirm model guard blocks access to test split without UNLOCK_TEST=1."""
    monkeypatch.delenv("UNLOCK_TEST", raising=False)
    monkeypatch.delenv("UNLOCK_POST", raising=False)

    # 1. Attempting to load split='test' must raise PermissionError
    for fname in V2_1_ANALYSIS_TABLES:
        with pytest.raises(PermissionError, match="Access to 'test' split"):
            load_v2_1_table(fname, split="test")

    # 2. Loading full table without unlock must return 0 test rows
    for fname in V2_1_ANALYSIS_TABLES:
        df = load_v2_1_table(fname)
        assert (df["final_split"] != "test").all()

    # 3. Passing test dataframe to assert_no_test_or_post without unlock must raise PermissionError
    test_rows = pd.read_parquet(DATA_V2_1 / "analysis_tier1.parquet")
    test_sub = test_rows[test_rows["final_split"] == "test"]
    if not test_sub.empty:
        with pytest.raises(PermissionError, match="locked by model_guard"):
            assert_no_test_or_post(test_sub)

    # 4. Explicit unlock must succeed and return test rows
    monkeypatch.setenv("UNLOCK_TEST", "1")
    df_unlocked = load_v2_1_table("analysis_tier1.parquet", split="test")
    assert (df_unlocked["final_split"] == "test").all()


def test_v2_1_model_guard_post_window_lock_enforcement(monkeypatch):
    """Confirm model guard blocks access to quarantined post_window (2026) without UNLOCK_POST=1."""
    monkeypatch.delenv("UNLOCK_TEST", raising=False)
    monkeypatch.delenv("UNLOCK_POST", raising=False)

    post_df = pd.read_parquet(DATA_V2_1 / "post_window_2026.parquet")
    with pytest.raises(PermissionError, match="quarantined and locked"):
        assert_no_test_or_post(post_df)

    monkeypatch.setenv("UNLOCK_POST", "1")
    assert_no_test_or_post(post_df)


def test_v2_1_leakage_audit_suite():
    """Run full leakage audit and verify all 5 checks pass."""
    df_audit = run_leakage_audit()
    assert (df_audit["passed"] == 1).all()
    assert (df_audit["violations_count"] == 0).all()
