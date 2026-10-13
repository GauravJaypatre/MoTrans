# Shock validation (Phase D)

Grades: A = public high-frequency surprise; B = 1-year yield change proxy; C = no usable shock (descriptive only). `shock_std` is in units of the training-period (to 2019) SD of its source.

## Coverage by regime

| regime | events | A | B | C | first shock | last shock |
|---|---|---|---|---|---|---|
| BCB | 238 | 0 | 182 | 56 | 2000-03-29 | 2019-09-18 |
| Banxico | 238 | 0 | 0 | 238 | - | - |
| BoC | 75 | 0 | 72 | 3 | 2001-01-23 | 2025-10-30 |
| BoE | 55 | 0 | 55 | 0 | 2000-01-13 | 2025-12-18 |
| BoJ | 333 | 0 | 333 | 0 | 2000-01-17 | 2026-09-18 |
| BoK | 60 | 0 | 0 | 60 | - | - |
| CBR | 108 | 0 | 100 | 8 | 2003-02-17 | 2026-07-27 |
| ECB | 299 | 286 | 13 | 0 | 2000-01-05 | 2026-09-10 |
| Fed | 227 | 201 | 26 | 0 | 2000-02-02 | 2026-09-16 |
| PBoC | 40 | 0 | 0 | 40 | - | - |
| RBA | 72 | 0 | 0 | 72 | - | - |
| RBI | 163 | 0 | 0 | 163 | - | - |

## High-frequency vs proxy (overlap, standardised)

| regime | events with both | correlation |
|---|---|---|
| Fed | 201 | 0.55 |
| ECB | 205 | 0.61 |

## Known episodes

Expected sign: tightening surprises positive, easing surprises negative. A hike that markets fully expected can have a near-zero shock; that is not an error.

| event | decision | size (bp) | grade | shock_std |
|---|---|---|---|---|
| fed_2013-06-19 | hold | 0 | A | +0.19 |
| fed_2020-03-03 | cut | -50 | A | -2.53 |
| fed_2020-03-15 | cut | -100 | A | -3.75 |
| fed_2022-03-16 | hike | 25 | A | +2.43 |
| fed_2022-06-15 | hike | 75 | A | +1.65 |
| fed_2022-09-21 | hike | 75 | A | +2.37 |
| ecb_2011-04-07 | hike | 25 | A | +0.11 |
| ecb_2011-07-07 | hike | 25 | A | +0.32 |
| ecb_2022-07-21 | hike | 50 | A | +2.05 |
| ecb_2022-09-08 | hike | 75 | A | +2.42 |
| boj_2024-03-19 | hike | 15 | B | -1.85 |
| boe_2022-02-03 | hike | 25 | B | +1.99 |
| bcb_2022-03-16 | hike | 100 | C | - |
| rbi_2022-05-04 | hike | 40 | C | - |

## Largest absolute shocks (review these first)

| event | decision | size (bp) | grade | source | shock_std |
|---|---|---|---|---|---|
| fed_2001-09-17 | cut | -50 | B | 1-year yield change, US (bp) | -8.34 |
| boj_2024-07-31 | hike | 20 | B | 1-year yield change, JP (bp) | +8.02 |
| cbr_2014-12-16 | hike | 650 | B | 1-year yield change, RU (bp) | +7.72 |
| boj_2016-07-29 | unclassified | nan | B | 1-year yield change, JP (bp) | +7.67 |
| bcb_2002-06-19 | hold | 0 | B | 1-year yield change, BR (bp) | +6.61 |
| boj_2008-10-31 | cut | -20 | B | 1-year yield change, JP (bp) | -5.03 |
| fed_2001-04-18 | cut | -50 | A | FRBSF Bauer-Swanson MPS (bp) | -4.98 |
| ecb_2008-06-05 | hold | 0 | A | EA-MPD OIS 1Y, monetary event window (bp) | +4.62 |
| bcb_2002-12-18 | hike | 300 | B | 1-year yield change, BR (bp) | -4.57 |
| boj_2008-12-19 | cut | -20 | B | 1-year yield change, JP (bp) | -4.41 |
| fed_2008-12-16 | cut | -75 | A | FRBSF Bauer-Swanson MPS (bp) | -4.40 |
| ecb_2011-08-04 | hold | 0 | A | EA-MPD OIS 1Y, monetary event window (bp) | -4.00 |
| bcb_2002-10-14 | hike | 300 | B | 1-year yield change, BR (bp) | +3.89 |
| boj_2016-01-29 | unclassified | nan | B | 1-year yield change, JP (bp) | -3.88 |
| ecb_2000-06-08 | hike | 50 | A | EA-MPD OIS 1Y, monetary event window (bp) | +3.80 |

Plots per regime: outputs/shocks_<regime>.png (regenerate with `python -m src.build_shocks`).
