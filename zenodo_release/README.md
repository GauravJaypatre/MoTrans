# MoTrans-15: Monetary policy surprises, central bank communication and equity-index responses for the largest economies, 2010-2025 (v2.1.1)

## Overview & Scope
**MoTrans-15 (v2.1.1)** is a standardized, replication-certified dataset tracking central bank monetary policy announcements, high-frequency surprises, macroeconomic controls, and equity market responses across the world's major economies for the evaluation window **2010-01-01 to 2025-12-31** (16 calendar years).

### Configuration & Access Terms
- **ACCESS_MODE**: `restricted` (Access granted by request for academic replication)
- **DATA_LICENSE**: `CC-BY-4.0`
- **CODE_LICENSE**: `MIT`
- **Authors & Affiliations**: See `CITATION.cff` (Placeholders marked `TODO` pending publication metadata)
- **Reason for Restricted Access**: Financial index return series are derived from commercial exchange closing prices without signed vendor redistribution clearance. Closing price levels (`level_local`) are omitted from all tables; access to derived return tables is restricted to verified academic researchers upon request.

---

## 1. Sample Splits & Embargo Protocol

| Split | Window Range | Decisions | Hikes | Cuts | Holds | Event Rows | Role in Research Design |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `train` | 2010-01-01 to 2021-12-31 | 572 | 35 | 63 | 474 | 21,247 | Historical model estimation (12 years) |
| `validation` | 2022-01-01 to 2023-12-31 | 76 | 57 | 0 | 19 | 2,818 | Model selection, hyperparameter tuning |
| `test` | 2024-01-01 to 2025-12-31 | 70 | 0 | 28 | 42 | 2,590 | Strictly locked out-of-sample benchmark |
| **Total** | **2010-01-01 to 2025-12-31** | **718** | **92** | **91** | **535** | **26,655** | **Full Usable Analysis Sample** |

### 60-Day Embargo Protocol
Because multi-horizon event windows span up to 60 trading days (`clr_60`), any policy decision occurring within 60 calendar days prior to a partition boundary (or whose 60-day response window crosses into the subsequent split) is quarantined under `embargo_dropped` (64 decisions, 2,432 rows) to eliminate look-ahead leakage.

### Critical Property of the Test Split
The out-of-sample test split (2024-2025) contains **0 interest rate hikes**, reflecting the empirical reality of the 2024-2025 global easing cycle (28 cuts, 42 holds). Models must not be evaluated on rate-hike conditioning during test evaluation.

---

## 2. Table Tiers & Partition Membership

All row and decision counts are computed strictly from committed CSV reports (`reports/row_membership.csv`):

| Table Name | Tier & Description | Regimes | Decisions | Event Rows | Share of Panel |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `data/analysis_tier1.parquet` | **Tier 1**: High-frequency intraday surprises (Bauer-Swanson MPS; EA-MPD 1Y OIS) | Fed, ECB | 253 | 9,350 | 17.897% |
| `data/analysis_tier2_primary.parquet` | **Tier 2 Primary**: Rate-change decisions with 1-day sovereign yield proxy surprises | BoE, BoC, RBA, CBR, Fed, ECB | 130 | 4,851 | 9.286% |
| `data/secondary_holds.parquet` | **Secondary Holds**: Scheduled hold decisions with sovereign yield proxy surprises | BoE, BoC, RBA, Fed | 335 | 12,454 | 23.839% |
| `data/sensitivity_macro_revision.parquet` | **Macro Revision Sensitivity**: Controls robustness table | All primary regimes | 382 | 14,201 | — |
| `data/panel_returns_only.parquet` | **Daily Panel**: Continuous log returns without proprietary closing levels | 15 economies | — | 148,869 | — |

*Convenience CSV exports are provided for Tier 1 (`analysis_tier1.csv`), Tier 2 (`analysis_tier2_primary.csv`), and Secondary Holds (`secondary_holds.csv`).*

---

## 3. Rolling-Origin Cross-Validation & Final Fit (`data/folds.csv`)

To respect the temporal arrow of time, MoTrans-15 defines 4 rolling-origin evaluation folds plus a unified `final_fit` set (documented in `reports/fold_counts.csv`):

