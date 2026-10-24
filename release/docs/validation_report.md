# MoTrans-15 Data Validation, Tiers, Overlap, and Completeness Report

*Generated automatically from `shocks.parquet`, `policy_decisions.csv`, `events.parquet`, and `controls_long.parquet` on 2026-10-24.*

All tables below are computed directly from the underlying pipeline datasets via code (never typed by hand).

## 1. Usable Shocks (`shock_usable == 1`) by Regime and Split

`shock_usable = 1` requires a valid non-missing standardized shock (`shock_grade` in `{"A", "B"}`).

| Regime | Usable Train | Usable Crisis | Usable Blind Test | Total Usable | Usability Coverage |
|---|---|---|---|---|---|
| BCB | 182 | 0 | 0 | 182 | 76.5% (182/238) |
| Banxico | 0 | 0 | 0 | 0 | 0.0% (0/238) |
| BoC | 154 | 18 | 38 | 210 | 98.1% (210/214) |
| BoE | 228 | 18 | 38 | 284 | 100.0% (284/284) |
| BoJ | 278 | 17 | 38 | 333 | 100.0% (333/333) |
| BoK | 0 | 0 | 0 | 0 | 0.0% (0/60) |
| CBR | 64 | 11 | 25 | 100 | 92.6% (100/108) |
| ECB | 245 | 16 | 38 | 299 | 100.0% (299/299) |
| Fed | 170 | 18 | 38 | 226 | 99.6% (226/227) |
| PBoC | 30 | 3 | 7 | 40 | 100.0% (40/40) |
| RBA | 217 | 23 | 44 | 284 | 99.0% (284/287) |
| RBI | 0 | 0 | 0 | 0 | 0.0% (0/163) |
| **Total** | **1568** | **124** | **266** | **1958** | **78.6% (1958/2491)** |

## 2. Primary Shocks — Baseline Conservative Pre-Registration (`shock_primary = 0` for all BoJ)

Excludes: all BoJ (zero lower bound peg), CBR post-Feb 2022 (structural break / sanctions), PBoC (tenor 2Y proxy), and RBA pre-Feb 2008 unannounced holds.

| Regime | Primary Train | Primary Crisis | Primary Blind Test | Total Primary | Blind Test Status |
|---|---|---|---|---|---|
| BCB | 112 | 0 | 0 | 112 | **FLAGGED (< 20)** |
| Banxico | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| BoC | 50 | 3 | 19 | 72 | **FLAGGED (< 20)** |
| BoE | 33 | 3 | 19 | 55 | **FLAGGED (< 20)** |
| BoJ | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| BoK | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| CBR | 64 | 11 | 1 | 76 | **FLAGGED (< 20)** |
| ECB | 245 | 16 | 33 | 294 | Sufficient (>= 20) |
| Fed | 169 | 18 | 23 | 210 | Sufficient (>= 20) |
| PBoC | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| RBA | 49 | 3 | 19 | 71 | **FLAGGED (< 20)** |
| RBI | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| **Total** | **722** | **54** | **114** | **890** | — |

## 3. Effective Analysis Sample by Shock Tier (`shock_tier`) and Timing Readiness

- **Tier 1 (Identification Grade)**: Consensus high-frequency intraday OIS / futures surprise (`hf_ois`). Pre-registered headline blind test sample.
- **Tier 2 (Secondary Transfer Test)**: Daily sovereign benchmark yield change proxy (`yield_proxy`). Evaluated as secondary out-of-sample transfer test.
- **Effective Sample**: Requires `shock_primary == 1 AND analysis_ready_timing == 1`.

| Tier | Regime | Measure Type | Train (to 2019) | Crisis (2020-21) | Blind Test (2022+) | Total Decisions | Effective Sample (`eff == 1`) | Status / Role |
|---|---|---|---|---|---|---|---|---|
| Tier 1 | ECB | `hf_ois` | 245 | 16 | 31 | **292** | **292** | Headline Pre-Registered Test |
| Tier 1 | Fed | `hf_ois` | 168 | 18 | 16 | **202** | **202** | Headline Pre-Registered Test |
| **Subtotal Tier 1** | — | — | **413** | **34** | **47** | **494** | **494** | — |
| Tier 2 | BCB | `yield_proxy` | 182 | 0 | 0 | **182** | **0** | Secondary Transfer Test |
| Tier 2 | BoC | `yield_proxy` | 154 | 18 | 38 | **210** | **29** | Secondary Transfer Test |
| Tier 2 | BoE | `yield_proxy` | 228 | 18 | 38 | **284** | **25** | Secondary Transfer Test |
| Tier 2 | BoJ | `yield_proxy` | 278 | 17 | 38 | **333** | **0** | BoJ ZIRP Peg (Primary = 0) |
| Tier 2 | CBR | `yield_proxy` | 64 | 11 | 25 | **100** | **41** | Secondary Transfer Test |
| Tier 2 | ECB | `yield_proxy` | 0 | 0 | 7 | **7** | **2** | Secondary Transfer Test |
| Tier 2 | Fed | `yield_proxy` | 2 | 0 | 22 | **24** | **8** | Secondary Transfer Test |
| Tier 2 | PBoC | `yield_proxy` | 30 | 3 | 7 | **40** | **0** | Secondary Transfer Test |
| Tier 2 | RBA | `yield_proxy` | 217 | 23 | 44 | **284** | **71** | Secondary Transfer Test |
| **Subtotal Tier 2** | — | — | **1155** | **90** | **219** | **1464** | **176** | — |

