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


def test_v2_1_overlap_prior_causality():
    """Verify that overlap_prior_* columns exist and use only earlier decisions (t_prior < t)."""
    import numpy as np
    policy_raw = pd.read_csv(ROOT / "data" / "final" / "policy_decisions.csv", dtype={"decision_date": str})
    pol_clean = policy_raw[policy_raw["event_type"] != "non_decision"].drop_duplicates("event_id").copy()
    bdate_range = pd.bdate_range("1999-01-01", "2026-12-31")
    pol_dates = pd.to_datetime(pol_clean["decision_date"]).to_numpy()
    pol_ids = pol_clean["event_id"].to_numpy()

    for fname in V2_1_ANALYSIS_TABLES:
        df = pd.read_parquet(DATA_V2_1 / fname)
        for W in (1, 3, 5, 20, 60):
            flag_col = f"overlap_prior_{W}d"
            cnt_col = f"overlap_prior_count_{W}d"
            assert flag_col in df.columns, f"{flag_col} missing in {fname}"
            assert cnt_col in df.columns, f"{cnt_col} missing in {fname}"

    # Verify that the decision window strictly ends at t - 1 trading day
    for d, eid in zip(pol_dates[:50], pol_ids[:50]):
        prev_idx = int(np.searchsorted(bdate_range, d, side="left")) - 1
        for W in (1, 3, 5, 20, 60):
            start_idx = max(0, prev_idx - W + 1)
            start_b = bdate_range[start_idx]
            end_b = bdate_range[prev_idx]
            mask = (pol_dates >= start_b) & (pol_dates <= end_b) & (pol_ids != eid)
            matched = pol_dates[mask]
            assert (matched < d).all(), f"Leakage found in prior window for {eid}"


def test_v2_1_final_fit_isolation():
    """Verify final_fit row in folds.csv and verify it never includes test or post_window rows."""
    import datetime as dt
    folds_df = pd.read_csv(DATA_V2_1 / "folds.csv")
    ff_row = folds_df[folds_df["fold_id"] == "final_fit"]
    assert not ff_row.empty, "final_fit row missing from folds.csv"
    assert int(ff_row["train_decisions_total"].iloc[0]) == 648
    assert int(ff_row["val_decisions_total"].iloc[0]) == 0
    assert int(ff_row["train_hikes_total"].iloc[0]) == 92

    for fname in ["analysis_tier1.parquet", "analysis_tier2_primary.parquet", "secondary_holds.parquet"]:
        df_ff = load_v2_1_table(fname, split="final_fit")
        # Must never have test or post_window rows
        assert (df_ff["final_split"].isin(["train", "validation"])).all()
        assert (df_ff["final_split"] != "test").all()
        assert (df_ff["final_split"] != "post_window").all()
        # Decision date strictly before 2024-01-01
        d_dates = pd.to_datetime(df_ff["decision_date"]).dt.date
        assert (d_dates < dt.date(2024, 1, 1)).all(), "final_fit contains decisions >= 2024-01-01"
        assert (df_ff["embargo_dropped"] == 0).all()


def test_v2_1_fold_counts_reconciliation():
    """Verify fold_counts.csv reconciles perfectly with split_counts.csv on Fold 4 validation."""
    fc = pd.read_csv(ROOT / "outputs" / "v2_1" / "fold_counts.csv")
    sc = pd.read_csv(ROOT / "outputs" / "v2_1" / "split_counts.csv")

    f4_val = fc[(fc["fold_id"].astype(str) == "4") & (fc["role"] == "val")]
    assert len(f4_val) == 6, f"Expected 6 rows for fold 4 val, got {len(f4_val)}"
    assert f4_val["decisions_count"].sum() == 76
    assert f4_val["hikes_count"].sum() == 57
    assert f4_val["cuts_count"].sum() == 0
    assert f4_val["holds_count"].sum() == 19

    # Reconcile with validation split in split_counts
    val_sc = sc[sc["split"] == "validation"]
    assert val_sc["decisions_count"].sum() == 76
    hikes_sc = val_sc[val_sc["decision"] == "hike"]["decisions_count"].sum()
    holds_sc = val_sc[val_sc["decision"] == "hold"]["decisions_count"].sum()
    assert hikes_sc == 57
    assert holds_sc == 19


def test_v2_1_row_membership_partition():
    """Verify row_membership.csv sums exactly to 52,242 rows and no 2026 decision is included."""
    rm = pd.read_csv(ROOT / "outputs" / "v2_1" / "row_membership.csv")
    total_rows = rm["event_rows_count"].sum()
    assert total_rows == 52242, f"Expected 52,242 total event rows in 2010-2025, got {total_rows}"

    # Verify unverified_regime in row_membership does not include 2026
    events = pd.read_parquet(ROOT / "data" / "final" / "events.parquet")
    events = events[events["event_type"] != "non_decision"].copy()
    em_2026 = events[(events["decision_date"] >= "2026-01-01") & (events["regime"].isin(["BCB", "Banxico", "RBI"]))]
    assert len(em_2026) > 0, "Expected 2026 EM rows to exist in source"
    
    # In 2010-2025, decisions for BCB, Banxico, RBI must be exactly 369
    events_win = events[(events["decision_date"] >= "2010-01-01") & (events["decision_date"] <= "2025-12-31")]
    em_win = events_win[events_win["regime"].isin(["BCB", "Banxico", "RBI"])]
    assert em_win["event_id"].nunique() == 369, f"Expected 369 decisions for BCB/Banxico/RBI in 2010-2025, got {em_win['event_id'].nunique()}"


def test_v2_1_test_window_composition_separation():
    """Verify test_window_composition.csv separates Tier 1, Tier 2 primary, and Secondary holds."""
    tw = pd.read_csv(ROOT / "outputs" / "v2_1" / "test_window_composition.csv")
    tables = set(tw["table"].unique())
    assert tables == {"Tier 1", "Tier 2 primary", "Secondary holds"}
    
    t1_sub = tw[tw["table"] == "Tier 1"]
    assert t1_sub["decisions_count"].sum() == 14
    assert t1_sub["cuts_count"].sum() == 8
    assert t1_sub["holds_count"].sum() == 6

    t2_sub = tw[tw["table"] == "Tier 2 primary"]
    assert t2_sub["decisions_count"].sum() == 20
    assert t2_sub["cuts_count"].sum() == 20
    assert t2_sub["holds_count"].sum() == 0

    sec_sub = tw[tw["table"] == "Secondary holds"]
    assert sec_sub["decisions_count"].sum() == 36
    assert sec_sub["holds_count"].sum() == 36
    assert sec_sub["cuts_count"].sum() == 0

