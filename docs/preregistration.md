# Pre-Registration Plan & Methodological Lock — MoTrans-15

**Project**: Monetary Transmission to Equities Across the 15 Largest Economies (MoTrans-15)  
**Authors**: MoTrans Research Team  
**Status**: **LOCKED** (No outcome models have been estimated; all rules locked prior to unblinding)  
**Lock Date**: 2026-10-24  

---

## 1. Study Overview & Objective

MoTrans-15 investigates the causal impact of central bank monetary policy announcements on equity markets across the 15 largest global economies (US, China, Japan, Germany, UK, France, India, Italy, Brazil, Canada, Russia, South Korea, Australia, Mexico, Spain) spanning 2000 to 2026.

The research design evaluates:
1. **Domestic Equity Transmission**: The immediate and persistent reaction of broad market, banking sector, and small-cap equity indices to domestic policy surprises.
2. **Cross-Border Spillovers**: The international transmission of US Federal Reserve and European Central Bank policy shocks to foreign equity markets.
3. **Transmission Channels**: Decomposing responses across interest rate expectations, term premia, and equity risk premia.

---

## 2. Sample Split & Blind Test Architecture

To prevent $p$-hacking, data snooping, and specification search, the dataset is strictly partitioned into three chronological sample splits:

| Split Tag | Calendar Window | Purpose | Model Fitting Status |
|---|---|---|---|
| `train` | 2000-01-01 to 2019-12-31 | Model development, baseline estimation, hyperparameter tuning | Pre-registered for exploratory & training estimation |
| `crisis` | 2020-01-01 to 2021-12-31 | COVID-19 pandemic crisis period (liquidity interventions, asset purchases, zero bounds) | Evaluated separately as a crisis stress-test regime |
| `blind_test` | 2022-01-01 to 2026-10-24 | Post-pandemic inflation shock, aggressive global tightening, and current cycle | **Strictly held out; zero model estimation prior to lock** |

All shock standardizations (`shock_std`) are computed strictly using the standard deviation of raw shocks over the `train` period ($t \le 2019-12-31$), ensuring that variance from the blind test or crisis periods never leaks into shock scaling.

---

## 3. Identification Strategy & Tiering Hierarchy

Policy surprises are categorized into a hierarchical identification structure based on measurement precision:

### Tier 1: High-Frequency Identification (Headline Primary)
- **Coverage**: US Federal Reserve and Euro Area (ECB).
- **Instruments**:
  - **Fed**: Consensus intraday futures monetary policy surprise (`MPS`), 30-minute window around FOMC statements/press conferences (Bauer and Swanson, 2023).
  - **ECB**: 1-year Overnight Index Swap (OIS) change within the monetary event window from the Euro Area Monetary Policy Event-Study Database (EA-MPD; Altavilla et al., 2019).
- **Designation**: Primary headline evaluation. Evaluated across both rate changes and meeting holds (`shock_primary = 1`).

### Tier 2: Sovereign Benchmark Yield Proxies (Secondary Transfer Test)
- **Coverage**: Bank of England (BoE), Bank of Canada (BoC), Reserve Bank of Australia (RBA), Central Bank of Russia (CBR), and post-HFI fallback periods for Fed and ECB.
- **Instrument**: Change in the 1-year (or 2-year where 1-year is unavailable) sovereign benchmark yield from baseline market close to the reacting session close.
- **Designation**: Out-of-sample transfer test evaluating whether cross-border equity reactions generalize from high-frequency surprises to daily sovereign yield proxies.

### Excluded / Descriptive Regimes
- **Banxico, BoK, RBI**: Excluded from causal primary/secondary panels due to absence of continuous, freely accessible daily sovereign yield curve data.
- **BCB**: Post-2019 decisions excluded due to termination of the daily 1-year swap curve (SGS 7806).
- **PBoC**: Excluded from primary due to regulatory policy shifts and Loan Prime Rate (LPR) benchmark proxy limitations.

---

## 4. Outcomes, Event Windows, and Controls

1. **Cumulative Log Returns ($clr_W$)**:
   $$\text{clr}_W = \ln(P_{t+W-1} / P_{t-1})$$
   where $t-1$ is the pre-announcement baseline closing price and $t$ is the first exchange trading session reacting to the announcement. Pre-registered horizons: $W \in \{1, 3, 5, 20, 60\}$ trading days.
