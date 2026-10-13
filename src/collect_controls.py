"""Control variables for all 15 countries (Phase C).

Output: data/interim/controls_long.parquet with one row per (country, variable, date):
  country, variable, date, value, available_from, source
`available_from` is the first date the value may be used (no look-ahead):
  daily market data   -> the observation date itself (a close known at that day's end)
  monthly macro data  -> first day of month m+2 for month m (DECISION-016; free sources
                         carry no release calendars, so a conservative fixed lag is used)

Variables
  fx_lcu_per_usd  BIS WS_XRU daily (local currency per USD)
  policy_rate     BIS WS_CBPOL daily
  cpi             BIS WS_LONG_CPI monthly index
  ind_prod        OECD STES industrial production index (seasonally adjusted), monthly
  yield_1y        1-year government yield from national sources (see YIELD_SOURCES)
  vix             CBOE VIX (US implied volatility, Yahoo ^VIX)
Valuation (P/E or earnings yield) has no free historical source for these markets and is
not collected (docs/issues.md).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

from src.download import RAW_DIR, save_raw_file

INTERIM = Path(__file__).resolve().parent.parent / "data" / "interim"
UA = {"User-Agent": "Mozilla/5.0 (MoTrans-15 research data collection)"}
TODAY = dt.date.today()
BIS_TERMS = "BIS terms of use: free reuse with attribution"

# country -> (BIS area code, currency)
AREAS = {"US": ("US", "USD"), "DE": ("XM", "EUR"), "FR": ("XM", "EUR"), "IT": ("XM", "EUR"),
         "ES": ("XM", "EUR"), "EA": ("XM", "EUR"), "GB": ("GB", "GBP"), "JP": ("JP", "JPY"),
         "CN": ("CN", "CNY"), "IN": ("IN", "INR"), "RU": ("RU", "RUB"), "CA": ("CA", "CAD"),
         "BR": ("BR", "BRL"), "MX": ("MX", "MXN"), "AU": ("AU", "AUD"), "KR": ("KR", "KRW")}
CPI_AREA = {"DE": "DE", "FR": "FR", "IT": "IT", "ES": "ES", "EA": "XM"}  # national CPI where it exists
OECD_ISO3 = {"US": "USA", "DE": "DEU", "FR": "FRA", "IT": "ITA", "ES": "ESP", "GB": "GBR", "JP": "JPN",
             "CA": "CAN", "AU": "AUS", "KR": "KOR", "MX": "MEX", "BR": "BRA", "IN": "IND", "CN": "CHN",
             "RU": "RUS", "EA": "EA20"}


def fetch(url: str, filename: str, *, source: str, series_id: str, licence: str, notes: str = "",
          timeout: int = 120) -> bytes:
    path = RAW_DIR / filename
    if path.exists():
        return path.read_bytes()
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=UA, timeout=timeout)
            resp.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(10)
    time.sleep(0.3)
    save_raw_file(resp.content, filename, source=source, url_or_api=url, series_id=series_id,
                  licence=licence, notes=notes)
    return resp.content


def bis_csv(dataflow: str, key: str, filename: str, notes: str) -> list[dict]:
    url = f"https://stats.bis.org/api/v1/data/{dataflow}/{key}?format=csv&startPeriod=1999-01-01"
    raw = fetch(url, filename, source="Bank for International Settlements", series_id=f"{dataflow}/{key}",
                licence=BIS_TERMS, notes=notes)
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))


def rows(country: str, variable: str, points, source: str, monthly: bool = False) -> list[dict]:
    out = []
    for day, value in points:
        if value is None:
            continue
        avail = (dt.date(day.year + (day.month + 1) // 12, (day.month + 1) % 12 + 1, 1) if monthly else day)
        out.append({"country": country, "variable": variable, "date": day, "value": float(value),
                    "available_from": avail, "source": source})
    return out


# --- BIS: FX, policy rate, CPI ------------------------------------------------

def bis_daily(dataflow: str, key: str, filename: str, notes: str) -> list[tuple[dt.date, float]]:
    return [(dt.date.fromisoformat(r["TIME_PERIOD"]), float(r["OBS_VALUE"]))
            for r in bis_csv(dataflow, key, filename, notes) if r.get("OBS_VALUE") not in ("", "NaN", None)]


def collect_bis() -> list[dict]:
    out = []
    for area, ccy in sorted({v for k, v in AREAS.items() if k != "US"}):
        fx = bis_daily("WS_XRU", f"D.{area}.{ccy}.A", f"controls/bis_fx_{area.lower()}.csv",
                       f"Daily exchange rate, {ccy} per USD")
        for country, (a, _) in AREAS.items():
            if a == area:
                out += rows(country, "fx_lcu_per_usd", fx, "BIS WS_XRU")
    for area in sorted({a for a, _ in AREAS.values()}):
        pr = bis_daily("WS_CBPOL", f"D.{area}", f"bis_cbpol_{area.lower()}.csv", f"Central bank policy rate, {area}")
        for country, (a, _) in AREAS.items():
            if a == area:
                out += rows(country, "policy_rate", pr, "BIS WS_CBPOL")
    for country, (a, _) in AREAS.items():
        area = CPI_AREA.get(country, a)
        recs = bis_csv("WS_LONG_CPI", f"M.{area}.771", f"controls/bis_cpi_{area.lower()}.csv",
                       f"Consumer prices, index, monthly, {area}")
        pts = [(dt.date.fromisoformat(r["TIME_PERIOD"] + "-01"), float(r["OBS_VALUE"]))
               for r in recs if r.get("OBS_VALUE") not in ("", "NaN", None)]
        out += rows(country, "cpi", pts, "BIS WS_LONG_CPI", monthly=True)
    return out


# --- OECD industrial production ----------------------------------------------------

def collect_oecd_ip(issues: list[str]) -> list[dict]:
    areas = "+".join(sorted(set(OECD_ISO3.values())))
    url = (f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_INDSERV,4.0/"
           f"{areas}.M.PRVM.IX.BTE.Y...?startPeriod=1999-01&format=csvfile")
    raw = fetch(url, "controls/oecd_industrial_production.csv", source="OECD STES",
                series_id="DF_INDSERV PRVM IX BTE (SA)", licence="OECD terms (CC BY 4.0)",
                notes="Industrial production index, seasonally adjusted, monthly", timeout=300)
    df = pd.read_csv(io.BytesIO(raw))
    out = []
    for country, iso in OECD_ISO3.items():
        g = df[df["REF_AREA"] == iso]
        if g.empty:
            issues.append(f"{country}: no OECD industrial production series ({iso}).")
            continue
        pts = [(dt.date.fromisoformat(p + "-01"), v) for p, v in zip(g["TIME_PERIOD"], g["OBS_VALUE"])]
        out += rows(country, "ind_prod", pts, "OECD STES DF_INDSERV", monthly=True)
    return out


# --- 1-year government yields ---------------------------------------------------------

def y_us() -> list[tuple]:
    pts = []
    for year in range(2000, TODAY.year + 1):
        url = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/"
               f"{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv")
        raw = fetch(url, f"controls/us_treasury_{year}.csv", source="US Department of the Treasury",
                    series_id=f"Daily par yield curve {year}", licence="Public domain (US Government)")
        for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
            if r.get("1 Yr"):
                pts.append((dt.datetime.strptime(r["Date"], "%m/%d/%Y").date(), float(r["1 Yr"])))
    return pts


def y_de() -> list[tuple]:
    url = ("https://api.statistiken.bundesbank.de/rest/download/BBSIS/"
           "D.I.ZST.ZI.EUR.S1311.B.A604.R01XX.R.A.A._Z._Z.A?format=csv&lang=en")
    raw = fetch(url, "controls/bundesbank_1y.csv", source="Deutsche Bundesbank",
                series_id="BBSIS.D.I.ZST.ZI.EUR.S1311.B.A604.R01XX.R.A.A._Z._Z.A",
                licence="Bundesbank terms (free reuse with source)", notes="1-year yield, listed Federal securities (Svensson)")
    pts = []
    for line in raw.decode("utf-8-sig").splitlines():
        m = re.match(r'"?(\d{4}-\d{2}-\d{2})"?,"?(-?\d+\.?\d*)"?', line)
        if m:
            pts.append((dt.date.fromisoformat(m.group(1)), float(m.group(2))))
    return pts


def y_ea() -> list[tuple]:
    url = "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_C.SV_C_YM.SR_1Y?format=csvdata"
    raw = fetch(url, "controls/ecb_yc_all_1y.csv", source="ECB Data Portal",
                series_id="YC.B.U2.EUR.4F.G_N_C.SV_C_YM.SR_1Y", licence="ECB reuse policy",
                notes="Euro area 1-year spot rate, all central-government bonds")
    return [(dt.date.fromisoformat(r["TIME_PERIOD"]), float(r["OBS_VALUE"]))
            for r in csv.DictReader(io.StringIO(raw.decode("utf-8"))) if r.get("OBS_VALUE")]


def y_jp() -> list[tuple]:
    pts = {}
    for name, url in (("all", "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv"),
                      ("current", "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv")):
        raw = fetch(url, f"controls/mof_jgb_{name}.csv", source="Ministry of Finance Japan",
                    series_id=f"JGB interest rates ({name})", licence="MoF Japan website terms (credit source)")
        for line in raw.decode("utf-8", errors="replace").splitlines():
            parts = line.split(",")
            if len(parts) > 1 and re.match(r"\d{4}/\d{1,2}/\d{1,2}$", parts[0]) and re.match(r"-?\d", parts[1]):
                pts[dt.datetime.strptime(parts[0], "%Y/%m/%d").date()] = float(parts[1])
    return sorted(pts.items())


def y_ca() -> list[tuple]:
    """Bank of Canada 2-year benchmark bond yield (daily). The 1-year T-bill series is weekly."""
    url = "https://www.bankofcanada.ca/valet/observations/group/bond_yields_benchmark/csv?start_date=1999-01-01"
    raw = fetch(url, "controls/boc_bond_yields_benchmark.csv", source="Bank of Canada Valet",
                series_id="group bond_yields_benchmark", licence="Bank of Canada terms (free reuse with attribution)",
                notes="Benchmark bond yields incl. 2-year (daily)")
    text = raw.decode("utf-8-sig")
    series = dict(re.findall(r'"(BD\.CDN\.[^"]+)","([^"]*)"', text))
    col = next((k for k in series if re.search(r"\.2YR\.", k)), None)  # e.g. BD.CDN.2YR.DQ.YLD
    obs = text[text.find('"OBSERVATIONS"'):]
    reader = csv.DictReader(io.StringIO(obs.split("\n", 1)[1]))
    return [(dt.date.fromisoformat(r["date"]), float(r[col])) for r in reader if col and r.get(col)]


def y_gb() -> list[tuple]:
    url = "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/glcnominalddata.zip"
    raw = fetch(url, "controls/boe_glc_nominal_daily.zip", source="Bank of England yield curves",
                series_id="GLC nominal daily spot curve", licence="Bank of England terms (free reuse with attribution)",
                notes="Daily nominal government liability curve archive", timeout=600)
    pts = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in z.namelist():
            if not name.lower().endswith((".xlsx", ".xls")):
                continue
            sheets = pd.read_excel(io.BytesIO(z.read(name)), sheet_name=None, header=None)
            sheet = next((s for k, s in sheets.items() if k.lower().rstrip().endswith("spot curve")), None)
            if sheet is None:
                continue
            hdr = sheet.index[sheet.iloc[:, 0].astype(str).str.contains("years", case=False, na=False)]
            if len(hdr) == 0:
                continue
            mats = sheet.iloc[hdr[0]].tolist()
            col = next((i for i, m in enumerate(mats) if isinstance(m, (int, float)) and abs(float(m) - 1.0) < 1e-6), None)
            if col is None:
                continue
            for _, r in sheet.iloc[hdr[0] + 1:].iterrows():
                if isinstance(r.iloc[0], (pd.Timestamp, dt.datetime)) and pd.notna(r.iloc[col]):
                    pts[r.iloc[0].date()] = float(r.iloc[col])
    return sorted(pts.items())


def y_ru() -> list[tuple]:
    pts = {}
    for year in range(2003, TODAY.year + 1):
        url = (f"https://www.cbr.ru/eng/hd_base/zcyc_params/?UniDbQuery.Posted=True"
               f"&UniDbQuery.From=01.01.{year}&UniDbQuery.To=31.12.{year}")
        raw = fetch(url, f"controls/cbr_zcyc_{year}.html", source="Bank of Russia",
                    series_id=f"Zero-coupon yield curve {year}", licence="Bank of Russia website terms")
        for row in re.findall(r"<tr>(.*?)</tr>", raw.decode("utf-8", errors="replace"), re.DOTALL):
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)]
            if len(cells) >= 5 and re.match(r"\d{2}\.\d{2}\.\d{4}$", cells[0]):
                # columns: date, 0.25, 0.5, 0.75, 1, 2, ... years
                pts[dt.datetime.strptime(cells[0], "%d.%m.%Y").date()] = float(cells[4].replace(",", "."))
    return sorted(pts.items())


def y_br() -> list[tuple]:
    pts = []
    for start in range(2000, TODAY.year + 1, 10):
        end = min(start + 9, TODAY.year)
        url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.7806/dados?formato=json"
               f"&dataInicial=01/01/{start}&dataFinal=31/12/{end}")
        try:
            raw = fetch(url, f"controls/bcb_sgs7806_{start}_{end}.json", source="Banco Central do Brasil SGS",
                        series_id="SGS 7806 (swap DI x pre 360 days)", licence="BCB open data (free reuse)")
        except requests.HTTPError:
            continue  # no observations in this window (series ended in 2019)
        import json
        pts += [(dt.datetime.strptime(r["data"], "%d/%m/%Y").date(), float(r["valor"]))
                for r in json.loads(raw) if r.get("valor") not in (None, "")]
    return pts


YIELD_SOURCES = {  # country -> (function, description)
    "US": (y_us, "US Treasury daily par yield, 1 year"),
    "DE": (y_de, "Bundesbank 1-year yield on listed Federal securities"),
    "FR": (y_ea, "ECB euro-area 1-year spot rate (all govt bonds) - proxy, no national daily series"),
    "IT": (y_ea, "ECB euro-area 1-year spot rate (all govt bonds) - proxy, no national daily series"),
    "ES": (y_ea, "ECB euro-area 1-year spot rate (all govt bonds) - proxy, no national daily series"),
    "EA": (y_ea, "ECB euro-area 1-year spot rate (all govt bonds)"),
    "JP": (y_jp, "MoF Japan JGB 1-year yield"),
    "CA": (y_ca, "Bank of Canada 2-year benchmark bond yield (daily; 1-year bills are weekly)"),
    "GB": (y_gb, "Bank of England nominal spot curve, 1 year"),
    "RU": (y_ru, "Bank of Russia zero-coupon curve, 1 year"),
    "BR": (y_br, "BCB SGS 7806 swap DI x pre 360 days (ends 2019)"),
}


def collect_yields(issues: list[str]) -> list[dict]:
    out, cache = [], {}
    for country in AREAS:
        if country not in YIELD_SOURCES:
            issues.append(f"{country}: no free daily 1-year yield source found; yield_1y missing.")
            continue
        func, desc = YIELD_SOURCES[country]
        try:
            pts = cache[func] if func in cache else cache.setdefault(func, func())
        except Exception as e:  # noqa: BLE001 - a failed source is logged, never filled
            issues.append(f"{country}: 1-year yield source failed ({desc}): {type(e).__name__}: {str(e)[:120]}")
            continue
        if not pts:
            issues.append(f"{country}: 1-year yield source returned no observations ({desc}).")
        out += rows(country, "yield_1y", pts, desc)
    return out


def collect_vix() -> list[dict]:
    path = RAW_DIR / "controls/us_vix_daily.csv"
    if not path.exists():
        import yfinance as yf
        hist = yf.Ticker("^VIX").history(period="max", auto_adjust=False)
        save_raw_file(hist.to_csv().encode("utf-8"), "controls/us_vix_daily.csv", source="Yahoo Finance (yfinance)",
                      url_or_api="yfinance:^VIX history(period='max')", series_id="^VIX",
                      licence="Yahoo Finance terms of service (no redistribution)", notes="CBOE VIX daily")
    df = pd.read_csv(path)
    pts = list(zip(pd.to_datetime(df["Date"].str[:10]).dt.date, df["Close"]))
    return rows("US", "vix", pts, "CBOE VIX via Yahoo")


def main() -> list[str]:
    issues: list[str] = []
    out = collect_bis() + collect_oecd_ip(issues) + collect_yields(issues) + collect_vix()
    df = pd.DataFrame(out)
    df = df[df["date"] >= dt.date(1999, 1, 1)].sort_values(["country", "variable", "date"])
    df.to_parquet(INTERIM / "controls_long.parquet", index=False)
    (INTERIM / "controls_issues.txt").write_text("\n".join(issues) + "\n", encoding="utf-8")
    cov = df.groupby(["country", "variable"])["date"].agg(["min", "max", "size"])
    print(cov.to_string())
    print(f"{len(df)} control rows; {len(issues)} issues -> {INTERIM / 'controls_issues.txt'}")
    return issues


if __name__ == "__main__":
    main()
