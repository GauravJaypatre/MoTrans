"""Audit inference procedures across headline models and alternative clustering structures.

Task 1:
- Print full permutation distributions (mean, sd, 2.5/97.5 percentiles, count of |beta_perm| >= |beta_real|)
  for headline specs: Tier 1, Pooled (with tier indicator and bivariate), and Macro Revision.
  Report exact permutation p with the +1 correction.
- Compare standard errors clustered by:
  (1) event_id
  (2) index_id
  (3) two-way (event_id, index_id)
  (4) decision_month (YYYY-MM)
  (5) regime_year (central bank x year)
- Compare with Wild Cluster Bootstrap (Rademacher at event_id level).
- Output results to CSV and JSON for inclusion in docs/INFERENCE_AUDIT.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.data_loader import load_modeling_data
from src.modeling.pipeline import FoldSafeScaler
from src.modeling.tier_handler import prepare_tier_sample
from src.modeling.uncertainty import wild_cluster_bootstrap, fit_twoway_clustered


def run_event_permutation_distribution(
    df: pd.DataFrame,
    outcome_col: str = "clr_5",
    shock_col: str = "shock_raw_bp_fold_std",
    covariates: List[str] | None = None,
    n_perms: int = 5000,
    seed: int = 2026,
) -> Dict[str, Any]:
    """Run event-level block permutation and return complete distribution details."""
    rng = np.random.default_rng(seed)

    # Base event-level table
    event_cols = ["event_id", "regime", "decision_date", shock_col]
    if "shock_tier" in df.columns:
        event_cols.append("shock_tier")
    events = df[event_cols].drop_duplicates().sort_values("decision_date")

    n_events = len(events)
    event_to_idx = {eid: idx for idx, eid in enumerate(events["event_id"])}
    row_event_idx = df["event_id"].map(event_to_idx).values

    if "shock_tier" in events.columns:
        strata_keys = list(zip(events["regime"].values, events["shock_tier"].values))
    else:
        strata_keys = list(events["regime"].values)

    unique_strata = sorted(list(set(strata_keys)))
    strata_indices = {s: np.where([sk == s for sk in strata_keys])[0] for s in unique_strata}

    # If covariates are present (e.g., shock_tier), residualize y and x or do full OLS
    y = df[outcome_col].values
    if covariates:
        # Frisch-Waugh-Lovell on covariates (e.g. constant + shock_tier)
        Z = sm.add_constant(df[covariates].values)
        gamma_y = np.linalg.lstsq(Z, y, rcond=None)[0]
        y_star = y - Z @ gamma_y
    else:
        y_star = y - np.mean(y)

    x_real = df[shock_col].values
    if covariates:
        Z = sm.add_constant(df[covariates].values)
        gamma_x = np.linalg.lstsq(Z, x_real, rcond=None)[0]
        x_real_star = x_real - Z @ gamma_x
    else:
        x_real_star = x_real - np.mean(x_real)

    real_beta = float(np.sum(x_real_star * y_star) / np.sum(x_real_star ** 2))

    base_shocks = events[shock_col].values
    placebo_betas = np.empty(n_perms, dtype=float)

    for b in range(n_perms):
        perm_s = np.empty(n_events, dtype=float)
        for s, idxs in strata_indices.items():
            n_s = len(idxs)
            shift = rng.integers(0, n_s) if n_s > 1 else 0
            shuffled = rng.permutation(base_shocks[idxs])
            perm_s[idxs] = np.roll(shuffled, shift)
        x_b = perm_s[row_event_idx]
        if covariates:
            gamma_xb = np.linalg.lstsq(Z, x_b, rcond=None)[0]
            x_b_star = x_b - Z @ gamma_xb
        else:
            x_b_star = x_b - np.mean(x_b)
        placebo_betas[b] = np.sum(x_b_star * y_star) / np.sum(x_b_star ** 2)

    abs_real = abs(real_beta)
    count_extreme = int(np.sum(np.abs(placebo_betas) >= abs_real))
    emp_p_standard = float(count_extreme / n_perms)
    emp_p_plus1 = float((1 + count_extreme) / (n_perms + 1))

    q025 = float(np.percentile(placebo_betas, 2.5))
    q975 = float(np.percentile(placebo_betas, 97.5))

    return {
        "real_beta": real_beta,
        "n_perms": n_perms,
        "placebo_mean": float(np.mean(placebo_betas)),
        "placebo_sd": float(np.std(placebo_betas)),
        "placebo_p025": q025,
        "placebo_p975": q975,
        "count_extreme": count_extreme,
        "p_perm_standard": emp_p_standard,
        "p_perm_plus1": emp_p_plus1,
    }


def compute_clustering_comparison(
    df: pd.DataFrame,
    y_col: str,
    x_cols: List[str],
) -> pd.DataFrame:
    """Compute SEs and p-values under 5 clustering schemes plus wild bootstrap."""
    clean = df.dropna(subset=[y_col] + x_cols).copy()
    clean["decision_month"] = pd.to_datetime(clean["decision_date"]).dt.to_period("M").astype(str)
    clean["regime_year"] = clean["regime"].astype(str) + "_" + pd.to_datetime(clean["decision_date"]).dt.year.astype(str)

    target = x_cols[0]
    Y = clean[y_col]
    X = sm.add_constant(clean[x_cols])

    # 1. Base OLS unclustered
    m_ols = sm.OLS(Y, X).fit()
    beta = float(m_ols.params[target])

    results = []

    # Unclustered OLS
    results.append({
        "clustering_scheme": "Unclustered (homoskedastic OLS)",
        "cluster_var": "none",
        "n_clusters": len(clean),
        "coef": beta,
        "se": float(m_ols.bse[target]),
        "t_stat": float(m_ols.tvalues[target]),
        "p_val": float(m_ols.pvalues[target]),
        "inference_type": "Asymptotic OLS",
    })

    # One-way schemes
    schemes = [
        ("Clustered by event_id (primary baseline)", "event_id"),
        ("Clustered by index_id", "index_id"),
        ("Clustered by decision_month (YYYY-MM)", "decision_month"),
        ("Clustered by central bank x year (regime_year)", "regime_year"),
    ]

    for label, cvar in schemes:
        m = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean[cvar]})
        results.append({
            "clustering_scheme": label,
            "cluster_var": cvar,
            "n_clusters": int(clean[cvar].nunique()),
            "coef": beta,
            "se": float(m.bse[target]),
            "t_stat": float(m.tvalues[target]),
            "p_val": float(m.pvalues[target]),
            "inference_type": "Cluster-robust asymptotic",
        })

    # Two-way clustered: event_id and index_id
    tw = fit_twoway_clustered(clean, y_col, x_cols, cluster1="event_id", cluster2="index_id")
    results.append({
        "clustering_scheme": "Two-Way Clustered (event_id x index_id)",
        "cluster_var": "event_id + index_id",
        "n_clusters": tw["n_cluster1"],
        "coef": beta,
        "se": float(tw["se_twoway"]),
        "t_stat": float(tw["t_stat_twoway"]),
        "p_val": float(tw["p_val_twoway"]),
        "inference_type": "Two-way Cameron-Gelbach-Miller (2011)",
    })

    # Wild cluster bootstrap at event_id level
    wb = wild_cluster_bootstrap(clean, y_col, x_cols, cluster_col="event_id", target_var=target, n_boot=999, seed=42)
    m_ev = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean["event_id"]})
    results.append({
        "clustering_scheme": "Wild Cluster Bootstrap (Rademacher at event_id)",
        "cluster_var": "event_id",
        "n_clusters": int(clean["event_id"].nunique()),
        "coef": beta,
        "se": float(m_ev.bse[target]),
        "t_stat": float(m_ev.tvalues[target]),
        "p_val": float(wb["p_val_wild"]),
        "inference_type": "Restricted Wild Cluster Bootstrap (999 draws)",
    })

    return pd.DataFrame(results)


def main():
    print("=================================================================")
    print("AUDIT OF INFERENCE PROCEDURES AND CLUSTERING ROBUSTNESS")
    print("=================================================================")

    # 1. Load samples
    # Tier 1 final_fit
    df_t1 = load_modeling_data("tier1", split="final_fit")
    scaler_t1 = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_t1.fit(df_t1, allow_final_fit=True)
    df_t1_s = scaler_t1.transform(df_t1)

    # Pooled final_fit
    df_p = prepare_tier_sample(tier="pooled", split="final_fit")
    scaler_p = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_p.fit(df_p, allow_final_fit=True)
    df_p_s = scaler_p.transform(df_p)

    # Macro revision final_fit
    df_s = load_modeling_data("sensitivity_macro_revision", split="final_fit")
    scaler_s = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_s.fit(df_s, allow_final_fit=True)
    df_s_s = scaler_s.transform(df_s)

    # -------------------------------------------------------------
    # A. Permutation Distributions
    # -------------------------------------------------------------
    print("\n--- [A] 5,000 Permutation Distributions ---")
    perm_results = {}

    # Tier 1 (bivariate)
    print("Running Tier 1 (clr_5 ~ shock)...")
    perm_t1 = run_event_permutation_distribution(df_t1_s, outcome_col="clr_5", shock_col="shock_raw_bp_fold_std")
    perm_results["Tier 1 (final_fit)"] = perm_t1

    # Pooled with tier indicator
    print("Running Pooled with tier indicator (clr_5 ~ shock + shock_tier)...")
    perm_p_cov = run_event_permutation_distribution(
        df_p_s, outcome_col="clr_5", shock_col="shock_raw_bp_fold_std", covariates=["shock_tier"]
    )
    perm_results["Pooled with tier indicator (final_fit)"] = perm_p_cov

    # Pooled bivariate
    print("Running Pooled bivariate (clr_5 ~ shock)...")
    perm_p_biv = run_event_permutation_distribution(df_p_s, outcome_col="clr_5", shock_col="shock_raw_bp_fold_std")
    perm_results["Pooled bivariate (final_fit)"] = perm_p_biv

    # Macro revision sensitivity
    print("Running Macro Revision (clr_5 ~ shock)...")
    perm_s = run_event_permutation_distribution(df_s_s, outcome_col="clr_5", shock_col="shock_raw_bp_fold_std")
    perm_results["Macro Revision Sensitivity (final_fit)"] = perm_s

    # Print distribution summary
    for k, v in perm_results.items():
        print(f"\nModel: {k}")
        print(f"  Real Beta:         {v['real_beta']:+.6f}")
        print(f"  Permutation Mean:  {v['placebo_mean']:+.6f}")
        print(f"  Permutation SD:    {v['placebo_sd']:.6f}")
        print(f"  2.5% Percentile:   {v['placebo_p025']:+.6f}")
        print(f"  97.5% Percentile:  {v['placebo_p975']:+.6f}")
        print(f"  Count |b|>=|real|: {v['count_extreme']} / {v['n_perms']}")
        print(f"  p (standard):      {v['p_perm_standard']:.5f}")
        print(f"  p (+1 corrected):  {v['p_perm_plus1']:.5f}")

    # Save to JSON
    json_path = ROOT / "outputs" / "modeling" / "permutation_distributions.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(perm_results, f, indent=2)
    print(f"\nWrote permutation distributions to {json_path}")

    # -------------------------------------------------------------
    # B. Clustering Comparison Check
    # -------------------------------------------------------------
    print("\n--- [B] Alternative Clustering Structures Comparison ---")

    print("\n[1] Tier 1 Headline (clr_5 ~ shock_raw_bp_fold_std):")
    df_clust_t1 = compute_clustering_comparison(df_t1_s, "clr_5", ["shock_raw_bp_fold_std"])
    df_clust_t1["model"] = "Tier 1 (final_fit)"
    print(df_clust_t1[["clustering_scheme", "n_clusters", "se", "t_stat", "p_val"]].to_string(index=False))

    print("\n[2] Pooled Headline with tier indicator (clr_5 ~ shock_raw_bp_fold_std + shock_tier):")
    df_clust_p = compute_clustering_comparison(df_p_s, "clr_5", ["shock_raw_bp_fold_std", "shock_tier"])
    df_clust_p["model"] = "Pooled with tier indicator (final_fit)"
    print(df_clust_p[["clustering_scheme", "n_clusters", "se", "t_stat", "p_val"]].to_string(index=False))

    print("\n[3] Pooled Bivariate (clr_5 ~ shock_raw_bp_fold_std):")
    df_clust_pb = compute_clustering_comparison(df_p_s, "clr_5", ["shock_raw_bp_fold_std"])
    df_clust_pb["model"] = "Pooled bivariate (final_fit)"
    print(df_clust_pb[["clustering_scheme", "n_clusters", "se", "t_stat", "p_val"]].to_string(index=False))

    all_clust = pd.concat([df_clust_t1, df_clust_p, df_clust_pb], ignore_index=True)
    csv_path = ROOT / "outputs" / "modeling" / "inference_clustering_comparison.csv"
    all_clust.to_csv(csv_path, index=False)
    print(f"\nWrote clustering comparison to {csv_path}")


if __name__ == "__main__":
    main()
