# MoTrans-15: Research Integrity Audit & Blinding Verification

**Date**: 2026-11-05  
**Status**: ACTIVE / HARDENED  
**Commit Context**: Modeling Harness Final Hardening & v2.2 Preparation  
**Target Submission**: *Scientific Data* (Descriptor) / *Nature Communications* (Article)

---

## 1. Executive Summary

This audit assesses methodological integrity, sample blinding, and shock instrumentation across the transition from MoTrans-15 v1.0 to v2.1.1 and preparations for v2.2. 

Key Findings:
1. **Sample Overlap**: Of the 70 policy decisions designated as the held-out test split (2024–2025) in v2.1.1, exactly **14 decisions (20.0%)** had their return outcomes computed during the pre-registered v1 blind test (`run_v1_blind_test.py`). These 14 decisions are all European Central Bank (ECB) announcements under Tier 1.
2. **Pristine Out-of-Sample Split**: The remaining **56 decisions (80.0%)**—comprising all Federal Reserve, Bank of England, Bank of Canada, and Reserve Bank of Australia decisions in 2024–2025—have **never been loaded, unblinded, or evaluated** by any outcome model.
3. **Fed Shock Instrumentation**: Federal Reserve high-frequency surprises (Bauer-Swanson MPS) terminate in December 2023. Post-2023 Fed meetings rely on daily sovereign yield proxies (`yield_proxy`), which places them in Tier 2. Consequently, Tier 1 contains zero Fed decisions in 2024–2025.
4. **Mandatory Reporting Protocol**: Final test scoring (Phase 4) must report benchmark metrics separately for:
   - Full Test Split ($N = 70$ decisions)
   - Pristine Unseen Test Split ($N = 56$ decisions; 0% prior exposure)

---

## 2. Quantitative Sample Split Overlap Audit

### 2.1 Sample Partitioning Across Generations

| Dataset Version | Calendar Window | Split Designation | Role |
| :--- | :--- | :--- | :--- |
| **v1.0** | 2000-01-01 to 2019-12-31 | `train` | Exploratory & baseline estimation |
| **v1.0** | 2020-01-01 to 2021-12-31 | `crisis` | COVID-19 pandemic stress-test regime |
| **v1.0** | 2022-01-01 to 2025-10-30 | `blind_test` | Confirmatory pre-registered blind test (47 decisions) |
| **v2.1.1** | 2010-01-01 to 2021-12-31 | `train` | Cross-validation training folds (CV Folds 1–4) |
| **v2.1.1** | 2022-01-01 to 2023-12-31 | `validation` | Hyperparameter selection & validation |
| **v2.1.1** | 2024-01-01 to 2025-12-31 | `test` | Strictly held-out benchmark split (70 decisions) |
| **v2.1.1** | 2026-01-01+ | `post_window` | Quarantined future observation buffer |

### 2.2 Granular Breakdown of Overlap

The pre-registered v1 blind test evaluated 47 decisions from `data/final/analysis_tier1.parquet`:
- **16 Federal Reserve decisions** (2022-01-26 to 2023-12-13): All fall within the v2.1 `validation` window (2022–2023). **Zero overlap with v2.1 test split.**
- **16 ECB decisions** (2022-02-03 to 2023-12-14): All fall within the v2.1 `validation` window (2022–2023). **Zero overlap with v2.1 test split.**
- **14 ECB decisions** (2024-01-25 to 2025-09-11): Fall within the v2.1 `test` window. **These 14 decisions overlap.**
  The exact 14 decisions evaluated in the v1 blind test are: `ecb_2024-01-25`, `ecb_2024-03-07`, `ecb_2024-04-11`, `ecb_2024-06-06`, `ecb_2024-07-18`, `ecb_2024-09-12`, `ecb_2024-10-17`, `ecb_2024-12-12`, `ecb_2025-01-30`, `ecb_2025-03-06`, `ecb_2025-04-17`, `ecb_2025-06-05`, `ecb_2025-07-24`, `ecb_2025-09-11`.
- **1 ECB decision** (`ecb_2025-10-30`): Excluded from v2.1 test split due to the 60-day embargo requirement prior to the dataset end date (2025-12-31).

