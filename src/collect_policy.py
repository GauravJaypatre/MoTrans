"""Collect pilot policy decisions (Fed, ECB, RBI, BoJ), 2000 to latest.

Two stages, so the table can always be rebuilt from data/raw/ alone:

1. fetch: official documents are downloaded once through src.download.save_raw_file()
   (write-once, logged in MANIFEST.csv). A file already in data/raw/ is reused.
2. parse: every row is derived from those saved files. No dates, rates or times are
   typed into this module.

Sources per regime
------------------
Fed  meetings/statements : fomchistorical{YYYY}.htm (2000-2020), fomccalendars.htm (2021+)
     rate                : openmarket.htm (target / target-range upper bound)
     time                : "For release at ..." line on each statement page
ECB  meetings            : EA-MPD press-release sheet (to its last update) + ECB
                           monetary-policy-statement year lists (press conferences)
     rates               : ECB Data Portal MRO (fixed rate / minimum bid rate), DFR, MLF
     time                : EA-MPD notes (release 13:45 CET to June 2022, 14:15 from July 2022)
RBI  meetings            : RBI monetary policy archive (one page per financial year)
     rate                : BIS WS_CBPOL daily policy rate (bank rate before 3 Apr 2001)
     time                : not published on the source pages -> unknown
BoJ  meetings            : BoJ statement lists + minutes lists
     rate                : BIS WS_CBPOL daily policy rate
     time                : meeting end time from the minutes (release follows the meeting)

Rate changes that cannot be attributed to a listed meeting are kept as
"unscheduled_rate_change" rows dated by the rate's effective date and logged in
docs/issues.md; they are never dropped or re-dated by hand.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
import time
import zipfile
import zoneinfo
from collections.abc import Iterable
from pathlib import Path

import bs4
import requests

from src.download import RAW_DIR, save_raw_file

INTERIM_DIR = Path(__file__).resolve().parent.parent / "data" / "interim"
OUT_CSV = INTERIM_DIR / "pilot_policy_decisions.csv"
START = dt.date(2000, 1, 1)
TODAY = dt.date.today()

TZ = {
    "Fed": zoneinfo.ZoneInfo("America/New_York"),
    "ECB": zoneinfo.ZoneInfo("Europe/Berlin"),
    "RBI": zoneinfo.ZoneInfo("Asia/Kolkata"),
    "BoJ": zoneinfo.ZoneInfo("Asia/Tokyo"),
    # Phase C regimes (collected in src/collect_policy_more.py)
    "BoE": zoneinfo.ZoneInfo("Europe/London"),
    "PBoC": zoneinfo.ZoneInfo("Asia/Shanghai"),
    "CBR": zoneinfo.ZoneInfo("Europe/Moscow"),
    "BoC": zoneinfo.ZoneInfo("America/Toronto"),
    "BCB": zoneinfo.ZoneInfo("America/Sao_Paulo"),
    "Banxico": zoneinfo.ZoneInfo("America/Mexico_City"),
    "RBA": zoneinfo.ZoneInfo("Australia/Sydney"),
    "BoK": zoneinfo.ZoneInfo("Asia/Seoul"),
}

FIELDS = [
    "regime", "decision_date", "event_type", "scheduled", "decision", "size_bp",
    "new_rate_pct", "rate_basis", "rate_mro", "rate_dfr", "rate_mlf",
    "announce_time_local", "timezone", "announce_ts_utc", "time_quality", "time_source",
    "window_start_utc", "window_end_utc", "date_source", "source_url",
]

# Announcement window per time quality (DECISION-013). B2 measures returns from the last
# close before window_start and reacts from the first session closing after window_start.
APPROX_WINDOW = {  # (minutes before, minutes after) the recorded approximate time
    "BoJ": (0, 60),    # minutes give the meeting END; the release follows it
    "Fed": (-15, 15),  # assumed 14:15 ET schedule (pre-Apr 2011)
}


def announcement_window(r: dict) -> tuple[str, str]:
    """[earliest, latest] possible UTC release time for an event row."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    if r["time_quality"] in ("exact", "approximate") and r["announce_ts_utc"]:
        t = dt.datetime.strptime(r["announce_ts_utc"], fmt).replace(tzinfo=dt.UTC)
        before, after = APPROX_WINDOW.get(r["regime"], (0, 0)) if r["time_quality"] == "approximate" else (0, 0)
        return ((t + dt.timedelta(minutes=before)).strftime(fmt), (t + dt.timedelta(minutes=after)).strftime(fmt))
    # Unknown time: any moment of the announcement date in the central bank's local time.
    day = dt.date.fromisoformat(r["decision_date"])
    start = dt.datetime(day.year, day.month, day.day, tzinfo=TZ[r["regime"]])
    end = start + dt.timedelta(days=1) - dt.timedelta(minutes=1)
    return start.astimezone(dt.UTC).strftime(fmt), end.astimezone(dt.UTC).strftime(fmt)

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "Mozilla/5.0 (MoTrans-15 research data collection)"
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


# =============================================================================
# Fetch helpers
# =============================================================================

