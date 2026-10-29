# MoTrans-15 v2.1 Data Quality Scorecard

## 1. Table Consistency and Verification Grades

Each v2.1 table is graded on two distinct dimensions:
- **Internal Consistency**: Mathematical precision, alignment causality, embargo isolation, absence of lookahead leakage.
- **External Verification**: Independent verification against official primary central bank sources, official timing calendars, and second-source price/shock series.

| Table | Observations | Decisions | Internal Consistency | External Verification | Notes & Verification Scope |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `analysis_tier1.parquet` | 9,350 | 253 | **A+ (100%)** | **A (High)** | Fed (Bauer-Swanson MPS) and ECB (EA-MPD OIS 1Y). High-frequency intraday surprises with proven timestamps. |
| `analysis_tier2_primary.parquet` | 4,851 | 127 | **A+ (100%)** | **B+ (Substantial)** | Clean rate-change decisions for BoE, BoC, RBA, CBR, and Fed/ECB fallbacks. 1-day sovereign yield proxy shocks. |
| `secondary_holds.parquet` | 12,454 | 334 | **A+ (100%)** | **B+ (Substantial)** | Scheduled hold decisions with proxy yield shocks. Kept for sensitivity analysis. |
| `panel.parquet` | 148,869 | — | **A+ (100%)** | **B (Vendor Base)** | 38 international equity series (33 cash indices, 5 sector/size ETFs) with daily log returns. |
| `sensitivity_macro_revision.parquet` | 14,201 | 380 | **A+ (100%)** | **B (Point-in-Time)** | Analysis decisions with real-time Industrial Production (IP) revision controls attached. |
| `excluded_rows.parquet` | 25,473 | 1,024 | **A+ (100%)** | **Traceable** | Quarantined rows (`policy_verified == 0`, `timing_unverified`, `timing_ambiguous`, `moex_halt`, `embargo_dropped`). |
| `post_window_2026.parquet` | 2,280 | 60 | **A+ (100%)** | **Quarantined** | 2026 post-window observations locked from train, validation, and test splits. |

---

## 2. Exhaustive List of Items Remaining Unverified

In accordance with strict research integrity rules, the following components remain unverified or rely on single-source vendor feeds in v2.1:

1. **Single-Source Equity Price Feeds**:
   - Only **S&P 500** (`us_sp500`) and **Nikkei 225** (`jp_nikkei225`) are externally verified against FRED second-source series (`price_source_verified = 1`).
   - The remaining 36 indices (including FTSE 100, DAX 40, CAC 40, TSX 60, ASX 200, IMOEX, Ibovespa, IPC, Nifty 50, KOSPI 200, CSI 300) rely entirely on primary vendor feeds (`price_source_verified = 0`).
2. **Statistics Canada CPI Release Calendar**:
   - Canadian CPI release dates prior to 2017 rely on standard third-Friday conventions rather than scraped StatCan web archives.
3. **Emerging Market Announcement Timestamps**:
   - **Banco Central do Brasil (BCB / Copom)**: Exact announcement timestamps are unarchived; announcements are imputed at 18:30 BRT (`timing_verified_level = 'none'`). All BCB rows are disqualified (`analysis_ok = 0`).
   - **Banco de México (Banxico)**: Historical statement releases prior to 2018 rely on convention (`timing_verified_level = 'none'`).
   - **Reserve Bank of India (RBI)**: Post-meeting policy statements rely on standard press conference time blocks (`timing_verified_level = 'none'`).
4. **Bank of England Pre-2016 MPC Timing**:
   - BoE announcement timing for 2010–2015 is verified at the **convention level** (strict Thursday 12:00 noon GMT protocol) rather than individual press release web scrape timestamps (`timing_verified_level = 'convention'`).
5. **Industrial Production (IP) Vintage Revisions**:
   - IP macro controls reflect latest available historical time series and first-available vintage indicators rather than complete real-time point-in-time vintage triangles across all 12 economies (`macro_vintage_verified = 0`).
6. **Hand Labels Not Completed**:
   - Manual statement qualitative text classifications and narrative hand labels remain in draft status and have not undergone double-blind expert replication (`hand_labels_completed = 0`).
