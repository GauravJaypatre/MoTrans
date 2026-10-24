# Data Dictionary — MoTrans-15

Every column in the final output files is defined here. This document is the
authoritative reference for column names, types, units, and definitions.

---

## `data/final/panel_daily.parquet`

The main daily panel in **long format** (one row per date × country × index).

| Column | Type | Unit | Definition | Source |
|---|---|---|---|---|
| `date` | `date` | — | Trading date on the local exchange calendar | Exchange calendars |
| `country` | `str` | — | ISO 3166-1 alpha-2 code (UK = `GB`); `EA` = euro-area-wide series | Design spec |
| `index_id` | `str` | — | Unique identifier for the index series (e.g. `us_sp500`, `de_dax`) | Source registry |
| `index_class` | `str` | — | One of: `broad`, `banks`, `smallcap` | Design spec |
| `level_local` | `float64` | index points | Daily closing level in local currency (price index, not total return) | yfinance / source |
| `ret_local` | `float64` | log return | Daily log return: ln(P_t / P_{t−1}) in local currency | Computed |
| `ret_usd` | `float64` | log return | Daily log return denominated in USD (using daily FX) | Computed from FX + ret_local |
| `yield_1y` | `float64` | percent | 1-year government yield (CA: 2-year; FR/IT/ES: euro-area curve); empty if older than 7 days | National sources (DECISION-016) |
| `fx_lcu_per_usd` | `float64` | local per USD | Units of local currency per 1 USD (US = 1) | BIS WS_XRU |
| `cpi` | `float64` | index | Consumer price index for month m, usable from the first day of month m+2 (DECISION-016) | BIS WS_LONG_CPI |
| `valuation` | `float64` | ratio | Empty: no free historical P/E or earnings-yield source (ISS-021) | — |
| `split_tag` | `str` | — | Sample split label: `train` (≤2019-12-31), `crisis` (2020-01-01–2021-12-31), `blind_test` (≥2022-01-01) | Date-based rule (`src.split_tag()`) |
| `russia_post_feb2022` | `int8` | flag | 1 from 2022-02-24 onward for Russia rows; 0 otherwise | Date-based rule |
| `halt_flag` | `int8` | flag | 1 on Moscow Exchange sessions 24 Feb - 31 Mar 2022 with no index value (prices empty). Missing data, NOT zero returns. | MOEX ISS history + XMOS calendar |
| `ret_spans_halt` | `int8` | flag | 1 on the first return after a halt (it spans the whole halt) | Computed |
| `ticker`, `source` | `str` | — | Ticker / index code and data provider | Source registry |
| `policy_rate` | `float64` | percent | Central bank policy rate as of the date | BIS WS_CBPOL |
| `vol_realized_20d` | `float64` | annualised | Std. dev. of the broad index's last 20 daily log returns x sqrt(252) (EA: DAX) | Computed |
| `vol_implied` | `float64` | index points | VIX for US rows; empty elsewhere | CBOE via Yahoo |
| `ind_prod` | `float64` | index | Industrial production (SA) for month m, usable from month m+2 | OECD STES |
| `exdiv_flag`, `stale_flag`, `outlier_flag` | `int8` | flag | ETF ex-dividend day, ETF zero volume, abs return > 10% | Computed |

---

## `data/final/events.parquet`

One row per **(decision × reacting country × reacting index)**.