2. **Macroeconomic and Financial Controls**:
   All controls are merged strictly as-of their public availability date (`available_from <= decision_date`) with strict maximum carry-forward windows (7 days for daily financial series, 62 days for monthly macro series). No forward-filling across stale intervals is permitted.
3. **Decision Overlap Tracking**:
   Forward event windows must control for overlapping central bank policy decisions occurring within $[t, t+W-1]$ using indicators `overlap_Wd` and continuous counts `overlap_count_Wd`.

---

## 5. Methodological Amendments (Dated & Pre-Specified)

The following amendments to the original research specification were formally adopted. **Every amendment was established prior to running any outcome regressions or inspecting empirical causal responses.**

| Rule / Amendment | Date Set | Status Regarding Outcomes | Methodological Rationale |
|---|---|---|---|
| **Tier 1 Headline Blind Test** | 2026-10-22 | **Before inspecting outcomes** | Pre-specified that the definitive benchmark test of cross-border monetary transmission is evaluated on the held-out `blind_test` period (2022–2026) for Tier 1 high-frequency shocks. |
| **Tier 2 Rate-Changes-Only Primary** | 2026-10-23 | **Before inspecting outcomes** | Restricted Tier 2 `shock_primary = 1` strictly to policy actions (`decision in ("hike", "cut")`). Holds are relegated to secondary sensitivity (`shock_secondary = 1`) because empirical diagnostics revealed that daily yield variance on hold days is indistinguishable from non-meeting noise ($VR \approx 1.0$), whereas rate-change days carry massive excess volatility ($VR = 3.8\text{ to }7.2$). |
| **BoJ Excluded from Primary** | 2026-10-21 | **Before inspecting outcomes** | Bank of Japan is excluded from primary baseline (`shock_primary = 0`) due to prolonged Zero Interest Rate Policy (ZIRP) and Yield Curve Control (YCC) peg suppressing daily sovereign yield variance. Retained under `shock_primary_rescaled` for post-March 2024 exit sensitivity. |
| **PBoC Excluded from Primary** | 2026-10-21 | **Before inspecting outcomes** | People's Bank of China excluded from primary baseline (`shock_primary = 0`) due to Loan Prime Rate (LPR) regulatory benchmark shifts and proxy limitations. |
| **RBA Pre-2008 Holds are Non-Announcement Days** | 2026-10-22 | **Before inspecting outcomes** | Sourced from official RBA Media Release MR-07-22: Board meetings prior to February 2008 issued no public announcement when rates were held unchanged. Classified as `non_announcement_day`, `time_quality = "unknown"`, `analysis_ready_timing = 0`, and `shock_primary = 0`. |
| **BoE Pre-2016 Timing Approximate** | 2026-10-24 | **Before inspecting outcomes** | Bank of England decisions prior to 2016-01-01 assigned `time_quality = "approximate"` and `analysis_ready_timing = 0`, as on-disk documentation verifies the 12:00 noon Thursday publication rule only for the 2016–present MPC convention. |
| **Overlap Contamination Controls** | 2026-10-22 | **Before inspecting outcomes** | Mandatory inclusion of forward window policy overlap controls (`overlap_1d` to `overlap_60d` and counts) to isolate multi-central bank confounding at medium and long horizons. |
| **Winsorization at ±4.0 SD** | 2026-10-22 | **Before inspecting outcomes** | Standardized shocks capped strictly at $\pm 4.0$ SD (`shock_std_w`) to prevent extreme geopolitical and crisis outliers (e.g., CBR emergency hike of February 2022) from exerting disproportionate leverage on linear estimators. |

---

## 6. Pre-Registration Lock Confirmation

- **Outcome Model Status**: Zero outcome regressions, local projections, panel models, or causal inferences have been estimated on the frozen dataset.
- **Dataset Integrity**: All data transformations, cleaning scripts, timing rules, and shock constructions are fully deterministic, frozen, and reproducible from `data/raw/`.
- **Lock Declaration**: This document is formally **LOCKED** as of 2026-10-24. Any subsequent changes to sample definitions, timing rules, or variable constructions must be documented as post-freeze deviations in a new version changelog.
