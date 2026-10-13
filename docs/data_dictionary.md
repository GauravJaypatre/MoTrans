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
| `shock_grade` | `str` | — | Quality grade: `A` (clean public surprise), `B` (reasonable proxy), `C` (weak). Populated in Phase D. |
| `clr_1` | `float64` | log return | Cumulative log return over 1 trading day after the reacting session |
| `clr_3` | `float64` | log return | Cumulative log return over 3 trading days after the reacting session |
| `clr_5` | `float64` | log return | Cumulative log return over 5 trading days after the reacting session |
| `clr_20` | `float64` | log return | Cumulative log return over 20 trading days after the reacting session |
| `clr_60` | `float64` | log return | Cumulative log return over 60 trading days after the reacting session |
| `clr_pre5` | `float64` | log return | Cumulative log return over 5 trading days BEFORE the reacting session (pre-event window for placebo use) |
| `split_tag` | `str` | — | Sample split label (same rule as panel_daily) |

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
| `shock_std` | `float64` | SD | Standardized shock (within-source z-score) |
| `shock_source` | `str` | — | Source of the shock (e.g. "HF surprise series", "1Y yield change proxy") |
| `shock_grade` | `str` | — | A / B / C with written justification in `docs/shock_validation.md` |
| `split_tag` | `str` | — | Sample split label |

---

## `data/final/statements.parquet`

One row per **central-bank statement**. Built in Phase E.

| Column | Type | Unit | Definition |
|---|---|---|---|
| `event_id` | `str` | — | Matches `events.event_id` |
| `regime` | `str` | — | Central bank code |
| `decision_date` | `date` | — | Date of the associated policy decision |
| `pub_ts_utc` | `datetime64[ns, UTC]` | UTC | Publication timestamp of the statement |
| `source_url` | `str` | — | URL of the original statement |
| `language` | `str` | — | Language of the statement (e.g. `en`, `ja`) |
| `retrieval_utc` | `datetime64[ns, UTC]` | UTC | When the statement was retrieved |
| `text` | `str` | — | Full text of the statement |
| `word_count` | `int32` | words | Word count of the statement text |

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
