# MoTrans-15 — Dataset Build Specification

Source plan: `docs/MoTrans-15 14-Day Implementation Plan.pdf`

You are helping build the research dataset for "MoTrans-15: Monetary transmission to equities
across the 15 largest economies". Your job is ONLY the dataset: repo setup, data collection,
alignment, shock construction and the central-bank text corpus. Do NOT run any econometrics
or ML models.

## NON-NEGOTIABLE WORKING RULES

1. Work phase by phase (A → E below). At the end of each phase STOP, summarize what you built,
   show test results, list open problems, and wait for my approval before continuing.
2. Never fabricate, guess, or silently interpolate/forward-fill data. If a source fails,
   is paywalled, or its terms of service forbid scraping, log it in docs/issues.md and ASK me.
3. Never invent URLs, dataset names, or citations. Only use a source after you have actually
   opened it and confirmed it contains the series. Record the exact URL/API endpoint.
4. Every series carries provenance: source, URL/API, ticker/series ID, retrieval date (UTC),
   licence/terms, and every transformation applied.
5. No look-ahead: any value used for date t must have been publicly known at t.
6. data/raw/ is write-once and read-only after download. All cleaning goes to data/interim/
   and data/final/.
7. Free/public sources only (FRED, ECB Data Portal, BIS, OECD, IMF, national central banks
   and statistics offices, official exchange/index-provider sites, yfinance/Stooq as a
   fallback with that limitation documented). Do not scrape sites whose ToS prohibit it.
8. Log every design choice with a date in DECISIONS.md.

## LOCKED DESIGN (do not change without asking)

**Countries (15):** US, China, Germany, India, Japan, UK, France, Italy, Russia, Canada, Brazil,
Spain, Mexico, Australia, South Korea.

**Policy regimes / shock sources (12):** Fed, ECB (one shock source for DE, FR, IT, ES), PBoC,
BoJ, BoE, CBR, BoC, BCB, Banxico, RBA, BoK, RBI.

**Window:** 2000-01-01 (or earliest reliable date; ~2005 for some EMs) to latest available.
Tag the 2011+ robustness subsample.

**Frequency:** daily trading days, per-exchange calendars.

**Indices:** 3 per country — (1) broad market, (2) banks/financials, (3) small-cap or growth.
About 45 series in total. Candidate list below. VERIFY each one before using it, and propose
substitutes where no free daily history exists:

| Country | Broad | Banks / financials | Small-cap / growth |
|---|---|---|---|
| US | S&P 500 | S&P 500 Financials or KBW Bank | Russell 2000 |
| China | CSI 300 | CSI 300 Financials (or SSE Financials) | CSI 500 or ChiNext |
| Japan | TOPIX or Nikkei 225 | TOPIX Banks | TSE Growth / Mothers |
| Germany | DAX | euro-area bank index (NOT country-specific, so document this) or a German financials index | SDAX or MDAX |
| France | CAC 40 | French financials/banks | CAC Mid & Small |
| Italy | FTSE MIB | FTSE Italia Banks | FTSE Italia Small Cap / STAR |
| Spain | IBEX 35 | Spanish banks index | IBEX Small Cap |
| UK | FTSE 100 | FTSE 350 Banks | FTSE 250 or FTSE SmallCap |
| India | Nifty 50 | Nifty Bank | Nifty Smallcap 100 |
| Russia | MOEX Russia | MOEX Financials | MOEX SMID |
| Canada | S&P/TSX Composite | TSX Financials | TSX SmallCap |
| Brazil | Ibovespa | IFNC | SMLL |
| Mexico | S&P/BMV IPC | Mexican financials (verify) | small/mid-cap (verify) |
| Australia | S&P/ASX 200 | ASX 200 Financials | Small Ordinaries |
| South Korea | KOSPI | KRX Banks | KOSDAQ |

**Returns:** daily log returns of the local-currency PRICE index (primary). Also store USD
returns (using daily FX) for robustness. Store raw levels too.

**Russia:** add flag `russia_post_feb2022` = 1 from 2022-02-24 onward (sanctions, trading halts
and capital controls). Explicitly mark every trading-halt period, because those are missing
data, not zero returns.

**Shocks:**
- US: public high-frequency monetary policy surprise series (find a maintained, citable one
  and extend it to the latest FOMC meeting if possible; document exactly how).
- Euro area: the Euro Area Monetary Policy Event-Study Database (EA-MPD) or an equivalent
  public series.
- All other regimes: change in the 1-year government bond yield on the announcement day
  (a proxy). If a daily 1-year yield isn't freely available, propose the closest
  alternative (e.g. 2-year yield or a short-tenor OIS/interbank rate), log it and ASK.
- Standardize each shock within its own source (unit = 1 SD of that source).
- Include every decision: hikes, cuts AND holds, including unscheduled/emergency meetings.
- Give every regime a shock-quality grade: A = clean public surprise series,
  B = reasonable proxy, C = weak (descriptive use only). Write down why each grade was given.

