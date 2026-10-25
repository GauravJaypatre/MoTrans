"""MoTrans-15 v2.1 Table Builder & Leakage Protection Pipeline.

Builds:
- data/v2_1/analysis_tier1.parquet
- data/v2_1/analysis_tier2_primary.parquet
- data/v2_1/secondary_holds.parquet
- data/v2_1/panel.parquet
- data/v2_1/sensitivity_macro_revision.parquet
- data/v2_1/post_window_2026.parquet
- data/v2_1/excluded_rows.parquet
- data/v2_1/folds.csv
- data/v2_1/release/ (release subset without licensed price levels)

Produces reports under outputs/v2_1/:
- split_counts.csv
- fold_counts.csv
- test_window_composition.csv
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


def build_v2_1_tables():
    print("=== Starting MoTrans-15 v2.1 Dataset Build ===")
    
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
    cbr_legacy_scale = float(np.std(cbr_train["shock_proxy_raw"].values, ddof=1))

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

    # 4. Compute 60-day observation date and embargo drop
    print("--- Computing 60-Day Embargo and Drop Flags ---")
    dates_by_idx = {sid: np.array(g.sort_values("date")["date"].tolist()) for sid, g in panel.groupby("index_id")}

    # Precompute obs_60_date on unique (index_id, react_obs_date)
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

    # 5. Assign Rolling-Origin Folds inside TRAIN + VALIDATION
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

    # 6. QE / YCC Indicator (BoJ)
    def is_boj_qe_ycc(row):
        if row["regime"] != "BoJ":
            return 0
        d = dt.date.fromisoformat(row["decision_date"][:10])
        # QQE introduced 2013-04-04; YCC ended 2024-03-19
        return 1 if (dt.date(2013, 4, 4) <= d <= dt.date(2024, 3, 19)) else 0

    events["qe_ycc_indicator"] = events.apply(is_boj_qe_ycc, axis=1)

    # 7. Row-Quality Columns & Exclusion Reasons
    print("--- Deriving Row Quality & Exclusion Reasons ---")
    # price_source_verified: us_sp500 and jp_nikkei225 verified against FRED
    events["price_source_verified"] = events["index_id"].isin(["us_sp500", "jp_nikkei225"]).astype(int)

    # shock_replicated: Tier 1 HF OIS and Tier 2 clean sovereign yield proxies
    events["shock_replicated"] = (events["shock_usable"].fillna(0).astype(int) == 1).astype(int)

    # timing_verified_level: event / convention / none
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

    # analysis_ok: clean, verified, not ambiguous, not halted, not embargo dropped
    is_moex_halt = (events["index_id"] == "ru_imoex") & (pd.to_datetime(events["decision_date"]).dt.date >= dt.date(2022, 2, 24))
    events["analysis_ok"] = (
        (events["policy_verified"] == 1) &
        (events["timing_verified_level"] != "none") &
        (events["timing_ambiguous"] == 0) &
        (~is_moex_halt) &
        (events["embargo_dropped"] == 0)
    ).astype(int)

    # Exclusion reason for analysis_ok == 0
    def derive_exclusion_reason(row):
        if row["analysis_ok"] == 1:
            return "none"
        if row["embargo_dropped"] == 1:
            return "embargo_dropped"
        if row["regime"] in ["BCB", "Banxico", "RBI"]:
            return "unverified_regime"
        if row["policy_verified"] == 0:
            return "policy_unverified"
        if row["timing_verified_level"] == "none":
            return "timing_unverified"
        if row["timing_ambiguous"] == 1:
            return "timing_ambiguous"
        if row["index_id"] == "ru_imoex" and str(row["decision_date"]) >= "2022-02-24":
            return "moex_halt"
        if row.get("shock_usable", 1) == 0:
            return "shock_unusable"
        return "unverified_quality"

    events["exclusion_reason"] = events.apply(derive_exclusion_reason, axis=1)

    # 8. Separate 2026 Post-Window Rows (Quarantined)
    print("--- Isolating 2026 Post-Window Rows ---")
    post_window_rows = events[events["final_split"] == "post_window"].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    post_window_rows.to_parquet(DATA_V2_1 / "post_window_2026.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'post_window_2026.parquet'}: {len(post_window_rows):,} rows (quarantined).")

    # Filter window for analysis tables: 2010-01-01 to 2025-12-31
    events_window = events[events["final_split"].isin(["train", "validation", "test"])].copy()

    # Excluded rows companion file (analysis_ok == 0 in 2010-2025 window)
    excluded_rows = events_window[events_window["analysis_ok"] == 0].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    excluded_rows.to_parquet(DATA_V2_1 / "excluded_rows.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'excluded_rows.parquet'}: {len(excluded_rows):,} rows.")

    # Base columns for analysis tables
    analysis_cols = [
        "event_id", "regime", "decision_date", "final_split", "fold_1", "fold_2", "fold_3", "fold_4",
        "embargo_dropped", "v1_split_tag", "decision", "size_bp", "shock_raw_bp", "shock_std",
        "shock_std_legacy", "shock_measure_type", "shock_tier", "home_market", "index_id", "index_class",
        "clr_1", "clr_3", "clr_5", "clr_20", "clr_60",
        "overlap_1d", "overlap_3d", "overlap_5d", "overlap_20d", "overlap_60d",
        "overlap_count_1d", "overlap_count_3d", "overlap_count_5d", "overlap_count_20d", "overlap_count_60d",
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
    print(f"Saved {DATA_V2_1 / 'analysis_tier1.parquet'}: {len(t1_df):,} rows ({t1_df['decision_date'].nunique()} decisions).")

    # Table 2: analysis_tier2_primary.parquet (Rate change decisions with proxy shocks; analysis_ok == 1)
    t2_df = events_window[
        (events_window["shock_tier"] == 2) & 
        (events_window["shock_primary"] == 1) & 
        (events_window["shock_usable"] == 1) & 
        (events_window["analysis_ok"] == 1)
    ][analysis_cols].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    t2_df.to_parquet(DATA_V2_1 / "analysis_tier2_primary.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'analysis_tier2_primary.parquet'}: {len(t2_df):,} rows ({t2_df['decision_date'].nunique()} decisions).")

    # Table 3: secondary_holds.parquet (Scheduled hold decisions; analysis_ok == 1)
    sec_holds_df = events_window[
        (events_window["shock_tier"] == 2) & 
        (events_window["shock_secondary"] == 1) & 
        (events_window["decision"] == "hold") & 
        (events_window["analysis_ok"] == 1)
    ][analysis_cols].sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    sec_holds_df.to_parquet(DATA_V2_1 / "secondary_holds.parquet", index=False)
    print(f"Saved {DATA_V2_1 / 'secondary_holds.parquet'}: {len(sec_holds_df):,} rows ({sec_holds_df['decision_date'].nunique()} decisions).")

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
    print(f"Saved {DATA_V2_1 / 'sensitivity_macro_revision.parquet'}: {len(sens_df):,} rows.")

    # 9. Create data/v2_1/folds.csv
    print("--- Creating data/v2_1/folds.csv ---")
    fold_summary = []
    # Count decisions based on unique event_id among usable decisions
    for fid, orig, val_end in origins:
        fcol = f"fold_{fid}"
        train_sub = events_window[events_window[fcol] == "train"]
        val_sub = events_window[events_window[fcol] == "val"]
        
        train_decs = train_sub["event_id"].nunique()
        val_decs = val_sub["event_id"].nunique()

        train_hikes = train_sub[train_sub["decision"] == "hike"]["event_id"].nunique()
        val_hikes = val_sub[val_sub["decision"] == "hike"]["event_id"].nunique()

        # Tier 1 hikes in training
        t1_hikes = train_sub[(train_sub["shock_tier"] == 1) & (train_sub["decision"] == "hike")]["event_id"].nunique()

        flag_under_10 = 1 if t1_hikes < 10 else 0
        note = "Low tightening content in 2010-2015 (ZIRP era)" if flag_under_10 else "Standard expansion window"

        fold_summary.append({
            "fold_id": fid,
            "origin_date": str(orig),
            "train_start": "2010-01-01",
            "train_end_nominal": str(orig - dt.timedelta(days=1)),
            "val_start": str(orig),
            "val_end": str(val_end),
            "embargo_days": EMBARGO_DAYS,
            "train_decisions_total": train_decs,
            "val_decisions_total": val_decs,
            "train_hikes_total": train_hikes,
            "val_hikes_total": val_hikes,
            "train_tier1_hikes": t1_hikes,
            "flag_under_10_tier1_hikes": flag_under_10,
            "notes": note
        })

    df_folds = pd.DataFrame(fold_summary)
    df_folds.to_csv(DATA_V2_1 / "folds.csv", index=False)
    print(f"Saved {DATA_V2_1 / 'folds.csv'}.")

    # 10. Generate Release Directory (strip proprietary level_local)
    print("--- Creating Release Bundle (stripped level_local) ---")
    panel_returns_only = panel_window.drop(columns=["level_local"])
    panel_returns_only.to_parquet(DATA_V2_1_RELEASE / "panel_returns_only.parquet", index=False)
    
    shutil.copy2(DATA_V2_1 / "analysis_tier1.parquet", DATA_V2_1_RELEASE / "analysis_tier1.parquet")
    shutil.copy2(DATA_V2_1 / "analysis_tier2_primary.parquet", DATA_V2_1_RELEASE / "analysis_tier2_primary.parquet")
    shutil.copy2(DATA_V2_1 / "secondary_holds.parquet", DATA_V2_1_RELEASE / "secondary_holds.parquet")
    shutil.copy2(DATA_V2_1 / "sensitivity_macro_revision.parquet", DATA_V2_1_RELEASE / "sensitivity_macro_revision.parquet")
    shutil.copy2(DATA_V2_1 / "folds.csv", DATA_V2_1_RELEASE / "folds.csv")

    readme_content = """# MoTrans-15 v2.1 Release Distribution Notice

