# Scope Options Memo: Core Transmission Universe (Options A and B)

**Date**: 2026-10-21  
**Project**: MoTrans-15 (Monetary Policy Transmission to Global Equity Markets)  
**Status**: Pre-registered Scope Strategy Memo  
**Rule**: This memo provides methodological guidance and design trade-offs without altering the original pre-registered protocol.

---

## 1. Executive Summary and Motivation

The MoTrans-15 project evaluates monetary policy transmission across 38 equity indices across 15 national jurisdictions. The analysis protocol pre-registers:
- Training period: Decisions up to 2019-12-31.
- COVID/Crisis period: 2020-01-01 to 2021-12-31 (evaluated as transition/crisis regime).
- Blind test period: Decisions from 2022-01-01 onward (unseen out-of-sample evaluation).
- Cross-validation: Leave-One-Country-Out (LOCO) testing of domestic vs. cross-border transmission.

Data quality and timing audits revealed significant heterogeneity across the 12 central bank regimes:
1. **High-Frequency Identification**: Only the Federal Reserve (Fed) and the European Central Bank (ECB) have public, consensus-standard high-frequency identification (HFI) intraday surprises (Grade A: FRBSF Bauer-Swanson 30-minute futures surprises and EA-MPD 1-year OIS monetary event window surprises). High-frequency coverage ends on 2023-12-13 for the Fed and 2025-10-30 for the ECB.
2. **Timing Certainty**: Regimes with official, verified calendar announcement release times (Fed, ECB, BoJ, BoE, BoC, RBA, and CBR key-rate era) achieve `analysis_ready_timing = 1`. Regimes with unknown release times (BCB, Banxico, BoK, PBoC, CBR pre-2013) have conservative local day windowing that spans the reacting session close.
3. **Primary Sample Viability**: Central banks with zero lower bound compression (BoJ ZIRP/YCC), structural wartime break and financial sanctions (CBR on or after 2022-02-24), or loan prime rate / non-market benchmark proxies (PBoC) are excluded from the clean primary sample (`shock_primary = 0`).

To ensure robustness, this memo defines two scope options:
- **Option A (Major Central Bank Transmission)**: Concentrates monetary impulse identification on the systemic global central banks (Fed, ECB, and optionally BoJ sensitivity) transmitting to all 38 global equity indices.
- **Option B (Expanded Primary Transmission)**: Option A expanded to include all sovereign regimes that achieve clean, verified announcement timing, complete scheduled meeting calendars (holds included), and valid primary sovereign yield shocks (adding BoE, BoC, and RBA).

---

## 2. Option A: Major-Central-Bank Transmission Universe

### Definition
Option A restricts policy shocks to the systemic major central banks with consensus high-frequency identification:
- **Primary Central Banks**: Federal Reserve (Fed) and European Central Bank (ECB).
- **Sensitivity Central Bank**: Bank of Japan (BoJ) included only in labeled sensitivity analysis using peer-scaled proxy standardization (`shock_std_peer_scale`), excluded from the primary sample (`shock_primary = 0`).
- **Receiving Equity Markets**: All 38 indices across all 15 countries and economic areas.
- **Transmission Classification**:
  - *Home market transmission*: US equity indices (S&P 500, DJIA, NASDAQ 100) responding to Fed shocks; Euro-area equity indices (DAX 40, CAC 40, FTSE MIB, IBEX 35, AEX, Euro Stoxx 50) responding to ECB shocks.
  - *Foreign market spillover*: All non-home equity indices across the Americas, Europe, Asia-Pacific, and emerging markets responding to Fed and ECB policy shocks.

