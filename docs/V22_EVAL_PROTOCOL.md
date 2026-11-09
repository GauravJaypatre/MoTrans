# MoTrans-15 v2.2 Evaluation Protocol & Out-of-Sample Pre-Specification

**Document ID**: `DOCS-EVAL-001`  
**Dataset Version**: MoTrans-15 v2.2  
**Date**: November 2026  
**Status**: PRE-DECLARED SPECIFICATION (FROZEN PRIOR TO TEST UNLOCK)  
**Rule**: Strictly NO test scoring or alternative test design evaluation is executed until approved by the principal investigator.

---

## 1. Single Source of Truth & Sample Partitioning

All data loaders, validation pipelines, and final scoring scripts must derive partition boundaries strictly from `data/v2_2/splits.csv` (and `data/v2_2/release/splits.csv`).

### 1.1 Out-of-Sample Test Partitions (2024–2025)

The held-out test split terminates on 2025-12-31 with a 60-day embargo. When test scoring is unlocked (Phase 4), all benchmarks must be evaluated across two distinct, parallel samples:

| Sample Partition | Decision Count ($N_{\text{decs}}$) | Event Rows ($N_{\text{obs}}$) | Prior Exposure (`read_by_prior_analysis`) | Description / Composition |
| :--- | :---: | :---: | :---: | :--- |
| **Sample A: Full Test Set** | **70** | **2,590** | 14 (20.0%) | Comprehensive test window ($14 \text{ ECB} + 20 \text{ Tier 2 Actions} + 36 \text{ Holds}$). Includes the 14 ECB meetings evaluated during the v1 blind test. |
| **Sample B: Pristine Test Set** | **56** | **2,072** | **0 (0.0%)** | Pure unblinded sample (`read_by_prior_analysis == 0`). Contains strictly Fed, BoE, BoC, and RBA decisions with zero prior return exposure. |

*Row counts: 37 equity index series per decision.*

---

## 2. Pre-Declared Alternative Test Designs (DO NOT RUN PRIOR TO FREEZE)

To avoid post-hoc specification searching while addressing the structural characteristics of macroeconomic cycles, three alternative test designs are formally pre-declared:

### 2.1 Design 1: Regime-Stratified Forward-Chaining
- **Motivation**: Cross-country pooling risks letting high-frequency central banks (Fed and ECB) dominate cross-validation tuning. 
- **Specification**:
  $$\text{clr}_{i,t}^W = \alpha_r + \beta_r \cdot \text{shock}_{t}^{\text{fold\_std}} + \epsilon_{i,t}$$
  estimated independently across rolling folds (Folds 1–4) for each central bank regime $r \in \{\text{Fed}, \text{ECB}, \text{BoE}, \text{BoC}, \text{RBA}, \text{CBR}, \text{BoJ}\}$.
- **Aggregation**: Cross-regime meta-analytic slope $\bar{\beta} = \sum w_r \hat{\beta}_r$ weighted by inverse variance, with between-regime heterogeneity $\tau^2$ (DerSimonian-Laird).
- **Execution Rule**: Evaluated strictly on training and validation folds (2010–2023).

### 2.2 Design 2: Leave-One-Tightening-Episode-Out (LOTEO)
- **Motivation**: Monetary tightening is rare, autocorrelated, and concentrated in distinct macro episodes. Standard k-fold or time-block splitting can interpolate within an active tightening cycle.
- **Identified Tightening Episodes**:
  - **Episode 1 ($E_1$, 2011)**: ECB Trichet rate hikes (April and July 2011).
  - **Episode 2 ($E_2$, 2015–2018)**: Federal Reserve post-ZIRP tightening cycle (9 rate hikes).
  - **Episode 3 ($E_3$, 2022–2023)**: Synchronized global inflation response (Fed, ECB, BoE, BoC, RBA rapid hikes).
