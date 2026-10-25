# Known Limitations & Methodological Constraints — MoTrans-15

This document outlines the known methodological, data, and institutional limitations of the MoTrans-15 dataset in plain language. Researchers and users should review these constraints prior to conducting econometric modeling or interpreting causal estimates.

---

## 1. Effective Sample Size by Tier

Although the MoTrans-15 catalog contains **2,491 central bank policy decisions** across 12 monetary regimes from 2000 to 2026, only a subset meets the rigorous pre-registered criteria for causal identification:

- **Effective Analysis Sample**: Strictly **670 decisions** satisfy `shock_primary == 1 AND analysis_ready_timing == 1`.
- **Tier 1 (High-Frequency Consensus Surprises)**:
  - **494 decisions total**: 292 European Central Bank (ECB) decisions and 202 US Federal Reserve (Fed) decisions.
  - **By Split**: 413 `train` (≤2019), 34 `crisis` (2020–2021), and **47 held-out `blind_test`** decisions (2022+).
  - This constitutes the headline primary benchmark for monetary transmission.
- **Tier 2 Primary (Sovereign Yield Proxies on Rate-Change Days)**:
  - **176 decisions total**: 71 RBA (Australia), 41 CBR (Russia), 29 BoC (Canada), 25 BoE (United Kingdom), 8 Fed fallback, and 2 ECB fallback decisions.
  - **By Split**: 86 `train`, 19 `crisis`, and **71 held-out `blind_test`** decisions.
  - Serves as an out-of-sample transfer evaluation evaluating cross-border generalization to daily sovereign yields.
- **Excluded Decisions (1,424 total)**:
  - Decisions without verified timing evidence (`analysis_ready_timing == 0`), including pre-2016 BoE, pre-2013 BoC, pre-2013 CBR, and all Banxico, BoK, and RBI decisions.
  - Pre-2008 unannounced RBA holds (68 meetings where no statement was issued).
  - Regimes operating under exchange-rate or bond yield pegs (BoJ ZIRP/YCC).

---

## 2. High-Frequency Series Coverage End Dates

High-frequency intraday monetary policy surprise series rely on academic and institutional databases with fixed historical coverage:

- **US Federal Reserve**: The FRBSF Bauer-Swanson consensus intraday futures series ends on **13 December 2023**. Fed decisions in 2024, 2025, and 2026 fall back to daily 1-year Treasury yield changes (`shock_tier = 2`).
- **European Central Bank**: The Euro Area Monetary Policy Event-Study Database (EA-MPD; Altavilla et al., 2019) ends on **30 October 2025**. ECB decisions after this date fall back to daily 1-year German sovereign yield changes (`shock_tier = 2`).
- Consequently, while the dataset extends to late 2026, true intraday high-frequency identification is unavailable for the most recent FOMC meetings.

---

## 3. Regimes Without Usable Causal Shocks

Four of the 12 central bank regimes cannot be used for primary causal shock estimation due to data availability and market structure constraints:

- **Banxico (Mexico), Bank of Korea (BoK), and Reserve Bank of India (RBI)**: Lack continuous, freely accessible, daily short-term sovereign bond yield histories without paywalls or restrictive terms. While policy rates and statements are fully tracked, their shocks are graded `C` (unusable for econometric identification).
- **Banco Central do Brasil (BCB)**: The daily 1-year interbank deposit swap series (SGS 7806) ceased publication in December 2019. Consequently, BCB decisions from 2020 onward have no continuous daily yield proxy.
- **People's Bank of China (PBoC)**: Operates under a shifting regulatory framework where benchmark lending rates transitioned to the Loan Prime Rate (LPR). Daily 2-year sovereign yield proxies exhibit weak institutional linkage to policy rate directives.

---

## 4. Proxy Quality & Hold-Day Noise

Empirical variance ratio audits revealed a major structural divergence between policy actions and policy holds:

