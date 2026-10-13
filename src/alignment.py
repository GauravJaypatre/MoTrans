"""Map each policy announcement to the sessions of each exchange (DECISION-013).

For an announcement window [start, end] (UTC) and an exchange:
  baseline session  = last session whose close is at or before `start`
  reacting session  = first session whose close is after `start`
  timing_ambiguous  = 1 if using `end` instead gives a different reacting session
  announce_in_session = 1 if `start` falls between that session's open and close

Session open/close times come from exchange_calendars (UTC, DST and early closes
included). The library applies today's trading hours to the whole history; older
changes in Xetra/NSE hours are not modelled (docs/issues.md ISS-014).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from functools import cache

import exchange_calendars as xcals
import numpy as np
import pandas as pd

# exchange_calendars has no NSE calendar; BSE (XBOM) has the same sessions and hours.
# EA = euro-area-wide series traded on Xetra. Single source of truth: src.collect_indices.
from src.collect_indices import CALENDARS

# Regime -> markets it is the home central bank of (ECB covers every euro-area market).
HOME_MARKETS = {"Fed": {"US"}, "ECB": {"DE", "FR", "IT", "ES", "EA"}, "RBI": {"IN"}, "BoJ": {"JP"},
                "BoE": {"GB"}, "PBoC": {"CN"}, "CBR": {"RU"}, "BoC": {"CA"}, "BCB": {"BR"},
                "Banxico": {"MX"}, "RBA": {"AU"}, "BoK": {"KR"}}


@dataclass(frozen=True)
class Alignment:
    baseline_date: dt.date | None
    reacting_date: dt.date | None
    announce_in_session: bool
    timing_ambiguous: bool


@cache
def sessions(country: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(session dates, open UTC, close UTC) as numpy arrays, sorted by session."""
    sched = xcals.get_calendar(CALENDARS[country], start="1999-01-01").schedule
    dates = np.array([d.date() for d in sched.index])
    opens = sched["open"].dt.tz_convert("UTC").to_numpy(dtype="datetime64[ns]")
    closes = sched["close"].dt.tz_convert("UTC").to_numpy(dtype="datetime64[ns]")
    return dates, opens, closes


def _ts(value: str | pd.Timestamp | dt.datetime) -> np.datetime64:
    return pd.Timestamp(value).tz_convert("UTC").tz_localize(None).to_datetime64() \
        if pd.Timestamp(value).tzinfo else pd.Timestamp(value).to_datetime64()


def align(window_start, window_end, country: str) -> Alignment:
    """Baseline and reacting sessions of `country` for an announcement window."""
    dates, opens, closes = sessions(country)
    start, end = _ts(window_start), _ts(window_end)
    i = int(np.searchsorted(closes, start, side="right"))  # first close strictly after start
    j = int(np.searchsorted(closes, end, side="right"))
    if i >= len(dates):
        return Alignment(dates[i - 1] if i else None, None, False, False)
    return Alignment(
        baseline_date=dates[i - 1] if i > 0 else None,
        reacting_date=dates[i],
        announce_in_session=bool(opens[i] <= start < closes[i]),
        timing_ambiguous=bool(j != i),
    )
