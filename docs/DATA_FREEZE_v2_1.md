# MoTrans-15 v2.1 Data Freeze Certification

**Release Tag**: `v2.1-train-test-ready`  
**Git Commit Hash**: `67cb97b60af58d2663e91333ebfacfe3780c8356`  
**Parent Freeze Tags**: `v1.0-data-freeze`, `v2.0-data-freeze`, `v2.0.1-data-freeze` (permanently preserved)  
**Certification Date**: 2026-10-25  
**Verification Engine**: Bitwise Double-Rebuild Verification Pass (Python 3.13)  

---

## 1. Parameters (Configured in src/v2_1_config.py and docs/v2_1_spec.md)

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

## 2. Cryptographic File Hashes (SHA-256)

Every file in `data/v2_1/` was rebuilt twice from raw sources; all hashes match identically across successive runs.

| File Path | SHA-256 Hash | Status |
| :--- | :--- | :---: |
| `data/v2_1/analysis_tier1.parquet` | `94147ec418d22fd62245e7ecc04bc5b3faf0a2c48cf05a456534033b2554681c` | **VERIFIED** |
| `data/v2_1/analysis_tier2_primary.parquet` | `04664cf26d6481bbf9ecea7c527b24c7b769ad9e46a411a6cc4531645880c818` | **VERIFIED** |
| `data/v2_1/secondary_holds.parquet` | `6da1bf61f376b11244d068cae4908c2bb79bf52a90277d4d8ebc1f7b0eb35fb9` | **VERIFIED** |
| `data/v2_1/panel.parquet` | `d0ba4036f39597288ab5b150736f34724827440ab9e8caba0c4dfca6373cbb08` | **VERIFIED** |
| `data/v2_1/sensitivity_macro_revision.parquet` | `bcc7410432bc09281eb70d3d6075f09d5d212dff3f13d85f938f794da04c6857` | **VERIFIED** |
| `data/v2_1/post_window_2026.parquet` | `2985cfaee580759108b8a91b8d94ae56695dbb8d57d359866b4835939c4a197b` | **VERIFIED** |
| `data/v2_1/excluded_rows.parquet` | `d47e52849543d15aaf18bbf334e88e37cec2fda9a6031cafe3cbb9aa8a9adcd1` | **VERIFIED** |
| `data/v2_1/folds.csv` | `f4dd7768afda09d2ac1d77aeba332ca402b5969d0bdb27334b618449c5e58cd4` | **VERIFIED** |
| `data/v2_1/release/analysis_tier1.parquet` | `94147ec418d22fd62245e7ecc04bc5b3faf0a2c48cf05a456534033b2554681c` | **VERIFIED** |
| `data/v2_1/release/analysis_tier2_primary.parquet` | `04664cf26d6481bbf9ecea7c527b24c7b769ad9e46a411a6cc4531645880c818` | **VERIFIED** |
| `data/v2_1/release/secondary_holds.parquet` | `6da1bf61f376b11244d068cae4908c2bb79bf52a90277d4d8ebc1f7b0eb35fb9` | **VERIFIED** |
| `data/v2_1/release/sensitivity_macro_revision.parquet` | `bcc7410432bc09281eb70d3d6075f09d5d212dff3f13d85f938f794da04c6857` | **VERIFIED** |
| `data/v2_1/release/panel_returns_only.parquet` | `e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620` | **VERIFIED** |
| `data/v2_1/release/folds.csv` | `f4dd7768afda09d2ac1d77aeba332ca402b5969d0bdb27334b618449c5e58cd4` | **VERIFIED** |

---

## 3. Reproduction Command

To reproduce the complete MoTrans-15 v2.1 dataset from raw sources in non-interactive batch mode:

```bash
# 1. Checkout v2.1 freeze tag
git checkout v2.1-train-test-ready

# 2. Re-run complete pipeline and v2.1 table builder
python -m src.pipeline
python -m src.v2_fix_cbr_dates
python -m src.v2_1_build_tables
python -m src.v2_1_leakage_audit
python -m src.v2_1_freeze

# 3. Run full test suite (no path, no -k)
pytest
```

---

## 4. Release Distribution & Privacy

Per distribution agreements, proprietary equity closing index levels are omitted from public release bundles:
- `data/v2_1/release/panel_returns_only.parquet` provides continuous log returns (`ret_local`, `ret_usd`) without proprietary price levels (`level_local`).
- All cumulative event returns (`clr_1`, `clr_3`, `clr_5`, `clr_20`, `clr_60`), monetary shocks (`shock_raw_bp`), and as-of macro controls are fully accessible in `data/v2_1/release/analysis_tier1.parquet` and `data/v2_1/release/analysis_tier2_primary.parquet`.
- Due to upstream licensing terms for financial market indices, this release directory **must remain private and not redistributed** until commercial and academic distribution terms are cleared.