| Column | Type | Unit | Definition |
|---|---|---|---|
| `event_id` | `str` | — | Unique event identifier (e.g. `fed_2022-03-16`) |
| `regime` | `str` | — | Central bank code: `Fed`, `ECB`, `PBoC`, `BoJ`, `BoE`, `CBR`, `BoC`, `BCB`, `Banxico`, `RBA`, `BoK`, `RBI` |
| `country` | `str` | — | ISO 3166-1 alpha-2 code of the reacting market's country |
| `index_id` | `str` | — | Identifier of the reacting index (matches `panel_daily.index_id`) |
| `announce_ts_utc` | `datetime64[ns, UTC]` | UTC | Exact announcement timestamp in UTC |
| `reacting_session_date` | `date` | — | First session of this exchange closing after `window_start_utc` (DECISION-013) |
| `baseline_date` | `date` | — | Last session closing at or before `window_start_utc`; returns are measured from its close |
| `timing_ambiguous` | `int8` | flag | 1 if `window_end_utc` would give a different reacting session (use h ≥ 3; robustness without) |
| `decision` | `str` | — | `hike`, `cut`, or `hold` |
| `size_bp` | `int16` | basis points | Size of the rate change (0 for holds) |
| `new_rate_pct` | `float64` | percent | New policy rate after the decision |
| `scheduled` | `bool` | — | `True` if scheduled meeting; `False` if emergency/unscheduled |
| `shock_std` | `float64` | standard deviations | Standardized shock (1 SD = 1 SD of that shock source). NaN until Phase D. |
| `shock_std_w` | `float64` | standard deviations | Winsorized standardized shock, capped strictly at [-4.0, +4.0] SD (DECISION-021). |
| `shock_grade` | `str` | — | Quality grade: `A` (clean public surprise), `B` (reasonable proxy), `C` (weak). Populated in Phase D. |
| `shock_usable` | `int8` | flag | 1 if `shock_grade` in {A, B} AND `shock_std` is finite and non-null; 0 for Grade C / missing shock (DECISION-021). |
| `shock_primary` | `int8` | flag | 1 for clean analysis cases; 0 for BoJ ZIRP/YCC, CBR post-Feb 2022, PBoC, and unusable shocks (DECISION-021). |
| `shock_proxy_tenor` | `str` | — | Tenor of sovereign yield proxy (e.g. `1Y`, `2Y`); empty if no proxy used (DECISION-021). |
| `shock_quality_flag` | `str` | — | Quality caveats; e.g. `low_sensitivity_zero_lower_bound`, `structural_break_ukraine_sanctions`, `tenor_2y_proxy_policy_transmission` (DECISION-021). |
| `clr_1` | `float64` | log return | Cumulative log return over 1 trading day after the reacting session |
| `clr_3` | `float64` | log return | Cumulative log return over 3 trading days after the reacting session |
| `clr_5` | `float64` | log return | Cumulative log return over 5 trading days after the reacting session |
| `clr_20` | `float64` | log return | Cumulative log return over 20 trading days after the reacting session |
| `clr_60` | `float64` | log return | Cumulative log return over 60 trading days after the reacting session |
| `clr_pre5` | `float64` | log return | Cumulative log return over 5 trading days BEFORE the reacting session (pre-event window for placebo use) |
| `split_tag` | `str` | — | Sample split label (same rule as panel_daily) |
| `time_quality` | `str` | — | `exact`, `approximate`, or `unknown`; from the decision table |
| `window_start_utc`, `window_end_utc` | `str` | UTC ISO | Earliest / latest possible announcement time (DECISION-013/020) |
| `analysis_ready_timing` | `int8` | flag | 1 if `timing_ambiguous == 0` AND `time_quality` in {exact, approximate} AND `reacting_session_date >= decision_date`; 0 otherwise. Rows with 0 are kept; use this flag to restrict to the unambiguous clean subset (DECISION-020). |

> **Naming convention:** `clr` = cumulative log return. These are NOT called
> "cumulative abnormal returns" (CAR) because no benchmark model has been
> chosen at this stage (see DECISION-006).

---

## `data/final/shocks.parquet`

One row per **(regime × decision date)**. Built in Phase D.

