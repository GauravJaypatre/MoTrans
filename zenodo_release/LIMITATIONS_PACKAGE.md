# MoTrans-15 v2.1.1 Release Package Limitations

In accordance with open research integrity standards, this document discloses all known package constraints, data limitations, and unverified components:

1. **Single-Source Equity Price Feeds**:
   - Only S&P 500 (`us_sp500`) and Nikkei 225 (`jp_nikkei225`) have been cross-verified against independent FRED data (`price_source_verified = 1`).
   - The remaining 36 indices rely on primary vendor feeds (`price_source_verified = 0`).

2. **Emerging Market Announcement Timestamps**:
   - Banco Central do Brasil (BCB), Banco de México (Banxico), Reserve Bank of India (RBI), and Bank of Korea (BoK) lack official scraped minute-level release archives. These decisions are disqualified from the primary evaluation sample (`analysis_ok = 0`). Brazil, Mexico, India, Korea and China have no usable decisions in this version.

3. **Bank of England Pre-2016 MPC Timing**:
   - BoE announcement timing prior to 2016-01-01 is verified at convention level (strict Thursday 12:00 noon GMT protocol) rather than minute-level press release scrapes (`timing_verified_level = 'convention'`).

4. **Statistics Canada CPI Calendar**:
   - Statistics Canada historical CPI release dates and times follow agency release calendar schedules rather than minute-level announcement timestamps.

5. **Macroeconomic Industrial-Production Vintage Revisions**:
   - Industrial Production series reflect historical time series with first-available vintage indicators rather than real-time point-in-time vintage triangles across all economies (`macro_vintage_verified = 0`).

6. **Qualitative Hand Labels Not Completed**:
   - Narrative statement qualitative hand classifications have not undergone double-blind expert replication and are excluded from this release (see `docs/labelling_guide.md`).

7. **2026 Decisions Verified Only Internally**:
   - 2026 policy decisions and market data are quarantined in `post_window_2026.parquet` and verified only internally; they are strictly excluded from the release tables to prevent temporal contamination.

8. **Test Split Properties (Zero Hikes and Zero Fed Tier 1 Decisions)**:
   - The 2024–2025 strictly locked test split contains exactly **0 interest rate hikes**, reflecting the easing cycle among the included central banks.
   - The test split contains **0 Fed Tier 1 decisions** because the Bauer-Swanson high-frequency surprise series ends in December 2023 (2024–2025 Fed decisions rely on 1-day sovereign yield proxy surprises under Tier 2).

9. **Skipped Package Tests (149 of 177)**:
   - In the isolated release package (`code/`), 149 of 177 tests are auto-skipped via `conftest.py` because proprietary vendor raw feeds (`data/raw/`), legacy tables (`data/v2/`), unredacted price levels (`level_local`), and quarantined 2026 data cannot be redistributed. Running all 177 tests requires restoring primary raw feeds.
