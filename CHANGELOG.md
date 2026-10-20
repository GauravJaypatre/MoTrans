# MoTrans-15 Dataset Changelog

All modifications are applied at the pipeline code level (`src/`), never by hand-editing
output files. The original workbook `data/final/MoTrans15_all_records.xlsx` is untouched.
The cleaned output is `data/final/MoTrans15_v2.xlsx`.

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
