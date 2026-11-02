# MoTrans-15: Pre-Registered V1 Confirmatory Blind Test Report

**Execution Status**: COMPLETED FIRST (Preserving Blinding Integrity)  
**Parent Release**: `v1.0-data-freeze`  
**Lock Document**: `docs/preregistration.md` (Hash: `384c0d71a1debb054798272965f42f0d36f2e7c6f96461770a6291004739c040`)  
**Evaluation Sample**: 47 Held-Out Decisions (Fed: 16, ECB: 31, 2022-01-26 to 2025-10-30; 1,786 event rows)

---

## 1. Headline Transmission Results (H1 & H2)

| Horizon | Shock Variable | Coef (beta) | Cluster SE | Two-Way SE | p (Cluster) | p (Wild Boot) | Effective N (N_eff) | R² |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `clr_1` | `shock_std` | **-0.0007** | 0.0008 | 0.0008 | 0.4036 | 0.4424 | 215.5 | 0.0041 |
| `clr_3` | `shock_std` | **-0.0029** | 0.0018 | 0.0018 | 0.1091 | 0.1592 | 110.1 | 0.0236 |
| `clr_5` | `shock_std` | **-0.0025** | 0.0022 | 0.0021 | 0.2443 | 0.2753 | 115.1 | 0.0121 |
| `clr_20` | `shock_std` | **-0.0039** | 0.0042 | 0.0042 | 0.3572 | 0.3463 | 140.4 | 0.0073 |
| `clr_60` | `shock_std` | **-0.0068** | 0.0058 | 0.0057 | 0.2354 | 0.2492 | 150.8 | 0.0095 |

---

## 2. Domestic vs. Cross-Border Decomposition

| Horizon | Component | Coef (beta) | Cluster SE | t-stat | p-value | R² |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `clr_1` | Domestic (Home) | **-0.0005** | 0.0016 | -0.31 | 0.7544 | 0.0042 |
| `clr_1` | Cross-Border (Spillover) | **-0.0007** | 0.0007 | -0.96 | 0.3357 | 0.0042 |
| `clr_5` | Domestic (Home) | **-0.0014** | 0.0025 | -0.54 | 0.5896 | 0.0126 |
| `clr_5` | Cross-Border (Spillover) | **-0.0028** | 0.0022 | -1.24 | 0.2136 | 0.0126 |

---

## 3. Methodological Observations & Verification
1. **Blinding Integrity**: This confirmatory test was executed prior to any exploratory model fitting on the v2.1 dataset.
2. **Effective Sample Size**: Because 38 international equity indices react simultaneously to each central bank announcement, high within-event intracluster correlation ($ICC \approx 0.15 - 0.25$) reduces the effective independent sample size from $N = 1,786$ to $N_{\text{eff}} \approx 120 - 180$.
3. **Inference Robustness**: P-values derived from one-way clustered standard errors, two-way clustered standard errors (event and index), and wild cluster bootstrap (Rademacher 999 draws) exhibit consistent significance profiles.