| Column | Type | Unit | Definition |
|---|---|---|---|
| `event_id` | `str` | — | Matches `events.event_id` |
| `regime` | `str` | — | Central bank code |
| `decision_date` | `date` | — | Date of the policy decision |
| `announce_ts_utc` | `datetime64[ns, UTC]` | UTC | Exact announcement timestamp |
| `decision` | `str` | — | `hike`, `cut`, or `hold` |
| `size_bp` | `int16` | basis points | Rate change size |
| `shock_raw` | `float64` | source units | Raw shock value (surprise in source units) |
| `shock_std` | `float64` | SD | raw / within-regime training-period (to 2019) SD of the same source; HF where available, else proxy (DECISION-018, DECISION-022) |
| `shock_std_peer_scale` | `float64` | SD | Peer-scale standardized shock: for BoJ post-exit events, rescaled by peer DM training SD (ECB Bund 4.48 bp); identical to `shock_std` for other regimes (DECISION-022) |
| `shock_std_w` | `float64` | SD | Winsorized standardized shock, capped strictly at [-4.0, +4.0] SD (DECISION-021) |
| `shock_source` | `str` | — | Source of the shock (e.g. "HF surprise series", "1Y yield change proxy") |
| `shock_grade` | `str` | — | A / B / C with written justification in `docs/shock_validation.md` |
| `shock_measure_type` | `str` | — | `hf_ois` for high-frequency surprise (Grade A); `yield_proxy` for sovereign yield change proxy (Grade B); empty for Grade C (NEW 1) |
| `shock_tier` | `Int64` | tier | 1 for consensus high-frequency intraday OIS/futures surprise (`hf_ois`, Grade A); 2 for daily sovereign yield change proxy (`yield_proxy`, Grade B); `<NA>` for Grade C (TIERS requirement). Headline blind test uses Tier 1 only; Tier 2 is secondary transfer test. |
| `shock_usable` | `int8` | flag | 1 if `shock_grade` in {A, B} AND `shock_std` is finite and non-null; 0 for Grade C / missing shock (DECISION-021). |
| `shock_primary` | `int8` | flag | 1 for primary clean analysis cases; 0 for all BoJ (pre-registered baseline rule), CBR post-Feb 2022, PBoC, and unusable shocks (DECISION-021, DECISION-022). |
| `shock_primary_rescaled` | `int8` | flag | 1 for labeled sensitivity analysis cases admitting post-exit BoJ events under peer scaling; 0 for BoJ ZIRP, CBR post-Feb 2022, PBoC, and unusable shocks (DECISION-022). |
| `shock_proxy_tenor` | `str` | — | Tenor of sovereign yield proxy (e.g. `1Y`, `2Y`); empty if no proxy used (DECISION-021). |
| `shock_quality_flag` | `str` | — | Quality caveats; e.g. `low_sensitivity_zero_lower_bound`, `structural_break_ukraine_sanctions`, `tenor_2y_proxy_policy_transmission` (DECISION-021). |
| `overlap_1d`, `overlap_3d`, `overlap_5d`, `overlap_20d`, `overlap_60d` | `int8` | flag | 1 if at least one other central bank policy decision occurs within the trading horizon window of $W \in \{1, 3, 5, 20, 60\}$ days; 0 otherwise (OVERLAP requirement). |
| `overlap_count_1d`, `overlap_count_3d`, `overlap_count_5d`, `overlap_count_20d`, `overlap_count_60d` | `int16` | count | Number of other policy decisions from any regime occurring within the trading horizon window of $W \in \{1, 3, 5, 20, 60\}$ days (OVERLAP requirement). |
| `event_type` | `str` | — | As in the decision table |
| `shock_hf_raw`, `shock_hf_std` | `float64` | bp / SD | High-frequency surprise (Fed MPS, ECB OIS 1Y) and its standardised value |
| `shock_proxy_raw`, `shock_proxy_std` | `float64` | bp / SD | 1-year or 2-year yield change proxy and its standardised value |
| `split_tag` | `str` | — | Sample split label |

---

## `data/final/statements.parquet`

One row per **central-bank statement** (920 rows). Built in Phase E (DECISION-019). Hand-label sample: `docs/hand_label_sample.csv` (same columns plus five empty label columns).

