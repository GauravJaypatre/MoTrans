# MoTrans-15: Manuscript Framing & Scientific Strategy

**Date**: 2026-11-04  
**Target Journals**: *Scientific Data* (Data Descriptor) / *Nature Communications* (Article)  
**Status**: ACTIVE WORKING DRAFT  
**Guiding Principle**: Uncompromising scientific integrity; zero overclaiming; honest reporting of pre-registered null results.

---

## 1. Primary Empirical Result

The core empirical finding of the MoTrans-15 investigation is established by the pre-registered confirmatory blind test (`docs/preregistration.md`, executed on 47 held-out policy decisions from 2022 to 2025):

> **Primary Result**: High-frequency intraday monetary policy surprises (Federal Reserve Bauer-Swanson MPS and ECB EA-MPD 1-year OIS) did **not exert a statistically detectable causal impact on international equity indices** during the held-out 2022–2025 cycle ($p > 0.10$ across all pre-registered horizons $W \in \{1, 3, 5, 20, 60\}$ trading days; wild cluster bootstrap $p \in [0.159, 0.442]$).

While point estimates exhibit the negative direction predicted by economic theory ($\beta \in [-0.0068, -0.0007]$), standard errors are comparable in magnitude, yielding an unambiguous **statistical null finding**.

---

## 2. Supported vs. Unsupported Claims

| Research Dimension | Scientifically Supported Claim | Unsupported / Rescoped Claim (Do Not Make) |
| :--- | :--- | :--- |
| **Causal Impact** | Pre-registered high-frequency transmission to equity returns yields a statistically robust null result in the held-out sample. | *Do not claim* that central bank announcements predictably move global equity indices across multi-day horizons. |
| **Cross-Border Spillovers** | International spillovers from Fed and ECB surprises are statistically indistinguishable from zero ($p \ge 0.21$). | *Do not claim* robust global financial spillovers during the post-pandemic tightening cycle. |
| **Out-of-Sample Transfer** | The held-out test split benchmarks model generalization exclusively during an easing/hold regime (0 interest rate hikes). | *Do not claim* out-of-sample validity for contractionary tightening regimes. |
| **Instrument Precision** | Daily sovereign yield proxies contain ~67% non-HFI background market noise ($R^2 = 0.3305$ vs HFI on common decisions). | *Do not claim* that daily yield proxies are functionally equivalent to high-frequency intraday surprise measures. |
| **Emerging Markets** | High-frequency analysis is methodologically restricted to Developed Markets due to timing provenance limitations. | *Do not claim* causal transmission conclusions for Brazil, Mexico, or India (quarantined in `excluded_rows`). |
| **Inference Framework** | Clustered standard errors are mandatory due to high intracluster correlation ($ICC \approx 0.15 - 0.25$), reducing effective $N$ by ~90%. | *Do not report* unclustered or naive OLS standard errors. |
| **Exploratory Multiplicity** | Exploratory significance in pooled models is eliminated after Holm-Bonferroni family-wise error adjustment ($p_{\text{Holm}} = 0.1804$). | *Do not claim* statistically significant transmission based on uncorrected exploratory p-values. |

---

## 3. Title Options

### Option 1 (Descriptive / Data-Centric — Target: *Scientific Data*)
> **MoTrans-15: A Harmonized Multi-Country Benchmark of Central Bank Communication, Monetary Surprises, and Equity Reactions (2010–2025)**  
> *Framing*: Emphasizes the standardized multi-country data asset, cryptographic freeze, leakage-proof train/test architecture, and multi-horizon equity return panels across the 15 largest global economies.

### Option 2 (Causal / Null-Centered — Target: *Nature Communications*)
> **Decoupling of High-Frequency Monetary Surprises and Global Equity Transmission During the 2022–2025 Cycle**  
> *Framing*: Centers on the substantive economic finding that the classic intraday monetary transmission channel decoupled during the post-pandemic inflation shock, as equity markets responded primarily to macroeconomic fundamentals and inflation prints rather than 30-minute central bank surprises.

### Option 3 (Methodological / Open Science — Alternative Target)
> **High-Frequency Identification and Multi-Country Equity Transmission: Pre-Registered Evidence and Regime Boundaries Across 15 Major Economies**  
> *Framing*: Highlights methodological rigor, the perils of unclustered inference, noise decomposition in sovereign yield proxies, and the imperative of pre-registration in empirical macro-finance.

---

## 4. Scientific Contribution of the Null Finding

1. **Counteracting Publication Bias**: Academic macro-finance literature exhibits severe publication bias toward statistically significant transmission estimates. Publishing an unhacked, pre-registered null finding preserves the empirical record and prevents uncorrected specification searches.
2. **Macroeconomic Regime Shift**: The finding demonstrates that the empirical relationships established during the 2000–2019 low-inflation, zero-rate environment did not transfer to the 2022–2025 inflationary regime, where macroeconomic data releases (e.g. CPI, non-farm payrolls) systematically eclipsed policy announcement surprises.
3. **Econometric Reality of Daily Proxies**: Proving that daily sovereign yield proxies carry 67% non-HFI background noise provides an essential methodological warning for empirical studies relying on daily interest rate changes as policy instruments.

---

## 5. Journal Fit Assessment

### Target A: *Scientific Data* (Descriptor)
- **Suitability**: Exceptional (Tier 1 fit).
- **Core Strengths**:
  - Fully deterministic raw-to-final processing pipeline with bit-for-bit cryptographic verification (`DATA_FREEZE_v2_1.md`).
  - Standardized temporal splits with leakage-proof code guardrails (`src/model_guard.py`).
  - Comprehensive data dictionaries, quality scorecards, and multi-tier provenance levels.
  - Restricted access deposit on Zenodo complying with intellectual property terms for financial market indices.

### Target B: *Nature Communications* (Article)
- **Suitability**: Strong (Subject to honest null framing).
- **Core Strengths**:
  - Resolves a central question in international macroeconomics using a pre-registered confirmatory research design across the 15 largest global economies.
  - Demonstrates the empirical breakdown of high-frequency monetary transmission during a historic inflation cycle.
  - Introduces a rigorous framework for decomposing intracluster correlation ($ICC$) and instrument noise across sovereign yield proxies.

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