def fetch(url: str, filename: str, *, source: str, series_id: str, licence: str,
          notes: str = "", data: dict | None = None, session: requests.Session = SESSION,
          missing_ok: bool = False) -> bytes | None:
    """Return the raw file, downloading and registering it first if needed."""
    path = RAW_DIR / filename
    if path.exists():
        return path.read_bytes()
    resp = session.post(url, data=data, timeout=60) if data else session.get(url, timeout=60)
    time.sleep(0.4)  # be polite to official servers
    if resp.status_code == 404 and missing_ok:
        return None
    resp.raise_for_status()
    save_raw_file(resp.content, filename, source=source, url_or_api=url,
                  series_id=series_id, licence=licence, notes=notes)
    return resp.content


def html_text(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def ymd(s: str) -> dt.date:
    return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def parse_month_day_year(text: str) -> dt.date | None:
    """Parse 'Jan 27, 2009' / 'Sept. 21, 2016' / '21 July 2022' style dates."""
    text = text.replace("\xa0", " ")
    m = re.search(r"([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+((?:19|20)\d\d)", text)
    if m:
        mon = MONTHS.get(m.group(1)[:3].lower())
        return dt.date(int(m.group(3)), mon, int(m.group(2))) if mon else None
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,9})\s+((?:19|20)\d\d)", text)
    if m:
        mon = MONTHS.get(m.group(2)[:3].lower())
        return dt.date(int(m.group(3)), mon, int(m.group(1))) if mon else None
    return None


def localize(regime: str, day: dt.date, hhmm: str | None) -> tuple[str, str]:
    """Return (local 'HH:MM', UTC ISO timestamp) or ('', '') when the time is unknown."""
    if not hhmm:
        return "", ""
    h, m = map(int, hhmm.split(":"))
    local = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=TZ[regime])
    return hhmm, local.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_24h(h: str, m: str, ampm: str) -> str:
    hour = int(h) % 12 + (12 if ampm.lower().startswith("p") else 0)
    return f"{hour:02d}:{int(m):02d}"


# =============================================================================
# Rate series helpers
# =============================================================================

class StepSeries:
    """A policy rate observed on (possibly sparse) dates; value carried forward."""

    def __init__(self, points: Iterable[tuple[dt.date, float]]):
        pts = sorted(points)
        self.dates = [d for d, _ in pts]
        self.values = [v for _, v in pts]

    def asof(self, day: dt.date) -> float | None:
        import bisect
        i = bisect.bisect_right(self.dates, day) - 1
        return self.values[i] if i >= 0 else None

    def changes(self, since: dt.date) -> list[tuple[dt.date, float, float]]:
        """(effective_date, old, new) for every change in level on/after `since`."""
        out = []
        for i in range(1, len(self.dates)):
            if self.values[i] != self.values[i - 1] and self.dates[i] >= since:
                out.append((self.dates[i], self.values[i - 1], self.values[i]))
        return out


def bis_policy_rate(cc: str) -> tuple[StepSeries, list[dt.date], str]:
    """BIS WS_CBPOL daily policy rate: (series, compilation break dates, compilation note)."""
    url = f"https://stats.bis.org/api/v1/data/WS_CBPOL/D.{cc}?format=csv&startPeriod=1999-01-01"
    raw = fetch(url, f"bis_cbpol_{cc.lower()}.csv", source="Bank for International Settlements",
                series_id=f"WS_CBPOL/D.{cc}",
                licence="BIS terms of use: free reuse with attribution",
                notes=f"Central bank policy rate, daily, {cc}")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
    pts = [(dt.date.fromisoformat(r["TIME_PERIOD"]), float(r["OBS_VALUE"]))
           for r in rows if r.get("OBS_VALUE") not in (None, "", "NaN")]
    note = rows[0].get("COMPILATION", "") if rows else ""
    breaks = []
    for m in re.finditer(r"[Ff]rom (\d{1,2} \w{3} \d{4})", note):
        breaks.append(dt.datetime.strptime(m.group(1), "%d %b %Y").date())
    return StepSeries(pts), breaks, note


def attribute_changes(meetings: list[dt.date], changes: list[tuple[dt.date, float, float]],
                      max_lag_days: int) -> tuple[dict[dt.date, list], list]:
    """Assign each rate change to the latest meeting on/before its effective date."""
    import bisect
    ms = sorted(meetings)
    by_meeting: dict[dt.date, list] = {}
    unmatched = []
    for eff, old, new in changes:
        i = bisect.bisect_right(ms, eff) - 1
        if i >= 0 and (eff - ms[i]).days <= max_lag_days:
            by_meeting.setdefault(ms[i], []).append((eff, old, new))
        else:
            unmatched.append((eff, old, new))
    return by_meeting, unmatched


def classify(size_bp: int) -> str:
    return "hike" if size_bp > 0 else ("cut" if size_bp < 0 else "hold")


def row(regime: str, day: dt.date, **kw) -> dict:
    r = {f: "" for f in FIELDS}
    r.update(regime=regime, decision_date=day.isoformat(), timezone=str(TZ[regime]))
    r.update(kw)
    return r


