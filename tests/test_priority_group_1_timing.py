"""Priority Group 1 validation: conservative reaction-session rule and session-ordering invariants.

Checks that:
1. No reacting session in the entire dataset precedes the decision date.
2. Every reacting session close is strictly after window_start_utc (checked on a random sample).
3. analysis_ready_timing flag is consistent with its definition.
4. Known event dates exist in the dataset and satisfy the session-ordering invariants.
   NOTE: time_quality values for unsourced regimes (BoE, BoC, RBA, BoK, Banxico, BCB, CBR,
   PBoC, RBI) are not asserted here because those times have not yet been sourced from
   saved files (ISS-029). Only existence in the decision/event tables is checked.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


from src.alignment import _ts, sessions

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"

needs_data = pytest.mark.skipif(not (FINAL / "events.parquet").exists(), reason="run pipeline first")

# Known event dates per regime — verified only as existing rows with valid session ordering.
# Time quality assertions for unsourced regimes are deliberately absent (see module docstring).
KNOWN_EVENTS = {
    "Fed": [
        "2001-01-03", "2008-01-22", "2008-12-16", "2011-04-27", "2013-06-19",
        "2015-12-16", "2020-03-03", "2020-03-15", "2022-03-16", "2022-06-15"
    ],
    "ECB": [
        "2000-06-08", "2001-09-17", "2008-10-08", "2011-04-07", "2011-07-07",
        "2011-11-03", "2014-06-05", "2016-03-10", "2022-07-21", "2022-09-08"
    ],
    "BoJ": [
        "2000-08-11", "2001-03-19", "2006-07-14", "2007-02-21", "2008-10-31",
        "2013-04-04", "2016-01-29", "2016-09-21", "2024-03-19", "2024-07-31"
    ],
    "BoE": [
        "2000-01-13", "2000-02-10", "2001-02-08", "2003-07-10", "2007-07-05",
        "2008-11-06", "2009-03-05", "2016-08-04", "2020-03-11", "2022-02-03"
    ],
    "BoC": [
        "2001-01-23", "2001-03-06", "2001-04-17", "2001-05-29", "2001-07-17",
        "2002-04-16", "2003-03-04", "2007-07-10", "2008-10-21", "2009-04-21"
    ],
    "RBA": [
        "2000-02-02", "2000-04-05", "2000-05-03", "2000-08-02", "2001-02-07",
        "2001-03-07", "2001-04-04", "2008-03-04", "2009-10-06", "2020-03-03"
    ],
    "BoK": [
        "2000-02-10", "2000-10-05", "2001-02-08", "2001-07-05", "2008-10-09",
        "2010-07-09", "2012-07-12", "2016-06-09", "2021-08-26", "2022-07-13"
    ],
    "Banxico": [
        "2008-06-20", "2008-07-18", "2008-08-15", "2009-01-16", "2015-12-17",
        "2017-06-22", "2019-08-15", "2021-06-24", "2022-06-23", "2024-03-21"
    ],
    "BCB": [
        "2000-06-20", "2003-02-19", "2005-09-14", "2008-04-16", "2009-01-21",
        "2016-10-19", "2020-08-05", "2021-03-17", "2022-03-16", "2023-08-02"
    ],
    "RBI": [
        "2001-04-19", "2008-10-20", "2010-03-19", "2013-05-03", "2014-01-28",
        "2016-10-04", "2018-06-06", "2020-03-27", "2022-05-04", "2022-06-08"
    ],
    "PBoC": [
        "2004-10-29", "2006-04-28", "2007-03-18", "2008-09-16", "2019-09-20",
        "2019-11-20", "2020-02-20", "2020-04-20", "2021-12-20", "2022-01-20"
    ],
    "CBR": [
        "2000-01-24", "2002-04-09", "2008-02-04", "2013-09-13", "2014-03-03",
        "2014-12-16", "2022-02-28", "2023-08-15", "2025-06-09", "2025-07-28"
    ]
}

# Regimes whose times ARE sourced from saved files / official conventions (Fed, ECB, BoJ, BoE, BoC, RBA, CBR).
# Only these may be checked for time_quality = "exact" or "approximate".
SOURCED_REGIMES = {"Fed", "ECB", "BoJ", "BoE", "BoC", "RBA", "CBR"}


@pytest.fixture(scope="module")
def events_df() -> pd.DataFrame:
    return pd.read_parquet(FINAL / "events.parquet")


@pytest.fixture(scope="module")
def policy_df() -> pd.DataFrame:
    return pd.read_csv(FINAL / "policy_decisions.csv", dtype={"decision_date": str})


@needs_data
class TestPriorityGroup1Timing:
    def test_zero_reacting_dates_precede_decision_date(self, events_df):
        """Mandatory audit fix: no reacting session may precede the decision date."""
        bad = events_df[events_df["reacting_session_date"].astype(str) < events_df["decision_date"].astype(str)]
        assert len(bad) == 0, f"Found {len(bad)} rows where reacting_session_date < decision_date!"

    def test_zero_reacting_sessions_precede_earliest_possible_announcement(self, events_df):
        """Every reacting session close must be strictly after window_start_utc."""
        sample = events_df.sample(min(1000, len(events_df)), random_state=42)
        for r in sample.itertuples():
            dates, _opens, closes = sessions(r.country)
            idx = int(np.where(dates == r.reacting_session_date)[0][0])
            close_utc = closes[idx]
            start_ts = _ts(r.window_start_utc)
            assert close_utc > start_ts, (
                f"{r.event_id} ({r.country}) reacting close {close_utc} precedes window start {start_ts}"
            )

    def test_analysis_ready_timing_flag_integrity(self, events_df):
        """analysis_ready_timing must equal 1 iff timing is clean (unambiguous, non-unknown, valid reaction, excluding BoE pre-2016)."""
        is_boe_pre2016 = (events_df["regime"] == "BoE") & (pd.to_datetime(events_df["decision_date"]).dt.date < dt.date(2016, 1, 1))
        clean_condition = (
            (events_df["timing_ambiguous"] == 0) &
            (events_df["time_quality"].isin(["exact", "approximate"])) &
            (~is_boe_pre2016) &
            (events_df["reacting_session_date"].notna()) &
            (events_df["reacting_session_date"].astype(str) >= events_df["decision_date"].astype(str))
        )
        assert (events_df["analysis_ready_timing"] == clean_condition.astype(int)).all()

    @pytest.mark.parametrize("regime", list(KNOWN_EVENTS))
    def test_known_event_dates_exist_and_sessions_are_ordered(self, policy_df, events_df, regime):
        """Known event dates must exist in the data; reacting session must not precede decision date."""
        for d_str in KNOWN_EVENTS[regime]:
            p_match = policy_df[(policy_df.regime == regime) & (policy_df.decision_date == d_str)]
            assert len(p_match) == 1, f"Missing decision for {regime} on {d_str}"

            ev_match = events_df[(events_df.regime == regime) & (events_df.decision_date == d_str)]
            assert len(ev_match) > 0, f"No event rows for {regime} on {d_str}"

            # Reacting session must not precede decision date
            assert (ev_match.reacting_session_date.astype(str) >= d_str).all(), (
                f"{regime} on {d_str} has reacting dates preceding decision date"
            )
            # Baseline must strictly precede reacting session
            assert (ev_match.baseline_date < ev_match.reacting_session_date).all(), (
                f"{regime} on {d_str} has baseline >= reacting date"
            )

    @pytest.mark.parametrize("regime", list(SOURCED_REGIMES))
    def test_sourced_regimes_home_market_is_analysis_ready(self, policy_df, events_df, regime):
        """For sourced regimes, unambiguous home-market rows must be >=90% analysis_ready_timing=1 (for BoE, evaluated 2016+)."""
        home_ev = events_df[
            (events_df.regime == regime) &
            (events_df.home_market == 1) &
            (events_df.timing_ambiguous == 0) &
            (events_df.time_quality.isin(["exact", "approximate"]))
        ]
        if regime == "BoE":
            home_ev = home_ev[pd.to_datetime(home_ev.decision_date).dt.date >= dt.date(2016, 1, 1)]
        if len(home_ev) == 0:
            return
        ready_share = home_ev["analysis_ready_timing"].mean()
        assert ready_share >= 0.90, (
            f"{regime} home-market unambiguous rows: only {ready_share:.1%} are analysis_ready_timing=1"
        )



# --- provenance of announcement times (ISS-029) -----------------------------------

def _manifest_urls() -> set[str]:
    import csv
    with open(ROOT / "data" / "raw" / "MANIFEST.csv", encoding="utf-8") as f:
        return {r["url_or_api"] for r in csv.DictReader(f)}


@needs_data
class TestTimeProvenance:
    def test_only_sourced_regimes_have_known_times(self, policy_df, events_df):
        """A time may be exact/approximate only for regimes whose times come from saved files."""
        for name, df in (("policy_decisions", policy_df), ("events", events_df)):
            known = df[df.time_quality.isin(["exact", "approximate"])]
            bad = sorted(set(known.regime) - SOURCED_REGIMES)
            assert not bad, f"{name}: unsourced regimes carry known times: {bad}"

    def test_cited_time_urls_were_downloaded(self, policy_df):
        """Every URL cited in time_source for a known time must be a file in MANIFEST.csv."""
        import re
        urls = _manifest_urls()
        known = policy_df[policy_df.time_quality.isin(["exact", "approximate"])]
        cited = {u for s in known.time_source.dropna() for u in re.findall(r"https?://[^\s)'\"]+", s)}
        missing = sorted(u for u in cited if u not in urls)
        assert not missing, f"time_source cites URLs that were never downloaded: {missing[:5]}"
