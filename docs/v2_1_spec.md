# MoTrans-15 v2.1 Dataset Specification

## 1. Scope & Primary Parameters

This document defines the official parameters for **MoTrans-15 v2.1**, the training and testing-ready dataset covering monetary policy decisions from 2010-01-01 through 2025-12-31.

All parameters are configured in [`src/v2_1_config.py`](file:///c:/Users/HP/OneDrive/المستندات/Projects/MoTrans/src/v2_1_config.py):

| Parameter | Value | Description |
| :--- | :---: | :--- |
| `WINDOW_START` | `2010-01-01` | Official start of the evaluation panel |
| `WINDOW_END` | `2025-12-31` | Official cutoff for train, validation, and test splits |
| `TRAIN` | `2010-01-01` to `2021-12-31` | Primary historical training window (12 calendar years) |
| `VALIDATION` | `2022-01-01` to `2023-12-31` | Hyperparameter tuning and model selection window |
| `TEST` | `2024-01-01` to `2025-12-31` | Strictly locked out-of-sample test window |
| `EMBARGO_DAYS` | `60` | Embargo buffer (events whose `clr_60` horizon reaches across boundaries are dropped) |
| `POST_WINDOW` | `2026-01-01+` | Excluded from evaluation splits; quarantined to `post_window_2026.parquet` |

---

## 2. Table Layout

All tables reside under `data/v2_1/`:
1. `analysis_tier1.parquet`: Fed and ECB decisions with high-frequency monetary shocks (Bauer-Swanson MPS and EA-MPD OIS 1Y).
2. `analysis_tier2_primary.parquet`: Rate-change decisions for BoE, BoC, RBA, CBR, and Fed/ECB fallbacks using sovereign yield proxies.
3. `secondary_holds.parquet`: Scheduled hold decisions (sensitivity only).
4. `panel.parquet`: Daily equity panel with log returns, macro controls, and volatility indicators for 2010–2025.
5. `sensitivity_macro_revision.parquet`: Industrial production revision vintages and real-time release controls.
6. `excluded_rows.parquet`: Fully traceable record of all excluded event rows with explicit reasons (`policy_verified == 0`, `timing_ambiguous`, `timing_verified_level == none`, `MOEX halt`, `embargo_dropped`).
7. `post_window_2026.parquet`: Quarantined post-window observations (2026).

---

## 3. Leakage Guardrails

1. **Embargo Isolation**: Any decision whose 60-day event window (`clr_60`) extends across a split boundary (or within 60 calendar days of the boundary) is flagged `embargo_dropped = 1` and excluded from the earlier split.
2. **Model Guard Lock**: The test set and post-window set are locked by default; accessing them without explicit environment variables (`UNLOCK_TEST=1` and `UNLOCK_POST=1`) raises `PermissionError`.
3. **Decoupled Scaling**: Shocks include `shock_raw_bp` unscaled; any standardisation in model pipelines is performed within each training fold.
