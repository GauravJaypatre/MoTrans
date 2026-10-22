# MoTrans-15 Data Validation & Effective Sample Report

*Generated automatically from `shocks.parquet`, `policy_decisions.csv`, and `events.parquet` on 2026-10-22.*

All tables below are computed directly from the underlying data files via code (never hand-typed).

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
| RBA | 150 | 23 | 44 | 217 | 98.6% (217/220) |
| RBI | 0 | 0 | 0 | 0 | 0.0% (0/163) |
| **Total** | **1501** | **124** | **267** | **1892** | **78.1% (1892/2424)** |

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
| RBA | 150 | 23 | 44 | 217 | Sufficient (>= 20) |
| RBI | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| **Total** | **1193** | **104** | **198** | **1495** | — |

## 3. Primary Shocks — Alternative Pre-Specified Rule (BoJ Post-Exit Admitted with Peer DM Scale)

Includes the 21 post-2024-03-18 BoJ decisions standardized with the peer DM sovereign 1Y yield training SD (4.48 bp).

| Regime | Primary Train | Primary Crisis | Primary Blind Test | Total Primary | Blind Test Status |
|---|---|---|---|---|---|
| BCB | 182 | 0 | 0 | 182 | **FLAGGED (< 20)** |
| Banxico | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| BoC | 154 | 18 | 38 | 210 | Sufficient (>= 20) |
| BoE | 228 | 18 | 38 | 284 | Sufficient (>= 20) |
| BoJ | 0 | 0 | 21 | 21 | Sufficient (>= 20) |
| BoK | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| CBR | 64 | 11 | 1 | 76 | **FLAGGED (< 20)** |
| ECB | 245 | 16 | 38 | 299 | Sufficient (>= 20) |
| Fed | 170 | 18 | 39 | 227 | Sufficient (>= 20) |
| PBoC | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| RBA | 150 | 23 | 44 | 217 | Sufficient (>= 20) |
| RBI | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| **Total** | **1193** | **104** | **219** | **1516** | — |

## 4. Effective Analysis Sample (`analysis_ready_timing == 1` AND `shock_primary == 1`)

Decisions ready for causal event-study regressions requiring both clean announcement timing and clean shock identification.

| Regime | Effective Train | Effective Crisis | Effective Blind Test | Total Effective (Baseline) | Total Effective (Rescaled BoJ) | Reason if Zero Usable |
|---|---|---|---|---|---|---|
| BCB | 0 | 0 | 0 | **0** | **0** | Timing unknown (pending PG3 Item F); SGS yield proxy ended Sep 2019 |
| Banxico | 0 | 0 | 0 | **0** | **0** | Timing unknown (pending PG3 Item F); Yield data requires SIE API token |
| BoC | 154 | 18 | 38 | **210** | **210** | Fully analysis-ready (exact FAD schedule; Grade B yield proxy) |
| BoE | 228 | 18 | 38 | **284** | **284** | Fully analysis-ready (exact 12:00 convention; Grade B yield proxy) |
| BoJ | 0 | 0 | 0 | **0** | **20** | Baseline excludes ZIRP; Rescaled admits 21 post-exit blind-test events |
| BoK | 0 | 0 | 0 | **0** | **0** | Timing unknown (pending PG3 Item F); Yield data requires ECOS API key |
| CBR | 29 | 11 | 1 | **41** | **41** | Analysis-ready pre-Feb 2022 (exact 13:30 convention; post-2022 excluded due to sanctions) |
| ECB | 245 | 16 | 38 | **299** | **299** | Fully analysis-ready (exact times from EA-MPD; Grade A/B shocks) |
| Fed | 170 | 18 | 39 | **227** | **227** | Fully analysis-ready (exact times from FRBSF/Fed; Grade A/B shocks) |
| PBoC | 0 | 0 | 0 | **0** | **0** | Timing unknown (pending PG3 Item F); 2Y proxy retained for descriptive use |
| RBA | 150 | 23 | 44 | **217** | **217** | Fully analysis-ready (exact 14:30 convention; Grade B yield proxy) |
| RBI | 0 | 0 | 0 | **0** | **0** | Timing unknown (pending PG3 Item F); DBIE portal restricted |
| **Total** | **976** | **104** | **198** | **1278** | **1298** | — |