# =============================================================================
# Fed
# =============================================================================

FED = "https://www.federalreserve.gov"


def fed_rate_table() -> tuple[StepSeries, dict[dt.date, str]]:
    """openmarket.htm -> target (upper bound of range) by announcement date."""
    raw = fetch(f"{FED}/monetarypolicy/openmarket.htm", "fed_openmarket_target_rates.html",
                source="Federal Reserve Board", series_id="FOMC_TARGET_RATE_HISTORY",
                licence="Public domain (US Government)")
    soup = bs4.BeautifulSoup(html_text(raw), "html.parser")
    pts, level_text = [], {}
    for table in soup.find_all("table"):
        head = table.find_previous(["h2", "h3", "h4", "h5", "caption"])
        ym = re.search(r"(19|20)\d\d", head.get_text()) if head else None
        if not ym:
            continue
        year = int(ym.group(0))
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True).replace("\xa0", " ") for c in tr.find_all(["td", "th"])]
            if len(cells) < 4:
                continue
            day = parse_month_day_year(f"{cells[0]} {year}".replace(",", ""))
            nums = re.findall(r"\d+(?:\.\d+)?", cells[3])
            if not day or not nums:
                continue
            pts.append((day, float(nums[-1])))  # upper bound (or the single target)
            level_text[day] = cells[3]
    return StepSeries(pts), level_text


def fed_statement_links() -> list[dict]:
    """All FOMC statements 2000+ with date, statement URL and scheduled flag."""
    events = []
    for year in range(2000, 2021):
        url = f"{FED}/monetarypolicy/fomchistorical{year}.htm"
        raw = fetch(url, f"fed_fomchistorical{year}.html", source="Federal Reserve Board",
                    series_id=f"FOMC_{year}", licence="Public domain (US Government)",
                    notes=f"FOMC historical materials {year}")
        blocks = re.split(r"<h5[^>]*>", html_text(raw))[1:]
        for block in blocks:
            heading = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", block.split("</h5>")[0])).strip()
            for href, text in re.findall(r'href="([^"]+)"[^>]*>\s*([^<]*?)\s*<', block):
                if text.strip().lower() != "statement":
                    continue
                m = re.search(r"(\d{8})", href)
                if not m:
                    continue
                scheduled = "meeting" in heading.lower() and "unscheduled" not in heading.lower()
                events.append({"date": ymd(m.group(1)), "url": FED + href if href.startswith("/") else href,
                               "scheduled": scheduled, "heading": heading, "page": url})

    url = f"{FED}/monetarypolicy/fomccalendars.htm"
    raw = fetch(url, "fed_fomccalendars.html", source="Federal Reserve Board",
                series_id="FOMC_CALENDARS", licence="Public domain (US Government)")
    soup = bs4.BeautifulSoup(html_text(raw), "html.parser")
    for meeting in soup.select("div.fomc-meeting"):
        date_div = meeting.select_one(".fomc-meeting__date")
        date_txt = date_div.get_text(" ", strip=True) if date_div else ""
        for a in meeting.find_all("a", href=re.compile(r"monetary\d{8}a\.htm")):
            d = ymd(re.search(r"(\d{8})", a["href"]).group(1))
            events.append({"date": d, "url": FED + a["href"] if a["href"].startswith("/") else a["href"],
                           "scheduled": "unscheduled" not in date_txt.lower(),
                           "heading": date_txt, "page": url})
    seen, out = set(), []
    for e in sorted(events, key=lambda e: e["date"]):
        if e["date"] not in seen and e["date"] >= START:
            seen.add(e["date"])
            out.append(e)
    return out


def fed_release_time(stmt_url: str, day: dt.date) -> str | None:
    raw = fetch(stmt_url, f"fed_statements/fed_stmt_{day:%Y%m%d}.html", source="Federal Reserve Board",
                series_id=f"FOMC_STATEMENT_{day:%Y%m%d}", licence="Public domain (US Government)",
                notes="FOMC statement press release (used for release time)", missing_ok=True)
    if raw is None:
        return None
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_text(raw)))
    m = re.search(r"For release at (\d{1,2}):(\d{2})\s*([ap])\.?m\.?", text, re.IGNORECASE)
    return to_24h(m.group(1), m.group(2), m.group(3)) if m else None


FED_RANGE_START = dt.date(2008, 12, 16)  # target range (25 bp wide) replaces the single target


def fed_target_upper(issues: list[str]) -> StepSeries:
    """Fed target (upper bound of the range from 16 Dec 2008), from BIS WS_CBPOL US.

    BIS records the mid-point of the target; the range has been 25 bp wide since
    16 Dec 2008, so upper bound = mid-point + 0.125. Cross-checked against openmarket.htm
    (which only reaches back to 2003 and lists effective dates).
    """
    mid, _, _ = bis_policy_rate("US")
    upper = StepSeries((d, v + 0.125 if d >= FED_RANGE_START else v) for d, v in zip(mid.dates, mid.values))
    om, _ = fed_rate_table()
    mismatches = [(d, v, upper.asof(d)) for d, v in zip(om.dates, om.values)
                  if upper.asof(d + dt.timedelta(days=1)) != v]
    if mismatches:
        issues.append(f"Fed: {len(mismatches)} openmarket.htm levels disagree with BIS-derived upper bound: "
                      + ", ".join(f"{d} om={v} bis={b}" for d, v, b in mismatches[:5]))
    return upper


