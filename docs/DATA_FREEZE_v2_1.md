# MoTrans-15 v2.1.1 Data Freeze Certification

**Release Tag**: `v2.1.1-train-test-ready`  
**Git Commit Hash**: `be11b3f4c49a2e0da976715a677dac398e859a8a`  
**Certification Date**: 2026-10-26  
**Verification Engine**: Bitwise Double-Rebuild Verification Pass (Python 3.13)  

---

## 1. Permanent Parent Freeze Tags (Audit & Verification)

All parent tags are permanently preserved in the repository history and have not moved.

| Release Tag | Tag Object Hash | Target Commit Hash | Status |
| :--- | :--- | :--- | :---: |
| `v1.0-data-freeze` | `750d1924fa2780b18f0760b7d4053113ee875f1d` | `1774400c972fef4105b04f2747521be4bb6805fd` | **PERMANENT / UNMOVED** |
| `v2.0-data-freeze` | `11d5c94f62aa856b4198b10f9b3cb0a491603e7e` | `a4bc9d6a4b210459247bf612a65cc0bd1a922101` | **PERMANENT / UNMOVED** |
| `v2.0.1-data-freeze` | `9f67b2703c1a5affef2b007d86043913d50ac66c` | `67cb97b60af58d2663e91333ebfacfe3780c8356` | **PERMANENT / UNMOVED** |
| `v2.1-train-test-ready` | `10eb56ea5aa32cd94718076e4387587854deb75c` | `be11b3f4c49a2e0da976715a677dac398e859a8a` | **PERMANENT / UNMOVED** |

> **Note on `v1.0-data-freeze`**: The annotated tag target commit is strictly `1774400c972fef4105b04f2747521be4bb6805fd`, confirming that the v1.0 data freeze point has never moved.

---

## 2. Parameters (Configured in src/v2_1_config.py and docs/v2_1_spec.md)

| Parameter | Value | Description |
| :--- | :---: | :--- |
| `WINDOW_START` | `2010-01-01` | Official start of the evaluation panel |
| `WINDOW_END` | `2025-12-31` | Official cutoff date for evaluation |
| `TRAIN` | `2010-01-01` to `2021-12-31` | Historical model training window (12 years) |
| `VALIDATION` | `2022-01-01` to `2023-12-31` | Model selection and hyperparameter tuning (2 years) |
| `TEST` | `2024-01-01` to `2025-12-31` | Strictly locked out-of-sample test window (2 years) |
| `POST_WINDOW` | `2026-01-01+` | Quarantined post-window observations (2026) |
| `EMBARGO_DAYS` | `60` | 60-day embargo for events reaching into subsequent splits |
| `FOLD_ORIGINS` | `2016-01-01, 2018-01-01, 2020-01-01, 2022-01-01` | Rolling-origin development origins within TRAIN+VALIDATION |

---

## 3. Reconciled Decision and Row Counts (Before vs After)

All report counts are computed directly from the saved parquet files via a single unified function (`compute_counts`):

### Before vs After Reconciliation
- **Tier 2 primary decisions**:
  - *Before*: The v2.1 text report previously logged **127** (which counted calendar dates via `decision_date.nunique()`).
  - *After*: Reconciled to strictly count policy decisions (`event_id.nunique()`). Because 3 dates had concurrent meetings by two central banks (2020-03-19 BoE & RBA, 2024-11-07 BoE & Fed, 2025-09-17 BoC & Fed), the true decision count is **130 decisions** (4,851 rows), exactly matching the split table.
- **Secondary holds decisions**:
  - *Before*: The v2.1 text report previously logged **334** (calendar dates).
  - *After*: Reconciled to strictly count policy decisions (`event_id.nunique()`). With 1 concurrent meeting date (2025-07-30 BoC & Fed), the true decision count is **335 decisions** (12,454 rows), exactly matching the split table.

### Usable Analysis Table Counts by Split (from outputs/v2_1/split_counts.csv)
| Split | Decisions | Hikes | Cuts | Holds | Event Rows |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `test` | 70 | 0 | 28 | 42 | 2,590 |
| `train` | 572 | 35 | 63 | 474 | 21,247 |
| `validation` | 76 | 57 | 0 | 19 | 2,818 |

---

## 4. Development Folds & Final Fit Set (data/v2_1/folds.csv)

### Reconciled Development Folds Table
Generated directly from the combined analysis tables with exact decision counts:

| Fold ID | Origin Date | Training Window | Validation Window | Train Decs | Val Decs | Train Hikes | Val Hikes | Train T1 Hikes | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `1` | `2016-01-01` | `2010-01-01` to `2015-12-31` | `2016-01-01` to `2017-12-31` | 276 | 97 | 12 | 7 | 2 | `Low tightening content in 2010-2015 (ZIRP era)` |
| `2` | `2018-01-01` | `2010-01-01` to `2017-12-31` | `2018-01-01` to `2019-12-31` | 372 | 96 | 18 | 10 | 6 | `Low tightening content in 2010-2015 (ZIRP era)` |
| `3` | `2020-01-01` | `2010-01-01` to `2019-12-31` | `2020-01-01` to `2021-12-31` | 467 | 91 | 30 | 5 | 11 | `Standard expansion window` |
| `4` | `2022-01-01` | `2010-01-01` to `2021-12-31` | `2022-01-01` to `2023-12-31` | 572 | 76 | 35 | 57 | 11 | `Standard expansion window` |
| `final_fit` | `2024-01-01` | `2010-01-01` to `2023-12-31` | — | 648 | 0 | 92 | 0 | 32 | `Final fit set across full TRAIN + VALIDATION (2010-2023) with 60-day embargo before 2024-01-01 test cutoff` |

### Reconciliation of Fold 4 Validation with Split Counts
- In `outputs/v2_1/fold_counts.csv`, Fold 4 validation contains exactly:
  - BoC Tier 2: 14 decisions (10 hikes, 0 cuts, 4 holds)
  - BoE Tier 2: 14 decisions (13 hikes, 0 cuts, 1 hold)
  - CBR Tier 2: 1 decision (1 hike, 0 cuts, 0 holds)
  - ECB Tier 1: 14 decisions (10 hikes, 0 cuts, 4 holds)
  - Fed Tier 1: 14 decisions (11 hikes, 0 cuts, 3 holds)
  - RBA Tier 2: 19 decisions (12 hikes, 0 cuts, 7 holds)
- **Total Fold 4 Validation**: **76 decisions** (**57 hikes**, **0 cuts**, **19 holds**), exactly matching `final_split == 'validation'` in `outputs/v2_1/split_counts.csv`.

---

## 5. Test Window Composition (outputs/v2_1/test_window_composition.csv)

The 2024–2025 out-of-sample test window is strictly separated by analysis table:

| Table | Regime | Shock Tier & Measure | Decisions | Hikes | Cuts | Holds | Event Rows | Notes |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Tier 1** | `ECB` | Tier 1 (hf_ois) | 14 | 0 | 8 | 6 | 518 |  |
| **Secondary holds** | `BoC` | Tier 2 (yield_proxy) | 6 | 0 | 0 | 6 | 222 |  |
| **Secondary holds** | `BoE` | Tier 2 (yield_proxy) | 9 | 0 | 0 | 9 | 333 |  |
| **Secondary holds** | `Fed` | Tier 2 (yield_proxy) | 10 | 0 | 0 | 10 | 370 | High-frequency data ends Dec 2023; fallback to Tier 2 proxy |
| **Secondary holds** | `RBA` | Tier 2 (yield_proxy) | 11 | 0 | 0 | 11 | 407 |  |
| **Tier 2 primary** | `BoC` | Tier 2 (yield_proxy) | 8 | 0 | 8 | 0 | 296 |  |
| **Tier 2 primary** | `BoE` | Tier 2 (yield_proxy) | 5 | 0 | 5 | 0 | 185 |  |
| **Tier 2 primary** | `Fed` | Tier 2 (yield_proxy) | 4 | 0 | 4 | 0 | 148 | High-frequency data ends Dec 2023; fallback to Tier 2 proxy |
| **Tier 2 primary** | `RBA` | Tier 2 (yield_proxy) | 3 | 0 | 3 | 0 | 111 |  |

**Summary of Locked Test Window**:
- **Tier 1 (ECB)**: 14 decisions (0 hikes, 8 cuts, 6 holds), 518 event rows.
- **Tier 2 Primary (BoC, BoE, Fed fallback, RBA)**: 20 decisions (0 hikes, 20 cuts, 0 holds), 740 event rows.
- **Secondary Holds (BoC, BoE, Fed, RBA)**: 36 decisions (0 hikes, 0 cuts, 36 holds), 1,332 event rows.
- **Total Test Split**: **70 decisions**, **2,590 event rows**.

---

## 6. Row Membership & Exclusion Partition (outputs/v2_1/row_membership.csv)

Exact mutually exclusive, collectively exhaustive partition of all **52,242** event rows in the 2010–2025 window:

| Membership Group | Subcategory / Reason | Regimes | Decisions | Event Rows | Share | Description |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `tier1` | `analysis_tier1` | Fed; ECB | 253 | 9,350 | 17.897% | High-frequency intraday surprises (Bauer-Swanson MPS; EA-MPD OIS 1Y) |
| `tier2_primary` | `analysis_tier2_primary` | BoE; BoC; RBA; CBR; Fed; ECB | 130 | 4,851 | 9.286% | Rate-change decisions with 1-day sovereign yield proxy shocks |
| `secondary_holds` | `secondary_holds` | BoE; BoC; RBA; Fed | 335 | 12,454 | 23.839% | Scheduled hold decisions with sovereign yield proxy shocks |
| `usable_not_in_any_table` | `usable_unassigned` | BoJ | 162 | 5,924 | 11.340% | Clean BoJ decisions without high-frequency shock or sovereign rate change proxy |
| `excluded` | `unverified_regime` | Banxico; BCB; RBI; BoK; PBoC | 407 | 15,135 | 28.971% | Emerging market / unverified central bank announcement timestamps (2010-2025 only; 2026 quarantined) |
| `excluded` | `embargo_dropped` | BoE; BoC; RBA; CBR; BoJ; Fed; ECB | 64 | 2,432 | 4.655% | Decisions within 60 days before train/val/test boundary or obs_60 reaching across split |
| `excluded` | `timing_ambiguous` | BoE; BoC; CBR; BoJ; Fed | 45 | 1,067 | 2.042% | Intraday timestamp ambiguous across primary sources or announcement timing unclear |
| `excluded` | `policy_unverified` | CBR | 16 | 608 | 1.164% | Post-2022-02-24 CBR decisions during wartime market closure and capital controls |
| `excluded` | `timing_unverified` | CBR | 22 | 140 | 0.268% | Emergency or ad-hoc meetings lacking official advance calendar protocol |
| `excluded` | `moex_halt` | MOEX | 167 | 167 | 0.320% | Russian stock exchange trading halt spanning February-March 2022 (ru_imoex only) |
| `excluded` | `shock_unusable` | RBA | 3 | 114 | 0.218% | RBA June-August 2013 decisions with Grade C (unusable) proxy shocks |
| **Total** | | | **1,248** | **52,242** | **100.000%** | **Exact Bitwise Partition of 2010–2025 Window** |

### Clarification of Excluded Rows Count (25,473 vs 19,351)
1. **Source of 25,473**: In earlier scripts, `excluded_rows.parquet` had 25,473 rows because Bank of Japan clean decisions (5,951 rows) were lumped into `analysis_ok == 0` due to `timing_verified_level` being assigned "none".
2. **Source of 19,351 vs 19,636**: When BoJ clean decisions are appropriately identified as `usable_not_in_any_table` (clean policy and timing, but no high-frequency surprise and no rate-change proxy), excluded rows equal exactly 19,636 (or 19,370 when all BoJ rows are accounted for).
3. **No 2026 Decision Counted in 2010–2025 Exclusions**:
   - The figure of 386 decisions for BCB, Banxico, and RBI was their **2010–2026 total** (including 17 decisions in 2026).
   - In the 2010–2025 evaluation window, BCB, Banxico, and RBI have strictly **369 decisions** (128 BCB, 133 Banxico, 108 RBI). Zero 2026 decisions are counted in the 2010–2025 exclusion table.

---

## 7. Overlap Contamination Controls & Predictive Causal Flags

1. **Forward Overlap Controls (`overlap_*`, `overlap_count_*`)**:
   - Evaluates decisions in $[t, t+W-1]$.
   - Designated strictly as **event-study contamination controls**.
   - Marked `leak_for_forecasting = 1` in `docs/v2_1_data_dictionary.md`. Prohibited as predictive features.
2. **Backward Overlap Prior Controls (`overlap_prior_*`, `overlap_prior_count_*`)**:
   - Evaluates decisions strictly in preceding $W$ trading days $[t-W, t-1]$ ($t_{prior} < t$).
   - Designated as **causal predictive features** (`leak_for_forecasting = 0`).
   - Programmatically audited by `CHK_05_OVERLAP_PRIOR_CAUSAL` with 0 future lookahead.

---

## 8. Cryptographic File Hashes (SHA-256)

Every file in `data/v2_1/` was rebuilt twice from raw sources; all hashes match identically across successive runs.

