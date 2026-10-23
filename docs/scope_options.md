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

## 2. Option A: Major-Central-Bank Transmission Universe (Fed + ECB Only)

### Definition
Option A restricts policy shocks strictly to the systemic global central banks with consensus high-frequency identification:
- **Central Banks Included**: Federal Reserve (Fed) and European Central Bank (ECB) only.
- **Identification Framework**:
  - **Tier 1 (High-Frequency Identification)**: Consensus intraday surprises (`hf_ois`: FRBSF Bauer-Swanson 30-minute futures and EA-MPD 1-year OIS monetary event window).
  - **Tier 2 (Yield-Proxy Extension)**: Daily sovereign benchmark yield change proxy (`yield_proxy`) for periods post-dating HFI dataset releases (Fed 2024–2026, ECB late 2025–2026) and 3 historical Fed unscheduled decisions.
- **Receiving Equity Markets**: All 38 indices across all 15 countries and economic areas.
- **Transmission Classification**:
  - *Home market transmission*: US equity indices (S&P 500, DJIA, NASDAQ 100) responding to Fed shocks; Euro-area equity indices (DAX 40, CAC 40, FTSE MIB, IBEX 35, AEX, Euro Stoxx 50) responding to ECB shocks.
  - *Foreign market spillover*: All non-home equity indices across the Americas, Europe, Asia-Pacific, and emerging markets responding to Fed and ECB policy shocks.

### Empirical Counts (Code-Derived from `shocks.parquet` and `events.parquet`)

#### Table A1: Option A by Central Bank and Split
| Central Bank | Primary Measure Type | Total Decisions | Train ($\le 2019$) | Crisis ($2020-21$) | Blind Test ($\ge 2022$) | `events.parquet` Rows |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Fed** | `hf_ois` (to 2023) / `yield_proxy` (2024+) | 227 | 170 | 18 | 39 | 7,557 |
| **ECB** | `hf_ois` (to 2025) / `yield_proxy` (2025+) | 299 | 245 | 16 | 38 | 9,443 |
| **Total Option A (Fed + ECB)** | `hf_ois` + `yield_proxy` | **526** | **415** | **34** | **77** | **17,000** |

#### Table A2: Option A Split by Quality Tier
| Tier / Sub-sample | Fed Decisions | ECB Decisions | Total Decisions | Train ($\le 2019$) | Crisis ($2020-21$) | Blind Test ($\ge 2022$) | `events.parquet` Rows |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Tier 1 (HFI Only)** | 201 | 292 | **493** | 412 | 34 | 47 | **15,774** |
| **Tier 2 (Yield Proxy)** | 26 | 7 | **33** | 3 | 0 | 30 | **1,226** |
| **Total Option A** | **227** | **299** | **526** | **415** | **34** | **77** | **17,000** |

- **Actual Index-Event Observations (`events.parquet`)**:
  - Full Option A: **17,000** index-event observations (replaces naive product $526 \times 38 = 19,988$).
  - Tier 1 HFI Headline Sample: **15,774** index-event observations (replaces naive product $493 \times 38 = 18,734$).
- **Independent Blind-Test Shocks**:
  - Full Option A: **77 independent decision events** (39 Fed, 38 ECB).
  - Tier 1 Headline Blind Test: **47 independent decision events** (16 Fed, 31 ECB).

### Feasibility of Pre-registered Tests & Structural Limitations
- **Leave-One-Country-Out (LOCO) Limitation**:
  - *Critical Flag*: Standard LOCO **cannot test own-country (home) transmission** under Option A because only two economic jurisdictions (US and Euro Area) generate policy shocks. Dropping the US leaves only the Euro Area as a home-market pair; dropping the Euro Area leaves only the US. Thus, LOCO reduces to a two-point test of domestic sensitivity, preventing meaningful leave-one-country-out validation of home vs. foreign response differentials.
