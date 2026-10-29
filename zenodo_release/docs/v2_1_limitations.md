# MoTrans-15 v2.1 Dataset Limitations & Methodological Constraints

This document explicitly catalogues known structural, econometric, and data limitations in MoTrans-15 v2.1. Researchers and quantitative modelers must account for these constraints.

---

## 1. Low Tightening Content in Early Sample (2010–2015)

- Following the 2008 Global Financial Crisis, G6 central banks engaged in prolonged Zero Lower Bound (ZLB) and Zero Interest Rate Policy (ZIRP).
- Between 2010 and 2015:
  - The Federal Reserve implemented **zero rate hikes** (the first post-crisis hike occurred in December 2015).
  - The European Central Bank implemented only **2 rate hikes** (April and July 2011, quickly reversed).
  - The Bank of England implemented **zero rate hikes**.
  - The Bank of Japan remained at zero / negative interest rates throughout.
- **Econometric Consequence**: Development Folds 1 and 2 (origins 2016 and 2018) contain fewer than 10 Tier 1 rate hikes in training (Fold 1 has 2; Fold 2 has 6). Models trained purely on early folds lack empirical exposure to monetary tightening regimes.

---

## 2. High-Frequency Shocks Truncation & Fallbacks

- **Federal Reserve (Bauer-Swanson MPS)**: High-frequency intraday futures surprises end in **December 2023**. Consequently:
  - In the **Test Split (2024–2025)**, the Fed has **zero Tier 1 high-frequency decisions**.
  - Fed rate decisions in 2024–2025 fall back entirely to Tier 2 sovereign 1-year yield proxies.
- **European Central Bank (EA-MPD OIS 1Y)**: EA-MPD intraday OIS surprises cover through late 2023 / early 2024; later 2024–2025 meetings transition to sovereign yield proxies.

---

## 3. Test Window Regime Asymmetry (Mostly Easing Cycle)

- The locked out-of-sample test window covers **2024-01-01 through 2025-12-31**.
- Across all central banks in the test window:
  - Total rate hikes: **0** (zero rate hikes across all G6 central banks in 2024–2025).
  - Rate cuts: 28 usable decision events.
  - Holds: 42 usable decision events.
- **Econometric Consequence**: The test split evaluates model generalisation exclusively during a synchronized global easing cycle. Test evaluations cannot assess model performance during policy tightening.

---

## 4. Tier 2 Proxy Shock Measurement Quality

- Tier 2 shocks rely on 1-day or 2-day daily changes in sovereign government bond yields (1Y or 2Y) between baseline and reacting sessions.
- While sovereign yields reflect shifts in short-term policy expectations, daily yield changes inevitably absorb:
  - Term premium fluctuations.
  - Sovereign credit risk and fiscal news.
  - Concurrently released macroeconomic data (e.g., employment reports released on announcement mornings).
- Proxy shocks exhibit higher variance and potential attenuation bias compared to Tier 1 30-minute intraday surprises.

---

## 5. Bank of Russia (CBR) Rate-Change Only History & Wartime Truncation

- The Bank of Russia key-rate history in the dataset comprises rate-change decisions and major policy meetings; routine scheduled holds without rate changes were not consistently tracked in legacy data.
- **2014-12-16 Emergency Meeting**: The emergency midnight hike (+650 bp) resulted in a +499 bp 1-day yield change. Including this event in standard deviation calculations inflates the training SD to 66.62 bp; v2.1 implements a robust MAD scale (13.34 bp) while providing unscaled `shock_raw_bp` on all rows.
- **Wartime Truncation**: Following the escalation of hostilities on 2022-02-24, MOEX trading was suspended, Russian equities became non-convertible for foreign investors, and CBR policy decisions shifted to wartime emergency operations. All post-February 2022 CBR decisions are disqualified (`analysis_ok = 0`).

---

## 6. Brazil (BCB) Proxy Cessation

- Banco Central do Brasil (BCB) relies on the SGS 7806 swap DI x pre 360 days series for its short-term yield proxy.
- **Cessation**: The SGS 7806 series officially ceased publication on **2019-09-30**.
- Combined with unarchived Copom meeting announcement timestamps (`timing_verified_level = 'none'`), all 134 BCB decisions in 2010–2025 have `analysis_ok = 0`. BCB contributes zero usable decisions to the analysis tables.

---

## 7. Proprietary Equity Indices & Release Licensing

- Equity returns (`ret_local`, `ret_usd`, `clr_1`, `clr_3`, `clr_5`, `clr_20`, `clr_60`) in `data/v2_1/release/` are derived from licensed financial index price feeds.
- Proprietary closing index levels (`level_local`) have been stripped from release bundles.
- Due to upstream licensing restrictions from commercial benchmark providers, the release bundle **must remain private and not redistributed** until full commercial and academic redistribution terms are confirmed.

---

## 8. Uncompleted Hand Labels

- Manual textual sentiment classifications, tone tags, and narrative hand labels remain in preliminary draft status and have not been validated by double-blind inter-annotator agreement.
- Hand labels are not included in the primary econometric analysis tables and must not be used for causal inference without prior verification.
