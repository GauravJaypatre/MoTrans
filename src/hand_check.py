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
    "in_nifty50": "https://www.niftyindices.com/reports/historical-data",
    "jp_nikkei225": "https://finance.yahoo.com/quote/%5EN225/history",
}
MARKET = {"US": "United States: S&P 500", "DE": "Germany: DAX", "IN": "India: NIFTY 50",
          "JP": "Japan: Nikkei 225"}
BANK = {"fed": "Federal Reserve", "ecb": "European Central Bank", "rbi": "Reserve Bank of India",
        "boj": "Bank of Japan"}
CITY = {"America/New_York": "New York", "Europe/Berlin": "Frankfurt", "Asia/Kolkata": "India",
        "Asia/Tokyo": "Tokyo"}
WHY = {
    "fed_2022-03-16": "First hike of the 2022 cycle; exact time; clean same-day vs next-day case",
    "fed_2020-03-15": "Emergency cut announced on a Sunday evening",
    "fed_2008-10-08": "Coordinated emergency cut before the US open; India closed 9 Oct",
    "fed_2013-06-19": "Taper tantrum; release time unknown, so every market is flagged",
    "ecb_2022-07-21": "First ECB hike in 11 years; release at the new 14:15 time",
    "ecb_2011-04-07": "ECB hike under the old 13:45 release time",
    "rbi_2022-05-04": "Off-cycle RBI hike; time unknown; Japan closed for Golden Week",
    "rbi_2019-02-07": "Scheduled RBI cut; time unknown",
    "boj_2016-01-29": "Negative-rate decision; time from the minutes, during Tokyo trading",
    "boj_2024-03-19": "BoJ ends negative rates; time from the minutes",
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
    xlsx = ROOT / "docs" / "phase_b_hand_check.xlsx"
    if reviewed(xlsx):
        print(f"{xlsx.name} already holds reviewer sign-off; not overwritten "
              "(delete or rename it to regenerate a blank sheet).")
    else:
        write_xlsx(sheet, xlsx)
    print(f"Hand-check sheet: {sheet.event_id.nunique()} events, {len(sheet)} rows")
    return sheet


def reviewed(path: Path) -> bool:
    """True if any reviewer column (CHECK 1-4, Checked by) in the workbook is filled."""
    if not path.exists():
        return False
    from openpyxl import load_workbook
    ws = load_workbook(path, read_only=True)["Checklist"]
    return any(v not in (None, "") for row in ws.iter_rows(min_row=2, min_col=23, max_col=27, values_only=True)
               for v in row)


def write_xlsx(sheet: pd.DataFrame, path: Path) -> None:
    """Reviewer workbook: one row per (event x market), tick-box columns in yellow."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    font = Font(name="Arial", size=10)
    bold = Font(name="Arial", size=10, bold=True)
    head_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    link_font = Font(name="Arial", size=10, color="0563C1", underline="single")
    fill_head = PatternFill("solid", fgColor="1F3864")
    fill_check_head = PatternFill("solid", fgColor="7F6000")
    fill_check = PatternFill("solid", fgColor="FFF2CC")
    shades = [PatternFill("solid", fgColor="FFFFFF"), PatternFill("solid", fgColor="EEF3FA")]
    thin, thick = Side(style="thin", color="BFBFBF"), Side(style="medium", color="1F3864")
    wrap = Alignment(wrap_text=True, vertical="top")

    wb = Workbook()
    ws = wb.active
    ws.title = "Checklist"
    cols = [  # (header, width)
        ("#", 4), ("Event", 15), ("Central bank", 14), ("Decision", 9), ("Size (bp)", 7),
        ("Why this event", 30), ("Announced (local time)", 17), ("Time quality", 10),
        ("Window start (UTC)", 17), ("Market: index", 20), ("Baseline session\n(last close before news)", 15),
        ("Reacting session\n(first close after news)", 15), ("News during trading?", 9), ("Timing ambiguous?", 9),
        ("Baseline close", 12), ("Reacting close", 12), ("1-day return\n(pipeline)", 11),
        ("1-day return\n(recomputed)", 11), ("Match?", 8), ("5-day return\n(pipeline)", 11),
        ("Announcement source", 16), ("Price source", 16),
        ("CHECK 1\nDate & time right?", 12), ("CHECK 2\nSessions right?", 12),
        ("CHECK 3\nBaseline close right?", 12), ("CHECK 4\nReacting close right?", 12),
        ("Checked by", 12), ("Notes", 30),
    ]
    first_check = 23
    for c, (h, w) in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font, cell.alignment = head_font, Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.fill = fill_check_head if c >= first_check else fill_head
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 54

    yes_no = DataValidation(type="list", formula1='"Yes,No,Unsure"', allow_blank=True)
    ws.add_data_validation(yes_no)
    prev, shade = None, -1
    for n, r in enumerate(sheet.itertuples(), start=1):
        row = n + 1
        if r.event_id != prev:
            shade, prev = shade + 1, r.event_id
        bank = r.event_id.split("_")[0]
        city = CITY.get(r.timezone, r.timezone)
        when = (f"{r.announce_time_local} {city}" if isinstance(r.announce_time_local, str)
                else f"unknown (whole {city} day)")
        values = [n, r.event_id, BANK[bank], r.decision, r.size_bp, WHY.get(r.event_id, ""), when,
                  r.time_quality, r.window_start_utc.replace("T", " ").replace("Z", ""), MARKET[r.country],
                  r.baseline_date, r.reacting_session_date, "Yes" if r.announce_in_session else "No",
                  "Yes" if r.timing_ambiguous else "No", r.baseline_close, r.react_close, r.clr_1,
                  f"=LN(P{row}/O{row})", f'=IF(ABS(R{row}-Q{row})<0.00001,"Yes","NO")', r.clr_5,
                  r.source_url, r.price_source, "", "", "", "", "", ""]
        for c, v in enumerate(values, start=1):
            cell = ws.cell(row=row, column=c, value=v)
            cell.font, cell.alignment = font, wrap
            cell.fill = fill_check if c >= first_check else shades[shade % 2]
            cell.border = Border(left=thin, right=thin, bottom=thin, top=thick if values[1] != getattr(
                sheet.iloc[n - 2], "event_id", None) or n == 1 else thin)
        for c in (11, 12):
            ws.cell(row=row, column=c).number_format = "yyyy-mm-dd ddd"
        for c in (15, 16):
            ws.cell(row=row, column=c).number_format = "#,##0.00"
        for c in (17, 18, 20):
            ws.cell(row=row, column=c).number_format = "0.0000"
        for c, url in ((21, r.source_url), (22, r.price_source)):
            ws.cell(row=row, column=c).hyperlink = url
            ws.cell(row=row, column=c).value = "Open announcement" if c == 21 else "Open price history"
            ws.cell(row=row, column=c).font = link_font
        yes_no.add(f"{get_column_letter(first_check)}{row}:{get_column_letter(first_check + 3)}{row}")
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(sheet) + 1}"

    guide = wb.create_sheet("How to check", 0)
    lines = [
        ("Phase B hand-check: 10 policy announcements x 4 stock markets (40 rows)", bold),
        (("Gate before Phase C. Fill only the yellow columns on the Checklist sheet (Yes / No / Unsure, "
         "your name, notes). Do not edit any other cell."), font),
        ("", font),
        ("CHECK 1: Date & time right?", bold),
        (("Click 'Open announcement'. Is the announcement on this date? If a time is shown in 'Announced', "
         "does the source show the same time (Fed pages say 'For release at ...')? For RBI rows find the "
         "press release of that date on rbi.org.in; for ECB rows the date is enough (13:45 CET to June "
         "2022, 14:15 CET from July 2022). For BoJ rows the time is when the meeting ended (from the minutes)."), font),
        ("CHECK 2: Sessions right?", bold),
        (("Reacting session = the first trading day of that market whose CLOSE is after 'Window start "
         "(UTC)'. Baseline = that market's previous trading day. Watch for weekends and holidays. Market "
         "hours (local): NYSE 09:30-16:00 New York; Xetra 09:00-17:30 Frankfurt; NSE 09:15-15:30 India; "
         "Tokyo 09:00-15:00 (15:30 from 5 Nov 2024). Rows marked 'Timing ambiguous = Yes' have an unknown "
         "or wide time, so the earliest possible session is used on purpose; only check it follows that rule."), font),
        ("CHECK 3 and 4: Closing prices right?", bold),
        (("Click 'Open price history' and look up the closing value on the baseline and reacting dates. "
         "Differences under 0.05% are fine (data vendors round). The Match? column already confirms the "
         "1-day return equals ln(Reacting close / Baseline close)."), font),
        ("", font),
        (("If anything is wrong: answer No, write what you saw in Notes (with the source value), and tell "
         "the Data lead. Do not change the numbers here; the pipeline is fixed and the sheet regenerated."), font),
        ("", font),
        ("Example of a completed row (format only):", bold),
        (("CHECK 1 = Yes | CHECK 2 = Yes | CHECK 3 = Yes | CHECK 4 = No | Checked by = A. Reviewer | "
         "Notes = 'Yahoo reacting close differs from the sheet by 0.3% - value seen: <number>'"), font),
        ("", font),
        (("Generated by src/hand_check.py from data/interim/pilot_events.parquet. Rule: DECISIONS.md "
         "DECISION-013."), font),
    ]
    guide.column_dimensions["A"].width = 120
    for i, (text, f) in enumerate(lines, start=1):
        cell = guide.cell(row=i, column=1, value=text)
        cell.font, cell.alignment = f, Alignment(wrap_text=True, vertical="top")

    wb.calculation.fullCalcOnLoad = True  # formulas compute when the file is opened
    wb.save(path)


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
