"""Test suite asserting integrity and zero look-ahead for analysis parquets."""

from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"


def test_analysis_tier1_structure():
    path = FINAL / "analysis_tier1.parquet"
    assert path.exists(), "analysis_tier1.parquet must exist in data/final"
    df = pd.read_parquet(path)
    assert len(df) == 15805, f"Expected 15,805 rows in Tier 1, got {len(df)}"

    required_cols = [
        "event_id", "regime", "decision_date", "decision", "country", "index_id",
        "shock_std", "shock_std_w", "shock_measure_type", "split_tag",
        "clr_1", "clr_3", "clr_5", "clr_20", "clr_60", "home_market",
        "overlap_1d", "overlap_3d", "overlap_5d", "overlap_20d", "overlap_60d",
        "ctrl_cpi", "ctrl_ind_prod", "ctrl_policy_rate", "ctrl_fx_lcu_per_usd",
        "ctrl_yield_short", "ctrl_vix"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column {col} in analysis_tier1"

    # All rows must be Tier 1
    assert (df["shock_tier"] == 1).all(), "All rows in analysis_tier1 must have shock_tier == 1"
    assert set(df["regime"].unique()) == {"Fed", "ECB"}, "Tier 1 must strictly cover Fed and ECB"


def test_analysis_tier2_primary_structure():
    path = FINAL / "analysis_tier2_primary.parquet"
    assert path.exists(), "analysis_tier2_primary.parquet must exist in data/final"
    df = pd.read_parquet(path)
    assert len(df) == 6297, f"Expected 6,297 rows in Tier 2 Primary, got {len(df)}"

    required_cols = [
        "event_id", "regime", "decision_date", "decision", "country", "index_id",
        "shock_std", "shock_std_w", "shock_measure_type", "split_tag",
        "clr_1", "clr_3", "clr_5", "clr_20", "clr_60", "home_market",
        "overlap_1d", "overlap_3d", "overlap_5d", "overlap_20d", "overlap_60d",
        "ctrl_cpi", "ctrl_ind_prod", "ctrl_policy_rate", "ctrl_fx_lcu_per_usd",
        "ctrl_yield_short", "ctrl_vix"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column {col} in analysis_tier2_primary"

    # Must strictly be Tier 2 rate changes with analysis_ready_timing == 1 and shock_primary == 1
    assert (df["shock_tier"] == 2).all(), "All rows must have shock_tier == 2"
    assert df["decision"].isin(["hike", "cut"]).all(), "Primary sample must strictly be rate changes"
    assert (df["analysis_ready_timing"] == 1).all(), "All rows must have verified analysis_ready_timing == 1"
    assert (df["shock_primary"] == 1).all(), "All rows must have shock_primary == 1"
    assert "BoJ" not in df["regime"].unique(), "BoJ must be excluded from primary sample"
    assert "PBoC" not in df["regime"].unique(), "PBoC must be excluded from primary sample"


def test_zero_lookahead_property():
    """Assert that controls never use future information relative to decision_date."""
    t1 = pd.read_parquet(FINAL / "analysis_tier1.parquet")
    controls = pd.read_parquet(ROOT / "data" / "interim" / "controls_long.parquet")
    controls["available_from"] = pd.to_datetime(controls["available_from"])

    # Sample test: verify that for a random sample of 50 events, the attached ctrl_policy_rate
    # strictly equals the policy_rate available at or before decision_date
    sample = t1.sample(50, random_state=42)
    for _, row in sample.iterrows():
        c_sub = controls[
            (controls["country"] == row["country"])
            & (controls["variable"] == "policy_rate")
            & (controls["available_from"] <= pd.to_datetime(row["decision_date"]))
        ]
        if not c_sub.empty:
            latest = c_sub.sort_values("available_from").iloc[-1]
            if (pd.to_datetime(row["decision_date"]) - latest["available_from"]).days <= 7:
                assert row["ctrl_policy_rate"] == latest["value"]