### 2.3 Comprehensive Decision Accounting in V2.1 Test Split

| Decision Table | Total Test Decisions | Decisions in v1 Blind Test | Pristine Test Decisions | Pristine Rows |
| :--- | :---: | :---: | :---: | :---: |
| `analysis_tier1` (ECB) | 14 | 14 (100.0%) | 0 (0.0%) | 0 |
| `analysis_tier2_primary` (Actions) | 20 | 0 (0.0%) | 20 (100.0%) | 740 |
| `secondary_holds` (Holds) | 36 | 0 (0.0%) | 36 (100.0%) | 1,332 |
| **Total Test Split** | **70** | **14 (20.0%)** | **56 (80.0%)** | **2,072** |

*Rows: 518 overlapping rows ($14 \times 37$ index series) vs 2,072 pristine rows ($56 \times 37$ index series).*

---

## 3. Federal Reserve Shock Coverage & Fallback Audit (A2)

### 3.1 Data Source Boundaries
- **Instrument**: High-Frequency Monetary Policy Surprise (`MPS`), defined as the 30-minute change in federal funds and Eurodollar/SOFR futures around FOMC releases (Bauer and Swanson, 2023).
- **Termination Date**: The official FRBSF Bauer-Swanson dataset terminates on **December 13, 2023** (`fed_2023-12-13`).
- **Post-2023 Fallback**: In `src/build_shocks.py`, Federal Reserve decisions in 2024 and 2025 have `shock_hf_raw = NaN`. The pipeline assigns the daily 1-year US Treasury yield change as `shock_proxy_raw`, with `shock_grade = "B"` and `shock_measure_type = "yield_proxy"`.

### 3.2 Tier Routing Implications
- By pre-registered design (`docs/preregistration.md` Section 3), Tier 1 requires `shock_tier == 1` (`shock_grade == "A"` and `shock_measure_type == "hf_ois"`).
- Consequently, all post-2023 Fed meetings were routed out of Tier 1 into Tier 2:
  - 4 rate cuts (`fed_2024-09-18`, `fed_2024-11-07`, `fed_2024-12-18`, `fed_2025-09-17`) were routed to `analysis_tier2_primary.parquet`.
  - 10 rate holds were routed to `secondary_holds.parquet`.
- **Finding**: Tier 1 in v2.1 contains **0 Federal Reserve decisions in 2024–2025**. Any Tier 1 evaluation of 2024–2025 evaluates exclusively ECB monetary policy.

---

## 4. Leakage Prevention Architecture in V2.1 & V2.2

To ensure that no model exploration or hyperparameter search accesses test split outcomes:
1. **Physical Column Guard**: `src/modeling/data_loader.py` physically strips `clr_1` through `clr_60` whenever `split="test"` or `split="all"` is loaded, unless `UNLOCK_TEST=1` is explicitly defined in the environment AND `allow_test_outcomes=True` is passed as a function argument.
2. **Access Trapping**: Unauthorized attempts to load test outcomes raise `PermissionError` and append a timestamped audit entry with git commit hash to `outputs/v2_1/unlock_audit.log`.
3. **Audit Log Verification**: Prior to Phase 4 test scoring, `unlock_audit.log` must contain exactly 16 historical lines (all dating to packaging and verification). Zero unauthorized or exploratory accesses have occurred.
4. **Automated Static Codebase Scan**: `tests/test_model_guard_integrity.py` and `scripts/verify_no_unguarded_outcomes.py` recursively audit all Python files across `scripts/` and `src/` to guarantee zero direct unblinded reads of held-out tables or hardcoded unlock flags.

---

## 5. Protocol for Phase 4 Scoring

When Phase 4 test scoring is approved:
1. `scripts/run_test_scoring.py` must verify that git HEAD is tagged `modeling-spec-frozen`.
2. The script must report all performance statistics across two distinct samples:
   - **Sample A (Full Test Set, $N = 70$)**: Standard comprehensive benchmark.
   - **Sample B (Pristine Test Set, $N = 56$)**: Pure unblinded sample containing exclusively decisions that were never in the v1 blind test.