## 5. Effective Analysis Sample by Shock Measure Type (`shock_measure_type`)

Breakdown of analysis-ready primary decisions by identification strategy: high-frequency OIS/futures surprise (`hf_ois`) vs sovereign yield change proxy (`yield_proxy`).

| Regime | Shock Type | Train | Crisis | Blind Test | Total | Coverage Notes |
|---|---|---|---|---|---|---|
| BoC | `yield_proxy` | 154 | 18 | 38 | **210** |  sovereign yield proxy |
| BoE | `yield_proxy` | 228 | 18 | 38 | **284** | 1Y sovereign yield proxy |
| CBR | `yield_proxy` | 29 | 11 | 1 | **41** |  sovereign yield proxy |
| ECB | `hf_ois` | 245 | 16 | 31 | **292** | EA-MPD OIS 1Y (coverage ends 2025-10-30) |
| ECB | `yield_proxy` | 0 | 0 | 7 | **7** | 1Y Bund change proxy (post-Oct 2025 decisions) |
| Fed | `hf_ois` | 167 | 18 | 16 | **201** | FRBSF Bauer-Swanson MPS (coverage ends 2023-12-13) |
| Fed | `yield_proxy` | 3 | 0 | 23 | **26** | 1Y Treasury change proxy (post-2023 + 3 in-range exceptions) |
| RBA | `yield_proxy` | 150 | 23 | 44 | **217** | 2Y sovereign yield proxy |
| **Total Primary Effective** | — | **976** | **104** | **198** | **1278** | — |

## 6. Bank of Japan Post-Exit Event Scaling (21 Events Post-2024-03-18)

| Decision Date | Decision | Size (bp) | Proxy Change (bp) | Legacy Std (1.14 bp SD) | Rescaled Std (4.48 bp SD) | Winsorized Std [-4, +4] |
|---|---|---|---|---|---|---|
| 2024-03-19 | hike | 15 | -2.1 | -1.85 | -0.47 | -0.47 |
| 2024-04-26 | hold | 0 | +0.0 | +0.00 | +0.00 | +0.00 |
| 2024-06-14 | hold | 0 | -1.9 | -1.67 | -0.42 | -0.42 |
| 2024-07-31 | hike | 20 | +9.1 | +8.01 | +2.03 | +2.03 |
| 2024-09-20 | hold | 0 | +0.1 | +0.09 | +0.02 | +0.02 |
| 2024-10-31 | hold | 0 | -0.9 | -0.79 | -0.20 | -0.20 |
| 2024-12-19 | hold | 0 | +0.2 | +0.18 | +0.04 | +0.04 |
| 2025-01-24 | hike | 25 | +1.9 | +1.67 | +0.42 | +0.42 |
| 2025-03-19 | hold | 0 | +1.2 | +1.06 | +0.27 | +0.27 |
| 2025-05-01 | hold | 0 | -3.0 | -2.64 | -0.67 | -0.67 |
| 2025-06-17 | hold | 0 | +0.2 | +0.18 | +0.04 | +0.04 |
| 2025-07-31 | hold | 0 | +0.2 | +0.18 | +0.04 | +0.04 |
| 2025-09-19 | hold | 0 | +2.8 | +2.47 | +0.62 | +0.62 |
| 2025-10-30 | hold | 0 | -0.7 | -0.62 | -0.16 | -0.16 |
| 2025-12-19 | hike | 25 | +2.2 | +1.94 | +0.49 | +0.49 |
| 2026-01-23 | hold | 0 | +4.2 | +3.70 | +0.94 | +0.94 |
| 2026-03-19 | hold | 0 | +2.1 | +1.85 | +0.47 | +0.47 |
| 2026-04-28 | hold | 0 | +0.4 | +0.35 | +0.09 | +0.09 |
| 2026-06-16 | hike | 25 | +0.6 | +0.53 | +0.13 | +0.13 |
| 2026-07-31 | hold | 0 | +1.2 | +1.06 | +0.27 | +0.27 |
| 2026-09-18 | hike | 25 | +4.6 | +4.05 | +1.03 | +1.03 |