| Fold ID | Origin Cutoff | Training Window | Validation Window | Train Decs | Val Decs | Train Hikes | Val Hikes | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `1` | 2016-01-01 | 2010-01-01 to 2015-12-31 | 2016-01-01 to 2017-12-31 | 276 | 97 | 12 | 7 | ZIRP / Post-GFC recovery era |
| `2` | 2018-01-01 | 2010-01-01 to 2017-12-31 | 2018-01-01 to 2019-12-31 | 372 | 96 | 18 | 10 | Pre-COVID normalization |
| `3` | 2020-01-01 | 2010-01-01 to 2019-12-31 | 2020-01-01 to 2021-12-31 | 467 | 91 | 30 | 5 | Pandemic policy shock era |
| `4` | 2022-01-01 | 2010-01-01 to 2021-12-31 | 2022-01-01 to 2023-12-31 | 572 | 76 | 35 | 57 | Global inflation tightening cycle |
| `final_fit` | 2024-01-01 | 2010-01-01 to 2023-12-31 | — | 648 | 0 | 92 | 0 | Full TRAIN + VALIDATION estimation set before locked test split |

### How to Use `folds.csv`
- When selecting models, train exclusively on `fold == k & is_train == 1` and evaluate on `fold == k & is_val == 1`.
- For the final model to be benchmarked on the locked `test` split (2024-2025), fit model parameters strictly on the `final_fit` partition (648 decisions, 92 hikes).

---

## 4. Package Contents & Navigation
```
zenodo_release/
├── README.md                          # This document
├── LICENSE                            # Creative Commons CC-BY-4.0 (Dataset)
├── LICENSE-CODE                       # MIT License (Code)
├── CITATION.cff                       # Citation metadata (CFF 1.2.0)
├── .zenodo.json                       # Zenodo deposit metadata
├── CHECKSUMS.sha256                   # SHA-256 hashes of all packaged files
├── MANIFEST.csv                       # Package file inventory with sizes and hashes
├── LICENCE_AND_PROVENANCE.md          # Provider inventory and license terms
├── PROVENANCE.md                      # Audit certification & guardrail log
├── LIMITATIONS_PACKAGE.md             # Scientific limitations & unverified items
├── data/
│   ├── analysis_tier1.parquet         # Tier 1 high-frequency surprise table
│   ├── analysis_tier1.csv             # Convenience CSV copy
│   ├── analysis_tier2_primary.parquet # Tier 2 rate-change surprise table
│   ├── analysis_tier2_primary.csv     # Convenience CSV copy
│   ├── secondary_holds.parquet        # Secondary scheduled hold surprise table
│   ├── secondary_holds.csv            # Convenience CSV copy
│   ├── sensitivity_macro_revision.parquet # Controls robustness table
│   ├── panel_returns_only.parquet     # Daily index return panel (no price levels)
│   └── folds.csv                      # Rolling-origin CV folds & final_fit
├── docs/
│   ├── v2_1_data_dictionary.md        # Comprehensive variable definitions
│   ├── v2_1_limitations.md            # Technical limitations
│   ├── v2_1_spec.md                   # Engineering specification
│   ├── preregistration.md             # Formal research design pre-registration
│   ├── limitations.md                 # Core dataset limitations
│   ├── DATA_FREEZE_v2_1.md            # Data freeze certification & hashes
│   ├── data_quality_scorecard.md      # Data quality scorecard
│   └── labelling_guide.md             # Statement qualitative annotation guide
├── reports/
│   ├── split_counts.csv               # Decisions & rows by split and regime
│   ├── fold_counts.csv                # Decisions & rows across CV folds
│   ├── test_window_composition.csv    # Granular test window composition
│   ├── row_membership.csv             # Partition membership breakdown
│   ├── leakage_audit.csv              # Zero-leakage audit verification
│   ├── analysis_ok_breakdown.csv      # Usable vs disqualified rows
│   ├── years_thin.csv                 # Annual density breakdown
│   └── verification_summary.csv       # External verification audit results
└── code/
    ├── src/                           # Python data processing modules
    ├── tests/                         # Full regression test suite
    ├── tasks.py                       # Task runner
    ├── requirements.txt               # Full Python dependency lock
    ├── pytest.ini                     # Test configuration
    └── README.md                      # Code instructions & raw data notice
```

---

## 5. Exclusions & Limitations Notice
- **Statement Qualitative Hand Labels**: Manual statement qualitative classifications have not undergone double-blind expert replication and are **not included** in this release package (see `docs/labelling_guide.md` for guidelines).
- **Post-Window Observations (`post_window_2026`)**: 2026 data are strictly quarantined and omitted from release tables.
- **Excluded Rows Table (`excluded_rows.parquet`)**: Omitted to keep package focused on analysis-ready and secondary tables.
