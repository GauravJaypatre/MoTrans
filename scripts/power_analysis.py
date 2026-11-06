"""Statistical Power & Minimum Detectable Effect (MDE) Analysis for MoTrans-15.

Phase 1 Item 7:
Computes the Minimum Detectable Effect (MDE) at 80% power and 5% two-sided significance
using event-clustered standard errors across:
- All cumulative log return horizons: clr_1, clr_3, clr_5, clr_20, clr_60
- All core estimation designs: Tier 1 Final Fit, Tier 2 Primary Final Fit, Pooled Final Fit
- Out-of-sample test splits: Pristine Test Set (N=56) and Full Test Set (N=70)

Outputs:
- outputs/modeling/power_analysis_mde.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.data_loader import load_modeling_data
from src.modeling.pipeline import FoldSafeScaler
from src.modeling.tier_handler import prepare_tier_sample


HORIZONS = ["clr_1", "clr_3", "clr_5", "clr_20", "clr_60"]


def compute_mde(se: float, df_t: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """Compute Minimum Detectable Effect (MDE).
    
    MDE = (t_{1 - alpha/2, df} + t_{power, df}) * SE
    """
    t_alpha = stats.t.ppf(1.0 - alpha / 2.0, df=df_t)
    t_power = stats.t.ppf(power, df=df_t)
    return float((t_alpha + t_power) * se)


def run_power_analysis():
    print("=================================================================")
    print("STATISTICAL POWER & MINIMUM DETECTABLE EFFECT (MDE) ANALYSIS")
    print("=================================================================")

    out_records = []

    # -------------------------------------------------------------
    # 1. Tier 1 Final Fit (239 decisions)
    # -------------------------------------------------------------
    df_t1 = prepare_tier_sample("tier1", split="final_fit", version="v2_2")
    scaler_t1 = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_t1.fit(df_t1, allow_final_fit=True)
    df_t1 = scaler_t1.transform(df_t1)

    x_cols_t1 = ["shock_raw_bp_fold_std"]
    G_t1 = int(df_t1["event_id"].nunique())
    N_t1 = len(df_t1)
    df_t1_deg = G_t1 - len(x_cols_t1) - 1

    se_t1_map = {}
    for h in HORIZONS:
        clean = df_t1.dropna(subset=[h] + x_cols_t1 + ["event_id"])
        Y = clean[h].values
        X = sm.add_constant(clean[x_cols_t1]).values
        m = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean["event_id"].values})
        se = float(m.bse[1])
        se_t1_map[h] = se
        mde = compute_mde(se, df_t=df_t1_deg)
        out_records.append({
            "design": "Tier 1 Final Fit",
            "tier": "tier1",
            "split": "final_fit",
            "horizon": h,
            "n_decisions": G_t1,
            "n_obs": N_t1,
            "se_cluster": se,
            "t_crit_alpha": stats.t.ppf(0.975, df=df_t1_deg),
            "t_crit_power": stats.t.ppf(0.80, df=df_t1_deg),
            "mde_coef": mde,
            "mde_bp_per_std": mde * 10000,
            "mde_pct_per_std": mde * 100,
            "notes": "Estimated from in-sample final_fit event-clustered covariance"
        })

    # -------------------------------------------------------------
    # 2. Tier 2 Primary Final Fit (110 decisions)
    # -------------------------------------------------------------
    df_t2 = prepare_tier_sample("tier2_primary", split="final_fit", version="v2_2")
    scaler_t2 = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_t2.fit(df_t2, allow_final_fit=True)
    df_t2 = scaler_t2.transform(df_t2)

    G_t2 = int(df_t2["event_id"].nunique())
    N_t2 = len(df_t2)
    df_t2_deg = G_t2 - len(x_cols_t1) - 1

    se_t2_map = {}
    for h in HORIZONS:
        clean = df_t2.dropna(subset=[h] + x_cols_t1 + ["event_id"])
        Y = clean[h].values
        X = sm.add_constant(clean[x_cols_t1]).values
        m = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean["event_id"].values})
        se = float(m.bse[1])
        se_t2_map[h] = se
        mde = compute_mde(se, df_t=df_t2_deg)
        out_records.append({
            "design": "Tier 2 Primary Final Fit",
            "tier": "tier2_primary",
            "split": "final_fit",
            "horizon": h,
            "n_decisions": G_t2,
            "n_obs": N_t2,
            "se_cluster": se,
            "t_crit_alpha": stats.t.ppf(0.975, df=df_t2_deg),
            "t_crit_power": stats.t.ppf(0.80, df=df_t2_deg),
            "mde_coef": mde,
            "mde_bp_per_std": mde * 10000,
            "mde_pct_per_std": mde * 100,
            "notes": "Estimated from in-sample final_fit event-clustered covariance"
        })

    # -------------------------------------------------------------
    # 3. Pooled Final Fit (349 decisions)
    # -------------------------------------------------------------
    df_pool = prepare_tier_sample("pooled", split="final_fit", version="v2_2")
    scaler_pool = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_pool.fit(df_pool, allow_final_fit=True)
    df_pool = scaler_pool.transform(df_pool)

    x_pool = ["shock_raw_bp_fold_std", "shock_tier"]
    G_pool = int(df_pool["event_id"].nunique())
    N_pool = len(df_pool)
    df_pool_deg = G_pool - len(x_pool) - 1

    se_pool_map = {}
    for h in HORIZONS:
        clean = df_pool.dropna(subset=[h] + x_pool + ["event_id"])
        Y = clean[h].values
        X = sm.add_constant(clean[x_pool]).values
        m = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean["event_id"].values})
        se = float(m.bse[1])
        se_pool_map[h] = se
        mde = compute_mde(se, df_t=df_pool_deg)
        out_records.append({
            "design": "Pooled Final Fit",
            "tier": "pooled",
            "split": "final_fit",
            "horizon": h,
            "n_decisions": G_pool,
            "n_obs": N_pool,
            "se_cluster": se,
            "t_crit_alpha": stats.t.ppf(0.975, df=df_pool_deg),
            "t_crit_power": stats.t.ppf(0.80, df=df_pool_deg),
            "mde_coef": mde,
            "mde_bp_per_std": mde * 10000,
            "mde_pct_per_std": mde * 100,
            "notes": "Estimated from in-sample final_fit event-clustered covariance"
        })

    # -------------------------------------------------------------
    # 4. Out-of-Sample Test Split Projections (NO OUTCOMES LOADED)
    # -------------------------------------------------------------
    # Sample A: Full Test Set (N=70 decisions)
    # Sample B: Pristine Test Set (N=56 decisions)
    # Standard errors scale strictly inversely with sqrt(G_test) relative to pooled final_fit
    test_designs = [
        ("Full Test Split (Sample A)", 70, 2590, "Sample A: 70 total test decisions (includes 14 ECB overlap)"),
        ("Pristine Test Split (Sample B)", 56, 2072, "Sample B: 56 pure unblinded decisions (0 prior exposure)"),
    ]

    for d_name, g_test, n_test, d_notes in test_designs:
        df_deg_test = g_test - len(x_pool) - 1
        scale_factor = np.sqrt(G_pool / g_test)
        for h in HORIZONS:
            se_proj = se_pool_map[h] * scale_factor
            mde = compute_mde(se_proj, df_t=df_deg_test)
            out_records.append({
                "design": d_name,
                "tier": "pooled_test",
                "split": "test",
                "horizon": h,
                "n_decisions": g_test,
                "n_obs": n_test,
                "se_cluster": se_proj,
                "t_crit_alpha": stats.t.ppf(0.975, df=df_deg_test),
                "t_crit_power": stats.t.ppf(0.80, df=df_deg_test),
                "mde_coef": mde,
                "mde_bp_per_std": mde * 10000,
                "mde_pct_per_std": mde * 100,
                "notes": f"Projected from pooled design variance without unblinding test outcomes; {d_notes}"
            })

    df_out = pd.DataFrame(out_records)
    out_dir = ROOT / "outputs" / "modeling"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "power_analysis_mde.csv"
    df_out.to_csv(out_path, index=False)
    print(f"\nWrote MDE analysis across {len(df_out)} specifications to {out_path}")

    # Print summary table for headline 5-day horizon
    print("\n--- SUMMARY: MINIMUM DETECTABLE EFFECT (MDE) AT 5-DAY HORIZON (clr_5) ---")
    sub_5d = df_out[df_out["horizon"] == "clr_5"][["design", "n_decisions", "se_cluster", "mde_coef", "mde_bp_per_std", "mde_pct_per_std"]]
    print(sub_5d.to_string(index=False))

    return df_out


if __name__ == "__main__":
    run_power_analysis()