3. Both sets must be presented in parallel with full multiplicity corrections and the mandatory regime caveat:
   > *"Evaluated during an easing cycle among the included central banks (the Bank of Japan hiked in the same period) with zero interest rate hikes."*

---

## 6. Addendum: Quantitative Audits, Provenance Checks & Reaction Timing

### 6.1 Audit of "413 Common Fed/ECB Decisions" (Task 3a)
A quantitative verification was conducted across `data/final/shocks.parquet` and `data/final/analysis_tier1.parquet` to resolve the precise distinction between policy decisions (unique `event_id`) and panel event rows:
1. **Decisions with Dual Instruments**: In `data/final/shocks.parquet`, exactly **413 decisions** contain non-null values for both the high-frequency shock (`shock_hf_raw`) and the daily sovereign yield proxy (`shock_proxy_raw`):
   - **Federal Reserve**: 202 decisions (spanning 2000 to 2023; 8–11 decisions/year; terminates December 2023 due to the end of the Bauer-Swanson series).
   - **European Central Bank**: 211 decisions (spanning 2004 to 2025; 2004: 3 decisions, 2005–2014: 12–13 decisions/year, 2015–2024: 8 decisions/year, 2025: 7 decisions).
   - **Total**: $202 + 211 = 413$ unique decisions. On `shocks.parquet`, each row represents exactly one decision (413 rows = 413 decisions).
   - **Correlation**: On these 413 decisions, the Pearson correlation between intraday HFI and daily yield changes is $r = 0.5749$ ($R^2 = 0.3305$), establishing that daily yield changes contain ~67% non-HFI background market noise.

2. **Decisions by Year and Central Bank (Dual-Instrument Sample)**:
   ```
   Year:    2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 Total
   ECB:        0    0    0    0    3   12   12   12   13   12   12   12   12   12   12    8    8    8    8    8    8    8    8    8    8    7   211
   Fed:        8   10    8    8    8    8    8   10   11    8    8    8    8    8    8    8    8    8    8    9   10    8    8    8    0    0   202
   Total:      8   10    8    8   11   20   20   22   24   20   20   20   20   20   20   16   16   16   16   17   18   16   16   16    8    7   413
   ```

3. **Coincidental 413 Count in Historical Train Split**: In `data/final/analysis_tier1.parquet`, the historical `train` split ($t \le 2019-12-31$) coincidentally contains exactly **413 decisions** (12,727 panel rows; average of ~30.8 index series per decision).
   - **Exact Filters Compared**:
     - *(i) Dual-Instrument Filter*: `shocks[shocks['regime'].isin(['Fed', 'ECB']) & shocks['shock_hf_raw'].notna() & shocks['shock_proxy_raw'].notna()]` $\rightarrow$ 413 unique decisions across 2000–2025.
     - *(ii) Tier 1 Train Split Filter*: `analysis_tier1[analysis_tier1['split_tag'] == 'train']['event_id'].nunique()` $\rightarrow$ 413 unique decisions across 2000–2019.
   - **Intersection Analysis**: The intersection of these two sets contains exactly **332 decisions**. Exactly 81 decisions in the dual-instrument set belong to post-2019 splits (`crisis` and `blind_test`), while 81 decisions in the Tier 1 `train` split lack sovereign yield proxy pairs (e.g. pre-2004 ECB).
   - **Conclusion**: The two sets do not share a common filter; the equal count of 413 is an exact numerical coincidence. An audit of all documentation confirms that **no document refers to panel rows as 'decisions'**; both references to 413 correctly designate unique policy decisions (`event_id`).

### 6.2 Mathematical Equivalence of Pooled vs. Macro Revision Placebos (Task 3b)
In Phase 3 exploratory sweeps, the 5,000-draw block permutation placebo for the Pooled specification and the Macro Revision sensitivity produced identical numerical outputs down to floating-point precision:
$$\beta_{\text{real}} = +0.001914308312711, \quad \text{Placebo Mean} = +0.000238986484, \quad p_{\text{emp}} = 0.0506$$

