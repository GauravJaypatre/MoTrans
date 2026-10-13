# Decision Log — MoTrans-15

All design choices are logged here with dates. Changes to locked design
decisions require explicit approval.

---

## 2026-10-12

### DECISION-001: Repository structure

- Adopted the directory layout specified in `docs/PROJECT_SPEC.md` §Phase A.
- `data/raw/` is write-once; all transformations go to `data/interim/` and
  `data/final/`.
- `tasks.py` chosen as the task runner (Python-native, no external `make`
  dependency on Windows).

### DECISION-002: Python environment

- Python 3.12.4 (existing `.venv`).
- Direct dependencies listed in `requirements.in` (minimum versions).
- Full lock file in `requirements.txt` via `pip freeze` (includes transitive
  dependencies).
- `pymupdf` excluded from project requirements (used only for one-time PDF
  extraction during setup).

### DECISION-003: Data exclusion from version control

- Everything under `data/raw/` is git-ignored via `data/raw/*`, with explicit
  exceptions for `data/raw/.gitkeep` and `data/raw/MANIFEST.csv`.
- `data/interim/`, `data/final/`, and `outputs/` are git-ignored (regenerable
  via `python tasks.py data`).
- `MANIFEST.csv` is tracked to provide provenance for every raw file download.

### DECISION-004: Write-once raw data and provenance manifest

- All downloads to `data/raw/` must go through `src.download.save_raw_file()`.
- That function refuses to overwrite existing files (`FileExistsError`) and
  automatically appends a row to `data/raw/MANIFEST.csv` with: file_path,
  source, url_or_api, series_id, retrieval_utc, licence, sha256, notes.

### DECISION-005: Sample split boundaries

- `train`: up to 2019-12-31.
- `crisis`: 2020-01-01 to 2021-12-31.
- `blind_test`: 2022-01-01 onward.
- Implemented in `src.split_tag()` and verified by `tests/test_smoke.py`.

### DECISION-006: Cumulative return naming convention

- Event-window returns are called "cumulative log returns" (e.g. `clr_1`,
  `clr_3`, `clr_5`, `clr_20`, `clr_60`), NOT "cumulative abnormal returns"
  (CAR), because no benchmark model has been chosen at this stage.

### DECISION-007: Russia halt_flag sourcing

- The list of Russian equity trading halt dates must come from cited,
  verifiable sources (e.g. MOEX official announcements, press releases).
- Sources will be recorded in `docs/source_registry.md`.
- No halt dates are entered from memory or guesswork.

### DECISION-008: Phase A completion fixes

- `tasks.py` output made ASCII-only: the original Unicode symbols crashed every
  task on the default Windows console (cp1252).
- Ruff auto-fixes applied (import ordering, `datetime.UTC`); `ruff check` clean.
- Lock file `requirements.txt` generated with a full `pip freeze`. Resolved
  versions include pandas 3.0.6, numpy 2.5.4, yfinance 1.7.0,
  exchange_calendars 4.13.2, pandas_market_calendars 5.5.0. pandas 3.x is new;
  if a dependency breaks in Phase B, pinning `pandas<3` is the first fallback
  (log it here if used).

---

## 2026-10-13 — Phase B1 (pilot data: US, euro area/DE, India, Japan)

### DECISION-009: Pilot equity series
Chosen by the project lead from the options table (see docs/issues.md for coverage losses):

| Market | Broad | Banks | Small-cap |
|---|---|---|---|
| US | S&P 500 `^GSPC` | KBW Bank `^BKX` (replaces XLF, an ETF) | Russell 2000 `^RUT` |
| DE | DAX `^GDAXI` | iShares EURO STOXX Banks 30-15 ETF `EXX1.DE` (2008+); DAXsector Banks `^CXPBX` (2013+) kept as robustness | MDAX `^MDAXI` |
| IN | NIFTY 50 (niftyindices.com) | NIFTY BANK (niftyindices.com) | NIFTY Smallcap 100 (niftyindices.com) |
| JP | Nikkei 225 `^N225` | NEXT FUNDS TOPIX Banks ETF `1615.T` (2008+) | TSE Mothers ETF `1563.T` (2011+) |

- India series moved from Yahoo (2007+) to the official NSE Indices source (2000+).
- Prices are closes with `auto_adjust=False` (price, not total return).
- ETF rows carry `exdiv_flag` (ex-dividend day) and `stale_flag` (zero traded volume).
- Yahoo zero-volume rows on exchange holidays are dropped as placeholders (count logged).

### DECISION-010: Policy decisions are rebuilt only from saved official documents
The first B1 collector (Antigravity/Gemini) hard-coded ~140 RBI decisions, the ECB
2024-2026 meeting dates, all emergency meetings and the BoJ "exact" times from memory.
It was rewritten so every row is parsed from files in data/raw (see module docstring
of src/collect_policy.py). Rate changes that do not match a listed meeting are kept as
`unscheduled_rate_change` rows and logged, never re-dated by hand.

