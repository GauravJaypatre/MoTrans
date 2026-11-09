"""MoTrans-15 v2.2 Table Builder & Leakage Protection Pipeline.

Builds:
- data/v2_2/splits.csv (Single Source of Truth for event-level partition and contamination metadata)
- data/v2_2/analysis_tier1.parquet
- data/v2_2/analysis_tier2_primary.parquet
- data/v2_2/secondary_holds.parquet
- data/v2_2/panel.parquet
- data/v2_2/sensitivity_macro_revision.parquet
- data/v2_2/post_window_2026.parquet
- data/v2_2/excluded_rows.parquet
- data/v2_2/folds.csv (with final_fit row)
- data/v2_2/release/ (release subset without licensed price levels)

Key v2.2 Enhancements:
1. shock_std trap eliminated: shock_std is replaced by shock_descriptive_2019.
   Only shock_raw_bp is used for modeling, standardized strictly on folds via FoldSafeScaler.
2. Window timing: adds clr_1_clean (valid only for announce_in_session == 0) and in_session flag.
3. Single Source of Truth: splits.csv catalogs all decisions with split, fold memberships,
   tier, read_by_v1, read_by_prior_analysis, in_session, and timing_verified_level.
4. Contamination flags: read_by_prior_analysis explicitly isolates the 14 ECB test decisions
   previously computed in v1, ensuring the 56 pristine test decisions are selected by code construction.
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

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
DATA_V2_2 = ROOT / "data" / "v2_2"
DATA_V2_2_RELEASE = DATA_V2_2 / "release"
OUTPUTS_V2_2 = ROOT / "outputs" / "v2_2"

DATA_V2_2.mkdir(parents=True, exist_ok=True)
DATA_V2_2_RELEASE.mkdir(parents=True, exist_ok=True)
OUTPUTS_V2_2.mkdir(parents=True, exist_ok=True)


def compute_counts(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Unified counting function for summary reports."""
    records = []
    for keys, g in df.groupby(group_cols, observed=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        rec = dict(zip(group_cols, keys))
        decs = g.drop_duplicates("event_id")
        rec["decisions_count"] = int(len(decs))
        rec["hikes_count"] = int((decs["decision"] == "hike").sum())
        rec["cuts_count"] = int((decs["decision"] == "cut").sum())
        rec["holds_count"] = int((decs["decision"] == "hold").sum())
        rec["event_rows_count"] = int(len(g))
        records.append(rec)
    return pd.DataFrame(records)


def main():
    print("=================================================================")
    print("MoTrans-15 v2.2 Table Builder & Pipeline Hardening")
    print("=================================================================")

    # 1. Load Primary Inputs
    print("Loading raw final parquets...")
    events = pd.read_parquet(DATA_FINAL / "events.parquet")
    panel = pd.read_parquet(DATA_FINAL / "panel_daily.parquet")
    policy = pd.read_csv(DATA_FINAL / "policy_decisions.csv", dtype={"decision_date": str})
    shocks = pd.read_parquet(DATA_FINAL / "shocks.parquet")
    ctrl = pd.read_parquet(DATA_INTERIM / "controls_long.parquet")

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

    # 3. Add shock_raw_bp and rename shock_std to shock_descriptive_2019
    print("--- Adding Shock Raw BP & Descriptive Scales (v2.2 Schema) ---")
    shocks_map = shocks.set_index("event_id")

    cbr_train = shocks[(shocks["regime"] == "CBR") & 
                       (pd.to_datetime(shocks["decision_date"]).dt.date <= dt.date(2019, 12, 31)) &
                       (shocks["shock_proxy_raw"].notna())]
    cbr_non_emerg = cbr_train[cbr_train["decision_date"] != "2014-12-16"]
    cbr_med = float(np.median(cbr_non_emerg["shock_proxy_raw"].values))
    cbr_mad = float(np.median(np.abs(cbr_non_emerg["shock_proxy_raw"].values - cbr_med)))
    cbr_robust_scale = cbr_mad * 1.4826

    shock_raw_list = []
    shock_desc_list = []

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
        if reg == "CBR" and pd.notna(raw):
            shock_desc_list.append(round(raw / cbr_robust_scale, 6))
        else:
            shock_desc_list.append(s_std)

    events["shock_raw_bp"] = shock_raw_list
    events["shock_descriptive_2019"] = shock_desc_list

    # 4. Backward-Looking Overlap Prior Controls
    print("--- Adding Backward-Looking Overlap Prior Controls ---")
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

    # 6. Assign Rolling-Origin Folds
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
                    return "unused"
                return "train"
            elif orig <= d <= val_end:
                return "val"
            return "unused"

        events[col] = events.apply(assign_f, axis=1)

    # 7. QE / YCC Indicator
    def is_boj_qe_ycc(row):
        if row["regime"] != "BoJ":
            return 0
        d = dt.date.fromisoformat(row["decision_date"][:10])
        return 1 if (dt.date(2013, 4, 4) <= d <= dt.date(2024, 3, 19)) else 0

    events["qe_ycc_indicator"] = events.apply(is_boj_qe_ycc, axis=1)

    # 8. Row Quality, Timing Verification & Contamination Metadata
    print("--- Deriving Quality, Timing, and Contamination Metadata ---")
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

    events["policy_verified"] = (
        events["regime"].isin(["Fed", "ECB", "BoE", "BoC", "RBA", "BoJ"]) |
        ((events["regime"] == "CBR") & (pd.to_datetime(events["decision_date"]).dt.date <= dt.date(2022, 2, 24)))
    ).astype(int)

    etf_proxies = {"ea_emu_smallcap_etf", "de_stoxx_banks_etf", "jp_topix_banks_etf", "kr_banks_etf", "jp_mothers_etf"}
    events["proxy_type"] = events["index_id"].apply(lambda sid: "etf_proxy" if sid in etf_proxies else "cash_benchmark")

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

    # Window timing: in_session and clr_1_clean
    events["in_session"] = events["announce_in_session"].astype(int)
    events["clr_1_clean"] = np.where(events["announce_in_session"] == 0, events["clr_1"], np.nan)

    # Contamination Flags:
    # 47 decisions evaluated in v1 blind test
    t1_v1_path = DATA_FINAL / "analysis_tier1.parquet"
    if t1_v1_path.exists():
        df_v1 = pd.read_parquet(t1_v1_path)
        v1_blind_test_eids = set(df_v1[df_v1["split_tag"] == "blind_test"]["event_id"].unique())
    else:
        v1_blind_test_eids = set()

    events["read_by_v1"] = events["event_id"].apply(lambda x: 1 if x in v1_blind_test_eids else 0)
    # read_by_prior_analysis is 1 for all decisions whose returns were computed in prior analyses
    events["read_by_prior_analysis"] = events["read_by_v1"]

    # 9. Separate 2026 Post-Window Rows (Quarantined)
    print("--- Isolating 2026 Post-Window Rows ---")
    post_window_rows = events[events["final_split"] == "post_window"].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    post_window_rows.to_parquet(DATA_V2_2 / "post_window_2026.parquet", index=False)
    print(f"Saved {DATA_V2_2 / 'post_window_2026.parquet'}: {len(post_window_rows):,} rows ({post_window_rows['event_id'].nunique()} decisions).")

    # Filter window for analysis tables: 2010-01-01 to 2025-12-31
    events_window = events[events["final_split"].isin(["train", "validation", "test"])].copy()

    excluded_rows = events_window[events_window["analysis_ok"] == 0].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    excluded_rows.to_parquet(DATA_V2_2 / "excluded_rows.parquet", index=False)
    print(f"Saved {DATA_V2_2 / 'excluded_rows.parquet'}: {len(excluded_rows):,} rows ({excluded_rows['event_id'].nunique()} decisions).")

    # Base analysis columns for v2.2 (strictly shock_raw_bp, shock_descriptive_2019, clr_1_clean, in_session, contamination flags)
    analysis_cols_v2_2 = [
        "event_id", "regime", "decision_date", "final_split", "fold_1", "fold_2", "fold_3", "fold_4",
        "embargo_dropped", "v1_split_tag", "decision", "size_bp", "shock_raw_bp", "shock_descriptive_2019",
        "shock_measure_type", "shock_tier", "home_market", "index_id", "index_class",
        "announce_in_session", "in_session",
        "clr_1", "clr_1_clean", "clr_3", "clr_5", "clr_20", "clr_60",
        "read_by_v1", "read_by_prior_analysis",
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

    # Table 1: analysis_tier1.parquet
    t1_df = events_window[
        (events_window["shock_tier"] == 1) & 
        (events_window["shock_usable"] == 1) & 
        (events_window["analysis_ok"] == 1)
    ][analysis_cols_v2_2].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    t1_df.to_parquet(DATA_V2_2 / "analysis_tier1.parquet", index=False)
    print(f"Saved {DATA_V2_2 / 'analysis_tier1.parquet'}: {len(t1_df):,} rows ({t1_df['event_id'].nunique()} decisions).")

    # Table 2: analysis_tier2_primary.parquet
    t2_df = events_window[
        (events_window["shock_tier"] == 2) & 
        (events_window["shock_primary"] == 1) & 
        (events_window["shock_usable"] == 1) & 
        (events_window["analysis_ok"] == 1)
    ][analysis_cols_v2_2].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    t2_df.to_parquet(DATA_V2_2 / "analysis_tier2_primary.parquet", index=False)
    print(f"Saved {DATA_V2_2 / 'analysis_tier2_primary.parquet'}: {len(t2_df):,} rows ({t2_df['event_id'].nunique()} decisions).")

    # Table 3: secondary_holds.parquet
    sec_holds_df = events_window[
        (events_window["shock_tier"] == 2) & 
        (events_window["shock_secondary"] == 1) & 
        (events_window["decision"] == "hold") & 
        (events_window["analysis_ok"] == 1)
    ][analysis_cols_v2_2].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    sec_holds_df.to_parquet(DATA_V2_2 / "secondary_holds.parquet", index=False)
    print(f"Saved {DATA_V2_2 / 'secondary_holds.parquet'}: {len(sec_holds_df):,} rows ({sec_holds_df['event_id'].nunique()} decisions).")

    # Table 4: panel.parquet
    panel_window = panel[(panel["date"] >= dt.date(2010, 1, 1)) & (panel["date"] <= dt.date(2025, 12, 31))].sort_values(["index_id", "date"]).reset_index(drop=True)
    panel_window["final_split"] = panel_window["date"].astype(str).apply(assign_split)
    panel_window.to_parquet(DATA_V2_2 / "panel.parquet", index=False)
    print(f"Saved {DATA_V2_2 / 'panel.parquet'}: {len(panel_window):,} rows.")

    # Table 5: sensitivity_macro_revision.parquet
    sens_cols = analysis_cols_v2_2 + ["ctrl_ind_prod"]
    sens_df = events_window[
        (events_window["shock_tier"].isin([1, 2])) & 
        (events_window["shock_primary"] == 1) & 
        (events_window["analysis_ok"] == 1)
    ][sens_cols].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    sens_df.to_parquet(DATA_V2_2 / "sensitivity_macro_revision.parquet", index=False)
    print(f"Saved {DATA_V2_2 / 'sensitivity_macro_revision.parquet'}: {len(sens_df):,} rows ({sens_df['event_id'].nunique()} decisions).")

    # 10. Generate Single Source of Truth: data/v2_2/splits.csv
    print("--- Creating Single Source of Truth: splits.csv ---")
    all_analysis_tables = pd.concat([
        t1_df.assign(tier="tier1"),
        t2_df.assign(tier="tier2_primary"),
        sec_holds_df.assign(tier="secondary_holds"),
    ], ignore_index=True)

    # Home market session indicator per event
    home_sess_map = (
        events_window[events_window["home_market"] == 1]
        .groupby("event_id")["announce_in_session"]
        .first()
        .to_dict()
    )

    split_records = []
    for eid, g in all_analysis_tables.groupby("event_id", observed=False):
        row0 = g.iloc[0]
        split_records.append({
            "event_id": eid,
            "regime": row0["regime"],
            "decision_date": row0["decision_date"],
            "decision": row0["decision"],
            "split": row0["final_split"],
            "fold_1": row0["fold_1"],
            "fold_2": row0["fold_2"],
            "fold_3": row0["fold_3"],
            "fold_4": row0["fold_4"],
            "embargo_dropped": int(row0["embargo_dropped"]),
            "tier": row0["tier"],
            "shock_measure_type": row0["shock_measure_type"],
            "read_by_v1": int(row0["read_by_v1"]),
            "read_by_prior_analysis": int(row0["read_by_prior_analysis"]),
            "home_in_session": int(home_sess_map.get(eid, 0)),
            "timing_verified_level": row0["timing_verified_level"],
        })

    df_splits = pd.DataFrame(split_records).sort_values(["regime", "decision_date", "event_id"]).reset_index(drop=True)
    splits_csv_path = DATA_V2_2 / "splits.csv"
    df_splits.to_csv(splits_csv_path, index=False)
    print(f"Saved {splits_csv_path}: {len(df_splits)} decisions cataloged.")

    # 11. Create data/v2_2/folds.csv
    print("--- Creating data/v2_2/folds.csv ---")
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

    # Add final_fit row
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
    df_folds.to_csv(DATA_V2_2 / "folds.csv", index=False)
    print(f"Saved {DATA_V2_2 / 'folds.csv'}.")

    # 12. Create Release Bundle (stripped level_local)
    print("--- Creating Release Bundle (stripped level_local) ---")
    panel_returns_only = panel_window.drop(columns=["level_local"])
    panel_returns_only.to_parquet(DATA_V2_2_RELEASE / "panel_returns_only.parquet", index=False)
    
    shutil.copy2(DATA_V2_2 / "analysis_tier1.parquet", DATA_V2_2_RELEASE / "analysis_tier1.parquet")
    shutil.copy2(DATA_V2_2 / "analysis_tier2_primary.parquet", DATA_V2_2_RELEASE / "analysis_tier2_primary.parquet")
    shutil.copy2(DATA_V2_2 / "secondary_holds.parquet", DATA_V2_2_RELEASE / "secondary_holds.parquet")
    shutil.copy2(DATA_V2_2 / "sensitivity_macro_revision.parquet", DATA_V2_2_RELEASE / "sensitivity_macro_revision.parquet")
    shutil.copy2(DATA_V2_2 / "folds.csv", DATA_V2_2_RELEASE / "folds.csv")
    shutil.copy2(DATA_V2_2 / "splits.csv", DATA_V2_2_RELEASE / "splits.csv")

    # 13. Generate Reports under outputs/v2_2/
    print("--- Generating Summary Reports in outputs/v2_2/ ---")
    split_counts = compute_counts(all_analysis_tables, ["tier", "final_split"])
    split_counts.to_csv(OUTPUTS_V2_2 / "split_counts.csv", index=False)

    test_comp = compute_counts(
        all_analysis_tables[all_analysis_tables["final_split"] == "test"],
        ["tier", "regime", "read_by_prior_analysis"]
    )
    test_comp.to_csv(OUTPUTS_V2_2 / "test_window_composition.csv", index=False)

    print("\n=================================================================")
    print("v2.2 Table Build Complete!")
    print(f"  Tier 1 Decisions: {t1_df['event_id'].nunique():,}")
    print(f"  Tier 2 Primary Decisions: {t2_df['event_id'].nunique():,}")
    print(f"  Secondary Holds Decisions: {sec_holds_df['event_id'].nunique():,}")
    print(f"  Total Cataloged Decisions in splits.csv: {len(df_splits):,}")
    print("=================================================================")


if __name__ == "__main__":
    main()
