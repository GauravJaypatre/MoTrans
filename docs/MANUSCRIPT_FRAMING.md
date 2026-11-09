# MoTrans-15: Manuscript Framing & Scientific Strategy

**Date**: 2026-11-04  
**Target Journals**: *Scientific Data* (Primary Target) / *Nature Communications* (Stretch only if all TODO-HUMAN items completed; Nature itself unsupported)  
**Status**: ACTIVE WORKING DRAFT  
**Guiding Principle**: Uncompromising scientific integrity; zero overclaiming; honest reporting of pre-registered null results.

---

## 1. Primary Empirical Result

The core empirical finding of the MoTrans-15 investigation is established by the pre-registered confirmatory blind test (`docs/preregistration.md`, executed on 47 held-out policy decisions from 2022 to 2025):

> **Primary Result**: High-frequency intraday monetary policy surprises (Federal Reserve Bauer-Swanson MPS and ECB EA-MPD 1-year OIS) did **not exert a statistically detectable causal impact on international equity indices** during the held-out 2022–2025 cycle ($p > 0.10$ across all pre-registered horizons $W \in \{1, 3, 5, 20, 60\}$ trading days; wild cluster bootstrap $p \in [0.159, 0.479]$).

While point estimates exhibit the negative direction predicted by economic theory ($\beta \in [-0.0068, -0.0006]$), standard errors are comparable in magnitude, yielding an unambiguous **statistical null finding**. A low-power statistical null does not establish economic decoupling; rather, the data do not detect transmission in this window.

---

## 2. Supported vs. Unsupported Claims

| Research Dimension | Scientifically Supported Claim | Unsupported / Rescoped Claim (Do Not Make) |
| :--- | :--- | :--- |
| **Causal Impact** | Pre-registered high-frequency transmission to equity returns yields a statistically robust null result in the held-out sample. | *Do not claim* that central bank announcements predictably move global equity indices across multi-day horizons, or that the null proves structural decoupling. |
| **Cross-Border Spillovers** | International spillovers from Fed and ECB surprises are statistically indistinguishable from zero ($p \ge 0.21$). | *Do not claim* robust global financial spillovers during the post-pandemic tightening cycle. |
| **Out-of-Sample Transfer** | The held-out test split benchmarks model generalization exclusively during an easing/hold regime (0 interest rate hikes). | *Do not claim* out-of-sample validity for contractionary tightening regimes. |
| **Instrument Precision** | Daily sovereign yield proxies contain ~67% non-HFI background market noise ($R^2 = 0.3305$ vs HFI on common decisions). | *Do not claim* that daily yield proxies are functionally equivalent to high-frequency intraday surprise measures. |
| **Lead Placebo Falsification** | In pre-event lead placebos ($t-5$ to $t-1$), the lead placebo did not detect pre-announcement contamination ($\beta$, SE, $p$ reported); this does not rule out contamination. | *Do not claim* that Tier 2 passes the lead placebo or that contamination is definitively ruled out. |
| **Emerging Markets** | High-frequency analysis is methodologically restricted to Developed Markets due to timing provenance limitations. | *Do not claim* causal transmission conclusions for Brazil, Mexico, or India (quarantined in `excluded_rows`). |
| **Inference Framework** | Clustered standard errors are mandatory due to high intracluster correlation ($ICC \approx 0.15 - 0.25$), reducing effective $N$ by ~90%. | *Do not report* unclustered or naive OLS standard errors. |
| **Exploratory Multiplicity** | Exploratory significance in pooled models is eliminated after Holm-Bonferroni family-wise error adjustment ($p_{\text{Holm}} = 0.1804$). | *Do not claim* statistically significant transmission based on uncorrected exploratory p-values. |

---

## 3. Approved Manuscript Title & Scope Boundaries

### Approved Headline Title
> **MoTrans-15: Monetary policy surprises and equity-index responses for the largest economies, 2010-2025**

