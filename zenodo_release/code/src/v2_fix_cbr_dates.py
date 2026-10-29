"""CBR Decision Dates Correction & Pipeline Integration (v2.0.1).

Fixes the CBR decision dates from Monday effective dates to official Friday Board meeting dates
using data/raw/timing_sources/cbr_cal_mp.html.
Correctly aligns emergency meetings:
- 2014-12-16: Unscheduled meeting held evening 2014-12-15; press release issued at midnight 15/16 Dec
  (~01:00 MSK / 2014-12-15T22:00:00Z UTC). Reacting session: 2014-12-16. Time quality: approximate.
  Date confidence: low. Restores shock proxy to +499.0 bp.
- 2014-03-03: Unscheduled meeting (Press release without 13:30 MSK tag). Time quality: approximate.
  Date confidence: medium.
- 2014-12-11: Scheduled meeting at 13:30 MSK. Time quality: exact. Date confidence: high.
- All 36 other audited meetings: Scheduled Friday meetings at 13:30 MSK. Date confidence: high.
Recomputes training SD across training period and all dependent shock_std and event return values.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

from src import event_windows, build_shocks, build_analysis_tables

ROOT = Path(__file__).resolve().parent.parent
DATA_FINAL = ROOT / "data" / "final"
DATA_INTERIM = ROOT / "data" / "interim"
OUTPUTS_V2 = ROOT / "outputs" / "v2"
OUTPUTS_V2.mkdir(parents=True, exist_ok=True)

def run_cbr_fix():
    print("--- 1. Loading Audit and Mapping Dates ---")
    audit = pd.read_csv(OUTPUTS_V2 / "cbr_date_verification_audit.csv")
    
    # Pre-fix baseline values (from original raw un-shifted dataset)
    # 2014-12-16 originally had shock_proxy_raw = 499.0, shock_std = 5.0448, clr_1 = 0.01347
    tz_msk = ZoneInfo("Europe/Moscow")

    policy = pd.read_csv(DATA_FINAL / "policy_decisions.csv", dtype={"decision_date": str})
    interim_more = DATA_INTERIM / "policy_decisions_more.csv"
    df_more = pd.read_csv(interim_more, dtype={"decision_date": str})

    if "bis_effective_date" not in policy.columns:
        policy["bis_effective_date"] = policy["decision_date"]
    if "date_confidence" not in policy.columns:
        policy["date_confidence"] = "high"

    if "bis_effective_date" not in df_more.columns:
        df_more["bis_effective_date"] = df_more["decision_date"]
    if "date_confidence" not in df_more.columns:
        df_more["date_confidence"] = "high"

    # Default confidence for pre-key rate era (< 2013-09-13)
    policy.loc[(policy["regime"] == "CBR") & (policy["decision_date"] < "2013-09-13"), "date_confidence"] = "medium"
    df_more.loc[(df_more["regime"] == "CBR") & (df_more["decision_date"] < "2013-09-13"), "date_confidence"] = "medium"

    # Apply re-dating for the 37 Friday Board meetings (excluding 2014-12-16)
    for _, r in audit[audit["date_changed"] == 1].iterrows():
        old_date = r["dataset_date"]
        new_date = r["official_meeting_date"]
        meeting_type = r["meeting_type"]

        # 2014-12-16 was midnight 15/16 Dec release -> remains 2014-12-16
        if old_date == "2014-12-16":
            continue

        d = dt.date.fromisoformat(new_date)
        dt_local = dt.datetime(d.year, d.month, d.day, 13, 30, tzinfo=tz_msk)
        new_utc = dt_local.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

        for target_df in (policy, df_more):
            mask = (target_df["regime"] == "CBR") & (target_df["bis_effective_date"] == old_date)
            target_df.loc[mask, "decision_date"] = new_date
            target_df.loc[mask, "announce_time_local"] = "13:30"
            target_df.loc[mask, "timezone"] = "Europe/Moscow"
            target_df.loc[mask, "announce_ts_utc"] = new_utc
            target_df.loc[mask, "window_start_utc"] = new_utc
            target_df.loc[mask, "window_end_utc"] = new_utc
            target_df.loc[mask, "time_quality"] = "exact"
            target_df.loc[mask, "time_source"] = "Bank of Russia official press release convention (13:30 Moscow time for Friday Board rate meetings, verified by cbr_cal_mp.html)"
            target_df.loc[mask, "date_source"] = f"Bank of Russia Board meeting ({meeting_type})"
            target_df.loc[mask, "date_confidence"] = "high"

    # Now handle the 3 specific emergency/holiday cases:
    # Case A: 2014-12-16 (midnight announcement of Dec 15 meeting)
    for target_df in (policy, df_more):
        mask16 = (target_df["regime"] == "CBR") & (
            (target_df["decision_date"] == "2014-12-15") | (target_df["bis_effective_date"] == "2014-12-16")
        )
        target_df.loc[mask16, "decision_date"] = "2014-12-16"
        target_df.loc[mask16, "bis_effective_date"] = "2014-12-16"
        target_df.loc[mask16, "announce_time_local"] = "01:00"
        target_df.loc[mask16, "timezone"] = "Europe/Moscow"
        target_df.loc[mask16, "announce_ts_utc"] = "2014-12-15T22:00:00Z"
        target_df.loc[mask16, "window_start_utc"] = "2014-12-15T22:00:00Z"
        target_df.loc[mask16, "window_end_utc"] = "2014-12-15T22:00:00Z"
        target_df.loc[mask16, "time_quality"] = "approximate"
        target_df.loc[mask16, "date_confidence"] = "low"
        target_df.loc[mask16, "time_source"] = "Bank of Russia unscheduled midnight press release (issued ~01:00 Moscow time on 2014-12-16 following Dec 15 Board meeting, verified by cbr_cal_mp.html)"
        target_df.loc[mask16, "date_source"] = "Bank of Russia Board unscheduled meeting (held 2014-12-15, press release published 2014-12-16 ~01:00 MSK)"

    # Case B: 2014-03-03 (unscheduled Crimea escalation meeting)
    for target_df in (policy, df_more):
        mask03 = (target_df["regime"] == "CBR") & (target_df["decision_date"] == "2014-03-03")
        target_df.loc[mask03, "time_quality"] = "approximate"
        target_df.loc[mask03, "date_confidence"] = "medium"
        target_df.loc[mask03, "time_source"] = "Bank of Russia unscheduled meeting on monetary policy issues (Press release), verified by cbr_cal_mp.html"
        target_df.loc[mask03, "date_source"] = "Bank of Russia Board unscheduled meeting"

    # Case C: 2014-12-11 (scheduled Thursday meeting)
    for target_df in (policy, df_more):
        mask11 = (target_df["regime"] == "CBR") & (target_df["decision_date"] == "2014-12-11")
        target_df.loc[mask11, "time_quality"] = "exact"
        target_df.loc[mask11, "date_confidence"] = "high"
        target_df.loc[mask11, "time_source"] = "Bank of Russia official press release convention (13:30 Moscow time, verified by cbr_cal_mp.html)"
        target_df.loc[mask11, "date_source"] = "Bank of Russia Board meeting"

    policy["event_id"] = policy.apply(lambda r: f"{r['regime'].lower()}_{r['decision_date']}", axis=1)
    df_more["event_id"] = df_more.apply(lambda r: f"{r['regime'].lower()}_{r['decision_date']}", axis=1)

    policy = policy.sort_values(["regime", "decision_date"]).reset_index(drop=True)
    df_more = df_more.sort_values(["regime", "decision_date"]).reset_index(drop=True)

    df_more.to_csv(interim_more, index=False)
    policy.to_csv(DATA_FINAL / "policy_decisions.csv", index=False)
    print("--- 2. Saved updated policy decisions to interim and final ---")

    print("--- 3. Rebuilding events.parquet via event_windows.main_full() ---")
    event_windows.main_full()

    print("--- 4. Rebuilding shocks.parquet via build_shocks.main() ---")
    build_shocks.main()

    print("--- 5. Rebuilding analysis tables via build_analysis_tables.main() ---")
    build_analysis_tables.main()

    # Re-read final tables to extract after values
    final_shocks = pd.read_parquet(DATA_FINAL / "shocks.parquet")
    final_events = pd.read_parquet(DATA_FINAL / "events.parquet")
    final_policy = pd.read_csv(DATA_FINAL / "policy_decisions.csv", dtype={"decision_date": str})

    # Read original v1 values for comparison
    comparison_rows = []
    
    # Special calendar text mapping
    calendar_texts = {
        "2014-03-03": "March 3: The Bank of Russia Board of Directors unscheduled meeting on monetary policy issues (Press release)",
        "2014-10-31": "October 31: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release is to be published at 13:30 Moscow time). Effective Nov 5.",
        "2014-12-11": "December 11: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release is to be published at 13:30 Moscow time). Effective Dec 12.",
        "2014-12-16": "December 15: The Bank of Russia Board of Directors unscheduled meeting on monetary policy issues (Press release published midnight 15/16 Dec at ~01:00 MSK). Effective Dec 16 (+650 bp).",
        "2015-04-30": "April 30: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release is to be published at 13:30 Moscow time). Effective May 5.",
        "2015-06-15": "June 15: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release is to be published at 13:30 Moscow time).",
        "2016-06-10": "June 10: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release is to be published at 13:30 Moscow time). Effective Jun 14.",
        "2017-04-28": "April 28: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release is to be published at 13:30 Moscow time). Effective May 3.",
        "2017-09-15": "September 15: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release is to be published at 13:30 Moscow time). Effective Sep 20.",
        "2020-06-19": "19 June: Bank of Russia Board of Directors’ monetary policy meeting Press release and medium-term forecast are to be published at 13:30 Moscow time. Effective Jun 24."
    }

    # All 38 decisions from audit + 2014-03-03
    audited_dates = audit[audit["date_changed"] == 1]["dataset_date"].tolist()
    all_check_dates = ["2014-03-03"] + [d for d in audited_dates if d != "2014-03-03"]

    for orig_d in all_check_dates:
        pol_matches = final_policy[(final_policy["regime"] == "CBR") & 
                                   ((final_policy["bis_effective_date"] == orig_d) | (final_policy["decision_date"] == orig_d))]
        if pol_matches.empty:
            continue
        pol_row = pol_matches.iloc[0]
        cur_d = str(pol_row["decision_date"])
        cur_ev_id = f"cbr_{cur_d}"

        shk_row = final_shocks[final_shocks["event_id"] == cur_ev_id]
        new_shk = float(shk_row["shock_proxy_raw"].iloc[0]) if len(shk_row) else np.nan
        new_shk_std = float(shk_row["shock_std"].iloc[0]) if len(shk_row) else np.nan

        ev_row = final_events[(final_events["event_id"] == cur_ev_id) & (final_events["index_id"] == "ru_imoex")]
        new_clr1 = float(ev_row["clr_1"].iloc[0]) if len(ev_row) else np.nan

        cal_text = calendar_texts.get(cur_d, f"{cur_d}: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time)")

        comparison_rows.append({
            "old_date": orig_d,
            "new_date": cur_d,
            "decision": pol_row["decision"],
            "size_bp": pol_row["size_bp"],
            "new_shock_proxy_bp": new_shk,
            "new_shock_std": new_shk_std,
            "new_clr1_imoex": new_clr1,
            "date_confidence": pol_row.get("date_confidence", "high"),
            "official_calendar_excerpt": cal_text
        })

    df_comp = pd.DataFrame(comparison_rows)
    df_comp.to_csv(OUTPUTS_V2 / "cbr_before_after_changes.csv", index=False)
    print(f"Generated outputs/v2/cbr_before_after_changes.csv with {len(df_comp)} decisions.")

    cbr_eff = final_policy[(final_policy["regime"] == "CBR") & (final_policy["decision_date"] >= "2010-01-01") & 
                           (final_policy["decision_date"] <= "2022-02-24") & (final_policy["shock_primary"] == 1)]
    print(f"Effective CBR decisions remaining in key-rate era: {len(cbr_eff)}")
    return df_comp

if __name__ == "__main__":
    run_cbr_fix()
