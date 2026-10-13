"""Phase B gate: a 10-event sheet for checking the timing rule by hand.

For each event and each pilot market's broad index: announcement time and window,
baseline and reacting sessions, the closing levels used, clr_1 and clr_5, and the source
links needed to verify them. Columns `checked_by`, `ok` and `notes` are for the reviewer.

Writes outputs/hand_check_10_events.csv and docs/phase_b_hand_check.md (tracked).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"

# Chosen to cover every regime, a weekend, intermeeting cuts, exact / approximate /
# unknown times, an after-close BoJ meeting and a Golden Week holiday.
EVENTS = [
    "fed_2022-03-16", "fed_2020-03-15", "fed_2008-10-08", "fed_2013-06-19",
    "ecb_2022-07-21", "ecb_2011-04-07",
    "rbi_2022-05-04", "rbi_2019-02-07",
    "boj_2016-01-29", "boj_2024-03-19",
]
BROAD = {"US": "us_sp500", "DE": "de_dax", "IN": "in_nifty50", "JP": "jp_nikkei225"}
PRICE_SOURCE = {
    "us_sp500": "https://finance.yahoo.com/quote/%5EGSPC/history",
    "de_dax": "https://finance.yahoo.com/quote/%5EGDAXI/history",
    "in_nifty50": "https://www.niftyindices.com/reports/historical-data (NIFTY 50)",
    "jp_nikkei225": "https://finance.yahoo.com/quote/%5EN225/history",
}


def main() -> pd.DataFrame:
    events = pd.read_parquet(INTERIM / "pilot_events.parquet")
    policy = pd.read_csv(INTERIM / "pilot_policy_decisions.csv", dtype={"decision_date": str})
    policy["event_id"] = policy["regime"].str.lower() + "_" + policy["decision_date"]
    panel = pd.read_parquet(INTERIM / "pilot_indices_daily.parquet")
    level = panel.set_index(["index_id", "date"])["level_local"]

    sheet = events[events.event_id.isin(EVENTS) & events.index_id.isin(BROAD.values())].copy()
    sheet = sheet.merge(policy[["event_id", "announce_time_local", "timezone", "time_source", "source_url"]],
                        on="event_id", how="left")
    sheet["baseline_close"] = [level.get((i, d), np.nan) for i, d in zip(sheet.index_id, sheet.baseline_obs_date)]
    sheet["react_close"] = [level.get((i, d), np.nan) for i, d in zip(sheet.index_id, sheet.react_obs_date)]
    sheet["price_source"] = sheet.index_id.map(PRICE_SOURCE)
    sheet["checked_by"], sheet["ok"], sheet["notes"] = "", "", ""
    sheet["order"] = sheet.event_id.map({e: i for i, e in enumerate(EVENTS)})
    cols = ["event_id", "decision", "size_bp", "announce_time_local", "timezone", "time_quality",
            "window_start_utc", "window_end_utc", "country", "index_id", "baseline_date", "reacting_session_date",
            "announce_in_session", "timing_ambiguous", "baseline_close", "react_close", "clr_1", "clr_5",
            "source_url", "price_source", "checked_by", "ok", "notes"]
    sheet = sheet.sort_values(["order", "country"])[cols].reset_index(drop=True)
    sheet[["clr_1", "clr_5"]] = sheet[["clr_1", "clr_5"]].round(5)

    (ROOT / "outputs").mkdir(exist_ok=True)
    sheet.to_csv(ROOT / "outputs" / "hand_check_10_events.csv", index=False)
    write_markdown(sheet)
    print(f"Hand-check sheet: {sheet.event_id.nunique()} events, {len(sheet)} rows")
    return sheet


def write_markdown(sheet: pd.DataFrame) -> None:
    lines = [
        "# Phase B hand-check: 10 events x 4 broad indices",
        "",
        "Gate before Phase C (spec, Phase B step 6): a person checks every row against the",
        "official announcement and the price history, then fills `checked_by` / `ok` / `notes`",
        "in `outputs/hand_check_10_events.csv` (regenerate with `python -m src.hand_check`).",
        "",
        "How to check a row:",
        "1. Open `source_url`: confirm the date, and the time where one is given.",
        ("2. Confirm `reacting_session_date` is the first session of that market that closes after "
        "`window_start_utc` (DECISION-013), and `baseline_date` the session before it."),
        ("3. Open `price_source`: confirm `baseline_close` and `react_close`; "
        "`clr_1` = ln(react_close / baseline_close)."),
        "",
    ]
    for eid, g in sheet.groupby("event_id", sort=False):
        first = g.iloc[0]
        when = f"{first.announce_time_local} {first.timezone}" if isinstance(first.announce_time_local, str) \
            else f"time unknown ({first.timezone} day)"
        lines += [f"## {eid}: {first.decision} {first.size_bp:g} bp, {when} [{first.time_quality}]",
                  f"Source: {first.source_url}", "",
                  ("| market | baseline | reacting | in session | ambiguous | baseline close | react close "
                  "| clr_1 | clr_5 | ok |"), "|---|---|---|---|---|---|---|---|---|---|"]
        for r in g.itertuples():
            lines.append(f"| {r.country} ({r.index_id}) | {r.baseline_date} | {r.reacting_session_date} | "
                         f"{r.announce_in_session} | {r.timing_ambiguous} | {r.baseline_close:,.2f} | "
                         f"{r.react_close:,.2f} | {r.clr_1:.4f} | {r.clr_5:.4f} | ☐ |")
        lines.append("")
    (ROOT / "docs" / "phase_b_hand_check.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