An audit of the underlying datasets in `final_fit` confirms that this is **not a software defect**, but a direct consequence of dataset architecture:
- In `src/modeling/tier_handler.py`, `prepare_tier_sample('pooled', split='final_fit')` concatenates `analysis_tier1` and `analysis_tier2_primary` in the `final_fit` split (2010–2023, dropping embargo buffer events). This produces exactly **349 decisions and 12,943 rows**.
- In `src/modeling/data_loader.py`, `load_modeling_data('sensitivity_macro_revision', split='final_fit')` loads the materialized table `data/v2_1/sensitivity_macro_revision.parquet` for `final_fit`.
- In `final_fit`, all 349 decisions in both tables are identical, their row sort order matches, and the maximum absolute difference between `shock_raw_bp` across all 12,943 rows is identically **0.0 bp**.
- Consequently, both datasets evaluate the exact same numerical matrix in `final_fit`, yielding mathematically identical permutation distributions and test statistics.

### 6.3 Disjoint Event Sets in `sensitivity_macro_revision` (Task 3c)
An exhaustive set-intersection audit confirms that `sensitivity_macro_revision.parquet` is the exact disjoint union of Tier 1 and Tier 2 Primary:
- **Tier 1 (`analysis_tier1.parquet`)**: 253 unique decisions (`event_id`), 9,350 event rows.
- **Tier 2 Primary (`analysis_tier2_primary.parquet`)**: 130 unique decisions (`event_id`), 4,851 event rows.
- **Set Intersection**: $\text{set}(E_{\text{Tier 1}}) \cap \text{set}(E_{\text{Tier 2 Primary}}) = \emptyset$ (exactly 0 overlapping decisions).
- **Macro Revision Union**: $253 + 130 = \mathbf{383\text{ decisions}}$, $9,350 + 4,851 = \mathbf{14,201\text{ rows}}$.
- All release documentation (`README.md`, `.zenodo.json`, `docs/PROJECT_SUMMARY.md`) and package generation scripts use these verified parquet-derived figures.

### 6.4 Nikkei 225 T+1 Reporting Convention Audit & Window Date Restriction (Phase 0b & 0c)
The second-source audit of Nikkei 225 (`^N225`) against FRED (`NIKKEI225`) establishes:
- **Date Shift Mechanism**: FRED logs Tokyo closes under the US business day date on which the data are ingested ($t+1$ relative to Tokyo session date $t$). Shifting FRED dates backwards by 1 calendar day ($\text{date}_{\text{FRED}} - 1\text{d}$) aligns Tokyo session closes with US calendar dates.
- **Window Restriction to 2010–2025**:
  - The previous audit script compared raw series extending into late 2026, which inadvertently incorporated a session on `2026-10-21`. The MoTrans-15 v2.1.1 benchmark window terminates strictly on **2025-12-31**.
  - Restricting strictly to the official window ($2010-01-01 \le \text{date} \le 2025-12-31$) evaluates exactly **3,911 trading sessions**.
- **Audit Findings**:
  - Under T+1 timezone alignment, **3,909 out of 3,911 sessions (99.95%) match within 1 bp**.
  - Exactly two sessions in 2010 exhibit discrepancies exceeding 1 bp:
    1. **2010-07-20**: Return difference = **114.42 bp** (Yahoo return $-1.38\%$ vs FRED return $-0.23\%$).
    2. **2010-09-15**: Return difference = **233.45 bp** (Yahoo return $+2.26\%$ vs FRED return $-0.07\%$).
  - **Factual Classification**: These two instances are reported factually as **unexplained discrepancies** between Yahoo Finance closing prices and the Federal Reserve Bank of St. Louis (FRED) secondary series. Prior conjectures attributing them to missing intermediate trading days have been removed to preserve evidentiary rigor.
  - The session `2026-10-21` is quarantined in the 2026 post-window buffer and is not part of the release dataset evaluation.

### 6.5 Reaction Window Timing and Pre-Announcement Contamination Risk (Task 3e)
The one-session cumulative log return is defined as:
$$\text{clr}_1 = \ln(P_{\text{react}} / P_{\text{baseline}})$$
where $P_{\text{baseline}}$ is the closing price on `baseline_obs_date` and $P_{\text{react}}$ is the closing price on `react_obs_date`.

