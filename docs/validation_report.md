# MoTrans-15 Data Validation, Tiers, Overlap, and Completeness Report

*Generated automatically from `shocks.parquet`, `policy_decisions.csv`, `events.parquet`, and `controls_long.parquet` on 2026-10-22.*

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
| Fed | 170 | 18 | 39 | 227 | 100.0% (227/227) |
| PBoC | 30 | 3 | 7 | 40 | 100.0% (40/40) |
| RBA | 217 | 23 | 44 | 284 | 99.0% (284/287) |
| RBI | 0 | 0 | 0 | 0 | 0.0% (0/163) |
| **Total** | **1568** | **124** | **267** | **1959** | **78.6% (1959/2491)** |

## 2. Primary Shocks — Baseline Conservative Pre-Registration (`shock_primary = 0` for all BoJ)

Excludes: all BoJ (zero lower bound peg), CBR post-Feb 2022 (structural break / sanctions), and PBoC (tenor 2Y proxy).

| Regime | Primary Train | Primary Crisis | Primary Blind Test | Total Primary | Blind Test Status |
|---|---|---|---|---|---|
| BCB | 182 | 0 | 0 | 182 | **FLAGGED (< 20)** |
| Banxico | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| BoC | 154 | 18 | 38 | 210 | Sufficient (>= 20) |
| BoE | 228 | 18 | 38 | 284 | Sufficient (>= 20) |
| BoJ | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| BoK | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| CBR | 64 | 11 | 1 | 76 | **FLAGGED (< 20)** |
| ECB | 245 | 16 | 38 | 299 | Sufficient (>= 20) |
| Fed | 170 | 18 | 39 | 227 | Sufficient (>= 20) |
| PBoC | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| RBA | 217 | 23 | 44 | 284 | Sufficient (>= 20) |
| RBI | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| **Total** | **1260** | **104** | **198** | **1562** | — |

## 3. Effective Analysis Sample by Shock Tier (`shock_tier`)

- **Tier 1 (Identification Grade)**: Consensus high-frequency intraday OIS / futures surprise (`hf_ois`). Pre-registered headline blind test sample.
- **Tier 2 (Secondary Transfer Test)**: Daily sovereign benchmark yield change proxy (`yield_proxy`). Evaluated as secondary out-of-sample transfer test.

| Tier | Regime | Measure Type | Train (to 2019) | Crisis (2020-21) | Blind Test (2022+) | Total Decisions | Status / Role |
|---|---|---|---|---|---|---|---|
| Tier 1 | ECB | `hf_ois` | 245 | 16 | 31 | **292** | Headline Pre-Registered Test |
| Tier 1 | Fed | `hf_ois` | 167 | 18 | 16 | **201** | Headline Pre-Registered Test |
| **Subtotal Tier 1** | — | — | **412** | **34** | **47** | **493** | — |
| Tier 2 | BCB | `yield_proxy` | 182 | 0 | 0 | **182** | Secondary Transfer Test |
| Tier 2 | BoC | `yield_proxy` | 154 | 18 | 38 | **210** | Secondary Transfer Test |
| Tier 2 | BoE | `yield_proxy` | 228 | 18 | 38 | **284** | Secondary Transfer Test |
| Tier 2 | CBR | `yield_proxy` | 64 | 11 | 1 | **76** | Secondary Transfer Test |
| Tier 2 | ECB | `yield_proxy` | 0 | 0 | 7 | **7** | Secondary Transfer Test |
| Tier 2 | Fed | `yield_proxy` | 3 | 0 | 23 | **26** | Secondary Transfer Test |
| Tier 2 | RBA | `yield_proxy` | 217 | 23 | 44 | **284** | Secondary Transfer Test |
| **Subtotal Tier 2** | — | — | **848** | **70** | **151** | **1069** | — |

## 4. Policy Decision Overlap and Event Contamination by Window Length

For each event and trading horizon $W \in \{1, 3, 5, 20, 60\}$ days, counts other policy decisions from any regime occurring within the window.

| Horizon (Trading Days) | Contaminated Events | Total Events | Share Contaminated | Mean Other Decisions | Max Other Decisions |
|---|---|---|---|---|---|
| **1 day** (`clr_1`) | 897 | 2,491 | **36.01%** | 0.43 | 3 |
| **3 days** (`clr_3`) | 1,720 | 2,491 | **69.05%** | 1.23 | 7 |
| **5 days** (`clr_5`) | 2,107 | 2,491 | **84.58%** | 1.85 | 7 |
| **20 days** (`clr_20`) | 2,484 | 2,491 | **99.72%** | 6.59 | 18 |
| **60 days** (`clr_60`) | 2,490 | 2,491 | **99.96%** | 20.91 | 39 |

## 5. Sovereign Yield Proxy Quality: Variance Ratio Analysis (Meeting vs Non-Meeting Days)

