"""Event-window returns for every (policy event x pilot equity series).

clr_h   = ln(P at the h-th index observation from the reacting session) - ln(P at baseline)
clr_pre5 = ln(P at baseline) - ln(P 5 observations earlier)   (placebo / pre-trend window)

Baseline and reacting sessions come from src.alignment (DECISION-013). Prices are taken
from the index's own observations: baseline = last observation on or before the baseline
session; reaction starts at the first observation on or after the reacting session
(`react_obs_gap` = 1 when that observation is a later day, i.e. the index has no value on
the reacting session). Horizons running past the last observation are left empty.

Output: data/interim/pilot_events.parquet (+ .csv). Shock columns are filled in Phase D.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from src import split_tag
from src.alignment import HOME_MARKETS, align

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
HORIZONS = (1, 3, 5, 20, 60)
PRE = 5

KEEP = ["regime", "decision_date", "event_type", "scheduled", "decision", "size_bp", "new_rate_pct",
        "time_quality", "announce_ts_utc", "window_start_utc", "window_end_utc"]


def series_arrays(panel: pd.DataFrame) -> dict[str, dict]:
    out = {}
    for sid, g in panel.groupby("index_id"):
        g = g.sort_values("date")
        out[sid] = {
            "country": g["country"].iloc[0], "index_class": g["index_class"].iloc[0],
            "dates": np.array(g["date"].tolist()), "logp": np.log(g["level_local"].to_numpy()),
            "exdiv": g["exdiv_flag"].to_numpy(), "stale": g["stale_flag"].to_numpy(),
        }
    return out


def window_returns(s: dict, baseline: dt.date, reacting: dt.date) -> dict | None:
    dates, logp = s["dates"], s["logp"]
    b = int(np.searchsorted(dates, baseline, side="right")) - 1   # last obs <= baseline session
    r = int(np.searchsorted(dates, reacting, side="left"))        # first obs >= reacting session
    if b < 0 or r >= len(dates) or r <= b:
        return None
    out = {
        "baseline_obs_date": dates[b], "react_obs_date": dates[r],
        "react_obs_gap": int(dates[r] != reacting),
        "clr_pre5": logp[b] - logp[b - PRE] if b - PRE >= 0 else np.nan,
        "stale_on_react": int(s["stale"][r]),
        "exdiv_in_clr5": int(s["exdiv"][r:r + 5].any()),
    }
    for h in HORIZONS:
        k = r + h - 1
        out[f"clr_{h}"] = logp[k] - logp[b] if k < len(dates) else np.nan
    return out


def build(policy: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    series = series_arrays(panel)
    rows = []
    for ev in policy.itertuples(index=False):
        ev = ev._asdict()
        event_id = f"{ev['regime'].lower()}_{ev['decision_date']}"
        cache: dict[str, object] = {}
        for sid, s in series.items():
            country = s["country"]
            if country not in cache:
                cache[country] = align(ev["window_start_utc"], ev["window_end_utc"], country)
            a = cache[country]
            if a.baseline_date is None or a.reacting_date is None:
                continue
            w = window_returns(s, a.baseline_date, a.reacting_date)
            if w is None:
                continue
            rows.append({
                "event_id": event_id, **{k: ev[k] for k in KEEP},
                "country": country, "index_id": sid, "index_class": s["index_class"],
                "home_market": int(country in HOME_MARKETS[ev["regime"]]),
                "baseline_date": a.baseline_date, "reacting_session_date": a.reacting_date,
                "announce_in_session": int(a.announce_in_session),
                "timing_ambiguous": int(a.timing_ambiguous), **w,
                "shock_std": np.nan, "shock_grade": "",
                "split_tag": split_tag(dt.date.fromisoformat(ev["decision_date"])),
            })
    return pd.DataFrame(rows)


def main() -> pd.DataFrame:
    """Phase B pilot table (4 regimes x 13 series) -> data/interim/pilot_events.parquet."""
    policy = pd.read_csv(INTERIM / "pilot_policy_decisions.csv", dtype={"decision_date": str})
    panel = pd.read_parquet(INTERIM / "pilot_indices_daily.parquet")
    events = build(policy, panel)
    events.to_parquet(INTERIM / "pilot_events.parquet", index=False)
    events.to_csv(INTERIM / "pilot_events.csv", index=False)
    print(f"{events['event_id'].nunique()} events x {events['index_id'].nunique()} series = "
          f"{len(events)} rows -> {INTERIM / 'pilot_events.parquet'}")
    return events


def policy_all() -> pd.DataFrame:
    """All 12 regimes: pilot decisions + Phase C regimes."""
    parts = [pd.read_csv(INTERIM / f, dtype={"decision_date": str})
             for f in ("pilot_policy_decisions.csv", "policy_decisions_more.csv")]
    return pd.concat(parts, ignore_index=True).sort_values(["regime", "decision_date"]).reset_index(drop=True)


def main_full() -> pd.DataFrame:
    """Phase C: every regime x every series -> data/final/events.parquet."""
    final = ROOT / "data" / "final"
    final.mkdir(parents=True, exist_ok=True)
    policy = policy_all()
    policy.to_csv(final / "policy_decisions.csv", index=False)
    panel = pd.read_parquet(final / "panel_daily.parquet")
    panel = panel[panel["level_local"].notna()]  # halt placeholders carry no price
    events = build(policy, panel)
    events.to_parquet(final / "events.parquet", index=False)
    print(f"events: {events['event_id'].nunique()} events x {events['index_id'].nunique()} series = "
          f"{len(events):,} rows -> {final / 'events.parquet'}")
    return events


if __name__ == "__main__":
    main()
