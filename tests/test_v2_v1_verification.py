"""Tests for Phase V1 Independent Verification Pipeline and Data Quality Scorecard."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest


def test_verification_summary_exists_and_grades():
    p = Path("outputs/v2/verification_summary.csv")
    assert p.exists(), "outputs/v2/verification_summary.csv must exist"
    df = pd.read_csv(p)
    assert len(df) == 6, f"Expected 6 check families, got {len(df)}"

    required_families = [
        "A. Index Prices",
        "B. Policy Decisions",
        "C. Shocks & Yields",
        "D. Event Returns",
        "E. Timing & DST Edge Cases",
        "F. Macro Controls Lags",
    ]
    for fam in required_families:
        assert (df["check_family"] == fam).any(), f"Family {fam} missing from verification summary"

    # All check families must have status PASS
    for _, row in df.iterrows():
        assert "PASS" in row["status"], f"Family {row['check_family']} failed with status: {row['status']}"


def test_price_crosscheck_csv():
    p = Path("outputs/v2/price_crosscheck.csv")
    assert p.exists()
    df = pd.read_csv(p)
    assert len(df) == 38, f"Expected 38 series, got {len(df)}"

    # Check ETF proxies
    etf_proxies = ["de_stoxx_banks_etf", "ea_emu_smallcap_etf", "jp_topix_banks_etf", "jp_mothers_etf", "kr_banks_etf"]
    for proxy in etf_proxies:
        p_row = df[df["index_id"] == proxy]
        assert len(p_row) == 1
        assert p_row["proxy_type"].iloc[0] == "etf_proxy"
        assert pd.notna(p_row["tracking_error_ann"].iloc[0])


def test_policy_crosscheck_csv():
    p = Path("outputs/v2/policy_crosscheck.csv")
    assert p.exists()
    df = pd.read_csv(p)
    assert len(df) >= 993, f"Expected at least 993 rows, got {len(df)}"

    # Verify skipped regimes have 'not verified' note
    skipped = ["Banxico", "BoK", "RBI", "PBoC", "BCB"]
    for s in skipped:
        s_rows = df[df["regime"] == s]
        assert len(s_rows) > 0
        assert "not verified" in s_rows["resolution_evidence"].iloc[0].lower()


def test_shocks_crosscheck_csv():
    p = Path("outputs/v2/shocks_crosscheck.csv")
    assert p.exists()
    df = pd.read_csv(p)

    fed_row = df[df["test"].str.contains("Fed Standardized Shock")]
    assert len(fed_row) == 1
    assert float(fed_row["max_diff"].iloc[0]) < 1e-5

    ecb_row = df[df["test"].str.contains("ECB Standardized Shock")]
    assert len(ecb_row) == 1
    assert float(ecb_row["max_diff"].iloc[0]) < 1e-5


def test_scorecard_and_limitations_exist():
    scorecard = Path("docs/v2_quality_scorecard.md")
    limitations = Path("docs/v2_limitations.md")
    assert scorecard.exists()
    assert limitations.exists()

    sc_text = scorecard.read_text(encoding="utf-8")
    assert "Grade A" in sc_text
    assert "Grade B" in sc_text
    assert "A. Index Prices" in sc_text

    lim_text = limitations.read_text(encoding="utf-8")
    assert "Single-Source Price Series" in lim_text
    assert "ETF Proxy Tracking Errors" in lim_text
