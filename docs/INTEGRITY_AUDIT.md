# MoTrans-15: Research Integrity Audit & Blinding Verification

**Date**: 2026-11-03  
**Status**: ACTIVE / HARDENED  
**Commit Context**: Modeling Harness Final Hardening  
**Target Submission**: *Scientific Data* (Descriptor) / *Nature Communications* (Article)

---

## 1. Executive Summary

This audit assesses methodological integrity, sample blinding, and shock instrumentation across the transition from MoTrans-15 v1.0 to v2.1.1. 

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

## 4. Leakage Prevention Architecture in V2.1

To ensure that no model exploration or hyperparameter search accesses test split outcomes:
1. **Physical Column Guard**: `src/modeling/data_loader.py` physically strips `clr_1` through `clr_60` whenever `split="test"` or `split="all"` is loaded, unless `UNLOCK_TEST=1` is explicitly defined in the environment AND `allow_test_outcomes=True` is passed as a function argument.
2. **Access Trapping**: Unauthorized attempts to load test outcomes raise `PermissionError` and append a timestamped audit entry with git commit hash to `outputs/v2_1/unlock_audit.log`.
3. **Audit Log Verification**: Prior to Phase 4 test scoring, `unlock_audit.log` must contain exactly 16 historical lines (all dating to packaging and verification). Zero unauthorized or exploratory accesses have occurred.

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

3. **Coincidental 413 Count in Historical Train Split**: In `data/final/analysis_tier1.parquet`, the historical `train` split ($t \le 2019-12-31$) coincidentally contains exactly **413 decisions** (12,727 panel rows; average of ~30.8 index series per decision). An audit of all documentation confirms that **no document refers to panel rows as 'decisions'**; both references to 413 correctly designate unique policy decisions (`event_id`).

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

### 6.4 Nikkei 225 T+1 Reporting Convention Audit (Task 3d)
The second-source audit of Nikkei 225 (`^N225`) against FRED (`NIKKEI225`) demonstrates:
- **Date Shift Mechanism**: FRED logs Tokyo closes under the US business day date on which the data are ingested ($t+1$ relative to Tokyo session date $t$). Shifting FRED dates backwards by 1 calendar day ($\text{date}_{\text{FRED}} - 1\text{d}$) aligns Tokyo session closes with US calendar dates.
- **Session Alignment Counts**:
  - *Direct Calendar (Unshifted)*: 3,177 sessions compared; 99.59% fail (> 1 bp return difference; max diff = 2,262 bp).
  - *Timezone Shifted (T+1)*: 4,105 sessions compared; 99.93% match within 1 bp (only 3 sessions differ due to Tokyo typhoon/holiday closure reconciliations; max diff = 233.45 bp).
- **Integrity Certification**: The T+1 shift documents a known secondary data-ingestion convention and does not conceal genuine price or timing misalignment.

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

