# MoTrans-15: Comprehensive Dataset Limitations & Methodological Boundaries

**Date**: 2026-11-04  
**Status**: ACTIVE WORKING DRAFT  
**Scope**: MoTrans-15 v2.1.1 Dataset and Econometric Architecture  
**Target Publication**: *Scientific Data* (Descriptor) / *Nature Communications* (Article)

---

## 1. Overview

This document presents an exhaustive enumeration of all structural, empirical, and econometric limitations governing the MoTrans-15 dataset. These limitations are derived directly from committed source tables, cryptographic freeze records, and empirical diagnostic tests. Researchers utilizing this dataset must report these boundaries explicitly.

---

## 2. Eleven Fundamental Empirical Limitations

### Limitation 1: Emerging Market Timing Provenance (`timing_verified_level = "none"`)
- **Empirical Reality**: Central bank announcement times for Banco Central do Brasil (BCB), Banco de Mexico (Banxico), and the Reserve Bank of India (RBI) could not be independently verified to the minute against public machine-readable feeds across 2000–2025.
- **Protocol Action**: All BCB, Banxico, and RBI policy decisions are permanently quarantined into `data/v2_1/excluded_rows.parquet` (344 decisions, 12,722 event rows) and excluded from all primary causal estimation tables.
- **Boundary**: Causal inferences regarding monetary transmission in emerging markets cannot be drawn from this dataset.

### Limitation 2: Bank of Japan ZIRP/YCC Yield Suppression
- **Empirical Reality**: Prolonged Zero Interest Rate Policy (ZIRP) and Yield Curve Control (YCC) pegged Japanese Government Bond (JGB) yields for over two decades. The training standard deviation of the BoJ daily 1-year yield change is only 1.1357 bp (compared to 4.4806 bp for Germany and 5.7533 bp for the US).
- **Protocol Action**: BoJ decisions are quarantined (`shock_primary = 0`) to prevent near-zero denominators from generating pathological leveraged outliers. BoJ is retained exclusively under `shock_primary_rescaled` using a peer Developed Market benchmark scale.
- **Boundary**: Japan must not be pooled into standard linear panels without explicitly addressing yield curve peg distortions.

### Limitation 3: Federal Reserve High-Frequency Truncation (December 2023)
- **Empirical Reality**: The official FRBSF Bauer-Swanson high-frequency futures surprise series terminates at **December 13, 2023** (`fed_2023-12-13`). High-frequency intraday monetary surprises do not exist for the Fed in 2024–2025.
- **Protocol Action**: Post-2023 Fed meetings fall back to daily sovereign yield proxies (`shock_measure_type = "yield_proxy"`), routing them into Tier 2 (`analysis_tier2_primary.parquet` for rate cuts, `secondary_holds.parquet` for holds).
- **Boundary**: Tier 1 contains **0 Federal Reserve decisions in the 2024–2025 test split**. Any Tier 1 evaluation of 2024–2025 evaluates exclusively European Central Bank monetary policy.

### Limitation 4: Bank of England Pre-2016 Approximate Timing Convention
- **Empirical Reality**: Bank of England decisions prior to 2016-01-01 are assigned `time_quality = "approximate"` and `timing_verified_level = "convention"`. Official Bank of England documentation confirms the strict 12:00 noon Thursday announcement rule on-disk only for the 2016–present MPC framework.
- **Protocol Action**: In `analysis_tier2_primary`, all BoE decisions occurred post-2016 (rate cut on 2016-08-04 was the first action in the 2010+ window). Pre-2016 BoE hold decisions are quarantined in `secondary_holds.parquet`.
- **Boundary**: Pre-2016 BoE hold decisions must be evaluated with explicit timing sensitivity filters.

### Limitation 5: Low Signal-to-Noise of Secondary Hold Decisions ($VR \approx 1.0$)
- **Empirical Reality**: Empirical variance ratio diagnostics indicate that daily sovereign yield changes on scheduled rate hold meetings exhibit a variance ratio $VR \approx 1.0$ relative to non-meeting trading days. By contrast, rate change days exhibit massive excess volatility ($VR = 3.8 \text{ to } 7.2$).
- **Protocol Action**: Scheduled holds under Tier 2 are quarantined into `secondary_holds.parquet` and strictly barred from primary models (`shock_primary = 0, shock_secondary = 1`).
- **Boundary**: Yield changes on hold days are econometric noise and cannot serve as causal instruments without high-frequency intraday extraction.

### Limitation 6: Zero Interest Rate Hikes in Out-of-Sample Test Split (2024–2025)
- **Empirical Reality**: The held-out test split contains **0 interest rate hikes** across all included central banks (reflecting an easing cycle among the included central banks, with 28 cuts and 42 holds).
- **Protocol Action**: All out-of-sample evaluations must enforce the mandatory regime caveat:
  > *"Evaluated during an easing cycle among the included central banks (the Bank of Japan hiked in the same period) with zero interest rate hikes; cannot assess tightening transfer."*