- **Protocol**:
  - Iteratively hold out episode $E_k$.
  - Fit model on all remaining training/validation periods ($t \le 2023-12-31 \setminus E_k$).
  - Evaluate out-of-episode directional prediction accuracy and mean squared prediction error on $E_k$.
- **Decision Criterion**: A negative equity transmission response ($\beta < 0$) must persist out-of-episode across at least 2 of the 3 episodes to be considered structurally stable.

### 2.3 Design 3: Held-Out Test as Sanity Check for Easing and Holds Only
- **Structural Limitation**: The 2024–2025 out-of-sample period coincides with a global monetary loosening cycle among the included central banks (the Bank of Japan hiked rates in March and July 2024, but BoJ is routed to Tier 2 sensitivity).
  - **Sample A**: 12 rate cuts, 58 holds, **0 rate hikes**.
  - **Sample B**: 10 rate cuts, 46 holds, **0 rate hikes**.
- **Scope & Rescoping**:
  - The held-out test split **CANNOT** evaluate monetary tightening transmission.
  - The test split is pre-registered strictly as a **sanity check on easing response and hold inertia**.
  - Any paper draft submitted to *Scientific Data* or *Nature Communications* must explicitly declare:
    > *"Out-of-sample testing evaluates transmission during an easing and pause regime; empirical findings cannot be generalized to tightening cycles without historical conditioning."*

---

## 3. Inference Hierarchy & Default Standards

1. **Primary Headline Metric**: Restricted Wild Cluster Bootstrap (Rademacher two-point weights at `event_id`, $B=999$ replications).
2. **Secondary Standard Error**: Two-way cluster-robust covariance ($\text{event\_id} \times \text{index\_id}$) with finite-sample degrees of freedom $df = \min(G_{\text{event}} - 1, G_{\text{index}} - 1)$.
3. **Prohibited Inferential Routines**:
   - Unclustered OLS (prohibited due to severe Moulton intra-event inflation).
   - Index-only clustering (prohibited because monetary shocks vary at the decision level).

---

## 4. Window Timing & Reaction Purity Protocol

1. **Pristine Window Reaction (`clr_1_clean`)**:
   - Defined strictly for out-of-session announcements (`announce_in_session == 0`):
     $$\text{clr}_1^{\text{clean}} = \begin{cases} \text{clr}_1 & \text{if } \text{announce\_in\_session} = 0 \\ \text{NaN} & \text{if } \text{announce\_in\_session} = 1 \end{cases}$$
   - Completely excludes pre-announcement morning trading returns.
2. **Robustness Check (`clr_1` with In-Session Interaction)**:
   $$\text{clr}_{i,t}^1 = \alpha + \beta_1 \cdot \text{shock}_t + \beta_2 \cdot (\text{shock}_t \times \text{in\_session}_i) + \gamma \cdot \text{in\_session}_i + \epsilon_{i,t}$$

---

## 5. Multiplicity Control

For confirmatory reporting across the 5 horizons ($M = 5$: $\text{clr}_1, \text{clr}_3, \text{clr}_5, \text{clr}_{20}, \text{clr}_{60}$):
- **Holm-Bonferroni Adjusted p-values**:
  $$p_{(k)}^{\text{Holm}} = \min\left(1, \max_{j \le k} \left[(M - j + 1) \cdot p_{(j)}\right]\right)$$
- No individual horizon may be claimed statistically significant unless its Holm-adjusted wild bootstrap p-value satisfies $p^{\text{Holm}} < 0.05$.

---

## 6. Statistical Power, Corrected MDE & Outlier Distortion

### 6.1 Statistical Power & Minimum Detectable Effect (MDE) Table
All power calculations are generated from `scripts/power_analysis.py` (`outputs/modeling/power_analysis_mde.csv`) at 80% statistical power ($\alpha = 0.05$, two-sided):