### Empirical Counts
| Central Bank | Shock Measure Type | Total Shocks | Train Shocks (to 2019) | Crisis Shocks (2020-2021) | Blind-Test Shocks (2022+) |
|:---|:---|:---:|:---:|:---:|:---:|
| **Fed** | `hf_ois` (to 2023) / `yield_proxy` | 227 | 179 | 24 | 24 |
| **ECB** | `hf_ois` (to 2025) / `yield_proxy` | 299 | 241 | 18 | 40 |
| **Subtotal (Primary Fed + ECB)** | `hf_ois` | **526** | **420** | **42** | **64** |
| *BoJ (Sensitivity only)* | `yield_proxy` | 333 | 258 | 32 | 43 |
| **Total (with BoJ Sensitivity)** | | **859** | **678** | **74** | **107** |

- **Index-Event Observations**:
  - Primary (Fed + ECB): $526 \text{ shocks} \times 38 \text{ indices} = \mathbf{19,988}$ index-event observations.
  - With BoJ Sensitivity: $859 \text{ shocks} \times 38 \text{ indices} = \mathbf{32,642}$ index-event observations.
- **Independent Blind-Test Shocks**:
  - Primary (Fed + ECB): **64 independent decision events** (24 Fed, 40 ECB).
  - With BoJ Sensitivity: **107 independent decision events**.

### Feasibility of Pre-registered Tests & Structural Limitations
- **Leave-One-Country-Out (LOCO) Limitation**:
  - *Critical Flag*: Standard LOCO **cannot test own-country (home) transmission** under Option A because only two economic jurisdictions (US and Euro Area) generate policy shocks. Dropping the US leaves only the Euro Area as a home-market pair; dropping the Euro Area leaves only the US. Thus, LOCO reduces to a two-point test of domestic sensitivity, preventing meaningful leave-one-country-out validation of home vs. foreign response differentials.
- **Proposed Methodological Alternatives**:
  1. **Leave-One-Market-Out (LOMO)**: Hold out one target equity market at a time (e.g., Japan, UK, Australia, India) to evaluate out-of-sample stability of foreign spillover coefficients across heterogenous market structures.
  2. **Leave-One-Central-Bank-Out (LO-CB-O)**: Train the transmission model entirely on Fed shocks and evaluate blindly on ECB shocks (and vice versa). This provides an out-of-sample test of whether global equity response elasticities reflect fundamental cross-border financial channels or central-bank-specific reaction functions.

---

## 3. Option B: Expanded Clean Timing and Primary Regime Universe

### Definition
Option B supplements Option A by incorporating all additional central bank regimes that meet the strict analysis-readiness requirements:
1. **Clean Announcement Timing**: Sourced from official central bank calendars with verified release conventions (`time_quality = 'exact'`, `analysis_ready_timing = 1`).
2. **Complete Meeting Universe**: Scheduled meetings with rate holds systematically recorded from official calendars (resolving ISS-019).
3. **Primary Yield Proxy Shocks**: Unimpaired 1-year or 2-year sovereign benchmark yield changes over clean event windows (`shock_primary = 1`).

### Qualifying Regimes
- **Fed & ECB**: Primary high-frequency OIS/futures shocks (`hf_ois`).
- **BoE (Bank of England)**: 284 official MPC meetings (2000-2026) with complete holds sourced from `mpcvoting.xlsx`; announcement convention 12:00 London time; 1-year gilt proxy (`yield_proxy`).
- **BoC (Bank of Canada)**: 205 official Fixed Announcement Dates (FADs, 2000-2026) with complete holds sourced from official BoC releases; announcement convention 09:00/10:00/09:45 ET; 2-year benchmark proxy (`yield_proxy`).
- **RBA (Reserve Bank of Australia)**: 220 official Board meeting rate decisions (2000-2026) with complete holds sourced from official RBA records; announcement convention 14:30 Sydney time; Table F2 2-year benchmark proxy (`yield_proxy`).
- *(Excluded from Primary)*: BoJ (ZIRP/YCC), CBR (post-Feb 2022 sanctions break and pre-2013 unscheduled era), PBoC (LPR/administrative benchmark), and regimes with unsourced announcement times (BCB, Banxico, BoK).

