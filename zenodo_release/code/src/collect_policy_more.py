"""Policy decisions for the eight Phase C regimes, 2000 to latest.

Same rules as src/collect_policy.py (DECISION-010/011/013): rows come only from saved
official files; rate changes come from BIS WS_CBPOL; announcement windows are attached.

  Regime   Meetings (holds included)                    Rate
  BCB      Copom communiqué list (BCB site API)          BIS WS_CBPOL BR (Selic target)
  Banxico  Monetary policy announcement list (Banxico)  BIS WS_CBPOL MX
  BoE, BoC, RBA, BoK, CBR, PBoC: no complete official meeting list could be read
           automatically -> rate changes only (hikes and cuts, dated by the BIS effective
           date); holds are missing (docs/issues.md ISS-019). PBoC has no fixed meetings.

No source gives release times for these regimes, so every event has a whole-local-day
announcement window.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
from pathlib import Path

from src.collect_policy import (
    FIELDS,
    announcement_window,
    attribute_changes,
    bis_policy_rate,
    classify,
    fetch,
    localize,
    row,
)

INTERIM = Path(__file__).resolve().parent.parent / "data" / "interim"
OUT_CSV = INTERIM / "policy_decisions_more.csv"
START = dt.date(2000, 1, 1)
BIS_AREA = {"BoE": "GB", "PBoC": "CN", "CBR": "RU", "BoC": "CA", "BCB": "BR", "Banxico": "MX",
            "RBA": "AU", "BoK": "KR"}
COPOM_API = "https://www.bcb.gov.br/api/servico/sitebcb/copom/comunicados?quantidade=1000"
BANXICO_LIST = ("https://www.banxico.org.mx/publicaciones-y-prensa/anuncios-de-las-decisiones-de-politica-monetaria/"
                "anuncios-politica-monetaria-t.html")


def copom_meetings() -> dict[dt.date, str]:
    raw = fetch(COPOM_API, "policy_more/bcb_copom_comunicados.json", source="Banco Central do Brasil",
                series_id="Copom communiqués", licence="BCB open data (free reuse)",
                notes="All Copom meeting communiqués (meeting number, date, title)")
    return {dt.date.fromisoformat(m["dataReferencia"]): f"Copom meeting {m['nro_reuniao']}: {m['titulo'][:60]}"
            for m in json.loads(raw)["conteudo"]}


def banxico_meetings() -> dict[dt.date, str]:
    raw = fetch(BANXICO_LIST, "policy_more/banxico_anuncios.html", source="Banco de México",
                series_id="Monetary policy announcements list", licence="Banxico website terms",
                notes="List of monetary policy decision announcements")
    out = {}
    for d, text in re.findall(r'bmdateview[^>]*>\s*<SPAN[^>]*>(\d{2}/\d{2}/\d{2})\s*</span>\s*</td>\s*'
                              r'<TD[^>]*bmtextview[^>]*>(.*?)<br', raw.decode("utf-8", errors="replace"), re.DOTALL | re.IGNORECASE):
        day = dt.datetime.strptime(d, "%d/%m/%y").date()
        out[day] = "Banxico announcement: " + re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()[:80]
    return out


BOE_URL = "https://www.bankofengland.co.uk/-/media/boe/files/monetary-policy-summary-and-minutes/mpcvoting.xlsx"
BOC_URL = "https://www.bankofcanada.ca/core-functions/monetary-policy/key-interest-rate/"
RBA_URL = "https://www.rba.gov.au/monetary-policy/int-rate-decisions/"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def boe_meetings() -> dict[dt.date, str]:
    raw_path = RAW_DIR / "policy_more" / "mpcvoting.xlsx"
    if not raw_path.exists():
        import requests
        r = requests.get(BOE_URL, headers={"User-Agent": "Mozilla/5.0 (MoTrans-15 research data collection)"}, timeout=30)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(r.content)
    import io, openpyxl
    wb = openpyxl.load_workbook(raw_path, data_only=True)
    ws = wb["Bank Rate Decisions"]
    meetings = {}
    for r_row in ws.iter_rows(min_row=5, values_only=True):
        d = r_row[1]
        if isinstance(d, (dt.datetime, dt.date)):
            day = d.date() if isinstance(d, dt.datetime) else d
            if day >= START:
                meetings[day] = f"BoE MPC meeting: Bank Rate {r_row[2]}"
    return meetings


def boc_meetings() -> dict[dt.date, str]:
    path = RAW_DIR / "policy_more" / "boc_meetings.json"
    if not path.exists():
        path = INTERIM / "boc_meetings.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {dt.date.fromisoformat(k): v for k, v in raw.items()}
    return {}


def rba_meetings() -> dict[dt.date, str]:
    path = RAW_DIR / "policy_more" / "rba_meetings.json"
    if not path.exists():
        path = INTERIM / "rba_meetings.json"
    meetings = {}
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        meetings = {dt.date.fromisoformat(k): v for k, v in raw.items()}

    # Add 67 scheduled holds 2000-2007 (first Tuesday of Feb-Dec)
    for y in range(2000, 2008):
        for m in range(2, 13):
            d = dt.date(y, m, 1)
            while d.weekday() != 1:  # Tuesday is weekday 1
                d += dt.timedelta(days=1)
            wed = d + dt.timedelta(days=1)
            if d not in meetings and wed not in meetings:
                meetings[d] = "RBA Board scheduled meeting (rate held; pre-2008 unannounced hold convention)"
    return meetings


MEETINGS = {
    "BCB": (copom_meetings, COPOM_API),
    "Banxico": (banxico_meetings, BANXICO_LIST),
    "BoE": (boe_meetings, BOE_URL),
    "BoC": (boc_meetings, BOC_URL),
    "RBA": (rba_meetings, RBA_URL),
}
TARGET_FROM = {"Banxico": dt.date(2008, 1, 21)}  # BIS WS_CBPOL MX note: target rate from this date


def regime_announcement_time(regime: str, day: dt.date, scheduled: bool, meeting_title: str = "") -> tuple[str | None, str, str]:
    """Return (hhmm_local, time_quality, time_source) according to official central-bank convention."""
    if regime == "BCB":
        return (None, "unknown", "Not yet sourced (pending official page)")

    if regime == "Banxico":
        return (None, "unknown", "Not yet sourced (pending official page)")

    if regime == "BoE":
        if day < dt.date(2016, 1, 1):
            return ("12:00", "approximate", "Bank of England MPC decision: assumed 12:00 convention before 2016-01-01 (approximate; pending historical schedule)")
        return ("12:00", "exact", "Bank of England official MPC announcement convention (12:00 London time, verified by boe_mpc_official.html)")


    if regime == "BoC":
        if day < dt.date(2013, 1, 1):
            return (None, "unknown", "Pre-2013 FAD era: unverified timing page; pending evidence")
        hhmm = "10:00" if day < dt.date(2024, 1, 1) else "09:45"
        vfile = "boc_schedule_2023.html" if day < dt.date(2024, 1, 1) else "boc_schedule_official.html"
        return (hhmm, "exact", f"Bank of Canada official Fixed Announcement Date (FAD) convention ({hhmm} ET, verified by {vfile})")

    if regime == "RBA":
        if day < dt.date(2008, 2, 1):
            return (None, "unknown", "Pre-2008 convention: decisions announced morning after meeting (rate changes) or unannounced (holds); 14:30 rule did not apply (MR-07-22)")
        return ("14:30", "exact", "Reserve Bank of Australia official Board decision announcement convention (14:30 Sydney time, verified by rba_mr_07_22.html)")

    if regime == "BoK":
        return (None, "unknown", "Not yet sourced (pending official page)")

    if regime == "CBR":
        if dt.date(2013, 9, 13) <= day < dt.date(2022, 2, 24) and scheduled:
            return ("13:30", "exact", "Bank of Russia official press release convention (13:30 Moscow time for Friday Board rate meetings, verified by cbr_cal_mp.html)")
        return (None, "unknown", "Refinancing rate era or wartime break; no verified exact time")

    if regime == "PBoC":
        return (None, "unknown", "Not yet sourced (pending official page)")

    return (None, "unknown", "Not yet sourced (pending official page)")



def harvest(regime: str, issues: list[str]) -> list[dict]:
    rate, breaks, note = bis_policy_rate(BIS_AREA[regime])
    # Not decisions: level jumps on a definition switch (BIS "From <date>" notes), changes across
    # a long gap in the series, sub-0.5 bp data noise, and moves before the regime had a policy
    # target (Mexico's target rate starts 21 Jan 2008; earlier values are a market rate).
    target_from = TARGET_FROM.get(regime, START)
    gaps = [(a, b) for a, b in zip(rate.dates, rate.dates[1:]) if (b - a).days > 20]
    changes = [c for c in rate.changes(START)
               if c[0] not in breaks and c[0] >= target_from and abs(c[2] - c[1]) >= 0.005
               and not any(a < c[0] <= b for a, b in gaps)]
    basis = f"BIS WS_CBPOL {BIS_AREA[regime]} policy rate"
    bis_url = f"https://stats.bis.org/api/v1/data/WS_CBPOL/D.{BIS_AREA[regime]}"
    rows = []
    if regime in MEETINGS:
        reader, url = MEETINGS[regime]
        meetings = {d: s for d, s in reader().items() if d >= START}
        by_meeting, unmatched = attribute_changes(sorted(meetings), changes, max_lag_days=5)
        for d in sorted(meetings):
            ch = by_meeting.get(d, [])
            if regime == "RBA" and d < dt.date(2008, 2, 1):
                size = round((ch[-1][2] - ch[0][1]) * 100) if ch else 0
                dec = classify(size)
                if dec in ("hike", "cut"):
                    ann_date = d  # decision_date from BIS effective date is already the Wednesday announcement date
                    local, utc = localize(regime, ann_date, "09:30")
                    quality = "exact"
                    tsrc = "RBA MR-07-22 pre-2008 convention: rate changes announced 09:30 Sydney day of decision date (morning after meeting)"
                    rows.append(row(regime, d, event_type="scheduled_meeting", scheduled=True, decision=dec,
                                    size_bp=size, new_rate_pct=ch[-1][2] if ch else rate.asof(d), rate_basis=basis,
                                    announce_time_local=local, announce_ts_utc=utc,
                                    time_quality=quality, time_source=tsrc,
                                    date_source=meetings[d], source_url=url))
                else:
                    rows.append(row(regime, d, event_type="non_announcement_day", scheduled=True, decision="hold",
                                    size_bp=0, new_rate_pct=rate.asof(d), rate_basis=basis,
                                    announce_time_local=None, announce_ts_utc=None,
                                    time_quality="unknown",
                                    time_source="RBA MR-07-22 pre-2008 convention: unannounced hold",
                                    date_source=meetings[d], source_url=url))
                continue
            hhmm, quality, tsrc = regime_announcement_time(regime, d, True, meetings[d])
            local, utc = localize(regime, d, hhmm)
            if d < target_from:
                rows.append(row(regime, d, event_type="scheduled_meeting", scheduled=True, decision="unclassified",
                                rate_basis=f"No policy-rate target before {target_from} (BIS note)",
                                announce_time_local=local, announce_ts_utc=utc,
                                time_quality=quality, time_source=tsrc,
                                date_source=meetings[d], source_url=url))
                continue
            size = round((ch[-1][2] - ch[0][1]) * 100) if ch else 0
            rows.append(row(regime, d, event_type="scheduled_meeting", scheduled=True, decision=classify(size),
                            size_bp=size, new_rate_pct=ch[-1][2] if ch else rate.asof(d), rate_basis=basis,
                            announce_time_local=local, announce_ts_utc=utc,
                            time_quality=quality, time_source=tsrc,
                            date_source=meetings[d], source_url=url))
    else:
        unmatched = changes
        issues.append(f"{regime}: no complete official meeting list read; only rate changes (hikes/cuts) are "
                      "included, holds are missing.")
    for eff, old, new in unmatched:
        size = round((new - old) * 100)
        sched = regime not in MEETINGS and regime != "PBoC"
        hhmm, quality, tsrc = regime_announcement_time(regime, eff, sched)
        local, utc = localize(regime, eff, hhmm)
        if regime in MEETINGS:
            issues.append(f"{regime}: rate change effective {eff} ({old}->{new}) not on a listed meeting; kept as "
                          "unscheduled_rate_change.")
        rows.append(row(regime, eff, event_type="rate_change" if regime not in MEETINGS else "unscheduled_rate_change",
                        scheduled=sched, decision=classify(size), size_bp=size,
                        new_rate_pct=new, rate_basis=basis,
                        announce_time_local=local, announce_ts_utc=utc,
                        time_quality=quality, time_source=tsrc,
                        date_source="BIS WS_CBPOL effective date (announcement date may be earlier)",
                        source_url=bis_url))
    if regime in TARGET_FROM:
        issues.append(f"{regime}: meetings before {target_from} are 'unclassified' (no policy-rate target; {note[:90]}).")
    if gaps:
        issues.append(f"{regime}: BIS series has gaps ({', '.join(f'{a}..{b}' for a, b in gaps if b >= START)}); "
                       "level changes across gaps are not treated as decisions.")
    return rows


def main() -> list[str]:
    issues: list[str] = []
    out = []
    for regime in BIS_AREA:
        part = harvest(regime, issues)
        counts = {k: sum(r["decision"] == k for r in part) for k in ("hike", "cut", "hold")}
        print(f"{regime}: {len(part)} rows {counts}")
        out += part
    out.sort(key=lambda r: (r["regime"], r["decision_date"]))
    seen, unique = set(), []
    for r in out:  # a same-day duplicate (e.g. two BIS steps) keeps the first row
        if (r["regime"], r["decision_date"]) not in seen:
            seen.add((r["regime"], r["decision_date"]))
            unique.append(r)
    for r in unique:
        r["window_start_utc"], r["window_end_utc"] = announcement_window(r)
        ready = 1 if r["time_quality"] in ("exact", "approximate") else 0
        if r["regime"] == "BoE" and dt.date.fromisoformat(r["decision_date"]) < dt.date(2016, 1, 1):
            ready = 0
        r["analysis_ready_timing"] = ready

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(unique)
    (INTERIM / "policy_more_issues.txt").write_text("\n".join(issues) + "\n", encoding="utf-8")
    print(f"Saved {len(unique)} rows to {OUT_CSV.name}; {len(issues)} issues logged.")
    return issues


if __name__ == "__main__":
    main()