| Column | Type | Unit | Definition |
|---|---|---|---|
| `event_id` | `str` | — | Matches `events.event_id` |
| `regime` | `str` | — | Central bank code (Fed, ECB, BoJ, RBI) |
| `decision_date` | `date` | — | Date of the associated policy decision |
| `decision` | `str` | — | hike / cut / hold / unclassified, from the decision table |
| `pub_ts_utc` | `datetime64[ns, UTC]` | UTC | Publication timestamp of the statement |
| `source_url` | `str` | — | URL of the original statement |
| `language` | `str` | — | Language of the statement (e.g. `en`, `ja`) |
| `retrieval_utc` | `datetime64[ns, UTC]` | UTC | When the statement was retrieved |
| `text` | `str` | — | Full text of the statement |
| `word_count` | `int32` | words | Word count of the statement text |

---

## `data/final/analysis_tier1.parquet`

One row per **(Tier 1 decision × reacting index)**.
This table represents the primary headline analysis sample for high-frequency monetary policy shocks (Fed consensus MPS from Bauer-Swanson 2023, and ECB EA-MPD 1-year OIS monetary surprise from Altavilla et al. 2019). All macroeconomic and financial controls are merged strictly where `available_from <= decision_date` with no look-ahead.

Total rows: **15,805** across 494 decisions (ECB: 292 decisions, 9,177 rows; Fed: 202 decisions, 6,628 rows).

| Column | Type | Unit | Definition |
|---|---|---|---|
| `event_id` | `str` | — | Unique identifier for the event-index observation (e.g. `Fed_2008-01-22_us_sp500`) |
| `regime` | `str` | — | Central bank regime: `Fed` or `ECB` |
| `decision_date` | `str` | ISO date | Official announcement date (`YYYY-MM-DD`) |
| `event_type` | `str` | — | Meeting type: `scheduled_meeting`, `unscheduled_meeting` |
| `scheduled` | `bool` | — | `True` for scheduled calendar meetings; `False` for unscheduled/emergency actions |
| `decision` | `str` | — | Policy action: `hike`, `cut`, or `hold` |
| `size_bp` | `float64` | basis points | Policy rate change in basis points |
| `new_rate_pct` | `float64` | percent | Target policy rate level following announcement |
| `country` | `str` | — | ISO 2-letter country code of the reacting equity index |
| `index_id` | `str` | — | Identifier of reacting equity index (e.g. `us_sp500`, `de_dax`) |
| `index_class` | `str` | — | Equity asset class: `broad`, `banks`, or `smallcap` |
| `home_market` | `int8` | flag | 1 if equity index is in the home economy of the central bank; 0 if cross-border |
| `time_quality` | `str` | — | Quality of announcement timestamp: `exact`, `approximate`, `unknown` |
| `announce_ts_utc` | `datetime64[ns, UTC]` | UTC | Exact UTC timestamp of monetary policy announcement |
| `baseline_date` | `date` | — | Date of pre-announcement baseline closing price |
| `reacting_session_date` | `date` | — | Date of first exchange trading session reacting to announcement |
| `announce_in_session` | `int8` | flag | 1 if announcement occurred during exchange trading hours; 0 otherwise |
| `timing_ambiguous` | `int8` | flag | 1 if uncertainty in release window shifts reacting trading session |
| `analysis_ready_timing` | `int8` | flag | 1 if announcement timing is verified for event-study use; 0 otherwise |
| `shock_std` | `float64` | standard deviations | High-frequency monetary surprise standardized by train-period standard deviation |
| `shock_std_w` | `float64` | standard deviations | Standardized surprise winsorized at ±4.0 standard deviations |
| `shock_measure_type` | `str` | — | Type of shock measure: `mps_consensus_hf` (Fed) or `ois_1y_monetary_hf` (ECB) |
| `shock_tier` | `int64` | — | Shock quality tier: 1 (Consensus high-frequency intraday surprise) |
| `shock_grade` | `str` | — | Shock quality grade: `A` |
| `shock_source` | `str` | — | Source of high-frequency series (FRBSF Bauer-Swanson or EA-MPD Altavilla et al.) |
| `shock_usable` | `int8` | flag | 1 if shock is non-null and verified usable for econometric estimation |
| `shock_primary` | `int8` | flag | 1 for primary baseline specification |
| `shock_secondary` | `int8` | flag | 1 for secondary sensitivity specification (0 for Tier 1) |
| `shock_primary_rescaled` | `int8` | flag | 1 for extended primary sample |
| `shock_proxy_tenor` | `str` | — | Empty for Tier 1 (HFI shocks use intraday futures/OIS) |
| `split_tag` | `str` | — | Sample split: `train` (≤2019-12-31), `crisis` (2020-2021), `blind_test` (≥2022-01-01) |
| `clr_1` | `float64` | log return | 1-day cumulative log return from baseline to reacting session close |
| `clr_3` | `float64` | log return | 3-day cumulative log return across reacting window |
| `clr_5` | `float64` | log return | 5-day cumulative log return across reacting window |
| `clr_20` | `float64` | log return | 20-day cumulative log return across reacting window |
| `clr_60` | `float64` | log return | 60-day cumulative log return across reacting window |
| `overlap_1d` ... `overlap_60d` | `int8` | flag | 1 if another central bank policy decision occurs within forward [t, t+W-1] window |
| `overlap_count_1d` ... `overlap_count_60d` | `int64` | count | Total count of overlapping foreign/domestic central bank decisions in forward window |
| `ctrl_cpi` | `float64` | index level | Most recently published monthly CPI for country where `available_from <= decision_date` (max age 62 days) |
| `ctrl_ind_prod` | `float64` | index level | Most recently published Industrial Production index where `available_from <= decision_date` (max age 62 days) |
| `ctrl_policy_rate` | `float64` | percent | Local central bank policy rate as-of decision date (max age 7 days) |
| `ctrl_fx_lcu_per_usd` | `float64` | local per USD | Local currency exchange rate per USD as-of decision date (US = 1.0; max age 7 days) |
| `ctrl_yield_1y` | `float64` | percent | Local 1-year benchmark sovereign yield as-of decision date (max age 7 days) |
| `ctrl_yield_2y` | `float64` | percent | Local 2-year benchmark sovereign yield as-of decision date (AU, CA, CN; max age 7 days) |
| `ctrl_yield_short` | `float64` | percent | Composite short benchmark sovereign yield (1Y where available, else 2Y) |
| `ctrl_vix` | `float64` | index points | Global CBOE VIX close as-of decision date (max age 7 days) |

