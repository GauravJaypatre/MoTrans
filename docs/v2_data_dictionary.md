# MoTrans-15 v2.0 Data Dictionary

**Release**: `v2.0-data-freeze`  
**Base Population**: 2010–2026 Policy Announcements, Daily Market Prices, and Controls  
**File Formats**: Apache Parquet (`.parquet`) and Comma-Separated Values (`.csv`)  
**Parent Confirmatory Release**: `v1.0-data-freeze` (permanently locked and preserved)  
**Date of Freeze**: 2026-10-25  

---

## 1. Overview of Tables in `data/v2/`

| Table Name | File Path | Primary Entity | Rows | Description |
| :--- | :--- | :--- | :---: | :--- |
| **Tier 1 Analysis Table** | [`data/v2/analysis_tier1_2010plus.parquet`](file:///c:/Users/HP/OneDrive/المستندات/Projects/MoTrans/data/v2/analysis_tier1_2010plus.parquet) | Event $\times$ Index | 9,732 | Consensus high-frequency monetary policy surprises for Fed (FRBSF Bauer-Swanson) and ECB (EA-MPD OIS 1Y). Both rate changes and scheduled holds included. |
| **Tier 2 Primary Analysis Table** | [`data/v2/analysis_tier2_primary_2010plus.parquet`](file:///c:/Users/HP/OneDrive/المستندات/Projects/MoTrans/data/v2/analysis_tier2_primary_2010plus.parquet) | Event $\times$ Index | 7,643 | Clean sovereign benchmark yield proxies (1Y/2Y sovereign bond yield changes) for policy rate changes (hikes and cuts) across BoE, BoC, RBA, CBR, and post-truncation Fed/ECB. |
| **Secondary Holds Table** | [`data/v2/secondary_holds_2010plus.parquet`](file:///c:/Users/HP/OneDrive/المستندات/Projects/MoTrans/data/v2/secondary_holds_2010plus.parquet) | Event $\times$ Index | 15,895 | Scheduled policy holds for Tier 2 regimes where daily yield changes are secondary proxies (separated from primary rate changes to avoid attenuation bias). |
| **Daily Index Panel** | [`data/v2/panel_2010plus.parquet`](file:///c:/Users/HP/OneDrive/المستندات/Projects/MoTrans/data/v2/panel_2010plus.parquet) | Trading Date $\times$ Index | 156,248 | Daily closing prices, arithmetic and log returns, local currency FX, daily policy rate, 1Y yield, realized/implied volatility, and data quality flags for 38 equity indices. |
| **Sensitivity Table (Macro Revisions)** | [`data/v2/sensitivity_macro_revision_2010plus.parquet`](file:///c:/Users/HP/OneDrive/المستندات/Projects/MoTrans/data/v2/sensitivity_macro_revision_2010plus.parquet) | Event $\times$ Index | 17,375 | All primary decisions (Tier 1 and Tier 2) with OECD Industrial Production (`ctrl_ind_prod`) attached to test robustness against retrospective revision noise. |

---

## 2. Variable Definitions & Schemas

### 2.1 Identifiers & Policy Event Metadata

| Column | Type | Units / Range | Description |
| :--- | :--- | :--- | :--- |
| `event_id` | string | `regime_YYYY-MM-DD` | Unique policy announcement identifier (e.g. `fed_2022-03-16`, `cbr_2014-04-25`). |
| `regime` | string | `{Fed, ECB, BoE, BoC, RBA, CBR, BoJ, ...}` | Central bank institution responsible for the policy decision. |
| `decision_date` | string | `YYYY-MM-DD` | Official calendar announcement date on which the policy statement was released. |
| `v1_split_tag` | string | `{train, val, blind_test, crisis}` | Reference sample split tag from v1 release. |
| `final_holdout` | int | `{0, 1}` | Binary indicator for permanently locked holdout test sample (1 for decisions $\ge$ 2022-01-01; 0 for train/validation). |
| `event_type` | string | `{scheduled_meeting, unscheduled_rate_change}` | Meeting categorization. |
| `scheduled` | bool | `{True, False}` | Whether the decision occurred at a pre-scheduled committee meeting. |
| `decision` | string | `{hike, cut, hold}` | Direction of policy rate change. |
| `size_bp` | float | Basis points | Policy rate change magnitude in basis points ($1\text{ bp} = 0.01\%$). |
| `policy_rate` | float | Percent per annum | Central bank policy target rate level following the decision (e.g. 4.60). |
| `zero_lower_bound` | int | `{0, 1}` | Indicator equal to 1 if `policy_rate` $\le 0.25\%$, 0 otherwise. |
| `regime_state` | string | `{tightening, easing, hold}` | Policy regime phase (`tightening` for hike, `easing` for cut, `hold` for pause). |

### 2.2 Index & Market Dimensions

| Column | Type | Units / Range | Description |
| :--- | :--- | :--- | :--- |
| `country` | string | ISO 2-letter | Country / currency area of the equity index (e.g. `US`, `DE`, `JP`, `GB`, `AU`). |
| `index_id` | string | Ticker code | Specific index series code (e.g. `us_sp500`, `jp_nikkei225`, `au_asx200`). |
| `index_class` | string | `{broad_market, large_cap, banking, small_cap}` | Sectoral/size classification of the index. |
| `proxy_type` | string | `{cash_benchmark, etf_proxy}` | Instrument structure. Identifies tradeable ETF proxies subject to tracking divergence. |
| `home_market` | int | `{0, 1}` | Binary indicator equal to 1 if the index is in the jurisdiction of the central bank. |

### 2.3 Announcement Timing & Session Alignment

| Column | Type | Units / Range | Description |
| :--- | :--- | :--- | :--- |
| `time_quality` | string | `{exact, approximate, unknown}` | Provenance precision of the recorded announcement time. |
| `announce_ts_utc` | string | ISO UTC timestamp | Standardized UTC timestamp of policy statement release. |
| `baseline_date` | date | `YYYY-MM-DD` | Date of the last trading session whose exchange close strictly preceded `announce_ts_utc`. |
| `reacting_session_date` | date | `YYYY-MM-DD` | Date of the first trading session whose exchange close strictly succeeded `announce_ts_utc`. |
| `announce_in_session` | int | `{0, 1}` | Indicator equal to 1 if statement release occurred while the home exchange was open. |
| `timing_ambiguous` | int | `{0, 1}` | Indicator equal to 1 if window boundaries span multiple trading sessions. |
| `analysis_ready_timing` | int | `{0, 1}` | Quality gate: 1 if `timing_ambiguous == 0` and announcement time is verified. |

### 2.4 Monetary Policy Shocks

| Column | Type | Units / Range | Description |
| :--- | :--- | :--- | :--- |
| `shock_std` | float | Standard deviations | Standardized monetary policy surprise. Scaled strictly by within-regime training period standard deviation ($\text{SD}_{\le 2019}$); not de-meaned so 0 represents no surprise. |
| `shock_std_w` | float | $[-4.0, +4.0]$ | Winsorized standardized shock, bounded at $\pm 4.0\sigma$. |
| `shock_measure_type` | string | `{hf_ois, yield_proxy}` | Identification methodology (`hf_ois` for consensus intraday OIS/futures; `yield_proxy` for daily sovereign bond yield changes). |
| `shock_tier` | int | `{1, 2}` | Hierarchy tier (1 = consensus high-frequency; 2 = sovereign yield proxy). |
| `shock_grade` | string | `{A, B, C}` | Provenance grade (A = published intraday surprise; B = clean sovereign yield proxy; C = unverified). |
| `shock_source` | string | Source citation | Raw source file citation (e.g. `FRBSF Bauer-Swanson MPS`, `EA-MPD OIS 1Y`). |
| `shock_usable` | int | `{0, 1}` | 1 if shock is non-missing and meets quality standards for econometric estimation. |
| `shock_primary` | int | `{0, 1}` | Primary identification designator (Tier 1 clean events; Tier 2 rate changes). |
| `shock_secondary` | int | `{0, 1}` | Secondary identification designator (Tier 2 scheduled holds). |
| `shock_proxy_tenor` | string | `{1Y, 2Y}` | Tenor of the underlying sovereign benchmark yield proxy. |

### 2.5 Event Window Cumulative Log Returns ($clr_h$)

| Column | Type | Units / Formula | Description |
| :--- | :--- | :--- | :--- |
| `clr_1` | float | $\ln(P_{\text{react}}) - \ln(P_{\text{base}})$ | 1-session announcement reaction return. |
| `clr_3` | float | $\ln(P_{\text{react}+2}) - \ln(P_{\text{base}})$ | 3-session cumulative post-decision return. |
| `clr_5` | float | $\ln(P_{\text{react}+4}) - \ln(P_{\text{base}})$ | 5-session cumulative post-decision return. |
| `clr_20` | float | $\ln(P_{\text{react}+19}) - \ln(P_{\text{base}})$ | 20-session (1-month) cumulative post-decision return. |
| `clr_60` | float | $\ln(P_{\text{react}+59}) - \ln(P_{\text{base}})$ | 60-session (1-quarter) cumulative post-decision return. |

### 2.6 Overlap & Event Clustering Controls

| Column | Type | Range | Description |
| :--- | :--- | :--- | :--- |
| `overlap_1d` | int | `{0, 1}` | Indicator equal to 1 if another central bank announced within $\pm 1$ calendar day. |
| `overlap_3d` | int | `{0, 1}` | Indicator equal to 1 if another central bank announced within $\pm 3$ calendar days. |
| `overlap_5d` | int | `{0, 1}` | Indicator equal to 1 if another central bank announced within $\pm 5$ calendar days. |
| `overlap_20d` | int | `{0, 1}` | Indicator equal to 1 if another central bank announced within $\pm 20$ calendar days. |
| `overlap_60d` | int | `{0, 1}` | Indicator equal to 1 if another central bank announced within $\pm 60$ calendar days. |
| `overlap_count_hd` | int | $\ge 0$ | Count of distinct foreign central bank announcements within $\pm h$ calendar days. |

### 2.7 As-Of Macro & Financial Controls (Default Set)

All controls matched using conservative point-in-time rule: $\text{available\_from} \le \text{decision\_date}$ with zero lookahead bias.

| Column | Type | Units / Source | Description |
| :--- | :--- | :--- | :--- |
| `ctrl_cpi` | float | Year-over-year % | Consumer Price Index YoY rate. Availability verified $\ge 0$ days lag from official agency release calendars (BLS, Eurostat, ONS, ABS, SBJ). |
| `ctrl_yield_1y` | float | % per annum | 1-Year sovereign government benchmark yield as of decision date. |
| `ctrl_yield_short` | float | % per annum | Composite short yield (1Y sovereign yield where available; 2Y fallback for CA/AU/CN). |
| `ctrl_vix` | float | Index points | CBOE Volatility Index (VIX) closing level on or before decision date. |
| `ctrl_fx_lcu_per_usd` | float | LCU per USD | Exchange rate level expressed as local currency units per US Dollar (identically 1.0 for US). |
| `ctrl_policy_rate` | float | % per annum | Policy rate in effect immediately prior to announcement. |
| `ctrl_ind_prod` | float | Index (2015=100) | OECD Industrial Production. **Excluded from default tables**; retained strictly in `sensitivity_macro_revision_2010plus.parquet`. |

### 2.8 Data Quality & Verification Flags (V2 Addition)

| Column | Type | Range | Definition & Filtering Rule |
| :--- | :--- | :--- | :--- |
| `price_source_verified` | int | `{0, 1}` | 1 for `us_sp500` (verified against FRED within 1.2 bp); 0 for 37 single-source series. |
| `shock_verified` | int | `{0, 1}` | 1 for shocks verified by replication against saved raw data files. |
| `timing_verified_level` | string | `{event, convention, none}` | Timing provenance: `event` (statement header verified); `convention` (official period convention verified); `none` (unverified). |
| `policy_verified` | int | `{0, 1}` | 1 for official central-bank-audited policy decisions. |
| `analysis_ok` | int | `{0, 1}` | Primary quality filter. Equal to 0 if timing is unverified (`none`) for a primary decision, date is unverified, or event spans prolonged halts. Equal to 1 for clean analysis sample. |

---

## 3. Recommended Filter for Clean Empirical Estimation

To obtain the recommended clean estimation sample without lookahead contamination or unverified timing:

```python
import pandas as pd

df = pd.read_parquet("data/v2/analysis_tier1_2010plus.parquet")
clean_sample = df[
    (df["analysis_ok"] == 1) &
    (df["overlap_1d"] == 0) &
    (df["proxy_type"] == "cash_benchmark")
]
```