## Proprietary License and Privacy Restrictions

This release directory contains cumulative log returns (`clr_1`, `clr_3`, `clr_5`, `clr_20`, `clr_60`), daily returns (`ret_local`, `ret_usd`), monetary shocks, and as-of macro controls for academic replication.

**IMPORTANT LICENSING RESTRICTION**:
1. All returns in `panel_returns_only.parquet` and the analysis tables are derived from closing price levels of licensed financial equity market indices.
2. Proprietary price index levels (`level_local`) have been stripped from public release bundles.
3. Due to upstream licensing terms for financial market indices, this dataset **must remain private and not redistributed** until commercial and academic distribution terms are cleared.
"""
    (DATA_V2_1_RELEASE / "README.md").write_text(readme_content, encoding="utf-8")
    print("Saved release tables and data/v2_1/release/README.md.")

    # 11. Generate Sample Reports in outputs/v2_1/
    print("--- Generating Sample Reports in outputs/v2_1/ ---")
    
    # 11a. split_counts.csv
    split_records = []
    # Usable event rows
    grp = events_window[events_window["analysis_ok"] == 1].groupby([
        "final_split", "regime", "shock_tier", "shock_measure_type", "decision"
    ])
    for (sp, reg, tier, s_type, dec), g in grp:
        split_records.append({
            "split": sp,
            "regime": reg,
            "tier": tier,
            "shock_measure_type": s_type,
            "decision": dec,
            "decisions_count": g["event_id"].nunique(),
            "event_rows_count": len(g)
        })
    df_splits = pd.DataFrame(split_records).sort_values(["split", "regime", "tier", "decision"]).reset_index(drop=True)
    df_splits.to_csv(OUTPUTS_V2_1 / "split_counts.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'split_counts.csv'}.")

    # 11b. fold_counts.csv
    fold_counts_records = []
    for fid, orig, val_end in origins:
        fcol = f"fold_{fid}"
        for role in ["train", "val"]:
            sub = events_window[(events_window[fcol] == role) & (events_window["analysis_ok"] == 1)]
            for (reg, tier), g in sub.groupby(["regime", "shock_tier"]):
                decs = g["event_id"].nunique()
                hikes = g[g["decision"] == "hike"]["event_id"].nunique()
                cuts = g[g["decision"] == "cut"]["event_id"].nunique()
                holds = g[g["decision"] == "hold"]["event_id"].nunique()
                flag = 1 if (role == "train" and tier == 1 and hikes < 10) else 0
                fold_counts_records.append({
                    "fold_id": fid,
                    "role": role,
                    "regime": reg,
                    "tier": tier,
                    "decisions_count": decs,
                    "hikes_count": hikes,
                    "cuts_count": cuts,
                    "holds_count": holds,
                    "event_rows_count": len(g),
                    "flag_under_10_tier1_hikes": flag
                })
    df_fcounts = pd.DataFrame(fold_counts_records).sort_values(["fold_id", "role", "regime", "tier"]).reset_index(drop=True)
    df_fcounts.to_csv(OUTPUTS_V2_1 / "fold_counts.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'fold_counts.csv'}.")

    # 11c. test_window_composition.csv
    test_usable = events_window[(events_window["final_split"] == "test") & (events_window["analysis_ok"] == 1)]
    test_comp = []
    for (reg, tier, s_type), g in test_usable.groupby(["regime", "shock_tier", "shock_measure_type"]):
        decs = g["event_id"].nunique()
        hikes = g[g["decision"] == "hike"]["event_id"].nunique()
        cuts = g[g["decision"] == "cut"]["event_id"].nunique()
        holds = g[g["decision"] == "hold"]["event_id"].nunique()
        fed_note = "High-frequency data ends Dec 2023; fallback to Tier 2 proxy" if reg == "Fed" and tier == 2 else ""
        test_comp.append({
            "regime": reg,
            "shock_tier": tier,
            "shock_measure_type": s_type,
            "decisions_count": decs,
            "hikes_count": hikes,
            "cuts_count": cuts,
            "holds_count": holds,
            "event_rows_count": len(g),
            "notes": fed_note
        })
    df_test_comp = pd.DataFrame(test_comp).sort_values(["shock_tier", "regime"]).reset_index(drop=True)
    df_test_comp.to_csv(OUTPUTS_V2_1 / "test_window_composition.csv", index=False)
    print(f"Saved {OUTPUTS_V2_1 / 'test_window_composition.csv'}.")

    # 11d. years_thin.csv
    policy_window = policy[(policy["decision_date"] >= "2010-01-01") & (policy["decision_date"] <= "2025-12-31")].copy()
    policy_window["year"] = pd.to_datetime(policy_window["decision_date"]).dt.year
    
    # Decisions by regime year
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

    # 11e. analysis_ok_breakdown.csv
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

    print("=== MoTrans-15 v2.1 Tables and Reports Successfully Generated ===")

if __name__ == "__main__":
    build_v2_1_tables()
