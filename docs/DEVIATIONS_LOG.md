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

## 4. Pre-Registered Success Criteria & Statistical Power Assessment

### Decision Rule Search in Pre-Registration
An exhaustive search of `docs/preregistration.md` (lines 1–91) and associated protocol documents was conducted for an explicit statistical decision rule (significance threshold $\alpha$, directional sign constraint, or minimum effect size).
- **Finding**: **No formal decision rule found.**
- `docs/preregistration.md` defines research objectives (Section 1), sample split dates (Section 2), identification tiers (Section 3), outcome equations and overlap controls (Section 4), and dated methodological amendments (Section 5). It does not specify a numerical rejection threshold or formal confirmatory success boundary.

### Confirmatory Assessment
**The pre-registration contained no formal success threshold; the confirmatory estimates are statistically indistinguishable from zero with wide intervals.**

Across both the primary confirmatory specification (`clr_W ~ shock_std + overlap_Wd`) and the labelled deviation (`clr_W ~ shock_std`), two-tailed cluster $p$-values exceed $0.10$ and wild cluster bootstrap $p$-values exceed $0.15$ across all five horizons.

### Minimum Detectable Effect (MDE) and Power Limitations
Because the held-out sample contains $N_{\text{events}} = 47$ decisions (16 Fed, 31 ECB), statistical power is fundamentally constrained. At nominal $\alpha = 0.05$ (two-tailed) and 80% power, the Minimum Detectable Effect is:
$$\text{MDE}_{80\%} = (t_{0.025, G-1} + t_{0.20, G-1}) \times \text{SE}_{\text{cluster}} \approx 2.802 \times \text{SE}_{\text{cluster}}$$

#### Table 2: Minimum Detectable Effect (MDE) across Horizons ($N_{\text{events}} = 47$)

| Horizon | Primary Confirmatory Spec | Estimated $\beta$ | Event-Cluster SE | 95% Confidence Interval | MDE (80% Power) | MDE in Basis Points |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **`clr_1`** | `clr_1 ~ shock_std + overlap_1d` | $-0.000620$ | $0.000804$ | $[-0.002195, +0.000956]$ | $0.002252$ | 22.5 bp |
| **`clr_3`** | `clr_3 ~ shock_std + overlap_3d` | $-0.002972$ | $0.001913$ | $[-0.006721, +0.000777]$ | $0.005360$ | 53.6 bp |
| **`clr_5`** | `clr_5 ~ shock_std + overlap_5d` | $-0.002261$ | $0.002083$ | $[-0.006344, +0.001822]$ | $0.005837$ | 58.4 bp |
| **`clr_20`** | `clr_20 ~ shock_std + overlap_20d` | $-0.003896$ | $0.004232$ | $[-0.012191, +0.004399]$ | $0.011858$ | 118.6 bp |
| **`clr_60`** | `clr_60 ~ shock_std + overlap_60d` | $-0.006837$ | $0.005761$ | $[-0.018129, +0.004455]$ | $0.016142$ | 161.4 bp |

*Note: All values generated by script from `outputs/modeling/v1_compliance_diff.csv`.*

### Methodological Interpretation
These MDE figures demonstrate that the confirmatory test has 80% power only to detect massive market reactions—exceeding **58.4 bp** at 5 days and **161.4 bp** at 60 days for a 1-SD monetary policy shock. Consequently, the empirical null result must be framed as a **low-power design with wide confidence intervals that encompass both zero and economically plausible effect sizes**, rather than definitive evidence of zero monetary transmission.
