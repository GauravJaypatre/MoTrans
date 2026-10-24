# Methodological & Data Limitations — MoTrans-15 v2.0

**Status**: Formal Record of Known Constraints and Unverified Items  
**Date**: 2026-10-24  

---

## 1. Single-Source Price Series & Anti-Bot Constraints
- Automated external downloaders (Stooq, FRED) encountered Cloudflare JavaScript challenges and request timeouts. Consequently, 27 index series currently rely on single-source Yahoo Finance feeds (marked `single-source` in [`outputs/v2/price_crosscheck.csv`](file:///c:/Users/HP/OneDrive/المستندات/Projects/MoTrans/outputs/v2/price_crosscheck.csv)).
- 11 series are verified against independent primary exchange archives: Moscow Exchange ISS (`ru_imoex`, `ru_moex_fin`, `ru_moex_smid`), CSI (`cn_csi300`, `cn_csi300_banks`, `cn_csi500`), B3 (`br_ifnc`, `br_smll`), and NSE India (`in_nifty50`, `in_nifty_bank`, `in_nifty_smallcap100`).

## 2. ETF Proxy Tracking Errors
Tradeable ETF proxies exhibit tracking divergence from cash benchmarks due to expense ratios, dividend timing, cash drag, and localized index composition:
- `ea_emu_smallcap_etf` vs `de_mdax`: Annualized Tracking Error = 9.28%, Correlation = 0.8673.
- `de_stoxx_banks_etf` vs `de_dax_banks`: Annualized Tracking Error = 17.70%, Correlation = 0.8583.
- `jp_topix_banks_etf` vs `jp_nikkei225`: Annualized Tracking Error = 20.52%, Correlation = 0.6676.
- `kr_banks_etf` vs `kr_kospi`: Annualized Tracking Error = 22.44%, Correlation = 0.5546.
- `jp_mothers_etf` vs `jp_nikkei225`: Annualized Tracking Error = 31.65%, Correlation = 0.5145.
All 5 series are marked with `proxy_type = 'etf_proxy'`.

## 3. High-Frequency Shock Coverage Truncation
- High-frequency monetary shock series end prematurely relative to the full dataset:
  - Federal Reserve (FRBSF Bauer-Swanson): Ends **December 2023** (zero Tier 1 shocks in 2024–2026).
  - European Central Bank (EA-MPD): Ends **October 2025** (zero Tier 1 shocks in 2026).
- Post-truncation events fall back to Tier 2 daily sovereign yield proxies, which capture rate changes but lack intraday precision on rate holds.

## 4. Omitted Emerging Market Shocks
Per the narrowed Phase V1 scope:
- Banxico (MX), BoK (KR), RBI (IN), PBoC (CN), and BCB (BR) lack daily 1Y sovereign yield proxies in the v1 pipeline, producing 0 primary shocks. These regimes are marked `'not verified: no primary shocks'` and excluded from primary time-series forecasting models.
- CBR (RU) is audited only prior to 2022-02-24 due to subsequent capital controls and exchange suspensions.

## 5. BoJ Policy Instruments & Discrete Rate Labels
- During the Kuroda QQE and negative interest rate regimes (2013–2016), target policy rates were not the active operating instrument. Unclassified decisions contain non-zero or NaN target rate changes (`size_bp`). Any sensitivity modeling on BoJ must strictly use monetary surprise variables (`shock_primary`, `shock_usable`), not discrete hike/cut classification labels.
