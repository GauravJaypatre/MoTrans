"""Phase C: harmonised daily panel -> data/final/panel_daily.parquet (+ quality report).

One row per (date x index). Controls are merged "as of" their `available_from` date, so a
row never uses information published after its date (no look-ahead):
  ret_usd             ret_local - change in ln(local currency per USD) since the previous row
  fx_lcu_per_usd, policy_rate, yield_1y   latest daily value on or before the date
  cpi, ind_prod       latest monthly value whose available_from <= date (DECISION-016)
  (a value older than MAX_AGE_DAYS is left empty: no stale carry-forward)
  vol_realized_20d    annualised std. dev. of the country's broad-index log returns over the
                      last 20 observations (EA uses the DAX)
  vol_implied         VIX for US rows; empty elsewhere (no free implied-vol history)
  valuation           empty: no free historical P/E or earnings-yield source (ISS-021)
Russia: rows are added for Moscow Exchange sessions with no index value between
24 Feb 2022 and 31 Mar 2022 (halt_flag = 1, prices empty); the first return after the
halt carries ret_spans_halt = 1.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from src import split_tag

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
BROAD_FOR_VOL = {"EA": "de_dax"}
HALT_WINDOW = (dt.date(2022, 2, 24), dt.date(2022, 3, 31))
RU_INVASION = dt.date(2022, 2, 24)


def russia_halt_rows(panel: pd.DataFrame) -> pd.DataFrame:
    import exchange_calendars as xcals
    sessions = [s.date() for s in xcals.get_calendar("XMOS", start="2021-01-01").sessions_in_range(*map(str, HALT_WINDOW))]
    extra = []
    for sid, g in panel[panel["country"] == "RU"].groupby("index_id"):
        have = set(g["date"])
        for d in sessions:
            if d not in have:
                extra.append({"date": d, "country": "RU", "index_id": sid, "index_class": g["index_class"].iloc[0],
                              "ticker": g["ticker"].iloc[0], "source": g["source"].iloc[0], "level_local": np.nan,
                              "ret_local": np.nan, "exdiv_flag": 0, "stale_flag": 0, "outlier_flag": 0, "halt_flag": 1})
    return pd.DataFrame(extra)


# Longest a value may be carried forward before it counts as missing (never fill stale data):
# daily market data 7 days (weekends/holidays), monthly macro data 62 days (one release cycle).
MAX_AGE_DAYS = {"fx_lcu_per_usd": 7, "policy_rate": 7, "yield_1y": 7, "cpi": 62, "ind_prod": 62}


def asof_merge(panel: pd.DataFrame, controls: pd.DataFrame, variable: str) -> pd.Series:
    c = controls[controls["variable"] == variable][["country", "available_from", "value"]].copy()
    c["available_from"] = pd.to_datetime(c["available_from"])
    c = c.sort_values("available_from")
    left = panel[["country", "date"]].copy()
    left["_d"] = pd.to_datetime(left["date"])
    left["_i"] = np.arange(len(left))
    merged = pd.merge_asof(left.sort_values("_d"), c, left_on="_d", right_on="available_from", by="country",
                           direction="backward", tolerance=pd.Timedelta(days=MAX_AGE_DAYS[variable]))
    return merged.sort_values("_i")["value"].to_numpy()


def build() -> pd.DataFrame:
    panel = pd.read_parquet(INTERIM / "indices_daily.parquet")
    panel["halt_flag"] = 0
    panel = pd.concat([panel, russia_halt_rows(panel)], ignore_index=True)
    panel = panel.sort_values(["index_id", "date"]).reset_index(drop=True)
    after_halt = panel.groupby("index_id")["halt_flag"].shift(1).fillna(0).astype(int)
    panel["ret_spans_halt"] = ((after_halt == 1) & panel["level_local"].notna()).astype("int8")
    # Returns across the halt: from the last pre-halt close to the first post-halt close.
    obs = panel[panel["level_local"].notna()].copy()
    obs["ret_local"] = obs.groupby("index_id")["level_local"].transform(lambda s: np.log(s / s.shift(1)))
    panel.loc[obs.index, "ret_local"] = obs["ret_local"]

    controls = pd.read_parquet(INTERIM / "controls_long.parquet")
    for var in ("fx_lcu_per_usd", "policy_rate", "yield_1y", "cpi", "ind_prod"):
        panel[var] = asof_merge(panel, controls, var)
    panel.loc[panel["country"] == "US", "fx_lcu_per_usd"] = 1.0

    fx_prev = panel[panel["level_local"].notna()].groupby("index_id")["fx_lcu_per_usd"].shift(1)
    panel["ret_usd"] = np.nan
    panel.loc[fx_prev.index, "ret_usd"] = (panel.loc[fx_prev.index, "ret_local"]
                                           - np.log(panel.loc[fx_prev.index, "fx_lcu_per_usd"] / fx_prev))

    broad = panel[panel["index_class"] == "broad"][["country", "date", "ret_local"]]
    vol = {}
    for country in panel["country"].unique():
        sid_country = "DE" if country == "EA" else country
        b = broad[broad["country"] == sid_country].sort_values("date")
        vol[country] = pd.Series((b["ret_local"].rolling(20, min_periods=15).std() * np.sqrt(252)).to_numpy(),
                                 index=b["date"].to_numpy())
    panel["vol_realized_20d"] = [vol[c].get(d, np.nan) for c, d in zip(panel["country"], panel["date"])]
    vix = controls[controls["variable"] == "vix"].set_index("date")["value"]
    panel["vol_implied"] = np.where(panel["country"] == "US", panel["date"].map(vix), np.nan)
    panel["valuation"] = np.nan

    panel["split_tag"] = panel["date"].map(split_tag)
    panel["russia_post_feb2022"] = ((panel["country"] == "RU") & (panel["date"] >= RU_INVASION)).astype("int8")
    cols = ["date", "country", "index_id", "index_class", "ticker", "source", "level_local", "ret_local", "ret_usd",
            "fx_lcu_per_usd", "policy_rate", "yield_1y", "vol_realized_20d", "vol_implied", "cpi", "ind_prod",
            "valuation", "split_tag", "russia_post_feb2022", "halt_flag", "ret_spans_halt", "exdiv_flag",
            "stale_flag", "outlier_flag"]
    for c in ("halt_flag", "exdiv_flag", "stale_flag", "outlier_flag"):
        panel[c] = panel[c].astype("int8")
    return panel[cols].sort_values(["country", "index_id", "date"]).reset_index(drop=True)


def quality_report(panel: pd.DataFrame) -> str:
    import exchange_calendars as xcals

    from src.collect_indices import CALENDARS
    obs = panel[panel["level_local"].notna()]
    lines = ["# Data quality report (Phase C)", "",
             (f"Panel: {len(panel):,} rows, {panel['index_id'].nunique()} series, {panel['country'].nunique()} markets, "
             f"{panel['date'].min()} to {panel['date'].max()}."), "",
             "## Series coverage vs exchange calendars", "",
             "| series | country | class | source | first | last | obs | missing sessions | outliers >10% | stale | halt rows |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for sid, g in panel.groupby("index_id"):
        o = g[g["level_local"].notna()]
        cal = xcals.get_calendar(CALENDARS[g["country"].iloc[0]], start="1999-01-01")
        expected = {s.date() for s in cal.sessions_in_range(str(o["date"].min()), str(o["date"].max()))}
        lines.append(f"| {sid} | {g['country'].iloc[0]} | {g['index_class'].iloc[0]} | {g['source'].iloc[0]} | "
                     f"{o['date'].min()} | {o['date'].max()} | {len(o):,} | {len(expected - set(o['date']))} | "
                     f"{int(o['outlier_flag'].sum())} | {int(o['stale_flag'].sum())} | {int(g['halt_flag'].sum())} |")
    lines += ["", "## Control coverage (share of observed rows with a value)", "",
              "| country | fx | policy rate | 1y yield | realized vol | CPI | ind. prod. |", "|---|---|---|---|---|---|---|"]
    for country, g in obs.groupby("country"):
        share = lambda c, g=g: f"{g[c].notna().mean():.0%}"
        lines.append(f"| {country} | {share('fx_lcu_per_usd')} | {share('policy_rate')} | {share('yield_1y')} | "
                     f"{share('vol_realized_20d')} | {share('cpi')} | {share('ind_prod')} |")
    lines += ["", "Valuation is empty for every market (no free historical source; ISS-021).",
              "Coverage gaps, substitutions and open questions: docs/issues.md.", ""]
    return "\n".join(lines)


def main() -> pd.DataFrame:
    FINAL.mkdir(parents=True, exist_ok=True)
    panel = build()
    panel.to_parquet(FINAL / "panel_daily.parquet", index=False)
    report = quality_report(panel)
    (ROOT / "docs" / "data_quality_report.md").write_text(report, encoding="utf-8")
    print(f"panel_daily: {len(panel):,} rows x {panel.shape[1]} columns, {panel['index_id'].nunique()} series")
    return panel


if __name__ == "__main__":
    main()
