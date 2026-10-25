# Data Quality Scorecard — MoTrans-15 v2.0 (Phase V1 Addendum)

**Status**: Exploratory & Forecasting Dataset Verification  
**Evaluation Scope**: Narrowed Phase V1 (Fed, ECB, BoE, BoC, RBA, CBR pre-2022, BoJ as sensitivity)  
**Parent Release**: `v1.0-data-freeze` (Confirmatory test permanently preserved)  
**Verification Date**: 2026-10-25  

---

## 1. Executive Summary Table

All metrics generated directly by committed scripts and saved in [`outputs/v2/verification_summary.csv`](file:///c:/Users/HP/OneDrive/المستندات/Projects/MoTrans/outputs/v2/verification_summary.csv):

| Check Family | Check Type | Entities Tested | N Tested | N Failed | Failure Rate | Internal Consistency | External Verification | Verification Assessment |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **A. Index Prices** | external | 38 Index Series (2010+) | 10,795 | 0 | 0.00% | **Grade A** | **Grade C** | Internal returns match prices exactly. External second-source: SP500 matches FRED within 1.2 bp; Nikkei 225 fails unshifted calendar comparison due to 1-day US reporting lag on FRED; 36 series remain single-source Yahoo. |
| **B. Policy Decisions** | external | 6 Regimes + BoJ Sensitivity | 993 | 30 | 3.02% | **Grade A** | **Grade B** | 41 decisions in 2026 audited against central bank official releases. RBA 2026-09-29 fixed to hike +25 bp to 4.60% (effective 30 Sep 2026) per official Media Release 2026-27. CBR audited against official calendar: 38/41 effective decisions logged on Monday effective dates vs Friday Board meetings; CBR has no scheduled holds. |
| **C. Shocks & Yields** | replication | Fed, ECB, Tier 2 Proxies, 6 Yields | 1,979 | 0 | 0.00% | **Grade A** |  | Replication: Standardized Fed and ECB shocks match raw files to machine epsilon (<1e-15); 1,117 yield proxies exact match. External verification left blank per user audit (benchmarks replicated dataset values). |
| **D. Event Returns** | replication | 9,732 Tier 1 + 2,000 Random Events | 58,638 | 7 | 0.0119% | **Grade A** | **Grade B** | Replication: 99.99% exact match across 58,638 return calculations (7 halt-spanning exceptions on MOEX in Feb 2022). External: 500 sampled events show 0 date alignment mismatches using independent exchange calendars. |
| **E. Announcement Timing** | external | 100 Official Events across 5 Regimes | 100 | 0 | 0.00% | **Grade A** | **Grade C** | 100 events verified across 10 convention periods against official page headers and release schedules. All unverified events stay `timing_verified = 0`. |
| **F. Macro Controls** | external | 144 Monthly CPI Releases (6 Countries) | 144 | 0 | 0.00% | **Grade A** | **Grade C** | 5 official agency calendars saved in data/raw (BLS, Eurostat, ONS, ABS, SBJ); StatCan unverified due to HTTP 503. `ind_prod` flagged `revised_series = 1` and excluded from default v2 control set. |

---

## 2. Table-by-Table Data Quality Grades

### Table 1: `policy_decisions.csv`
- **Internal Consistency**: **Grade A** — Target rate levels and changes are internally consistent with BIS CBPOL series across 993 decisions. Fed midpoint convention (+0.125%) and ECB DFR/MRO spread changes resolved.
- **External Verification**: **Grade B** — Audited against official central bank release pages (`fed_fomc_calendars_2026.html`, `ecb_key_rates_2026.html`, `boe_mpc_dates_2026.html`, `boc_key_rates_2026.html`, `boj_decisions_2026.html`, `rba_cash_rate_2026.html`, `cbr_cal_mp.html`):
  - **RBA 2026-09-29 Discrepancy**: Dataset logged `hold` at 4.35%. Official RBA Media Release 2026-27 explicitly confirmed a **hike of +25 bp to 4.60%** (effective 30 Sep 2026): *"At its meeting today, the Board decided to increase the cash rate target by 25 basis points to 4.60 per cent."*
  - **CBR Date Lag**: Dataset logged Monday BIS effective dates rather than Friday Board decision announcements.
  - **BoJ Operating Target**: BIS series tracks the Complementary Lending Facility rate rather than uncollateralized call target.

### Table 2: `shocks.parquet`
- **Internal Consistency**: **Grade A** — Standardized shocks recomputed from raw Excel spreadsheets (`frbsf_monetary_policy_surprises.xlsx`, `ecb_ea_mpd_dataset.xlsx`) replicate to machine epsilon ($< 10^{-15}$). All 1,117 Tier 2 yield proxy changes match `shock_proxy_raw`.
- **External Verification**: *Blank (Internal Only)* — Benchmark values were previously taken from internal dataset replication; per user audit, external verification is left blank and graded internal replication only.

### Table 3: `panel_daily.parquet`
- **Internal Consistency**: **Grade A** — Arithmetic daily log returns recomputed from price levels match `ret_local` across 100% of tested days (< 1 bp).
- **External Verification**: **Grade C** — Automated external downloaders (Stooq) were blocked by Cloudflare anti-bot challenges and no manual Stooq CSVs were placed. FRED second-sources:
  - S&P 500 (`^GSPC`): Matches FRED `SP500` within 1.2 bp max return difference across 2,510 days.
  - Nikkei 225 (`^N225`): Fails unshifted calendar matching (99.6% > 1 bp) because FRED logs Tokyo closes with a 1-day US reporting lag. Matches to cents when shifted T+1.
  - Remaining 36 series have no secondary source and remain strictly classified as `single-source`.

### Table 4: `events.parquet`
- **Internal Consistency**: **Grade A** — Recomputed cumulative log returns ($clr_1, clr_3, clr_5, clr_{20}, clr_{60}$) across 11,732 events achieved 99.99% exact match (58,631 / 58,638). Discrepancies strictly isolated to MOEX February 2022 halt-spanning periods.
- **External Verification**: **Grade B** — Date alignment audit recomputed baseline and reaction sessions for 500 randomly sampled events using the independent `exchange_calendars` library, confirming 0 date alignment mismatches (100% agreement).

### Table 5: Announcement Timing & Controls
- **Announcement Timing**: **Internal: Grade A | External: Grade C** — 100 events (10 per convention period across Fed, ECB, BoE, BoC, RBA) verified against saved official page headers. All unverified events remain `timing_verified = 0`.
- **Macro Controls**: **Internal: Grade A | External: Grade C** — 5 agency calendars saved in data/raw (BLS, Eurostat, ONS, ABS, SBJ); StatCan unverified due to HTTP 503. Zero lookahead bias verified across 144 CPI releases. Industrial Production flagged `revised_series = 1` due to OECD STES historical revisions and excluded from default v2 controls.
