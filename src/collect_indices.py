"""Daily levels and log returns for the pilot equity series (US, Germany, India, Japan).

Raw-first: each series is downloaded once through save_raw_file() (write-once, logged in
MANIFEST.csv) and the panel is always rebuilt from the saved raw file, so a re-run
reproduces the same panel. Delete a raw file by hand only to deliberately refresh it.

Columns: unadjusted close (auto_adjust=False), ret_local = ln(P_t / P_{t-1}),
exdiv_flag (ETF ex-dividend day, from the raw Dividends column), stale_flag (ETF day
with zero traded volume, so the close is not a fresh price), outlier_flag (|ret| > 0.10).
The current (possibly still trading) day is excluded.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from src.download import RAW_DIR, save_raw_file

INTERIM_DIR = Path(__file__).resolve().parent.parent / "data" / "interim"
CALENDARS = {"US": "XNYS", "DE": "XETR", "IN": "XBOM", "JP": "XTKS"}
START = dt.date(2000, 1, 1)
OUTLIER = 0.10
YAHOO_TERMS = "Yahoo Finance terms of service (personal/research use; no redistribution)"
NSE_TERMS = "NSE Indices Limited website terms of use (no redistribution of data)"
NIFTY_URL = "https://www.niftyindices.com/BackPage/getHistoricaldatatabletoString"

# (country, index_id, index_class, code, source, is_etf, raw_file)
SERIES_SPEC = [
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
]
DROPPED: dict[str, int] = {}  # index_id -> zero-volume rows dropped on non-session days
COLS = ["date", "country", "index_id", "index_class", "ticker", "source", "level_local", "ret_local",
        "exdiv_flag", "stale_flag", "outlier_flag"]


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
    out = pd.DataFrame({
        "date": pd.to_datetime(df["Date"].str[:10]).dt.date,
        "level_local": df["Close"].astype(float),
        "exdiv_flag": (df.get("Dividends", 0) > 0).astype("int8") if is_etf else 0,
        "stale_flag": (df["Volume"] == 0).astype("int8") if is_etf else 0,
        "volume": df["Volume"],
    })
    return out


def raw_niftyindices(name: str, raw_file: str) -> pd.DataFrame:
    path = RAW_DIR / raw_file
    if not path.exists():
        end = (dt.date.today() - dt.timedelta(days=1)).strftime("%d-%b-%Y")
        payload = {"cinfo": f"{{'name':'{name}','startDate':'01-Jan-1999','endDate':'{end}','indexName':'{name}'}}"}
        resp = requests.post(NIFTY_URL, json=payload, timeout=60, headers={
            "User-Agent": "Mozilla/5.0", "Content-Type": "application/json; charset=UTF-8",
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
    out = pd.DataFrame(recs).drop_duplicates("date")
    out["exdiv_flag"], out["stale_flag"] = 0, 0
    return out


def build_series(country, index_id, index_class, code, source, is_etf, raw_file) -> pd.DataFrame:
    df = raw_yfinance(code, raw_file, is_etf) if source == "yfinance" else raw_niftyindices(code, raw_file)
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
    df["source"] = "yfinance" if source == "yfinance" else "niftyindices.com"
    df[["exdiv_flag", "stale_flag"]] = df[["exdiv_flag", "stale_flag"]].astype("int8")
    return df[COLS]


def main() -> pd.DataFrame:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.concat([build_series(*spec) for spec in SERIES_SPEC], ignore_index=True)
    panel.to_parquet(INTERIM_DIR / "pilot_indices_daily.parquet", index=False)
    panel.to_csv(INTERIM_DIR / "pilot_indices_daily.csv", index=False)
    print("Zero-volume non-session rows dropped:", {k: v for k, v in DROPPED.items() if v})
    print(f"{panel['index_id'].nunique()} series, {len(panel)} rows -> {INTERIM_DIR / 'pilot_indices_daily.parquet'}")
    return panel


if __name__ == "__main__":
    main()
