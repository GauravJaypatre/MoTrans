# Data Freeze & Provenance Audit — MoTrans-15

**Project**: Monetary Transmission to Equities Across the 15 Largest Economies (MoTrans-15)  
**Freeze Version**: `v1.0-data-freeze`  
**Git Tag**: `v1.0-data-freeze`  
**Freeze Date**: 2026-10-24  
**Pipeline Status**: Frozen. Double rebuild verified with 100% bitwise identity. Test suite passed (140/140).

---

## 1. Bitwise SHA-256 Checksums

All final datasets are deterministically generated from `data/raw/` alone via `python -m src.pipeline` and `python -m src.export_excel`.

### Final Analysis Datasets (`data/final/`)

| File | Size (Bytes) | SHA-256 Checksum |
|---|---|---|
| `analysis_tier1.parquet` | 1,109,418 | `beaa4563023f6b6a22d0ed0131ca0a4049f4728494101607a3f3c89a003d5bae` |
| `analysis_tier2_primary.parquet` | 447,926 | `83f3c53736ff588423a94acdd5ab88377265d967df6bde00a0a3e2e7a9f70628` |
| `events.parquet` | 4,874,542 | `1097551c08cd5cfcfa6c061aba20ee4e607b5a7848493e2aecb3622e321a5b54` |
| `hand_label_sample_with_text.csv` | 2,664,068 | `1591b0d47499d9242a4b4c2355809d3f61d49801cd6ffc3eab426847f4eccc64` |
| `panel_daily.parquet` | 8,559,700 | `26a149972615b4bc2f6fd90173ba036768244c05b75e6262a20ea2235f0b79b1` |
| `policy_decisions.csv` | 1,235,904 | `4df411b05cb066efab17d6e6b0393638cd4112db6f7a377ec84a099512cd58d1` |
| `shocks.parquet` | 165,471 | `e793c6e94a9444bdf9981bb801c0e52a96c00122f6040cb83e5a1d8b73911093` |
| `statements.parquet` | 6,010,746 | `975a7f6e1e6924d62d124fcefc596f1ba1da0e1c8cd813e0f79bcd786e1c9271` |
| `MoTrans15_v2.xlsx` | 63,100,350 | `3d54fa6a3ed837e28c8b57e373a1a70d3196cf2b426c3614aedf604c993c7695` |
| `MoTrans15_all_records.xlsx` (v1) | 52,137,981 | `cd4887f5b506662f074125edbb3aef09c39a7d8c73ec8a57885d80c01d78f8a3` |

### Raw Manifest (`data/raw/`)

| File | SHA-256 Checksum |
|---|---|
| `data/raw/MANIFEST.csv` | `77a19175d1eac69f11e4e2b4d7385660ac0b9c97dd72e0d11294dee6646359ba` |

---

## 2. Core Python Environment & Package Versions

- **Python Runtime**: `3.13.1` (compatible with Python `3.12+`)
- **Operating System**: Windows 11 (64-bit)

### Key Scientific & Econometric Packages:
- `pandas`: `2.3.1`
- `numpy`: `2.3.1`
- `pyarrow`: `26.0.0`
- `scipy`: `1.16.0`
- `scikit-learn`: `1.7.1`
- `openpyxl`: `3.1.5`
- `exchange_calendars`: `4.13.2`
- `pandas_market_calendars`: `5.5.0`
- `statsmodels`: `0.14.5`
- `requests`: `2.32.4`
- `pytest`: `9.1.1`

Complete dependencies are locked in `requirements.txt`.

---

## 3. Exact Commands to Reproduce

To reproduce the frozen dataset from scratch starting from `data/raw/`:

```bash
# 1. Install locked dependencies in a virtual environment
pip install -r requirements.txt

# 2. Run the end-to-end data pipeline (cleans data/interim and data/final)
python -m src.pipeline

# 3. Export the consolidated Excel workbook (MoTrans15_v2.xlsx)
python -m src.export_excel

# 4. Verify all tests (asserts 140/140 passed)
pytest -v

# 5. Run the double rebuild verification (asserts bit-for-bit SHA-256 determinism)
python -m scratch.verify_double_rebuild
```

---

## 4. Freeze Invariance Rule

Under tag `v1.0-data-freeze`:
- No files under `data/final/` may be altered, regenerated, or re-dated.
- Any future change to policy dates, shock definitions, or sample rules must be introduced as a new minor version (e.g. `v1.1.0`) accompanied by a formal entry in `CHANGELOG.md` and an updated freeze document.
