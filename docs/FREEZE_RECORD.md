# MoTrans-15 Modeling Specification Freeze Record (v2.2)

**Timestamp UTC**: 2026-11-09T23:30:00Z  
**Branch**: `v2-2-hardening`  
**Freeze Status**: **OFFICIALLY FROZEN** (Tag: `modeling-spec-frozen`)  
**Authorized Scope**: "MoTrans-15: Monetary policy surprises and equity-index responses for the largest economies, 2010-2025" (six central banks).

---

## 1. Commit and Code Integrity

- **Pre-Freeze HEAD Commit Hash**: `771b4dd7c2fd3b317116c643deb7c6b181951f6e` (`DECISION-043`)
- **Code Tree Hash (`src/` and `scripts/`, 64 files)**:  
  `ca894a25940787e73e25881daa9bd2afc89a5b60e8ec56b067db944874c648e9`
- **Evaluation Protocol Hash (`docs/V22_EVAL_PROTOCOL.md`)**:  
  `4cf109948bd8deff77af0259d1c920b6d5c118778475092ecdcc86cf6f0e41ff`
- **Verification Gates Status**: All 12 Release Gates passed (Exit code 0).

---

## 2. Cryptographic Data Hashes (from `docs/DATA_FREEZE_v2_2.md`)

The release data bundle frozen for modeling and public distribution under `data/v2_2/release/` and `zenodo_release_v22/data/` consists of:

| File Name | File Size (Bytes) | Row Count | Decision Count | SHA-256 Checksum |
| :--- | :---: | :---: | :---: | :--- |
| `analysis_tier1.parquet` | 654,279 | 9,350 | 253 | `37ca577bb6520825428c6cefc185ca7f936e042f5547f400141dd8e8b344eb2c` |
| `analysis_tier2_primary.parquet` | 361,070 | 4,851 | 130 | `8127036a7d0e6fd2f92d1ae878e81e028e6b65646b68421ccb1ba14005f96ca2` |
| `secondary_holds.parquet` | 851,313 | 12,454 | 335 | `fce39831717f1403ff6463cf288b55ceb9e57aa08ab94d8ef78dc7d6de1706ec` |
| `sensitivity_macro_revision.parquet` | 979,743 | 14,201 | 383 | `d6daec49e2dd4fc304c6227df19508f44c32186077fa0b4849a6eb193969c58e` |
| `panel_returns_only.parquet` | 4,805,040 | 148,869 | — | `e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620` |
| `splits.csv` | 77,544 | 718 | 718 | `f362ad426f1d6dbfe7294d4320e932e89c39273f81f3154936022096bc52b1b6` |
| `folds.csv` | 838 | 718 | 718 | `5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee` |
| `README.md` | 869 | — | — | `9dee6d06ec6caf8ffe0ce157dea6c83dc5d50ff0ae737cfbbda325be11ae8f58` |

---

## 3. Pre-Registered Modeling Protocol & Confirmatory Hierarchy

1. **Confirmatory Primary Specification**:
   - Equation: $\text{clr\_W} \sim \text{shock\_raw\_bp\_fold\_std} + \text{overlap\_Wd}$
   - Sample: 47-decision pre-registered v1 sample (US, EA, JP) across horizons $\{1, 3, 5, 20, 60\}$.
   - Inference: Cluster-robust SE and restricted wild cluster bootstrap at `event_id`.
2. **Disclosed Specification Deviation**:
   - The bivariate specification ($\text{clr\_W} \sim \text{shock\_raw\_bp\_fold\_std}$) is maintained strictly as a **disclosed deviation**, not approved as a pre-registration change.
3. **Headline Exploratory Designs**:
   - Pre-declared in `docs/V22_EVAL_PROTOCOL.md`:
     - Design 1: Regime-stratified forward chaining (train up to $Y \in \{2011, 2017, 2018, 2022\}$, score $Y+1$, strictly train+validation).
     - Design 2: Leave-one-tightening-episode-out (LOTEO) across declared episodes (2011, 2015–2018, 2022–2023).
     - Design 3: Formal restatement of v1 blind test results.
4. **Held-Out Blinding Status**:
   - `outputs/v2_1/unlock_audit.log` remains strictly at **16 lines**. Zero test split outcomes loaded prior to freeze.