An audit across all 82,054 decision-index pairs in `data/final/events.parquet` establishes the exact conditions under which the reaction window encapsulates pre-announcement trading:
1. **In-Session Announcements (`announce_in_session == 1`, 17,301 pairs)**:
   - When a policy announcement occurs while a local equity exchange is open, the reacting session is the same day's close ($t$), and the baseline session is the previous day's close ($t-1$).
   - **Pre-Announcement Return Contamination**: For all in-session pairs, $\text{clr}_1 = \ln(P_t / P_{t-1})$ spans the entire trading day of $t$. Consequently, $\text{clr}_1$ **incorporates pre-announcement morning trading returns** from exchange open until the announcement timestamp.
   - **Affected Bank / Market Index Pairs**:
     - **Federal Reserve (Fed)**: US equity indices (`us_sp500`, `us_rut`, `us_bkx`) trade 09:30–16:00 ET; FOMC statements release at 14:00 ET. $\text{clr}_1$ contains 4.5 hours of morning trading and morning macro releases (e.g. 08:30 CPI/employment data).
     - **European Central Bank (ECB)**: European indices (`de_dax`, `fr_cac40`, `es_ibex35`, `it_ftsemib`, `gb_ftse100`, etc.) trade 09:00–17:30 CET; ECB releases at 14:15 CET. $\text{clr}_1$ contains 5.25 hours of pre-announcement European trading.
     - **Bank of England (BoE)**: UK/European indices trade 08:00–16:30 London time; BoE announces at 12:00 noon. $\text{clr}_1$ contains 4 hours of morning trading.
     - **Bank of Canada (BoC)**: Canadian/US indices (`ca_tsx`, `us_sp500`) trade from 09:30 ET; BoC announces at 09:45 or 10:00 ET. $\text{clr}_1$ contains 15–30 minutes of pre-announcement trading.
     - **Reserve Bank of Australia (RBA)**: Australian/Asian indices (`au_asx200`, `jp_nikkei225`, `in_nifty50`, etc.) trade from 10:00 Sydney time; RBA announces at 14:30. $\text{clr}_1$ contains 4.5 hours of morning trading.
     - **Bank of Japan (BoJ)**: Japanese indices (`jp_nikkei225`, `jp_topix_banks_etf`) trade 09:00–11:30 JST (morning session); BoJ announces midday. $\text{clr}_1$ contains morning session trading.
     - **Bank of Russia (CBR)**: Russian indices (`ru_imoex`) trade from 10:00 MSK; CBR announces at 13:30 MSK. $\text{clr}_1$ contains 3.5 hours of morning trading.

2. **Out-of-Session Announcements (`announce_in_session == 0`, 64,753 pairs)**:
   - When a policy announcement occurs after a market has closed (e.g. Asian markets on Fed/ECB announcements; European markets on Fed 14:00 ET announcements), `baseline_obs_date` is the closing price on date $t$ (which closed before the announcement), and `react_obs_date` is the closing price on date $t+1$.
   - **Clean Post-Announcement Reaction**: For out-of-session pairs, the return window starts strictly after the policy announcement. No pre-announcement trading is encapsulated.

### 6.6 Empirical Robustness to Window Timing (Task 2)
To rigorously evaluate whether pre-announcement morning trading in $\text{clr}_1$ or subsequent cumulative returns contaminates empirical conclusions, all confirmatory specifications and headline exploratory models were re-estimated separately on:
1. **Out-of-Session Subset (`announce_in_session == 0`)**: Clean reaction windows where the baseline closing price occurs strictly prior to the announcement.
2. **In-Session Subset (`announce_in_session == 1`)**: Reaction windows spanning the announcement date from previous close, containing pre-announcement morning trading.

All models were evaluated using event-clustered standard errors and 999-draw restricted wild cluster bootstrap (Rademacher at `event_id`). Results are saved to `outputs/modeling/window_timing_robustness.csv`.

#### Side-by-Side Robustness Comparison

