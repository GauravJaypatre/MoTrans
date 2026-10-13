# MoTrans-15

**Monetary transmission to equities across the 15 largest economies:
policy surprises, central-bank language and blind transfer to an unseen cycle.**

This repository builds the research dataset for MoTrans-15. It covers data
collection, alignment, shock construction and the central-bank text corpus.
No econometric or ML models are run here — only the dataset.

## Countries (15)

US · China · Germany · India · Japan · UK · France · Italy · Russia · Canada ·
Brazil · Spain · Mexico · Australia · South Korea

## Data Window

2000-01-01 (or earliest reliable date, ~2005 for some EMs) to latest available.

## Getting started (new teammate)

Needs Git and Python 3.12. On macOS/Linux use `.venv/bin/` instead of `.venv\Scripts\`.

```bash
git clone https://github.com/prachi-3011/MoTrans-15.git
cd MoTrans-15
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python tasks.py data    # downloads raw data and builds everything (about 1-2 hours)
.venv\Scripts\python tasks.py test    # data tests are skipped until the data is built
```

Raw data is not in git (licences). `tasks.py data` re-downloads it from the official
sources; alternatively ask the Data lead for a private copy of `data/` and check it
against `data/raw/MANIFEST.csv` (SHA-256 of every file). Other tasks: `setup`, `clean`, `lint`.

## The dataset (data/final/)

| File | One row is | Approx. size |
|---|---|---|
| `panel_daily.parquet` | one trading day × one equity index (38 series, 16 markets) | 222,646 × 24 |
| `policy_decisions.csv` | one central-bank decision (12 regimes, 2000-2026) | 1,908 |
| `events.parquet` | one decision × one reacting index, with event-window returns and shock | 62,461 |
| `shocks.parquet` | one decision: graded policy surprise (A/B/C) | 1,908 |
| `statements.parquet` | one English policy statement (Fed, ECB, BoJ, RBI) | see docs/statements_coverage.md |

Excel copy of every table: `.venv\Scripts\python -m src.export_excel` writes
`data/final/MoTrans15_all_records.xlsx` (local only - it contains licensed price data).
Plain-language summary of all phases: [docs/MoTrans15_Project_Summary.docx](docs/MoTrans15_Project_Summary.docx).

Read first: [data dictionary](docs/data_dictionary.md), [issues](docs/issues.md) (all known gaps),
[decisions](DECISIONS.md), [data quality report](docs/data_quality_report.md),
[shock validation](docs/shock_validation.md).

## Repository Layout

```
MoTrans-15/
├── data/
│   ├── raw/               Write-once downloads (git-ignored except MANIFEST.csv)
│   │   └── MANIFEST.csv   Provenance manifest — tracked in git
│   ├── interim/            Cleaned intermediate files (regenerable)
│   └── final/              Publication-ready outputs (regenerable)
├── src/                    Python source modules (one per pipeline step, see pipeline.py)
│   ├── pipeline.py         End-to-end pipeline entry point
│   ├── collect_*.py        Downloaders/parsers (indices, policy, controls, statements)
│   ├── alignment.py        Timing rule: announcement -> trading sessions (DECISION-013)
│   ├── event_windows.py    Event-window returns
│   ├── build_panel.py      Final daily panel
│   ├── build_shocks.py     Graded policy shocks
│   └── download.py         Write-once download helper + manifest writer
├── tests/                  pytest test suite
├── notebooks/              Exploration notebooks
├── docs/                   Documentation
│   ├── PROJECT_SPEC.md     Full specification
│   ├── source_registry.md  Variable-level source registry
│   ├── data_dictionary.md  Column-level data dictionary
│   └── issues.md           Failed sources and open questions
├── outputs/                Generated reports and plots (regenerable)
├── tasks.py                Task runner (setup | data | test | clean | lint)
├── requirements.in         Direct dependencies (minimum versions)
├── requirements.txt        Full pip freeze lock file
├── DECISIONS.md            Dated decision log
└── .gitignore
```

## Key Rules

1. **Write-once raw data** — never overwrite files in `data/raw/`. Use
   `src.download.save_raw_file()` which enforces this and writes MANIFEST.csv.
2. **No look-ahead** — any value used for date *t* must have been publicly
   known at *t*.
3. **Provenance** — every series carries source, URL/API, series ID, retrieval
   date, licence, and transformation history.
4. **Phase gates** — work proceeds phase by phase (A → E); the Phase B timing
   hand-check was signed off by a person (docs/phase_b_hand_check.xlsx).

## Documentation

- [Project specification](docs/PROJECT_SPEC.md)
- [Source registry](docs/source_registry.md)
- [Data dictionary](docs/data_dictionary.md)
- [Decision log](DECISIONS.md)
- [Issues log](docs/issues.md)
