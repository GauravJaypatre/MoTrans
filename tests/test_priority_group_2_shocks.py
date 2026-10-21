"""Priority Group 2 validation: monetary policy shocks, yield proxies, and shock_usable flag.

Checks that:
1. shock_usable flag is consistent with its definition (1 iff grade in {'A', 'B'} and shock_std is not null).
2. Decision size (size_bp) is never substituted for a missing shock.
3. RBA (AU) and PBoC (CN) have Grade B yield proxies standardized within regime.
4. Banxico, BoK, and RBI remain Grade C without fabricated values.
5. Regimes with fewer than 20 usable blind-test events are identified.
6. Japan zero-rate era events carry the honest quality flag.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"

needs_data = pytest.mark.skipif(not (FINAL / "shocks.parquet").exists(), reason="run pipeline first")


@pytest.fixture(scope="module")
def shocks_df() -> pd.DataFrame:
    return pd.read_parquet(FINAL / "shocks.parquet")


@pytest.fixture(scope="module")
def events_df() -> pd.DataFrame:
    return pd.read_parquet(FINAL / "events.parquet")


@pytest.fixture(scope="module")
def policy_df() -> pd.DataFrame:
    return pd.read_csv(FINAL / "policy_decisions.csv", dtype={"decision_date": str})


@needs_data
class TestPriorityGroup2Shocks:
    def test_shock_usable_definition(self, shocks_df):
        """shock_usable must be 1 iff shock_std is not null and shock_grade in ('A', 'B')."""
        expected = (shocks_df["shock_grade"].isin(["A", "B"]) & shocks_df["shock_std"].notna()).astype(int)
        assert (shocks_df["shock_usable"] == expected).all()

    def test_no_substitution_of_size_for_shock(self, shocks_df):
        """Decision size must NEVER be used as a substitute for a surprise."""
        unusable = shocks_df[shocks_df["shock_usable"] == 0]
        # In unusable events, shock_raw and shock_std must be null
        assert unusable["shock_raw"].isna().all(), "Unusable shocks carry non-null shock_raw!"
        assert unusable["shock_std"].isna().all(), "Unusable shocks carry non-null shock_std!"

    def test_rba_and_pboc_have_grade_b_proxies(self, shocks_df):
        """RBA and PBoC must have Grade B yield-change proxies from sovereign yield data."""
        pboc = shocks_df[shocks_df["regime"] == "PBoC"]
        assert (pboc["shock_grade"] == "B").all()
        assert (pboc["shock_usable"] == 1).all()
        assert len(pboc) == 40

        rba = shocks_df[shocks_df["regime"] == "RBA"]
        # Exactly 71 of 72 events have Grade B; 1 (2013-08-07) has no 2y yield in transition window
        assert (rba["shock_grade"] == "B").sum() == 71
        assert (rba["shock_grade"] == "C").sum() == 1
        assert (rba["shock_usable"] == 1).sum() == 71

    def test_gated_regimes_remain_grade_c(self, shocks_df):
        """Banxico, BoK, and RBI must remain Grade C (no unsourced/fabricated numbers)."""
        for reg in ["Banxico", "BoK", "RBI"]:
            sub = shocks_df[shocks_df["regime"] == reg]
            assert (sub["shock_grade"] == "C").all(), f"{reg} carries non-C grade without public unauthenticated data!"
            assert (sub["shock_usable"] == 0).all()
            assert sub["shock_std"].isna().all()

    def test_events_and_shocks_merge_consistency(self, shocks_df, events_df):
        """shock_usable in events must match shock_usable in shocks for every event_id."""
        ev_sub = events_df[["event_id", "shock_usable", "shock_grade"]].drop_duplicates()
        merged = ev_sub.merge(shocks_df[["event_id", "shock_usable", "shock_grade"]], on="event_id", suffixes=("_ev", "_sh"))
        assert (merged["shock_usable_ev"] == merged["shock_usable_sh"]).all()
        assert (merged["shock_grade_ev"] == merged["shock_grade_sh"]).all()

    def test_blind_test_event_counts_and_flags(self, shocks_df):
        """Verify the usable blind_test event counts by regime."""
        bt = shocks_df[(shocks_df["split_tag"] == "blind_test") & (shocks_df["shock_usable"] == 1)]
        counts = bt.groupby("regime").size().to_dict()

        # Check regimes with >= 20 blind-test events
        assert counts.get("Fed", 0) >= 20
        assert counts.get("ECB", 0) >= 20
        assert counts.get("BoJ", 0) >= 20
        assert counts.get("CBR", 0) >= 20

        # Check regimes flagged with < 20 blind-test events
        for reg in ["BCB", "Banxico", "BoC", "BoE", "BoK", "PBoC", "RBA", "RBI"]:
            assert counts.get(reg, 0) < 20, f"{reg} expected < 20 blind-test events but got {counts.get(reg, 0)}"

    def test_japan_zirp_quality_flag(self, shocks_df):
        """BoJ events during the zero-rate / QQE era must carry the honest quality flag."""
        boj_zirp = shocks_df[(shocks_df["regime"] == "BoJ") & (shocks_df["decision_date"].astype(str) <= "2024-03-18")]
        assert (boj_zirp["shock_quality_flag"] == "low_sensitivity_zero_lower_bound").all()
