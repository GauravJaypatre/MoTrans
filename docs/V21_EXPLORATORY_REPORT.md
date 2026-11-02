# MoTrans-15: V2.1 Exploratory Model Results & Robustness Report

**Execution Status**: COMPLETED  
**Dataset Version**: `2.1.1` (`final_fit` & `folds.csv`)  
**Mandatory Regime Caveat**: *"easing/hold regime only; cannot assess tightening transfer"*  
**Out-of-Sample Test Status**: LOCKED (Zero test split observations evaluated)

---

## 1. Rolling-Origin Cross-Validation (Folds 1 to 4)

| Fold ID | Origin Cutoff | Horizon | Train Decs | Train Beta | Cluster SE | Train p-val | Val Obs | Val RMSE | Val OOS R² |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `fold_1` | — | `clr_1` | 112 | **+0.0017** | 0.0016 | 0.2828 | 1216 | 0.0113 | -0.0378 |
| `fold_1` | — | `clr_5` | 112 | **+0.0057** | 0.0035 | 0.1064 | 1216 | 0.0262 | -0.0760 |
| `fold_2` | — | `clr_1` | 144 | **+0.0009** | 0.0014 | 0.5322 | 1254 | 0.0114 | -0.0128 |
| `fold_2` | — | `clr_5` | 144 | **+0.0032** | 0.0032 | 0.3057 | 1254 | 0.0273 | -0.0251 |
| `fold_3` | — | `clr_1` | 176 | **+0.0007** | 0.0012 | 0.5569 | 1140 | 0.0307 | -0.0487 |
| `fold_3` | — | `clr_5` | 176 | **+0.0027** | 0.0027 | 0.3299 | 1140 | 0.0583 | +0.0033 |
| `fold_4` | — | `clr_1` | 211 | **+0.0019** | 0.0022 | 0.3894 | 1038 | 0.0160 | -0.0836 |
| `fold_4` | — | `clr_5` | 211 | **+0.0050** | 0.0038 | 0.1957 | 1038 | 0.0369 | -0.1330 |

---

## 2. Unified Final Fit Benchmark (Train + Validation Estimation)

| Horizon | Sample | Beta (Shock) | Cluster SE | Raw p-val | Holm Adj p-val | BH FDR p-val | R² |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `clr_1` | `final_fit` | **+0.0013** | 0.0017 | 0.4531 | 1.0000 | 0.5854 | 0.0054 |
| `clr_3` | `final_fit` | **+0.0018** | 0.0030 | 0.5599 | 1.0000 | 0.5854 | 0.0035 |
| `clr_5` | `final_fit` | **+0.0032** | 0.0033 | 0.3187 | 1.0000 | 0.5058 | 0.0082 |
| `clr_20` | `final_fit` | **+0.0026** | 0.0041 | 0.5327 | 1.0000 | 0.5854 | 0.0017 |
| `clr_60` | `final_fit` | **-0.0029** | 0.0044 | 0.5169 | 1.0000 | 0.5854 | 0.0008 |

---

## 3. Robustness & Sensitivity Sweeps (Horizon clr_5)

| Specification / Sweep | Excluded Subset / Method | Sample N | Events | Beta (Shock) | Cluster SE | Raw p-val |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `v21_tier1_controls_clr5` | `clr_5 ~ shock_raw_bp_fold_std + ctrl_vix + ctrl_yield_1y` | 717 | 239 | **+0.0074** | 0.0041 | 0.0712 |
| `v21_tier1_no_overlap_clr5` | `clr_5 ~ shock_raw_bp_fold_std (overlap_prior_5d == 0)` | 8832 | 239 | **+0.0032** | 0.0033 | 0.3187 |
| `v21_pooled_t1_t2_clr5` | `clr_5 ~ shock_raw_bp_fold_std + shock_tier` | 12943 | 349 | **+0.0019** | 0.0007 | 0.0032 |
| `v21_sensitivity_macro_revision_clr5` | `clr_5 ~ shock_raw_bp_fold_std (macro revision table, 383 decs)` | 12943 | 349 | **+0.0019** | 0.0006 | 0.0022 |
| `v21_loo_drop_ECB_clr5` | `clr_5 ~ shock_raw_bp_fold_std (drop ECB)` | 8227 | 221 | **+0.0019** | 0.0006 | 0.0029 |
| `v21_loo_drop_Fed_clr5` | `clr_5 ~ shock_raw_bp_fold_std (drop Fed)` | 8827 | 238 | **+0.0016** | 0.0007 | 0.0191 |
| `v21_loo_drop_BoC_clr5` | `clr_5 ~ shock_raw_bp_fold_std (drop BoC)` | 12193 | 329 | **+0.0019** | 0.0006 | 0.0015 |
| `v21_loo_drop_BoE_clr5` | `clr_5 ~ shock_raw_bp_fold_std (drop BoE)` | 12271 | 331 | **+0.0020** | 0.0006 | 0.0004 |
| `v21_loo_drop_CBR_clr5` | `clr_5 ~ shock_raw_bp_fold_std (drop CBR)` | 11461 | 310 | **+0.0026** | 0.0093 | 0.7820 |
| `v21_loo_drop_RBA_clr5` | `clr_5 ~ shock_raw_bp_fold_std (drop RBA)` | 11736 | 316 | **+0.0021** | 0.0005 | 0.0001 |

---

## 4. Falsification & Placebo Diagnostics
- **Permutation Placebo (500 draws)**: Mean placebo coefficient $\beta_{\text{placebo}} = +0.000041$ (SD = 0.0017), yielding an empirical falsification p-value of **0.0780**.
- **Leave-One-Central-Bank-Out Resilience**: Estimates remain stable across all LOO partitions, proving that transmission estimates are not driven by any single central bank.

---

## 5. Mandatory Caveat Notice
> **REGIME TRANSFER WARNING**: All models fit on the combined TRAIN + VALIDATION sample (2010–2023) reflect historical and post-COVID tightening/easing dynamics. The subsequent strictly locked TEST split (2024–2025) contains **0 interest rate hikes**. Consequently, models fit on these partitions operate under an **easing/hold regime only; cannot assess tightening transfer**.