- **Proposed Methodological Alternatives**:
  1. **Leave-One-Market-Out (LOMO)**: Hold out one target equity market at a time (e.g., Japan, UK, Australia, India) to evaluate out-of-sample stability of foreign spillover coefficients across heterogenous market structures.
  2. **Leave-One-Central-Bank-Out (LO-CB-O)**: Train the transmission model entirely on Fed shocks and evaluate blindly on ECB shocks (and vice versa). This provides an out-of-sample test of whether global equity response elasticities reflect fundamental cross-border financial channels or central-bank-specific reaction functions.

---

## 3. Option B: Expanded Clean Timing and Primary Regime Universe

### Definition
Option B supplements Option A by incorporating all additional central bank regimes that meet strict analysis-readiness requirements:
1. **Clean Announcement Timing**: Sourced from official central bank calendars with verified release conventions (`time_quality = 'exact'`, `analysis_ready_timing = 1`).
2. **Complete Meeting Universe**: Scheduled meetings with rate holds systematically recorded from official calendars (resolving ISS-019).
3. **Primary Yield Proxy Shocks**: Unimpaired 1-year or 2-year sovereign benchmark yield changes over clean event windows (`shock_primary = 1`).

### Qualifying Regimes
- **Fed & ECB**: Primary high-frequency OIS/futures shocks (`hf_ois`) plus yield-proxy extensions.
- **BoE (Bank of England)**: 284 official MPC meetings (2000–2026) with complete holds sourced from `mpcvoting.xlsx`; announcement convention 12:00 London time; 1-year gilt proxy (`yield_proxy`).
- **BoC (Bank of Canada)**: 210 analysis-ready Fixed Announcement Dates (FADs, 2000–2026; 4 unscheduled without proxies excluded) with complete holds; announcement convention 09:00/10:00/09:45 ET; 2-year benchmark proxy (`yield_proxy`).
- **RBA (Reserve Bank of Australia)**: 196 analysis-ready Board meeting rate decisions (Feb 2008–2026) with complete holds; announcement convention 14:30 Sydney time; Table F2 2-year benchmark proxy (`yield_proxy`). The 68 unannounced holds prior to Feb 2008 are excluded (`shock_primary = 0`, flagged `rba_pre2008_unannounced_hold`) per official practice (MR-07-22).
- *(Excluded from Primary)*: BoJ (all 333 decisions have `shock_primary = 0` due to ZIRP/YCC rate compression), CBR (post-Feb 2022 sanctions break and pre-2013 unscheduled era), PBoC (`shock_primary = 0`, LPR benchmark proxy), and regimes without verified announcement times (BCB, Banxico, BoK).

### Empirical Counts (Code-Derived from `shocks.parquet` and `events.parquet`)

#### Table B1: Option B Primary Regimes by Split
| Central Bank | Primary Measure Type | Primary Decisions | Train ($\le 2019$) | Crisis ($2020-21$) | Blind Test ($\ge 2022$) | Primary `events.parquet` Rows |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Fed** | `hf_ois` / `yield_proxy` | 227 | 170 | 18 | 39 | 7,557 |
| **ECB** | `hf_ois` / `yield_proxy` | 299 | 245 | 16 | 38 | 9,443 |
| **BoE** | `yield_proxy` (1Y Gilt) | 284 | 228 | 18 | 38 | 9,289 |
| **BoC** | `yield_proxy` (2Y GoC) | 210 | 154 | 18 | 38 | 7,195 |
| **RBA** | `yield_proxy` (2Y ACGB) | 196 | 129 | 23 | 44 | 6,564 |
| **Total Option B Primary** | `hf_ois` + `yield_proxy` | **1,216** | **926** | **93** | **197** | **40,048** |

*(Note: In `events.parquet`, total rows flagged `shock_primary == 1` equal 49,354 across all domestic and cross-border pairs).*

- **Independent Blind-Test Shocks**:
  - **197 independent decision events** (Fed 39, ECB 38, BoE 38, BoC 38, RBA 44). Every qualifying regime provides $\ge 38$ independent blind-test shocks, satisfying pre-registration power thresholds.

---

## 4. Per-Year Index Availability Explaining `events.parquet` Row Counts

The total row count of `events.parquet` is **82,054 rows**, rather than the naive product of total policy decisions ($2,491$) and 38 equity indices ($2,491 \times 38 = 94,658$ rows). 

