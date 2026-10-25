# MoTrans-15 v2.1 Data Dictionary

Comprehensive variable definitions, types, measurement units, provenance sources, and data leakage isolation notes for MoTrans-15 v2.1.

---

## 1. Primary Identification & Timing Variables

| Column Name | Data Type | Units / Format | Provenance Source | Description & Leakage Isolation Notes |
| :--- | :---: | :---: | :--- | :--- |
| `event_id` | string | `<regime>_<date>` | Standardised identifier | Unique decision event identifier (e.g. `fed_2021-11-03`, `ecb_2022-07-21`). |
| `regime` | string | Code (e.g. `Fed`) | Central bank metadata | Governing central bank: `Fed`, `ECB`, `BoE`, `BoC`, `RBA`, `CBR`, `BoJ`, `BCB`, `Banxico`, `RBI`, `BoK`, `PBoC`. |
| `decision_date` | string | `YYYY-MM-DD` | Official CB calendar | Exact announcement date of the policy decision. Defines train/val/test splits without leakage. |
| `announce_ts_utc` | string | ISO-8601 UTC | CB press releases / API | Exact timestamp of the policy announcement in UTC. |
| `time_quality` | string | `exact` / `approximate` / `convention` | Timing audit | Quality flag of announcement timestamp. |
| `timing_verified_level`| string | `event` / `convention` / `none` | Verification audit | Independent timing provenance level. Pre-2016 BoE is `convention`; BCB/Banxico/RBI are `none`. |
| `baseline_date` | string | `YYYY-MM-DD` | Alignment engine | Last trading session close strictly at or before the announcement. |
| `reacting_session_date`| string | `YYYY-MM-DD` | Alignment engine | First trading session close strictly after the announcement. |
| `announce_in_session` | int | 0 / 1 | Exchange schedule | Flag indicating whether announcement occurred during trading hours of the reacting market. |
| `timing_ambiguous` | int | 0 / 1 | Alignment engine | Flag indicating whether an announcement window spans multiple closing sessions. |

---

## 2. Splits, Folds, and Embargo Variables

| Column Name | Data Type | Units / Format | Provenance Source | Description & Leakage Isolation Notes |
| :--- | :---: | :---: | :--- | :--- |
| `final_split` | string | `train` / `validation` / `test` / `post_window` | `src/v2_1_config.py` | Official evaluation split. `train` (2010–2021), `validation` (2022–2023), `test` (2024–2025), `post_window` (2026+). |
| `embargo_dropped` | int | 0 / 1 | Embargo engine | Flag indicating whether the 60-day observation window (`clr_60`) extends across a split boundary. Dropped from usable sample (`analysis_ok = 0`). |
| `fold_1` | string | `train` / `val` / `unused` | Rolling-origin fold | Development Fold 1: Origin `2016-01-01`. Validates 2016–2017. |
| `fold_2` | string | `train` / `val` / `unused` | Rolling-origin fold | Development Fold 2: Origin `2018-01-01`. Validates 2018–2019. |
| `fold_3` | string | `train` / `val` / `unused` | Rolling-origin fold | Development Fold 3: Origin `2020-01-01`. Validates 2020–2021. |
| `fold_4` | string | `train` / `val` / `unused` | Rolling-origin fold | Development Fold 4: Origin `2022-01-01`. Validates 2022–2023. |
| `v1_split_tag` | string | `train` / `blind_test` | v1.0 heritage | Legacy split tag preserved for backward compatibility and reference only. |

---

## 3. Monetary Shocks and Policy Variables

| Column Name | Data Type | Units / Format | Provenance Source | Description & Leakage Isolation Notes |
| :--- | :---: | :---: | :--- | :--- |
| `decision` | string | `hike` / `cut` / `hold` | Central bank statement | Policy rate action taken at the meeting. |
| `size_bp` | float | Basis points | Policy rate series | Official policy rate change in basis points (e.g. `+25.0`, `-50.0`, `0.0`). |
| `shock_raw_bp` | float | Basis points | High-freq OIS / Yield proxy | Unscaled monetary policy surprise in basis points. Provided for leak-free within-fold standardisation. |
| `shock_std` | float | Standard deviations | Descriptive fixed scale | Descriptive standardised shock. For CBR, scaled by robust MAD scale (13.3434 bp); for others, pre-2020 SD. |
| `shock_std_legacy` | float | Standard deviations | Legacy SD scale | Historical standardized shock using full sample standard deviation (including 2014-12-16 emergency event for CBR). |
| `shock_measure_type` | string | `high_frequency` / `proxy_yield` | Shock registry | Shock measurement methodology: Tier 1 high-frequency OIS surprise vs Tier 2 1Y/2Y sovereign yield change. |
| `shock_tier` | int | 1 / 2 | Shock hierarchy | Tier 1 (clean high-frequency intraday) vs Tier 2 (daily sovereign yield change proxy). |
| `policy_rate` | float | Percent per annum | Central bank policy rate | Official target policy rate level following the announcement. |
| `zero_lower_bound` | int | 0 / 1 | Policy classification | Binary indicator: 1 if `policy_rate <= 0.25%`, 0 otherwise. |
| `qe_ycc_indicator` | int | 0 / 1 | BoJ policy classification | Binary indicator for Bank of Japan: 1 during QQE/YCC era (2013-04-04 to 2024-03-19), 0 otherwise. |