- **Hold-Day Noise**: On decision days where central banks leave rates unchanged (holds), daily sovereign yield changes exhibit variance ratios indistinguishable from non-meeting noise ($VR \approx 1.0$, $p > 0.30$ for BoE, RBA, Fed, and ECB). Daily sovereign bond markets do not register meaningful surprise signals on hold days, which is why Tier 2 holds are excluded from primary analysis.
- **Rate-Change Excess Volatility**: On rate-change days (hikes and cuts), sovereign yield changes display strong, statistically significant policy signal ($VR = 3.8\text{ to }7.2$, $p < 0.001$).
- **Bank of Canada Proxy Weakness**: While BoC 2-year sovereign yields exhibit significant excess volatility on meeting days overall ($VR = 3.93$), under lag-shift testing the variance ratio drops, indicating that Canadian daily bond yields contain a higher noise-to-signal ratio than UK Gilts or Australian Commonwealth bonds.

---

## 5. Announcement Timing Evidence Gaps

While current release schedules are well-documented and verified by official central bank pages, historical timing conventions suffer from archive gaps:

- **Bank of England**: The official 12:00 noon Thursday announcement convention is formally verified on-disk for the 2016–present period. Prior to 2016, releases occurred on Thursday noon but lack machine-readable official calendar documentation; they are conservatively classified as `time_quality = "approximate"` and `analysis_ready_timing = 0`.
- **Bank of Canada & Central Bank of Russia**: FAD schedules (10:00 ET for BoC; 13:30 Moscow time for CBR) are verified from 2013 onward. Decisions prior to 2013 lack timestamp evidence and are assigned `analysis_ready_timing = 0`.
- Researchers requiring strict timestamp provenance should restrict samples to `analysis_ready_timing == 1`.

---

## 6. Raw Data Provenance & Manifest Break

During Phase E and subsequent validation audits:
- **Reproducibility Break**: Re-downloading and re-registering ~454 raw files (due to Windows CRLF line endings, PowerShell UTF-8 BOM injection, and live HTML re-downloads) created a break in bitwise SHA-256 tracking relative to the original Phase A manifest.
- **Mitigation & Verification**: An exhaustive reconciliation (`outputs/raw_hash_audit.csv` and `outputs/v1_vs_v2_diff.csv`) verified zero substantive divergence in shared price levels, equity returns, statement texts, or policy decision classifications. All on-disk files match `data/raw/MANIFEST.csv`.

---

## 7. Proprietary & Licensed Data Redistribution

- **Redistribution Prohibition**: Daily equity closing price levels (`level_local`) and raw provider files are subject to exchange and provider redistribution terms.
- **Handling**: Raw equity index files and level price series cannot be distributed in public repositories. The public release subset includes only open-source code, documentation, derived cumulative log returns, and standardized monetary shocks.

---

## 8. Central Bank Statement Hand-Coding Status

- **Unlabeled Benchmark Set**: The hand-label validation sample (`data/final/hand_label_sample_with_text.csv`, 181 statements across Fed, ECB, BoJ, and RBI) contains intentionally blank label columns.
- **Coding Kit Provided**: A detailed labelling guide (`docs/labelling_guide.md`) and inter-annotator agreement evaluation script (`src/label_agreement.py`) are provided, but human consensus scores have not yet been produced.

---

## 9. Overlapping Event Windows at Extended Horizons

Monetary policy decisions across the 12 regimes frequently occur in close proximity:
- **Contamination Share**: Overlap shares are 36.0% at 1 day (`overlap_1d`), 69.1% at 3 days, 84.6% at 5 days, 99.7% at 20 days, and 99.96% at 60 days.
- **Causal Attribution**: At horizons beyond 5 trading days ($clr_{20}$, $clr_{60}$), equity price changes almost certainly reflect the compounding effects of multiple global central bank actions. Researchers estimating medium-to-long horizon cumulative returns must control for `overlap_count_Wd` or restrict analysis to non-overlapping windows.

---

## 10. MoTrans-15 v2.0 Addendum & Specific Methodological Limits

