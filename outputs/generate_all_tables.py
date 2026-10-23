"""Generate all audited raw output CSVs and docs markdown tables for MoTrans-15.

Ensures every table in docs/ and outputs/ is generated strictly from code and data.
No tables are hand-typed.
"""

from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd

ROOT = Path(".")
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
DOCS = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. EFFECTIVE SAMPLE TABLE (Item 7 & 9)
# -----------------------------------------------------------------------------
shocks = pd.read_parquet(FINAL / "shocks.parquet")
policy = pd.read_csv(FINAL / "policy_decisions.csv")

# Merge analysis_ready_timing
if "analysis_ready_timing" in policy.columns and "analysis_ready_timing" not in shocks.columns:
    merged = shocks.merge(policy[["event_id", "analysis_ready_timing"]], on="event_id")
else:
    merged = shocks.copy()

merged["is_effective_primary"] = ((merged["shock_primary"] == 1) & (merged["analysis_ready_timing"] == 1)).astype(int)
merged["is_effective_secondary"] = ((merged["shock_secondary"] == 1) & (merged["analysis_ready_timing"] == 1)).astype(int)

eff_rows = []
for (regime, tier), g in merged[merged["shock_tier"].notna()].groupby(["regime", "shock_tier"]):
    tier = int(tier)
    p_tr = len(g[(g["split_tag"] == "train") & (g["is_effective_primary"] == 1)])
    p_cr = len(g[(g["split_tag"] == "crisis") & (g["is_effective_primary"] == 1)])
    p_bl = len(g[(g["split_tag"] == "blind_test") & (g["is_effective_primary"] == 1)])
    tot_p = p_tr + p_cr + p_bl

    s_tr = len(g[(g["split_tag"] == "train") & (g["is_effective_secondary"] == 1)])
    s_cr = len(g[(g["split_tag"] == "crisis") & (g["is_effective_secondary"] == 1)])
    s_bl = len(g[(g["split_tag"] == "blind_test") & (g["is_effective_secondary"] == 1)])
    tot_s = s_tr + s_cr + s_bl

    tot_dec = len(g)
    mtype = g["shock_measure_type"].iloc[0]

    eff_rows.append({
        "regime": regime,
        "shock_tier": tier,
        "shock_measure_type": mtype,
        "total_decisions": tot_dec,
        "primary_train": p_tr,
        "primary_crisis": p_cr,
        "primary_blind": p_bl,
        "total_primary": tot_p,
        "secondary_train": s_tr,
        "secondary_crisis": s_cr,
        "secondary_blind": s_bl,
        "total_secondary": tot_s,
    })

eff_df = pd.DataFrame(eff_rows).sort_values(["shock_tier", "regime"])
eff_df.to_csv(OUT / "effective_sample.csv", index=False)
print("Saved outputs/effective_sample.csv")

# -----------------------------------------------------------------------------
# 2. VARIANCE RATIOS & BOOTSTRAP PLACEBO (Item 6 & 8)
# -----------------------------------------------------------------------------
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

        for rep, b_vr in enumerate(placebo_vrs[:100], 1):
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

vr_df = pd.DataFrame(vr_rows)
vr_df.to_csv(OUT / "variance_ratios.csv", index=False)
print("Saved outputs/variance_ratios.csv")

boot_df = pd.DataFrame(bootstrap_rows)
boot_df.to_csv(OUT / "bootstrap_placebo.csv", index=False)
print("Saved outputs/bootstrap_placebo.csv")

# -----------------------------------------------------------------------------
# 3. OVERLAP STATS
# -----------------------------------------------------------------------------
overlap_rows = []
for W in [1, 3, 5, 20, 60]:
    flag_col = f"overlap_{W}d"
    cnt_col = f"overlap_count_{W}d"
    contam = int(shocks[flag_col].sum())
    n_tot = len(shocks)
    pct = round((contam / n_tot) * 100, 2)
    mean_c = round(float(shocks[cnt_col].mean()), 2)
    max_c = int(shocks[cnt_col].max())
    overlap_rows.append({
        "window_days": W,
        "horizon_label": f"clr_{W}",
        "contaminated_events": contam,
        "total_events": n_tot,
        "contamination_share_pct": pct,
        "mean_other_decisions": mean_c,
        "max_other_decisions": max_c,
    })

overlap_df = pd.DataFrame(overlap_rows)
overlap_df.to_csv(OUT / "overlap_stats.csv", index=False)
print("Saved outputs/overlap_stats.csv")

