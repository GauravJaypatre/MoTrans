# MoTrans-15: Monetary Policy Surprises and Equity-Index Responses (v2.2.0)

**Version**: 2.2.0  
**Deposit Type**: Zenodo Restricted Access  
**Release Tag**: `v2.2.0-package`  
**License**: MIT (Code) / Restricted Non-Open Research License (Derived Returns)  

---

## Critical Disclosure: Test Split Partitions (Sample A vs. Sample B)

The held-out evaluation window (2024–2025, 70 decisions) is partitioned into two distinct evaluation samples in `data/splits.csv`:

1. **Sample A: Full Test Split ($N=70$ decisions, 2,590 event rows)**:
   - Spans all qualifying policy decisions from 2024 to 2025 across Tier 1, Tier 2 Primary Actions, and Secondary Holds.
   - **Prior Exposure Notice**: Exactly **14 decisions (20.0%)**—all ECB Tier 1 announcements—had return outcomes evaluated during the pre-registered v1 confirmatory blind test (`src/modeling/run_v1_blind_test.py`, documented in `docs/INTEGRITY_AUDIT.md`).
   - Flagged in `splits.csv` as `read_by_prior_analysis == 1`.

2. **Sample B: Pristine Held-Out Test Split ($N=56$ decisions, 2,072 event rows)**:
   - Selected by filtering `splits.csv` for `split == 'test' and read_by_prior_analysis == 0`.
   - **Zero Prior Exposure**: Evaluates exclusively decisions with zero model exposure or outcome reads in prior project phases.
   - **Regime Limitation Notice**: Sample B contains **ZERO interest rate hikes** (0 tightening decisions). It comprises exclusively **holds (36 decisions) and rate cuts (20 decisions)** from Tier 2 central banks (BoE, BoC, RBA, CBR).

Researchers evaluating out-of-sample model generalization must report Sample A and Sample B side by side.

---

## Package Contents

- `data/`: Certified cryptographic release tables (all `level_local` price levels and `shock_std` traps removed).
- `docs/`: Data freeze certificates, pre-analysis plans, eval protocols, and audit logs.
- `reports/`: Complete 123-model results ledger, outlier leverage audits, and power analysis.
- `code/`: Reproducible estimation and testing pipeline.
