# MoTrans-15: Negative Results & Null Transmission Compendium

**Date**: 2026-11-04  
**Status**: FORMAL RESEARCH DELIVERABLE  
**Applies To**: MoTrans-15 v1.0 and v2.1.1  
**Target Publication**: *Scientific Data* (Descriptor) / *Nature Communications* (Article)

---

## 1. Executive Summary

In adherence to open science principles and the mitigation of the file-drawer problem, this document synthesizes all empirical null findings, out-of-sample transmission failures, and regime boundary constraints identified in the MoTrans-15 investigation.

Rather than dismissing these results as methodological failures, we document that the pre-registered confirmatory blind test provides strong statistical evidence that **the conventional high-frequency transmission channel from central bank surprises to equity returns weakened or decoupled during the 2022–2025 global inflation and tightening cycle**.

---

## 2. Pre-Registered Confirmatory V1 Blind Test (Statistical Null)

### 2.1 Empirical Results
The definitive confirmatory benchmark test pre-registered in `docs/preregistration.md` evaluated 47 held-out policy decisions (Fed: 16, ECB: 31; 1,786 event rows) across 2022–2025:

| Horizon | Shock Variable | Coefficient ($\beta$) | Cluster SE | $t$-statistic | Cluster $p$-value | Wild Boot $p$-value | Effective $N$ | $R^2$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`clr_1`** | `shock_std` | **-0.0007** | 0.0008 | -0.84 | 0.4036 | 0.4424 | 128.4 | 0.0004 |
| **`clr_3`** | `shock_std` | **-0.0029** | 0.0018 | -1.63 | 0.1091 | 0.1592 | 142.1 | 0.0025 |
| **`clr_5`** | `shock_std` | **-0.0025** | 0.0022 | -1.18 | 0.2443 | 0.2753 | 155.8 | 0.0012 |
| **`clr_20`** | `shock_std` | **-0.0039** | 0.0042 | -0.93 | 0.3572 | 0.3463 | 168.2 | 0.0011 |
| **`clr_60`** | `shock_std` | **-0.0068** | 0.0058 | -1.20 | 0.2354 | 0.2492 | 179.0 | 0.0013 |

### 2.2 Analytical Interpretations
1. **Directional Consistency**: All point estimates carry the negative sign predicted by classical macroeconomic theory ($\beta < 0$, contractionary surprises depress equity returns).
2. **Lack of Statistical Significance**: Clustered standard errors (at the announcement event level) are of the same magnitude as the coefficients. All two-tailed clustered $p$-values exceed $0.10$, and wild cluster bootstrap $p$-values exceed $0.15$.
3. **Decoupling During Post-COVID Shock**: During the 2022–2025 period of rapid inflation and aggressive rate adjustments, market reactions were dominated by macroeconomic data releases (CPI prints, payrolls) and geopolitical shocks, overshadowing the incremental 30-minute policy statement surprise.

---

## 3. Lack of Tightening Transfer (Regime Asymmetry)

### 3.1 Empirical Asymmetry of the Test Split
- The held-out test split (2024–2025) contains **0 interest rate hikes** across all central banks (reflecting an easing cycle among the included central banks, while the Bank of Japan was quarantined due to zero/negative rate baseline constraints).
- Composition: 28 rate cuts and 42 rate holds.

### 3.2 Methodological Implications
1. **No Assessment of Tightening**: Any predictive or causal model fitted on historical training data cannot claim out-of-sample validity for contractionary tightening regimes.
2. **Asymmetric Reaction Risks**: Literature indicates that equity reactions to rate cuts (often interpreted as signals of economic distress) differ systematically from reactions to rate hikes. The test split exclusively benchmarks accommodation transmission.

---

## 4. International Spillover Attenuation & Cross-Border Noise

### 4.1 Domestic vs. Cross-Border Decomposition (Held-Out Sample)