The exact difference of **12,604 rows** is fully explained by the staggered historical inception dates of the 38 underlying equity indices and sector ETFs. Per Non-Negotiable Rule 1, rows are never backfilled with interpolated or fabricated prices prior to an index's official base date.

#### Table 4: Annual Policy Decisions, Active Indices, and Event Rows
| Period | Active Indices | Policy Decisions | Actual `events.parquet` Rows | Theoretical Max ($N 	imes 38$) | Difference (Missing Pre-Inception) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **2000** | 21 | 105 | 2,045 | 3,990 | 1,945 |
| **2001** | 22 | 111 | 2,334 | 4,218 | 1,884 |
| **2002** | 23 | 92 | 2,115 | 3,496 | 1,381 |
| **2003** | 23 | 101 | 2,323 | 3,838 | 1,515 |
| **2004** | 25 | 101 | 2,491 | 3,838 | 1,347 |
| **2005** | 30 | 96 | 2,819 | 3,648 | 829 |
| **2006** | 30 | 97 | 2,910 | 3,686 | 776 |
| **2007** | 31 | 102 | 3,155 | 3,876 | 721 |
| **2008** | 33 | 118 | 3,894 | 4,484 | 590 |
| **2009** | 34 | 103 | 3,408 | 3,914 | 506 |
| **2010** | 34 | 103 | 3,502 | 3,914 | 412 |
| **2011** | 35 | 99 | 3,377 | 3,762 | 385 |
| **2012** | 36 | 96 | 3,362 | 3,648 | 286 |
| **2013** | 38 | 91 | 3,431 | 3,458 | 27 |
| **2014-2025** | 38 | 1,016 | 38,608 | 38,608 | 0 |
| **2026** | 38 | 60 | 2,280 | 2,280 | 0 |
| **Total** | — | **2,491** | **82,054** | **94,658** | **12,604** |

---

## 5. Comparative Summary and Pre-Registration Trade-Offs

| Metric / Dimension | Option A (Fed + ECB Only) | Option B (Expanded Clean Universe) |
|:---|:---:|:---:|
| **Central Banks Included** | Fed, ECB | Fed, ECB, BoE, BoC, RBA |
| **Primary Identification** | High-frequency OIS/futures (`hf_ois`) + Yield proxies (post-2024) | High-frequency OIS (`hf_ois`) + Sovereign yield proxies (`yield_proxy`) |
| **Total Decisions** | 526 | 1,216 |
| **Tier 1 Decisions** | 493 | 493 |
| **Actual Index-Event Rows** | 17,000 (Tier 1: 15,774) | 40,048 (Total Primary: 49,354) |
| **Blind-Test Shocks (2022+)** | 77 (Tier 1: 47) | 197 |
| **Domestic Markets Tested** | 2 (US, Euro Area) | 5 (US, Euro Area, UK, Canada, Australia) |
| **Foreign Receiving Indices** | 38 | 38 |
| **Leave-One-Country-Out (LOCO)**| **Infeasible for home transmission** | **Fully feasible across 5 sovereign jurisdictions** |
| **Recommended Alternative Validation** | LOMO (Leave-One-Market-Out) & LO-CB-O (Leave-One-Central-Bank-Out) | LOCO (Leave-One-Country-Out) + LOMO + Shock Type Heterogeneity |
| **Pre-registration Compliance** | High internal validity (Grade A focus) | High statistical power and external generalizability |

---

## 6. Conclusion and Implementation Path
- **Pre-registration Integrity**: Both options adhere strictly to the train ($\le 2019$), crisis ($2020-2021$), and blind test ($\ge 2022$) split boundaries and the 1-year/2-year benchmark maturity definitions.
- **Recommendation**:
  - Adopt **Option B** as the primary empirical architecture once BoE, BoC, and RBA calendar holds and verified timing conventions are fully pipeline-integrated, ensuring sufficient power for LOCO cross-validation.
  - Retain **Option A** as a pre-specified high-frequency core sensitivity analysis restricted purely to `hf_ois` events.

