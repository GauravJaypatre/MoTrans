# MoTrans-15 v2.0 Dataset Specification (2010-to-Latest)

**Project**: MoTrans-15 v2.0: Verified 2010+ Dataset for Time-Ordered Model Training  
**Branch**: `v2-2010plus`  
**Status**: Exploratory / Forecasting Research Specification (NOT the Pre-Registered Confirmatory Test)  
**Parent Release**: `v1.0-data-freeze` (Preserved intact under tag `v1.0-data-freeze` in `data/final/`)  
**Specification Date**: 2026-10-24  

---

## 1. Study Nature & Governing Purpose

> [!IMPORTANT]
> **Exploratory & Forecasting Disclaimer**:  
> MoTrans-15 v2.0 is designed exclusively for **time-ordered exploratory modeling, out-of-sample forecasting, and machine learning model validation**. It is **NOT** the pre-registered confirmatory event-study test, which is permanently locked in v1.0 under tag `v1.0-data-freeze`. All documentation, tables, and reporting must prominently state this exploratory status.

### Core Objectives:
1. **Focus on Modern Financial Regimes**: Restrict the primary analysis window to **2010-01-01 to latest available complete trading day** (`2026-10-13`), omitting the structural breaks of the early 2000s and 2007–2009 Global Financial Crisis from baseline model training.
2. **Multi-Source Independent Verification**: Audit and cross-check prices, decisions, shocks, and macro controls against independent second sources to calculate empirical error rates and assign row-level quality flags.
3. **Strict Time-Ordered Evaluation Architecture**: Ensure that model training, validation, and hyperparameter tuning use strictly time-ordered evaluation methods with temporal embargos.

---

## 2. Window & Long-History Partitioning

1. **Primary Analysis Window (`data/v2/`)**:
   - `2010-01-01` to `2026-10-13` (or latest complete trading day).
   - All primary tables in `data/v2/` will contain strictly observations within this modern sample.
2. **Pre-2010 Robustness Archive (`data/v2/archive_2000_2009/`)**:
   - Observations from `2000-01-01` to `2009-12-31` are retained exclusively in dedicated long-history robustness files (e.g. `panel_2000_2009.parquet`, `events_2000_2009.parquet`).
   - They are never pooled into the primary time-series models.

---

## 3. Time-Ordered Validation & Guardrail Architecture

Random cross-validation ($k$-fold) and random shuffling are **strictly prohibited** in monetary transmission and asset pricing models due to look-ahead bias and serial correlation.

### Evaluation Protocol:
1. **Time-Ordered Methods Only**:
   - **Expanding Window**: Training on $[t_0, t_k]$ with validation on $[t_k + \text{embargo}, t_{k+h}]$.
   - **Rolling Origin**: Fixed lookback window rolled forward in time.
2. **Mandatory Embargo**:
   - An embargo period equal to the longest outcome horizon ($\ge 60$ trading days) must be enforced between training folds and validation folds to eliminate information leakage from overlapping return windows ($clr_{60}$).
3. **Holdout Design & Candidate Analysis**:
   - Current baseline reserves the final 12 months (`2025-10-14` to `2026-10-13`) as `split_tag = "final_holdout"`, locked by `src/model_guard.py`.
   - *Status Note*: The final holdout design is pending a decision based on `outputs/v2/holdout_candidates.csv` (evaluating origins 2022-01-01, 2024-01-01, 2025-01-01, and 2025-10-14). Neither Alternative A (tier-specific holdout) nor Alternative B (decision-count holdout) will be implemented because both leak across regimes since monetary shocks cross international financial markets.
   - A *rolling-origin evaluation* architecture (origins 2016, 2018, 2020, 2022, 2024 with a 60-day embargo) is being actively considered to ensure robust temporal validation across market cycles.
4. **v2 Sample Partitioning & Blind Test Isolation**:
   - v2 tables must **not** reuse `'blind_test'` or `'train'` tags from v1.
   - In v2 tables, `v1_split_tag` stores a copy of the v1 tag for provenance reference only, while v2 split assignments are time-ordered and assigned dynamically by modeling code.
   - v2 results are strictly exploratory and cannot be reported as confirmatory evidence for the v1 blind test.
   - v2 modelling must not start before the pre-registered v1 blind test (Milestone M3) is run, or, if it does, the v1 analysis plan hash in `docs/analysis_plan.md` (`384c0d71a1debb054798272965f42f0d36f2e7c6f96461770a6291004739c040`) must be recorded first.
   - A unit test enforces that no v2 table contains the tag `'blind_test'`.
5. **BoJ Policy Instruments & Sensitivity Note**:
   - For BoJ, unclassified decisions can have nonzero or NaN target rate changes (`size_bp`) during the Kuroda QQE and negative interest rate regimes (2013–2016).
   - Sensitivity work must use monetary policy surprise variables (`shock_primary`, `shock_usable`), not discrete hike/cut classification labels.

---

## 4. Multi-Source Quality Flags & Verification Criteria

In Phase V1 and V2, every row in `data/v2/` is augmented with independent quality indicators:

| Column | Type | Values | Definition |
|---|---|---|---|
| `price_source_verified` | `int8` | `0, 1` | 1 if equity closing price matches independent secondary source within 1 bp tolerance on sampled audit days. |
| `shock_verified` | `int8` | `0, 1` | 1 if monetary policy surprise matches recomputed independent source calculation. |
| `timing_verified` | `int8` | `0, 1` | 1 if announcement timestamp is verified against official text release documentation. |
| `proxy_type` | `str` | `direct_index`, `etf_proxy`, `synthetic` | Distinguishes underlying cash indices from ETF tradeable proxies (e.g., `de_stoxx_banks_etf`, `ea_emu_smallcap_etf`). |
| `analysis_ok` | `int8` | `0, 1` | 1 if all verification checks pass and timing is sound; 0 if any audit failed. Rows with `0` are kept in the data for provenance but filtered from primary modeling. |

---

## 5. Macroeconomic State & Regime Interaction Variables

To capture non-linear transmission across economic regimes, v2.0 tables incorporate:
1. `zlb_flag`: Binary indicator (1 if policy rate $\le 0.25\%$, 0 otherwise).
2. `qe_ycc_flag`: Central bank balance sheet expansion or Yield Curve Control indicator (e.g. BoJ 2016–2024).
3. `inflation_regime`: Local inflation relative to official target (`high_inflation` if $\text{CPI} \ge \text{target} + 1\%$, `target_range`, `low_inflation`).
4. `vix_regime`: Global risk environment (`low` < 15, `normal` 15–25, `high_vol` > 25).
5. `overlap_foreign_cb`: Forward overlap count isolating foreign central bank announcements within the event window.

---

## 6. Implementation Workflow

- **Phase V0**: Complete coverage audit of v1.0 holdings for the 2010+ period (`outputs/v2/coverage_2010plus.csv`).
- **Phase V1**: Independent second-source verification across prices, policy rates, shocks, event returns, timing, and macro releases (`outputs/v2/verification_summary.csv`, `docs/v2_quality_scorecard.md`).
- **Phase V2**: Pipeline correction for items failing verification; addition of quality flags.
- **Phase V3**: Construction of final 2010+ parquets in `data/v2/`.
- **Phase V4**: Test suite run, double rebuild verification, documentation freeze (`docs/DATA_FREEZE_v2.md`), and tag `v2.0-data-freeze`.
