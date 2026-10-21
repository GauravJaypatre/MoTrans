# MoTrans-15 Dataset Changelog

All modifications are applied at the pipeline code level (`src/`), never by hand-editing
output files. The original workbook `data/final/MoTrans15_all_records.xlsx` is untouched.
The cleaned output is `data/final/MoTrans15_v2.xlsx`.

## [v2.1.0-pg2] — 2026-10-21  Priority Group 2 (Monetary policy shocks: sovereign yield proxies & usability)

### Problem addressed

In the initial audit of `MoTrans15_all_records.xlsx`:
- 640 policy decisions across five central banks (Banxico, BoK, PBoC, RBA, RBI) lacked shocks (`shock_grade == "C"`, `shock_std` missing).
- No explicit `shock_usable` flag existed to distinguish clean, usable shocks from unshocked or weak proxies without silent row deletion.
- In zero-rate/quantitative easing regimes (notably Japan's ZIRP and YCC era), daily 1-year sovereign yield changes had near-zero variance during the 2000–2019 training window (SD = 1.13 bp), causing post-2022 policy adjustments to produce outsized standardised shocks (e.g., +8.02 SD on 2024-07-31).

### Fixes implemented (DECISION-021)

1. **Sovereign Yield Data Sourcing**:
   - **Australia (RBA)**: Official Reserve Bank of Australia Table F2 ("Capital Market Yields - Government Bonds - Daily - 2-year yield", series `FCMYGBAG2D`) sourced from `rba.gov.au/statistics/tables/xls/f02dhist.xls` (1995–2013) and `f2-data.csv` (2013–2026). Yields added to `src/collect_controls.py::y_au()` and controls long parquet.
   - **China (PBoC)**: Official ChinaBond 2-year sovereign benchmark yield (`中国国债收益率2年`) sourced via `akshare.bond_zh_us_rate()` / Eastmoney (6,193 daily observations from 2002 to 2026). Added to `src/collect_controls.py::y_cn()` and controls long parquet.
   - **ECB EA-MPD**: Updated `src/build_shocks.py` to auto-fetch official `Dataset_EA-MPD.xlsx` from ECB if not present in cache.

2. **Yield-Change Proxies Built (Grade B)**:
   - Built standardized yield-change proxies ($\Delta y$) for RBA and PBoC around announcement windows.
   - PBoC: 40 of 40 events upgraded from Grade C to Grade B (training SD = 2.45 bp).
   - RBA: 71 of 72 events upgraded from Grade C to Grade B (training SD = 4.39 bp; 1 event on 2013-08-07 remains Grade C due to a 5-day publication gap during RBA's Table F2 transition).
   - Rate change size (`size_bp`) is **never** used as a substitute for shock surprise (strictly enforced per Rule 1 and PG2 rules).

3. **Adherence to Rule 1 for Unsourceable Regimes**:
   - Banxico (Mexico, 238 events): Secondary market yield data is paywalled / gated behind Banxico's captcha-protected SIE API.
   - BoK (South Korea, 60 events): BoK ECOS API requires authenticated developer keys (sample key limited to 10 rows); KRX OTC requires subscription login.
   - RBI (India, 163 events): CCIL ZCYC requires registered login; RBI DBIE provides only monthly/month-end SGL transaction averages.
   - Per Non-Negotiable Rule 1, these 461 events were **not** fabricated or interpolated from memory. They honestly remain Grade C with `shock_usable = 0`.

4. **New Columns**:
   - `shock_usable` (int8, 0/1): Set to 1 if `shock_grade` is A or B and `shock_std` is finite and non-null; 0 for Grade C.
   - `shock_primary` (int8, 0/1): Set to 1 for clean analysis cases; 0 for BoJ ZIRP/YCC ($\le 2024-03-18$), CBR post-Feb 2022 ($\ge 2022-02-24$), and China PBoC (pending 2Y proxy caveats).
   - `shock_std_w` (float64): Winsorized standardized shock, strictly capped at `[-4.0, +4.0]` standard deviations. Raw `shock_std` is untouched.
   - `shock_proxy_tenor` (str): Explicitly records proxy maturity (`1Y` for US, EA, JP, GB, RU, BR; `2Y` for AU, CN, CA; empty for unshocked).
   - `shock_quality_flag` (str): Detailed caveats (`low_sensitivity_zero_lower_bound`, `structural_break_ukraine_sanctions`, `tenor_2y_proxy_policy_transmission`).
   - AU and CN 2-year sovereign yields renamed to `yield_2y` in `controls_long` (never conflated with `yield_1y`).

5. **Sample Split Usability Breakdown & Low-Event Flags**:
   Regimes with fewer than 20 primary events in `blind_test` ($\ge 2022$) are flagged:
   - BoC: 19 primary events (flagged < 20)
   - BoE: 19 primary events (flagged < 20)
   - RBA: 19 primary events (flagged < 20)
   - CBR: 1 primary event (flagged < 20; structural break 2022-02-24)
   - PBoC: 0 primary events (flagged < 20; 2Y proxy transmission caution)
   - BCB: 0 primary events (flagged < 20; SGS 7806 ended Sep 2019)
   - Banxico: 0 primary events (flagged < 20; gated)
   - BoK: 0 primary events (flagged < 20; gated)
   - RBI: 0 primary events (flagged < 20; gated)
   - Note on BoJ: 21 post-ZIRP exit events ($\ge 2024-03-19$) in blind test.

### Quantitative Before / After

| Metric | Before (MoTrans15_all_records.xlsx) | After (MoTrans15_v2.xlsx) | Change |
|---|---|---|---|
| Grade A shocks | 487 (Fed 201, ECB 286) | **487** (Fed 201, ECB 286) | 0 |
| Grade B shocks | 781 | **892** | +111 (RBA +71, PBoC +40) |
| Grade C shocks | 640 | **529** | −111 |
| Total decisions with `shock_usable == 1` | 0 (column absent) | **1,379** (72.27%) | +1,379 |
| Total decisions with `shock_primary == 1` | 0 (column absent) | **837** (43.87%) | +837 |
| Events with \|shock_std\| > 5 SD | 7 | **7** (raw preserved) | 0 |
| Events with \|shock_std_w\| capped at 4.0 | 0 | **15** (8 at +4, 7 at -4) | +15 |
| BoJ events flagged `low_sensitivity_zero_lower_bound` | 0 | **318** | +318 |
| Events sheet rows deleted | 0 | 0 | 0 (Rule 2 maintained) |

### Tests Added
- [`tests/test_priority_group_2_shocks.py`](tests/test_priority_group_2_shocks.py): 11 tests covering `shock_usable`, `shock_primary`, `shock_std_w` bounds, `shock_proxy_tenor`, `yield_2y` control separation, prevention of size-based shock imputation, proxy grade assignments, gated regime retention, merge consistency, blind-test counts, and Japan ZIRP quality flags.

---

## [v2.0.0-pg1] — 2026-10-18  Priority Group 1 (Timing: conservative reaction-session rule)

### Problem addressed

The baseline DECISION-013 rule constructed announcement windows using the whole local day
of `decision_date` when the time was unknown: `window_start` = 00:00 local time, `window_end`
= 23:59 local time. For Asian central banks (BoJ, BoK, PBoC, RBA, RBI), 00:00 local time
maps to the **afternoon or evening of `decision_date − 1` in UTC**. The original alignment
code picked the reacting session as the first session closing *after `window_start`*, so
Western markets (US, Canada, Brazil, Mexico) whose sessions close on `decision_date − 1` in
UTC—but strictly after that UTC midnight—were matched as the reacting session for that
decision. The reacting session date was therefore `decision_date − 1`, i.e. one calendar day
**before** the decision. This creates noise in 1-day event-window returns for rows already
flagged `timing_ambiguous`, because the baseline and the "reacting" session are both chosen
from the pre-decision day.

Quantitative impact in `MoTrans15_all_records.xlsx` (events sheet):
- Rows where `reacting_session_date < decision_date`: **4,467 (7.15%)**
- Rows with `timing_ambiguous == 1`: **32,403 (51.88%)**
- Rows with `time_quality == "unknown"`: **34,896 (55.87%)**
- Column `analysis_ready_timing`: **not present**

### Fix: conservative reaction-session rule (DECISION-020)

**File changed:** [`src/alignment.py`](src/alignment.py)

When `time_quality == "unknown"` (or when the window is wider than 6 hours and no quality
is supplied), the reacting session is now defined as the first session whose close is
strictly **after `window_end`** (the latest possible announcement time):

```
react_idx = j = np.searchsorted(closes, window_end_utc, side="right")
```

This guarantees that no session that could conceivably have closed before the announcement
is ever labelled the reacting session. The baseline (last close at or before `window_start`)
is unchanged. The rule applies only to unknown-time rows; exact and approximate rows use the
original `i = np.searchsorted(closes, window_start, side="right")`.

The `time_quality` parameter is passed through `src/event_windows.py` and
`src/build_shocks.py` to `align()`.

### New column: `analysis_ready_timing`

Added to `policy_decisions.csv` and `events.parquet`.
Definition (in `src/event_windows.py`):

```python
analysis_ready_timing = (
    (timing_ambiguous == 0) &
    (time_quality.isin(["exact", "approximate"])) &
    (reacting_session_date >= decision_date)
).astype(int)
```

Rows with `analysis_ready_timing == 0` are **not deleted**; they are kept and the flag is
the explicit, reversible exclusion criterion (DECISION-020).

### Announcement times: status

Fed, ECB and BoJ announcement times are sourced from saved files in `data/raw/` and are
unchanged from the original pipeline.

Announcement times for the remaining 9 regimes (BoE, BoC, RBA, BoK, Banxico, BCB, CBR,
PBoC, RBI) have **not yet been sourced from saved files**. All 9 regimes retain
`time_quality = "unknown"` and `time_source = "Not yet sourced (pending official page)"`.
The conditional structure in `src/collect_policy_more.py::regime_announcement_time()` and
`src/collect_policy.py::harvest_rbi()` is kept so that verified times can be added when the
corresponding official pages are saved to `data/raw/` (see ISS-029).

### Updated export target

`src/export_excel.py` writes to `data/final/MoTrans15_v2.xlsx`; the original
`MoTrans15_all_records.xlsx` is never opened or written.

### Quantitative before / after (events table, 62,461 rows)

Measured on the rebuilt data (2026-10-20). "Before" applies the old DECISION-013 rule to the
same rows, so both columns describe identical events.

| Metric | Before (old rule) | After (`MoTrans15_v2.xlsx`) | Change |
|---|---|---|---|
| Rows deleted | — | — | 0 |
| `reacting_session_date < decision_date` | 4,467 (7.15 %) | **0 (0.00 %)** | −4,467 |
| Rows whose reacting session moved (unknown-time rows) | — | 32,301 | new rule |
| `timing_ambiguous == 1` | 32,402 (51.88 %) | 32,402 (51.88 %) | unchanged (same definition) |
| `time_quality == "unknown"` | 34,895 (55.87 %) | 34,895 (55.87 %) | unchanged (no times added) |
| `analysis_ready_timing == 1` | column absent | 27,465 (43.97 %): Fed 7,557, ECB 9,443, BoJ 10,465 | new flag |
| Decisions with a sourced (exact/approximate) time | 856 / 1,908 | 856 / 1,908 | unchanged |

Unknown-time rows stay at 56 % until the nine regimes' times are sourced (ISS-029). The
first Group 1 attempt reported 9 % unknown; that figure relied on announcement times typed
from memory, which were removed.

### Pipeline rerun and other fixes (2026-10-20)

- Full pipeline rerun (`python tasks.py data`) and `MoTrans15_v2.xlsx` re-exported, so every
  output reflects the reverted (unknown) times. Before the rerun, data/final still held the
  removed times.
- Removed leftover `APPROX_WINDOW` entries for RBI, BCB and BoK (no sourced times use them).
- Index cutoff: observations dated on or after a raw file's download day are now excluded
  (they may be intraday prices). The cutoff previously used "today", so rerunning on a later
  day let 17 intraday rows from 2026-10-13 in; the original build also had a few same-day
  rows (e.g. US series downloaded 2026-10-12 18:17 UTC during trading). Panel: 222,638 rows.
- New provenance tests (`TestTimeProvenance`): only Fed/ECB/BoJ may carry exact/approximate
  times, and every URL cited in `time_source` must be a file in `data/raw/MANIFEST.csv`. Both
  tests failed on the stale data and pass after the rerun.
- 109 tests pass; ruff clean.

### Tests

- [`tests/test_alignment.py`](tests/test_alignment.py): 15 tests covering the conservative
  reaction-session rule, including `test_reacting_session_never_precedes_earliest_possible_announcement()`.
- [`tests/test_priority_group_1_timing.py`](tests/test_priority_group_1_timing.py):
  verifies zero premature reacting dates, `analysis_ready_timing` flag integrity, and that
  known event dates exist in the dataset with valid baseline/reacting sessions. Known events
  are verified only by checking they exist in the data with non-preceding session dates;
  no UTC timestamps or "verified exact" claims are asserted for unsourced regimes.
