# MoTrans-15: V2.1 Exploratory Model Specification Registry

This document pre-declares all exploratory empirical model specifications for the **MoTrans-15 v2.1** dataset prior to cross-validation evaluation, establishing multiplicity adjustment protocols and falsification tests.

---

## 1. Multiplicity Adjustment Framework

To control false discovery across multi-horizon event windows ($W \in \{1, 3, 5, 20, 60\}$) and multi-country panels, all reported p-values are evaluated alongside:
1. **Holm-Bonferroni (FWER)**: Step-down adjusted p-values ensuring strong control of family-wise error rate at $\alpha = 0.05$.
2. **Benjamini-Hochberg (FDR)**: Step-up False Discovery Rate control maintaining expected false discovery proportion $q \le 0.05$.

---

## 2. Pre-Declared Specification Families

### Family A: Primary Transmission Models
- **SPEC-01: Baseline Tier 1 High-Frequency Surprise**
  $$\text{clr}_W = \alpha_i + \beta_W \cdot \text{shock\_std\_fold} + \epsilon_{i,t}$$
  Evaluated for $W \in \{1, 3, 5, 20, 60\}$ on Tier 1 (Fed & ECB). Standard errors clustered at decision level (`event_id`).
- **SPEC-02: Macroeconomic & Financial Controls**
  $$\text{clr}_W = \alpha_i + \beta_W \cdot \text{shock\_std\_fold} + \gamma_1 \cdot \text{ctrl\_vix} + \gamma_2 \cdot \text{ctrl\_yield\_1y} + \gamma_3 \cdot \text{ctrl\_cpi} + \epsilon_{i,t}$$
- **SPEC-03: Pooled Primary (Tier 1 + Tier 2 Primary) with Tier Indicator**
  $$\text{clr}_W = \alpha_i + \beta_W \cdot \text{shock\_std\_fold} + \delta \cdot \text{shock\_tier} + \beta_{\text{tier\_int}} (\text{shock\_std\_fold} \times \text{shock\_tier}) + \boldsymbol{\gamma}' \mathbf{X}_{i,t} + \epsilon_{i,t}$$
- **SPEC-04: Domestic vs. International Spillover Decomposition**
  $$\text{clr}_W = \alpha_i + \beta_{\text{dom}} (\text{shock\_std\_fold} \times \text{home\_market}) + \beta_{\text{spill}} (\text{shock\_std\_fold} \times (1 - \text{home\_market})) + \boldsymbol{\gamma}' \mathbf{X}_{i,t} + \epsilon_{i,t}$$

### Family B: Robustness & Sensitivity Sweeps
- **SPEC-05: Overlap Exclusion Sweep**
  Drop events where prior policy decisions occurred within the look-back window (`overlap_prior_Wd == 0`).
- **SPEC-06: Leave-One-Central-Bank-Out (LOO-CB)**
  Iteratively drop one central bank at a time (Fed, ECB, BoE, BoC, RBA, CBR) to ensure estimates are not driven by a single sovereign authority.
- **SPEC-07: Winsorized Shocks at $\pm 4.0$ SD**
  Re-estimate baseline models using `shock_std_w` to verify outlier resilience against crisis episodes.
- **SPEC-08: Macro Revision Sensitivity Table**
  Re-estimate baseline and controlled models on `data/v2_1/release/sensitivity_macro_revision.parquet` (383 decisions, 14,201 rows) evaluating sensitivity to macroeconomic revisions.
- **SPEC-09: Secondary Holds Sensitivity Table**
  Estimate models on `data/v2_1/release/secondary_holds.parquet` (335 scheduled hold decisions, 12,454 rows) labeled strictly with `is_sensitivity = True`.

### Family C: Falsification & Placebo Tests
- **SPEC-10A: Temporal Placebo (Lead Returns)**
  Regress pre-announcement returns ($\text{clr}_{[-5, -1]}$) on upcoming policy surprise ($\text{shock\_std\_fold}$). Under valid identification and no look-ahead leakage, estimated coefficient must be statistically indistinguishable from zero ($\beta_{\text{placebo}} \approx 0$).
- **SPEC-10B: Permutation Placebo (Shuffled Shocks)**
  1,000 Monte Carlo permutations randomly shuffling policy surprise dates across trading calendar days while holding market return structure fixed.