- **Modeling Scope**: Strictly six central banks (Federal Reserve, European Central Bank, Bank of England, Bank of Canada, Reserve Bank of Australia, Central Bank of Russia).
- **Communication Scope Exclusion**: Zero mention of "central bank communication" in title or primary modeling framing (statement topic/tone labels are quarantined until formal double-annotation and adjudication are executed).
- **Economy Scope Discipline**: Zero claim of "15 economies" for primary econometric modeling; the panel spans indices in 15 economies, but causal shock transmission models are strictly estimated on the six central banks with verified shock series.

---

## 4. Statistical Power, Corrected MDE & Outlier Distortion

### 4.1 Statistical Power & Minimum Detectable Effect (MDE) Table
All power calculations are generated from `scripts/power_analysis.py` (`outputs/modeling/power_analysis_mde.csv`) at 80% statistical power ($\alpha = 0.05$, two-sided):

| Estimation Design | Decision Count ($N_{\text{decs}}$) | Event Rows ($N_{\text{obs}}$) | Untrimmed Asymptotic Cluster SE | Untrimmed Wild Bootstrap SE | Trimmed Top 1% SE | Headline Robust SE | Untrimmed Asymptotic MDE (bp) | Untrimmed Wild Bootstrap MDE (bp) | Conservative Headline MDE (bp) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tier 1 Final Fit** | 239 | 8,832 | 0.003252 | 0.003600 | 0.003274 | **0.003600** | 91.47 bp | 101.27 bp | **101.27 bp** |
| **Tier 2 Primary Final Fit** | 110 | 4,111 | 0.001302 | 0.001389 | 0.006107 | **0.006107** | 36.82 bp | 39.28 bp | **172.65 bp** |
| **Pooled Final Fit** | 349 | 12,943 | 0.000653 | 0.000713 | 0.004239 | **0.004239** | 18.35 bp | 20.03 bp | **119.10 bp** |
| **Full Test Split (Sample A)** | 70 | 2,590 | 0.001458 (proj) | 0.001594 (proj) | 0.009466 (proj) | **0.009466** | 41.46 bp | 45.33 bp | **269.12 bp** |
| **Pristine Test Split (Sample B)**| 56 | 2,072 | 0.001630 (proj) | 0.001782 (proj) | 0.010583 (proj) | **0.010583** | 46.53 bp | 50.87 bp | **302.06 bp** |

### 4.2 Methodological Note on Pooled MDE and Influence Sensitivity
> **METHODOLOGICAL NOTE ON POOLED MDE AND INFLUENCE SENSITIVITY**:
> An earlier draft of the power analysis reported an untrimmed asymptotic pooled MDE of **18.35 bp** per 1 SD shock ($SE = 0.000653$). 
> Econometric leverage auditing in Phase 0 demonstrated that this asymptotic standard error is heavily compressed by a single high-leverage event: `cbr_2014-12-16` (the Central Bank of Russia emergency 650 bp overnight rate hike, where policy decision `size_bp = 650.0`, sovereign 1-year yield proxy shock `shock_raw_bp = 499.0`, and `shock_tier = 2`).
> In ordinary least squares, a single massive regressor outlier inflates the sample variance $(X'X)$ in the denominator of $(X'X)^{-1}$, creating a mechanically compressed asymptotic standard error.
> When trimming the top 1% most influential events, the standard error is $0.004239$, yielding a **conservative headline MDE of 119.10 bp**.
> The pooled MDE of 119.10 bp is reported as the **"conservative headline MDE after trimming the top 1% influential events"**, presented side by side with the untrimmed asymptotic (18.35 bp) and wild bootstrap (20.03 bp) MDEs, rather than as an "error correction" or "+549% distortion". Both untrimmed and trimmed figures are reported together to ensure complete methodological transparency.

### 4.3 Robust Influence Handling Protocol
To ensure empirical transparency and eliminate any possibility of post-hoc sample pruning:
1. **Primary Headline Model**: Estimated on the **full, unpruned sample** ($N=349$ for pooled, $N=239$ for Tier 1) using restricted wild cluster bootstrap at `event_id`. Outliers are strictly **not dropped** from the primary specification.
2. **Pre-Declared Robustness Check**: Alongside every headline result, authors report a pre-declared sensitivity check estimating the exact same model after excluding the single most influential event (`cbr_2014-12-16`, policy hike `size_bp = 650.0`, sovereign yield proxy shock `shock_raw_bp = 499.0`, `shock_tier = 2`).