- **Boundary**: Out-of-sample metrics evaluate accommodation transmission only; model performance during policy tightening remains unverified.

### Limitation 7: High Cross-Sectional Intracluster Correlation ($ICC \approx 0.15 - 0.25$)
- **Empirical Reality**: Because 38 international equity indices react simultaneously to each central bank announcement, responses share substantial common global factor exposure. Intracluster correlation ranges between 0.15 and 0.25.
- **Protocol Action**: Clustered standard errors at the `event_id` level and two-way clustering (event and index) are mandatory. Effective independent sample size is reduced from $N = 1,786$ to $N_{\text{eff}} \approx 120 - 180$.
- **Boundary**: Unclustered standard errors or naive OLS inference severely overestimate statistical precision and are methodologically invalid.

### Limitation 8: Substantial Background Noise in Sovereign Yield Proxies (67% Non-HFI Noise)
- **Empirical Reality**: On 413 overlapping Fed and ECB decisions where both high-frequency surprises (`hf_ois`) and daily yield proxies (`yield_proxy`) exist, the Pearson correlation is $r = 0.5749$ ($R^2 = 0.3305$).
- **Protocol Action**: Daily yield proxies contain approximately 67% non-HFI background noise (macro data releases, European/Asian trading, background drift). Tier 2 models must never be pooled with Tier 1 without explicit tier indicators.
- **Boundary**: Tier 2 instruments are valid only as secondary transfer tests, not as primary causal benchmarks.

### Limitation 9: Intellectual Property and Restricted Access Terms
- **Empirical Reality**: Historical daily closing index levels (`level_local`) are proprietary commercial assets governed by exchange licensing agreements (S&P DJI, STOXX, FTSE Russell, Nikkei Inc., B3).
- **Protocol Action**: All raw price levels are stripped from the public release. The repository provides standardized log returns (`clr_1` through `clr_60`) and residual return series in `panel_returns_only.parquet`.
- **Boundary**: Price levels cannot be redistributed openly. Access to derived return tables is restricted to approved non-commercial academic researchers pending formal vendor clearance.

### Limitation 10: Test Split Partitioning — Sample A ($N = 70$) vs. Sample B ($N = 56$ Pristine)
- **Empirical Reality**: In the 2024–2025 test split, 14 of the 70 policy decisions had their return outcomes computed in the pre-registered v1 blind test (`run_v1_blind_test.py`). These 14 decisions are exclusively European Central Bank announcements evaluated under Tier 1 high-frequency OIS surprises.
- **Protocol Action**: Out-of-sample benchmark performance must be reported separately across two partitions:
  - **Sample A (Full Test Set, $N = 70$ decisions, 2,590 event rows)**: The complete chronological evaluation window (14 ECB Tier 1 decisions, 20 Tier 2 Primary rate cuts, 36 Secondary holds).
  - **Sample B (Pristine Test Set, $N = 56$ decisions, 2,072 event rows)**: Pure unblinded sample containing exclusively decisions that were never in the v1 blind test.
- **Critical Methodological Boundary**: The 14 excluded ECB decisions represent the **ONLY Tier 1 high-frequency identification decisions in the entire 2024–2025 test window**. Consequently, all 56 pristine decisions in Sample B are **Tier 2 daily sovereign yield proxy decisions**, and they feature **zero interest rate hikes** (20 rate cuts and 36 holds). Researchers cannot evaluate clean high-frequency surprises or monetary tightening on the pristine unseen test split.

### Limitation 11: Pre-Announcement Morning Trading Contamination in In-Session Windows (21.08%)
- **Empirical Reality**: In exactly **17,301 out of 82,054 decision-index pairs (21.08%)**, the central bank policy announcement occurs while the local equity exchange is open (`announce_in_session == 1`). Because the single-day reaction return is computed from previous close ($t-1$) to today's close ($t$), $\text{clr}_1 = \ln(P_t / P_{t-1})$ encapsulates between 15 minutes and 5.25 hours of pre-announcement morning trading (e.g., FOMC 14:00 ET releases vs US equity market open at 09:30 ET; ECB 14:15 CET releases vs European equity open at 09:00 CET).
- **Protocol Action**: Robustness audits documented in `docs/INTEGRITY_AUDIT.md` (Section 6.6) re-estimated all confirmatory horizons and headline specifications separately on the clean out-of-session subset (`announce_in_session == 0`, 64,753 pairs, 78.92%) and the in-session subset (`announce_in_session == 1`, 17,301 pairs, 21.08%).
- **Boundary**: In the immediate response window (`clr_1`), the shock coefficient is virtually identical between clean out-of-session decisions ($\beta = -0.000679$, $p_{\text{wild}} = 0.4224$) and in-session decisions ($\beta = -0.000609$, $p_{\text{wild}} = 0.6336$). Both subsets represent statistical nulls. While pre-announcement trading does not drive or mask the empirical null, fine-grained intraday tick/minute equity data are necessary to isolate high-frequency asset price discovery.
