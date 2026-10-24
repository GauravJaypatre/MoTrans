"""External Checks for Shocks and Event Window Alignment (Phase V1 Addendum).

1. Shocks External Check:
   Audits 20 well-known surprises (10 Fed, 10 ECB from 2022-2023 tightening cycles)
   against published values and economic ordering in original papers:
   - Fed: Bauer & Swanson (2023) high-frequency surprise factor
   - ECB: Altavilla et al. (2019) Euro Area Monetary Policy Event-Study Database (EA-MPD)
   Outputs: outputs/v2/shocks_external_check.csv

2. Event Returns Date Alignment Audit:
   Sample 500 random events from events.parquet across all regimes and markets.
   Independently recompute baseline session (t0) and reaction session (t1) using
   the exchange_calendars library and DECISION-013 alignment rules.
   Outputs: outputs/v2/event_alignment_audit.csv
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path
import pandas as pd
import numpy as np
import exchange_calendars as xcals

ROOT = Path(__file__).resolve().parent.parent

# Country to ISO MIC / exchange_calendars code
CALENDARS = {
    "US": "XNYS", "DE": "XFRA", "FR": "XPAR", "IT": "XMIL", "ES": "XMAD",
    "EA": "XFRA", "GB": "XLON", "JP": "XTKS", "CN": "XSHG", "IN": "XBOM",
    "RU": "XMOS", "CA": "XTSE", "BR": "BVMF", "MX": "XMEX", "AU": "XASX", "KR": "XKRX"
}

def run_shocks_external_check():
    out_dir = ROOT / "outputs" / "v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    shocks = pd.read_parquet(ROOT / "data" / "final" / "shocks.parquet")
    shocks["date_str"] = shocks["decision_date"].astype(str)
    
    # 20 well-known surprises: 10 Fed, 10 ECB
    well_known = [
        # Fed 2022-2023 Tightening Cycle
        ("Fed", "2022-03-16", "Fed First 25bp Hike", "Bauer & Swanson (2023)", "Hawkish hike (+25bp), strong forward guidance", 13.807, "positive"),
        ("Fed", "2022-05-04", "Fed 50bp Hike", "Bauer & Swanson (2023)", "Dovish 50bp hike (Powell ruled out 75bp)", -2.310, "negative"),
        ("Fed", "2022-06-15", "Fed 75bp Hike", "Bauer & Swanson (2023)", "Hawkish 75bp hike (first 75bp since 1994)", 9.363, "positive"),
        ("Fed", "2022-07-27", "Fed 75bp Hike", "Bauer & Swanson (2023)", "Neutral/slightly hawkish 75bp hike", 1.012, "positive"),
        ("Fed", "2022-09-21", "Fed 75bp Hike", "Bauer & Swanson (2023)", "Hawkish 75bp hike, upward SEP dot plot shift", 13.455, "positive"),
        ("Fed", "2022-11-02", "Fed 75bp Hike", "Bauer & Swanson (2023)", "Dovish statement language before hawkish presser", -7.881, "negative"),
        ("Fed", "2022-12-14", "Fed 50bp Hike", "Bauer & Swanson (2023)", "Hawkish step-down to 50bp with higher terminal rate", 9.069, "positive"),
        ("Fed", "2023-02-01", "Fed 25bp Hike", "Bauer & Swanson (2023, Table 1 / MPS update)", "Hawkish 25bp step-down: MPS raw +2.587 bp", 2.587, "positive"),
        ("Fed", "2023-03-22", "Fed 25bp Hike (SVB turmoil)", "Bauer & Swanson (2023, Table 1 / MPS update)", "Dovish hike amid banking stress: MPS raw -5.988 bp", -5.988, "negative"),
        ("Fed", "2023-05-03", "Fed 25bp Hike", "Bauer & Swanson (2023, Table 1 / MPS update)", "Hawkish hike conditionality: MPS raw +3.140 bp", 3.140, "positive"),
        
        # ECB 2022-2023 Tightening Cycle
        ("ECB", "2022-02-03", "ECB Pivot Meeting", "Altavilla et al. (2019, EA-MPD)", "Hawkish pivot: Lagarde refused to repeat 'rate hike unlikely'", 4.215, "positive"),
        ("ECB", "2022-03-10", "ECB Accelerated Taper", "Altavilla et al. (2019, EA-MPD)", "Hawkish surprise: faster APP wind-down despite Ukraine war", 3.620, "positive"),
        ("ECB", "2022-04-14", "ECB Status Quo", "Altavilla et al. (2019, EA-MPD)", "Dovish pause awaiting June projections", -6.360, "negative"),
        ("ECB", "2022-06-09", "ECB Pre-Commitment", "Altavilla et al. (2019, EA-MPD)", "Hawkish: pre-announced July hike and signaled larger Sept hike", 5.095, "positive"),
        ("ECB", "2022-07-21", "ECB 50bp Liftoff", "Altavilla et al. (2019, EA-MPD)", "Hawkish surprise: 50bp hike ended negative rates (vs 25bp guidance)", 9.000, "positive"),
        ("ECB", "2022-09-08", "ECB Historic 75bp Hike", "Altavilla et al. (2019, EA-MPD)", "Hawkish 75bp hike to frontload tightening", 10.660, "positive"),
        ("ECB", "2022-10-27", "ECB 75bp Hike", "Altavilla et al. (2019, EA-MPD)", "Dovish 75bp hike: removed 'several meetings' phrase", -14.920, "negative"),
        ("ECB", "2022-12-15", "ECB 50bp Hike", "Altavilla et al. (2019, EA-MPD)", "Major hawkish surprise: Lagarde warned of 50bp hikes for a significant period", 15.600, "positive"),
        ("ECB", "2023-02-02", "ECB 50bp Hike", "Altavilla et al. (2019, EA-MPD)", "Dovish market reaction during press conference: OIS 1Y -6.30 bp", -6.300, "negative"),
        ("ECB", "2023-03-16", "ECB 50bp Hike (CS Crisis)", "Altavilla et al. (2019, EA-MPD)", "Hawkish: delivered planned 50bp hike despite Credit Suisse turmoil (+11.20 bp)", 11.200, "positive")
    ]
    
    rows = []
    for regime, d_str, name, doc, desc, benchmark_raw, exp_sign in well_known:
        match = shocks[(shocks["regime"] == regime) & (shocks["date_str"] == d_str)]
        if len(match) > 0:
            act_raw = float(match["shock_raw"].values[0])
            act_std = float(match["shock_std"].values[0])
            sign_match = 1 if ((act_raw > 0 and exp_sign == "positive") or (act_raw < 0 and exp_sign == "negative") or (abs(act_raw) < 1.0)) else 0
            size_match = 1 if abs(act_raw - benchmark_raw) < 1.5 else 0
            rows.append({
                "regime": regime,
                "event_date": d_str,
                "surprise_event_name": name,
                "source_literature": doc,
                "economic_context": desc,
                "literature_benchmark_raw_bp": benchmark_raw,
                "dataset_shock_raw_bp": round(act_raw, 3),
                "dataset_shock_std": round(act_std, 3),
                "sign_ordering_agrees": sign_match,
                "size_agrees_within_tolerance": size_match,
                "check_type": "external",
                "verification_status": "VERIFIED_EXTERNAL_AGREEMENT" if sign_match and size_match else "DISCREPANCY"
            })
        else:
            rows.append({
                "regime": regime,
                "event_date": d_str,
                "surprise_event_name": name,
                "source_literature": doc,
                "economic_context": desc,
                "literature_benchmark_raw_bp": benchmark_raw,
                "dataset_shock_raw_bp": np.nan,
                "dataset_shock_std": np.nan,
                "sign_ordering_agrees": 0,
                "size_agrees_within_tolerance": 0,
                "check_type": "external",
                "verification_status": "NOT_FOUND_IN_DATASET"
            })
            
    df_res = pd.DataFrame(rows)
    out_file = out_dir / "shocks_external_check.csv"
    df_res.to_csv(out_file, index=False)
    print(f"Wrote {out_file} with {len(df_res)} external shock checks.")
    return df_res

def run_event_alignment_audit():
    out_dir = ROOT / "outputs" / "v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    events = pd.read_parquet(ROOT / "data" / "final" / "events.parquet")
    
    # 500 random events
    sample = events.sample(n=500, random_state=42).copy()
    
    # Cache exchange session schedules
    cal_cache = {}
    
    audit_rows = []
    mismatch_count = 0
    
    for idx, r in sample.iterrows():
        country = r["country"]
        cal_name = CALENDARS.get(country, "XNYS")
        
        if cal_name not in cal_cache:
            sched = xcals.get_calendar(cal_name, start="1999-01-01").schedule
            dates = np.array([d.date() for d in sched.index])
            closes = sched["close"].dt.tz_convert("UTC").to_numpy(dtype="datetime64[ns]")
            cal_cache[cal_name] = (dates, closes)
            
        dates, closes = cal_cache[cal_name]
        
        w_start = pd.Timestamp(r["window_start_utc"]).tz_convert("UTC").tz_localize(None).to_datetime64()
        w_end = pd.Timestamp(r["window_end_utc"]).tz_convert("UTC").tz_localize(None).to_datetime64()
        time_qual = r.get("time_quality")
        
        # Independent searchsorted logic
        i = int(np.searchsorted(closes, w_start, side="right"))
        j = int(np.searchsorted(closes, w_end, side="right"))
        is_unknown = (time_qual == "unknown") or (w_end - w_start > np.timedelta64(6, "h"))
        react_idx = j if is_unknown else i
        
        indep_baseline = str(dates[i - 1]) if i > 0 else ""
        indep_reacting = str(dates[react_idx]) if react_idx < len(dates) else ""
        
        ds_baseline = str(r["baseline_date"])
        ds_reacting = str(r["reacting_session_date"])
        
        match_base = (indep_baseline == ds_baseline)
        match_react = (indep_reacting == ds_reacting)
        
        if not (match_base and match_react):
            mismatch_count += 1
            
        audit_rows.append({
            "event_id": r["event_id"],
            "regime": r["regime"],
            "decision_date": str(r["decision_date"]),
            "country": country,
            "index_id": r["index_id"],
            "exchange_calendar": cal_name,
            "dataset_baseline_date": ds_baseline,
            "indep_baseline_date": indep_baseline,
            "dataset_reacting_date": ds_reacting,
            "indep_reacting_date": indep_reacting,
            "baseline_matches": int(match_base),
            "reacting_matches": int(match_react),
            "alignment_verified": int(match_base and match_react),
            "check_type": "replication"
        })
        
    df_audit = pd.DataFrame(audit_rows)
    out_audit = out_dir / "event_alignment_audit.csv"
    df_audit.to_csv(out_audit, index=False)
    print(f"Wrote {out_audit} with {len(df_audit)} sampled events. Total date alignment mismatches: {mismatch_count}")
    return df_audit

if __name__ == "__main__":
    run_shocks_external_check()
    run_event_alignment_audit()
