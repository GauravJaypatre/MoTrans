# Methodological & Data Limitations — MoTrans-15 v2.0 (Phase V1 Addendum)

**Status**: Formal Record of Known Constraints and Unverified Items  
**Date**: 2026-10-24  

---

## 1. Single-Source Price Series & Anti-Bot Constraints
- Per instructions, Stooq was not scripted due to Cloudflare anti-bot restrictions. No manual CSVs were present in `data/raw/second_source/`.
- FRED second sources were downloaded via verified HTTPS for US and Japan:
  - S&P 500 (`^GSPC`): Matches FRED `SP500` within 1.2 bp max diff across 2,510 overlapping days (only 0.16% > 1 bp due to rounding).
  - Nikkei 225 (`^N225`): Direct calendar alignment with FRED `NIKKEI225` failed after two attempts (99.7% of days > 1 bp difference). Root cause: FRED logs Tokyo exchange closing levels on the subsequent US observation date (T+1 calendar lag). When shifted by 1 business day to account for FRED's US-centric reporting convention, price levels match to cents.
  - All 36 remaining equity index series have no secondary source and remain strictly classified as `single-source`.

## 2. Policy Decisions Discrepancies
- **RBA 2026-09-29**: The v1 dataset recorded `decision = hold, size_bp = 0.0, new_rate_pct = 4.35%`. Official RBA Media Release 2026-27 (released 29 September 2026) confirmed: *"At its meeting today, the Board decided to increase the cash rate target by 25 basis points to 4.60 per cent."* (Effective 30 September 2026). The v1 record is erroneous.
- **CBR Meeting vs Effective Dates**: v1 recorded Monday effective dates from BIS `WS_CBPOL/D.RU` rather than the official Friday Board decision announcement dates.
- **BoJ Complementary Lending Facility**: In 2026, BIS `WS_CBPOL/D.JP` records the Complementary Lending Facility rate (0.75% -> 1.00% -> 1.25%), rather than the uncollateralized call rate target. Meeting dates and direction of actions match official MPM statements.

## 3. Macro Controls Vintage Contamination (`ind_prod`)
- Industrial Production from OECD STES represents the latest revised historical vintage rather than real-time first releases. Because industrial production undergoes substantial revisions (up to 12 months after reference month), including it in contemporaneous policy event studies introduces revision/lookahead contamination.
- Flagged with `revised_series = 1` and excluded from the default v2 control set (retained only in a labeled sensitivity set).
- In contrast, CPI is conservative: official release calendars from BLS, Eurostat, ONS, StatCan, ABS, and SBJ confirm that all releases occur in month m+1, strictly preceding the dataset's `available_from = 1st of month m+2` rule (zero lookahead).

## 4. Announcement Timing Verification Scope
- Announcement times for 100 events across 10 convention periods for Fed, ECB, BoE, BoC, and RBA were officially verified against saved release page headers.
- All other events remain `timing_verified = 0`.

## 5. ETF Proxy Tracking Errors
Tradeable ETF proxies exhibit tracking divergence from cash benchmarks due to expense ratios, dividend timing, cash drag, and localized index composition:
- `ea_emu_smallcap_etf` vs `de_mdax`: Annualized Tracking Error = 9.28%, Correlation = 0.8673.
- `de_stoxx_banks_etf` vs `de_dax_banks`: Annualized Tracking Error = 17.70%, Correlation = 0.8583.
- `jp_topix_banks_etf` vs `jp_nikkei225`: Annualized Tracking Error = 20.52%, Correlation = 0.6676.
- `kr_banks_etf` vs `kr_kospi`: Annualized Tracking Error = 22.44%, Correlation = 0.5546.
- `jp_mothers_etf` vs `jp_nikkei225`: Annualized Tracking Error = 31.65%, Correlation = 0.5145.
All 5 series are marked with `proxy_type = 'etf_proxy'`.

## 6. High-Frequency Shock Coverage Truncation
- High-frequency monetary shock series end prematurely relative to the full dataset:
  - Federal Reserve (FRBSF Bauer-Swanson): Ends **December 2023** (zero Tier 1 shocks in 2024–2026).
  - European Central Bank (EA-MPD): Ends **October 2025** (zero Tier 1 shocks in 2026).
- Post-truncation events fall back to Tier 2 daily sovereign yield proxies, which capture rate changes but lack intraday precision on rate holds.

## 7. Omitted Emerging Market Shocks
Per the narrowed Phase V1 scope:
- Banxico (MX), BoK (KR), RBI (IN), PBoC (CN), and BCB (BR) lack daily 1Y sovereign yield proxies in the v1 pipeline, producing 0 primary shocks. These regimes are marked `'not verified: no primary shocks'` and excluded from primary time-series forecasting models.
- CBR (RU) is audited only prior to 2022-02-24 due to subsequent capital controls and exchange suspensions.
