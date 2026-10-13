"""Phase B1 data checks: provenance, policy-decision table and index panel.

These run against data/raw and data/interim, which are not in git. On a fresh clone
they are skipped until the collectors have been run.

The "known event" tests are spot checks of the parsers against well-documented
decisions; they are assertions about the output, not inputs to it.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
POLICY = ROOT / "data" / "interim" / "pilot_policy_decisions.csv"
PANEL = ROOT / "data" / "interim" / "pilot_indices_daily.parquet"

needs_policy = pytest.mark.skipif(not POLICY.exists(), reason="run src.collect_policy first")
needs_panel = pytest.mark.skipif(not PANEL.exists(), reason="run src.collect_indices first")


@pytest.fixture(scope="module")
def policy() -> pd.DataFrame:
    return pd.read_csv(POLICY, parse_dates=["decision_date"])


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_parquet(PANEL)


def event(policy: pd.DataFrame, regime: str, day: str) -> pd.Series:
    hit = policy[(policy.regime == regime) & (policy.decision_date == day)]
    assert len(hit) == 1, f"{regime} {day}: expected one row, found {len(hit)}"
    return hit.iloc[0]


# --- provenance --------------------------------------------------------------

@pytest.mark.skipif(not any(RAW.glob("*.csv")), reason="no raw data downloaded")
class TestManifest:
    def rows(self):
        with open(RAW / "MANIFEST.csv", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_every_raw_file_is_registered(self):
        registered = {Path(r["file_path"]).as_posix() for r in self.rows()}
        on_disk = {p.relative_to(ROOT).as_posix() for p in RAW.rglob("*")
                   if p.is_file() and p.name not in (".gitkeep", "MANIFEST.csv")}
        assert on_disk - registered == set()

    def test_hashes_match(self):
        bad = []
        for r in self.rows():
            path = ROOT / Path(r["file_path"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != r["sha256"]:
                bad.append(r["file_path"])
        assert bad == []


# --- policy decisions --------------------------------------------------------

@needs_policy
class TestPolicySchema:
    def test_categories(self, policy):
        assert set(policy.decision) <= {"hike", "cut", "hold", "unclassified"}
        assert (policy[policy.decision == "unclassified"].regime == "BoJ").all()
        assert set(policy.time_quality) <= {"exact", "approximate", "unknown"}
        assert set(policy.regime) == {"Fed", "ECB", "RBI", "BoJ"}

    def test_every_row_has_a_source(self, policy):
        assert policy.date_source.notna().all() and policy.source_url.notna().all()

    def test_known_time_has_utc_timestamp(self, policy):
        known = policy[policy.time_quality != "unknown"]
        assert known.announce_ts_utc.notna().all()

    def test_no_duplicate_events(self, policy):
        assert not policy.duplicated(["regime", "decision_date"]).any()

    def test_holds_present(self, policy):
        holds = policy[policy.decision == "hold"].groupby("regime").size()
        assert (holds > 20).all()

    def test_fed_meets_every_year(self, policy):
        fed = policy[(policy.regime == "Fed") & (policy.event_type == "scheduled_meeting")]
        per_year = fed.groupby(fed.decision_date.dt.year).size()
        # March 2020's scheduled meeting was replaced by the unscheduled 15 March meeting.
        assert per_year.loc[2000:2025].drop(2020).min() >= 8 and per_year.loc[2020] == 7


@needs_policy
class TestKnownEvents:
    def test_fed_2022_03_16_hike(self, policy):
        e = event(policy, "Fed", "2022-03-16")
        assert (e.decision, e.size_bp, e.announce_time_local) == ("hike", 25, "14:00")

    def test_fed_2020_03_15_sunday_cut(self, policy):
        e = event(policy, "Fed", "2020-03-15")
        assert (e.decision, e.size_bp, e.announce_time_local, bool(e.scheduled)) == ("cut", -100, "17:00", False)

    def test_fed_2020_03_03_intermeeting_cut(self, policy):
        e = event(policy, "Fed", "2020-03-03")
        assert (e.decision, e.size_bp, bool(e.scheduled)) == ("cut", -50, False)

    def test_fed_2008_12_16_range(self, policy):
        e = event(policy, "Fed", "2008-12-16")
        assert (e.decision, e.size_bp, e.new_rate_pct) == ("cut", -75, 0.25)

    def test_fed_2004_2006_tightening(self, policy):
        fed = policy[(policy.regime == "Fed") & policy.decision_date.between("2004-06-01", "2006-06-30")]
        assert (fed.decision == "hike").sum() == 17

    def test_ecb_2005_2008_hikes(self, policy):
        ecb = policy[(policy.regime == "ECB") & policy.decision_date.between("2005-12-01", "2008-07-31")]
        assert (ecb.decision == "hike").sum() == 9

    def test_ecb_2022_07_21(self, policy):
        e = event(policy, "ECB", "2022-07-21")
        assert (e.decision, e.size_bp, e.announce_time_local) == ("hike", 50, "14:15")

    def test_ecb_2011_04_07(self, policy):
        e = event(policy, "ECB", "2011-04-07")
        assert (e.decision, e.size_bp, e.announce_time_local) == ("hike", 25, "13:45")

    def test_rbi_2022_05_04_offcycle(self, policy):
        e = event(policy, "RBI", "2022-05-04")
        assert (e.decision, e.size_bp) == ("hike", 40)

    def test_boj_2016_01_29_inside_quantity_target_gap(self, policy):
        # BIS has no JP policy rate Apr 2013 - Sep 2016, so the decision is left for Phase D.
        assert event(policy, "BoJ", "2016-01-29").decision == "unclassified"

    def test_boj_2024_03_19_exit_negative_rates(self, policy):
        e = event(policy, "BoJ", "2024-03-19")
        assert (e.decision, e.new_rate_pct) == ("hike", 0.05)

    def test_boj_2016_01_29_time_from_minutes(self, policy):
        e = event(policy, "BoJ", "2016-01-29")
        assert (e.announce_time_local, e.time_quality) == ("12:31", "approximate")


# --- index panel -------------------------------------------------------------

@needs_panel
class TestPanel:
    def test_thirteen_series(self, panel):
        assert panel.index_id.nunique() == 13

    def test_no_duplicate_dates(self, panel):
        assert not panel.duplicated(["index_id", "date"]).any()

    def test_log_return_math(self, panel):
        for _, g in panel.groupby("index_id"):
            g = g.sort_values("date")
            expected = np.log(g.level_local / g.level_local.shift(1))
            assert np.allclose(g.ret_local, expected, equal_nan=True)

    def test_finite_and_flagged(self, panel):
        r = panel.ret_local.dropna()
        assert np.isfinite(r).all()
        assert ((panel.ret_local.abs() > 0.10) == panel.outlier_flag.astype(bool)).all()

    def test_india_from_official_source_since_2000(self, panel):
        nifty = panel[panel.index_id == "in_nifty50"]
        assert nifty.source.iloc[0] == "niftyindices.com" and str(nifty.date.min()) < "2000-01-10"


# --- announcement windows (DECISION-013) ----------------------------------------

@needs_policy
class TestAnnouncementWindow:
    def test_every_row_has_a_window(self, policy):
        assert policy.window_start_utc.notna().all() and policy.window_end_utc.notna().all()
        assert (policy.window_start_utc <= policy.window_end_utc).all()

    def test_known_time_inside_window(self, policy):
        known = policy[policy.time_quality != "unknown"]
        assert ((known.window_start_utc <= known.announce_ts_utc)
                & (known.announce_ts_utc <= known.window_end_utc)).all()

    def test_exact_is_a_point(self, policy):
        e = event(policy, "Fed", "2022-03-16")
        assert e.window_start_utc == e.window_end_utc == "2022-03-16T18:00:00Z"

    def test_boj_meeting_end_plus_one_hour(self, policy):
        e = event(policy, "BoJ", "2016-01-29")  # meeting ended 12:31 JST
        assert (e.window_start_utc, e.window_end_utc) == ("2016-01-29T03:31:00Z", "2016-01-29T04:31:00Z")

    def test_unknown_is_the_whole_local_day(self, policy):
        e = event(policy, "RBI", "2022-05-04")  # IST = UTC+5:30
        assert (e.window_start_utc, e.window_end_utc) == ("2022-05-03T18:30:00Z", "2022-05-04T18:29:00Z")


# --- event windows (Phase B2) -----------------------------------------------------

EVENTS = ROOT / "data" / "interim" / "pilot_events.parquet"


@pytest.fixture(scope="module")
def events() -> pd.DataFrame:
    return pd.read_parquet(EVENTS)


@pytest.mark.skipif(not EVENTS.exists(), reason="run src.event_windows first")
class TestEventWindows:
    def test_one_row_per_event_and_series(self, events):
        assert not events.duplicated(["event_id", "index_id"]).any()

    def test_baseline_before_reaction(self, events):
        assert (events.baseline_date < events.reacting_session_date).all()
        assert (events.baseline_obs_date < events.react_obs_date).all()

    def test_clr_1_matches_the_daily_return(self, events, panel):
        # When the reacting observation directly follows the baseline one, clr_1 is that day's return.
        ret = panel.set_index(["index_id", "date"])["ret_local"]
        sample = events.sample(500, random_state=0)
        for r in sample.itertuples():
            dates = panel.loc[panel.index_id == r.index_id, "date"]
            prev = dates[dates < r.react_obs_date].max()
            if prev == r.baseline_obs_date:
                assert np.isclose(r.clr_1, ret[(r.index_id, r.react_obs_date)])

    def test_home_market_flag(self, events):
        home = events[events.home_market == 1].groupby("regime").country.unique()
        assert {k: list(v) for k, v in home.items()} == {"BoJ": ["JP"], "ECB": ["DE"], "Fed": ["US"], "RBI": ["IN"]}

    def test_exact_time_events_are_never_ambiguous(self, events):
        assert events.loc[events.time_quality == "exact", "timing_ambiguous"].eq(0).all()
