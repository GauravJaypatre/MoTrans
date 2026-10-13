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

## Quick Start

```bash
# Activate the virtual environment
.venv\Scripts\activate        # Windows

# Install pinned dependencies
python tasks.py setup

# Run the test suite
python tasks.py test

# Rebuild the full pipeline (raw → interim → final)
python tasks.py data

# Clean regenerable data (keeps raw)
python tasks.py clean

# Lint the codebase
python tasks.py lint
```

## Repository Layout

```
MoTrans-15/
├── data/
│   ├── raw/               Write-once downloads (git-ignored except MANIFEST.csv)
│   │   └── MANIFEST.csv   Provenance manifest — tracked in git
│   ├── interim/            Cleaned intermediate files (regenerable)
│   └── final/              Publication-ready outputs (regenerable)
├── src/                    Python source modules
│   ├── __init__.py         Package init + split_tag() helper
│   ├── pipeline.py         End-to-end pipeline entry point
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
4. **Phase gates** — work proceeds phase by phase (A → E) with human approval
   between each.

## Documentation

- [Project specification](docs/PROJECT_SPEC.md)
- [Source registry](docs/source_registry.md)
- [Data dictionary](docs/data_dictionary.md)
- [Decision log](DECISIONS.md)
- [Issues log](docs/issues.md)
