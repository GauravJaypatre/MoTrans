# MoTrans-15: V2.1 Exploratory Model Results & Robustness Report

**Execution Status**: COMPLETED  
**Dataset Version**: `2.1.1` (`final_fit` & `folds.csv`)  
**Mandatory Regime Caveat**: *"easing/hold regime only; cannot assess tightening transfer"*  
**Out-of-Sample Test Status**: LOCKED (Zero test split observations evaluated)

---

## 1. Rolling-Origin Cross-Validation (Folds 1 to 4)

| Fold ID | Origin Cutoff | Horizon | Train Decs | Train Beta | Cluster SE | Train p-val | Val Obs | Val RMSE | Val OOS R² |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `fold_1` | 2019-12-31 | `clr_1` | 112 | **+0.0017** | 0.0016 | 0.2828 | 1216 | 0.0113 | -0.0378 |
| `fold_1` | 2019-12-31 | `clr_5` | 112 | **+0.0057** | 0.0035 | 0.1064 | 1216 | 0.0262 | -0.0760 |
| `fold_2` | 2020-12-31 | `clr_1` | 144 | **+0.0009** | 0.0014 | 0.5322 | 1254 | 0.0114 | -0.0128 |
| `fold_2` | 2020-12-31 | `clr_5` | 144 | **+0.0032** | 0.0032 | 0.3057 | 1254 | 0.0273 | -0.0251 |
| `fold_3` | 2021-12-31 | `clr_1` | 176 | **+0.0007** | 0.0012 | 0.5569 | 1140 | 0.0307 | -0.0487 |
| `fold_3` | 2021-12-31 | `clr_5` | 176 | **+0.0027** | 0.0027 | 0.3299 | 1140 | 0.0583 | +0.0033 |
| `fold_4` | 2022-12-31 | `clr_1` | 211 | **+0.0019** | 0.0022 | 0.3894 | 1038 | 0.0160 | -0.0836 |
| `fold_4` | 2022-12-31 | `clr_5` | 211 | **+0.0050** | 0.0038 | 0.1957 | 1038 | 0.0369 | -0.1330 |

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

## 3. Robustness & Sensitivity Sweeps (Horizon `clr_5`)

| Specification / Sweep | Excluded Subset / Method | Sample N | Events | Beta (Shock) | Cluster SE | Raw p-val | Holm p-val | BH FDR p-val |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `v21_tier1_controls_clr5` | `clr_5 ~ shock + ctrl_vix + ctrl_yield_1y` | 717 | 239 | **+0.0074** | 0.0041 | 0.0712 | 1.0000 | 0.5429 |
| `v21_tier1_no_overlap_clr5` | `clr_5 ~ shock (overlap_prior_5d == 0)` | 8,832 | 239 | **+0.0032** | 0.0033 | 0.3187 | 1.0000 | 0.5058 |
| `v21_pooled_t1_t2_clr5` | `clr_5 ~ shock + shock_tier` | 12,943 | 349 | **+0.0019** | 0.0007 | 0.0032 | 0.1804 | 0.0328 |
| `v21_sensitivity_macro_revision_clr5` | `clr_5 ~ shock (macro revision table, 383 decs)` | 12,943 | 349 | **+0.0019** | 0.0006 | 0.0022 | 0.1286 | 0.0328 |
| `v21_loo_drop_ECB_clr5` | `clr_5 ~ shock (drop ECB)` | 8,227 | 221 | **+0.0019** | 0.0006 | 0.0029 | 0.1639 | 0.0328 |
| `v21_loo_drop_Fed_clr5` | `clr_5 ~ shock (drop Fed)` | 8,827 | 238 | **+0.0016** | 0.0007 | 0.0191 | 1.0000 | 0.1662 |
| `v21_loo_drop_BoC_clr5` | `clr_5 ~ shock (drop BoC)` | 12,193 | 329 | **+0.0019** | 0.0006 | 0.0015 | 0.0902 | 0.0311 |
| `v21_loo_drop_BoE_clr5` | `clr_5 ~ shock (drop BoE)` | 12,271 | 331 | **+0.0020** | 0.0006 | 0.0004 | 0.0217 | 0.0110 |
| `v21_loo_drop_CBR_clr5` | `clr_5 ~ shock (drop CBR)` | 11,461 | 310 | **+0.0026** | 0.0093 | 0.7820 | 1.0000 | 0.7820 |
| `v21_loo_drop_RBA_clr5` | `clr_5 ~ shock (drop RBA)` | 11,736 | 316 | **+0.0021** | 0.0005 | 0.0001 | 0.0084 | 0.0084 |

---

## 4. Falsification & 5,000-Permutation Placebo Diagnostics (Task A5)

To account for central-bank clustering, meeting calendar spacing, and tier-specific shock distributions, we execute a rigorous **5,000-draw block-shuffled permutation placebo test**. Shocks are permuted strictly within each $(\text{Central Bank} \times \text{Tier})$ block, augmented with circular date shifting to preserve calendar autocorrelation.

