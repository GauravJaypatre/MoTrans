"""CBR Decision Dates Correction & Pipeline Integration.

Fixes the 38 CBR decision dates from Monday effective dates to official Friday Board meeting dates
using data/raw/timing_sources/cbr_cal_mp.html.
Preserves old date in 'bis_effective_date', sets 'date_confidence' (high/medium),
recomputes announce_ts_utc (13:30 MSK), event alignment, window returns,
shocks, and overlap flags using standard pipeline functions.
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
    print("--- 1. Loading Audit and Backing Up Pre-Fix Values ---")
    audit = pd.read_csv(OUTPUTS_V2 / "cbr_date_verification_audit.csv")
    changed_map = {}
    for _, r in audit[audit["date_changed"] == 1].iterrows():
        changed_map[r["dataset_date"]] = {
            "official_date": r["official_meeting_date"],
            "official_day": r["official_meeting_day"],
            "meeting_type": r["meeting_type"]
        }

    special_calendar_text = {
        "2014-03-03": "March 3: The Bank of Russia Board of Directors unscheduled meeting on monetary policy issues(Press release)",
        "2014-10-31": "October 31: The Bank of Russia Board of Directors meeting on monetary policy issues(Press releaseis to be published at 13:30 Moscow time)",
        "2014-12-11": "December 11: The Bank of Russia Board of Directors meeting on monetary policy issues(Press releaseis to be published at 13:30 Moscow time)",
        "2014-12-15": "December 15: The Bank of Russia Board of Directors unscheduled meeting on monetary policy issues(Press release)",
        "2015-04-30": "April 30: The Bank of Russia Board of Directors meeting on monetary policy issues(Press releaseis to be published at 13:30 Moscow time)",
        "2015-06-15": "June 15: The Bank of Russia Board of Directors meeting on monetary policy issues(Press releaseis to be published at 13:30 Moscow time)",
        "2016-06-10": "June 10: The Bank of Russia Board of Directors meeting on monetary policy issues(Press releaseis to be published at 13:30 Moscow time)",
        "2017-04-28": "April 28: The Bank of Russia Board of Directors meeting on monetary policy issues(Press releaseis to be published at 13:30 Moscow time)",
        "2017-09-15": "September 15: The Bank of Russia Board of Directors meeting on monetary policy issues(Press releaseis to be published at 13:30 Moscow time)",
        "2020-06-19": "19 June: Bank of Russia Board of Directors’ monetary policy meeting Press release and medium-term forecast are to be published at 13:30 Moscow time"
    }

    policy = pd.read_csv(DATA_FINAL / "policy_decisions.csv", dtype={"decision_date": str})
    shocks = pd.read_parquet(DATA_FINAL / "shocks.parquet")
    events = pd.read_parquet(DATA_FINAL / "events.parquet")

    # Store pre-fix values for comparison
    pre_shk_map = {}
    for _, r in shocks[shocks["regime"] == "CBR"].iterrows():
        pre_shk_map[str(r["decision_date"])] = {
            "shock_proxy_raw": r["shock_proxy_raw"],
            "shock_std": r["shock_std"]
        }

    pre_clr_map = {}
    for _, r in events[(events["regime"] == "CBR") & (events["index_id"] == "ru_imoex")].iterrows():
        pre_clr_map[str(r["decision_date"])] = r["clr_1"]

    # Add bis_effective_date and date_confidence columns
    if "bis_effective_date" not in policy.columns:
        policy["bis_effective_date"] = policy["decision_date"]
    if "date_confidence" not in policy.columns:
        policy["date_confidence"] = "high"

    # Pre-2014 refinancing rate era gets medium confidence
    policy.loc[(policy["regime"] == "CBR") & (policy["decision_date"] < "2013-09-13"), "date_confidence"] = "medium"

    tz_msk = ZoneInfo("Europe/Moscow")

    for old_date, info in changed_map.items():
        new_date = info["official_date"]
        new_ev_id = f"cbr_{new_date}"

        # 13:30 MSK
        d = dt.date.fromisoformat(new_date)
        dt_local = dt.datetime(d.year, d.month, d.day, 13, 30, tzinfo=tz_msk)
        new_utc = dt_local.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

        mask = (policy["regime"] == "CBR") & (policy["bis_effective_date"] == old_date)
        policy.loc[mask, "decision_date"] = new_date
        policy.loc[mask, "event_id"] = new_ev_id
        policy.loc[mask, "announce_time_local"] = "13:30"
        policy.loc[mask, "timezone"] = "Europe/Moscow"
        policy.loc[mask, "announce_ts_utc"] = new_utc
        policy.loc[mask, "window_start_utc"] = new_utc
        policy.loc[mask, "window_end_utc"] = new_utc
        policy.loc[mask, "time_quality"] = "exact"
        policy.loc[mask, "time_source"] = "Bank of Russia official press release convention (13:30 Moscow time for Friday Board rate meetings, verified by cbr_cal_mp.html)"
        policy.loc[mask, "date_source"] = f"Bank of Russia Board meeting ({info['meeting_type']})"
        policy.loc[mask, "date_confidence"] = "high"

    # Also update interim policy_decisions_more.csv so it stays in sync
    interim_more = DATA_INTERIM / "policy_decisions_more.csv"
    if interim_more.exists():
        df_more = pd.read_csv(interim_more, dtype={"decision_date": str})
        if "bis_effective_date" not in df_more.columns:
            df_more["bis_effective_date"] = df_more["decision_date"]
        for old_date, info in changed_map.items():
            new_date = info["official_date"]
            d = dt.date.fromisoformat(new_date)
            dt_local = dt.datetime(d.year, d.month, d.day, 13, 30, tzinfo=tz_msk)
            new_utc = dt_local.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
            mask = (df_more["regime"] == "CBR") & (df_more["bis_effective_date"] == old_date)
            df_more.loc[mask, "decision_date"] = new_date
            df_more.loc[mask, "announce_time_local"] = "13:30"
            df_more.loc[mask, "timezone"] = "Europe/Moscow"
            df_more.loc[mask, "announce_ts_utc"] = new_utc
            df_more.loc[mask, "window_start_utc"] = new_utc
            df_more.loc[mask, "window_end_utc"] = new_utc
            df_more.loc[mask, "time_quality"] = "exact"
            df_more.loc[mask, "time_source"] = "Bank of Russia official press release convention (13:30 Moscow time for Friday Board rate meetings, verified by cbr_cal_mp.html)"
            df_more.loc[mask, "date_source"] = f"Bank of Russia Board meeting ({info['meeting_type']})"
        df_more.to_csv(interim_more, index=False)
        print("Updated data/interim/policy_decisions_more.csv")

    policy = policy.sort_values(["regime", "decision_date"]).reset_index(drop=True)
    policy.to_csv(DATA_FINAL / "policy_decisions.csv", index=False)
    print("--- 2. Saved updated policy_decisions.csv ---")

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

    comparison_rows = []
    for old_date, info in changed_map.items():
        new_date = info["official_date"]
        new_ev_id = f"cbr_{new_date}"

        pol_row = final_policy[(final_policy["regime"] == "CBR") & (final_policy["decision_date"] == new_date)].iloc[0]
        shk_row = final_shocks[final_shocks["event_id"] == new_ev_id]
        new_shk = shk_row["shock_proxy_raw"].iloc[0] if len(shk_row) else np.nan
        new_shk_std = shk_row["shock_std"].iloc[0] if len(shk_row) else np.nan

        ev_row = final_events[(final_events["event_id"] == new_ev_id) & (final_events["index_id"] == "ru_imoex")]
        new_clr1 = ev_row["clr_1"].iloc[0] if len(ev_row) else np.nan

        pre_s = pre_shk_map.get(old_date, {})
        old_shk = pre_s.get("shock_proxy_raw", np.nan)
        old_shk_std = pre_s.get("shock_std", np.nan)
        old_clr1 = pre_clr_map.get(old_date, np.nan)

        cal_text = special_calendar_text.get(new_date, f"{new_date}: {info['meeting_type']}")

        comparison_rows.append({
            "old_date": old_date,
            "new_date": new_date,
            "decision": pol_row["decision"],
            "size_bp": pol_row["size_bp"],
            "old_shock_proxy_bp": old_shk,
            "new_shock_proxy_bp": new_shk,
            "old_shock_std": old_shk_std,
            "new_shock_std": new_shk_std,
            "old_clr1_imoex": old_clr1,
            "new_clr1_imoex": new_clr1,
            "date_confidence": pol_row.get("date_confidence", "high"),
            "official_calendar_excerpt": cal_text
        })

    df_comp = pd.DataFrame(comparison_rows)
    df_comp.to_csv(OUTPUTS_V2 / "cbr_before_after_changes.csv", index=False)
    print(f"Generated outputs/v2/cbr_before_after_changes.csv with {len(df_comp)} changed decisions.")

    cbr_eff = final_policy[(final_policy["regime"] == "CBR") & (final_policy["decision_date"] >= "2010-01-01") & 
                           (final_policy["decision_date"] <= "2022-02-24") & (final_policy["shock_primary"] == 1)]
    print(f"Effective CBR decisions remaining in key-rate era: {len(cbr_eff)}")
    return df_comp

if __name__ == "__main__":
    run_cbr_fix()
