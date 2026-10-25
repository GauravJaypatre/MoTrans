"""Official Source Announcement Timing and Date Verification (Priority Group 3).

Checks at least 10 specific policy decision dates per regime against official central bank
sources for:
1. Bank of England (BoE): Official MPC meeting calendar and Bank Rate decisions.
2. Bank of Canada (BoC): Official Fixed Announcement Date (FAD) schedule.
3. Reserve Bank of Australia (RBA): Official Board meeting calendar and MR-07-22 announcement rule.
4. Bank of Russia (CBR): Official Board Friday Key Rate meeting schedule.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"

needs_data = pytest.mark.skipif(not (FINAL / "policy_decisions.csv").exists(), reason="run pipeline first")

# 10 verified events per regime from official central-bank calendars
OFFICIAL_SAMPLES = {
    "BoE": [
        # (date, expected_time_local, expected_time_quality, expected_decision)
        # Pre-2016: assumed 12:00 convention, approximate quality; analysis_ready_timing = 0
        ("2000-01-13", "12:00", "approximate", "hike"),
        ("2000-02-10", "12:00", "approximate", "hike"),
        ("2001-02-08", "12:00", "approximate", "cut"),
        ("2003-07-10", "12:00", "approximate", "cut"),
        ("2007-07-05", "12:00", "approximate", "hike"),
        ("2008-11-06", "12:00", "approximate", "cut"),
        ("2009-03-05", "12:00", "approximate", "cut"),
        # 2016+: official MPC publication convention, exact quality (boe_mpc_official.html)
        ("2016-08-04", "12:00", "exact", "cut"),
        ("2020-03-11", "12:00", "exact", "cut"),
        ("2022-02-03", "12:00", "exact", "hike"),
        ("2023-08-03", "12:00", "exact", "hike"),
        ("2024-08-01", "12:00", "exact", "cut"),
    ],

    "BoC": [
        # Pre-2013: no verified official schedule file stating exact release time -> unknown
        ("2001-01-23", None, "unknown", "cut"),
        ("2001-04-17", None, "unknown", "cut"),
        ("2002-04-16", None, "unknown", "hike"),
        ("2007-07-10", None, "unknown", "hike"),
        ("2009-04-21", None, "unknown", "cut"),
        ("2010-06-01", None, "unknown", "hike"),
        # 2013-2023 FAD schedule: 10:00 ET (verified in data/raw/timing_sources/boc_schedule_2023.html)
        ("2015-01-21", "10:00", "exact", "cut"),
        ("2020-03-04", "10:00", "exact", "cut"),
        ("2022-03-02", "10:00", "exact", "hike"),
        ("2023-01-25", "10:00", "exact", "hike"),
        # 2024+ FAD schedule: 09:45 ET (verified in data/raw/timing_sources/boc_schedule_official.html)
        ("2024-06-05", "09:45", "exact", "cut"),
    ],
    "RBA": [
        # Pre-Feb 2008: morning after announcement (changes, 09:30 exact) or unannounced (holds, unknown)
        ("2000-02-02", "09:30", "exact", "hike"),
        ("2000-03-07", None, "unknown", "hold"),
        ("2001-02-07", "09:30", "exact", "cut"),
        ("2002-05-08", "09:30", "exact", "hike"),
        ("2003-11-05", "09:30", "exact", "hike"),
        ("2004-02-03", None, "unknown", "hold"),
        # Commencing Feb 2008 (MR-07-22): 14:30 Sydney time -> time_quality == "exact"
        ("2008-02-05", "14:30", "exact", "hike"),
        ("2008-03-04", "14:30", "exact", "hike"),
        ("2009-10-06", "14:30", "exact", "hike"),
        ("2011-11-01", "14:30", "exact", "cut"),
        ("2020-03-03", "14:30", "exact", "cut"),
        ("2022-05-03", "14:30", "exact", "hike"),
    ],
    "CBR": [
        # Pre-2013 refinancing rate era: unscheduled / unknown timing
        ("2000-01-24", None, "unknown", "cut"),
        ("2002-04-09", None, "unknown", "cut"),
        ("2008-02-04", None, "unknown", "hike"),
        # Key Rate era (2013-09-13 to 2022-02-11): 13:30 Moscow time
        ("2013-09-13", "13:30", "exact", "cut"),
        ("2014-03-03", "13:30", "approximate", "hike"),
        ("2014-04-25", "13:30", "exact", "hike"),
        ("2014-07-25", "13:30", "exact", "hike"),
        ("2014-12-11", "13:30", "exact", "hike"),
        ("2014-12-16", "01:00", "approximate", "hike"),
        ("2015-01-30", "13:30", "exact", "cut"),
        ("2015-03-13", "13:30", "exact", "cut"),
        ("2016-06-10", "13:30", "exact", "cut"),
        ("2017-03-24", "13:30", "exact", "cut"),
        ("2017-12-15", "13:30", "exact", "cut"),
    ]
}


@needs_data
class TestOfficialTimingSamples:
    @pytest.fixture(scope="module")
    def policy_df(self) -> pd.DataFrame:
        return pd.read_csv(FINAL / "policy_decisions.csv", dtype={"decision_date": str})

    @pytest.mark.parametrize("regime", ["BoE", "BoC", "RBA", "CBR"])
    def test_at_least_ten_events_match_official_calendar(self, policy_df, regime):
        samples = OFFICIAL_SAMPLES[regime]
        assert len(samples) >= 10, f"{regime} must test at least 10 events"
        
        reg_df = policy_df[policy_df["regime"] == regime].set_index("decision_date")
        
        for date_str, exp_time, exp_quality, exp_decision in samples:
            assert date_str in reg_df.index, f"{regime} missing official event {date_str}"
            row = reg_df.loc[date_str]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            
            # Check decision type if specified
            if exp_decision:
                assert row["decision"] == exp_decision, (
                    f"{regime} on {date_str} expected {exp_decision} but got {row['decision']}"
                )
            
            # Check time quality
            assert row["time_quality"] == exp_quality, (
                f"{regime} on {date_str} expected time_quality={exp_quality} but got {row['time_quality']}"
            )
            
            # Check local time
            if exp_time is None:
                assert pd.isna(row["announce_time_local"]) or row["announce_time_local"] == "", (
                    f"{regime} on {date_str} expected empty announce_time_local but got {row['announce_time_local']}"
                )
            else:
                assert row["announce_time_local"] == exp_time, (
                    f"{regime} on {date_str} expected {exp_time} but got {row['announce_time_local']}"
                )

    def test_rba_pre_2008_never_claims_1430(self, policy_df):
        """RBA 14:30 was established in Feb 2008 (MR-07-22); pre-2008 must never claim 14:30."""
        rba_pre = policy_df[(policy_df["regime"] == "RBA") & (policy_df["decision_date"] < "2008-02-01")]
        assert (rba_pre["announce_time_local"] != "14:30").all()
        # Holds before Feb 2008 were unannounced
        holds = rba_pre[rba_pre["decision"] == "hold"]
        assert (holds["event_type"] == "non_announcement_day").all()
        assert (holds["time_quality"] == "unknown").all()
        assert holds["announce_time_local"].isna().all()
        # Rate changes before Feb 2008 were announced at 09:30 the following day (MR-07-22)
        changes = rba_pre[rba_pre["decision"].isin(["hike", "cut"])]
        assert (changes["time_quality"] == "exact").all()
        assert (changes["announce_time_local"] == "09:30").all()

    def test_rba_2008_onward_is_1430_exact(self, policy_df):
        """RBA decisions from Feb 2008 onward must be exact 14:30 Sydney time."""
        rba_post = policy_df[(policy_df["regime"] == "RBA") & (policy_df["decision_date"] >= "2008-02-01")]
        assert (rba_post["time_quality"] == "exact").all()
        assert (rba_post["announce_time_local"] == "14:30").all()