| Estimation Design | Decision Count ($N_{\text{decs}}$) | Event Rows ($N_{\text{obs}}$) | Untrimmed Asymptotic Cluster SE | Untrimmed Wild Bootstrap SE | Trimmed Top 1% SE | Headline Robust SE | Untrimmed Asymptotic MDE (bp) | Untrimmed Wild Bootstrap MDE (bp) | Conservative Headline MDE (bp) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tier 1 Final Fit** | 239 | 8,832 | 0.003252 | 0.003600 | 0.003274 | **0.003600** | 91.47 bp | 101.27 bp | **101.27 bp** |
| **Tier 2 Primary Final Fit** | 110 | 4,111 | 0.001302 | 0.001389 | 0.006107 | **0.006107** | 36.82 bp | 39.28 bp | **172.65 bp** |
| **Pooled Final Fit** | 349 | 12,943 | 0.000653 | 0.000713 | 0.004239 | **0.004239** | 18.35 bp | 20.03 bp | **119.10 bp** |
| **Full Test Split (Sample A)** | 70 | 2,590 | 0.001458 (proj) | 0.001594 (proj) | 0.009466 (proj) | **0.009466** | 41.46 bp | 45.33 bp | **269.12 bp** |
| **Pristine Test Split (Sample B)**| 56 | 2,072 | 0.001630 (proj) | 0.001782 (proj) | 0.010583 (proj) | **0.010583** | 46.53 bp | 50.87 bp | **302.06 bp** |

### 6.2 Methodological Note on Pooled MDE and Influence Sensitivity
> **METHODOLOGICAL NOTE ON POOLED MDE AND INFLUENCE SENSITIVITY**:
> An earlier draft of the power analysis reported an untrimmed asymptotic pooled MDE of **18.35 bp** per 1 SD shock ($SE = 0.000653$). 
> Econometric leverage auditing demonstrated that this asymptotic standard error is heavily compressed by a single high-leverage event: `cbr_2014-12-16` (the Central Bank of Russia emergency 650 bp overnight rate hike, where policy decision `size_bp = 650.0`, sovereign 1-year yield proxy shock `shock_raw_bp = 499.0`, and `shock_tier = 2`).
> In ordinary least squares, a single massive regressor outlier inflates the sample variance $(X'X)$ in the denominator of $(X'X)^{-1}$, creating a mechanically compressed asymptotic standard error.
> When trimming the top 1% most influential events, the standard error is $0.004239$, yielding a **conservative headline MDE of 119.10 bp**.
> The pooled MDE of 119.10 bp is reported as the **"conservative headline MDE after trimming the top 1% influential events"**, presented side by side with the untrimmed asymptotic (18.35 bp) and wild bootstrap (20.03 bp) MDEs, rather than as an "error correction" or "+549% distortion". Both untrimmed and trimmed figures are reported together to ensure complete methodological transparency.

---

## 7. Robust Influence Handling Protocol

To ensure empirical transparency and eliminate any possibility of post-hoc sample pruning:
1. **Primary Headline Model**: The confirmatory and headline exploratory models are estimated on the **full, unpruned sample** ($N=349$ for pooled, $N=239$ for Tier 1) using restricted wild cluster bootstrap at `event_id`. Outliers are strictly **not dropped** from the primary specification.
2. **Mandatory Pre-Declared Influence Robustness Check**: Every headline result must be accompanied side by side with a pre-declared robustness check:
   - Re-fit the exact model omitting the single most influential event identified by Leave-One-Event-Out (LOEO) absolute DFBETA (for the pooled model: `cbr_2014-12-16`, policy rate hike `size_bp = 650.0`, sovereign proxy `shock_raw_bp = 499.0`, `shock_tier = 2`).
   - Report $\beta$, clustered SE, wild bootstrap p-value, and $\Delta \beta$.
   - Explicitly label this refit as `"Robustness Check: Dropping #1 Most Influential Event (cbr_2014-12-16)"`.
   - If a result is statistically significant in the primary fit but collapses upon omitting that single event, it is classified as **"fragile to leverage; cannot reject null"**.