### DECISION-011: Policy rate and size convention per regime
- Fed: target rate; upper bound of the target range from 16 Dec 2008 (openmarket.htm).
- ECB: MRO (fixed rate, or minimum bid rate during variable-rate tenders 28 Jun 2000 -
  14 Oct 2008) until 17 Sep 2024; deposit facility rate from 18 Sep 2024. Source for the
  switch: BIS WS_CBPOL euro-area compilation note ("From 18 Sep 2024 onwards: official
  central bank steering rate is the deposit facility rate"). All three rates are stored.
- RBI: repo rate from 3 Apr 2001, bank rate before (BIS WS_CBPOL IN).
- BoJ: BIS WS_CBPOL JP policy rate. In the quantity-target periods the rate is flat, so
  QE/YCC decisions are classified "hold" by rate; the shock series (Phase D) must
  capture them.
- `size_bp` = change in that rate attributed to the decision.

### DECISION-012: Announcement-time rules
- Fed: "For release at ..." from each statement page = exact. Older pages say "For
  immediate release": scheduled meetings before 27 Apr 2011 get 14:15 ET (approximate,
  to verify in Phase D); unscheduled ones are unknown.
- ECB: 13:45 CET until June 2022, 14:15 CET from July 2022, from the EA-MPD notes.
- RBI: no time on source pages, so unknown (open issue for B2).
- BoJ: meeting end time from the MPM minutes = approximate release time; unknown where
  minutes are not yet published.

### DECISION-013: Matching events with unknown or approximate times to sessions (2026-10-13)
Every event gets an announcement window `[window_start_utc, window_end_utc]`, the earliest
and latest moment it could have been released, sized by what the sources tell us:

| time_quality | Window | Basis |
|---|---|---|
| exact | the stated time (a point) | statement page / EA-MPD release schedule |
| approximate, BoJ | meeting end → +60 min | minutes give the meeting end; the release follows it (60 min is a conservative assumption) |
| approximate, Fed (pre-Apr 2011) | 14:15 ET ± 15 min | assumed standard schedule |
| unknown (RBI, Fed 2011-15, some unscheduled) | the whole announcement date, 00:00-23:59 in the central bank's local time | no information, so no assumption |

Phase B2 timing rule, for each event and each exchange:
1. **Baseline** = close of the last session that closed **at or before `window_start`**.
   Nothing after the baseline can contain the announcement, so there is no look-ahead.
2. **Reacting session** = the first session whose close is **after `window_start`**.
   This is the earliest session that could react, so no reaction is missed.
3. `clr_h` = log(close of reacting session + h − 1) − log(baseline close); `clr_pre5`
   ends at the baseline.
4. **`timing_ambiguous` = 1** if using `window_end` instead would give a different
   reacting session for that exchange (an open or close falls inside the window). For these
   rows `clr_1` may include pre-announcement movement or miss the reaction, so headline
   results use h ≥ 3 for them, and every analysis is repeated without them as robustness.

Why: a wrong guess of the time either leaks future information (if too early) or misses
the reaction (if too late). Widening the window and measuring from before its start
never leaks information, and at worst adds noise on short horizons, which is flagged and
testable. Exact times keep the precise rule, so nothing changes for the well-timed
events. In practice (Phase B2 results): RBI announcements on Indian trading days still
react the same day in India (baseline = previous close), but because RBI times are
unknown nearly all RBI rows (~95%) are flagged `timing_ambiguous`; ~21% of Fed rows
(2011-15 and some unscheduled actions) are flagged; ECB rows never and BoJ rows rarely.
Correction (2026-10-13): an earlier draft said RBI rows would stay unflagged for India.
Revisit when Phase D adds exact Fed times (ISS-006).

---

## 2026-10-13 — Phase B2 (timing rule and event windows)

### DECISION-014: Event-window construction
- One row per (policy event × pilot series), for all four regimes and all 13 series, so
  cross-market responses (e.g. Fed → Japan) are available; `home_market` = 1 marks the
  regime's own market (Fed→US, ECB→DE, RBI→IN, BoJ→JP).
- Session timing uses exchange calendars (`src/alignment.py`); prices use each index's own
  observations, so `clr_h` spans h index observations from the reacting one. If the index
  has no value on the reacting session the next observation is used and
  `react_obs_gap` = 1 (0 cases in the pilot).
- `announce_in_session` = 1 when the window starts while that market is open (the day's
  close already partly reflects pre-announcement trading).
- ETF rows carry `stale_on_react` and `exdiv_in_clr5` so those observations can be
  excluded.
- Horizons that run past the last available observation are left empty, never filled.
- Output is `data/interim/pilot_events.parquet`; `data/final/events.parquet` is built in
  Phase C once all 15 countries are in.

### GATE-B: Phase B hand-check passed (2026-10-13)
Prachi verified all 10 events x 4 broad indices in `docs/phase_b_hand_check.xlsx`
against the official announcements and price histories: date/time, baseline and
reacting sessions, and both closing prices - 160/160 checks "Yes". The timing rule
(DECISION-013) is accepted; Phase C (full 15-country dataset) may start.
`src/hand_check.py` will not overwrite a signed workbook.

