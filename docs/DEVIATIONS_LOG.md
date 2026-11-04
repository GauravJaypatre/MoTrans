# MoTrans-15: Pre-Registration Compliance & Deviations Log

**Date**: 2026-11-04  
**Lock Reference**: `docs/preregistration.md` (Hash: `384c0d71a1debb054798272965f42f0d36f2e7c6f96461770a6291004739c040`, locked 2026-10-24)  
**Execution Script**: `src/modeling/run_v1_blind_test.py`  
**Git History Status**: Introduced in commit `f771af790cd6b58ca6b12632315adb238c3ff863` (Phase 3 confirmatory execution)

---

## 1. Overview and Pre-Registration Compliance Assessment

The MoTrans-15 research design was formally pre-registered and cryptographically locked in `docs/preregistration.md` prior to unblinding any outcome data. This document records all identified differences between the locked protocol and the confirmatory evaluation script executed in Phase 3 (`src/modeling/run_v1_blind_test.py`).

In accordance with strict open science standards, the pre-registered specification controlling for forward policy overlaps (`overlap_Wd`) is treated as the **confirmatory primary result**. The executed bivariate regression (`clr_W ~ shock_std`) is classified as a **labelled deviation**.

---

## 2. Classification of Methodological Deviations

### Deviation DEV-001: Absence of Policy Overlap Controls in Executed Blind Test Script
- **Pre-Registered Protocol (`docs/preregistration.md` Section 4.3 & Section 5)**:
  > *"Forward event windows must control for overlapping central bank policy decisions occurring within $[t, t+W-1]$ using indicators `overlap_Wd` and continuous counts `overlap_count_Wd`."*  
  > *"Mandatory inclusion of forward window policy overlap controls (`overlap_1d` to `overlap_60d` and counts) to isolate multi-central bank confounding at medium and long horizons."*
- **Script Implementation (`src/modeling/run_v1_blind_test.py` lines 80–120)**:
  The executed confirmatory script fitted bivariate clustered OLS regressions:
  $$\text{clr}_W = \alpha + \beta \cdot \text{shock\_std} + \epsilon$$
  omitting `overlap_Wd` and `overlap_count_Wd`.
- **Classification**: **Specification Change (Requires Author Approval)**.  
  *Note on classification*: This deviation is formally classified as a **specification change, not a bug fix**, and is designated **"requires author approval"**. In accordance with pre-registration auditing guidelines, this is an unapproved divergence from the registered protocol.
- **Confirmatory Status**: The pre-registration treats the overlap-controlled specification ($\text{clr}_W \sim \text{shock\_std} + \text{overlap\_Wd}$) as **confirmatory (primary result)**. The bivariate model ($\text{clr}_W \sim \text{shock\_std}$) is a **labelled deviation**.

### Deviation DEV-002: Fed Sample Truncation in Tier 1 Blind Test
- **Pre-Registered Protocol (`docs/preregistration.md` Section 2)**:
  `blind_test` calendar window defined as `2022-01-01 to 2026-10-24` across Tier 1 (Fed and ECB).
- **Observed Table Reality**:
  The official Bauer-Swanson high-frequency intraday futures surprise series terminates at **December 13, 2023** (`fed_2023-12-13`). For 2024–2025, Fed policy surprises were constructed using daily 1-year Treasury yield changes (`yield_proxy`, `shock_grade = "B"`), routing them by rule to Tier 2. Consequently, Tier 1 contains 0 Federal Reserve decisions after 2023-12-13.
- **Classification**: Upstream data source limitation (anticipated in Section 3 notes on post-HFI fallback).
- **Impact Assessment**: In the v1 blind test, all 15 decisions in 2024–2025 were ECB decisions. The Federal Reserve tightening/easing cycle in 2024–2025 was not evaluated under Tier 1.

---

## 3. Side-by-Side Comparison: Primary Confirmatory (Overlap) vs. Labelled Deviation (Bivariate)