def harvest_fed(issues: list[str]) -> list[dict]:
    rate = fed_target_upper(issues)
    stmts = fed_statement_links()
    sdates = [e["date"] for e in stmts]
    # BIS/openmarket dates can be the effective day after the announcement.
    by_stmt, unmatched = attribute_changes(sdates, rate.changes(START), max_lag_days=2)
    basis = "Fed funds target; upper bound of the 25 bp range from 16 Dec 2008 (BIS WS_CBPOL US mid-point + 0.125)"
    rows = []
    for e in stmts:
        d = e["date"]
        ch = by_stmt.get(d, [])
        size = round((ch[-1][2] - ch[0][1]) * 100) if ch else 0
        hhmm = fed_release_time(e["url"], d)
        if hhmm:
            quality, tsrc = "exact", f"Statement page: 'For release at {hhmm}' ({e['url']})"
        elif e["scheduled"] and d < dt.date(2011, 4, 27):
            hhmm, quality = "14:15", "approximate"
            tsrc = ("Statement page says 'For immediate release'; FOMC standard 2:15 p.m. ET release "
                    "assumed for scheduled meetings before April 2011 - verify against Phase D surprise data")
        else:
            quality, tsrc = "unknown", f"No release time on statement page ({e['url']})"
        local, utc = localize("Fed", d, hhmm)
        rows.append(row("Fed", d, event_type="scheduled_meeting" if e["scheduled"] else "unscheduled_meeting",
                        scheduled=e["scheduled"], decision=classify(size), size_bp=size,
                        new_rate_pct=ch[-1][2] if ch else rate.asof(d), rate_basis=basis,
                        announce_time_local=local, announce_ts_utc=utc, time_quality=quality,
                        time_source=tsrc, date_source=f"FOMC statement link on {e['page']} ({e['heading']})",
                        source_url=e["url"]))
    for eff, old, new in unmatched:
        size = round((new - old) * 100)
        issues.append(f"Fed: target change effective {eff} ({old}->{new}) has no FOMC statement within 2 days; "
                      "kept as unscheduled_rate_change.")
        rows.append(row("Fed", eff, event_type="unscheduled_rate_change", scheduled=False,
                        decision=classify(size), size_bp=size, new_rate_pct=new, rate_basis=basis,
                        time_quality="unknown", time_source="No statement found",
                        date_source="BIS WS_CBPOL US effective date",
                        source_url="https://stats.bis.org/api/v1/data/WS_CBPOL/D.US"))
    return rows


# =============================================================================
# ECB
# =============================================================================

ECB_API = "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.{}.LEV?format=csvdata"
ECB_RATES = {"mrr_fr": "MRR_FR", "mrr_mbr": "MRR_MBR", "dfr": "DFR", "mlf": "MLFR"}
ECB_RATE_FILES = {"mrr_fr": "ecb_rate_mrr_dataportal.csv", "mrr_mbr": "ecb_rate_mrr_mbr_dataportal.csv",
                  "dfr": "ecb_rate_dfr_dataportal.csv", "mlf": "ecb_rate_mlf_dataportal.csv"}
ECB_MPS = "https://www.ecb.europa.eu/press/press_conference/monetary-policy-statement"
ECB_TIME_SWITCH = dt.date(2022, 7, 1)    # EA-MPD notes: windows change "As of July 2022"
ECB_STEERING_DFR = dt.date(2024, 9, 18)  # BIS WS_CBPOL XM compilation note


def ecb_rate(key: str) -> StepSeries:
    code = ECB_RATES[key]
    raw = fetch(ECB_API.format(code), ECB_RATE_FILES[key], source="ECB Data Portal", series_id=f"FM.D.U2.EUR.4F.KR.{code}.LEV",
                licence="ECB reuse policy (free reuse with attribution)",
                notes=f"ECB key interest rate {code}")
    pts = []
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8"))):
        if r.get("OBS_VALUE") not in (None, "", "NaN"):
            pts.append((dt.date.fromisoformat(r["TIME_PERIOD"]), float(r["OBS_VALUE"])))
    return StepSeries(pts)


def ecb_mro() -> StepSeries:
    """MRO = fixed rate where the ECB used fixed-rate tenders, else minimum bid rate."""
    fr, mbr = ecb_rate("mrr_fr"), ecb_rate("mrr_mbr")
    pts = dict(zip(mbr.dates, mbr.values))
    pts.update(zip(fr.dates, fr.values))
    # Variable-rate tender regime (28 Jun 2000 - 14 Oct 2008): MBR is the policy rate.
    for d, v in zip(mbr.dates, mbr.values):
        if dt.date(2000, 6, 28) <= d <= dt.date(2008, 10, 14):
            pts[d] = v
    return StepSeries(pts.items())


