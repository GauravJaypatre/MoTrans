# MoTrans-15 v2.0 Data Freeze Certification

**Release Tag**: `v2.0.1-data-freeze` (CBR emergency alignment, non-decision exclusion, and usable sample freeze)  
**Initial v2.0 Tag**: `v2.0-data-freeze` (commit `1f9688bf8f3c2429875bcb6d71d032e70b774254`, preserved unchanged)  
**Git Commit Hash**: `a4bc9d6a4b210459247bf612a65cc0bd1a922101`  
**Parent Freeze**: `v1.0-data-freeze` (permanently locked and preserved)  
**Certification Date**: 2026-10-25  
**Verification Engine**: Bitwise Double-Rebuild Verification Pass  

---

## 1. Cryptographic File Hashes (SHA-256)

Every file in `data/v2/` was rebuilt twice from raw sources; all hashes match identically across successive runs.

| File Path | SHA-256 Hash | Status |
| :--- | :--- | :---: |
| `data/v2/analysis_tier1_2010plus.parquet` | `4062b36d62c415f8d24ab1a5aac79a85c10ce1d9c9d308470ccf2cd618b4fb0a` | **VERIFIED** |
| `data/v2/analysis_tier2_primary_2010plus.parquet` | `eacd0c7806029962f7a92066376210d46de7853d2bc03d686a72d61864c25c3b` | **VERIFIED** |
| `data/v2/panel_2010plus.parquet` | `ce60842095b1801d8b93a1edc1ab5f7b93253a190984213235ee6a356ea4368b` | **VERIFIED** |
| `data/v2/release/analysis_tier1_2010plus.parquet` | `4062b36d62c415f8d24ab1a5aac79a85c10ce1d9c9d308470ccf2cd618b4fb0a` | **VERIFIED** |
| `data/v2/release/analysis_tier2_primary_2010plus.parquet` | `eacd0c7806029962f7a92066376210d46de7853d2bc03d686a72d61864c25c3b` | **VERIFIED** |
| `data/v2/release/panel_2010plus_returns_only.parquet` | `7ec0a5e8626dd3cf8e960fc12e41923236aa1a7c9b96a160724fdf375993febc` | **VERIFIED** |
| `data/v2/release/secondary_holds_2010plus.parquet` | `2a12ae025995f10e89d941ee57f07f2f21b2def97ff6862eacadd9340f1def6e` | **VERIFIED** |
| `data/v2/release/sensitivity_macro_revision_2010plus.parquet` | `e8c9a35535ecbf5fbc6a9a6dfedece7885c7cd3bf317f3bd0535288b498fa59b` | **VERIFIED** |
| `data/v2/secondary_holds_2010plus.parquet` | `2a12ae025995f10e89d941ee57f07f2f21b2def97ff6862eacadd9340f1def6e` | **VERIFIED** |
| `data/v2/sensitivity_macro_revision_2010plus.parquet` | `e8c9a35535ecbf5fbc6a9a6dfedece7885c7cd3bf317f3bd0535288b498fa59b` | **VERIFIED** |

---

## 2. Reproduction Command

To reproduce the complete MoTrans-15 v2.0 dataset from raw sources in non-interactive batch mode:

```bash
# 1. Checkout v2.0.1 freeze tag
git checkout v2.0.1-data-freeze

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