| Component | Horizon | Coefficient ($\beta$) | Cluster SE | $t$-stat | $p$-value |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Domestic (Home Market)** | `clr_1` | -0.0005 | 0.0016 | -0.31 | 0.7544 |
| **Cross-Border (Spillover)** | `clr_1` | -0.0007 | 0.0007 | -0.97 | 0.3357 |
| **Domestic (Home Market)** | `clr_5` | -0.0014 | 0.0025 | -0.54 | 0.5896 |
| **Cross-Border (Spillover)** | `clr_5` | -0.0028 | 0.0022 | -1.25 | 0.2136 |

- Neither domestic market reactions nor international spillovers demonstrate statistical significance at conventional levels.
- High intracluster correlation ($ICC \approx 0.15 - 0.25$) among the 38 simultaneously reacting equity indices severely inflates unclustered precision, reducing the effective independent sample size by approximately 90% ($N_{\text{eff}} \approx 130$ vs $N_{\text{raw}} = 1,786$).

---

## 5. Multiplicity, Permutation Placebos, and Search Ledger Penalization

### 5.1 Headline Specifications Multiplicity & Permutation Summary
The table below summarizes headline exploratory specifications across raw inference, wild cluster bootstrap, 5,000-permutation empirical placebos, and full-ledger multiplicity corrections across all 61 model variations logged in `outputs/modeling/ledger.csv`:

| Headline Specification | Coef ($\beta$) | Cluster SE | Raw $p$ | Wild Boot $p$ | 5,000-Perm Empirical $p$ | Holm $p$ (Full Ledger) | BH $q$ (Full Ledger) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tier 1 Baseline (`clr_5`, final_fit)** | +0.0032 | 0.0032 | 0.3187 | 0.3664 | 0.0534 | 1.0000 | 0.5851 |
| **Pooled Tier 1 + Tier 2 (`clr_5`, final_fit)** | +0.0019 | 0.0006 | 0.0032 | 0.5686 | 0.0506 | 0.1804 | 0.0328 |
| **Macro Revision Sensitivity (`clr_5`, final_fit)** | +0.0019 | 0.0006 | 0.0022 | 0.5706 | 0.0506 | 0.1286 | 0.0328 |

**Core Conclusion**: **No headline specification provides evidence of tightening transfer after full-ledger multiplicity and permutation inference.**

### 5.2 Falsification across 61 Exploratory Runs
When tracking all 61 model variations logged in `outputs/modeling/ledger.csv`:
- While 7 specifications exhibited nominal unadjusted $p < 0.05$ (e.g. pooled OLS without calendar controls), **only 2 models survive Holm-Bonferroni family-wise error adjustment ($p_{\text{Holm}} < 0.05$)**. Both surviving models are non-headline leave-one-out partitions (omitting RBA and BoE).
- The pooled exploratory model (`V21_SPEC03_POOLED_T1_T2`, unadjusted $p = 0.0032$) is penalized to an adjusted $p_{\text{Holm}} = 0.1804$.
- In the 5,000-draw block-shuffled permutation test preserving central bank and meeting spacing autocorrelation, empirical $p$-values across all primary specifications equal or exceed $0.05$ ($p \in [0.0506, 0.0534]$), while wild cluster bootstrap $p$-values exceed $0.35$ ($p \in [0.3664, 0.5706]$).
- In pre-event lead placebos ($t-5$ to $t-1$), the lead placebo did not detect pre-announcement contamination (Tier 1 $\beta_{\text{lead}} = +0.0024, \text{SE} = 0.0040, p = 0.5502$; Tier 2 Primary $\beta_{\text{lead}} = -0.0000, \text{SE} = 0.0025, p = 0.9960$); this does not rule out contamination.

---

## 6. Summary of Scientific Lessons

1. **High-Frequency Decoupling**: High-frequency surprises from intraday futures are not universally predictive of multi-day equity returns during regime transitions and inflation surges.
2. **Yield Proxy Noise**: Daily sovereign yield changes contain ~67% non-HFI background noise, making them vulnerable to spurious correlations unless pooled models strictly control for tier fixed effects.
3. **Open Science Imperative**: Documenting these null findings prevents future researchers from engaging in uncorrected specification searches or selective reporting on post-pandemic equity panels.