def ecb_eampd_dates() -> tuple[list[dt.date], str]:
    raw = (RAW_DIR / "ecb_ea_mpd_dataset.xlsx").read_bytes()  # saved in Phase B1 with provenance
    z = zipfile.ZipFile(io.BytesIO(raw))
    sheet = z.read("xl/worksheets/sheet2.xml").decode()      # 'Press Release Window'
    dates = set()
    for v in re.findall(r'<c r="A\d+"[^>]*><v>([\d.]+)</v>', sheet):
        d = dt.date(1899, 12, 30) + dt.timedelta(days=int(float(v)))
        if d >= dt.date(1999, 1, 1):
            dates.add(d)
    url = "https://www.ecb.europa.eu/pub/pdf/annex/Dataset_EA-MPD.xlsx"
    return sorted(dates), url


def ecb_statement_dates() -> dict[dt.date, str]:
    """Press-conference (monetary policy statement) dates from the ECB year lists."""
    out = {}
    for year in range(2000, TODAY.year + 1):
        url = f"{ECB_MPS}/{year}/html/index_include.en.html"
        raw = fetch(url, f"ecb_mps/ecb_mps_{year}.html", source="European Central Bank",
                    series_id=f"ECB_MP_STATEMENTS_{year}", licence="ECB reuse policy",
                    notes="List of monetary policy statements / press conferences", missing_ok=True)
        if raw is None:
            continue
        for dt_txt, dd in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd>(.*?)</dd>", html_text(raw), re.DOTALL):
            title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", dd))
            if re.search(r"monetary policy statement|introductory statement|press conference", title, re.IGNORECASE):
                d = parse_month_day_year(re.sub(r"<[^>]+>", " ", dt_txt))
                if d:
                    out[d] = url
    return out


def harvest_ecb(issues: list[str]) -> list[dict]:
    mro, dfr, mlf = ecb_mro(), ecb_rate("dfr"), ecb_rate("mlf")
    eampd, eampd_url = ecb_eampd_dates()
    stmts = ecb_statement_dates()
    last_eampd = max(eampd)
    # Cross-check the two meeting sources where both exist (2002-2023: one statement per meeting).
    overlap = [d for d in eampd if dt.date(2002, 1, 1) <= d <= last_eampd]
    missing = [d for d in overlap if d not in stmts]
    if missing:
        issues.append(f"ECB: {len(missing)} EA-MPD meeting dates have no press-conference entry: "
                      + ", ".join(map(str, missing[:10])))
    meetings = {d: ("EA-MPD Press Release Window sheet", eampd_url) for d in eampd if d >= START}
    for d, url in stmts.items():
        if d > last_eampd:
            meetings[d] = ("ECB monetary policy statement list (after last EA-MPD update)", url)
    mdates = sorted(meetings)

    rows = []
    for i, d in enumerate(mdates):
        nxt = mdates[i + 1] if i + 1 < len(mdates) else d + dt.timedelta(days=60)
        horizon = min(d + dt.timedelta(days=8), nxt - dt.timedelta(days=1))
        b = {k: s.asof(d) for k, s in (("mro", mro), ("dfr", dfr), ("mlf", mlf))}
        a = {k: s.asof(horizon) for k, s in (("mro", mro), ("dfr", dfr), ("mlf", mlf))}
        primary = "dfr" if d >= ECB_STEERING_DFR else "mro"
        size = round((a[primary] - b[primary]) * 100)
        hhmm = "14:15" if d >= ECB_TIME_SWITCH else "13:45"
        local, utc = localize("ECB", d, hhmm)
        src, url = meetings[d]
        rows.append(row("ECB", d, event_type="scheduled_meeting", scheduled=True,
                        decision=classify(size), size_bp=size, new_rate_pct=a[primary],
                        rate_basis="MRO (fixed rate or minimum bid rate)" if primary == "mro"
                        else "Deposit facility rate (steering rate from 18 Sep 2024, BIS WS_CBPOL XM note)",
                        rate_mro=a["mro"], rate_dfr=a["dfr"], rate_mlf=a["mlf"],
                        announce_time_local=local, announce_ts_utc=utc, time_quality="exact",
                        time_source=("EA-MPD notes: press release window 13:25-13:35 to 14:00-14:10 CET "
                                     "until June 2022; 13:55-14:05 to 14:30-14:40 from July 2022"),
                        date_source=src, source_url=url))

    # Rate changes on dates not attributable to a listed meeting (e.g. intermeeting cuts).
    for name, s in (("MRO", mro), ("DFR", dfr)):
        _, unmatched = attribute_changes(mdates, s.changes(START), max_lag_days=8)
        for eff, old, new in unmatched:
            issues.append(f"ECB: {name} change effective {eff} ({old}->{new}) not attributable to a "
                          "listed meeting; kept as unscheduled_rate_change (announcement date to verify).")
            if name == "MRO" or eff >= ECB_STEERING_DFR:
                size = round((new - old) * 100)
                rows.append(row("ECB", eff, event_type="unscheduled_rate_change", scheduled=False,
                                decision=classify(size), size_bp=size, new_rate_pct=new,
                                rate_basis=f"{name} effective-date change", rate_mro=mro.asof(eff),
                                rate_dfr=dfr.asof(eff), rate_mlf=mlf.asof(eff), time_quality="unknown",
                                time_source="Not available from rate series",
                                date_source="ECB Data Portal effective date (announcement date to verify)",
                                source_url=ECB_API.format(ECB_RATES['dfr' if name == 'DFR' else 'mrr_fr'])))
    return rows


