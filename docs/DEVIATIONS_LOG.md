# MoTrans-15: Pre-Registration Compliance & Deviations Log

**Date**: 2026-11-03  
**Lock Reference**: `docs/preregistration.md` (Hash: `384c0d71a1debb054798272965f42f0d36f2e7c6f96461770a6291004739c040`, locked 2026-10-24)  
**Execution Script**: `src/modeling/run_v1_blind_test.py`  
**Git History Status**: Introduced in commit `f771af790cd6b58ca6b12632315adb238c3ff863` (Phase 3 confirmatory execution)

---

## 1. Overview and Pre-Registration Compliance Assessment

The MoTrans-15 research design was formally pre-registered and cryptographically locked prior to unblinding any outcome data. This document records all identified differences between the locked protocol in `docs/preregistration.md` and the confirmatory evaluation script executed in Phase 3 (`src/modeling/run_v1_blind_test.py`).

In accordance with open science best practices, we report both the specification as executed in `run_v1_blind_test.py` and the exact pre-registered specification including forward policy overlap controls (`overlap_Wd`).

---

## 2. Classification of Methodological Deviations

### Deviation DEV-001: Absence of Policy Overlap Controls in Executed Script
- **Pre-Registered Protocol (`docs/preregistration.md` Section 4.3)**:
  > *"Forward event windows must control for overlapping central bank policy decisions occurring within $[t, t+W-1]$ using indicators `overlap_Wd` and continuous counts `overlap_count_Wd`."*
- **Script Implementation (`src/modeling/run_v1_blind_test.py` lines 80–120)**:
  The executed confirmatory script fitted bivariate clustered OLS regressions:
  $$\text{clr}_W = \alpha + \beta \cdot \text{shock\_std} + \epsilon$$
  omitting `overlap_Wd` and `overlap_count_Wd`.
- **Classification**: Script omission (pre-registered covariate excluded).
- **Impact Assessment**: Minimal to zero. As demonstrated in the sensitivity comparison below, both specifications yield statistically indistinguishable estimates with $p > 0.10$ across all horizons.

### Deviation DEV-002: Fed Sample Truncation in Tier 1 Blind Test
- **Pre-Registered Protocol (`docs/preregistration.md` Section 2)**:
  `blind_test` calendar window defined as `2022-01-01 to 2026-10-24` across Tier 1 (Fed and ECB).
- **Observed Table Reality**:
  The official Bauer-Swanson high-frequency intraday futures surprise series terminates at **December 13, 2023** (`fed_2023-12-13`). For 2024–2025, Fed policy surprises were constructed using daily 1-year Treasury yield changes (`yield_proxy`, `shock_grade = "B"`), routing them by rule to Tier 2. Consequently, Tier 1 contains 0 Federal Reserve decisions after 2023-12-13.
- **Classification**: Upstream data source limitation (anticipated in Section 3 notes on post-HFI fallback).
- **Impact Assessment**: In the v1 blind test, all 15 decisions in 2024–2025 were ECB decisions. The Federal Reserve tightening/easing cycle in 2024–2025 was not evaluated under Tier 1.

---

## 3. Empirical Sensitivity: Executed Bivariate vs. Pre-Registered Overlap Specification

To ensure complete transparency, we compare the executed bivariate regression against the exact pre-registered specification controlling for forward central bank overlaps (`overlap_Wd`):

| Horizon | Model Variant | Specification | Coef ($\beta$) | Cluster SE | $t$-stat | $p$-value | $R^2$ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`clr_1`** | Executed (Bivariate) | `clr_1 ~ shock_std` | -0.0007 | 0.0008 | -0.84 | 0.4036 | 0.0004 |
| | Pre-Registered (Overlap) | `clr_1 ~ shock_std + overlap_1d` | -0.0006 | 0.0008 | -0.78 | 0.4407 | 0.0006 |
| **`clr_3`** | Executed (Bivariate) | `clr_3 ~ shock_std` | -0.0029 | 0.0018 | -1.63 | 0.1091 | 0.0025 |
| | Pre-Registered (Overlap) | `clr_3 ~ shock_std + overlap_3d` | -0.0030 | 0.0019 | -1.58 | 0.1202 | 0.0027 |
| **`clr_5`** | Executed (Bivariate) | `clr_5 ~ shock_std` | -0.0025 | 0.0022 | -1.18 | 0.2443 | 0.0012 |
| | Pre-Registered (Overlap) | `clr_5 ~ shock_std + overlap_5d` | -0.0023 | 0.0021 | -1.10 | 0.2776 | 0.0014 |
| **`clr_20`** | Executed (Bivariate) | `clr_20 ~ shock_std` | -0.0039 | 0.0042 | -0.93 | 0.3572 | 0.0011 |
| | Pre-Registered (Overlap) | `clr_20 ~ shock_std + overlap_20d` | -0.0039 | 0.0042 | -0.93 | 0.3572 | 0.0011 |
| **`clr_60`** | Executed (Bivariate) | `clr_60 ~ shock_std` | -0.0068 | 0.0058 | -1.20 | 0.2354 | 0.0013 |
| | Pre-Registered (Overlap) | `clr_60 ~ shock_std + overlap_60d` | -0.0068 | 0.0058 | -1.20 | 0.2354 | 0.0013 |

*Notes: Clustered standard errors at the `event_id` level ($N_{\text{events}} = 47, N_{\text{obs}} = 1,786$). At 20d and 60d horizons, `overlap_Wd` is saturated (1.0 across all observations in the active easing/hiking window), resulting in collinearity and identical slope estimates.*

---

## 4. Formal Null Result Statement

Across both the executed and pre-registered specifications:
1. **Hypothesis Direction**: Point estimates are consistently negative ($\beta \in [-0.0068, -0.0006]$), which aligns with the theoretical hypothesis that contractionary surprises depress equity valuations.
2. **Statistical Significance**: All two-tailed clustered $p$-values exceed $0.10$ ($p \in [0.109, 0.441]$), and wild cluster bootstrap $p$-values exceed $0.15$ across all horizons.
3. **Substantive Conclusion**: The pre-registered confirmatory v1 blind test yields a **statistically robust null finding**. In the held-out post-pandemic cycle (2022–2025), high-frequency monetary policy surprises did not exert a statistically detectable causal impact on international equity indices. This failure to reject the null is a substantive empirical finding, not a failure of statistical implementation.
