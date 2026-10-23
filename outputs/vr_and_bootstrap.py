"""Variance Ratio and Bootstrap Placebo Analysis Script.

Usage:
    python outputs/vr_and_bootstrap.py

Outputs:
    outputs/variance_ratios.csv
    outputs/bootstrap_placebo.csv

Seed:
    2026

Procedure:
    1. For each central bank regime, loads the exact daily sovereign yield series
       corresponding to shock_proxy_tenor:
         - BoE: 1Y Gilt (GB, yield_1y, BoE spot curve)
         - BoC: 2Y GoC (CA, yield_1y, BoC 2Y benchmark bond)
         - RBA: 2Y ACGB (AU, yield_2y, RBA Table F2 benchmark)
         - CBR: 1Y OFZ (RU, yield_1y, CBR zero-coupon curve)
         - BoJ: 1Y JGB (JP, yield_1y, MoF Japan JGB yield)
         - BCB: 1Y Swap DI (BR, yield_1y, BCB SGS 7806 swap DI x pre 360d)
         - PBoC: 2Y ChinaBond (CN, yield_2y, ChinaBond sovereign benchmark)
         - Fed: 1Y Treasury (US, yield_1y, US Treasury par yield)
         - ECB: 1Y Bund (DE, yield_1y, Bundesbank listed Federal securities)
    2. Calculates daily yield changes in basis points: dy = (y_t - y_{t-1}) * 100.
    3. Partitions days into non-meeting days, rate action days (hike/cut), and rate hold days.
    4. Computes variance ratios:
         VR_action = Var(dy | action) / Var(dy | non-meeting)
         VR_hold = Var(dy | hold) / Var(dy | non-meeting)
    5. For hold days, runs a Monte Carlo placebo test with B = 1,000 iterations:
       In each iteration b, draws N_hold observations without replacement from non-meeting days,
       computes placebo variance ratio, and calculates empirical p-value:
         p = (1/B) * sum(I(VR_placebo >= VR_hold)).
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

policy = pd.read_csv(FINAL / "policy_decisions.csv")
controls = pd.read_parquet(INTERIM / "controls_long.parquet")

regime_yield_map = {
    "BoE": ("GB", "yield_1y", "1Y", "1Y Gilt spot curve (Bank of England)"),
    "BoC": ("CA", "yield_2y", "2Y", "2Y GoC benchmark bond yield (Bank of Canada)"),
    "RBA": ("AU", "yield_2y", "2Y", "2Y ACGB benchmark yield (RBA Table F2)"),
    "CBR": ("RU", "yield_1y", "1Y", "1Y OFZ zero-coupon curve (Bank of Russia)"),
    "BoJ": ("JP", "yield_1y", "1Y", "1Y JGB Ministry of Finance yield"),
    "BCB": ("BR", "yield_1y", "1Y", "1Y Swap DI x pre 360d (BCB SGS 7806)"),
    "PBoC": ("CN", "yield_2y", "2Y", "2Y ChinaBond sovereign benchmark yield"),
    "Fed": ("US", "yield_1y", "1Y", "1Y US Treasury par yield (FRB H.15)"),
    "ECB": ("DE", "yield_1y", "1Y", "1Y Bundesbank Federal securities yield"),
}

vr_rows = []
bootstrap_rows = []
np.random.seed(2026)

for reg, (country, var, tenor, desc) in regime_yield_map.items():
    sub = controls[(controls["country"] == country) & (controls["variable"] == var)].sort_values("date").dropna(subset=["value"])
    sub["dy"] = sub["value"].diff() * 100
    sub = sub.dropna(subset=["dy"])
    
    p = policy[policy["regime"] == reg]
    meet_dates = set(pd.to_datetime(p["decision_date"]).dt.date)
    hold_dates = set(pd.to_datetime(p[p["decision"] == "hold"]["decision_date"]).dt.date)
    act_dates = set(pd.to_datetime(p[p["decision"].isin(["hike", "cut"])]["decision_date"]).dt.date)
    
    sub["date_dt"] = pd.to_datetime(sub["date"]).dt.date
    non_meet = sub[~sub["date_dt"].isin(meet_dates)]["dy"]
    var_nm = non_meet.var()
    sd_nm = non_meet.std()
    
    act = sub[sub["date_dt"].isin(act_dates)]["dy"]
    vr_act = act.var() / var_nm if len(act) > 1 and var_nm > 0 else np.nan
    
    hold = sub[sub["date_dt"].isin(hold_dates)]["dy"]
    vr_hold = hold.var() / var_nm if len(hold) > 1 and var_nm > 0 else np.nan
    
    if len(hold) > 1 and var_nm > 0:
        placebo_vrs = [
            float(np.var(np.random.choice(non_meet, size=len(hold), replace=False), ddof=1) / var_nm)
            for _ in range(1000)
        ]
        pval_hold = float(np.mean(np.array(placebo_vrs) >= vr_hold))
        p_mean = float(np.mean(placebo_vrs))
        p_p05 = float(np.percentile(placebo_vrs, 5))
        p_p50 = float(np.percentile(placebo_vrs, 50))
        p_p95 = float(np.percentile(placebo_vrs, 95))
        
        for rep, b_vr in enumerate(placebo_vrs, 1):
            bootstrap_rows.append({
                "regime": reg,
                "replicate": rep,
                "placebo_vr": round(b_vr, 4),
            })
    else:
        pval_hold, p_mean, p_p05, p_p50, p_p95 = np.nan, np.nan, np.nan, np.nan, np.nan

    vr_rows.append({
        "regime": reg,
        "shock_proxy_tenor": tenor,
        "series_description": desc,
        "n_non_meeting": len(non_meet),
        "sd_non_meeting_bp": round(sd_nm, 2),
        "n_action": len(act),
        "vr_action": round(vr_act, 2) if pd.notna(vr_act) else np.nan,
        "n_hold": len(hold),
        "vr_hold": round(vr_hold, 2) if pd.notna(vr_hold) else np.nan,
        "placebo_mean_vr": round(p_mean, 2) if pd.notna(p_mean) else np.nan,
        "placebo_p05": round(p_p05, 2) if pd.notna(p_p05) else np.nan,
        "placebo_p50": round(p_p50, 2) if pd.notna(p_p50) else np.nan,
        "placebo_p95": round(p_p95, 2) if pd.notna(p_p95) else np.nan,
        "pval_hold": round(pval_hold, 4) if pd.notna(pval_hold) else np.nan,
        "hold_signal_verdict": "Statistically Significant (p < 0.05)" if pval_hold < 0.05 else ("No Excess Signal (Noise-dominated)" if pd.notna(pval_hold) else "No Holds in Regime")
    })

pd.DataFrame(vr_rows).to_csv(OUT / "variance_ratios.csv", index=False)
pd.DataFrame(bootstrap_rows).to_csv(OUT / "bootstrap_placebo.csv", index=False)
print("Saved outputs/variance_ratios.csv and outputs/bootstrap_placebo.csv")