| Sample & Horizon | Specification | Window Timing Subset | $N_{\text{decs}}$ | $N_{\text{obs}}$ | Coef ($\beta$) | Cluster SE | Cluster $p$ | Wild Bootstrap $p$ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **v1 Blind Test `clr_1`** | Bivariate (`clr_1 ~ shock`) | Full Sample | 47 | 1,786 | $-0.000655$ | $0.000785$ | 0.4036 | 0.4424 |
| **v1 Blind Test `clr_1`** | Bivariate (`clr_1 ~ shock`) | **Out-of-Session (Clean)** | 47 | 1,197 | $-0.000679$ | $0.000789$ | 0.3898 | **0.4224** |
| **v1 Blind Test `clr_1`** | Bivariate (`clr_1 ~ shock`) | **In-Session (Contaminated)** | 47 | 589 | $-0.000609$ | $0.001087$ | 0.5751 | **0.6336** |
| **v1 Blind Test `clr_1`** | Pre-reg Overlap (`clr_1 ~ shock + ov`) | Full Sample | 47 | 1,786 | $-0.000620$ | $0.000804$ | 0.4407 | 0.4785 |
| **v1 Blind Test `clr_1`** | Pre-reg Overlap (`clr_1 ~ shock + ov`) | **Out-of-Session (Clean)** | 47 | 1,197 | $-0.000595$ | $0.000804$ | 0.4594 | **0.4905** |
| **v1 Blind Test `clr_1`** | Pre-reg Overlap (`clr_1 ~ shock + ov`) | **In-Session (Contaminated)** | 47 | 589 | $-0.000677$ | $0.001111$ | 0.5424 | **0.5956** |
| **v1 Blind Test `clr_5`** | Bivariate (`clr_5 ~ shock`) | Full Sample | 47 | 1,786 | $-0.002518$ | $0.002163$ | 0.2443 | 0.2753 |
| **v1 Blind Test `clr_5`** | Bivariate (`clr_5 ~ shock`) | **Out-of-Session (Clean)** | 47 | 1,197 | $-0.003518$ | $0.002185$ | 0.1073 | **0.1491** |
| **v1 Blind Test `clr_5`** | Bivariate (`clr_5 ~ shock`) | **In-Session (Contaminated)** | 47 | 589 | $-0.000571$ | $0.002225$ | 0.7975 | **0.8118** |
| **v1 Blind Test `clr_5`** | Pre-reg Overlap (`clr_5 ~ shock + ov`) | Full Sample | 47 | 1,786 | $-0.002261$ | $0.002083$ | 0.2776 | 0.3153 |
| **v1 Blind Test `clr_5`** | Pre-reg Overlap (`clr_5 ~ shock + ov`) | **Out-of-Session (Clean)** | 47 | 1,197 | $-0.003344$ | $0.002117$ | 0.1142 | **0.1461** |
| **v1 Blind Test `clr_5`** | Pre-reg Overlap (`clr_5 ~ shock + ov`) | **In-Session (Contaminated)** | 47 | 589 | $-0.000166$ | $0.002145$ | 0.9382 | **0.9459** |
| | | | | | | | | |
| **Tier 1 Final Fit `clr_5`** | Headline (`clr_5 ~ shock`) | Full Sample | 239 | 8,832 | $+0.003242$ | $0.003252$ | 0.3187 | 0.3664 |
| **Tier 1 Final Fit `clr_5`** | Headline (`clr_5 ~ shock`) | **Out-of-Session (Clean)** | 239 | 6,119 | $+0.002533$ | $0.003264$ | 0.4376 | **0.5576** |
| **Tier 1 Final Fit `clr_5`** | Headline (`clr_5 ~ shock`) | **In-Session (Contaminated)** | 238 | 2,713 | $+0.004926$ | $0.005011$ | 0.3256 | **0.4364** |
| **Tier 1 Final Fit Lead** | Lead Placebo (`clr_pre5 ~ shock`) | Full Sample | 239 | 8,829 | $+0.003040$ | $0.003927$ | 0.4388 | 0.6066 |
| **Tier 1 Final Fit Lead** | Lead Placebo (`clr_pre5 ~ shock`) | **Out-of-Session (Clean)** | 239 | 6,117 | $+0.004246$ | $0.004860$ | 0.3823 | 0.6857 |
| **Tier 1 Final Fit Lead** | Lead Placebo (`clr_pre5 ~ shock`) | **In-Session (Contaminated)** | 238 | 2,712 | $+0.000156$ | $0.003525$ | 0.9648 | 0.9660 |
| | | | | | | | | |
| **Pooled Final Fit `clr_5`** | Headline (`clr_5 ~ shock + tier`) | Full Sample | 349 | 12,943 | $+0.001924$ | $0.000653$ | 0.0032 | 0.5686 |
| **Pooled Final Fit `clr_5`** | Headline (`clr_5 ~ shock + tier`) | **Out-of-Session (Clean)** | 349 | 8,674 | $+0.002091$ | $0.000463$ | $6 \times 10^{-6}$ | **0.4505** |
| **Pooled Final Fit `clr_5`** | Headline (`clr_5 ~ shock + tier`) | **In-Session (Contaminated)** | 347 | 4,269 | $-0.001630$ | $0.005089$ | 0.7487 | **0.7708** |
| **Pooled Final Fit Lead** | Lead Placebo (`clr_pre5 ~ shock + tier`) | Full Sample | 349 | 12,940 | $-0.001407$ | $0.001066$ | 0.1868 | 0.7778 |
| **Pooled Final Fit Lead** | Lead Placebo (`clr_pre5 ~ shock + tier`) | **Out-of-Session (Clean)** | 349 | 8,672 | $-0.001511$ | $0.000930$ | 0.1041 | 0.7938 |
| **Pooled Final Fit Lead** | Lead Placebo (`clr_pre5 ~ shock + tier`) | **In-Session (Contaminated)** | 347 | 4,268 | $+0.001319$ | $0.005000$ | 0.7919 | 0.8048 |

