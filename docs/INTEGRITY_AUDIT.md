# MoTrans-15: Research Integrity Audit & Blinding Verification

**Date**: 2026-11-03  
**Status**: ACTIVE / HARDENED  
**Commit Context**: Modeling Harness Final Hardening  
**Target Submission**: *Scientific Data* (Descriptor) / *Nature Communications* (Article)

---

## 1. Executive Summary

This audit assesses methodological integrity, sample blinding, and shock instrumentation across the transition from MoTrans-15 v1.0 to v2.1.1. 

Key Findings:
1. **Sample Overlap**: Of the 70 policy decisions designated as the held-out test split (2024–2025) in v2.1.1, exactly **14 decisions (20.0%)** had their return outcomes computed during the pre-registered v1 blind test (`run_v1_blind_test.py`). These 14 decisions are all European Central Bank (ECB) announcements under Tier 1.
2. **Pristine Out-of-Sample Split**: The remaining **56 decisions (80.0%)**—comprising all Federal Reserve, Bank of England, Bank of Canada, and Reserve Bank of Australia decisions in 2024–2025—have **never been loaded, unblinded, or evaluated** by any outcome model.
3. **Fed Shock Instrumentation**: Federal Reserve high-frequency surprises (Bauer-Swanson MPS) terminate in December 2023. Post-2023 Fed meetings rely on daily sovereign yield proxies (`yield_proxy`), which places them in Tier 2. Consequently, Tier 1 contains zero Fed decisions in 2024–2025.
4. **Mandatory Reporting Protocol**: Final test scoring (Phase 4) must report benchmark metrics separately for:
   - Full Test Split ($N = 70$ decisions)
   - Pristine Unseen Test Split ($N = 56$ decisions; 0% prior exposure)

---

## 2. Quantitative Sample Split Overlap Audit

### 2.1 Sample Partitioning Across Generations

| Dataset Version | Calendar Window | Split Designation | Role |
| :--- | :--- | :--- | :--- |
| **v1.0** | 2000-01-01 to 2019-12-31 | `train` | Exploratory & baseline estimation |
| **v1.0** | 2020-01-01 to 2021-12-31 | `crisis` | COVID-19 pandemic stress-test regime |
| **v1.0** | 2022-01-01 to 2025-10-30 | `blind_test` | Confirmatory pre-registered blind test (47 decisions) |
| **v2.1.1** | 2010-01-01 to 2021-12-31 | `train` | Cross-validation training folds (CV Folds 1–4) |
| **v2.1.1** | 2022-01-01 to 2023-12-31 | `validation` | Hyperparameter selection & validation |
| **v2.1.1** | 2024-01-01 to 2025-12-31 | `test` | Strictly held-out benchmark split (70 decisions) |
| **v2.1.1** | 2026-01-01+ | `post_window` | Quarantined future observation buffer |

### 2.2 Granular Breakdown of Overlap

The pre-registered v1 blind test evaluated 47 decisions from `data/final/analysis_tier1.parquet`:
- **16 Federal Reserve decisions** (2022-01-26 to 2023-12-13): All fall within the v2.1 `validation` window (2022–2023). **Zero overlap with v2.1 test split.**
- **16 ECB decisions** (2022-02-03 to 2023-12-14): All fall within the v2.1 `validation` window (2022–2023). **Zero overlap with v2.1 test split.**
- **14 ECB decisions** (2024-01-25 to 2025-09-11): Fall within the v2.1 `test` window. **These 14 decisions overlap.**
- **1 ECB decision** (`ecb_2025-10-30`): Excluded from v2.1 test split due to the 60-day embargo requirement prior to the dataset end date (2025-12-31).

### 2.3 Comprehensive Decision Accounting in V2.1 Test Split

| Decision Table | Total Test Decisions | Decisions in v1 Blind Test | Pristine Test Decisions | Pristine Rows |
| :--- | :---: | :---: | :---: | :---: |
| `analysis_tier1` (ECB) | 14 | 14 (100.0%) | 0 (0.0%) | 0 |
| `analysis_tier2_primary` (Actions) | 20 | 0 (0.0%) | 20 (100.0%) | 740 |
| `secondary_holds` (Holds) | 36 | 0 (0.0%) | 36 (100.0%) | 1,332 |
| **Total Test Split** | **70** | **14 (20.0%)** | **56 (80.0%)** | **2,072** |

*Rows: 518 overlapping rows ($14 \times 37$ index series) vs 2,072 pristine rows ($56 \times 37$ index series).*

---

## 3. Federal Reserve Shock Coverage & Fallback Audit (A2)

### 3.1 Data Source Boundaries
- **Instrument**: High-Frequency Monetary Policy Surprise (`MPS`), defined as the 30-minute change in federal funds and Eurodollar/SOFR futures around FOMC releases (Bauer and Swanson, 2023).
- **Termination Date**: The official FRBSF Bauer-Swanson dataset terminates on **December 13, 2023** (`fed_2023-12-13`).
- **Post-2023 Fallback**: In `src/build_shocks.py`, Federal Reserve decisions in 2024 and 2025 have `shock_hf_raw = NaN`. The pipeline assigns the daily 1-year US Treasury yield change as `shock_proxy_raw`, with `shock_grade = "B"` and `shock_measure_type = "yield_proxy"`.

### 3.2 Tier Routing Implications
- By pre-registered design (`docs/preregistration.md` Section 3), Tier 1 requires `shock_tier == 1` (`shock_grade == "A"` and `shock_measure_type == "hf_ois"`).
- Consequently, all post-2023 Fed meetings were routed out of Tier 1 into Tier 2:
  - 4 rate cuts (`fed_2024-09-18`, `fed_2024-11-07`, `fed_2024-12-18`, `fed_2025-09-17`) were routed to `analysis_tier2_primary.parquet`.
  - 10 rate holds were routed to `secondary_holds.parquet`.
- **Finding**: Tier 1 in v2.1 contains **0 Federal Reserve decisions in 2024–2025**. Any Tier 1 evaluation of 2024–2025 evaluates exclusively ECB monetary policy.

---

## 4. Leakage Prevention Architecture in V2.1

To ensure that no model exploration or hyperparameter search accesses test split outcomes:
1. **Physical Column Guard**: `src/modeling/data_loader.py` physically strips `clr_1` through `clr_60` whenever `split="test"` or `split="all"` is loaded, unless `UNLOCK_TEST=1` is explicitly defined in the environment AND `allow_test_outcomes=True` is passed as a function argument.
2. **Access Trapping**: Unauthorized attempts to load test outcomes raise `PermissionError` and append a timestamped audit entry with git commit hash to `outputs/v2_1/unlock_audit.log`.
3. **Audit Log Verification**: Prior to Phase 4 test scoring, `unlock_audit.log` must contain exactly 16 historical lines (all dating to packaging and verification). Zero unauthorized or exploratory accesses have occurred.

---

## 5. Protocol for Phase 4 Scoring

When Phase 4 test scoring is approved:
1. `scripts/run_test_scoring.py` must verify that git HEAD is tagged `modeling-spec-frozen`.
2. The script must report all performance statistics across two distinct samples:
   - **Sample A (Full Test Set, $N = 70$)**: Standard comprehensive benchmark.
   - **Sample B (Pristine Test Set, $N = 56$)**: Pure unblinded sample containing exclusively decisions that were never in the v1 blind test.
3. Both sets must be presented in parallel with full multiplicity corrections and the mandatory regime caveat:
   > *"Evaluated during an easing cycle among the included central banks (the Bank of Japan hiked in the same period) with zero interest rate hikes."*
