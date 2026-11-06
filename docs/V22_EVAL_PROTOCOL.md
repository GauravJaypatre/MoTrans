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