#### Conclusion on Window Timing
**The empirical conclusion does not change.** 
1. In the headline immediate response window (`clr_1`), the estimated shock coefficient is virtually identical between out-of-session decisions ($\beta = -0.000679$, $p_{\text{wild}} = 0.4224$) and in-session decisions ($\beta = -0.000609$, $p_{\text{wild}} = 0.6336$). Both subsets represent statistical nulls.
2. In Tier 1 and Pooled `final_fit` models, restricting to clean out-of-session announcements leaves the estimates statistically indistinguishable from zero under wild cluster bootstrap ($p_{\text{wild}} = 0.5576$ for Tier 1; $p_{\text{wild}} = 0.4505$ for Pooled).
3. The presence of pre-announcement morning trading in 21.08% of event pairs does not drive the observed empirical null.

---

### 6.7 Comprehensive Verification of Release Table Date Bounds (Phase 0d)
To ensure that no decisions outside the formal dataset scope (2010-01-01 to 2025-12-31) were incorporated into the frozen v2.1.1 package, all 5 released tables in `data/v2_1/release/` were comprehensively audited for chronological bounds:

| Released Table | Total Rows | Unique Decisions | Min Date | Max Date | Decisions Pre-2010 | Decisions Post-2025 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `analysis_tier1.parquet` | 9,350 | 253 | 2010-01-14 | 2025-09-11 | **0** | **0** |
| `analysis_tier2_primary.parquet` | 4,851 | 130 | 2010-03-02 | 2025-09-17 | **0** | **0** |
| `secondary_holds.parquet` | 12,410 | 335 | 2010-01-07 | 2025-09-30 | **0** | **0** |
| `sensitivity_macro_revision.parquet` | 14,201 | 383 | 2010-01-14 | 2025-09-17 | **0** | **0** |
| `panel_returns_only.parquet` | 144,300 | — | 2010-01-04 | 2025-12-31 | **0** | **0** |

**Finding**: Exactly **ZERO** decisions in any released table fall before 2010-01-01 or after 2025-12-31. The release dataset strictly obeys the pre-registered 2010–2025 window. (The historical count of 413 decisions evaluated in earlier documentation was strictly an internal artifact in `data/final/analysis_tier1.parquet` spanning 2000–2019, which is completely excluded from the released tables).

---

