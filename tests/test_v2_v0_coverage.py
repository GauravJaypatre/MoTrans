"""Tests for Phase V0 Coverage Audit and v2.0 Model Guardrail."""

from __future__ import annotations

import datetime as dt
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


def test_model_guard_assert_no_holdout():
    df_clean = pd.DataFrame({
        "date": ["2015-01-01", "2024-12-31"],
        "split_tag": ["model_train_val", "model_train_val"],
    })
    # Should pass without error
    assert_no_holdout(df_clean)

    df_contaminated = pd.DataFrame({
        "date": ["2015-01-01", "2026-01-15"],
        "split_tag": ["model_train_val", "final_holdout"],
    })
    with pytest.raises(PermissionError):
        assert_no_holdout(df_contaminated)


def test_verify_embargo():
    # Gap >= 60 days
    assert verify_embargo(dt.date(2020, 1, 1), dt.date(2020, 3, 15), min_embargo_days=60) is True
    # Gap < 60 days
    with pytest.raises(ValueError):
        verify_embargo(dt.date(2020, 1, 1), dt.date(2020, 1, 30), min_embargo_days=60)