---

## `data/final/analysis_tier2_primary.parquet`

One row per **(Tier 2 rate-change decision × reacting index)** where `analysis_ready_timing == 1` and `shock_primary == 1`.
This table represents the primary out-of-sample transfer evaluation sample evaluating whether sovereign yield changes proxy monetary surprises on rate-change days. Rate changes carry strong, verified policy signal ($VR = 3.8\text{ to }7.2$). Holds are excluded from the primary sample because daily yield variance on hold days is indistinguishable from non-meeting noise ($VR \approx 1.0$). Central banks without timing evidence or under pegs (BoJ ZIRP/YCC, PBoC, pre-2016 BoE, pre-2013 BoC/CBR) are excluded.

Total rows: **6,297** across 176 rate-change decisions (RBA: 71, CBR: 41, BoC: 29, BoE: 25, Fed: 8, ECB: 2).

Columns match `analysis_tier1.parquet` exactly, with:
- `shock_tier`: 2
- `shock_grade`: `B`
- `shock_measure_type`: `yield_proxy`
- `shock_proxy_tenor`: Tenor of sovereign benchmark used (`1Y` for BoE, CBR, Fed, ECB; `2Y` for BoC, RBA).
- `shock_primary`: Strictly 1
- `decision`: Restricted strictly to `hike` or `cut`
- `analysis_ready_timing`: Strictly 1

---

## Interim (Phase B1): `data/interim/pilot_policy_decisions.csv`

One row per policy event for the pilot regimes (Fed, ECB, RBI, BoJ), 2000 to latest.
Built by `src/collect_policy.py` from files in `data/raw/` only.