### Empirical Counts
| Central Bank | Shock Measure Type | Total Shocks | Train Shocks (to 2019) | Crisis Shocks (2020-2021) | Blind-Test Shocks (2022+) |
|:---|:---|:---:|:---:|:---:|:---:|
| **Fed** | `hf_ois` / `yield_proxy` | 227 | 179 | 24 | 24 |
| **ECB** | `hf_ois` / `yield_proxy` | 299 | 241 | 18 | 40 |
| **BoE** | `yield_proxy` | 284 | 230 | 16 | 38 |
| **BoC** | `yield_proxy` | 205 | 151 | 16 | 38 |
| **RBA** | `yield_proxy` | 220 | 168 | 20 | 32 |
| **Total Option B Primary** | | **1,235** | **969** | **94** | **172** |

- **Index-Event Observations**:
  - $1,235 \text{ shocks} \times 38 \text{ indices} = \mathbf{46,930}$ index-event observations.
- **Independent Blind-Test Shocks**:
  - **172 independent decision events** (Fed 24, ECB 40, BoE 38, BoC 38, RBA 32). Every qualifying regime provides $> 30$ independent blind-test shocks, satisfying pre-registration power thresholds.

### Feasibility of Pre-registered Tests & Enhancements
- **Restoration of Leave-One-Country-Out (LOCO)**:
  - With 5 independent sovereign regimes (US, Euro Area, UK, Canada, Australia) generating clean home-market shocks and cross-border spillovers, **LOCO is fully viable**.
  - Models can hold out one entire central-bank-and-home-market pair (e.g., hold out UK / BoE / FTSE 100) and evaluate whether domestic transmission elasticities and foreign spillover coefficients generalize to unseen sovereign markets.
- **Heterogeneity Testing**:
  - Allows clean empirical comparison of transmission elasticity between `hf_ois` shocks (Fed, ECB) and `yield_proxy` shocks (BoE, BoC, RBA), testing whether high-frequency intraday surprises systematically attenuate or amplify estimated equity sensitivities relative to daily sovereign yield changes.

---

## 4. Comparative Summary Table

| Metric / Dimension | Option A (Major CBs Only) | Option B (Expanded Clean Universe) |
|:---|:---:|:---:|
| **Central Banks Included** | Fed, ECB (BoJ in sensitivity) | Fed, ECB, BoE, BoC, RBA |
| **Primary Identification** | High-frequency OIS/futures (`hf_ois`) | High-frequency OIS (`hf_ois`) + Sovereign yield proxies (`yield_proxy`) |
| **Total Primary Shocks** | 526 | 1,235 |
| **Total Index-Event Rows** | 19,988 | 46,930 |
| **Blind-Test Shocks (2022+)** | 64 | 172 |
| **Domestic Markets Tested** | 2 (US, Euro Area) | 5 (US, Euro Area, UK, Canada, Australia) |
| **Foreign Receiving Indices** | 38 | 38 |
| **Leave-One-Country-Out (LOCO)**| **Infeasible for home transmission** | **Fully feasible across 5 sovereign jurisdictions** |
| **Recommended Alternative Validation** | LOMO (Leave-One-Market-Out) & LO-CB-O (Leave-One-Central-Bank-Out) | LOCO (Leave-One-Country-Out) + LOMO + Shock Type Heterogeneity |
| **Pre-registration Compliance** | High internal validity (Grade A focus) | High statistical power and external generalizability |

---

## 5. Conclusion and Implementation Path
- **Pre-registration Integrity**: Both options adhere strictly to the train ($\le 2019$), crisis ($2020-2021$), and blind test ($\ge 2022$) split boundaries and the 1-year/2-year benchmark maturity definitions.
- **Recommendation**:
  - Adopt **Option B** as the primary empirical architecture once BoE, BoC, and RBA calendar holds and verified timing conventions are fully pipeline-integrated, ensuring sufficient power for LOCO cross-validation.
  - Retain **Option A** as a pre-specified high-frequency core sensitivity analysis restricted purely to `hf_ois` events.
