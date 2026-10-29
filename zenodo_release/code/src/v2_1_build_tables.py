"""MoTrans-15 v2.1 / v2.1.1 Table Builder & Leakage Protection Pipeline.

Builds:
- data/v2_1/analysis_tier1.parquet
- data/v2_1/analysis_tier2_primary.parquet
- data/v2_1/secondary_holds.parquet
- data/v2_1/panel.parquet
- data/v2_1/sensitivity_macro_revision.parquet
- data/v2_1/post_window_2026.parquet
- data/v2_1/excluded_rows.parquet
- data/v2_1/folds.csv (with final_fit row)
- data/v2_1/release/ (release subset without licensed price levels)

Produces reports under outputs/v2_1/:
- split_counts.csv
- fold_counts.csv
- test_window_composition.csv
- row_membership.csv
- years_thin.csv
- analysis_ok_breakdown.csv
- decisions_by_regime_year_2010_2025.csv
"""

from __future__ import annotations

import datetime as dt
import shutil
import sys
from pathlib import Path
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.v2_1_config import (
    WINDOW_START,
    WINDOW_END,
    TRAIN_START,
    TRAIN_END,
    VAL_START,
    VAL_END,
    TEST_START,
    TEST_END,
    POST_WINDOW_START,
    EMBARGO_DAYS,
    FOLD_ORIGINS,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_FINAL = ROOT / "data" / "final"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_V2_1 = ROOT / "data" / "v2_1"
DATA_V2_1_RELEASE = DATA_V2_1 / "release"
OUTPUTS_V2_1 = ROOT / "outputs" / "v2_1"

DATA_V2_1.mkdir(parents=True, exist_ok=True)
DATA_V2_1_RELEASE.mkdir(parents=True, exist_ok=True)
OUTPUTS_V2_1.mkdir(parents=True, exist_ok=True)


def compute_counts(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Standard unified counting function used across all v2.1/v2.1.1 reports.
    
    Guarantees that decisions_count is strictly df['event_id'].nunique(),
    with consistent breakdown into hikes_count, cuts_count, holds_count,
    and event_rows_count.
    """
    records = []
    for keys, g in df.groupby(group_cols, observed=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        rec = dict(zip(group_cols, keys))
        decs = int(g["event_id"].nunique())
        hikes = int((g["decision"] == "hike").groupby(g["event_id"]).any().sum())
        cuts = int((g["decision"] == "cut").groupby(g["event_id"]).any().sum())
        holds = int((g["decision"] == "hold").groupby(g["event_id"]).any().sum())
        rows = int(len(g))
        rec["decisions_count"] = decs
        rec["hikes_count"] = hikes
        rec["cuts_count"] = cuts
        rec["holds_count"] = holds
        rec["event_rows_count"] = rows
        records.append(rec)
    return pd.DataFrame(records)


def build_v2_1_tables():
    print("=== Starting MoTrans-15 v2.1/v2.1.1 Dataset Build ===")
    
    # 1. Load source tables
    events = pd.read_parquet(DATA_FINAL / "events.parquet")
    policy = pd.read_csv(DATA_FINAL / "policy_decisions.csv", dtype={"decision_date": str})
    shocks = pd.read_parquet(DATA_FINAL / "shocks.parquet")
    panel = pd.read_parquet(DATA_FINAL / "panel_daily.parquet")
    ctrl = pd.read_parquet(DATA_INTERIM / "controls_long.parquet")

    # Exclude non-decision events (e.g. Fed Jackson Hole 2025-08-22 speech)
    events = events[events["event_type"] != "non_decision"].copy()
    policy = policy[policy["event_type"] != "non_decision"].copy()

    # Derive policy_rate and zero_lower_bound
    events["policy_rate"] = events["new_rate_pct"]
    events["zero_lower_bound"] = (events["policy_rate"] <= 0.25).astype(int)

    # Attach date_confidence from policy decisions
    if "date_confidence" in policy.columns:
        date_conf_map = policy[["event_id", "date_confidence"]].drop_duplicates().set_index("event_id")["date_confidence"].to_dict()
        events["date_confidence"] = events["event_id"].map(date_conf_map).fillna("high")
    else:
        events["date_confidence"] = "high"

    # 2. Attach macro controls respecting available_from <= decision_date
    print("--- Attaching As-Of Macro Controls ---")
    ctrl_clean = ctrl[ctrl["available_from"].notna()].copy()
    ctrl_clean["available_from"] = pd.to_datetime(ctrl_clean["available_from"]).dt.date
    ctrl_clean["date"] = pd.to_datetime(ctrl_clean["date"]).dt.date

    # Pre-index controls by (country, variable) using sorted arrays for instant searchsorted
    ctrl_indexed = {}
    for (country, var), g in ctrl_clean.groupby(["country", "variable"]):
        g_sorted = g.sort_values("available_from")
        ctrl_indexed[(country, var)] = (
            np.array(g_sorted["available_from"].tolist()),
            g_sorted["value"].to_numpy()
        )

    def get_asof_ctrl(country: str, var: str, decision_d: dt.date) -> float:
        entry = ctrl_indexed.get((country, var))
        if entry is None:
            return np.nan
        dates, vals = entry
        idx = int(np.searchsorted(dates, decision_d, side="right")) - 1
        if idx >= 0:
            return float(vals[idx])
        return np.nan

    events["d_date"] = pd.to_datetime(events["decision_date"]).dt.date
    unique_combos = events[["country", "d_date"]].drop_duplicates()

    ctrl_vars = ["cpi", "yield_1y", "yield_2y", "yield_short", "vix", "fx_lcu_per_usd", "policy_rate", "ind_prod"]
    asof_records = []
    for _, row in unique_combos.iterrows():
        c = row["country"]
        d = row["d_date"]
        rec = {"country": c, "d_date": d}
        for v in ctrl_vars:
            rec[f"ctrl_{v}"] = get_asof_ctrl(c, v, d)
        asof_records.append(rec)

    asof_df = pd.DataFrame(asof_records)
    events = events.merge(asof_df, on=["country", "d_date"], how="left")
    events = events.drop(columns=["d_date"])

    # 3. Add shock_raw_bp, shock_std, shock_std_legacy
    print("--- Adding Shock Raw BP and Descriptive Scales ---")
    shocks_map = shocks.set_index("event_id")
    
    # For CBR, robust scale MAD x 1.4826 from non-emergency events (13.3434 bp)
    # Legacy scale was 66.6249 bp
    cbr_train = shocks[(shocks["regime"] == "CBR") & 
                       (pd.to_datetime(shocks["decision_date"]).dt.date <= dt.date(2019, 12, 31)) &
                       (shocks["shock_proxy_raw"].notna())]
    cbr_non_emerg = cbr_train[cbr_train["decision_date"] != "2014-12-16"]
    cbr_med = float(np.median(cbr_non_emerg["shock_proxy_raw"].values))
    cbr_mad = float(np.median(np.abs(cbr_non_emerg["shock_proxy_raw"].values - cbr_med)))
    cbr_robust_scale = cbr_mad * 1.4826

    shock_raw_list = []
    shock_std_legacy_list = []
    shock_std_list = []

    for ev_id, reg, tier, s_type, s_std in zip(
        events["event_id"], events["regime"], events["shock_tier"], events["shock_measure_type"], events["shock_std"]
    ):
        if ev_id in shocks_map.index:
            s_row = shocks_map.loc[ev_id]
            if isinstance(s_row, pd.DataFrame):
                s_row = s_row.iloc[0]
            hf = s_row.get("shock_hf_raw")
            proxy = s_row.get("shock_proxy_raw")
            
            if pd.notna(tier) and tier == 1 and pd.notna(hf):
                raw = float(hf)
            elif pd.notna(proxy):
                raw = float(proxy)
            elif pd.notna(hf):
                raw = float(hf)
            else:
                raw = np.nan
        else:
            raw = np.nan

        shock_raw_list.append(raw)
        shock_std_legacy_list.append(s_std)

        if reg == "CBR" and pd.notna(raw):
            shock_std_list.append(round(raw / cbr_robust_scale, 6))
        else:
            shock_std_list.append(s_std)

    events["shock_raw_bp"] = shock_raw_list
    events["shock_std_legacy"] = shock_std_legacy_list
    events["shock_std"] = shock_std_list

    # 4. Backward-Looking Overlap Prior Controls (Predictive Use, No Lookahead)
    print("--- Adding Backward-Looking Overlap Prior Contamination Controls ---")
    bdate_range = pd.bdate_range("1999-01-01", "2026-12-31")
    pol_clean = policy[policy["event_type"] != "non_decision"].drop_duplicates("event_id").copy()
    pol_dates = pd.to_datetime(pol_clean["decision_date"]).to_numpy()
    pol_ids = pol_clean["event_id"].to_numpy()

    prior_cols = {}
    for W in (1, 3, 5, 20, 60):
        cnt_map = {}
        for d, eid in zip(pol_dates, pol_ids):
            prev_idx = int(np.searchsorted(bdate_range, d, side="left")) - 1
            start_idx = max(0, prev_idx - W + 1)
            start_b = bdate_range[start_idx]
            end_b = bdate_range[prev_idx]
            mask = (pol_dates >= start_b) & (pol_dates <= end_b) & (pol_ids != eid)
            cnt_map[eid] = int(mask.sum())
        prior_cols[f"overlap_prior_count_{W}d"] = cnt_map
        prior_cols[f"overlap_prior_{W}d"] = {k: int(v > 0) for k, v in cnt_map.items()}

    for cname, cdict in prior_cols.items():
        events[cname] = events["event_id"].map(cdict).fillna(0).astype(int)

    # 5. Compute 60-day observation date and embargo drop
    print("--- Computing 60-Day Embargo and Drop Flags ---")
    dates_by_idx = {sid: np.array(g.sort_values("date")["date"].tolist()) for sid, g in panel.groupby("index_id")}

    unique_pairs = events[["index_id", "react_obs_date"]].drop_duplicates()
    obs_60_dict = {}
    for _, row in unique_pairs.iterrows():
        sid = row["index_id"]
        react = row["react_obs_date"]
        if pd.isna(react) or sid not in dates_by_idx:
            obs_60_dict[(sid, react)] = ""
            continue
        dlist = dates_by_idx[sid]
        r = int(np.searchsorted(dlist, react, side="left"))
        if r + 59 < len(dlist):
            obs_60_dict[(sid, react)] = str(dlist[r + 59])
        else:
            obs_60_dict[(sid, react)] = ""

    events["obs_60_date"] = [obs_60_dict.get((s, r), "") for s, r in zip(events["index_id"], events["react_obs_date"])]
    max_obs_map = events.groupby("event_id")["obs_60_date"].max().to_dict()

    # Assign final_split by decision date
    def assign_split(date_str: str) -> str:
        d = dt.date.fromisoformat(str(date_str)[:10])
        if d < dt.date(2010, 1, 1):
            return "pre_window"
        if d <= dt.date(2021, 12, 31):
            return "train"
        if d <= dt.date(2023, 12, 31):
            return "validation"
        if d <= dt.date(2025, 12, 31):
            return "test"
        return "post_window"

    events["v1_split_tag"] = events.get("split_tag", "")
    events["final_split"] = events["decision_date"].apply(assign_split)

    # 60-day embargo drop: drop events reaching across split boundary
    def check_embargo(row):
        d = dt.date.fromisoformat(str(row["decision_date"])[:10])
        obs60 = max_obs_map.get(row["event_id"], "")
        sp = row["final_split"]
        
        if sp == "train":
            bound = dt.date(2022, 1, 1)
            if (obs60 and obs60 >= "2022-01-01") or d >= bound - dt.timedelta(days=EMBARGO_DAYS):
                return 1
        elif sp == "validation":
            bound = dt.date(2024, 1, 1)
            if (obs60 and obs60 >= "2024-01-01") or d >= bound - dt.timedelta(days=EMBARGO_DAYS):
                return 1
        elif sp == "test":
            bound = dt.date(2026, 1, 1)
            if (obs60 and obs60 >= "2026-01-01") or d >= bound - dt.timedelta(days=EMBARGO_DAYS):
                return 1
        return 0

    events["embargo_dropped"] = events.apply(check_embargo, axis=1)

    # 6. Assign Rolling-Origin Folds inside TRAIN + VALIDATION
    print("--- Assigning Rolling-Origin Development Folds ---")
    origins = [
        (1, dt.date(2016, 1, 1), dt.date(2017, 12, 31)),
        (2, dt.date(2018, 1, 1), dt.date(2019, 12, 31)),
        (3, dt.date(2020, 1, 1), dt.date(2021, 12, 31)),
        (4, dt.date(2022, 1, 1), dt.date(2023, 12, 31)),
    ]

    for fid, orig, val_end in origins:
        col = f"fold_{fid}"
        orig_str = str(orig)
        def assign_f(row):
            d = dt.date.fromisoformat(str(row["decision_date"])[:10])
            obs60 = max_obs_map.get(row["event_id"], "")
            if d < orig:
                if (obs60 and obs60 >= orig_str) or d >= orig - dt.timedelta(days=EMBARGO_DAYS):
                    return "unused"  # embargoed before validation origin
                return "train"
            elif orig <= d <= val_end:
                return "val"
            return "unused"

        events[col] = events.apply(assign_f, axis=1)

    # 7. QE / YCC Indicator (BoJ)
    def is_boj_qe_ycc(row):
        if row["regime"] != "BoJ":
            return 0
        d = dt.date.fromisoformat(row["decision_date"][:10])
        # QQE introduced 2013-04-04; YCC ended 2024-03-19
        return 1 if (dt.date(2013, 4, 4) <= d <= dt.date(2024, 3, 19)) else 0

    events["qe_ycc_indicator"] = events.apply(is_boj_qe_ycc, axis=1)

    # 8. Row-Quality Columns & Exclusion Reasons
    print("--- Deriving Row Quality & Exclusion Reasons ---")
    events["price_source_verified"] = events["index_id"].isin(["us_sp500", "jp_nikkei225"]).astype(int)
    events["shock_replicated"] = (events["shock_usable"].fillna(0).astype(int) == 1).astype(int)

    fed_event_dates = {
        "2016-01-27", "2016-03-16", "2016-06-15", "2016-12-14", "2017-03-15",
        "2018-03-21", "2019-07-31", "2020-01-29", "2022-03-16", "2026-09-16"
    }
    rba_event_dates = {"2026-09-29"}

    timing_level = []
    for reg, d_str in zip(events["regime"], events["decision_date"]):
        d = dt.date.fromisoformat(d_str[:10])
        if reg == "Fed" and d_str in fed_event_dates:
            timing_level.append("event")
        elif reg == "RBA" and d_str in rba_event_dates:
            timing_level.append("event")
        elif reg == "Fed":
            timing_level.append("convention")
        elif reg == "ECB":
            timing_level.append("convention")
        elif reg == "BoE" and d >= dt.date(2010, 1, 1):
            timing_level.append("convention")
        elif reg == "BoC" and d >= dt.date(2013, 1, 1):
            timing_level.append("convention")
        elif reg == "RBA" and d >= dt.date(2008, 1, 1):
            timing_level.append("convention")
        elif reg == "CBR" and dt.date(2013, 9, 13) <= d <= dt.date(2022, 2, 14):
            timing_level.append("convention")
        elif reg == "BoJ" and d >= dt.date(2010, 1, 1):
            timing_level.append("convention")
        else:
            timing_level.append("none")
    events["timing_verified_level"] = timing_level

    # policy_verified
    events["policy_verified"] = (
        events["regime"].isin(["Fed", "ECB", "BoE", "BoC", "RBA", "BoJ"]) |
        ((events["regime"] == "CBR") & (pd.to_datetime(events["decision_date"]).dt.date <= dt.date(2022, 2, 24)))
    ).astype(int)

    # proxy_type
    etf_proxies = {"ea_emu_smallcap_etf", "de_stoxx_banks_etf", "jp_topix_banks_etf", "kr_banks_etf", "jp_mothers_etf"}
    events["proxy_type"] = events["index_id"].apply(lambda sid: "etf_proxy" if sid in etf_proxies else "cash_benchmark")

    # analysis_ok: clean, verified, not ambiguous, not halted, not embargo dropped, shock usable if not BoJ
    is_moex_halt = (events["index_id"] == "ru_imoex") & (pd.to_datetime(events["decision_date"]).dt.date >= dt.date(2022, 2, 24))
    is_bad_shock = (events["regime"] != "BoJ") & (events["shock_usable"].fillna(0).astype(int) == 0)
    events["analysis_ok"] = (
        (events["policy_verified"] == 1) &
        (events["timing_verified_level"] != "none") &
        (events["timing_ambiguous"] == 0) &
        (~is_moex_halt) &
        (~is_bad_shock) &
        (events["embargo_dropped"] == 0)
    ).astype(int)

    # Exclusion reason for analysis_ok == 0
    def derive_exclusion_reason(row):
        if row["analysis_ok"] == 1:
            return "none"
        if row["embargo_dropped"] == 1:
            return "embargo_dropped"
        if row["regime"] in ["BCB", "Banxico", "RBI", "BoK", "PBoC"]:
            return "unverified_regime"
        if row["policy_verified"] == 0:
            return "policy_unverified"
        if row["timing_ambiguous"] == 1:
            return "timing_ambiguous"
        if row["timing_verified_level"] == "none":
            return "timing_unverified"
        if row["index_id"] == "ru_imoex" and str(row["decision_date"]) >= "2022-02-24":
            return "moex_halt"
        if row.get("shock_usable", 1) == 0:
            return "shock_unusable"
        return "unverified_quality"

    events["exclusion_reason"] = events.apply(derive_exclusion_reason, axis=1)

    # 9. Separate 2026 Post-Window Rows (Quarantined)
    print("--- Isolating 2026 Post-Window Rows ---")
    post_window_rows = events[events["final_split"] == "post_window"].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    post_window_rows.to_parquet(DATA_V2_1 / "post_window_2026.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'post_window_2026.parquet'}: {len(post_window_rows):,} rows ({post_window_rows['event_id'].nunique()} decisions quarantined).")

    # Filter window for analysis tables: 2010-01-01 to 2025-12-31
    events_window = events[events["final_split"].isin(["train", "validation", "test"])].copy()

    # Excluded rows companion file (analysis_ok == 0 in 2010-2025 window)
    excluded_rows = events_window[events_window["analysis_ok"] == 0].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    excluded_rows.to_parquet(DATA_V2_1 / "excluded_rows.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'excluded_rows.parquet'}: {len(excluded_rows):,} rows ({excluded_rows['event_id'].nunique()} decisions).")

    # Base columns for analysis tables
    analysis_cols = [
        "event_id", "regime", "decision_date", "final_split", "fold_1", "fold_2", "fold_3", "fold_4",
        "embargo_dropped", "v1_split_tag", "decision", "size_bp", "shock_raw_bp", "shock_std",
        "shock_std_legacy", "shock_measure_type", "shock_tier", "home_market", "index_id", "index_class",
        "clr_1", "clr_3", "clr_5", "clr_20", "clr_60",
        "overlap_1d", "overlap_3d", "overlap_5d", "overlap_20d", "overlap_60d",
        "overlap_count_1d", "overlap_count_3d", "overlap_count_5d", "overlap_count_20d", "overlap_count_60d",
        "overlap_prior_1d", "overlap_prior_3d", "overlap_prior_5d", "overlap_prior_20d", "overlap_prior_60d",
        "overlap_prior_count_1d", "overlap_prior_count_3d", "overlap_prior_count_5d", "overlap_prior_count_20d", "overlap_prior_count_60d",
        "policy_rate", "zero_lower_bound", "qe_ycc_indicator",
        "ctrl_vix", "ctrl_cpi", "ctrl_yield_1y", "ctrl_yield_2y", "ctrl_yield_short",
        "ctrl_fx_lcu_per_usd", "ctrl_policy_rate",
        "date_confidence", "time_quality", "timing_verified_level", "price_source_verified",
        "shock_replicated", "policy_verified", "proxy_type", "analysis_ok"
    ]

    # Table 1: analysis_tier1.parquet (Fed and ECB high-frequency shocks; analysis_ok == 1)
    t1_df = events_window[
        (events_window["shock_tier"] == 1) & 
        (events_window["shock_usable"] == 1) & 
        (events_window["analysis_ok"] == 1)
    ][analysis_cols].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    t1_df.to_parquet(DATA_V2_1 / "analysis_tier1.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'analysis_tier1.parquet'}: {len(t1_df):,} rows ({t1_df['event_id'].nunique()} decisions).")

    # Table 2: analysis_tier2_primary.parquet (Rate change decisions with proxy shocks; analysis_ok == 1)
    t2_df = events_window[
        (events_window["shock_tier"] == 2) & 
        (events_window["shock_primary"] == 1) & 
        (events_window["shock_usable"] == 1) & 
        (events_window["analysis_ok"] == 1)
    ][analysis_cols].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    t2_df.to_parquet(DATA_V2_1 / "analysis_tier2_primary.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'analysis_tier2_primary.parquet'}: {len(t2_df):,} rows ({t2_df['event_id'].nunique()} decisions).")

    # Table 3: secondary_holds.parquet (Scheduled hold decisions; analysis_ok == 1)
    sec_holds_df = events_window[
        (events_window["shock_tier"] == 2) & 
        (events_window["shock_secondary"] == 1) & 
        (events_window["decision"] == "hold") & 
        (events_window["analysis_ok"] == 1)
    ][analysis_cols].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    sec_holds_df.to_parquet(DATA_V2_1 / "secondary_holds.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'secondary_holds.parquet'}: {len(sec_holds_df):,} rows ({sec_holds_df['event_id'].nunique()} decisions).")

    # Table 4: panel.parquet (Daily panel for the 2010-2025 window)
    panel_window = panel[(panel["date"] >= dt.date(2010, 1, 1)) & (panel["date"] <= dt.date(2025, 12, 31))].sort_values(["index_id", "date"]).reset_index(drop=True)
    panel_window["final_split"] = panel_window["date"].astype(str).apply(assign_split)
    panel_window.to_parquet(DATA_V2_1 / "panel.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'panel.parquet'}: {len(panel_window):,} rows.")

    # Table 5: sensitivity_macro_revision.parquet (ind_prod only; analysis_ok == 1)
    sens_cols = analysis_cols + ["ctrl_ind_prod"]
    sens_df = events_window[
        (events_window["shock_tier"].isin([1, 2])) & 
        (events_window["shock_primary"] == 1) & 
        (events_window["analysis_ok"] == 1)
    ][sens_cols].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    sens_df.to_parquet(DATA_V2_1 / "sensitivity_macro_revision.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'sensitivity_macro_revision.parquet'}: {len(sens_df):,} rows ({sens_df['event_id'].nunique()} decisions).")

    # Combined analysis tables for unified fold counting and refitting
    all_analysis_tables = pd.concat([t1_df, t2_df, sec_holds_df], ignore_index=True)

    # 10. Create data/v2_1/folds.csv (with final_fit row)
    print("--- Creating data/v2_1/folds.csv ---")
    fold_summary = []
    for fid, orig, val_end in origins:
        fcol = f"fold_{fid}"
        train_sub = all_analysis_tables[all_analysis_tables[fcol] == "train"]
        val_sub = all_analysis_tables[all_analysis_tables[fcol] == "val"]
        
        train_decs = train_sub["event_id"].nunique()
        val_decs = val_sub["event_id"].nunique()

        train_hikes = (train_sub["decision"] == "hike").groupby(train_sub["event_id"]).any().sum()
        val_hikes = (val_sub["decision"] == "hike").groupby(val_sub["event_id"]).any().sum()

        t1_hikes = ((train_sub["shock_tier"] == 1) & (train_sub["decision"] == "hike")).groupby(train_sub["event_id"]).any().sum()

        flag_under_10 = 1 if t1_hikes < 10 else 0
        note = "Low tightening content in 2010-2015 (ZIRP era)" if flag_under_10 else "Standard expansion window"

        fold_summary.append({
            "fold_id": str(fid),
            "origin_date": str(orig),
            "train_start": "2010-01-01",
            "train_end_nominal": str(orig - dt.timedelta(days=1)),
            "val_start": str(orig),
            "val_end": str(val_end),
            "embargo_days": EMBARGO_DAYS,
            "train_decisions_total": int(train_decs),
            "val_decisions_total": int(val_decs),
            "train_hikes_total": int(train_hikes),
            "val_hikes_total": int(val_hikes),
            "train_tier1_hikes": int(t1_hikes),
            "flag_under_10_tier1_hikes": int(flag_under_10),
            "notes": note
        })

    # Add final_fit row (TRAIN + VALIDATION with 60-day embargo before test window 2024-01-01)
    final_fit_sub = all_analysis_tables[
        (all_analysis_tables["final_split"].isin(["train", "validation"])) & 
        (all_analysis_tables["embargo_dropped"] == 0)
    ]
    ff_decs = final_fit_sub["event_id"].nunique()
    ff_hikes = (final_fit_sub["decision"] == "hike").groupby(final_fit_sub["event_id"]).any().sum()
    ff_t1_hikes = ((final_fit_sub["shock_tier"] == 1) & (final_fit_sub["decision"] == "hike")).groupby(final_fit_sub["event_id"]).any().sum()

    fold_summary.append({
        "fold_id": "final_fit",
        "origin_date": "2024-01-01",
        "train_start": "2010-01-01",
        "train_end_nominal": "2023-12-31",
        "val_start": "",
        "val_end": "",
        "embargo_days": EMBARGO_DAYS,
        "train_decisions_total": int(ff_decs),
        "val_decisions_total": 0,
        "train_hikes_total": int(ff_hikes),
        "val_hikes_total": 0,
        "train_tier1_hikes": int(ff_t1_hikes),
        "flag_under_10_tier1_hikes": 0,
        "notes": "Final fit set across full TRAIN + VALIDATION (2010-2023) with 60-day embargo before 2024-01-01 test cutoff"
    })

    df_folds = pd.DataFrame(fold_summary)
    df_folds.to_csv(DATA_V2_1 / "folds.csv", index=False)
    print(f"Saved {DATA_V2_1 / 'folds.csv'}.")

    # 11. Generate Release Directory (strip proprietary level_local)
    print("--- Creating Release Bundle (stripped level_local) ---")
    panel_returns_only = panel_window.drop(columns=["level_local"])
    panel_returns_only.to_parquet(DATA_V2_1_RELEASE / "panel_returns_only.parquet", index=False)
    
    shutil.copy2(DATA_V2_1 / "analysis_tier1.parquet", DATA_V2_1_RELEASE / "analysis_tier1.parquet")
    shutil.copy2(DATA_V2_1 / "analysis_tier2_primary.parquet", DATA_V2_1_RELEASE / "analysis_tier2_primary.parquet")
    shutil.copy2(DATA_V2_1 / "secondary_holds.parquet", DATA_V2_1_RELEASE / "secondary_holds.parquet")
    shutil.copy2(DATA_V2_1 / "sensitivity_macro_revision.parquet", DATA_V2_1_RELEASE / "sensitivity_macro_revision.parquet")
    shutil.copy2(DATA_V2_1 / "folds.csv", DATA_V2_1_RELEASE / "folds.csv")

    readme_content = """# MoTrans-15 v2.1/v2.1.1 Release Distribution Notice

## Proprietary License and Privacy Restrictions

This release directory contains cumulative log returns (`clr_1`, `clr_3`, `clr_5`, `clr_20`, `clr_60`), daily returns (`ret_local`, `ret_usd`), monetary shocks, and as-of macro controls for academic replication.

**IMPORTANT LICENSING RESTRICTION**:
1. All returns in `panel_returns_only.parquet` and the analysis tables are derived from closing price levels of licensed financial equity market indices.
2. Proprietary price index levels (`level_local`) have been stripped from public release bundles.
3. Due to upstream licensing terms for financial market indices, this dataset **must remain private and not redistributed** until commercial and academic distribution terms are cleared.
"""
    (DATA_V2_1_RELEASE / "README.md").write_text(readme_content, encoding="utf-8")
    print("Saved release tables and data/v2_1/release/README.md.")

    # 12. Generate Sample Reports in outputs/v2_1/
    print("--- Generating Sample Reports in outputs/v2_1/ ---")
    
    # 12a. split_counts.csv (Unified count function across usable analysis tables)
    split_counts_df = compute_counts(all_analysis_tables, ["final_split", "regime", "shock_tier", "shock_measure_type", "decision"])
    split_counts_df = split_counts_df.rename(columns={"final_split": "split", "shock_tier": "tier"})
    split_counts_df = split_counts_df.sort_values(["split", "regime", "tier", "decision"]).reset_index(drop=True)
    split_counts_df.to_csv(OUTPUTS_V2_1 / "split_counts.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'split_counts.csv'}.")

    # 12b. fold_counts.csv (One row per fold, role, regime, and tier; no lumped rows)
    fold_counts_records = []
    for fid, orig, val_end in origins:
        fcol = f"fold_{fid}"
        for role in ["train", "val"]:
            sub = all_analysis_tables[all_analysis_tables[fcol] == role]
            df_c = compute_counts(sub, ["regime", "shock_tier"])
            for _, r in df_c.iterrows():
                flag = 1 if (role == "train" and r["shock_tier"] == 1 and r["hikes_count"] < 10) else 0
                fold_counts_records.append({
                    "fold_id": str(fid),
                    "role": role,
                    "regime": r["regime"],
                    "tier": int(r["shock_tier"]),
                    "decisions_count": int(r["decisions_count"]),
                    "hikes_count": int(r["hikes_count"]),
                    "cuts_count": int(r["cuts_count"]),
                    "holds_count": int(r["holds_count"]),
                    "event_rows_count": int(r["event_rows_count"]),
                    "flag_under_10_tier1_hikes": flag
                })
    df_fcounts = pd.DataFrame(fold_counts_records).sort_values(["fold_id", "role", "regime", "tier"]).reset_index(drop=True)
    df_fcounts.to_csv(OUTPUTS_V2_1 / "fold_counts.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'fold_counts.csv'}.")

    # 12c. test_window_composition.csv (Separating Tier 1, Tier 2 primary rate changes, and secondary holds)
    test_comp = []
    for tab_name, df_tab, s_tier in [
        ("Tier 1", t1_df, 1),
        ("Tier 2 primary", t2_df, 2),
        ("Secondary holds", sec_holds_df, 2)
    ]:
        sub = df_tab[df_tab["final_split"] == "test"]
        df_c = compute_counts(sub, ["regime", "shock_measure_type"])
        for _, r in df_c.iterrows():
            fed_note = "High-frequency data ends Dec 2023; fallback to Tier 2 proxy" if r["regime"] == "Fed" and tab_name != "Tier 1" else ""
            test_comp.append({
                "table": tab_name,
                "regime": r["regime"],
                "shock_tier": s_tier,
                "shock_measure_type": r["shock_measure_type"],
                "decisions_count": int(r["decisions_count"]),
                "hikes_count": int(r["hikes_count"]),
                "cuts_count": int(r["cuts_count"]),
                "holds_count": int(r["holds_count"]),
                "event_rows_count": int(r["event_rows_count"]),
                "notes": fed_note
            })
    df_test_comp = pd.DataFrame(test_comp).sort_values(["shock_tier", "table", "regime"]).reset_index(drop=True)
    df_test_comp.to_csv(OUTPUTS_V2_1 / "test_window_composition.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'test_window_composition.csv'}.")

    # 12d. row_membership.csv (Exact bitwise partition of all 52,242 rows in 2010-2025 window)
    print("--- Generating outputs/v2_1/row_membership.csv ---")
    t1_keys = set(t1_df["event_id"] + "__" + t1_df["index_id"])
    t2_keys = set(t2_df["event_id"] + "__" + t2_df["index_id"])
    sec_keys = set(sec_holds_df["event_id"] + "__" + sec_holds_df["index_id"])

    def assign_membership(row):
        k = row["event_id"] + "__" + row["index_id"]
        if k in t1_keys:
            return "tier1", "analysis_tier1", "Fed; ECB", "High-frequency intraday surprises (Bauer-Swanson MPS; EA-MPD OIS 1Y)"
        if k in t2_keys:
            return "tier2_primary", "analysis_tier2_primary", "BoE; BoC; RBA; CBR; Fed; ECB", "Rate-change decisions with 1-day sovereign yield proxy shocks"
        if k in sec_keys:
            return "secondary_holds", "secondary_holds", "BoE; BoC; RBA; Fed", "Scheduled hold decisions with sovereign yield proxy shocks"
        
        # Usable but not in any table (BoJ clean)
        if row["regime"] == "BoJ" and row["analysis_ok"] == 1:
            return "usable_not_in_any_table", "usable_unassigned", "BoJ", "Clean BoJ decisions without high-frequency shock or sovereign rate change proxy"
        
        # Excluded reasons
        reason = row["exclusion_reason"]
        if reason == "unverified_regime":
            return "excluded", "unverified_regime", "Banxico; BCB; RBI; BoK; PBoC", "Emerging market / unverified central bank announcement timestamps (2010-2025 only; 2026 quarantined)"
        if reason == "embargo_dropped":
            return "excluded", "embargo_dropped", "BoE; BoC; RBA; CBR; BoJ; Fed; ECB", "Decisions within 60 days before train/val/test boundary or obs_60 reaching across split"
        if reason == "timing_ambiguous":
            return "excluded", "timing_ambiguous", "BoE; BoC; CBR; BoJ; Fed", "Intraday timestamp ambiguous across primary sources or announcement timing unclear"
        if reason == "policy_unverified":
            return "excluded", "policy_unverified", "CBR", "Post-2022-02-24 CBR decisions during wartime market closure and capital controls"
        if reason == "timing_unverified":
            return "excluded", "timing_unverified", "CBR", "Emergency or ad-hoc meetings lacking official advance calendar protocol"
        if reason == "moex_halt":
            return "excluded", "moex_halt", "MOEX", "Russian stock exchange trading halt spanning February-March 2022 (ru_imoex only)"
        if reason == "shock_unusable":
            return "excluded", "shock_unusable", "RBA", "RBA June-August 2013 decisions with Grade C (unusable) proxy shocks"
        return "excluded", reason, row["regime"], "Other excluded event rows"

    mem_tuples = [assign_membership(r) for _, r in events_window.iterrows()]
    events_window["membership_category"] = [t[0] for t in mem_tuples]
    events_window["reason_or_table"] = [t[1] for t in mem_tuples]
    events_window["regimes_note"] = [t[2] for t in mem_tuples]
    events_window["description_note"] = [t[3] for t in mem_tuples]

    membership_records = []
    total_window_rows = len(events_window)

    order = [
        ("tier1", "analysis_tier1"),
        ("tier2_primary", "analysis_tier2_primary"),
        ("secondary_holds", "secondary_holds"),
        ("usable_not_in_any_table", "usable_unassigned"),
        ("excluded", "unverified_regime"),
        ("excluded", "embargo_dropped"),
        ("excluded", "timing_ambiguous"),
        ("excluded", "policy_unverified"),
        ("excluded", "timing_unverified"),
        ("excluded", "moex_halt"),
        ("excluded", "shock_unusable")
    ]

    for cat, r_or_t in order:
        sub = events_window[(events_window["membership_category"] == cat) & (events_window["reason_or_table"] == r_or_t)]
        if sub.empty:
            continue
        decs = sub["event_id"].nunique()
        rows = len(sub)
        share = rows / total_window_rows * 100.0
        reg_note = sub["regimes_note"].iloc[0]
        desc = sub["description_note"].iloc[0]
        membership_records.append({
            "membership_category": cat,
            "reason_or_table": r_or_t,
            "regimes": reg_note,
            "decisions_count": decs,
            "event_rows_count": rows,
            "share_of_total_rows": f"{share:.3f}%",
            "description": desc
        })

    df_membership = pd.DataFrame(membership_records)
    df_membership.to_csv(OUTPUTS_V2_1 / "row_membership.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'row_membership.csv'}: {df_membership['event_rows_count'].sum():,} total rows.")

    # 12e. years_thin.csv
    policy_window = policy[(policy["decision_date"] >= "2010-01-01") & (policy["decision_date"] <= "2025-12-31")].copy()
    policy_window["year"] = pd.to_datetime(policy_window["decision_date"]).dt.year
    
    g6_regimes = ["Fed", "ECB", "BoE", "BoC", "RBA", "CBR", "BoJ"]
    dec_by_yr = policy_window[policy_window["regime"].isin(g6_regimes)].groupby(["regime", "year"])["decision_date"].nunique().unstack(fill_value=0)
    dec_by_yr.to_csv(OUTPUTS_V2_1 / "decisions_by_regime_year_2010_2025.csv")

    thin_records = []
    for reg in g6_regimes:
        if reg in dec_by_yr.index:
            for yr in dec_by_yr.columns:
                cnt = int(dec_by_yr.loc[reg, yr])
                if cnt < 8:
                    if reg == "CBR":
                        reason = "Emergency rate-change only regime; peacetime schedule has 8 meetings/yr but 2022 wartime truncation stopped tracking"
                    elif reg == "RBA" and yr >= 2024:
                        reason = "RBA official governance reform moved schedule from 11 monthly meetings to 8 meetings per year starting 2024"
                    else:
                        reason = f"Fewer than 8 scheduled decisions recorded for {reg} in {yr}"
                    thin_records.append({
                        "regime": reg,
                        "year": yr,
                        "decisions_count": cnt,
                        "flag": "FEWER_THAN_8_DECISIONS",
                        "reason": reason
                    })
    df_thin = pd.DataFrame(thin_records).sort_values(["regime", "year"]).reset_index(drop=True)
    df_thin.to_csv(OUTPUTS_V2_1 / "years_thin.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'years_thin.csv'}.")

    # 12f. analysis_ok_breakdown.csv
    ex_breakdown = []
    ex_df = events_window[events_window["analysis_ok"] == 0].copy()
    ex_df["year"] = pd.to_datetime(ex_df["decision_date"]).dt.year

    for (reason, reg, yr), g in ex_df.groupby(["exclusion_reason", "regime", "year"]):
        ex_breakdown.append({
            "exclusion_reason": reason,
            "regime": reg,
            "year": yr,
            "decisions_count": g["event_id"].nunique(),
            "event_rows_count": len(g)
        })
    df_ex = pd.DataFrame(ex_breakdown).sort_values(["exclusion_reason", "regime", "year"]).reset_index(drop=True)
    df_ex.to_csv(OUTPUTS_V2_1 / "analysis_ok_breakdown.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'analysis_ok_breakdown.csv'}.")

    print("=== MoTrans-15 v2.1/v2.1.1 Tables and Reports Successfully Generated ===")


if __name__ == "__main__":
    build_v2_1_tables()