# =============================================================================
# RBI
# =============================================================================

RBI_URL = "https://www.rbi.org.in/Scripts/Annualpolicy.aspx"
RBI_DATE = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, (19|20)\d\d$")
RBI_POLICY = re.compile(r"Monetary Policy Statement|Monetary and Credit Policy|Policy Review|Quarter Review|"
                        r"Annual Policy Statement|Bi-monthly (Monetary )?Policy|Mid-term Review|"
                        r"Monetary Policy Review|Statement on Monetary Policy|Annual Policy", re.IGNORECASE)


def rbi_year_pages() -> dict[int, bytes]:
    pages, form = {}, None
    sess = requests.Session()
    sess.headers.update(SESSION.headers)
    for fy in range(2000, TODAY.year + 2):
        path = RAW_DIR / f"rbi_policy/rbi_policy_fy{fy}.html"
        if not path.exists() and form is None:
            soup = bs4.BeautifulSoup(sess.get(RBI_URL, timeout=60).text, "html.parser")
            form = {i.get("name"): i.get("value", "") for i in soup.find_all("input") if i.get("name")}
        data = dict(form or {}, hdnYear=str(fy))
        pages[fy] = fetch(RBI_URL, f"rbi_policy/rbi_policy_fy{fy}.html", source="Reserve Bank of India",
                          series_id=f"RBI_MONETARY_POLICY_FY{fy - 1}-{str(fy)[2:]}",
                          licence="RBI website terms of use",
                          notes=f"Monetary policy archive, financial year {fy - 1}-{fy} (form post hdnYear={fy})",
                          data=data, session=sess)
    return pages


def rbi_policy_dates(pages: dict[int, bytes]) -> tuple[dict[dt.date, str], dict[int, set[dt.date]]]:
    """Policy decision dates, and the MPC's pre-announced meeting end dates per financial year.

    The archive lists, per date, a section heading followed by documents. A decision is
    followed by transcripts/recordings on later days under the same heading, so dates are
    grouped into runs (same heading, <= 7 days apart) and the first date of each run is the
    announcement. Sections for macro reviews, minutes and schedules are not decisions.
    """
    sections: list[tuple[dt.date, str, int]] = []
    schedule: dict[int, set[dt.date]] = {}
    for fy, raw in pages.items():
        soup = bs4.BeautifulSoup(html_text(raw), "html.parser")
        current, items = None, {}
        for tr in soup.find_all("tr"):
            if tr.find("tr"):
                continue
            text = tr.get_text(" ", strip=True)
            if RBI_DATE.match(text):
                current = dt.datetime.strptime(re.sub(r"(\w{3})\w*", r"\1", text, count=1), "%b %d, %Y").date()
                items.setdefault(current, [])
            elif current and text:
                items[current].append(text)
        for d, titles in items.items():
            if not titles:
                continue
            section = titles[0]
            if section.startswith("Meeting Schedule of the Monetary Policy Committee"):
                for t in titles[1:]:
                    m = re.search(r"([A-Za-z]+)\s+\d{1,2}\s*(?:-|to|and)\s*(?:([A-Za-z]+)\s+)?(\d{1,2}),\s*(\d{4})", t)
                    if m and (mon := MONTHS.get((m.group(2) or m.group(1))[:3].lower())):
                        schedule.setdefault(fy, set()).add(dt.date(int(m.group(4)), mon, int(m.group(3))))
            elif RBI_POLICY.search(section) and not re.search(r"Macroeconomic|Minutes", section):
                sections.append((d, section, fy))
    decisions: dict[dt.date, str] = {}
    last_d, last_title = None, None
    for d, section, fy in sorted(sections):
        if last_d is None or section != last_title or (d - last_d).days > 7:
            decisions[d] = f"RBI monetary policy archive FY{fy - 1}-{str(fy)[2:]}: {section[:80]}"
        last_d, last_title = d, section
    return decisions, schedule


