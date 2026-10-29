"""Test suite for MoTrans-15 v2.0 data tables, row-quality flags, and controls."""

from pathlib import Path
import os
import pandas as pd
import pytest

from src.model_guard import assert_no_holdout

ROOT = Path(__file__).resolve().parent.parent
DATA_V2 = ROOT / "data" / "v2"
DOCS = ROOT / "docs"

V2_TABLES = [
    "analysis_tier1_2010plus.parquet",
    "analysis_tier2_primary_2010plus.parquet",
    "secondary_holds_2010plus.parquet",
    "panel_2010plus.parquet",
    "sensitivity_macro_revision_2010plus.parquet"
]

def test_v2_tables_exist():
    for fname in V2_TABLES:
        p = DATA_V2 / fname
        assert p.exists(), f"File {fname} missing from data/v2/"


def test_v2_tier1_table_structure():
    p = DATA_V2 / "analysis_tier1_2010plus.parquet"
    df = pd.read_parquet(p)
    assert len(df) == 9732, f"Expected 9,732 rows in Tier 1 2010+, got {len(df)}"

    required_cols = [
        "event_id", "regime", "decision_date", "v1_split_tag", "final_holdout",
        "policy_rate", "zero_lower_bound", "regime_state",
        "price_source_verified", "shock_replicated", "timing_verified_level", "policy_verified", "proxy_type", "analysis_ok",
        "overlap_1d", "overlap_3d", "overlap_5d", "overlap_20d", "overlap_60d",
        "ctrl_cpi", "ctrl_yield_1y", "ctrl_yield_short", "ctrl_vix", "ctrl_fx_lcu_per_usd", "ctrl_policy_rate"
    ]
    for c in required_cols:
        assert c in df.columns, f"Column {c} missing from analysis_tier1_2010plus"

    # ind_prod must NOT be in default controls table
    assert "ctrl_ind_prod" not in df.columns, "ctrl_ind_prod should only be in sensitivity table"

    # All decisions must be 2010+
    assert (df["decision_date"] >= "2010-01-01").all()
    assert (df["shock_tier"] == 1).all()


def test_v2_tier2_primary_table_structure():
    p = DATA_V2 / "analysis_tier2_primary_2010plus.parquet"
    df = pd.read_parquet(p)
    assert len(df) == 7643, f"Expected 7,643 rows in Tier 2 Primary 2010+, got {len(df)}"

    # All decisions must be 2010+
    assert (df["decision_date"] >= "2010-01-01").all()
    assert (df["shock_tier"] == 2).all()
    assert (df["shock_primary"] == 1).all()


def test_v2_secondary_holds_table_structure():
    p = DATA_V2 / "secondary_holds_2010plus.parquet"
    df = pd.read_parquet(p)
    assert len(df) == 15895, f"Expected 15,895 rows in Secondary Holds 2010+, got {len(df)}"
    assert (df["decision"] == "hold").all()
    assert (df["shock_secondary"] == 1).all()


def test_v2_sensitivity_macro_table_structure():
    p = DATA_V2 / "sensitivity_macro_revision_2010plus.parquet"
    df = pd.read_parquet(p)
    assert len(df) == 17375, f"Expected 17,375 rows in sensitivity table, got {len(df)}"
    assert "ctrl_ind_prod" in df.columns, "Sensitivity table must contain ctrl_ind_prod"


def test_v2_row_quality_flags():
    p = DATA_V2 / "analysis_tier1_2010plus.parquet"
    df = pd.read_parquet(p)

    # Both SP500 and Nikkei 225 verified against FRED
    verified_indices = df[df["index_id"].isin(["us_sp500", "jp_nikkei225"])]
    assert (verified_indices["price_source_verified"] == 1).all()
    other_indices = df[~df["index_id"].isin(["us_sp500", "jp_nikkei225"])]
    assert (other_indices["price_source_verified"] == 0).all()

    # ETF proxies identified
    etf_rows = df[df["index_id"].isin(["ea_emu_smallcap_etf", "de_stoxx_banks_etf", "jp_topix_banks_etf", "kr_banks_etf", "jp_mothers_etf"])]
    assert (etf_rows["proxy_type"] == "etf_proxy").all()

    # Shock replicated is binary
    assert set(df["shock_replicated"].unique()).issubset({0, 1})

    # Analysis OK column exists and is binary
    assert set(df["analysis_ok"].unique()).issubset({0, 1})


def test_v2_tables_final_holdout_locked_by_model_guard(monkeypatch):
    """Confirm final_holdout flag is present in every v2 table and blocked by model_guard."""
    monkeypatch.delenv("UNLOCK_HOLDOUT", raising=False)
    monkeypatch.delenv("UNLOCK_BLIND", raising=False)

    for fname in V2_TABLES:
        df = pd.read_parquet(DATA_V2 / fname)
        assert "final_holdout" in df.columns, f"final_holdout missing in {fname}"
        assert set(df["final_holdout"].unique()).issubset({0, 1})

        # Passing full dataset with final_holdout == 1 must raise PermissionError
        with pytest.raises(PermissionError):
            assert_no_holdout(df)

        # Passing filtered dataset without final_holdout rows must succeed
        df_clean = df[df["final_holdout"] == 0]
        assert_no_holdout(df_clean)

        # Passing with explicit unlock must succeed
        assert_no_holdout(df, allow_holdout=True)


def test_v2_data_dictionary_exists():
    dict_path = DOCS / "v2_data_dictionary.md"
    assert dict_path.exists(), "docs/v2_data_dictionary.md must exist"
    text = dict_path.read_text(encoding="utf-8")
    assert "analysis_tier1_2010plus" in text
    assert "analysis_tier2_primary_2010plus" in text
    assert "secondary_holds_2010plus" in text
    assert "panel_2010plus" in text
    assert "shock_replicated" in text
    assert "analysis_ok" in text
    assert "final_holdout" in text
