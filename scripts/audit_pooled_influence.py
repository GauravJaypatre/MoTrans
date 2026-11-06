"""Audit event-level leverage, influence, and sensitivity in the pooled specification.

Phase 0 Item (e):
- Full model: clr_5 ~ shock_raw_bp_fold_std + shock_tier on Pooled final_fit (G=349, N=12,943).
- Compute event-level influence via leave-one-event-out (LOEO) and event DFBETA / Cook's distance.
- Refit without top 1% (4 events), top 2% (7 events), and top 5% (18 events) most influential events.
- Report N_decs, N_rows, beta, event-clustered SE, t, p_cluster, and wild bootstrap p for each.
- Output top influential events and summary to outputs/modeling/pooled_influence_audit.csv.
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
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.tier_handler import prepare_tier_sample
from src.modeling.pipeline import FoldSafeScaler
from src.modeling.uncertainty import wild_cluster_bootstrap


def main():
    print("=================================================================")
    print("PHASE 0 (e): EVENT-LEVEL LEVERAGE & INFLUENCE AUDIT (POOLED SPEC)")
    print("=================================================================")

    # 1. Load Pooled sample in final_fit
    df_raw = prepare_tier_sample(tier="pooled", split="final_fit")
    scaler = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler.fit(df_raw, allow_final_fit=True)
    df = scaler.transform(df_raw)

    y_col = "clr_5"
    x_cols = ["shock_raw_bp_fold_std", "shock_tier"]
    target = x_cols[0]

    # Full sample fit
    Y = df[y_col].values
    X = sm.add_constant(df[x_cols]).values
    clusters = df["event_id"].values
    unique_events = np.unique(clusters)
    G = len(unique_events)

    m_full = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clusters})
    b_full = float(m_full.params[1])
    se_full = float(m_full.bse[1])
    t_full = float(m_full.tvalues[1])
    p_full = float(m_full.pvalues[1])

    wb_full = wild_cluster_bootstrap(df, y_col, x_cols, cluster_col="event_id", target_var=target, n_boot=999, seed=42)
    p_wild_full = float(wb_full["p_val_wild"])

    print(f"Full Model (G={G}, N={len(df)}):")
    print(f"  beta = {b_full:+.6f}, SE = {se_full:.6f}, t = {t_full:.3f}, p_cluster = {p_full:.4f}, p_wild = {p_wild_full:.4f}")

    # 2. Leave-One-Event-Out Influence
    print("\nComputing Leave-One-Event-Out (LOEO) across all 349 events...")
    event_meta = df[["event_id", "regime", "decision_date", "shock_raw_bp", "shock_raw_bp_fold_std", "shock_tier"]].drop_duplicates("event_id").set_index("event_id")

    # Pre-index events
    event_indices = {eid: np.where(clusters == eid)[0] for eid in unique_events}
    influence_records = []

    # Pre-compute X'X and X'Y
    XtX = X.T @ X
    XtY = X.T @ Y

    for eid in unique_events:
        idx = event_indices[eid]
        X_e = X[idx]
        Y_e = Y[idx]
        
        # Downdate (X'X)_{-e} and (X'Y)_{-e}
        XtX_sub = XtX - X_e.T @ X_e
        XtY_sub = XtY - X_e.T @ Y_e
        
        try:
            beta_sub = np.linalg.solve(XtX_sub, XtY_sub)
            b_target_sub = float(beta_sub[1])
        except Exception:
            # Fallback to direct slice
            mask = clusters != eid
            m_sub = sm.OLS(Y[mask], X[mask]).fit()
            b_target_sub = float(m_sub.params[1])

        delta_b = b_full - b_target_sub
        influence_records.append({
            "event_id": eid,
            "regime": event_meta.loc[eid, "regime"],
            "decision_date": str(event_meta.loc[eid, "decision_date"]),
            "shock_raw_bp": float(event_meta.loc[eid, "shock_raw_bp"]),
            "shock_std": float(event_meta.loc[eid, "shock_raw_bp_fold_std"]),
            "shock_tier": int(event_meta.loc[eid, "shock_tier"]),
            "beta_without_event": b_target_sub,
            "delta_beta": delta_b,
            "abs_delta_beta": abs(delta_b),
        })

    df_inf = pd.DataFrame(influence_records).sort_values("abs_delta_beta", ascending=False)
    df_inf["rank_influence"] = np.arange(1, len(df_inf) + 1)
    # DFBETA standardized by full SE
    df_inf["dfbeta"] = df_inf["delta_beta"] / se_full

    # Top 15 influential events
    print("\n--- TOP 15 MOST INFLUENTIAL EVENTS IN POOLED MODEL ---")
    top15 = df_inf.head(15)[["rank_influence", "event_id", "regime", "decision_date", "shock_raw_bp", "shock_tier", "delta_beta", "dfbeta"]]
    print(top15.to_string(index=False))

    # 3. Trimming Sensitivity: Top 1% (4 events), Top 2% (7 events), Top 5% (18 events)
    trim_levels = [
        ("Top 1%", int(np.ceil(0.01 * G))), # 4 events
        ("Top 2%", int(np.ceil(0.02 * G))), # 7 events
        ("Top 5%", int(np.ceil(0.05 * G))), # 18 events
    ]

    trim_results = [{
        "trim_level": "None (Full Sample)",
        "events_dropped": 0,
        "n_events": G,
        "n_obs": len(df),
        "coef_shock": b_full,
        "se_shock": se_full,
        "t_stat": t_full,
        "p_cluster": p_full,
        "p_wild": p_wild_full,
    }]

    for label, k in trim_levels:
        dropped_events = set(df_inf.head(k)["event_id"])
        sub_df = df[~df["event_id"].isin(dropped_events)].copy()
        
        # Fit OLS clustered
        Y_sub = sub_df[y_col].values
        X_sub = sm.add_constant(sub_df[x_cols]).values
        clust_sub = sub_df["event_id"].values
        
        m_trim = sm.OLS(Y_sub, X_sub).fit(cov_type="cluster", cov_kwds={"groups": clust_sub})
        b_trim = float(m_trim.params[1])
        se_trim = float(m_trim.bse[1])
        t_trim = float(m_trim.tvalues[1])
        p_trim = float(m_trim.pvalues[1])
        
        wb_trim = wild_cluster_bootstrap(sub_df, y_col, x_cols, cluster_col="event_id", target_var=target, n_boot=999, seed=42)
        
        trim_results.append({
            "trim_level": f"Drop {label} Most Influential",
            "events_dropped": k,
            "n_events": int(sub_df["event_id"].nunique()),
            "n_obs": len(sub_df),
            "coef_shock": b_trim,
            "se_shock": se_trim,
            "t_stat": t_trim,
            "p_cluster": p_trim,
            "p_wild": float(wb_trim["p_val_wild"]),
        })

    df_trim_summary = pd.DataFrame(trim_results)
    print("\n--- SENSITIVITY TABLE: REFITTING WITHOUT INFLUENTIAL EVENTS ---")
    print(df_trim_summary.to_string(index=False))

    # Save influence table and summary
    out_dir = ROOT / "outputs" / "modeling"
    out_dir.mkdir(parents=True, exist_ok=True)
    df_inf.to_csv(out_dir / "pooled_event_influence.csv", index=False)
    df_trim_summary.to_csv(out_dir / "pooled_influence_trim_sensitivity.csv", index=False)
    print(f"\nWrote event influence rankings to {out_dir / 'pooled_event_influence.csv'}")
    print(f"Wrote trim sensitivity table to {out_dir / 'pooled_influence_trim_sensitivity.csv'}")


if __name__ == "__main__":
    main()

