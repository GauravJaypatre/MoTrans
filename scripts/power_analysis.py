"""Statistical Power & Minimum Detectable Effect (MDE) Analysis for MoTrans-15.

Phase 1 Item 7 & Task 1 (v2.2 Hardening):
Computes the Minimum Detectable Effect (MDE) at 80% power and 5% two-sided significance
using:
1. Asymptotic event-clustered SE (full sample)
2. Wild cluster bootstrap SE (from Rademacher bootstrap distribution)
3. Event-clustered SE after dropping Top 1%, Top 2%, and Top 5% most influential events
4. Headline Robust MDE based on max(SE) across these specifications to prevent distortion
   from high-leverage outlier events (e.g., cbr_2014-12-16).

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
from src.modeling.uncertainty import wild_cluster_bootstrap

HORIZONS = ["clr_1", "clr_3", "clr_5", "clr_20", "clr_60"]


def compute_mde(se: float, df_t: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """Compute Minimum Detectable Effect (MDE).
    
    MDE = (t_{1 - alpha/2, df} + t_{power, df}) * SE
    """
    t_alpha = stats.t.ppf(1.0 - alpha / 2.0, df=df_t)
    t_power = stats.t.ppf(power, df=df_t)
    return float((t_alpha + t_power) * se)


def get_influence_rankings(df: pd.DataFrame, y_col: str, x_cols: List[str], target_var: str) -> pd.DataFrame:
    """Compute Leave-One-Event-Out influence rankings."""
    clusters = df["event_id"].values
    unique_events = np.unique(clusters)
    
    Y = df[y_col].values
    X = sm.add_constant(df[x_cols]).values
    x_names = ["const"] + x_cols
    target_idx = x_names.index(target_var)

    m_full = sm.OLS(Y, X).fit()
    b_full = float(m_full.params[target_idx])

    XtX = X.T @ X
    XtY = X.T @ Y

    event_indices = {eid: np.where(clusters == eid)[0] for eid in unique_events}
    records = []
    for eid in unique_events:
        idx = event_indices[eid]
        X_e = X[idx]
        Y_e = Y[idx]

        XtX_sub = XtX - X_e.T @ X_e
        XtY_sub = XtY - X_e.T @ Y_e
        try:
            beta_sub = np.linalg.solve(XtX_sub, XtY_sub)
            b_sub = float(beta_sub[target_idx])
        except Exception:
            mask = clusters != eid
            m_sub = sm.OLS(Y[mask], X[mask]).fit()
            b_sub = float(m_sub.params[target_idx])

        delta_b = b_full - b_sub
        records.append({"event_id": eid, "abs_delta_b": abs(delta_b)})

    return pd.DataFrame(records).sort_values("abs_delta_b", ascending=False).reset_index(drop=True)


def evaluate_sample_mde(df: pd.DataFrame, tier_name: str, x_cols: list[str], target_var: str) -> list[dict]:
    records = []
    G = int(df["event_id"].nunique())
    N = len(df)
    df_deg = G - len(x_cols) - 1

    for h in HORIZONS:
        clean = df.dropna(subset=[h] + x_cols + ["event_id"]).copy()
        Y = clean[h].values
        X = sm.add_constant(clean[x_cols]).values
        clusters = clean["event_id"].values

        # 1. Full sample asymptotic cluster SE
        m_full = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clusters})
        se_asymptotic = float(m_full.bse[1])

        # 2. Wild bootstrap SE
        wb = wild_cluster_bootstrap(clean, y_col=h, x_cols=x_cols, cluster_col="event_id", target_var=target_var, n_boot=499, seed=42)
        se_wild = float(wb.get("se_wild", se_asymptotic))

        # 3. Trimmed influence SEs
        inf_ranks = get_influence_rankings(clean, y_col=h, x_cols=x_cols, target_var=target_var)
        
        # Trim top 1%, 2%, 5%
        k_1pct = max(1, int(np.ceil(0.01 * G)))
        k_2pct = max(1, int(np.ceil(0.02 * G)))
        k_5pct = max(1, int(np.ceil(0.05 * G)))

        def get_trim_se(k_drop):
            drop_eids = set(inf_ranks.head(k_drop)["event_id"])
            sub = clean[~clean["event_id"].isin(drop_eids)]
            m_sub = sm.OLS(sub[h].values, sm.add_constant(sub[x_cols]).values).fit(
                cov_type="cluster", cov_kwds={"groups": sub["event_id"].values}
            )
            return float(m_sub.bse[1])

        se_trim_1pct = get_trim_se(k_1pct)
        se_trim_2pct = get_trim_se(k_2pct)
        se_trim_5pct = get_trim_se(k_5pct)

        # Headline SE is max across robust specifications to prevent outlier distortion
        se_headline = max(se_asymptotic, se_wild, se_trim_1pct, se_trim_2pct, se_trim_5pct)
        mde_headline = compute_mde(se_headline, df_t=df_deg)
        mde_asymptotic = compute_mde(se_asymptotic, df_t=df_deg)

        records.append({
            "design": f"{tier_name} Final Fit",
            "tier": tier_name.lower().replace(" ", "_"),
            "split": "final_fit",
            "horizon": h,
            "n_decisions": G,
            "n_obs": N,
            "se_asymptotic": se_asymptotic,
            "se_wild_bootstrap": se_wild,
            "se_trim_1pct": se_trim_1pct,
            "se_trim_2pct": se_trim_2pct,
            "se_trim_5pct": se_trim_5pct,
            "se_headline_robust": se_headline,
            "mde_asymptotic_bp": mde_asymptotic * 10000,
            "mde_headline_bp": mde_headline * 10000,
            "mde_headline_pct": mde_headline * 100,
            "distortion_ratio_pct": (se_headline / se_asymptotic - 1.0) * 100,
            "notes": f"Headline MDE uses max robust SE (Trim 1% drop {k_1pct} events, Trim 2% drop {k_2pct}, Trim 5% drop {k_5pct})"
        })

    return records


def run_power_analysis():
    print("=================================================================")
    print("ROBUST POWER & MINIMUM DETECTABLE EFFECT (MDE) ANALYSIS")
    print("=================================================================")

    all_records = []

    # 1. Tier 1 Final Fit (239 decisions)
    print("Computing Tier 1 Final Fit...")
    df_t1 = prepare_tier_sample("tier1", split="final_fit", version="v2_2")
    scaler_t1 = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_t1.fit(df_t1, allow_final_fit=True)
    df_t1 = scaler_t1.transform(df_t1)
    rec_t1 = evaluate_sample_mde(df_t1, "Tier 1", ["shock_raw_bp_fold_std"], "shock_raw_bp_fold_std")
    all_records.extend(rec_t1)

    # 2. Tier 2 Primary Final Fit (110 decisions)
    print("Computing Tier 2 Primary Final Fit...")
    df_t2 = prepare_tier_sample("tier2_primary", split="final_fit", version="v2_2")
    scaler_t2 = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_t2.fit(df_t2, allow_final_fit=True)
    df_t2 = scaler_t2.transform(df_t2)
    rec_t2 = evaluate_sample_mde(df_t2, "Tier 2 Primary", ["shock_raw_bp_fold_std"], "shock_raw_bp_fold_std")
    all_records.extend(rec_t2)

    # 3. Pooled Final Fit (349 decisions)
    print("Computing Pooled Final Fit...")
    df_pool = prepare_tier_sample("pooled", split="final_fit", version="v2_2")
    scaler_pool = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_pool.fit(df_pool, allow_final_fit=True)
    df_pool = scaler_pool.transform(df_pool)
    rec_pool = evaluate_sample_mde(df_pool, "Pooled", ["shock_raw_bp_fold_std", "shock_tier"], "shock_raw_bp_fold_std")
    all_records.extend(rec_pool)

    # 4. Out-of-Sample Test Split Projections (NO OUTCOMES LOADED)
    # Using the headline robust Pooled SE as baseline for projections
    pooled_by_h = {r["horizon"]: r for r in rec_pool}
    G_pool = 349

    test_configs = [
        ("Full Test Split (Sample A)", "full_test_sample_a", 70, 2590, "Sample A: 70 total test decisions (includes 14 ECB prior overlap)"),
        ("Pristine Test Split (Sample B)", "pristine_test_sample_b", 56, 2072, "Sample B: 56 pure unblinded decisions (0 prior exposure, all Tier 2)"),
    ]

    for d_name, d_tier, g_test, n_test, d_notes in test_configs:
        scale_factor = np.sqrt(G_pool / g_test)
        df_deg_test = g_test - 2 - 1
        for h in HORIZONS:
            p_rec = pooled_by_h[h]
            se_asymp_proj = p_rec["se_asymptotic"] * scale_factor
            se_wild_proj = p_rec["se_wild_bootstrap"] * scale_factor
            se_trim1_proj = p_rec["se_trim_1pct"] * scale_factor
            se_trim2_proj = p_rec["se_trim_2pct"] * scale_factor
            se_trim5_proj = p_rec["se_trim_5pct"] * scale_factor
            se_headline_proj = p_rec["se_headline_robust"] * scale_factor

            mde_asymp = compute_mde(se_asymp_proj, df_t=df_deg_test)
            mde_headline = compute_mde(se_headline_proj, df_t=df_deg_test)

            all_records.append({
                "design": d_name,
                "tier": d_tier,
                "split": "test",
                "horizon": h,
                "n_decisions": g_test,
                "n_obs": n_test,
                "se_asymptotic": se_asymp_proj,
                "se_wild_bootstrap": se_wild_proj,
                "se_trim_1pct": se_trim1_proj,
                "se_trim_2pct": se_trim2_proj,
                "se_trim_5pct": se_trim5_proj,
                "se_headline_robust": se_headline_proj,
                "mde_asymptotic_bp": mde_asymp * 10000,
                "mde_headline_bp": mde_headline * 10000,
                "mde_headline_pct": mde_headline * 100,
                "distortion_ratio_pct": (se_headline_proj / se_asymp_proj - 1.0) * 100,
                "notes": f"Projected from robust pooled design variance without unblinding test outcomes; {d_notes}"
            })

    df_out = pd.DataFrame(all_records)
    out_dir = ROOT / "outputs" / "modeling"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "power_analysis_mde.csv"
    df_out.to_csv(out_path, index=False)
    print(f"\nWrote corrected robust MDE analysis to {out_path}")

    # Print summary table for headline 5-day horizon
    print("\n--- SUMMARY: MINIMUM DETECTABLE EFFECT (MDE) AT 5-DAY HORIZON (clr_5) ---")
    sub_5d = df_out[df_out["horizon"] == "clr_5"][[
        "design", "n_decisions", "se_asymptotic", "se_headline_robust", "mde_asymptotic_bp", "mde_headline_bp", "distortion_ratio_pct"
    ]]
    print(sub_5d.to_string(index=False))

    return df_out


if __name__ == "__main__":
    run_power_analysis()
