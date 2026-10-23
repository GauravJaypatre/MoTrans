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
        # With all scheduled holds added (including 67 pre-2008 holds), RBA has 287 decisions: 284 Grade B, 3 Grade C
        assert (rba["shock_grade"] == "B").sum() == 284
        assert (rba["shock_grade"] == "C").sum() == 3
        assert (rba["shock_usable"] == 1).sum() == 284

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

        # Check regimes with >= 20 blind-test events (including newly expanded holds)
        for reg in ["Fed", "ECB", "BoJ", "CBR", "BoC", "BoE", "RBA"]:
            assert counts.get(reg, 0) >= 20, f"{reg} expected >= 20 blind-test events but got {counts.get(reg, 0)}"

        # Check regimes flagged with < 20 blind-test events
        for reg in ["BCB", "Banxico", "BoK", "PBoC", "RBI"]:
            assert counts.get(reg, 0) < 20, f"{reg} expected < 20 blind-test events but got {counts.get(reg, 0)}"

    def test_japan_zirp_quality_flag(self, shocks_df):
        """BoJ events during the zero-rate / QQE era must carry the honest quality flag."""
        boj_zirp = shocks_df[(shocks_df["regime"] == "BoJ") & (shocks_df["decision_date"].astype(str) <= "2024-03-18")]
        assert (boj_zirp["shock_quality_flag"] == "low_sensitivity_zero_lower_bound").all()

    def test_shock_primary_definition(self, shocks_df):
        """shock_primary must be 0 for all BoJ (pre-registered baseline rule), CBR post-Feb 2022, and China PBoC."""
        # BoJ: all 333 decisions have shock_primary == 0 under pre-registered baseline rule
        boj = shocks_df[shocks_df["regime"] == "BoJ"]
        assert (boj["shock_primary"] == 0).all()
        # Sensitivity analysis flag shock_primary_rescaled admits post-exit events
        boj_post = shocks_df[(shocks_df["regime"] == "BoJ") & (shocks_df["decision_date"].astype(str) > "2024-03-18")]
        assert (boj_post["shock_primary_rescaled"] == 1).all()

        # CBR post-Feb 2022
        cbr_break = shocks_df[(shocks_df["regime"] == "CBR") & (shocks_df["decision_date"].astype(str) >= "2022-02-24")]
        assert (cbr_break["shock_primary"] == 0).all()

        # PBoC
        pboc = shocks_df[shocks_df["regime"] == "PBoC"]
        assert (pboc["shock_primary"] == 0).all()

        # Clean Fed and ECB must have shock_primary == shock_usable
        for reg in ["Fed", "ECB"]:
            sub = shocks_df[shocks_df["regime"] == reg]
            assert (sub["shock_primary"] == sub["shock_usable"]).all()

        # RBA pre-2008 unannounced holds must have shock_primary == 0 and quality flag
        rba_pre_holds = shocks_df[(shocks_df["regime"] == "RBA") & (shocks_df["decision_date"].astype(str) < "2008-02-01") & (shocks_df["decision"] == "hold")]
        assert len(rba_pre_holds) == 68
        assert (rba_pre_holds["shock_primary"] == 0).all()
        assert (rba_pre_holds["shock_quality_flag"] == "rba_pre2008_unannounced_hold").all()

    def test_shock_measure_type(self, shocks_df):
        """shock_measure_type must be 'hf_ois' for Grade A, 'yield_proxy' for Grade B, '' for Grade C."""
        assert (shocks_df[shocks_df["shock_grade"] == "A"]["shock_measure_type"] == "hf_ois").all()
        assert (shocks_df[shocks_df["shock_grade"] == "B"]["shock_measure_type"] == "yield_proxy").all()
        assert (shocks_df[shocks_df["shock_grade"] == "C"]["shock_measure_type"] == "").all()

    def test_shock_std_peer_scale(self, shocks_df):
        """shock_std_peer_scale must rescale BoJ shocks using peer DM scale and match shock_std elsewhere."""
        boj_post = shocks_df[(shocks_df["regime"] == "BoJ") & (shocks_df["decision_date"].astype(str) > "2024-03-18")]
        nonzero = boj_post[boj_post["shock_proxy_raw"] != 0]
        assert (nonzero["shock_std_peer_scale"] != nonzero["shock_std"]).all()
        non_boj = shocks_df[shocks_df["regime"] != "BoJ"]
        pd.testing.assert_series_equal(non_boj["shock_std_peer_scale"], non_boj["shock_std"], check_names=False)

    def test_winsorized_shock_bounds(self, shocks_df):
        """shock_std_w must be capped strictly within [-4.0, 4.0]."""
        valid = shocks_df[shocks_df["shock_std"].notna()]
        assert (valid["shock_std_w"] >= -4.0).all()
        assert (valid["shock_std_w"] <= 4.0).all()
        # Raw shock must not be overwritten
        assert (valid["shock_std"] != valid["shock_std_w"]).any(), "Winsorization did not cap any outliers!"

    def test_shock_proxy_tenor(self, shocks_df):
        """Tenors must match expected values (2Y for AU, CN, CA; 1Y for US, EA, JP, GB, RU, BR)."""
        tenors = shocks_df[shocks_df["shock_proxy_std"].notna()].groupby("regime")["shock_proxy_tenor"].unique()
        assert tenors["RBA"] == ["2Y"]
        assert tenors["PBoC"] == ["2Y"]
        assert tenors["BoC"] == ["2Y"]
        for reg in ["Fed", "ECB", "BoJ", "BoE", "CBR", "BCB"]:
            assert tenors[reg] == ["1Y"]

    def test_controls_yield_2y(self):
        """AU and CN yields in controls_long must be labeled yield_2y, not yield_1y."""
        controls = pd.read_parquet(INTERIM / "controls_long.parquet")
        assert (controls[controls["country"] == "AU"]["variable"] == "yield_2y").any()
        assert not (controls[controls["country"] == "AU"]["variable"] == "yield_1y").any()
        assert (controls[controls["country"] == "CN"]["variable"] == "yield_2y").any()
        assert not (controls[controls["country"] == "CN"]["variable"] == "yield_1y").any()

    def test_shock_tier_definition(self, shocks_df):
        """shock_tier must be 1 for hf_ois (Grade A), 2 for yield_proxy (Grade B), and null for Grade C."""
        tier1 = shocks_df[shocks_df["shock_tier"] == 1]
        assert (tier1["shock_grade"] == "A").all()
        assert (tier1["shock_measure_type"] == "hf_ois").all()
        assert set(tier1["regime"].unique()) == {"Fed", "ECB"}

        tier2 = shocks_df[shocks_df["shock_tier"] == 2]
        assert (tier2["shock_grade"] == "B").all()
        assert (tier2["shock_measure_type"] == "yield_proxy").all()

        unshocked = shocks_df[shocks_df["shock_tier"].isna()]
        assert (unshocked["shock_grade"] == "C").all()
        assert (unshocked["shock_usable"] == 0).all()

    def test_overlap_columns(self, shocks_df, events_df):
        """Overlap columns must be present in shocks and events for W in 1, 3, 5, 20, 60."""
        for W in (1, 3, 5, 20, 60):
            flag_col = f"overlap_{W}d"
            cnt_col = f"overlap_count_{W}d"
            assert flag_col in shocks_df.columns
            assert cnt_col in shocks_df.columns
            assert flag_col in events_df.columns
            assert cnt_col in events_df.columns

            assert shocks_df[flag_col].isin([0, 1]).all()
            assert (shocks_df[cnt_col] >= 0).all()