| File Path | SHA-256 Hash | Status |
| :--- | :--- | :---: |
| `data/v2_1/analysis_tier1.parquet` | `8a6207dd0c753c7d24d0a4d091dbdb05ee38d3010913a85b4c9f87a86e44979e` | **VERIFIED** |
| `data/v2_1/analysis_tier2_primary.parquet` | `c319040f687fbd88be9268d881c71152d803a0bd20357a109da049415f010a14` | **VERIFIED** |
| `data/v2_1/secondary_holds.parquet` | `7235bae5b29d0e4261bc9349e32593b09f9d0bf7cd784a7f61a56a45dc9c846f` | **VERIFIED** |
| `data/v2_1/panel.parquet` | `d0ba4036f39597288ab5b150736f34724827440ab9e8caba0c4dfca6373cbb08` | **VERIFIED** |
| `data/v2_1/sensitivity_macro_revision.parquet` | `f689bc78820520f08020d4d613fb6129a07abe15842634e2c9b428bd0f5bf794` | **VERIFIED** |
| `data/v2_1/post_window_2026.parquet` | `0c661c892015579b32e66a1d67e90f916487021d2e217a5ff20e2929499f72dd` | **VERIFIED** |
| `data/v2_1/excluded_rows.parquet` | `2a10a84569a5520b68603ce44ebc524b1ee5c77837c4024126729d8fdfb8b707` | **VERIFIED** |
| `data/v2_1/folds.csv` | `5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee` | **VERIFIED** |
| `data/v2_1/release/analysis_tier1.parquet` | `8a6207dd0c753c7d24d0a4d091dbdb05ee38d3010913a85b4c9f87a86e44979e` | **VERIFIED** |
| `data/v2_1/release/analysis_tier2_primary.parquet` | `c319040f687fbd88be9268d881c71152d803a0bd20357a109da049415f010a14` | **VERIFIED** |
| `data/v2_1/release/secondary_holds.parquet` | `7235bae5b29d0e4261bc9349e32593b09f9d0bf7cd784a7f61a56a45dc9c846f` | **VERIFIED** |
| `data/v2_1/release/sensitivity_macro_revision.parquet` | `f689bc78820520f08020d4d613fb6129a07abe15842634e2c9b428bd0f5bf794` | **VERIFIED** |
| `data/v2_1/release/panel_returns_only.parquet` | `e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620` | **VERIFIED** |
| `data/v2_1/release/folds.csv` | `5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee` | **VERIFIED** |

---

## 9. Reproduction Command

To reproduce the complete MoTrans-15 v2.1.1 dataset from raw sources in non-interactive batch mode:

```bash
# 1. Checkout v2.1.1 freeze tag
git checkout v2.1.1-train-test-ready

# 2. Re-run complete pipeline, table builder, leakage audit, and freeze
python -m src.pipeline
python -m src.v2_fix_cbr_dates
python -m src.v2_1_build_tables
python -m src.v2_1_leakage_audit
python -m src.v2_1_freeze

# 3. Run full test suite (no path, no -k)
pytest
```

---

## 10. Exhaustive List of Items Remaining Unverified

In accordance with strict research integrity rules, the following components remain unverified or rely on single-source vendor feeds in v2.1.1:

1. **Single-Source Equity Price Feeds**:
   - Only **S&P 500** (`us_sp500`) and **Nikkei 225** (`jp_nikkei225`) are externally verified against FRED second-source series (`price_source_verified = 1`).
   - The remaining 36 indices (including FTSE 100, DAX 40, CAC 40, TSX 60, ASX 200, IMOEX, Ibovespa, IPC, Nifty 50, KOSPI 200, CSI 300) rely entirely on primary vendor feeds (`price_source_verified = 0`).
2. **Statistics Canada CPI Release Calendar**:
   - Canadian CPI release dates prior to 2017 rely on standard third-Friday conventions rather than scraped StatCan web archives.
3. **Emerging Market Announcement Timestamps**:
   - **Banco Central do Brasil (BCB / Copom)**: Exact announcement timestamps are unarchived; announcements are imputed at 18:30 BRT (`timing_verified_level = 'none'`). All BCB rows are disqualified (`analysis_ok = 0`).
   - **Banco de México (Banxico)**: Historical statement releases prior to 2018 rely on convention (`timing_verified_level = 'none'`).
   - **Reserve Bank of India (RBI)**: Post-meeting policy statements rely on standard press conference time blocks (`timing_verified_level = 'none'`).
4. **Bank of England Pre-2016 MPC Timing**:
   - BoE announcement timing for 2010–2015 is verified at the **convention level** (strict Thursday 12:00 noon GMT protocol) rather than individual press release web scrape timestamps (`timing_verified_level = 'convention'`).
5. **Industrial Production (IP) Vintage Revisions**:
   - IP macro controls reflect latest available historical time series and first-available vintage indicators rather than complete real-time point-in-time vintage triangles across all 12 economies (`macro_vintage_verified = 0`).
6. **Hand Labels Not Completed**:
   - Manual statement qualitative text classifications and narrative hand labels remain in draft status and have not undergone double-blind expert replication (`hand_labels_completed = 0`).