---

## 4. Cumulative Event Returns (Equity Horizons)

| Column Name | Data Type | Units / Format | Provenance Source | Description & Leakage Isolation Notes |
| :--- | :---: | :---: | :--- | :--- |
| `index_id` | string | Index symbol | Market price feed | International equity series identifier (33 broad market benchmarks, 5 sector/size ETFs). |
| `index_class` | string | `broad` / `sector` / `size` | Market classification | Broad market benchmark vs sector ETF proxy. |
| `home_market` | string | ISO country code | Market definition | Country/jurisdiction of the equity index. |
| `clr_1` | float | Log return | Daily equity close | 1-day cumulative log return: $\ln(P_{\text{react}}) - \ln(P_{\text{base}})$. |
| `clr_3` | float | Log return | Daily equity close | 3-day cumulative log return from baseline to 3rd trading day. |
| `clr_5` | float | Log return | Daily equity close | 5-day cumulative log return from baseline to 5th trading day. |
| `clr_20` | float | Log return | Daily equity close | 20-day cumulative log return (~1 calendar month). |
| `clr_60` | float | Log return | Daily equity close | 60-day cumulative log return (~3 calendar months). Monitored for split boundary embargo. |

---

## 5. Overlap Controls (Concurrent Central Bank Announcements)

| Column Name | Data Type | Units / Format | Provenance Source | Description & Leakage Isolation Notes |
| :--- | :---: | :---: | :--- | :--- |
| `overlap_1d` | int | 0 / 1 | Event study alignment | 1 if another central bank announcement occurs within 1 trading day. |
| `overlap_3d` | int | 0 / 1 | Event study alignment | 1 if another central bank announcement occurs within 3 trading days. |
| `overlap_5d` | int | 0 / 1 | Event study alignment | 1 if another central bank announcement occurs within 5 trading days. |
| `overlap_20d` | int | 0 / 1 | Event study alignment | 1 if another central bank announcement occurs within 20 trading days. |
| `overlap_60d` | int | 0 / 1 | Event study alignment | 1 if another central bank announcement occurs within 60 trading days. |
| `overlap_count_<h>` | int | Integer count | Event study alignment | Exact count of concurrent central bank decisions within the horizon. |

---

## 6. Point-in-Time As-Of Macro Controls

All macro controls strictly enforce point-in-time publication lags: values are mapped using `available_from <= decision_date`.

| Column Name | Data Type | Units / Format | Provenance Source | Description & Leakage Isolation Notes |
| :--- | :---: | :---: | :--- | :--- |
| `ctrl_cpi` | float | YoY Percent | National Statistical Agencies | Consumer Price Index YoY inflation as known on announcement day. |
| `ctrl_yield_1y` | float | Percent per annum | Central bank / Benchmark | 1-Year sovereign government bond yield. |
| `ctrl_yield_2y` | float | Percent per annum | Central bank / Benchmark | 2-Year sovereign government bond yield. |
| `ctrl_yield_short` | float | Percent per annum | Central bank / Benchmark | Short policy/money market reference yield. |
| `ctrl_vix` | float | Index points | CBOE / National exchange | Equity market implied volatility index (VIX or local proxy). |
| `ctrl_fx_lcu_per_usd` | float | FX exchange rate | Market close | Spot foreign exchange rate (Local Currency Units per 1 USD). |
| `ctrl_policy_rate` | float | Percent per annum | Central bank history | Prevailing policy rate prior to announcement. |
| `ctrl_ind_prod` | float | YoY Percent | National Statistical Agencies | Industrial Production growth YoY (attached in `sensitivity_macro_revision.parquet`). |

---

## 7. Data Quality & Usability Masks

| Column Name | Data Type | Units / Format | Provenance Source | Description & Leakage Isolation Notes |
| :--- | :---: | :---: | :--- | :--- |
| `price_source_verified`| int | 0 / 1 | FRED second-source audit | 1 for S&P 500 (`us_sp500`) and Nikkei 225 (`jp_nikkei225`); 0 for single-source vendor series. |
| `shock_replicated` | int | 0 / 1 | Replication audit | 1 for replicated Tier 1 HF OIS and Tier 2 clean sovereign yield proxies. |
| `policy_verified` | int | 0 / 1 | Official CB decision lists | 1 for G6 central banks and peacetime CBR; 0 for unverified emerging market series. |
| `proxy_type` | string | `cash_benchmark` / `etf_proxy` | Instrument classification | Cash equity index vs ETF proxy. |
| `analysis_ok` | int | 0 / 1 | Integrated row filter | Master quality flag: 1 if clean, verified, not ambiguous, not halted, and not embargo dropped. |
