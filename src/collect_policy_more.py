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


MEETINGS = {"BCB": (copom_meetings, COPOM_API), "Banxico": (banxico_meetings, BANXICO_LIST)}
TARGET_FROM = {"Banxico": dt.date(2008, 1, 21)}  # BIS WS_CBPOL MX note: target rate from this date


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
            if d < target_from:
                rows.append(row(regime, d, event_type="scheduled_meeting", scheduled=True, decision="unclassified",
                                rate_basis=f"No policy-rate target before {target_from} (BIS note)",
                                time_quality="unknown", time_source="Release time not stated by the source",
                                date_source=meetings[d], source_url=url))
                continue
            size = round((ch[-1][2] - ch[0][1]) * 100) if ch else 0
            rows.append(row(regime, d, event_type="scheduled_meeting", scheduled=True, decision=classify(size),
                            size_bp=size, new_rate_pct=ch[-1][2] if ch else rate.asof(d), rate_basis=basis,
                            time_quality="unknown", time_source="Release time not stated by the source",
                            date_source=meetings[d], source_url=url))
    else:
        unmatched = changes
        issues.append(f"{regime}: no complete official meeting list read; only rate changes (hikes/cuts) are "
                      "included, holds are missing.")
    for eff, old, new in unmatched:
        size = round((new - old) * 100)
        if regime in MEETINGS:
            issues.append(f"{regime}: rate change effective {eff} ({old}->{new}) not on a listed meeting; kept as "
                          "unscheduled_rate_change.")
        rows.append(row(regime, eff, event_type="rate_change" if regime not in MEETINGS else "unscheduled_rate_change",
                        scheduled=regime not in MEETINGS and regime != "PBoC", decision=classify(size), size_bp=size,
                        new_rate_pct=new, rate_basis=basis, time_quality="unknown",
                        time_source="Not available from rate series",
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
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(unique)
    (INTERIM / "policy_more_issues.txt").write_text("\n".join(issues) + "\n", encoding="utf-8")
    print(f"Saved {len(unique)} rows to {OUT_CSV}; {len(issues)} issues logged.")
    return issues


if __name__ == "__main__":
    main()
