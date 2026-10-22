
"""High-frequency monetary policy surprise coverage test.

Asserts that:
1. 100% of ECB policy decisions within EA-MPD high-frequency coverage (up to 2025-10-30)
   match a high-frequency surprise row (Grade A).
2. All Fed decisions within FRBSF Bauer-Swanson coverage (up to 2023-12-13), excluding
   the 3 known exceptions (2001-09-17 9/11 market closure, 2007-06-18 call, 2010-05-09 Sunday swap),
   match a high-frequency surprise row (Grade A).
3. All post-coverage decisions fall back cleanly to Grade B sovereign yield proxies.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from src.build_shocks import eampd, frbsf

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"

needs_data = pytest.mark.skipif(not (FINAL / "shocks.parquet").exists(), reason="run pipeline first")


@pytest.fixture(scope="module")
def shocks_df() -> pd.DataFrame:
    return pd.read_parquet(FINAL / "shocks.parquet")


@needs_data
class TestHighFrequencyCoverage:
    def test_ecb_decisions_within_hf_coverage_match_surprise_row(self, shocks_df):
        """Every ECB decision on or before 2025-10-30 must match an EA-MPD row and have Grade A."""
        ea = eampd()
        max_date = ea["date"].max()  # 2025-10-30
        assert max_date == dt.date(2025, 10, 30), f"Expected EA-MPD max date 2025-10-30, got {max_date}"

        ecb_shocks = shocks_df[shocks_df["regime"] == "ECB"]
        in_range = ecb_shocks[pd.to_datetime(ecb_shocks["decision_date"]).dt.date <= max_date]

        assert len(in_range) == 292, f"Expected 292 ECB decisions in HF coverage, found {len(in_range)}"
        unmatched = in_range[in_range["shock_grade"] != "A"]
        assert len(unmatched) == 0, (
            f"Found {len(unmatched)} ECB decisions in HF coverage without Grade A: "
            f"{unmatched[['decision_date', 'shock_grade']].to_dict('records')}"
        )
        assert (in_range["shock_hf_raw"].notna()).all()
        assert (in_range["shock_measure_type"] == "hf_ois").all()

    def test_fed_decisions_within_hf_coverage_match_surprise_row(self, shocks_df):
        """Every Fed decision on or before 2023-12-13 (excl 3 documented exceptions) must have Grade A."""
        fs = frbsf()
        max_date = fs["date"].max()  # 2023-12-13
        assert max_date == dt.date(2023, 12, 13), f"Expected FRBSF max date 2023-12-13, got {max_date}"

        fed_shocks = shocks_df[shocks_df["regime"] == "Fed"]
        in_range = fed_shocks[pd.to_datetime(fed_shocks["decision_date"]).dt.date <= max_date]

        assert len(in_range) == 204, f"Expected 204 Fed decisions in HF coverage range, found {len(in_range)}"

        # The 3 documented in-range exceptions
        known_exceptions = {dt.date(2001, 9, 17), dt.date(2007, 6, 18), dt.date(2010, 5, 9)}
        matched = in_range[~pd.to_datetime(in_range["decision_date"]).dt.date.isin(known_exceptions)]

        assert len(matched) == 201, f"Expected 201 matched Fed decisions, got {len(matched)}"
        unmatched = matched[matched["shock_grade"] != "A"]
        assert len(unmatched) == 0, (
            f"Found {len(unmatched)} Fed decisions in HF coverage without Grade A: "
            f"{unmatched[['decision_date', 'shock_grade']].to_dict('records')}"
        )
        assert (matched["shock_hf_raw"].notna()).all()
        assert (matched["shock_measure_type"] == "hf_ois").all()

    def test_post_coverage_decisions_fallback_to_grade_b(self, shocks_df):
        """Decisions past high-frequency coverage must fall back to Grade B yield proxy."""
        ecb_post = shocks_df[(shocks_df["regime"] == "ECB") & (pd.to_datetime(shocks_df["decision_date"]).dt.date > dt.date(2025, 10, 30))]
        assert len(ecb_post) == 7
        assert (ecb_post["shock_grade"] == "B").all()
        assert (ecb_post["shock_measure_type"] == "yield_proxy").all()

        fed_post = shocks_df[(shocks_df["regime"] == "Fed") & (pd.to_datetime(shocks_df["decision_date"]).dt.date > dt.date(2023, 12, 13))]
        assert len(fed_post) == 23
        assert (fed_post["shock_grade"] == "B").all()
        assert (fed_post["shock_measure_type"] == "yield_proxy").all()