### 10.1 Central Bank of Russia (CBR) Decision Dates & Lack of Holds
- **Correction from Effective Dates to Announcement Dates**: An audit against the official Bank of Russia calendar (`data/raw/timing_sources/cbr_cal_mp.html`) revealed that 38 out of 41 effective Key Rate decisions (2013–2022) were recorded on Monday effective dates. In v2.0, all 38 decisions have been re-dated to the official Friday Board meeting dates, re-aligning event windows and 1Y yield proxy surprises. The original BIS dates are preserved in `bis_effective_date`.
- **Complete Absence of Scheduled Holds**: CBR has **zero scheduled holds** recorded in the catalog. Only active rate changes (hikes and cuts) are published in the underlying BIS series.

### 10.2 Same-Pattern Audit Across All Regimes
- **G6 Central Banks (Fed, ECB, BoE, BoC, RBA, BoJ)**: 100% of decision dates in 2010+ correspond to official committee/board decision announcement dates. Zero decisions are Monday-after-meeting lags.
- **Emerging Market Regimes (BoK, PBoC)**:
  - Bank of Korea (BoK) and People's Bank of China (PBoC) lack automated official calendar readers; their dates reflect BIS effective dates. Scheduled rate holds are not recorded. Both regimes are marked with `shock_primary = 0` and `analysis_ok = 0`.
  - Banco Central do Brasil (BCB), Banco de México (Banxico), and Reserve Bank of India (RBI) are dated by official committee announcement schedules.

### 10.3 Single-Source Equity Prices & External Verification
- **S&P 500**: Verified against FRED `SP500` with 99.84% of daily returns agreeing within 1 bp (maximum difference 1.2 bp due to rounding).
- **Nikkei 225**: Matches FRED `NIKKEI225` to cents when accounting for FRED's 1-day US calendar reporting lag.
- **Single-Source Series**: The remaining 36 equity series have no secondary provider on disk and remain strictly classified as single-source Yahoo Finance data (`price_source_verified = 0`).

### 10.4 Macro Controls Vintage Contamination & Statistics Canada CPI Status
- **Industrial Production Revision Contamination**: OECD STES Industrial Production data represents latest revised historical series rather than real-time first releases. Because IP undergoes substantial revisions up to 12 months after reference periods, it introduces revision lookahead contamination and is **excluded from all default v2 tables** (`analysis_tier1_2010plus.parquet`, `analysis_tier2_primary_2010plus.parquet`), retained strictly in a labeled sensitivity table (`sensitivity_macro_revision_2010plus.parquet`).
- **Statistics Canada (StatCan) CPI Unverified**: Agency calendar pages for BLS (US), Eurostat (EA), ONS (GB), ABS (AU), and SBJ (JP) were downloaded and verified in `data/raw/cpi_calendars/`. Statistics Canada returned HTTP 503 (anti-bot protection); Canadian CPI release dates remain graded **Unverified (Grade C)**.

### 10.5 Tradeable ETF Proxy Tracking Divergence
Five tradeable ETF proxies exhibit significant annualized tracking error relative to cash benchmark indices due to expense ratios, dividend drag, and localized component weighting:
- `ea_emu_smallcap_etf` vs `de_mdax`: Tracking Error = 9.28% ($r = 0.8673$)
- `de_stoxx_banks_etf` vs `de_dax_banks`: Tracking Error = 17.70% ($r = 0.8583$)
- `jp_topix_banks_etf` vs `jp_nikkei225`: Tracking Error = 20.52% ($r = 0.6676$)
- `kr_banks_etf` vs `kr_kospi`: Tracking Error = 22.44% ($r = 0.5546$)
- `jp_mothers_etf` vs `jp_nikkei225`: Tracking Error = 31.65% ($r = 0.5145$)
All 5 series are explicitly flagged with `proxy_type = 'etf_proxy'`.

### 10.6 Bank of Japan Operating Target vs Facility Spread
On 2026-09-18, the BoJ Policy Board raised the uncollateralized overnight call rate target by +25 bp to around 1.25% (verified from official PDF statement). BIS series `WS_CBPOL/D.JP` logged the complementary lending facility ceiling rate (1.00%), creating a crosscheck spread difference. The dataset correctly records the official 1.25% operating target.

