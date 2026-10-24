"""Phase B1 audit: index coverage vs exchange calendars, and policy-decision summary.

Writes outputs/pilot_summary.md (the B1 summary table) and prints it.
"""

from __future__ import annotations

from pathlib import Path

import exchange_calendars as xcals
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INTERIM_DIR = ROOT / "data" / "interim"
OUT_MD = ROOT / "outputs" / "pilot_summary.md"

# exchange_calendars has no NSE calendar; BSE (XBOM) shares NSE's trading holidays.
CALENDAR_MAP = {"US": "XNYS", "DE": "XETR", "IN": "XBOM", "JP": "XTKS"}


def audit_indices() -> pd.DataFrame:
    df = pd.read_parquet(INTERIM_DIR / "pilot_indices_daily.parquet")
    cals = {c: xcals.get_calendar(code, start="1999-01-01") for c, code in CALENDAR_MAP.items()}
    rows = []
    for index_id, g in df.groupby("index_id"):
        g = g.sort_values("date")
        cal = cals[g["country"].iloc[0]]
        first, last = g["date"].min(), g["date"].max()
        expected = {s.date() for s in cal.sessions_in_range(str(first), str(last))}
        actual = set(g["date"])
        rows.append({
            "series": index_id, "country": g["country"].iloc[0], "class": g["index_class"].iloc[0],
            "ticker": g["ticker"].iloc[0], "source": g["source"].iloc[0],
            "first_date": str(first), "last_date": str(last), "obs": len(g),
            "missing_days": len(expected - actual), "extra_days": len(actual - expected),
            "zero_return_days": int((g["ret_local"] == 0).sum()),
            "stale_days": int(g["stale_flag"].sum()), "exdiv_days": int(g["exdiv_flag"].sum()),
            "outliers_gt_10pct": int(g["outlier_flag"].sum()),
        })
    return pd.DataFrame(rows).sort_values(["country", "class"]).reset_index(drop=True)


def audit_policy() -> tuple[pd.DataFrame, pd.DataFrame]:
    pol = pd.read_csv(INTERIM_DIR / "pilot_policy_decisions.csv")
    counts = (pol.groupby(["regime", "event_type", "decision"]).size()
              .unstack("decision", fill_value=0).reset_index())
    timing = pol.groupby(["regime", "time_quality"]).size().unstack(fill_value=0).reset_index()
    return counts, timing


def to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def main() -> str:
    idx = audit_indices()
    counts, timing = audit_policy()
    md = "\n\n".join([
        "# Phase B1 pilot summary",
        "## Equity series vs exchange calendars",
        ("`missing_days`: exchange sessions with no observation; `extra_days`: observations on "
        "non-session days; `stale_days`: ETF days with zero volume."),
        to_md(idx),
        "## Policy decisions by regime and event type",
        to_md(counts),
        "## Announcement-time quality",
        to_md(timing),
    ]) + "\n"
    OUT_MD.parent.mkdir(exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(md)
    return md


if __name__ == "__main__":
    main()