**Timing rule (critical):** map each decision to its exact announcement timestamp and time zone,
handling DST. Then map it to the FIRST trading session of EACH exchange that can react to it.
Example: an FOMC decision at 14:00 ET reaches Tokyo, Mumbai and Seoul on the NEXT local
trading day, but reaches US markets the same day. If the announcement comes after a market's
close, use that market's next session. Use exchange calendars (e.g. exchange_calendars or
pandas_market_calendars) and verify the holidays.

**Sample split tags (labels only, no modelling):** train = up to 2019-12-31;
crisis = 2020-01-01 to 2021-12-31; blind_test = 2022-01-01 onward.

## PHASE A — Repo and documentation setup

Create:
- `data/raw`, `data/interim`, `data/final`, `src/`, `tests/`, `notebooks/`, `docs/`, `outputs/`
- a pinned environment file (requirements.txt with exact versions, or environment.yml),
  using a Python 3.12 virtual environment in `.venv`
- a task runner (Makefile or a Python CLI) so `make data` rebuilds everything from raw
- `docs/source_registry.md` — one row per variable: source, URL/API, access method, coverage,
  known gaps, licence
- `docs/data_dictionary.md` — every column: name, type, unit, definition, source
- `DECISIONS.md` — dated log
- `docs/issues.md` — failed sources, substitutions, open questions

STOP for approval.

## PHASE B — Pilot: US, Germany/Euro area, India, Japan

1. Policy decisions for the Fed, ECB, RBI and BoJ: date, exact announcement time + time zone,
   decision (hike/cut/hold), size in bp, new rate, scheduled vs unscheduled, source URL.
2. The 3 indices per pilot country → daily levels and log returns.
3. `src/alignment.py`: announcement → first reacting session per exchange.
4. `src/event_windows.py`: cumulative returns over 1, 3, 5, 20 and 60 trading days after the
   reacting session (plus a pre-event window for later placebo use).
5. Unit tests in `tests/` covering at least 5 known events per market, including the
   2022-03-16 FOMC hike, the March 2020 emergency Fed cuts (03-03 and 03-15, a Sunday),
   the 2013 taper-tantrum period, and one BoJ decision with an irregular release time.
6. Produce a hand-check sheet of 10 events (announcement time, mapped session per market,
   returns) with source links, so I can verify them manually.

STOP. Do not scale up until I confirm that the hand-check passes.

## PHASE C — Full dataset (15 countries, ~45 indices) and controls

1. Extend to all countries in batches of 3–4, running data checks after each batch.
2. Controls (daily where possible, otherwise the native frequency with a release-date-aware
   lag): 1-year government yield, FX vs USD, a volatility measure (implied vol index where
   available, otherwise realized vol from the broad index), CPI, a growth indicator
   (industrial production or GDP), and a valuation proxy (P/E or earnings yield where freely
   available; log gaps). For low-frequency macro data, use only values released before date t.
3. For each index, record: start date, gaps, outliers (flag |daily log return| > a set
   threshold for review, do not delete), rebasings and substitutions.
4. Outputs:
   - `data/final/panel_daily.parquet` — long format: date, country, index_id, index_class,
     level_local, ret_local, ret_usd, controls..., split_tag, russia_post_feb2022, halt_flag
   - `data/final/events.parquet` — one row per (decision × reacting index): event_id,
     regime, announce_ts_utc, reacting_session_date, decision, shock_std, shock_grade,
     car_1, car_3, car_5, car_20, car_60, split_tag
   - `outputs/data_quality_report.html` (or .md) — coverage heatmap by country/index/year,
     missing dates, outliers, substitutions and Russia halts

STOP for approval.

## PHASE D — Shock construction

1. Load and extend the US and euro-area public surprise series.
2. Build the 1-year-yield-change proxy for the other 10 regimes on decision days, using the
   same timing logic (yield-market session).
3. Standardize each shock within its source. Assign grades A/B/C with written reasons.
4. Validate against known episodes (the 2022 Fed hikes, the 2013 taper tantrum, ECB
   2011/2022 hikes, March 2020) and plot the shocks over time per regime.
5. Output `data/final/shocks.parquet` plus `docs/shock_validation.md`.

STOP for approval.

## PHASE E — Central-bank text corpus (collection only)

1. Collect the official English-language policy statements / press releases for each
   decision (Fed, ECB, BoE, BoJ, RBI, and others where English statements exist; check BoC,
   RBA, BoK, BCB, Banxico, CBR, PBoC). Optionally add BIS central bankers' speeches where
   they align easily with a decision.
2. Store the raw text plus metadata: regime, decision date, publication timestamp, URL,
   language, retrieval date.
3. Align each statement to its event_id.
4. Output `data/final/statements.parquet` and a coverage table (regime × year) that honestly
   shows the gaps.
5. Build a stratified random sample of 150–200 statements (by regime and hike/cut/hold)
   exported to `docs/hand_label_sample.csv` with empty label columns: hawkish_dovish,
   inflation_concern, growth_concern, uncertainty, forward_guidance_shift.
   Do NOT fill in the labels — humans will do that.

STOP and give a final summary: coverage per country, grade per regime, every substitution,
and every open issue.