def harvest_rbi(issues: list[str]) -> list[dict]:
    rate, breaks, note = bis_policy_rate("IN")
    decisions, schedule = rbi_policy_dates(rbi_year_pages())
    ddates = sorted(d for d in decisions if d >= START)
    changes = [c for c in rate.changes(START) if c[0] not in breaks]
    by_meeting, unmatched = attribute_changes(ddates, changes, max_lag_days=3)
    rows = []
    for d in ddates:
        ch = by_meeting.get(d, [])
        size = round((ch[-1][2] - ch[0][1]) * 100) if ch else 0
        fy = d.year + 1 if d.month >= 4 else d.year
        fy_schedule = schedule.get(fy)
        scheduled = (d in fy_schedule) if d >= dt.date(2016, 10, 1) and fy_schedule else True
        rows.append(row("RBI", d, event_type="scheduled_meeting" if scheduled else "unscheduled_meeting",
                        scheduled=scheduled, decision=classify(size), size_bp=size,
                        new_rate_pct=rate.asof(d + dt.timedelta(days=3)),
                        rate_basis="Repo rate from 3 Apr 2001; bank rate before (BIS WS_CBPOL IN)",
                        time_quality="unknown", time_source="Release time not stated on RBI archive pages",
                        date_source=decisions[d], source_url=RBI_URL))
    for eff, old, new in unmatched:
        size = round((new - old) * 100)
        issues.append(f"RBI: policy rate change effective {eff} ({old}->{new}) not on a listed policy date; "
                      "kept as unscheduled_rate_change (announcement date to verify).")
        rows.append(row("RBI", eff, event_type="unscheduled_rate_change", scheduled=False,
                        decision=classify(size), size_bp=size, new_rate_pct=new,
                        rate_basis="Repo rate from 3 Apr 2001; bank rate before (BIS WS_CBPOL IN)",
                        time_quality="unknown", time_source="Not available from rate series",
                        date_source="BIS WS_CBPOL IN effective date (announcement date to verify)",
                        source_url="https://stats.bis.org/api/v1/data/WS_CBPOL/D.IN"))
    no_sched = sorted({(d.year + 1 if d.month >= 4 else d.year) for d in ddates
                       if d >= dt.date(2016, 10, 1)} - set(schedule))
    if no_sched:
        issues.append("RBI: no MPC meeting schedule found for FY ending " + ", ".join(map(str, no_sched))
                      + "; decisions in those years are marked scheduled - verify off-cycle meetings by hand.")
    if breaks:
        issues.append(f"RBI: BIS series breaks at {', '.join(map(str, breaks))} ({note[:120]}); level "
                      "jumps on break dates are not treated as decisions.")
    return rows


# =============================================================================
# BoJ
# =============================================================================

BOJ = "https://www.boj.or.jp"


def boj_statement_dates() -> dict[dt.date, str]:
    out = {}
    for year in range(2000, TODAY.year + 1):
        url = f"{BOJ}/en/mopo/mpmdeci/state_{year}/index.htm"
        raw = fetch(url, f"boj_state_{year}.html", source="Bank of Japan", series_id=f"BOJ_STATEMENTS_{year}",
                    licence="BoJ website terms of use (credit the source)", missing_ok=True)
        if raw is None:
            continue
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html_text(raw), re.DOTALL):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
            if len(tds) >= 2:
                d = parse_month_day_year(re.sub(r"<[^>]+>", " ", tds[0]).replace("&nbsp;", " "))
                link = re.search(r'href="([^"]+)"', tr)
                if d and d not in out:
                    out[d] = BOJ + link.group(1) if link else url
    return out


def boj_minutes() -> dict[dt.date, str]:
    """Minutes document URL keyed by the final meeting day (from the gYYMMDD file name)."""
    out = {}
    for year in range(2000, TODAY.year + 1):
        url = f"{BOJ}/en/mopo/mpmsche_minu/minu_{year}/index.htm"
        raw = fetch(url, f"boj_minutes/boj_minutes_index_{year}.html", source="Bank of Japan",
                    series_id=f"BOJ_MINUTES_INDEX_{year}", licence="BoJ website terms of use (credit the source)",
                    missing_ok=True)
        if raw is None:
            continue
        for href in re.findall(rf'href="(/en/mopo/mpmsche_minu/minu_{year}/g(\d{{6}})\.(?:pdf|htm))"', html_text(raw)):
            d = dt.datetime.strptime(href[1], "%y%m%d").date()
            out.setdefault(d, BOJ + href[0])
    return out


def boj_meeting_end(url: str, day: dt.date) -> str | None:
    ext = url.rsplit(".", 1)[-1]
    raw = fetch(url, f"boj_minutes/g{day:%y%m%d}.{ext}", source="Bank of Japan",
                series_id=f"BOJ_MINUTES_{day:%Y%m%d}", licence="BoJ website terms of use (credit the source)",
                notes="MPM minutes (used for meeting end time)", missing_ok=True)
    if raw is None:
        return None
    if ext == "pdf":
        import logging

        from pypdf import PdfReader
        logging.getLogger("pypdf").setLevel(logging.ERROR)  # font-encoding warnings are harmless here
        text =" ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages[:4])
    else:
        text = re.sub(r"<[^>]+>", " ", html_text(raw))
    text = re.sub(r"\s+", " ", text)
    # "... held ... on Thursday, January 28, 2016, from 2:00 p.m. to 3:46 p.m., and on Friday,
    #  January 29, from 9:00 a.m. to 12:31 p.m." -> the last 'to' time of the opening sentence.
    m = re.search(r"Policy Board was held(.{0,400}?)(?:Policy Board Members|Members Present|$)", text)
    if not m:
        return None
    seg = m.group(1)
    times = re.findall(r"to (\d{1,2}):(\d{2})\s*([ap])\.?\s?m", seg)
    return to_24h(*times[-1]) if times else None


