"""Timing rule (DECISION-013) on known announcements, for every pilot market.

These use only the exchange calendars, so they run without any downloaded data.
Each case: (announcement window in UTC) -> expected (baseline, reacting) per market.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from src.alignment import align
from src.event_windows import window_returns

D = dt.date
CASES = {
    # FOMC 16 Mar 2022, 14:00 EDT (exact). US reacts same day; others next day.
    "fed_2022_03_16": (("2022-03-16T18:00Z", "2022-03-16T18:00Z"), {
        "US": (D(2022, 3, 15), D(2022, 3, 16), False), "DE": (D(2022, 3, 16), D(2022, 3, 17), False),
        "IN": (D(2022, 3, 16), D(2022, 3, 17), False), "JP": (D(2022, 3, 16), D(2022, 3, 17), False)}),
    # FOMC 14 Dec 2022, 14:00 EST: winter time, still next day in Asia.
    "fed_2022_12_14": (("2022-12-14T19:00Z", "2022-12-14T19:00Z"), {
        "US": (D(2022, 12, 13), D(2022, 12, 14), False), "DE": (D(2022, 12, 14), D(2022, 12, 15), False),
        "IN": (D(2022, 12, 14), D(2022, 12, 15), False), "JP": (D(2022, 12, 14), D(2022, 12, 15), False)}),
    # Emergency cut 3 Mar 2020, 10:00 EST: inside the US and Xetra sessions.
    "fed_2020_03_03": (("2020-03-03T15:00Z", "2020-03-03T15:00Z"), {
        "US": (D(2020, 3, 2), D(2020, 3, 3), False), "DE": (D(2020, 3, 2), D(2020, 3, 3), False),
        "IN": (D(2020, 3, 3), D(2020, 3, 4), False), "JP": (D(2020, 3, 3), D(2020, 3, 4), False)}),
    # Sunday cut 15 Mar 2020, 17:00 EDT: everyone reacts Monday 16 Mar.
    "fed_2020_03_15": (("2020-03-15T21:00Z", "2020-03-15T21:00Z"), {
        "US": (D(2020, 3, 13), D(2020, 3, 16), False), "DE": (D(2020, 3, 13), D(2020, 3, 16), False),
        "IN": (D(2020, 3, 13), D(2020, 3, 16), False), "JP": (D(2020, 3, 13), D(2020, 3, 16), False)}),
    # Taper-tantrum FOMC 19 Jun 2013, time unknown -> whole ET day -> conservative reaction is next session after window end.
    "fed_2013_06_19": (("2013-06-19T04:00Z", "2013-06-20T03:59Z"), {
        "US": (D(2013, 6, 18), D(2013, 6, 20), True), "DE": (D(2013, 6, 18), D(2013, 6, 20), True),
        "IN": (D(2013, 6, 18), D(2013, 6, 20), True), "JP": (D(2013, 6, 18), D(2013, 6, 20), True)}),
    # BoJ 29 Jan 2016: meeting ended 12:31 JST, window to 13:31 JST - inside the Tokyo session.
    "boj_2016_01_29": (("2016-01-29T03:31Z", "2016-01-29T04:31Z"), {
        "US": (D(2016, 1, 28), D(2016, 1, 29), False), "DE": (D(2016, 1, 28), D(2016, 1, 29), False),
        "IN": (D(2016, 1, 28), D(2016, 1, 29), False), "JP": (D(2016, 1, 28), D(2016, 1, 29), False)}),
    # BoJ 18 Sep 2008 evening meeting (ended 15:42 JST, after the Tokyo close): Tokyo next day.
    "boj_2008_09_18": (("2008-09-18T06:42Z", "2008-09-18T07:42Z"), {
        "JP": (D(2008, 9, 18), D(2008, 9, 19), False), "US": (D(2008, 9, 17), D(2008, 9, 18), False)}),
    # ECB 21 Jul 2022, 14:15 CEST: Xetra and NYSE same day, Asia next day.
    "ecb_2022_07_21": (("2022-07-21T12:15Z", "2022-07-21T12:15Z"), {
        "US": (D(2022, 7, 20), D(2022, 7, 21), False), "DE": (D(2022, 7, 20), D(2022, 7, 21), False),
        "IN": (D(2022, 7, 21), D(2022, 7, 22), False), "JP": (D(2022, 7, 21), D(2022, 7, 22), False)}),
    # ECB 7 Apr 2011, 13:45 CEST.
    "ecb_2011_04_07": (("2011-04-07T11:45Z", "2011-04-07T11:45Z"), {
        "DE": (D(2011, 4, 6), D(2011, 4, 7), False), "JP": (D(2011, 4, 7), D(2011, 4, 8), False)}),
    # RBI 4 May 2022, whole-day IST window under conservative rule:
    # US reacts 4 May (closes 20:00Z > 18:29Z window end); IN/DE closed earlier so conservative reaction is 5 May.
    # 3 May was Indian holiday; Tokyo shut 3-5 May (Golden Week) -> 6 May.
    "rbi_2022_05_04": (("2022-05-03T18:30Z", "2022-05-04T18:29Z"), {
        "IN": (D(2022, 5, 2), D(2022, 5, 5), True), "JP": (D(2022, 5, 2), D(2022, 5, 6), False),
        "US": (D(2022, 5, 2), D(2022, 5, 4), True), "DE": (D(2022, 5, 3), D(2022, 5, 5), True)}),
    # RBI 4 May 2022 with exact official announcement time (14:00 IST / 08:30Z):
    # IN, DE, and US all react cleanly same day on 4 May 2022.
    "rbi_2022_05_04_exact": (("2022-05-04T08:30Z", "2022-05-04T08:30Z"), {
        "IN": (D(2022, 5, 2), D(2022, 5, 4), False), "JP": (D(2022, 5, 2), D(2022, 5, 6), False),
        "US": (D(2022, 5, 3), D(2022, 5, 4), False), "DE": (D(2022, 5, 3), D(2022, 5, 4), False)}),
}


@pytest.mark.parametrize("case", list(CASES))
def test_known_events(case):
    (start, end), expected = CASES[case]
    for country, (baseline, reacting, ambiguous) in expected.items():
        a = align(start, end, country)
        assert (a.baseline_date, a.reacting_date, a.timing_ambiguous) == (baseline, reacting, ambiguous), country


def test_tokyo_close_moved_to_1530_in_november_2024():
    # 15:15 JST: after the old 15:00 close, before the new 15:30 close (from 5 Nov 2024).
    assert align("2024-11-01T06:15Z", "2024-11-01T06:15Z", "JP").reacting_date == D(2024, 11, 5)
    a = align("2024-11-06T06:15Z", "2024-11-06T06:15Z", "JP")
    assert a.reacting_date == D(2024, 11, 6) and a.announce_in_session


def test_announcement_exactly_at_close_goes_to_next_session():
    # NYSE closes 20:00 UTC in winter; a release at the close cannot be traded that day.
    assert align("2022-12-14T21:00Z", "2022-12-14T21:00Z", "US").reacting_date == D(2022, 12, 15)


def test_window_returns_on_synthetic_series():
    dates = np.array([D(2024, 1, d) for d in (2, 3, 4, 5, 8, 9, 10, 11, 12)])
    logp = np.log(np.array([100, 101, 102, 103, 104, 105, 106, 107, 108], dtype=float))
    s = {"dates": dates, "logp": logp, "exdiv": np.zeros(9, int), "stale": np.zeros(9, int)}
    w = window_returns(s, baseline=D(2024, 1, 5), reacting=D(2024, 1, 6))  # Saturday -> next obs Monday
    assert w["react_obs_date"] == D(2024, 1, 8) and w["react_obs_gap"] == 1
    assert np.isclose(w["clr_1"], np.log(104 / 103)) and np.isclose(w["clr_3"], np.log(106 / 103))
    assert np.isnan(w["clr_20"])                                   # runs past the data
    assert np.isnan(w["clr_pre5"])                                 # only 3 days before the baseline
    w2 = window_returns(s, baseline=D(2024, 1, 9), reacting=D(2024, 1, 10))
    assert np.isclose(w2["clr_pre5"], np.log(105 / 100))           # 9 Jan vs five observations earlier


def test_reacting_session_never_precedes_earliest_possible_announcement():
    """Fail if any reacting session precedes the earliest possible announcement.
    
    Verifies that the 4,467 former timing defects (where Asian announcements on day T had
    reacting sessions on day T-1 in Western markets) are strictly rejected.
    """
    from src.alignment import _ts, sessions

    # Test cases representing the 5 regimes that previously had violations
    # (BoJ, BoK, PBoC, RBA, RBI) paired with Western markets (US, BR, CA, MX)
    cases = [
        # regime, decision_date, window_start_utc, window_end_utc
        ("BoJ", D(2007, 4, 27), "2007-04-26T15:00:00Z", "2007-04-27T14:59:00Z"),
        ("BoK", D(2008, 10, 9), "2008-10-08T15:00:00Z", "2008-10-09T14:59:00Z"),
        ("PBoC", D(2008, 9, 16), "2008-09-15T16:00:00Z", "2008-09-16T15:59:00Z"),
        ("RBA", D(2008, 10, 8), "2008-10-07T14:00:00Z", "2008-10-08T13:59:00Z"),
        ("RBI", D(2008, 10, 20), "2008-10-19T18:30:00Z", "2008-10-20T18:29:00Z"),
    ]

    western_countries = ["US", "BR", "CA", "MX"]

    for regime, dec_date, start_utc, end_utc in cases:
        for country in western_countries:
            a = align(start_utc, end_utc, country, time_quality="unknown")
            # 1. Reacting date must never precede the decision date
            assert a.reacting_date is not None
            assert a.reacting_date >= dec_date, (
                f"{regime} on {dec_date} got reacting date {a.reacting_date} in {country}, "
                f"which precedes the decision date!"
            )
            # 2. Reacting session close must be strictly after window_end (conservative rule)
            dates, _opens, closes = sessions(country)
            idx = int(np.where(dates == a.reacting_date)[0][0])
            react_close = closes[idx]
            end_ts = _ts(end_utc)
            assert react_close > end_ts, (
                f"{country} reacting session close {react_close} did not close after window end {end_ts}"
            )