# -----------------------------------------------------------------------------
# 4. ANNUAL INDEX AVAILABILITY TABLE (Item 3)
# -----------------------------------------------------------------------------
events = pd.read_parquet(FINAL / "events.parquet")
policy["year"] = pd.to_datetime(policy["decision_date"]).dt.year
events["year"] = pd.to_datetime(events["decision_date"]).dt.year

dec_yr = policy.groupby("year").size()
ev_yr = events.groupby("year").size()
ind_yr = events.groupby("year")["index_id"].nunique()

annual_rows = []
for y in range(2000, 2014):
    d = int(dec_yr.get(y, 0))
    e = int(ev_yr.get(y, 0))
    idx = int(ind_yr.get(y, 0))
    theo = d * 38
    diff = theo - e
    annual_rows.append({
        "Period": str(y),
        "Active Indices": idx,
        "Policy Decisions": d,
        "Actual events Rows": e,
        "Theoretical Max (N x 38)": theo,
        "Difference (Missing Pre-Inception)": diff,
    })

# 2014-2025 row
d_14_25 = int(sum(dec_yr.get(y, 0) for y in range(2014, 2026)))
e_14_25 = int(sum(ev_yr.get(y, 0) for y in range(2014, 2026)))
theo_14_25 = d_14_25 * 38
diff_14_25 = theo_14_25 - e_14_25
annual_rows.append({
    "Period": "2014-2025",
    "Active Indices": 38,
    "Policy Decisions": d_14_25,
    "Actual events Rows": e_14_25,
    "Theoretical Max (N x 38)": theo_14_25,
    "Difference (Missing Pre-Inception)": diff_14_25,
})

# 2026 row
d_26 = int(dec_yr.get(2026, 0))
e_26 = int(ev_yr.get(2026, 0))
theo_26 = d_26 * 38
diff_26 = theo_26 - e_26
annual_rows.append({
    "Period": "2026",
    "Active Indices": 38,
    "Policy Decisions": d_26,
    "Actual events Rows": e_26,
    "Theoretical Max (N x 38)": theo_26,
    "Difference (Missing Pre-Inception)": diff_26,
})

annual_df = pd.DataFrame(annual_rows)
tot_dec = annual_df["Policy Decisions"].sum()
tot_ev = annual_df["Actual events Rows"].sum()
tot_theo = annual_df["Theoretical Max (N x 38)"].sum()
tot_diff = annual_df["Difference (Missing Pre-Inception)"].sum()

tot_row = pd.DataFrame([{
    "Period": "Total",
    "Active Indices": "—",
    "Policy Decisions": tot_dec,
    "Actual events Rows": tot_ev,
    "Theoretical Max (N x 38)": tot_theo,
    "Difference (Missing Pre-Inception)": tot_diff,
}])
annual_df_with_tot = pd.concat([annual_df, tot_row], ignore_index=True)
annual_df_with_tot.to_csv(OUT / "annual_index_availability.csv", index=False)
print("Saved outputs/annual_index_availability.csv")

# -----------------------------------------------------------------------------
# 5. REGENERATE docs/scope_options.md TABLE 4
# -----------------------------------------------------------------------------
md_table_lines = [
    r"| Period | Active Indices | Policy Decisions | Actual `events.parquet` Rows | Theoretical Max ($N \times 38$) | Difference (Missing Pre-Inception) |",
    "|:---:|:---:|:---:|:---:|:---:|:---:|",
]
for r in annual_df.itertuples(index=False):
    md_table_lines.append(f"| **{r[0]}** | {r[1]} | {r[2]:,} | {r[3]:,} | {r[4]:,} | {r[5]:,} |")
md_table_lines.append(f"| **Total** | — | **{tot_dec:,}** | **{tot_ev:,}** | **{tot_theo:,}** | **{tot_diff:,}** |")
table4_md = "\n".join(md_table_lines)

scope_md_path = DOCS / "scope_options.md"
if scope_md_path.exists():
    content = scope_md_path.read_text(encoding="utf-8")
    import re
    # Replace Table 4
    table4_pattern = re.compile(r"\| Period \| Active Indices \|.*?\n\| \*\*Total\*\* \| — \|.*?\n", re.DOTALL)
    if table4_pattern.search(content):
        content = table4_pattern.sub(table4_md + "\n", content)
    else:
        # Check if old format with Year
        old_pattern = re.compile(r"\| Year \| Active Indices \|.*?\n\| \*\*Total\*\* \| — \|.*?\n", re.DOTALL)
        if old_pattern.search(content):
            content = old_pattern.sub(table4_md + "\n", content)
    scope_md_path.write_text(content, encoding="utf-8")
    print("Updated docs/scope_options.md Table 4 successfully!")

print("All outputs and docs tables generated successfully!")
