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
events. In practice, RBI announcements on Indian trading days stay same-day for India
(baseline = previous day's close). The flag mainly hits Asian markets for Fed events of
unknown time and markets whose open or close falls inside a BoJ hour.
Revisit when Phase D adds exact Fed times (ISS-006).