### 6.8 Pooled Model Event-Level Leverage and Influence Audit (Phase 0e)
In Phase 3 and Phase 4 audits, the Pooled `final_fit` model ($G=349$ decisions, $N=12,943$ rows) exhibited a striking divergence between its asymptotic cluster-robust p-value and its wild cluster bootstrap p-value:
$$\beta = +0.001924, \quad \text{Cluster SE} = 0.000653, \quad t = 2.946, \quad p_{\text{cluster}} = 0.0032, \quad p_{\text{wild}} = 0.5686$$

To diagnose the econometric origin of this divergence, Leave-One-Event-Out (LOEO) regressions and event-level DFBETA statistics were computed across all 349 decisions (`scripts/audit_pooled_influence.py`):

#### Top 10 Most Influential Events in Pooled Model

| Rank | Event ID | Central Bank | Decision Date | Shock (bp) | Tier | $\Delta \beta$ (Slope Shift) | DFBETA |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `cbr_2014-12-16` | CBR | 2014-12-16 | +499.00 | 2 | **+0.002525** | **3.867** |
| 2 | `fed_2020-03-15` | Fed | 2020-03-15 | -21.29 | 1 | +0.000210 | 0.322 |
| 3 | `cbr_2015-01-30` | CBR | 2015-01-30 | -73.00 | 2 | -0.000181 | -0.277 |
| 4 | `rba_2020-03-19` | RBA | 2020-03-19 | -18.10 | 2 | -0.000176 | -0.269 |
| 5 | `fed_2020-03-03` | Fed | 2020-03-03 | -14.33 | 1 | +0.000171 | 0.261 |
| 6 | `boe_2020-03-19` | BoE | 2020-03-19 | -11.34 | 2 | -0.000154 | -0.237 |
| 7 | `ecb_2011-08-04` | ECB | 2011-08-04 | -17.60 | 1 | +0.000151 | 0.232 |
| 8 | `ecb_2020-03-12` | ECB | 2020-03-12 | +7.71 | 1 | -0.000133 | -0.203 |
| 9 | `boe_2020-03-11` | BoE | 2020-03-11 | -4.17 | 2 | +0.000129 | 0.198 |
| 10 | `boc_2020-03-04` | BoC | 2020-03-04 | -5.00 | 2 | +0.000105 | 0.160 |

#### Trimming Sensitivity: Refitting Without Influential Events

| Specification Trim | Events Dropped | $N_{\text{events}}$ | $N_{\text{obs}}$ | Coef ($\beta$) | Event SE | $t$-stat | $p_{\text{cluster}}$ | $p_{\text{wild}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **None (Full Sample)** | 0 | 349 | 12,943 | $+0.001924$ | $0.000653$ | 2.946 | 0.0032 | 0.5686 |
| **Drop Top 1% Influential** | 4 | 345 | 12,791 | $-0.000134$ | $0.004239$ | -0.032 | **0.9747** | **0.9720** |
| **Drop Top 2% Influential** | 7 | 342 | 12,681 | $-0.002314$ | $0.003441$ | -0.672 | **0.5013** | **0.4785** |
| **Drop Top 5% Influential** | 18 | 331 | 12,269 | $+0.001410$ | $0.002711$ | 0.520 | **0.6030** | **0.6126** |

#### Econometric Resolution
1. **Single-Event Dominance**: The entire positive point estimate of the Pooled model is driven by a single event: `cbr_2014-12-16` (the Russian Central Bank's emergency 650 bp overnight interest rate hike during the ruble collapse), which exhibits a shock of $+499$ bp and an extreme DFBETA of $3.867$.
2. **Breakdown of Asymptotic Approximation**: When omitting this single outlier event, the point estimate collapses from $+0.001924$ to $-0.000601$. When dropping the top 1% most influential events (4 decisions), the asymptotic cluster p-value collapses from $p=0.0032$ to $p=0.9747$.
3. **Validity of Wild Cluster Bootstrap**: The restricted wild cluster bootstrap, which is invariant to this extreme leverage because it resamples residuals at the cluster level under the null hypothesis, correctly identified that the data do not support rejecting the null ($p_{\text{wild}} = 0.5686$). This resolves the inference disagreement completely: the asymptotic cluster SE is invalid due to extreme outlier leverage, and the wild bootstrap correctly reveals the true empirical null.