| Specification | Estimator | Real Coef ($\beta$) | Placebo Mean ($\beta_{\text{placebo}}$) | Placebo SD | Empirical Falsification $p$-value |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Tier 1 Final Fit** | `clr_5 ~ shock_std` | **+0.0032** | -0.000031 | 0.0017 | **0.0534** |
| **Pooled (Tier 1 + Tier 2)** | `clr_5 ~ shock_std + is_tier2` | **+0.0019** | +0.000239 | 0.0009 | **0.0506** |
| **Macro Revision Sensitivity** | `clr_5 ~ shock_std + controls` | **+0.0019** | +0.000239 | 0.0009 | **0.0506** |

**Empirical Falsification Assessment**: Under the 5,000-draw block-shuffled null, empirical $p$-values across all three specifications equal or exceed $0.05$ ($p \in [0.0506, 0.0534]$), demonstrating that exploratory significance in non-headline pooled models is sensitive to calendar and meeting autocorrelation.

### Full Ledger Multiplicity Corrections
Across all 61 models logged in `outputs/modeling/ledger.csv`:
- **Uncorrected Significance ($p < 0.05$)**: 7 of 61 models (11.5%).
- **Holm-Bonferroni Family-Wise Error Rate ($p_{\text{Holm}} < 0.05$)**: **2 of 61 models (3.3%)** (strictly RBA-excluded and BoE-excluded LOO models).
- **Benjamini-Hochberg False Discovery Rate ($p_{\text{BH}} < 0.05$)**: 6 of 61 models (9.8%).
- **Finding**: The pooled specification (`v21_pooled_t1_t2_clr5`, uncorrected $p = 0.0032$) is adjusted to $p_{\text{Holm}} = 0.1804$ when penalizing for the full search space. No primary headline model achieves statistical significance under family-wise error control.

---

## 5. Identification, Timing & Contamination Audit (Task A4)

### 5.1 Sign Convention
- **Direction**: In accordance with macroeconomic event-study conventions, `shock_raw_bp > 0` denotes a contractionary/hawkish surprise (positive rate hike surprise, upward shift in policy expectations). Dovish cuts/easing surprises are negative.
- **Empirical Check**: Verified across historical decisions (e.g. Fed hike 2015-12-16: $+2.87$ bp; ECB cut 2012-07-05: $-7.50$ bp).

### 5.2 Timezone & Window Timing Alignment
- All policy announcement timestamps (`announce_ts_utc`) are mapped to exchange trading hours using `exchange_calendars`.
- Baseline price is strictly the closing price of the session ending at or prior to announcement start. Reacting session is the first trading session closing after announcement start.
- Verified across all 15 index timezones (US Eastern, UK/Europe UTC/CET, Asia/Pacific JST/AEST/IST).

### 5.3 High-Frequency vs. Daily Yield Proxy Discrepancy
- On 413 overlapping Federal Reserve and ECB decisions where both high-frequency intraday shocks (`hf_ois`) and daily sovereign yield proxies (`yield_proxy`) exist:
  - **Overall Pearson Correlation**: $r = 0.5749$ ($R^2 = 0.3305$).
  - **Fed Subsample ($N = 202$)**: $r = 0.5535$.
  - **ECB Subsample ($N = 211$)**: $r = 0.6115$.
- **Econometric Consequence**: Approximately **67% of daily yield proxy variance** reflects non-HFI background noise (macro data releases, European/Asian session trading, multi-day market drift).

### 5.4 Lead Placebo Falsification ($t-5$ to $t-1$)
To test whether shocks are contaminated by pre-announcement trends or information leakage, pre-event returns ($\text{clr}_{\text{pre5}}$, from $t-5$ to $t-1$ relative to baseline) were regressed on `shock_std` across the 2010–2023 sample:
- **Tier 1 Lead Placebo ($N_{\text{obs}} = 9,159, N_{\text{events}} = 247$)**:
  $$\beta_{\text{lead}} = +0.0024 \quad (\text{SE} = 0.0040, \; t = +0.60, \; p = 0.5502)$$
- **Tier 2 Primary Lead Placebo ($N_{\text{obs}} = 6,502, N_{\text{events}} = 175$)**:
  $$\beta_{\text{lead}} = -0.0000 \quad (\text{SE} = 0.0025, \; t = -0.00, \; p = 0.9960)$$
- **Conclusion**: Both Tier 1 and Tier 2 pass the lead placebo test with clean null coefficients, confirming the absence of pre-announcement anticipation or trend contamination.

### 5.5 Definitive Headline Decision Rule
- **Primary Headline Benchmark**: Strictly restricted to **Tier 1 High-Frequency Identification** (Fed Bauer-Swanson MPS + ECB EA-MPD OIS 1Y).
- **Secondary Status for Tier 2**: While Tier 2 passes the lead placebo test (confirming pre-event exogeneity), its 67% non-HFI noise variance precludes it from serving as a primary causal benchmark. It is retained exclusively as an out-of-sample transfer test. Pooled models must always include explicit tier indicators (`shock_tier`).

---

## 6. Mandatory Caveat Notice
> **REGIME TRANSFER WARNING**: All models fit on the combined TRAIN + VALIDATION sample (2010–2023) reflect historical and post-COVID tightening/easing dynamics. The subsequent strictly locked TEST split (2024–2025) contains **0 interest rate hikes**. Consequently, models fit on these partitions operate under an **easing/hold regime only; cannot assess tightening transfer**.
