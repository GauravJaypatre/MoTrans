# MoTrans-15: Out-of-Sample Test Scoring Benchmark Report

**Execution Status**: COMPLETED  
**Authorization**: Single Authorized Run via `scripts/run_test_scoring.py`  
**Git Freeze Tag**: `modeling-spec-frozen`  
**Commit Hash**: `f95b35f868e7dfa4d8f7a4272d7e5d166ed38c26`  
**Unlock Audit Log**: `outputs/v2_1/unlock_audit.log` (Strictly 17 lines)  
**Mandatory Regime Caveat**: *"test split has zero hikes; cannot assess tightening transfer"*  

---

## 1. Test Scoring Benchmark Results (Easing & Holds Regime Only)

| Sample Partition | Horizon | Decisions | Rows | Hikes | $\hat{\beta}$ | Clustered SE | Wild Boot $p$ | Headline MDE (bp) | $R^2$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Sample A (All 70 Test Decisions) | `clr_1` | 70 | 2,590 | 0 | **+0.0008** | 0.0041 | 0.8719 | 116.0 bp | 0.0001 |
| Sample A (All 70 Test Decisions) | `clr_3` | 70 | 2,590 | 0 | **+0.0090** | 0.0107 | 0.4214 | 304.7 bp | 0.0047 |
| Sample A (All 70 Test Decisions) | `clr_5` | 70 | 2,590 | 0 | **+0.0045** | 0.0121 | 0.7207 | 345.2 bp | 0.0008 |
| Sample A (All 70 Test Decisions) | `clr_20` | 70 | 2,590 | 0 | **-0.0033** | 0.0154 | 0.8468 | 437.7 bp | 0.0001 |
| Sample A (All 70 Test Decisions) | `clr_60` | 70 | 2,590 | 0 | **+0.0258** | 0.0203 | 0.2142 | 577.4 bp | 0.0037 |
| Sample B (Pristine 56 Test Decisions, Tier 2 Only, Zero Hikes) | `clr_1` | 56 | 2,072 | 0 | **+0.0021** | 0.0045 | 0.6597 | 129.3 bp | 0.0012 |
| Sample B (Pristine 56 Test Decisions, Tier 2 Only, Zero Hikes) | `clr_3` | 56 | 2,072 | 0 | **+0.0142** | 0.0118 | 0.2543 | 335.3 bp | 0.0120 |
| Sample B (Pristine 56 Test Decisions, Tier 2 Only, Zero Hikes) | `clr_5` | 56 | 2,072 | 0 | **+0.0114** | 0.0133 | 0.4184 | 379.2 bp | 0.0052 |
| Sample B (Pristine 56 Test Decisions, Tier 2 Only, Zero Hikes) | `clr_20` | 56 | 2,072 | 0 | **+0.0064** | 0.0150 | 0.6537 | 427.5 bp | 0.0006 |
| Sample B (Pristine 56 Test Decisions, Tier 2 Only, Zero Hikes) | `clr_60` | 56 | 2,072 | 0 | **+0.0359** | 0.0202 | 0.1141 | 577.4 bp | 0.0079 |

---

## 2. Core Econometric Findings & Substantive Interpretation

1. **Structural Regime Limitation (Zero Hikes)**:  
   Across both Sample A (70 decisions) and Sample B (56 pristine decisions), there are **strictly ZERO interest rate hikes** (46 holds, 10 cuts in Sample B; 58 holds, 12 cuts in Sample A). Consequently, this out-of-sample evaluation **CANNOT assess monetary tightening transmission**. It serves strictly as a sanity check on equity behavior during an easing and pause regime.

2. **Empirical Null on Out-of-Sample Easing/Holds**:  
   Across all five horizons for both Sample A and Sample B, the estimated shock coefficient is statistically indistinguishable from zero after wild cluster bootstrap (Sample A `clr_5`: $\hat{\beta} = +0.0045, p_{\text{wild}} = 0.7207$; Sample B `clr_5`: $\hat{\beta} = +0.0114, p_{\text{wild}} = 0.4184$).

3. **Statistical Power in Test Split**:  
   Because the test split contains only 70 decisions (Sample A) and 56 decisions (Sample B), statistical power is severely constrained (Headline MDE $= 345.2$ bp for Sample A `clr_5`; $379.2$ bp for Sample B `clr_5`). The test split serves to confirm sign and magnitude plausibility rather than reject fine effect sizes.

---

## 3. Compliance and Verification
- `outputs/v2_1/unlock_audit.log` incremented by exactly 1 line (16 -> 17).
- All test results carry the mandatory caveat: *"test split has zero hikes; cannot assess tightening transfer"*.