---

## 5. Multiplicity Summary across Headline Specifications

The table below summarizes headline exploratory specifications across raw inference, wild cluster bootstrap, 5,000-permutation empirical placebos, and full-ledger multiplicity corrections across all 123 model variations logged in `outputs/modeling/ledger.csv`:

| Headline Specification | Coef ($\beta$) | Cluster SE | Raw $p$ | Wild Boot $p$ | 5,000-Perm Empirical $p$ | Holm $p$ (Full Ledger) | BH $q$ (Full Ledger) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tier 1 Baseline (`clr_5`, final_fit)** | +0.0032 | 0.0032 | 0.3187 | 0.3664 | 0.0534 | 1.0000 | 0.5851 |
| **Pooled Tier 1 + Tier 2 (`clr_5`, final_fit)** | +0.0019 | 0.0006 | 0.0032 | 0.5686 | 0.0506 | 0.1804 | 0.0328 |
| **Macro Revision Sensitivity (`clr_5`, final_fit)** | +0.0019 | 0.0006 | 0.0022 | 0.5706 | 0.0506 | 0.1286 | 0.0328 |

**Core Multiplicity Finding**: **No headline specification provides evidence of tightening transfer after full-ledger multiplicity and permutation inference.**

---

## 6. Journal Fit Assessment

### Target A: *Scientific Data* (Descriptor) — Primary Target
- **Suitability**: **Exceptional (Primary Recommended Venue)**.
- **Core Strengths**:
  - Fully deterministic raw-to-final processing pipeline with bit-for-bit cryptographic verification (`DATA_FREEZE_v2_1.md`).
  - Standardized temporal splits with leakage-proof code guardrails (`src/model_guard.py`).
  - Comprehensive data dictionaries, quality scorecards, and multi-tier provenance levels.
  - Restricted access deposit on Zenodo complying with intellectual property terms for financial market indices.

### Target B: *Nature Communications* (Article) — Stretch Venue Only
- **Suitability**: **Strictly a stretch venue contingent on all TODO-HUMAN deliverables being completed**.
- **Realistic Editorial Assessment**:
  - The confirmatory result is an empirical null, and a low-power null in a turbulent post-pandemic transition does not definitively establish structural decoupling.
  - The test split contains zero interest rate hikes and zero Fed Tier 1 decisions, limiting generalizability.
  - *Nature Communications* requires complete second-source price validation, independent human statement annotations, and vendor permissions that are currently unfinished TODO-HUMAN items.
  - *Nature* itself is **completely unsupported** by this design and data asset. Positioning this work for *Nature* would constitute gross overclaiming. *Scientific Data* represents the honest, fully defensible primary submission venue.

---

## 7. Related Literature Integration (`TODO-HUMAN`)

The final manuscript will contextualize these findings within key literature streams:
1. **High-Frequency Identification & Fed Surprises**:
   - Kuttner (2001); Gürkaynak, Sack, & Swanson (2005); Nakamura & Steinsson (2018); Bauer & Swanson (2023).
2. **European Monetary Transmission & EA-MPD**:
   - Altavilla, Brugnolini, Gürkaynak, Motto, & Ragusa (2019).
3. **International Monetary Spillovers**:
   - Miranda-Agrippino & Rey (2020); Dedola, Rivolta, & Stracca (2017); Rey (2015).
4. **Information Effects vs. Pure Monetary Shocks**:
   - Jarociński & Karadi (2020); Cieslak & Schrimpf (2019).
5. **Pre-Registration & Research Integrity in Economics**:
   - Christensen & Miguel (2018); Olken (2015); Camerer et al. (2016).

> **LITERATURE SYNTHESIS ACTION (`TODO-HUMAN`)**:  
> Exhaustive narrative literature review, citation synthesis, and author attribution are designated for human domain expert completion (`TODO-HUMAN`). No citations or historical claims have been invented.
