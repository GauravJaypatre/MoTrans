# MoTrans-15 Public Release Dataset (v1.0-data-freeze)

**Project**: Monetary Transmission to Equities Across the 15 Largest Economies (MoTrans-15)  
**Release Version**: `v1.0-data-freeze`  
**License**: Open Research License / Academic Use  

---

## 1. Overview & Contents

This release package contains the complete computational code, econometric analysis tables, central bank text corpus, and derived monetary policy shock series for the MoTrans-15 project.

The release is structured as follows:
- `src/`: Complete modular data collection, event-alignment, shock construction, and estimation pipeline.
- `tests/`: Comprehensive test suite (137 unit and integration tests asserting zero look-ahead, timing consistency, and mathematical identities).
- `docs/`: Full documentation including:
  - `docs/data_dictionary.md`: Authoritative schema definition for all tables.
  - `docs/preregistration.md`: Pre-registered analysis plan, methodological lock, and dated amendments.
  - `docs/limitations.md`: Complete disclosure of effective samples, proxy quality, and horizon overlap.
  - `docs/labelling_guide.md`: Statement annotation rubric and scale definitions.
  - `docs/DATA_FREEZE.md`: Provenance hashes, environment specifications, and replication commands.
- `data/final/`:
  - `analysis_tier1.parquet`: Headline high-frequency identification panel (ECB and Fed consensus surprises x 38 indices) with zero look-ahead controls.
  - `analysis_tier2_primary.parquet`: Primary sovereign yield proxy transfer panel for rate-change decisions.
  - `shocks.parquet`: Full catalog of standardized and winsorized policy shocks across all 12 regimes.
  - `policy_decisions.csv`: Complete catalog of 2,491 monetary policy decisions with announcement timestamps and timing quality flags.
  - `events.parquet`: Decision x reacting index event study observations with cumulative log returns (`clr_1` to `clr_60`).
  - `statements.parquet`: Full text corpus of English-language central bank policy statements (Fed, ECB, BoJ, RBI).
  - `panel_daily.parquet`: Harmonized daily panel of returns and macroeconomic controls (with proprietary price levels excluded).
- `data/raw/`:
  - `MANIFEST.csv`: Bitwise SHA-256 provenance manifest for every downloaded raw file.
  - `timing_sources/`: Saved official central bank release pages verifying policy announcement conventions.

---

## 2. Excluded Data & Licensing Notice

### Excluded Items:
1. **Daily Equity Price Levels (`level_local`)**: The raw daily index closing level series in `data/final/panel_daily.parquet` has been redacted (set to NaN).
2. **Raw Equity Series Files**: Raw downloaded price files (e.g. `data/raw/indices/`) are excluded.
3. **Consolidated Excel Workbook (`MoTrans15_v2.xlsx`)**: Excluded because it embeds raw index price levels.

### Rationale for Exclusion:
Commercial index providers (including S&P Dow Jones Indices, FTSE Russell, STOXX Ltd., Deutsche Börse, MOEX, and NSE India) and financial data vendors prohibit the public redistribution of raw historical price level time series.

### Redistribution Compliance:
All derived mathematical transformations—including daily log returns (`ret_local`, `ret_usd`), cumulative event-window log returns (`clr_1` to `clr_60`), realized volatility (`vol_realized_20d`), standardized monetary shocks (`shock_std`), and macroeconomic controls—are fully retained. Researchers wishing to reconstruct exact raw price levels can execute the automated collectors in `src/collect_indices.py` to retrieve series directly from authorized endpoints.

---

## 3. Quick Start & Reproduction

### Prerequisites:
- Python 3.12+ (or 3.13)
- Dependencies installed via:
  ```bash
  pip install -r requirements.txt
  ```

### Running Tests:
Verify the integrity of all data transformations and event window alignments:
```bash
pytest -v
```

### Reproducing Analysis Tables:
To regenerate the final analysis tables from the provided data:
```bash
python -m src.build_analysis_tables
```