Compares the variance of daily sovereign yield changes on policy decision days to non-meeting trading days:
$$\text{Variance Ratio } VR = \frac{\sigma^2_{\Delta y, \text{meeting}}}{\sigma^2_{\Delta y, \text{non-meeting}}}$$
Evaluated separately for Rate Changes (hikes/cuts) and Rate Holds, alongside a placebo bootstrap (1,000 random non-meeting draws).

| Regime | Tenor | Non-Meeting SD (bp) | VR (Rate Changes) | Decisions (Action) | VR (Holds) | Decisions (Hold) | Placebo VR (Holds) | Hold p-value | Hold Signal Verdict |
|---|---|---|---|---|---|---|---|---|---|
| BoE | yield_1y | 3.77 | **4.64** | 55 | **1.08** | 229 | 1.00 | 0.332 | No Excess Signal (Noise-dominated) |
| BoC | yield_1y | 4.86 | **3.93** | 72 | **1.61** | 138 | 1.00 | 0.013 | Statistically Significant (p < 0.05) |
| RBA | yield_2y | 5.43 | **5.78** | 71 | **1.00** | 213 | 1.00 | 0.448 | No Excess Signal (Noise-dominated) |
| CBR | yield_1y | 19.89 | **7.17** | 99 | — | 0 | — | — | No Holds in Regime |
| BoJ | yield_1y | 0.89 | **19.47** | 12 | **1.42** | 184 | 1.02 | 0.126 | No Excess Signal (Noise-dominated) |
| BCB | yield_1y | 23.60 | **1.07** | 112 | **1.57** | 70 | 1.00 | 0.168 | No Excess Signal (Noise-dominated) |
| PBoC | yield_2y | 8.63 | **1.59** | 28 | — | 0 | — | — | No Holds in Regime |
| Fed | yield_1y | 4.10 | **3.79** | 74 | **1.00** | 151 | 1.01 | 0.410 | No Excess Signal (Noise-dominated) |
| ECB | yield_1y | 3.50 | **2.33** | 59 | **0.77** | 240 | 1.00 | 0.853 | No Excess Signal (Noise-dominated) |

## 6. Central Bank Meeting Completeness by Year (BoC, BoE, RBA vs Official Calendars)

Verifies meeting counts per calendar year against official central bank institutional calendars.
- **BoE**: 12/year (2000-2015), 11 (2016 Warsh transition), 8/year (2017+).
- **BoC**: 8 Fixed Announcement Dates (FADs)/year from 2001+ (plus unscheduled emergency actions in 2001, 2008, 2020).
- **RBA**: 11 meetings/year (Feb-Dec first Tuesday, 2000-2023; with 67 pre-2008 holds restored); 8/year starting 2024 (RBA Review).

| Year | BoC Decisions | BoE Decisions | RBA Decisions | BoC Expected | BoE Expected | RBA Expected | Completeness Verdict |
|---|---|---|---|---|---|---|---|
| 2000 | 4 | 12 | 11 | 4 (1 FAD + 3 unsch) | 12 | 11 | Complete (100%) |
| 2001 | 9 | 13 | 11 | 8 (+1 unsch) | 12 (+1 unsch) | 11 | Complete (100%) |
| 2002 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2003 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2004 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2005 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2006 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2007 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2008 | 9 | 12 | 11 | 8 (+1 unsch) | 12 | 11 | Complete (100%) |
| 2009 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2010 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2011 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2012 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2013 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2014 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2015 | 8 | 12 | 11 | 8 | 12 | 11 | Complete (100%) |
| 2016 | 8 | 11 | 11 | 8 | 11 (transition) | 11 | Complete (100%) |
| 2017 | 8 | 8 | 11 | 8 | 8 | 11 | Complete (100%) |
| 2018 | 8 | 8 | 11 | 8 | 8 | 11 | Complete (100%) |
| 2019 | 8 | 8 | 11 | 8 | 8 | 11 | Complete (100%) |
| 2020 | 10 | 10 | 12 | 8 (+2 unsch) | 8 (+2 unsch) | 11 (+1 unsch) | Complete (100%) |
| 2021 | 8 | 8 | 11 | 8 | 8 | 11 | Complete (100%) |
| 2022 | 8 | 8 | 11 | 8 | 8 | 11 | Complete (100%) |
| 2023 | 8 | 8 | 11 | 8 | 8 | 11 | Complete (100%) |
| 2024 | 8 | 8 | 8 | 8 | 8 | 8 | Complete (100%) |
| 2025 | 8 | 8 | 8 | 8 | 8 | 8 | Complete (100%) |
| 2026 | 6 | 6 | 6 | 6 (thru Oct) | 6 (thru Oct) | 6 (thru Oct) | Complete (100%) |

## 7. Bank of Japan Post-Exit Event Scaling (21 Events Post-2024-03-18)

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