## 4. Policy Decision Overlap and Event Contamination by Window Length

For each event and trading horizon $W \in \{1, 3, 5, 20, 60\}$ days, counts other policy decisions from any regime occurring within the window.

| Horizon (Trading Days) | Contaminated Events | Total Events | Share Contaminated | Mean Other Decisions | Max Other Decisions |
|---|---|---|---|---|---|
| **1 day** (`clr_1`) | 897 | 2,491 | **36.01%** | 0.43 | 3 |
| **3 days** (`clr_3`) | 1,719 | 2,491 | **69.01%** | 1.23 | 7 |
| **5 days** (`clr_5`) | 2,108 | 2,491 | **84.62%** | 1.85 | 7 |
| **20 days** (`clr_20`) | 2,484 | 2,491 | **99.72%** | 6.59 | 18 |
| **60 days** (`clr_60`) | 2,490 | 2,491 | **99.96%** | 20.91 | 39 |

## 5. Sovereign Yield Proxy Quality: Variance Ratio Analysis (Meeting vs Non-Meeting Days)

Compares the variance of daily sovereign yield changes on policy decision days to non-meeting trading days using the EXACT yield series matched to `shock_proxy_tenor`:
$$\text{Variance Ratio } VR = \frac{\sigma^2_{\Delta y, \text{meeting}}}{\sigma^2_{\Delta y, \text{non-meeting}}}$$
Evaluated separately for Rate Changes (hikes/cuts) and Rate Holds, alongside a placebo bootstrap (1,000 random non-meeting draws, seed 2026).

| Regime | Tenor | Underlying Yield Series | Non-Meeting SD (bp) | VR (Rate Changes) | Decisions (Action) | VR (Holds) | Decisions (Hold) | Placebo VR (Holds) | Hold p-value | Hold Signal Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| BoE | 1Y | 1Y Gilt spot curve | 3.77 | **4.64** | 55 | **1.08** | 229 | 1.00 | 0.332 | No Excess Signal (Noise-dominated) |
| RBA | 2Y | 2Y ACGB Table F2 benchmark yield | 5.43 | **5.78** | 71 | **1.00** | 213 | 1.00 | 0.447 | No Excess Signal (Noise-dominated) |
| CBR | 1Y | 1Y OFZ zero-coupon curve | 19.89 | **7.17** | 99 | — | 0 | — | — | No Holds in Regime |
| BoJ | 1Y | 1Y JGB Ministry of Finance yield | 0.89 | **19.47** | 12 | **1.42** | 184 | 1.01 | 0.102 | No Excess Signal (Noise-dominated) |
| BCB | 1Y | 1Y Swap DI x pre 360d (SGS 7806) | 23.60 | **1.07** | 112 | **1.57** | 70 | 0.99 | 0.165 | No Excess Signal (Noise-dominated) |
| PBoC | 2Y | 2Y ChinaBond sovereign benchmark yield | 8.63 | **1.59** | 28 | — | 0 | — | — | No Holds in Regime |
| Fed | 1Y | 1Y US Treasury par yield | 4.10 | **3.79** | 74 | **0.98** | 150 | 0.99 | 0.390 | No Excess Signal (Noise-dominated) |
| ECB | 1Y | 1Y Bundesbank Federal securities yield | 3.50 | **2.33** | 59 | **0.77** | 240 | 1.00 | 0.867 | No Excess Signal (Noise-dominated) |

## 6. Central Bank Meeting Completeness by Year (BoE, BoC, RBA, Fed, ECB)

Compares recorded decision counts per calendar year against official central bank institutional meeting calendars.