---

## 2026-10-13 — Phase C (full dataset: 15 countries, controls)

### DECISION-015: Full equity series list (38 series)
- Official sources preferred over Yahoo where Yahoo has no history: China (CSIndex: CSI 300,
  CSI 300 Banks, CSI 500), Russia (Moscow Exchange ISS: MOEX Russia, MOEX Financials, MOEX
  SMID), Brazil sector/small-cap (B3: IFNC, SMLL), India (NSE Indices, from Phase B).
- Euro area: no free country-level bank or small-cap index exists for FR/IT/ES, so they share
  euro-area series: banks = `EXX1.DE` (the pilot's DE banks ETF), small-cap = MSCI EMU Small
  Cap ETF `SXRJ.DE` (2009+), stored once with country code `EA`. ECB home markets are
  DE, FR, IT, ES and EA. Shared series are counted once, never duplicated per country.
- Dropped (no free daily source): UK banks (FTSE 350 Banks), Mexico banks and small-cap.
- Canada small-cap uses the S&P/TSX Venture Composite (growth/small proxy; TSX SmallCap not free).
- Korea banks uses the KODEX Banks ETF (2007+); Australia financials the ASX 200 Financials
  index (2013+).

### DECISION-016: Controls and look-ahead rules
- Daily controls (FX, policy rate, 1-year yield) are usable from their observation date;
  monthly macro (CPI, industrial production) for month m from the first day of month m+2,
  because free sources carry no release calendars (conservative fixed lag).
- No stale carry-forward: a daily value older than 7 days, or a monthly value older than 62
  days past its availability date, is left empty. (This fixed an as-of merge that had carried
  Brazil's 2019 yield forward to 2026 - caught in review before commit.)
- 1-year yield sources: US Treasury, Bundesbank (DE), ECB euro-area 1Y spot (FR/IT/ES/EA proxy),
  MoF Japan, Bank of England spot curve (GB), Bank of Canada 2-year benchmark (CA; 1-year bills
  are weekly), Bank of Russia zero-coupon curve (RU), BCB swap DI 360 (BR, ends Sep 2019).
- Volatility: 20-day realised volatility of the country's broad index for all markets (EA uses
  the DAX); VIX as implied volatility for the US only.
- `ret_usd` = local log return minus the change in log(local currency per USD), BIS daily FX.

### DECISION-017: Decisions for the eight Phase C regimes
- Rate changes for all eight from BIS WS_CBPOL (same source as RBI/BoJ), excluding level jumps
  on definition switches (BIS notes: CN 2019 LPR, RU 2013 key rate, KR 2008, GB 2006),
  sub-0.5 bp data noise (seen in the BIS AU series) and Mexico before its target rate (21 Jan 2008).
- Holds are included only where an official meeting list was readable: BCB (Copom API) and
  Banxico (announcement list). BoE, BoC, RBA, BoK, CBR: rate changes only; PBoC has no meetings.
- No source states release times for these regimes, so all use whole-day windows (DECISION-013).

---

## 2026-10-13 — Phase D (shock construction)

### DECISION-018: Shock sources, grades and standardisation
- Fed (grade A): FRBSF update of Bauer and Swanson (2023), `MPS` = first principal component of
  30-minute futures-rate changes around FOMC announcements, to Dec 2023 (in bp).
- ECB (grade A): EA-MPD (Altavilla et al. 2019), 1-year OIS change in the monetary event window
  (press release + press conference), to Oct 2023 (in bp).
- All regimes (grade B proxy): change in the home 1-year yield from the baseline close to the
  reacting-session close, using the DECISION-013 session rule on the home market (euro area:
  ECB euro-area curve on Xetra sessions). Left empty when the yield is more than 5 days stale.
- Grade C: no high-frequency surprise and no usable yield -> `shock_std` empty (descriptive use).
- `shock_std` = raw / SD of the same source over training-period events (to 2019), per regime.
  Using the training SD keeps the 2022+ blind test out of the scaling. Not de-meaned, so zero
  still means "no surprise". Both the HF and the proxy shock are stored for every event.
- Validation (docs/shock_validation.md): HF vs proxy correlation 0.55 (Fed) and 0.61 (ECB);
  2020 emergency cuts strongly negative, 2022 Fed and ECB hikes strongly positive; the 15 largest
  shocks are all recognisable episodes (9/11, CBR Dec 2014, BoJ Jul 2024, Brazil 2002, ...).
- The FRBSF file also gives FOMC announcement times; they now fill the Fed release times that
  statement pages do not state (226 of 227 Fed decisions exact; resolves ISS-006). The signed
  Phase B hand-check workbook keeps its sign-off-time values (one row, fed_2013-06-19, was
  "unknown" then and is 14:00 ET now; its session mapping for the US is unchanged).
