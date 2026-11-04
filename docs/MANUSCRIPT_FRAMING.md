# MoTrans-15: Manuscript Framing & Scientific Strategy

**Date**: 2026-11-04  
**Target Journals**: *Scientific Data* (Data Descriptor — Primary Target) / *Nature Communications* (Article — Stretch Venue)  
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

## 3. Title Options

### Option 1 (Descriptive / Data-Centric — Target: *Scientific Data* — Primary Recommendation)
> **MoTrans-15: A Harmonized Leakage-Safe Multi-Country Benchmark of Central Bank Communication, Monetary Surprises, and Equity Reactions (2010–2025)**  
> *Framing*: Emphasizes the standardized multi-country data asset, cryptographic freeze, leakage-proof train/test architecture, and multi-horizon equity return panels across six major central banks.

### Option 2 (Benchmark & Low-Power Null Framing — Target: *Scientific Data* / Macro-Finance)
> **A Pre-Registered, Leakage-Safe Benchmark for Cross-Border Monetary Policy Transmission to Equities with a Low-Power Null Result Across Six Central Banks**  
> *Framing*: Centers on methodological transparency, pre-registration integrity, leakage guards, and the honest reporting of a low-power statistical null finding across Fed, ECB, BoE, BoC, RBA, and CBR decisions.

### Option 3 (Methodological & Multiplicity Framing — Alternative Descriptive Target)
> **Cross-Border Monetary Transmission to Equities: A Pre-Registered Benchmark, Multiplicity Penalization, and Low-Power Null Findings Across Six Major Central Banks**  
> *Framing*: Highlights econometric controls, cluster and permutation inference, instrument noise in daily yield proxies, and the full accounting of multiplicity in exploratory searches.

---

## 4. Multiplicity Summary across Headline Specifications

The table below summarizes headline exploratory specifications across raw inference, wild cluster bootstrap, 5,000-permutation empirical placebos, and full-ledger multiplicity corrections across all 61 model variations logged in `outputs/modeling/ledger.csv`:

| Headline Specification | Coef ($\beta$) | Cluster SE | Raw $p$ | Wild Boot $p$ | 5,000-Perm Empirical $p$ | Holm $p$ (Full Ledger) | BH $q$ (Full Ledger) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tier 1 Baseline (`clr_5`, final_fit)** | +0.0032 | 0.0032 | 0.3187 | 0.3664 | 0.0534 | 1.0000 | 0.5851 |
| **Pooled Tier 1 + Tier 2 (`clr_5`, final_fit)** | +0.0019 | 0.0006 | 0.0032 | 0.5686 | 0.0506 | 0.1804 | 0.0328 |
| **Macro Revision Sensitivity (`clr_5`, final_fit)** | +0.0019 | 0.0006 | 0.0022 | 0.5706 | 0.0506 | 0.1286 | 0.0328 |

**Core Multiplicity Finding**: **No headline specification provides evidence of tightening transfer after full-ledger multiplicity and permutation inference.**

---

## 5. Journal Fit Assessment

### Target A: *Scientific Data* (Descriptor) — Primary Target
- **Suitability**: **Exceptional (Primary Recommended Venue)**.
- **Core Strengths**:
  - Fully deterministic raw-to-final processing pipeline with bit-for-bit cryptographic verification (`DATA_FREEZE_v2_1.md`).
  - Standardized temporal splits with leakage-proof code guardrails (`src/model_guard.py`).
  - Comprehensive data dictionaries, quality scorecards, and multi-tier provenance levels.
  - Restricted access deposit on Zenodo complying with intellectual property terms for financial market indices.

### Target B: *Nature Communications* (Article) — Stretch Venue
- **Suitability**: **Stretch Venue (Confirmatory result is a null; high bar for standalone causal claims)**.
- **Realistic Editorial Assessment**:
  - The confirmatory result is an empirical null, and a low-power null in a turbulent post-pandemic transition does not definitively establish structural decoupling.
  - The test split contains zero interest rate hikes and zero Fed Tier 1 decisions, limiting generalizability.
  - While *Nature Communications* values open science and pre-registration, positioning a pure null finding as an article-level contribution without mechanistic micro-foundations is a significant editorial stretch. *Scientific Data* represents the stronger, more defensible primary submission target.

---

## 6. Related Literature Integration (`TODO-HUMAN`)

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
