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
