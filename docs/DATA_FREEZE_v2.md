# MoTrans-15 v2.0 Data Freeze Certification

**Release Tag**: `v2.0-data-freeze`  
**Git Commit Hash**: `b2c5ffbdc81a2e4543bb10ec8de229a0aaa2b06e`  
**Parent Freeze**: `v1.0-data-freeze` (permanently locked and preserved)  
**Certification Date**: 2026-10-25  
**Verification Engine**: Bitwise Double-Rebuild Verification Pass  

---

## 1. Cryptographic File Hashes (SHA-256)

Every file in `data/v2/` was rebuilt twice from raw sources; all hashes match identically across successive runs.

| File Path | SHA-256 Hash | Status |
| :--- | :--- | :---: |
| `data/v2/analysis_tier1_2010plus.parquet` | `619301e89858ae428dd456818fa45e75e69eacb5367b6b0b2a6f47350aa1fe16` | **VERIFIED** |
| `data/v2/analysis_tier2_primary_2010plus.parquet` | `1654a1714d1ea916584b20db18b51a16d54088854a7e4dbd045cfc612737ebeb` | **VERIFIED** |
| `data/v2/panel_2010plus.parquet` | `ce60842095b1801d8b93a1edc1ab5f7b93253a190984213235ee6a356ea4368b` | **VERIFIED** |
| `data/v2/release/analysis_tier1_2010plus.parquet` | `619301e89858ae428dd456818fa45e75e69eacb5367b6b0b2a6f47350aa1fe16` | **VERIFIED** |
| `data/v2/release/analysis_tier2_primary_2010plus.parquet` | `1654a1714d1ea916584b20db18b51a16d54088854a7e4dbd045cfc612737ebeb` | **VERIFIED** |
| `data/v2/release/panel_2010plus_returns_only.parquet` | `7ec0a5e8626dd3cf8e960fc12e41923236aa1a7c9b96a160724fdf375993febc` | **VERIFIED** |
| `data/v2/release/secondary_holds_2010plus.parquet` | `441a3ad8df52d3e8204d169a859e6154e404c86529e372605287bddec6f63f34` | **VERIFIED** |
| `data/v2/release/sensitivity_macro_revision_2010plus.parquet` | `a5c2a0c2b95f704502da4856b9171d43c0221162e5b24802baf10bd6b33d7f0a` | **VERIFIED** |
| `data/v2/secondary_holds_2010plus.parquet` | `441a3ad8df52d3e8204d169a859e6154e404c86529e372605287bddec6f63f34` | **VERIFIED** |
| `data/v2/sensitivity_macro_revision_2010plus.parquet` | `a5c2a0c2b95f704502da4856b9171d43c0221162e5b24802baf10bd6b33d7f0a` | **VERIFIED** |

---

## 2. Reproduction Command

To reproduce the complete MoTrans-15 v2.0 dataset from raw sources in non-interactive batch mode:

```bash
# 1. Checkout v2.0 freeze tag
git checkout v2.0-data-freeze

# 2. Re-run complete pipeline and v2 tables builder
python -m src.pipeline
python -m src.v2_fix_cbr_dates
python -m src.v2_build_tables
python -m src.v2_freeze

# 3. Run full test suite
pytest
```

---

## 3. Release Distribution (Licensed Price Levels Protection)

Per distribution agreements, proprietary equity closing index levels are omitted from public release bundles:
- `data/v2/release/panel_2010plus_returns_only.parquet` provides continuous log returns (`ret_local`, `ret_usd`) and macro controls without distributing closing price levels (`level_local`).
- All cumulative event returns (`clr_1`, `clr_3`, `clr_5`, `clr_20`, `clr_60`), monetary shocks, and as-of macro controls are fully accessible in `data/v2/release/analysis_tier1_2010plus.parquet` and `data/v2/release/analysis_tier2_primary_2010plus.parquet`.

