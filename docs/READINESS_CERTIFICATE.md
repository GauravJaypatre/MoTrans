# MoTrans-15 Readiness Certificate & Final Hardening Audit (v2.2)

**Audit Date UTC**: 2026-11-09T23:55:00Z  
**Branch**: `v2-2-hardening`  
**Active HEAD Commit**: `a74fb1c` (`DECISION-046`)  
**Specification Freeze Tag**: `modeling-spec-frozen` (commit `e20bfc2`, `DECISION-044`)  
**Official Release Package Tag**: `v2.2.0-package` (commit `9a37000`, `DECISION-042`)  
**Approved Project Title**: *"MoTrans-15: Monetary policy surprises and equity-index responses for the largest economies, 2010-2025"*  
**Approved Econometric Scope**: Six central banks (Federal Reserve, European Central Bank, Bank of England, Bank of Canada, Reserve Bank of Australia, Bank of Russia; Bank of Japan routed to Tier 2 sensitivity). Panel covers index returns across 15 economies.

---

## 1. Release & Verification Gate Status Table

All gates executed via `scripts/run_v22_gates.py` and dedicated test harnesses.

| Gate ID | Gate Name | Verification Check / Hash | Status |
| :---: | :--- | :--- | :---: |
| **Gate 1** | Checksums Valid | All 101 files match `zenodo_release_v22/CHECKSUMS.sha256` | **PASS** |
| **Gate 2** | Frozen Data Hashes | Parquets match `docs/DATA_FREEZE_v2_2.md` bit-for-bit | **PASS** |
| **Gate 3** | Proprietary Levels Stripped | Zero `level_local` in `panel_returns_only.parquet` | **PASS** |
| **Gate 4** | Purged `shock_std` Trap | Zero full-sample `shock_std` in any release table | **PASS** |
| **Gate 5** | Single Source of Truth Alignment | `splits.csv` (718 decisions) matches folds and parquets | **PASS** |
| **Gate 6** | Citation Schema Validation | `cffconvert --validate` passes CFF schema 1.2.0 | **PASS** |
| **Gate 7** | Isolated Package Pytest | `zenodo_release_v22/code/`: 28 passed, 149 skipped, 0 failed | **PASS** |
| **Gate 8** | Full Repository Pytest | 220 passed in 43.03s | **PASS** |
| **Gate 9** | Documented Numbers vs CSVs | Total=718, Train=572, Val=76, Test=70, Pristine=56 | **PASS** |
| **Gate 10** | Held-Out Blinding Intact | `unlock_audit.log` = 16 lines prior to freeze; 17 after Phase 4 run | **PASS** |
| **Gate 11** | Deterministic Zip Package | `MoTrans15_v2.2.0_zenodo_package.zip` (8,635,256 bytes) valid | **PASS** |
| **Gate 12** | Zip SHA-256 Checksum Match | `b6a8dd241c4ae1082c10a52c0e65d2061633d9c933b027a9f5ff0ec7ff7696ed` | **PASS** |
| **Gate 13** | Spec Freeze Tag Recorded | `modeling-spec-frozen` created at `e20bfc2` (`DECISION-044`) | **PASS** |

---

## 2. Hardening Conditions Removed by Software

The hardening passes on branch `v2-2-hardening` systematically resolved every train/test integrity condition that software and econometric engineering can resolve:

1. **Purged the `shock_std` Trap**:
   - Replaced ambiguous, full-sample standardized `shock_std` with raw basis-point shocks (`shock_raw_bp`) and pre-period descriptive scales (`shock_descriptive_2019`).
   - Implemented `FoldSafeScaler` to fit scalers strictly on training folds, eliminating look-ahead scale leakage.
2. **Corrected Inferential Defaults**:
   - Eliminated unclustered OLS and single-index clustering (which produced severe Moulton intra-event standard error deflation).
   - Established restricted wild cluster bootstrap at `event_id` ($B=999$) as the primary inference metric.
   - Fixed two-way clustering degrees of freedom: $df = \min(G_{\text{event}}-1, G_{\text{index}}-1)$ instead of inflated asymptotic degrees of freedom.
3. **Eliminated Leaky Test Split Mixing**:
   - Established `data/v2_2/splits.csv` as the Single Source of Truth cataloging all 718 decisions (572 train, 76 validation, 70 test).
   - Separated the 14 ECB test decisions evaluated in the historical v1 blind test from the 56 pristine test decisions (`read_by_prior_analysis == 0`).
4. **Resolved Window Timing Ambiguity (`clr_1_clean`)**:
   - Created `clr_1_clean` defined strictly for out-of-session announcements (`announce_in_session == 0`), purging contamination from morning trading before announcements.
   - Formulated interaction check $\text{clr}_1 \sim \text{shock} \times \text{in\_session}$.
5. **Addressed Pre-Registration Deviation**:
   - Restored and estimated the pre-registered overlap-controlled model ($\text{clr}_W \sim \text{shock} + \text{overlap}_{W\text{d}}$) across all five horizons.
   - Classified the bivariate run as a disclosed deviation requiring author approval in `docs/DEVIATIONS_LOG.md`.
6. **Corrected Misleading Power Numbers**:
   - Diagnosed that the earlier 18.35 bp asymptotic pooled MDE was heavily compressed by regressor variance inflation from a single event (`cbr_2014-12-16`, policy rate hike `size_bp = 650.0`, sovereign proxy `shock_raw_bp = 499.0`, `shock_tier = 2`).
   - Recomputed and reworded headline MDE: **119.10 bp** as the *"conservative headline MDE after trimming the top 1% influential events"*, reported side by side with untrimmed asymptotic (18.35 bp) and wild bootstrap (20.03 bp) MDEs.
