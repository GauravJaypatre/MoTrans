# MoTrans-15: Research Execution Order & Blinding Audit Log

This document records the exact execution order of all empirical evaluations, confirming that confirmatory benchmark evaluations were executed prior to exploratory model searches to prevent data snooping and preserve pre-registered blinding.

---

## Chronological Execution Ledger

| Sequence | Execution Date (UTC) | Milestone / Phase | Scope & Partitions | Status | Verification & Integrity Certification |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **01** | **2026-11-02** | **Pre-Registered V1 Confirmatory Blind Test** | 47 held-out decisions (Fed: 16, ECB: 31, 2022-01-26 to 2025-10-30; 1,786 event rows in `data/final/analysis_tier1.parquet`) | **EXECUTED FIRST** | Evaluated H1 (Domestic Transmission) and H2 (Spillovers) strictly under pre-registered lock (`docs/preregistration.md`, hash `384c0d71a...`). Clustered SEs, two-way clustered SEs, and wild cluster bootstrap (999 draws). Results logged in `outputs/modeling/v1_blind_test_results.csv` and `docs/V1_BLIND_TEST_REPORT.md`. Zero exploratory tuning preceded this evaluation. |
| **02** | **2026-11-02** | **V2.1 Exploratory Model Pre-Declaration** | 8 pre-declared specifications across rolling-origin cross-validation folds (`data/v2_1/folds.csv`) | **DECLARED** | Full specification registry declared in `docs/V21_SPEC_LIST.md` with Holm and Benjamini-Hochberg FDR multiplicity controls. |
| **03** | **2026-11-02** | **V2.1 Exploratory Rolling-Origin Cross-Validation & Robustness Sweeps** | Folds 1–4 (`fold_1` to `fold_4`) and unified `final_fit` partition (572 train + 76 val decisions) | **IN PROGRESS** | Scalers fit strictly on training fold data. Leave-one-central-bank-out (LOO-CB), overlap exclusion, horizon sweep, winsorization, macro revision sensitivity. |
| **04** | — | **V2.1 Out-of-Sample Test Scoring (2024–2025)** | 70 test decisions (ECB: 14, BoE: 14, BoC: 14, Fed: 14, RBA: 14; 2,590 event rows) | **STRICTLY BLOCKED** | Held out under `src/model_guard.py`. Will not be accessed or evaluated without explicit user authorization ("approve test unlock"). `unlock_audit.log` remains at 16 historical lines. |

---

## Blinding Integrity Attestation
1. The pre-registered v1 blind test was executed directly on the immutable freeze table (`data/final/analysis_tier1.parquet`), using strictly pre-specified variables and horizons ($W \in \{1, 3, 5, 20, 60\}$).
2. No v2.1 exploratory cross-validation models were estimated prior to logging the v1 confirmatory results.
3. The v2.1 test split (2024–2025) remains completely untouched and locked.