Both specifications were evaluated on the exact 47-decision held-out v1 sample ($N_{\text{obs}} = 1,786$) across all five pre-registered horizons using `scripts/generate_v1_compliance_diff.py`. Clustered standard errors are clustered at the `event_id` level, with wild cluster bootstrap (Rademacher 999 draws) and effective sample size ($N_{\text{eff}}$) accounting for within-event correlation:

| Horizon | Specification Type | Econometric Model | Coef ($\beta$) | Cluster SE | $p$ (Cluster) | $p$ (Wild Boot) | $N_{\text{eff}}$ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`clr_1`** | **Primary Confirmatory** | `clr_1 ~ shock_std + overlap_1d` | **-0.0006** | 0.0008 | 0.4407 | 0.4785 | 215.5 |
| | Labelled Deviation | `clr_1 ~ shock_std` | **-0.0007** | 0.0008 | 0.4036 | 0.4424 | 215.5 |
| **`clr_3`** | **Primary Confirmatory** | `clr_3 ~ shock_std + overlap_3d` | **-0.0030** | 0.0019 | 0.1202 | 0.1752 | 110.1 |
| | Labelled Deviation | `clr_3 ~ shock_std` | **-0.0029** | 0.0018 | 0.1091 | 0.1592 | 110.1 |
| **`clr_5`** | **Primary Confirmatory** | `clr_5 ~ shock_std + overlap_5d` | **-0.0023** | 0.0021 | 0.2776 | 0.3153 | 115.1 |
| | Labelled Deviation | `clr_5 ~ shock_std` | **-0.0025** | 0.0022 | 0.2443 | 0.2753 | 115.1 |
| **`clr_20`** | **Primary Confirmatory** | `clr_20 ~ shock_std + overlap_20d` | **-0.0039** | 0.0042 | 0.3572 | 0.3463 | 140.4 |
| | Labelled Deviation | `clr_20 ~ shock_std` | **-0.0039** | 0.0042 | 0.3572 | 0.3463 | 140.4 |
| **`clr_60`** | **Primary Confirmatory** | `clr_60 ~ shock_std + overlap_60d` | **-0.0068** | 0.0058 | 0.2354 | 0.2492 | 150.8 |
| | Labelled Deviation | `clr_60 ~ shock_std` | **-0.0068** | 0.0058 | 0.2354 | 0.2492 | 150.8 |

*Econometric Note on Medium/Long Horizons*: At horizons $W = 20$ and $W = 60$ trading days, every policy decision in the 2022–2025 window exhibits at least one overlapping central bank decision (`overlap_20d = 1` and `overlap_60d = 1` across all 1,786 rows). Because `overlap_Wd` is constant, it is mathematically collinear with the regression intercept; consequently, the slope coefficient $\beta$, clustered standard error, and wild bootstrap $p$-value are mathematically identical between the bivariate and overlap specifications.

---

## 4. Pre-Registered Success Criteria Assessment

### Verbatim Pre-Registered Objectives & Benchmark Criteria
From `docs/preregistration.md`:
1. **Section 1 (Study Overview & Objective)**:
   > *"The research design evaluates:*  
   > *1. Domestic Equity Transmission: The immediate and persistent reaction of broad market, banking sector, and small-cap equity indices to domestic policy surprises.*  
   > *2. Cross-Border Spillovers: The international transmission of US Federal Reserve and European Central Bank policy shocks to foreign equity markets.*  
   > *3. Transmission Channels: Decomposing responses across interest rate expectations, term premia, and equity risk premia."*
2. **Section 5 (Methodological Amendments)**:
   > *"Pre-specified that the definitive benchmark test of cross-border monetary transmission is evaluated on the held-out blind_test period (2022–2026) for Tier 1 high-frequency shocks."*

### One-Sentence Compliance & Success Assessment
**Neither the primary confirmatory specification nor the labelled deviation meets the pre-registered success criteria for demonstrating causal transmission to equities, as both models yield statistically indistinguishable null findings with two-tailed cluster p-values exceeding 0.10 and wild bootstrap p-values exceeding 0.15 across all five horizons.**
