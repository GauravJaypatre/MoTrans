"""Tests for Phase V0 Coverage Audit, Addendum, and v2.0 Model Guardrail."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import pandas as pd
import pytest

from src.model_guard import (
    FINAL_HOLDOUT_START,
    assert_no_holdout,
    split_tag_v2,
    verify_embargo,
)


def test_coverage_csv_exists_and_valid():
    csv_path = Path("outputs/v2/coverage_2010plus.csv")
    assert csv_path.exists(), "coverage_2010plus.csv must exist"

    df = pd.read_csv(csv_path)
    assert len(df) == 850, f"Expected 850 rows (204 regime-years + 646 index-years), got {len(df)}"

    required_cols = [
        "entity_type", "entity_id", "year", "country",
        "decisions", "tier", "shock_measure_type", "analysis_ready_timing", "shock_primary",
        "trading_days", "calendar_days", "missing_days", "stale_flags", "outlier_flags",
        "weak_coverage", "weak_reasons"
    ]
    for col in required_cols:
        assert col in df.columns, f"Column {col} missing from coverage_2010plus.csv"

    reg_df = df[df["entity_type"] == "regime"]
    assert len(reg_df) == 204, f"Expected 204 regime rows, got {len(reg_df)}"
    assert reg_df["entity_id"].nunique() == 12

    idx_df = df[df["entity_type"] == "index"]
    assert len(idx_df) == 646, f"Expected 646 index rows, got {len(idx_df)}"
    assert idx_df["entity_id"].nunique() == 38

    # Verify stale reasons are labeled 'Stale price' (not volume)
    stale_reasons = idx_df[idx_df["stale_flags"] > 5]["weak_reasons"].tolist()
    assert len(stale_reasons) > 0
    for r in stale_reasons:
        assert "Stale price" in r, f"Expected 'Stale price' in reason, got '{r}'"
        assert "volume" not in r.lower(), f"Did not expect 'volume' in reason, got '{r}'"


def test_model_guard_split_tag_v2():
    # Before 2010 -> pre2010_robustness
    assert split_tag_v2(dt.date(2005, 5, 1)) == "pre2010_robustness"
    assert split_tag_v2("2009-12-31") == "pre2010_robustness"

    # 2010 to pre-holdout -> model_train_val
    assert split_tag_v2(dt.date(2010, 1, 1)) == "model_train_val"
    assert split_tag_v2("2024-05-15") == "model_train_val"
    assert split_tag_v2(dt.date(2025, 10, 13)) == "model_train_val"

    # Final 12 months -> final_holdout
    assert split_tag_v2(dt.date(2025, 10, 14)) == "final_holdout"
    assert split_tag_v2("2026-10-13") == "final_holdout"


def test_model_guard_assert_no_holdout_and_blind_test():
    # Clean estimation data passes
    df_clean = pd.DataFrame({
        "date": ["2015-01-01", "2024-12-31"],
        "split_tag": ["model_train_val", "model_train_val"],
    })
    assert_no_holdout(df_clean)

    # final_holdout raises without UNLOCK_HOLDOUT=1
    df_holdout = pd.DataFrame({
        "date": ["2015-01-01", "2026-01-15"],
        "split_tag": ["model_train_val", "final_holdout"],
    })
    os.environ.pop("UNLOCK_HOLDOUT", None)
    with pytest.raises(PermissionError, match="final_holdout"):
        assert_no_holdout(df_holdout)

    # final_holdout passes with UNLOCK_HOLDOUT=1
    os.environ["UNLOCK_HOLDOUT"] = "1"
    try:
        assert_no_holdout(df_holdout)
    finally:
        os.environ.pop("UNLOCK_HOLDOUT", None)

    # v1 blind_test tables raise without UNLOCK_BLIND=1
    df_blind = pd.DataFrame({
        "date": ["2015-01-01", "2023-05-01"],
        "split_tag": ["train", "blind_test"],
    })
    os.environ.pop("UNLOCK_BLIND", None)
    with pytest.raises(PermissionError, match="blind_test"):
        assert_no_holdout(df_blind)

    # v1 blind_test passes with UNLOCK_BLIND=1
    os.environ["UNLOCK_BLIND"] = "1"
    try:
        assert_no_holdout(df_blind)
    finally:
        os.environ.pop("UNLOCK_BLIND", None)


def test_model_guard_locks_v1_actual_analysis_tables():
    # Load actual v1 analysis_tier1.parquet
    t1_path = Path("data/final/analysis_tier1.parquet")
    if t1_path.exists():
        t1 = pd.read_parquet(t1_path)
        
        # Test 1: Full table raises on final_holdout when UNLOCK_HOLDOUT is not set
        os.environ.pop("UNLOCK_HOLDOUT", None)
        with pytest.raises(PermissionError, match="final_holdout"):
            assert_no_holdout(t1)

        # Test 2: Pre-holdout slice of v1 table (2022 to 2025-10-13) has blind_test and raises without UNLOCK_BLIND
        t1_pre = t1[pd.to_datetime(t1["decision_date"]) < pd.to_datetime("2025-10-14")]
        assert (t1_pre["split_tag"] == "blind_test").any()
        
        os.environ.pop("UNLOCK_BLIND", None)
        with pytest.raises(PermissionError, match="blind_test"):
            assert_no_holdout(t1_pre)

        # Test 3: Setting UNLOCK_BLIND=1 allows accessing pre-holdout blind_test data
        os.environ["UNLOCK_BLIND"] = "1"
        try:
            assert_no_holdout(t1_pre)
        finally:
            os.environ.pop("UNLOCK_BLIND", None)

        # Test 4: Setting both UNLOCK_BLIND=1 and UNLOCK_HOLDOUT=1 allows full table
        os.environ["UNLOCK_BLIND"] = "1"
        os.environ["UNLOCK_HOLDOUT"] = "1"
        try:
            assert_no_holdout(t1)
        finally:
            os.environ.pop("UNLOCK_BLIND", None)
            os.environ.pop("UNLOCK_HOLDOUT", None)


def test_verify_embargo():
    # Gap >= 60 days
    assert verify_embargo(dt.date(2020, 1, 1), dt.date(2020, 3, 15), min_embargo_days=60) is True
    # Gap < 60 days
    with pytest.raises(ValueError, match="Temporal leak"):
        verify_embargo(dt.date(2020, 1, 1), dt.date(2020, 1, 30), min_embargo_days=60)


def test_v2_spec_states_exploratory():
    spec_path = Path("docs/v2_spec.md")
    assert spec_path.exists()
    content = spec_path.read_text(encoding="utf-8")
    assert "Exploratory" in content or "exploratory" in content
    assert "NOT the Pre-Registered Confirmatory Test" in content or "not the pre-registered" in content.lower()


def test_effective_sample_csvs():
    year_path = Path("outputs/v2/effective_by_year.csv")
    period_path = Path("outputs/v2/effective_by_period.csv")
    assert year_path.exists()
    assert period_path.exists()

    df_y = pd.read_csv(year_path)
    df_p = pd.read_csv(period_path)

    # Grand total effective decisions must be 406
    gt = df_y[df_y["year"] == "Grand Total"]
    assert len(gt) == 1
    assert int(gt["effective_decisions"].iloc[0]) == 406

    # CBR primary vs timing-ready distinction
    cbr_tot = df_y[(df_y["regime"] == "CBR") & (df_y["year"] == "Total")]
    assert int(cbr_tot["shock_primary"].iloc[0]) == 51
    assert int(cbr_tot["analysis_ready_timing"].iloc[0]) == 41
    assert int(cbr_tot["effective_decisions"].iloc[0]) == 41

    # Check period totals
    holdout_row = df_p[(df_p["period"].str.startswith("final_holdout")) & (df_p["tier"] == "All Tiers")]
    assert len(holdout_row) == 1
    assert int(holdout_row["total_effective"].iloc[0]) == 11

    holdout_t1 = df_p[(df_p["period"].str.startswith("final_holdout")) & (df_p["tier"] == "Tier 1")]
    assert int(holdout_t1["total_effective"].iloc[0]) == 1

    holdout_t2 = df_p[(df_p["period"].str.startswith("final_holdout")) & (df_p["tier"] == "Tier 2")]
    assert int(holdout_t2["total_effective"].iloc[0]) == 10

    # Fed non_decision exclusion check
    fed_tot = df_y[(df_y["regime"] == "Fed") & (df_y["year"] == "Total")]
    assert int(fed_tot["decisions"].iloc[0]) == 138


def test_holdout_candidates_csv():
    hc_path = Path("outputs/v2/holdout_candidates.csv")
    assert hc_path.exists()
    df_hc = pd.read_csv(hc_path)

    # Check that candidate boundaries exist
    boundaries = ["2022-01-01", "2024-01-01", "2025-01-01", "2025-10-14"]
    b_rows = df_hc[(df_hc["section"] == "boundary_summary") & (df_hc["regime"] == "All Regimes")]
    assert set(b_rows["boundary"]) == set(boundaries)

    # Check 11 holdout decisions
    ho_rows = df_hc[df_hc["section"] == "final_holdout_decisions"]
    assert len(ho_rows) == 11
    assert (ho_rows["shock_tier"] == "Tier 1").sum() == 1
    assert (ho_rows["shock_tier"] == "Tier 2").sum() == 10


def test_v2_tables_no_blind_test_tag():
    """Verify that split_tag_v2 never returns 'blind_test' and v2 tables forbid 'blind_test'."""
    test_dates = [
        dt.date(2010, 1, 1),
        dt.date(2022, 1, 1),
        dt.date(2023, 6, 15),
        dt.date(2024, 1, 1),
        dt.date(2025, 10, 14),
        dt.date(2026, 10, 13),
    ]
    for d in test_dates:
        tag = split_tag_v2(d)
        assert tag != "blind_test", f"split_tag_v2 returned forbidden tag 'blind_test' for {d}"

    # Also check if any file in data/v2 has split_tag == 'blind_test'
    v2_dir = Path("data/v2")
    if v2_dir.exists():
        for p in v2_dir.glob("*.parquet"):
            df = pd.read_parquet(p)
            if "split_tag" in df.columns:
                assert not (df["split_tag"] == "blind_test").any(), f"File {p.name} contains forbidden tag 'blind_test'!"
