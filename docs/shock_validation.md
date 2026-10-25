# Shock validation (Phase D & Priority Group 2)

Grades: A = public high-frequency surprise; B = 1-year (or 2-year benchmark) yield change proxy; C = no usable shock (descriptive only). `shock_std` is in units of the training-period (to 2019) SD of its source.

## Coverage by regime

| regime | events | A | B | C | first shock | last shock |
|---|---|---|---|---|---|---|
| BCB | 238 | 0 | 182 | 56 | 2000-03-29 | 2019-09-18 |
| Banxico | 238 | 0 | 0 | 238 | - | - |
| BoC | 214 | 0 | 210 | 4 | 2001-01-23 | 2026-09-02 |
| BoE | 284 | 0 | 284 | 0 | 2000-01-13 | 2026-09-17 |
| BoJ | 333 | 0 | 333 | 0 | 2000-01-17 | 2026-09-18 |
| BoK | 60 | 0 | 0 | 60 | - | - |
| CBR | 108 | 0 | 100 | 8 | 2003-02-17 | 2026-07-27 |
| ECB | 299 | 292 | 7 | 0 | 2000-01-05 | 2026-09-10 |
| Fed | 227 | 202 | 24 | 1 | 2000-02-02 | 2026-09-16 |
| PBoC | 40 | 0 | 40 | 0 | 2002-02-21 | 2025-05-20 |
| RBA | 287 | 0 | 284 | 3 | 2000-02-02 | 2026-09-29 |
| RBI | 163 | 0 | 0 | 163 | - | - |

## Usable and Primary shocks by regime and split (Priority Group 2)

`shock_usable = 1` requires a valid non-missing standardized shock (`shock_grade` in {'A', 'B'}). `shock_primary = 1` restricts to clean shocks (excluding BoJ ZIRP/YCC, CBR post-Feb 2022, and PBoC). Regimes with fewer than 20 primary blind-test events are flagged below.

| regime | usable train | primary train | usable crisis | primary crisis | usable blind | primary blind | total usable | total primary | primary blind status |
|---|---|---|---|---|---|---|---|---|---|
| BCB | 182 | 112 | 0 | 0 | 0 | 0 | 182 | 112 | **FLAGGED (< 20)** |
| Banxico | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| BoC | 154 | 50 | 18 | 3 | 38 | 19 | 210 | 72 | **FLAGGED (< 20)** |
| BoE | 228 | 33 | 18 | 3 | 38 | 19 | 284 | 55 | **FLAGGED (< 20)** |
| BoJ | 278 | 0 | 17 | 0 | 38 | 0 | 333 | 0 | **FLAGGED (< 20)** |
| BoK | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |
| CBR | 64 | 64 | 11 | 11 | 25 | 1 | 100 | 76 | **FLAGGED (< 20)** |
| ECB | 245 | 245 | 16 | 16 | 38 | 33 | 299 | 294 | Sufficient (>= 20) |
| Fed | 170 | 169 | 18 | 18 | 38 | 23 | 226 | 210 | Sufficient (>= 20) |
| PBoC | 30 | 0 | 3 | 0 | 7 | 0 | 40 | 0 | **FLAGGED (< 20)** |
| RBA | 217 | 49 | 23 | 3 | 44 | 19 | 284 | 71 | **FLAGGED (< 20)** |
| RBI | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **FLAGGED (< 20)** |

## Japan zero-rate proxy review

During 2000-2019 (ZIRP/QQE), the 1-year JGB yield was compressed near zero with minimal variance (train SD = 1.13 bp). As an artifact of standardization by the training SD, post-2022 rate movements scale to extreme values (e.g. +8.02 SD on 2024-07-31). In addition, during quantitative easing and Yield Curve Control, short yields were pinned, reducing sensitivity to policy surprises. Events during the zero-rate era carry `shock_quality_flag = 'low_sensitivity_zero_lower_bound'`.


## High-frequency vs proxy (overlap, standardised)

| regime | events with both | correlation |
|---|---|---|
| Fed | 202 | 0.55 |
| ECB | 211 | 0.61 |

## Known episodes

Expected sign: tightening surprises positive, easing surprises negative. A hike that markets fully expected can have a near-zero shock; that is not an error.

| event | decision | size (bp) | grade | shock_std |
|---|---|---|---|---|
| fed_2013-06-19 | hold | 0 | A | +0.19 |
| fed_2020-03-03 | cut | -50 | A | -2.53 |
| fed_2020-03-15 | cut | -100 | A | -3.76 |
| fed_2022-03-16 | hike | 25 | A | +2.44 |
| fed_2022-06-15 | hike | 75 | A | +1.65 |
| fed_2022-09-21 | hike | 75 | A | +2.38 |
| ecb_2011-04-07 | hike | 25 | A | +0.11 |
| ecb_2011-07-07 | hike | 25 | A | +0.32 |
| ecb_2022-07-21 | hike | 50 | A | +2.05 |
| ecb_2022-09-08 | hike | 75 | A | +2.42 |
| boj_2024-03-19 | hike | 15 | B | -1.85 |
| boe_2022-02-03 | hike | 25 | B | +3.34 |
| bcb_2022-03-16 | hike | 100 | C | - |
| rbi_2022-05-04 | hike | 40 | C | - |

## Largest absolute shocks (review these first)

| event | decision | size (bp) | grade | source | shock_std |
|---|---|---|---|---|---|
| fed_2001-09-17 | cut | -50 | B | 1Y yield change, US (bp) | -8.34 |
| boj_2024-07-31 | hike | 20 | B | 1Y yield change, JP (bp) | +8.01 |
| boj_2016-07-29 | unclassified | nan | B | 1Y yield change, JP (bp) | +7.66 |
| boe_2026-03-19 | hold | 0 | B | 1Y yield change, GB (bp) | +7.37 |
| bcb_2001-03-21 | hike | 50 | B | 1Y yield change, BR (bp) | +6.52 |
| rba_2008-10-07 | cut | -100 | B | 2Y yield change, AU (bp) | -6.34 |
| boe_2023-02-02 | hike | 50 | B | 1Y yield change, GB (bp) | -5.96 |
| bcb_2002-10-14 | hike | 300 | B | 1Y yield change, BR (bp) | +5.76 |
| boj_2008-10-31 | cut | -20 | B | 1Y yield change, JP (bp) | -5.02 |
| fed_2001-04-18 | cut | -50 | A | FRBSF Bauer-Swanson MPS (bp) | -4.99 |
| boe_2008-11-06 | cut | -150 | B | 1Y yield change, GB (bp) | -4.95 |
| boe_2003-02-06 | cut | -25 | B | 1Y yield change, GB (bp) | -4.76 |
| boe_2023-03-23 | hike | 25 | B | 1Y yield change, GB (bp) | -4.69 |
| ecb_2008-06-05 | hold | 0 | A | EA-MPD OIS 1Y, monetary event window (bp) | +4.62 |
| boe_2008-10-08 | cut | -50 | B | 1Y yield change, GB (bp) | -4.50 |

Plots per regime: outputs/shocks_<regime>.png (regenerate with `python -m src.build_shocks`).
