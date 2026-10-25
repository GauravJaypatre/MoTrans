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

    # Assert check_type column exists and contains valid types
    assert "check_type" in df.columns, "check_type column missing"
    assert set(df["check_type"].unique()).issubset({"arithmetic", "replication", "external"}), "Invalid check_type found"

    # Assert split grade columns exist
    assert "internal_consistency" in df.columns, "internal_consistency column missing"
    assert "external_verification" in df.columns, "external_verification column missing"

    # Check honest regraded grades
    grades = dict(zip(df["check_family"], zip(df["internal_consistency"], df["external_verification"].fillna(""))))
    assert grades["A. Index Prices"] == ("Grade A", "Grade C"), "Prices must be Internal A, External C (single-source)"
    assert grades["B. Policy Decisions"] == ("Grade A", "Grade B"), "Policy must be Internal A, External B"
    assert grades["C. Shocks & Yields"] == ("Grade A", ""), "Shocks must be Internal A, External blank"
    assert grades["D. Event Returns"] == ("Grade A", "Grade B"), "Event returns must be Internal A, External B"
    assert grades["E. Timing & DST Edge Cases"] == ("Grade A", "Grade C"), "Timing must be Internal A, External C"
    assert grades["F. Macro Controls Lags"] == ("Grade A", "Grade C"), "Controls must be Internal A, External C (StatCan unverified)"

    # All check families must have status PASS
    for _, row in df.iterrows():
        assert "PASS" in row["status"], f"Family {row['check_family']} failed with status: {row['status']}"


def test_price_second_source_check():
    p = Path("outputs/v2/prices_second_source_check.csv")
    assert p.exists(), "outputs/v2/prices_second_source_check.csv must exist"
    df = pd.read_csv(p)
    assert len(df) == 39, f"Expected 39 rows, got {len(df)}"

    sp500 = df[df["ticker"] == "^GSPC"]
    assert len(sp500) == 1
    assert sp500["n_compared"].iloc[0] > 2000
    assert sp500["max_abs_ret_diff"].iloc[0] < 0.002
    assert "PASS" in sp500["status"].iloc[0]

    # Verify single-source series count
    single_source = df[df["status"].str.contains("SINGLE_SOURCE")]
    assert len(single_source) == 36, f"Expected 36 single-source series, got {len(single_source)}"


def test_policy_2026_and_rba_fixed():
    p = Path("outputs/v2/policy_2026_verified.csv")
    assert p.exists(), "outputs/v2/policy_2026_verified.csv must exist"
    df = pd.read_csv(p)
    assert len(df) == 41, f"Expected 41 decisions in 2026, got {len(df)}"

    # Explicitly check RBA 2026-09-29 is verified match as hike
    rba_sep = df[(df["regime"] == "RBA") & (df["dataset_date"] == "2026-09-29")]
    assert len(rba_sep) == 1
    assert rba_sep["verification_status"].iloc[0] == "VERIFIED_MATCH"
    assert rba_sep["dataset_decision"].iloc[0] == "hike"
    assert rba_sep["official_decision"].iloc[0] == "hike"
    assert rba_sep["dataset_size_bp"].iloc[0] == 25.0
    assert rba_sep["dataset_new_rate"].iloc[0] == 4.60
    assert "4.60 per cent" in rba_sep["official_text_excerpt"].iloc[0]


def test_timing_official_check():
    p = Path("outputs/v2/timing_official_check.csv")
    assert p.exists(), "outputs/v2/timing_official_check.csv must exist"
    df = pd.read_csv(p)
    assert len(df) == 100, f"Expected 100 verified timing events, got {len(df)}"

    regimes = set(df["regime"].unique())
    assert regimes == {"Fed", "ECB", "BoE", "BoC", "RBA"}

    # 10 per convention period across 5 regimes = 20 per regime
    for r in regimes:
        assert (df["regime"] == r).sum() == 20, f"Expected 20 events for {r}"

    assert (df["timing_verified"] == 1).all()
    assert (df["timestamp_match"] == 1).all()

    # Evidence levels
    assert "convention_verified" in df.columns
    assert "event_verified" in df.columns
    assert "timing_verified_level" in df.columns
    assert (df["convention_verified"] == 1).all()
    assert df["event_verified"].sum() == 11  # 10 Fed statements + 1 RBA statement

    # Valid IANA timezone check
    assert not df["timezone"].str.contains("Frankfurt").any()
    assert (df["timezone"] == "Europe/Berlin").any()


def test_controls_cpi_and_vintage_audit():
    p_cpi = Path("outputs/v2/cpi_release_calendar_check.csv")
    assert p_cpi.exists()
    df_cpi = pd.read_csv(p_cpi)
    assert len(df_cpi) == 144, f"Expected 144 CPI releases, got {len(df_cpi)}"

    for c in ["US", "EA", "GB", "CA", "AU", "JP"]:
        assert (df_cpi["country"] == c).sum() == 24, f"Expected 24 releases for {c}"

    assert (df_cpi["zero_lookahead_verified"] == 1).all()
    assert (df_cpi["conservative_lag_days"] >= 0).all()

    p_vin = Path("outputs/v2/controls_vintage_audit.csv")
    assert p_vin.exists()
    df_vin = pd.read_csv(p_vin)
    ip_row = df_vin[df_vin["variable"] == "ind_prod"]
    assert len(ip_row) == 1
    assert ip_row["revised_series"].iloc[0] == 1
    assert "EXCLUDE_FROM_DEFAULT_SET" in ip_row["v2_recommendation"].iloc[0]


def test_shocks_replication_and_event_alignment():
    p_shk = Path("outputs/v2/shocks_replication_check.csv")
    assert p_shk.exists()
    df_shk = pd.read_csv(p_shk)
    assert len(df_shk) == 20, f"Expected 20 replication shock checks, got {len(df_shk)}"
    assert (df_shk["check_type"] == "replication").all()
    assert (df_shk["replication_status"] == "VERIFIED_INTERNAL_REPLICATION").all()

    p_align = Path("outputs/v2/event_alignment_audit.csv")
    assert p_align.exists()
    df_align = pd.read_csv(p_align)
    assert len(df_align) == 500, f"Expected 500 sampled events, got {len(df_align)}"
    assert (df_align["alignment_verified"] == 1).all()


def test_cbr_date_verification_audit():
    p_cbr = Path("outputs/v2/cbr_date_verification_audit.csv")
    assert p_cbr.exists(), "outputs/v2/cbr_date_verification_audit.csv must exist"
    df = pd.read_csv(p_cbr)
    assert len(df) == 51, f"Expected 51 CBR decisions, got {len(df)}"
    assert (df["is_effective"] == 1).sum() == 41, "Expected 41 effective decisions"
    assert df["date_changed"].sum() == 38, "Expected 38 decisions where date changes to Friday"


def test_scorecard_and_limitations_exist():
    scorecard = Path("docs/v2_quality_scorecard.md")
    limitations = Path("docs/v2_limitations.md")
    assert scorecard.exists()
    assert limitations.exists()

    sc_text = scorecard.read_text(encoding="utf-8")
    assert "Grade A" in sc_text
    assert "Grade B" in sc_text
    assert "Grade C" in sc_text
    assert "Internal Consistency" in sc_text
    assert "External Verification" in sc_text
    assert "A. Index Prices" in sc_text

    lim_text = limitations.read_text(encoding="utf-8")
    assert "Single-Source Price Series" in lim_text
    assert "RBA 2026-09-29" in lim_text
    assert "CBR Meeting vs Effective Dates" in lim_text
    assert "CBR Omission of Scheduled Holds" in lim_text
