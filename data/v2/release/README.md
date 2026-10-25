# MoTrans-15 v2.0 Release Bundle — Notice & Licensing Constraints

## 1. Derived Returns from Licensed Price Levels
The data tables included in this release directory (`data/v2/release/`):
- `analysis_tier1_2010plus.parquet`
- `analysis_tier2_primary_2010plus.parquet`
- `secondary_holds_2010plus.parquet`
- `sensitivity_macro_revision_2010plus.parquet`
- `panel_2010plus_returns_only.parquet`

contain continuous daily logarithmic returns (`ret_local`, `ret_usd`) and event-window cumulative log returns (`clr_1`, `clr_3`, `clr_5`, `clr_20`, `clr_60`).

While proprietary raw closing index levels (`level_local`) have been stripped from `panel_2010plus_returns_only.parquet`, the underlying returns are mathematically derived from licensed closing prices provided under exchange and data vendor terms.

## 2. Licensing Uncertainty & Private Distribution Requirement
Due to legal ambiguity and potential licensing restrictions surrounding the redistribution of derived continuous return series across multiple global exchanges (including Euronext, Deutsche Börse, London Stock Exchange, Tokyo Stock Exchange, TSX, ASX, MOEX, B3, and BMV):

> [!CAUTION]
> **STRICT PRIVATE USE REQUIREMENT**:
> This release bundle must remain strictly **PRIVATE**, confidential, and restricted to authorized local research environments.
> Under NO circumstances may these parquet or CSV files be redistributed in public repositories, shared via open public web endpoints, or distributed outside the project pair without formal written verification of exchange licensing terms and commercial redistribution agreements.