| Year | BoE Decisions | BoC Decisions | RBA Decisions | Fed Decisions | ECB Decisions | Annual Total |
|---|---|---|---|---|---|---|
| **2000** | 12 | 4 | 11 | 8 | 24 | **59** |
| **2001** | 13 | 9 | 11 | 11 | 24 | **68** |
| **2002** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2003** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2004** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2005** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2006** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2007** | 12 | 8 | 11 | 10 | 12 | **53** |
| **2008** | 12 | 9 | 11 | 11 | 13 | **56** |
| **2009** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2010** | 12 | 8 | 11 | 9 | 12 | **52** |
| **2011** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2012** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2013** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2014** | 12 | 8 | 11 | 8 | 12 | **51** |
| **2015** | 12 | 8 | 11 | 8 | 8 | **47** |
| **2016** | 11 | 8 | 11 | 8 | 8 | **46** |
| **2017** | 8 | 8 | 11 | 8 | 8 | **43** |
| **2018** | 8 | 8 | 11 | 8 | 8 | **43** |
| **2019** | 8 | 8 | 11 | 9 | 8 | **44** |
| **2020** | 10 | 10 | 12 | 10 | 8 | **50** |
| **2021** | 8 | 8 | 11 | 8 | 8 | **43** |
| **2022** | 8 | 8 | 11 | 8 | 8 | **43** |
| **2023** | 8 | 8 | 11 | 8 | 8 | **43** |
| **2024** | 8 | 8 | 8 | 8 | 8 | **40** |
| **2025** | 8 | 8 | 8 | 9 | 8 | **41** |
| **2026** | 6 | 6 | 6 | 6 | 6 | **30** |
| **Total** | **284** | **214** | **287** | **227** | **299** | **1311** |

**Last Decision Dates Recorded in Dataset:**
- **BoE**: `2026-09-17`
- **BoC**: `2026-09-02`
- **RBA**: `2026-09-29`
- **Fed**: `2026-09-16`
- **ECB**: `2026-09-10`

## 7. Bank of Japan Institutional Reconciliation & Post-Exit Event Scaling

**Reconciliation of BoJ Decision Population:**
- **Total BoJ Decisions (2000–2026)**: **333** decisions.
- **Pre-Exit ZIRP Decisions (< 2024-03-19)**: **312** decisions, all flagged `low_sensitivity_zero_lower_bound` with `shock_primary = 0`. (The figure "318" in prior summaries was an inadvertent typo; $333 - 21 = 312$).
- **Post-Exit Decisions (>= 2024-03-19)**: **21** decisions, flagged `sovereign_yield_proxy`.
- **Primary Baseline Rule**: `shock_primary == 0` for ALL 333 BoJ decisions. (The wording "primary 21" has been removed; post-exit events are evaluated exclusively under the labeled sensitivity flag `shock_primary_rescaled`).

| Decision Date | Decision | Size (bp) | Proxy Change (bp) | Legacy Std (1.14 bp SD) | Rescaled Std (4.48 bp SD) | Winsorized Std [-4, +4] | Split Tag |
|---|---|---|---|---|---|---|---|
| 2024-03-19 | hike | 15 | -2.1 | -1.85 | -0.47 | -0.47 | blind_test |
| 2024-04-26 | hold | 0 | +0.0 | +0.00 | +0.00 | +0.00 | blind_test |
| 2024-06-14 | hold | 0 | -1.9 | -1.67 | -0.42 | -0.42 | blind_test |
| 2024-07-31 | hike | 20 | +9.1 | +8.01 | +2.03 | +2.03 | blind_test |
| 2024-09-20 | hold | 0 | +0.1 | +0.09 | +0.02 | +0.02 | blind_test |
| 2024-10-31 | hold | 0 | -0.9 | -0.79 | -0.20 | -0.20 | blind_test |
| 2024-12-19 | hold | 0 | +0.2 | +0.18 | +0.04 | +0.04 | blind_test |
| 2025-01-24 | hike | 25 | +1.9 | +1.67 | +0.42 | +0.42 | blind_test |
| 2025-03-19 | hold | 0 | +1.2 | +1.06 | +0.27 | +0.27 | blind_test |
| 2025-05-01 | hold | 0 | -3.0 | -2.64 | -0.67 | -0.67 | blind_test |
| 2025-06-17 | hold | 0 | +0.2 | +0.18 | +0.04 | +0.04 | blind_test |
| 2025-07-31 | hold | 0 | +0.2 | +0.18 | +0.04 | +0.04 | blind_test |
| 2025-09-19 | hold | 0 | +2.8 | +2.47 | +0.62 | +0.62 | blind_test |
| 2025-10-30 | hold | 0 | -0.7 | -0.62 | -0.16 | -0.16 | blind_test |
| 2025-12-19 | hike | 25 | +2.2 | +1.94 | +0.49 | +0.49 | blind_test |
| 2026-01-23 | hold | 0 | +4.2 | +3.70 | +0.94 | +0.94 | blind_test |
| 2026-03-19 | hold | 0 | +2.1 | +1.85 | +0.47 | +0.47 | blind_test |
| 2026-04-28 | hold | 0 | +0.4 | +0.35 | +0.09 | +0.09 | blind_test |
| 2026-06-16 | hike | 25 | +0.6 | +0.53 | +0.13 | +0.13 | blind_test |
| 2026-07-31 | hold | 0 | +1.2 | +1.06 | +0.27 | +0.27 | blind_test |
| 2026-09-18 | hike | 25 | +4.6 | +4.05 | +1.03 | +1.03 | blind_test |