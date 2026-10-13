"""Daily levels and log returns for the equity series of all 15 countries.

Raw-first: each series is downloaded once through save_raw_file() (write-once, logged in
MANIFEST.csv) and the panel is always rebuilt from the saved raw file, so a re-run
reproduces the same panel. Delete a raw file by hand only to deliberately refresh it.

Sources: Yahoo Finance (yfinance), NSE Indices (India), China Securities Index (China),
Moscow Exchange ISS (Russia) and B3 (Brazil sector / small-cap indices).

Columns: unadjusted close (auto_adjust=False), ret_local = ln(P_t / P_{t-1}),
exdiv_flag (ETF ex-dividend day, from the raw Dividends column), stale_flag (ETF day
with zero traded volume, so the close is not a fresh price), outlier_flag (|ret| > 0.10).
The current (possibly still trading) day is excluded.

Outputs: data/interim/indices_daily.parquet (all series) and
data/interim/pilot_indices_daily.parquet (the Phase B pilot subset: US, DE, IN, JP).
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from src.download import RAW_DIR, save_raw_file

INTERIM_DIR = Path(__file__).resolve().parent.parent / "data" / "interim"
# EA = euro-area-wide series traded on Xetra (shared by DE, FR, IT, ES; see DECISION-015).
CALENDARS = {"US": "XNYS", "DE": "XETR", "IN": "XBOM", "JP": "XTKS", "CN": "XSHG", "GB": "XLON",
             "FR": "XPAR", "IT": "XMIL", "ES": "XMAD", "EA": "XETR", "RU": "XMOS", "CA": "XTSE",
             "BR": "BVMF", "MX": "XMEX", "AU": "XASX", "KR": "XKRX"}
PILOT = {"US", "DE", "IN", "JP"}
START = dt.date(2000, 1, 1)
OUTLIER = 0.10
UA = {"User-Agent": "Mozilla/5.0 (MoTrans-15 research data collection)"}
YAHOO_TERMS = "Yahoo Finance terms of service (personal/research use; no redistribution)"
NSE_TERMS = "NSE Indices Limited website terms of use (no redistribution of data)"
CSI_TERMS = "China Securities Index Co. website terms (no redistribution of data)"
MOEX_TERMS = "Moscow Exchange ISS terms (non-commercial use; no redistribution of data)"
B3_TERMS = "B3 S.A. website terms (no redistribution of data)"
NIFTY_URL = "https://www.niftyindices.com/BackPage/getHistoricaldatatabletoString"

# (country, index_id, index_class, code, source, is_etf, raw_file)
SERIES_SPEC = [
    # --- Phase B pilot ---
    ("US", "us_sp500", "broad", "^GSPC", "yfinance", False, "us_sp500_daily.csv"),
    ("US", "us_bkx", "banks", "^BKX", "yfinance", False, "us_bkx_daily.csv"),
    ("US", "us_rut", "smallcap", "^RUT", "yfinance", False, "us_rut_daily.csv"),
    ("DE", "de_dax", "broad", "^GDAXI", "yfinance", False, "de_dax_daily.csv"),
    ("DE", "de_stoxx_banks_etf", "banks", "EXX1.DE", "yfinance", True, "de_stoxx_banks_etf_daily.csv"),
    ("DE", "de_dax_banks", "banks_robustness", "^CXPBX", "yfinance", False, "de_dax_banks_daily.csv"),
    ("DE", "de_mdax", "smallcap", "^MDAXI", "yfinance", False, "de_mdax_daily.csv"),
    ("IN", "in_nifty50", "broad", "NIFTY 50", "niftyindices", False, "in_nifty50_niftyindices.json"),
    ("IN", "in_nifty_bank", "banks", "NIFTY BANK", "niftyindices", False, "in_nifty_bank_niftyindices.json"),
    ("IN", "in_nifty_smallcap100", "smallcap", "NIFTY SMALLCAP 100", "niftyindices", False,
     "in_nifty_smallcap100_daily.json"),
    ("JP", "jp_nikkei225", "broad", "^N225", "yfinance", False, "jp_nikkei225_daily.csv"),
    ("JP", "jp_topix_banks_etf", "banks", "1615.T", "yfinance", True, "jp_topix_banks_etf_daily.csv"),
    ("JP", "jp_mothers_etf", "smallcap", "1563.T", "yfinance", True, "jp_mothers_etf_daily.csv"),
    # --- Phase C ---
    ("CN", "cn_csi300", "broad", "000300", "csindex", False, "indices/cn_csi300_csindex.json"),
    ("CN", "cn_csi300_banks", "banks", "000951", "csindex", False, "indices/cn_csi300_banks_csindex.json"),
    ("CN", "cn_csi500", "smallcap", "000905", "csindex", False, "indices/cn_csi500_csindex.json"),
    ("GB", "gb_ftse100", "broad", "^FTSE", "yfinance", False, "indices/gb_ftse100_daily.csv"),
    ("GB", "gb_ftse_smallcap", "smallcap", "^FTSC", "yfinance", False, "indices/gb_ftse_smallcap_daily.csv"),
    ("FR", "fr_cac40", "broad", "^FCHI", "yfinance", False, "indices/fr_cac40_daily.csv"),
    ("IT", "it_ftsemib", "broad", "FTSEMIB.MI", "yfinance", False, "indices/it_ftsemib_daily.csv"),
    ("ES", "es_ibex35", "broad", "^IBEX", "yfinance", False, "indices/es_ibex35_daily.csv"),
    ("EA", "ea_emu_smallcap_etf", "smallcap", "SXRJ.DE", "yfinance", True, "indices/ea_emu_smallcap_etf_daily.csv"),
    ("RU", "ru_imoex", "broad", "IMOEX", "moex", False, "indices/ru_imoex_moex.json"),
    ("RU", "ru_moex_fin", "banks", "MOEXFN", "moex", False, "indices/ru_moex_fin_moex.json"),
    ("RU", "ru_moex_smid", "smallcap", "MCXSM", "moex", False, "indices/ru_moex_smid_moex.json"),
    ("CA", "ca_tsx", "broad", "^GSPTSE", "yfinance", False, "indices/ca_tsx_daily.csv"),
    ("CA", "ca_tsx_fin", "banks", "^SPTTFS", "yfinance", False, "indices/ca_tsx_fin_daily.csv"),
    ("CA", "ca_tsx_venture", "smallcap", "^SPCDNX", "yfinance", False, "indices/ca_tsx_venture_daily.csv"),
    ("BR", "br_ibov", "broad", "^BVSP", "yfinance", False, "indices/br_ibov_daily.csv"),
    ("BR", "br_ifnc", "banks", "IFNC", "b3", False, "indices/br_ifnc_b3.json"),
    ("BR", "br_smll", "smallcap", "SMLL", "b3", False, "indices/br_smll_b3.json"),
    ("MX", "mx_ipc", "broad", "^MXX", "yfinance", False, "indices/mx_ipc_daily.csv"),
    ("AU", "au_asx200", "broad", "^AXJO", "yfinance", False, "indices/au_asx200_daily.csv"),
    ("AU", "au_asx200_fin", "banks", "^AXFJ", "yfinance", False, "indices/au_asx200_fin_daily.csv"),
    ("AU", "au_small_ords", "smallcap", "^AXSO", "yfinance", False, "indices/au_small_ords_daily.csv"),
    ("KR", "kr_kospi", "broad", "^KS11", "yfinance", False, "indices/kr_kospi_daily.csv"),
    ("KR", "kr_banks_etf", "banks", "091170.KS", "yfinance", True, "indices/kr_banks_etf_daily.csv"),
    ("KR", "kr_kosdaq", "smallcap", "^KQ11", "yfinance", False, "indices/kr_kosdaq_daily.csv"),
]
SOURCE_NAME = {"yfinance": "yfinance", "niftyindices": "niftyindices.com", "csindex": "csindex.com.cn",
               "moex": "iss.moex.com", "b3": "b3.com.br"}
DROPPED: dict[str, int] = {}  # index_id -> zero-volume rows dropped on non-session days
COLS = ["date", "country", "index_id", "index_class", "ticker", "source", "level_local", "ret_local",
        "exdiv_flag", "stale_flag", "outlier_flag"]


def _frame(recs: list[dict]) -> pd.DataFrame:
    out = pd.DataFrame(recs).drop_duplicates("date")
    out["exdiv_flag"], out["stale_flag"] = 0, 0
    return out


def raw_yfinance(code: str, raw_file: str, is_etf: bool) -> pd.DataFrame:
    path = RAW_DIR / raw_file
    if not path.exists():
        import yfinance as yf
        hist = yf.Ticker(code).history(period="max", auto_adjust=False)
        if hist.empty:
            raise ValueError(f"No data returned for {code}")
        save_raw_file(hist.to_csv().encode("utf-8"), raw_file, source="Yahoo Finance (yfinance)",
                      url_or_api=f"yfinance:{code} history(period='max', auto_adjust=False)",
                      series_id=code, licence=YAHOO_TERMS,
                      notes=f"Daily OHLCV, unadjusted for dividends (is_etf={is_etf})")
    df = pd.read_csv(path)
    return pd.DataFrame({
        "date": pd.to_datetime(df["Date"].str[:10]).dt.date,
        "level_local": df["Close"].astype(float),
        "exdiv_flag": (df.get("Dividends", 0) > 0).astype("int8") if is_etf else 0,
        "stale_flag": (df["Volume"] == 0).astype("int8") if is_etf else 0,
        "volume": df["Volume"],
    })


def raw_niftyindices(name: str, raw_file: str) -> pd.DataFrame:
    path = RAW_DIR / raw_file
    if not path.exists():
        end = (dt.date.today() - dt.timedelta(days=1)).strftime("%d-%b-%Y")
        payload = {"cinfo": f"{{'name':'{name}','startDate':'01-Jan-1999','endDate':'{end}','indexName':'{name}'}}"}
        resp = requests.post(NIFTY_URL, json=payload, timeout=60, headers={
            **UA, "Content-Type": "application/json; charset=UTF-8",
            "Referer": "https://www.niftyindices.com/reports/historical-data"})
        resp.raise_for_status()
        save_raw_file(resp.content, raw_file, source="NSE Indices Ltd (niftyindices.com)",
                      url_or_api=f"POST {NIFTY_URL} cinfo name='{name}'", series_id=name,
                      licence=NSE_TERMS, notes="Official daily index values (price index close)")
    data = json.loads(path.read_bytes())
    if isinstance(data, dict) and "d" in data:
        data = json.loads(data["d"])
    recs = []
    for item in data:
        close = (item.get("CLOSE") or "").replace(",", "").strip()
        if close and close != "-":
            recs.append({"date": dt.datetime.strptime(item["HistoricalDate"].strip(), "%d %b %Y").date(),
                         "level_local": float(close)})
    return _frame(recs)


def raw_csindex(code: str, raw_file: str) -> pd.DataFrame:
    path = RAW_DIR / raw_file
    url = (f"https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode={code}"
           f"&startDate=19990101&endDate={(dt.date.today() - dt.timedelta(days=1)):%Y%m%d}")
    if not path.exists():
        for attempt in range(4):  # the CSI server is slow from outside China; retry with a pause
            try:
                resp = requests.get(url, headers=UA, timeout=240)
                resp.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(20)
        save_raw_file(resp.content, raw_file, source="China Securities Index Co. (csindex.com.cn)",
                      url_or_api=url, series_id=code, licence=CSI_TERMS,
                      notes="Official daily index values (price index close)")
    data = json.loads(path.read_bytes())["data"]
    return _frame([{"date": dt.datetime.strptime(r["tradeDate"], "%Y%m%d").date(), "level_local": float(r["close"])}
                   for r in data if r.get("close") is not None])


def raw_moex(code: str, raw_file: str) -> pd.DataFrame:
    """Moscow Exchange ISS history (100 rows per page); all pages saved as one raw file."""
    path = RAW_DIR / raw_file
    base = (f"https://iss.moex.com/iss/history/engines/stock/markets/index/securities/{code}.json"
            "?from=1999-01-01&iss.meta=off&history.columns=TRADEDATE,CLOSE")
    if not path.exists():
        pages, start = [], 0
        while True:
            resp = requests.get(f"{base}&start={start}", headers=UA, timeout=60)
            resp.raise_for_status()
            page = resp.json()
            pages.append(page)
            index, total, size = page["history.cursor"]["data"][0]
            start = index + size
            if start >= total:
                break
            time.sleep(0.2)
        save_raw_file(json.dumps(pages).encode("utf-8"), raw_file, source="Moscow Exchange ISS",
                      url_or_api=f"{base}&start=0..{start} (all pages)", series_id=code, licence=MOEX_TERMS,
                      notes=f"Official daily index values; {len(pages)} ISS pages concatenated")
    pages = json.loads(path.read_bytes())
    return _frame([{"date": dt.date.fromisoformat(d), "level_local": float(c)}
                   for page in pages for d, c in page["history"]["data"] if c is not None])


def raw_b3(code: str, raw_file: str) -> pd.DataFrame:
    """B3 index statistics (one call per year: day-of-month x month grid)."""
    path = RAW_DIR / raw_file
    api = "https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay/"
    if not path.exists():
        years = {}
        for year in range(2000, dt.date.today().year + 1):
            param = base64.b64encode(json.dumps({"index": code, "language": "en-us", "year": str(year)}).encode())
            resp = requests.get(api + param.decode(), headers=UA, timeout=60)
            resp.raise_for_status()
            years[year] = resp.json()
            time.sleep(0.2)
        save_raw_file(json.dumps(years).encode("utf-8"), raw_file, source="B3 S.A. index statistics",
                      url_or_api=f"{api}<base64 {{index:{code}, year}}> for 2000-{dt.date.today().year}",
                      series_id=code, licence=B3_TERMS, notes="Official daily closing values, one call per year")
    recs = []
    for year, payload in json.loads(path.read_bytes()).items():
        for day_row in payload.get("results") or []:
            for month in range(1, 13):
                value = day_row.get(f"rateValue{month}")
                if value:
                    recs.append({"date": dt.date(int(year), month, int(day_row["day"])),
                                 "level_local": float(value.replace(",", ""))})
    return _frame(recs)


READERS = {"niftyindices": raw_niftyindices, "csindex": raw_csindex, "moex": raw_moex, "b3": raw_b3}


def build_series(country, index_id, index_class, code, source, is_etf, raw_file) -> pd.DataFrame:
    df = raw_yfinance(code, raw_file, is_etf) if source == "yfinance" else READERS[source](code, raw_file)
    df = df[(df["date"] >= START) & (df["date"] < dt.date.today()) & (df["level_local"] > 0)]
    if source == "yfinance":
        # Yahoo inserts zero-volume placeholder rows on some exchange holidays; they are not prices.
        import exchange_calendars as xcals
        cal = xcals.get_calendar(CALENDARS[country], start="1999-01-01")
        sessions = {s.date() for s in cal.sessions_in_range(str(df["date"].min()), str(df["date"].max()))}
        placeholder = ~df["date"].isin(sessions) & (df["volume"] == 0)
        DROPPED[index_id] = int(placeholder.sum())
        df = df[~placeholder]
    df = df.sort_values("date").reset_index(drop=True)
    df["ret_local"] = np.log(df["level_local"] / df["level_local"].shift(1))
    df["outlier_flag"] = (df["ret_local"].abs() > OUTLIER).astype("int8")
    df["country"], df["index_id"], df["index_class"] = country, index_id, index_class
    df["ticker"] = code
    df["source"] = SOURCE_NAME[source]
    df[["exdiv_flag", "stale_flag"]] = df[["exdiv_flag", "stale_flag"]].astype("int8")
    return df[COLS]


def main() -> pd.DataFrame:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.concat([build_series(*spec) for spec in SERIES_SPEC], ignore_index=True)
    panel.to_parquet(INTERIM_DIR / "indices_daily.parquet", index=False)
    pilot = panel[panel["country"].isin(PILOT)].reset_index(drop=True)
    pilot.to_parquet(INTERIM_DIR / "pilot_indices_daily.parquet", index=False)
    pilot.to_csv(INTERIM_DIR / "pilot_indices_daily.csv", index=False)
    print("Zero-volume non-session rows dropped:", {k: v for k, v in DROPPED.items() if v})
    print(f"{panel['index_id'].nunique()} series, {len(panel)} rows -> {INTERIM_DIR / 'indices_daily.parquet'}")
    return panel


if __name__ == "__main__":
    main()