7. **Automated Guard Scanner & Allowlist**:
   - Audited all 65 Python files with `scripts/verify_no_unguarded_outcomes.py`. Zero unguarded outcome reads detected.
   - Historical allowlist strictly registered the single historical v1 test script in `docs/INTEGRITY_AUDIT.md`.
8. **Multiplicity Accounting Across Entire Ledger**:
   - Registered all 161 models in `outputs/modeling/ledger.csv`.
   - Recomputed Holm FWER and Benjamini-Hochberg FDR adjustments over wild cluster bootstrap p-values.

---

## 3. Conditions That Cannot Be Removed by Software

The following conditions reflect physical macroeconomic realities, data copyright law, or required human labor, and **cannot be resolved by software**:

1. **Zero Interest Rate Hikes in the Test Split**:
   - The 2024–2025 out-of-sample test window coincides with a global monetary easing and pause cycle across all included major central banks (Sample A: 58 holds, 12 cuts; Sample B: 46 holds, 10 cuts; strictly 0 rate hikes).
   - Software cannot generate monetary tightening in a period when central banks did not hike rates. Only physical calendar time or an alternative historical out-of-sample window can provide out-of-sample tightening shocks.
2. **Pristine Test Split (Sample B) is Tier 2 Only**:
   - The 56 pristine decisions consist entirely of Tier 2 daily sovereign yield proxies for the Bank of England, Bank of Canada, Reserve Bank of Australia, Bank of Russia, and Bank of Japan.
   - All Tier 1 high-frequency OIS/MPS shocks in the test split are ECB decisions that were evaluated during the v1 blind test. Expanding Tier 1 coverage requires external commercial high-frequency tick data.
3. **No 2026 High-Frequency Shocks**:
   - 2026 post-window rows are strictly quarantined in `data/v2_2/post_window_2026.parquet` with zero price outcome reads. Updating these series requires commercial vendor licenses.
4. **Constrained Statistical Power (High MDEs)**:
   - In clean Tier 1 intraday shocks, statistical power is inherently bounded by sample size (MDE $= 83.2$ bp to $101.3$ bp). In the test split, MDE is $345.2$ bp to $379.2$ bp.
   - The econometric design cannot statistically reject fine effect sizes ($< 25$ bp); null results must be interpreted in the context of these wide confidence intervals.
5. **Language Track Annotation Incomplete**:
   - 100 statement samples have been selected, randomized, and blinded in `data/annotation/annotator_1_sample.csv` and `annotator_2_sample.csv`.
   - Independent reading, scoring, and adjudication require human domain experts (`TODO-HUMAN`). Zero labels were fabricated.
6. **36 Financial Price Series from a Single Source**:
   - While S&P 500 and Nikkei 225 were verified against FRED second-source series, the remaining 36 price series rely on Yahoo Finance and require official vendor feeds (Bloomberg/LSEG) (`TODO-HUMAN`).
7. **Commercial Redistribution Restrictions**:
   - Benchmark equity index returns (S&P, STOXX, FTSE, Nikkei, TSX, ASX) are protected by intellectual property rights.
   - Commercial clearance has not been granted. The public repository must remain under restricted access on Zenodo (`TODO-HUMAN`).

---

## 4. Clear Verdict Lines

| Dimension | Readiness Verdict | Formal Explanation |
| :--- | :---: | :--- |
| **Train/Test Ready for Development** | **YES** | Cryptographically frozen, leakage-proof split architecture, hardened inferential defaults, zero unguarded outcome reads. |
| **Clean Out-of-Sample Test of Tightening Transfer** | **NO** | Test split contains **strictly zero interest rate hikes** (58 holds, 12 cuts). It serves strictly as a sanity check on easing and holds. |
| **Nature-Level Claim** | **NO** | Confirmatory empirical null, low statistical power, missing human statement annotations, single-source price series, missing commercial IP clearance. |

---

## 5. Prioritized Human Deliverable List (`TODO-HUMAN`)

To advance this project toward formal journal submission, human domain experts must execute the single next deliverable for each track:

| Priority | Track | Single Next Deliverable | Target Artifact |
| :---: | :--- | :--- | :--- |
| **1** | **Target Venue Selection** | Re-orient primary submission to ***Scientific Data*** (Descriptor). Position ***Nature Communications*** strictly as an exploratory stretch venue. Drop all claims for *Nature*. | `docs/MANUSCRIPT_FRAMING.md` |
| **2** | **Language Annotation** | Recruit two independent central bank macroeconomists to rate the 100 blinded policy statements in `data/annotation/annotator_1_sample.csv` and `annotator_2_sample.csv` using the 5-point rubric in `docs/LANGUAGE_PREANALYSIS_PLAN.md`. | `data/annotation/adjudication_log.csv` |
| **3** | **Second-Source Price Verification** | Pull official terminal price series from Bloomberg or LSEG Refinitiv for the 36 international equity indices cataloged in Section 4 of `docs/NATURE_READINESS.md` and execute `scripts/verify_prices_second_source.py`. | `outputs/verification/second_source_price_audit.csv` |
| **4** | **Commercial IP Permission** | Submit formal vendor permission requests (using template in `docs/OPEN_RELEASE_PLAN.md`) to S&P Global, Qontigo/STOXX, FTSE Russell, and Nikkei Inc. for open redistribution of derived daily percentage log returns. | `docs/OPEN_RELEASE_PLAN.md` |
| **5** | **Pre-Registration Formalization** | Obtain formal author sign-off acknowledging the overlap control deviation (`clr_W ~ shock + overlap_Wd` vs bivariate) in `docs/DEVIATIONS_LOG.md`. | `docs/DEVIATIONS_LOG.md` |