def harvest_boj(issues: list[str]) -> list[dict]:
    # The BIS JP note lists each policy regime as "From <date>: ...", so its dates are rate
    # changes, not definitional breaks. BIS has no observations while the BoJ targeted the
    # monetary base / zero rate; a level change across such a gap is not a decision.
    rate, _breaks, _note = bis_policy_rate("JP")
    gaps = [(a, b) for a, b in zip(rate.dates, rate.dates[1:]) if (b - a).days > 10]
    in_gap = lambda d: any(a < d <= b for a, b in gaps)
    stmts, minutes = boj_statement_dates(), boj_minutes()
    meetings = sorted(d for d in set(stmts) | set(minutes) if d >= START)
    changes = [c for c in rate.changes(START) if not in_gap(c[0])]
    by_meeting, unmatched = attribute_changes(meetings, changes, max_lag_days=21)
    issues.append("BoJ: no BIS policy rate during " + "; ".join(f"{a + dt.timedelta(days=1)} to {b}" for a, b in gaps
                  if b >= START) + " (monetary-base / zero-rate targeting); meetings in these spans are "
                  "'unclassified' and need classifying from the statements in Phase D.")
    rows = []
    for d in meetings:
        ch = by_meeting.get(d, [])
        size = round((ch[-1][2] - ch[0][1]) * 100) if ch else 0
        if in_gap(d):
            hhmm = boj_meeting_end(minutes[d], d) if d in minutes else None
            local, utc = localize("BoJ", d, hhmm)
            rows.append(row("BoJ", d, event_type="scheduled_meeting", scheduled=True, decision="unclassified",
                            rate_basis="No BIS policy rate in this period (quantity / zero-rate targeting)",
                            announce_time_local=local, announce_ts_utc=utc,
                            time_quality="approximate" if hhmm else "unknown",
                            time_source=(f"Meeting end time from MPM minutes ({minutes[d]})" if hhmm
                                         else "No end time available"),
                            date_source="BoJ statement list" if d in stmts else "BoJ minutes list (final meeting day)",
                            source_url=stmts.get(d) or minutes.get(d)))
            continue
        hhmm = boj_meeting_end(minutes[d], d) if d in minutes else None
        if hhmm:
            quality, tsrc = "approximate", f"Meeting end time from MPM minutes ({minutes[d]}); release follows the meeting"
        else:
            quality = "unknown"
            tsrc = "Minutes not yet published or no end time found" if d not in minutes else f"No end time in {minutes[d]}"
        local, utc = localize("BoJ", d, hhmm)
        rows.append(row("BoJ", d, event_type="scheduled_meeting", scheduled=True,
                        decision=classify(size), size_bp=size,
                        new_rate_pct=rate.asof(d + dt.timedelta(days=21)) if ch else rate.asof(d),
                        rate_basis="BIS WS_CBPOL JP policy rate (quantity-target periods carry the last rate)",
                        announce_time_local=local, announce_ts_utc=utc, time_quality=quality, time_source=tsrc,
                        date_source="BoJ statement list" if d in stmts else "BoJ minutes list (final meeting day)",
                        source_url=stmts.get(d) or minutes.get(d)))
    for eff, old, new in unmatched:
        size = round((new - old) * 100)
        issues.append(f"BoJ: policy rate change effective {eff} ({old}->{new}) not attributable to a listed "
                      "meeting; kept as unscheduled_rate_change.")
        rows.append(row("BoJ", eff, event_type="unscheduled_rate_change", scheduled=False,
                        decision=classify(size), size_bp=size, new_rate_pct=new,
                        rate_basis="BIS WS_CBPOL JP policy rate", time_quality="unknown",
                        time_source="Not available from rate series",
                        date_source="BIS WS_CBPOL JP effective date (announcement date to verify)",
                        source_url="https://stats.bis.org/api/v1/data/WS_CBPOL/D.JP"))
    unscheduled_hint = [d for d in meetings if d in minutes and d not in stmts]
    if unscheduled_hint:
        issues.append(f"BoJ: {len(unscheduled_hint)} meetings appear only in the minutes list (no statement "
                      "row); scheduled status not stated by the source.")
    return rows


# =============================================================================
# Main
# =============================================================================

def main() -> list[str]:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    issues: list[str] = []
    rows = []
    for name, harvest in (("Fed", harvest_fed), ("ECB", harvest_ecb), ("RBI", harvest_rbi), ("BoJ", harvest_boj)):
        part = harvest(issues)
        counts = {k: sum(r["decision"] == k for r in part) for k in ("hike", "cut", "hold")}
        print(f"{name}: {len(part)} rows {counts}")
        rows.extend(part)
    rows.sort(key=lambda r: (r["regime"], r["decision_date"]))
    for r in rows:
        r["window_start_utc"], r["window_end_utc"] = announcement_window(r)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    (INTERIM_DIR / "pilot_policy_issues.txt").write_text("\n".join(issues) + "\n", encoding="utf-8")
    print(f"Saved {len(rows)} rows to {OUT_CSV}; {len(issues)} issues logged.")
    return issues


if __name__ == "__main__":
    main()
