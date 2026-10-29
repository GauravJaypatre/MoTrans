# MoTrans-15 v2.1.1 Release Package Limitations

In accordance with open research integrity standards, this document discloses all known package constraints, data limitations, and unverified components:

1. **Restricted Access Designation**:
   - Because financial market return series are derived from commercial index feeds without signed redistribution clearance (`LICENCE_CLEARANCE.txt` not present), this dataset is designated **Restricted Access** on Zenodo (accessible upon academic request).

2. **Single-Source Equity Price Feeds**:
   - Only S&P 500 (`us_sp500`) and Nikkei 225 (`jp_nikkei225`) have been cross-verified against independent FRED data (`price_source_verified = 1`).
   - The remaining 36 indices rely on primary vendor feeds (`price_source_verified = 0`).

3. **Emerging Market Announcement Timestamps**:
   - Banco Central do Brasil (BCB), Banco de México (Banxico), Reserve Bank of India (RBI), and Bank of Korea (BoK) lack official scraped minute-level release archives. These decisions are disqualified from the primary evaluation sample (`analysis_ok = 0`).

4. **Bank of England Pre-2016 MPC Timing**:
   - BoE announcement timing prior to 2016-01-01 is verified at convention level (strict Thursday 12:00 noon GMT protocol) rather than minute-level press release scrapes (`timing_verified_level = 'convention'`).

5. **Macroeconomic Vintage Revisions**:
   - Industrial Production series reflect historical time series with first-available vintage indicators rather than real-time point-in-time vintage triangles across all 12 economies (`macro_vintage_verified = 0`).

6. **Qualitative Hand Labels Excluded**:
   - Narrative statement qualitative hand classifications have not undergone double-blind expert replication and are excluded from this release.

7. **Zero Rate Hikes in Out-of-Sample Test Split**:
   - The 2024–2025 strictly locked test split contains exactly **0 interest rate hikes**, reflecting the empirical reality of the global post-inflation monetary easing cycle. Models must not rely on rate hike observations during out-of-sample evaluation.

8. **Standalone Code Package Execution**:
   - `data/raw` cannot be redistributed. Running the raw pipeline from `code/` requires fetching raw files directly from primary sources.

9. **Full Test Suite Execution & Path Scope (Step 5f)**:
   - **Repository Root Run (pytest)**: **177 passed in 26.45s** (100% pass rate). All smoke tests, v1 regression tests, v2 alignment audits, timing tests, and v2.1 table tests pass without warning or error.
   - **Isolated Package Run (cd zenodo_release/code; pytest)**: **28 passed, 114 skipped, 35 failed in 8.17s**.
   - **Root Cause of Isolated Failures**:
     - 114 skipped tests are collector/raw tests decorated with pytest.mark.skipif(not RAW.exists()), which correctly skip when raw vendor data is not present.
     - 35 failed tests check for legacy and unredacted build artifacts (data/final/, data/v2/, outputs/v2/, panel.parquet with proprietary level_local, excluded_rows.parquet, and post_window_2026.parquet) which are intentionally excluded from the public Zenodo release package per distribution licensing rules (Step 2c).
     - No tests were modified (edited_tests = []) in order to preserve bit-for-bit code parity with the certified 2.1.1-train-test-ready tag.
