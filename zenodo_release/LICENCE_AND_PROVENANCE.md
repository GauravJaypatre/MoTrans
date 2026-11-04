# MoTrans-15 v2.1.1 Data Source Licence & Provenance Audit

This document provides an inventory of all data providers, quoting their stated terms directly from `data/raw/MANIFEST.csv` and documenting licensing questions for research dissemination.

## Summary of Licencing Status

- **Selected Access Mode**: `restricted` (Access granted by request via Zenodo for academic replication).
- **Data Licence**: Custom 'Other (non-open)' research-use license. Authors' original contributions are CC-BY-4.0 and MIT; derived return tables are restricted and subject to vendor terms. Any future open release is possible only if vendors permit, with no timeline.
- **Proprietary Closing Price Levels**: **Omitted** (`level_local` excluded from all packaged tables; `panel_returns_only.parquet` provides continuous log returns without starting levels).
- **Raw Data Status**: Excluded from package (`data/raw/` contains vendor feeds that cannot be redistributed).

## Provider Inventory & Quoted Terms

### Bank for International Settlements (BIS)

- **Data Category**: Central Bank Policy Rates
- **What is Used**: Daily central bank policy target rate histories across 15 economies (1999-2026)
- **Sample URL / API**: `https://stats.bis.org/api/v1/data/WS_CBPOL/D.AU?format=csv&startPeriod=1999-01-01`
- **Retrieval Timestamp (UTC)**: `2026-10-13T14:19:18Z` (total files tracked: 39)
- **Stated Terms (Quoted)**: *"BIS terms of use: free reuse with attribution"*
- **Open Legal / Scientific Question**: Does BIS permit open redistribution of parsed daily policy rates, or does academic use require attribution only?

### Federal Reserve Bank of St. Louis (FRED)

- **Data Category**: Macro Controls & US Benchmarks
- **What is Used**: S&P 500 (SP500) and Nikkei 225 (NIKKEI225) second-source cross-verification series; US macro controls
- **Sample URL / API**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM`
- **Retrieval Timestamp (UTC)**: `2026-10-24T16:57:30Z` (total files tracked: 3)
- **Stated Terms (Quoted)**: *"FRED Terms of Use; NASDAQ OMX Group attribution"*
- **Additional Quoted Terms**: *"FRED Terms of Use; Nikkei Inc. attribution"*, *"FRED Terms of Use; S&P Dow Jones Indices LLC attribution"*
- **Open Legal / Scientific Question**: Third-party series hosted on FRED (S&P Dow Jones Indices, Nikkei Inc.) prohibit raw commercial distribution. Are derived log return windows permitted under academic fair use?

### European Central Bank (EA-MPD / Altavilla et al. 2019)

- **Data Category**: High-Frequency Shocks
- **What is Used**: Tier 1 high-frequency monetary policy surprise measures (1Y OIS intraday changes) for Euro Area decisions
- **Sample URL / API**: `https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_C.SV_C_YM.SR_1Y?format=csvdata`
- **Retrieval Timestamp (UTC)**: `2026-10-13T14:21:53Z` (total files tracked: 6)
- **Stated Terms (Quoted)**: *"ECB reuse policy"*
- **Additional Quoted Terms**: *"ECB reuse policy / Academic citation (Altavilla et al. 2019)"*, *"ECB reuse policy (free reuse with attribution)"*
- **Open Legal / Scientific Question**: EA-MPD dataset terms request academic citation (Altavilla et al. 2019). Are package derivatives free to redistribute under CC-BY-4.0?

### Federal Reserve Bank of San Francisco (Bauer & Swanson 2023)

- **Data Category**: High-Frequency Shocks
- **What is Used**: Tier 1 high-frequency monetary policy surprise measures (orthogonalized MPS) for FOMC announcements through 2023
- **Sample URL / API**: `https://www.frbsf.org/wp-content/uploads/monetary-policy-surprises-data.xlsx`
- **Retrieval Timestamp (UTC)**: `2026-10-21T16:50:41Z` (total files tracked: 1)
- **Stated Terms (Quoted)**: *"FRBSF public data; cite Bauer and Swanson (2023)"*
- **Open Legal / Scientific Question**: Public domain academic series ending Dec 2023. Does fallback to 1-day sovereign yield proxy in 2024-2025 introduce regime discontinuity?

### Central Bank Official Web Portals (Fed, BoE, BoC, RBA, BoJ, CBR, RBI, BCB, Banxico)

- **Data Category**: Policy Decisions & Statements
- **What is Used**: Official policy decision dates, press release timestamps, monetary statements, and sovereign benchmark yields
- **Sample URL / API**: `https://www.boj.or.jp/en/mopo/mpmsche_minu/minu_2000/index.htm`
- **Retrieval Timestamp (UTC)**: `2026-10-13T12:22:10Z` (total files tracked: 1439)
- **Stated Terms (Quoted)**: *"BoJ website terms of use (credit the source)"*
- **Additional Quoted Terms**: *"BoJ Terms of Use"*, *"BCB open data (free reuse)"*, *"Bank of Canada terms (free reuse with attribution)"*
- **Open Legal / Scientific Question**: Terms vary from Open Government Licence (UK BoE) and Public Domain (US Fed) to standard website terms (BoJ, CBR, RBI). Unarchived intraday times for BCB, Banxico, RBI necessitate convention-based exclusion.

### Financial Index Providers (Yahoo Finance, B3 S.A., Moscow Exchange, CSI, NSE Indices)

- **Data Category**: Equity Index Price Series
- **What is Used**: Daily closing prices for 38 equity indices used strictly to compute cumulative event returns (clr_1 to clr_60)
- **Sample URL / API**: `yfinance:^VIX history(period='max')`
- **Retrieval Timestamp (UTC)**: `2026-10-13T14:26:06Z` (total files tracked: 39)
- **Stated Terms (Quoted)**: *"Yahoo Finance terms of service (no redistribution)"*
- **Additional Quoted Terms**: *"Yahoo Finance Terms of Service"*, *"NSE Indices Limited website terms of use (no redistribution of data)"*, *"NSE Indices Limited Terms of Use (internal/research use permitted)"*
- **Open Legal / Scientific Question**: Closing index levels (level_local) are strictly proprietary and omitted from release tables. Do exchange terms permit distribution of derived return residuals in restricted academic releases without licensed price levels?