| Column | Type | Definition |
|---|---|---|
| `regime` | `str` | `Fed`, `ECB`, `RBI`, `BoJ` |
| `decision_date` | `date` | Announcement date (local) |
| `event_type` | `str` | `scheduled_meeting`, `unscheduled_meeting`, or `unscheduled_rate_change` (a rate change with no listed meeting; dated by its effective date) |
| `scheduled` | `bool` | False for unscheduled meetings and unscheduled rate changes |
| `decision` | `str` | `hike` / `cut` / `hold`, from the sign of `size_bp` |
| `size_bp` | `int` | Change in the regime's policy rate attributed to the event (DECISION-011) |
| `new_rate_pct` | `float` | Policy rate after the event (percent) |
| `rate_basis` | `str` | Which rate `size_bp` and `new_rate_pct` refer to |
| `rate_mro`, `rate_dfr`, `rate_mlf` | `float` | ECB key rates after the decision (ECB rows only) |
| `announce_time_local` | `str` | `HH:MM` local time; empty when unknown |
| `timezone` | `str` | IANA time zone of `announce_time_local` |
| `announce_ts_utc` | `str` | ISO 8601 UTC timestamp; empty when unknown |
| `time_quality` | `str` | `exact` (time stated by the source), `approximate` (schedule or meeting end, see `time_source`), `unknown` |
| `time_source` | `str` | Where the time comes from |
| `window_start_utc`, `window_end_utc` | `str` | Earliest / latest possible release time (UTC), per DECISION-013; equal for exact times |
| `date_source` | `str` | Where the event date comes from |
| `source_url` | `str` | Official document for the event |
| `analysis_ready_timing` | `int8` | 1 if `time_quality` in {exact, approximate}; 0 for unknown (DECISION-020). Present in both `policy_decisions.csv` and `events.parquet`. |

## Interim (Phase B1): `data/interim/pilot_indices_daily.parquet`

Same columns as `panel_daily` (`date` … `ret_local`) plus:

| Column | Type | Definition |
|---|---|---|
| `ticker` | `str` | Yahoo ticker or NSE index name |
| `source` | `str` | `yfinance` or `niftyindices.com` |
| `exdiv_flag` | `int8` | 1 on an ETF ex-dividend day (price drop is a payout, not a market move) |
| `stale_flag` | `int8` | 1 on an ETF day with zero traded volume (close is not a fresh price) |
| `outlier_flag` | `int8` | 1 if \|ret_local\| > 0.10, for manual review (never deleted) |

## Interim (Phase B2): `data/interim/pilot_events.parquet`

One row per (policy event × pilot series). Columns as in `events.parquet` above, plus:

| Column | Type | Definition |
|---|---|---|
| `home_market` | `int8` | 1 if the series is in the regime's own market |
| `event_type`, `time_quality`, `window_start_utc`, `window_end_utc` | — | Copied from the decision table |
| `announce_in_session` | `int8` | 1 if the window starts while this market is open |
| `baseline_obs_date`, `react_obs_date` | `date` | Index observations actually used for the baseline and the reaction |
| `react_obs_gap` | `int8` | 1 if the index has no value on the reacting session (next observation used) |
| `stale_on_react` | `int8` | ETF reacting observation had zero volume |
| `exdiv_in_clr5` | `int8` | An ETF ex-dividend day falls inside the 5-observation window |

---

## `data/raw/MANIFEST.csv`

Provenance manifest for every raw file download. Tracked in git.

| Column | Type | Definition |
|---|---|---|
| `file_path` | `str` | Relative path from repo root (e.g. `data/raw/us_sp500_daily.csv`) |
| `source` | `str` | Data source name (e.g. `yfinance`, `FRED`) |
| `url_or_api` | `str` | Exact URL or API endpoint used |
| `series_id` | `str` | Ticker or series identifier (e.g. `^GSPC`, `DFEDTARU`) |
| `retrieval_utc` | `str` | ISO 8601 UTC timestamp of download |
| `licence` | `str` | Licence or terms of service |
| `sha256` | `str` | SHA-256 hex digest of the downloaded file |
| `notes` | `str` | Any additional notes |
