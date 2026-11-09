"""Verify robustness of monetary transmission estimates to window timing (announce_in_session).

Task 2:
17,301 of 82,054 decision-index pairs have announce_in_session == 1
(reaction window starts at previous close and includes pre-announcement morning trading).
- Rerun v1 blind test (both specs: clr_W ~ shock_std, and clr_W ~ shock_std + overlap_Wd; all 5 horizons)
  on out-of-session (announce_in_session == 0) and in-session (announce_in_session == 1) subsets.
- Rerun Tier 1 and Pooled final_fit headline specs on out-of-session and in-session subsets.
- Rerun lead placebo (clr_pre5 ~ shock) on both subsets across samples.
- Report side-by-side: N_decs, N_rows, beta, event-clustered SE, wild p.
- Save results to outputs/modeling/window_timing_robustness.csv.
"""

from __future__ import annotations

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

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.data_loader import load_modeling_data
from src.modeling.pipeline import FoldSafeScaler
from src.modeling.tier_handler import prepare_tier_sample
from src.modeling.uncertainty import wild_cluster_bootstrap


def fit_model_robustness(
    df: pd.DataFrame,
    y_col: str,
    x_cols: List[str],
    sample_label: str,
    spec_label: str,
    timing_label: str,
    cluster_col: str = "event_id",
    n_boot: int = 999,
    seed: int = 42,
) -> Dict[str, Any]:
    """Fit OLS clustered by event_id and compute wild cluster bootstrap p-value."""
    req = [y_col] + x_cols + [cluster_col]
    clean = df.dropna(subset=req).copy()
    if clean.empty:
        return {
            "sample": sample_label,
            "specification": spec_label,
            "window_timing": timing_label,
            "outcome_col": y_col,
            "shock_col": x_cols[0],
            "n_events": 0,
            "n_obs": 0,
            "coef_shock": np.nan,
            "se_shock": np.nan,
            "t_stat": np.nan,
            "p_cluster": np.nan,
            "p_wild": np.nan,
        }

    target = x_cols[0]
    Y = clean[y_col]
    X = sm.add_constant(clean[x_cols])

    m = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean[cluster_col]})
    beta = float(m.params[target])
    se = float(m.bse[target])
    t_val = float(m.tvalues[target])
    p_clust = float(m.pvalues[target])

    wb = wild_cluster_bootstrap(clean, y_col, x_cols, cluster_col=cluster_col, target_var=target, n_boot=n_boot, seed=seed)

    return {
        "sample": sample_label,
        "specification": spec_label,
        "window_timing": timing_label,
        "outcome_col": y_col,
        "shock_col": target,
        "n_events": int(clean[cluster_col].nunique()),
        "n_obs": int(len(clean)),
        "coef_shock": beta,
        "se_shock": se,
        "t_stat": t_val,
        "p_cluster": p_clust,
        "p_wild": float(wb["p_val_wild"]),
    }


def main():
    print("=================================================================")
    print("TASK 2: PRE-ANNOUNCEMENT RETURNS AND WINDOW TIMING ROBUSTNESS")
    print("=================================================================")

    # Load master events table for timing and pre-event lead return
    events_path = ROOT / "data" / "final" / "events.parquet"
    ev = pd.read_parquet(events_path)[["event_id", "index_id", "announce_in_session", "clr_pre5"]]

    results = []

    # -------------------------------------------------------------
    # 1. v1 Blind Test (47 decisions)
    # -------------------------------------------------------------
    print("\n[1/3] Running v1 Blind Test Timing Robustness (47 decisions)...")
    from src.modeling.run_v1_blind_test import load_v1_blind_test_sample
    bt = load_v1_blind_test_sample()
    if "clr_pre5" not in bt.columns:
        bt = bt.merge(ev[["event_id", "index_id", "clr_pre5"]], on=["event_id", "index_id"], how="left")

    horizons = ["clr_1", "clr_3", "clr_5", "clr_20", "clr_60"]

    timing_groups = [
        ("Full Sample", bt),
        ("Out-of-Session (Clean, announce_in_session=0)", bt[bt["announce_in_session"] == 0]),
        ("In-Session (Contaminated Morning, announce_in_session=1)", bt[bt["announce_in_session"] == 1]),
    ]

    for timing_lbl, sub_df in timing_groups:
        for h in horizons:
            # Spec A: Bivariate (clr_W ~ shock_std)
            res_a = fit_model_robustness(
                df=sub_df,
                y_col=h,
                x_cols=["shock_std"],
                sample_label="v1_blind_test",
                spec_label="clr_W ~ shock_std (Bivariate)",
                timing_label=timing_lbl,
            )
            results.append(res_a)

            # Spec B: Pre-registered overlap (clr_W ~ shock_std + overlap_Wd)
            ov_col = f"overlap_{h.split('_')[1]}d"
            x_b = ["shock_std", ov_col] if ov_col in sub_df.columns else ["shock_std"]
            res_b = fit_model_robustness(
                df=sub_df,
                y_col=h,
                x_cols=x_b,
                sample_label="v1_blind_test",
                spec_label=f"clr_W ~ shock_std + {ov_col} (Pre-registered)",
                timing_label=timing_lbl,
            )
            results.append(res_b)

        # Lead Placebo on v1 (clr_pre5 ~ shock_std)
        res_lp_v1 = fit_model_robustness(
            df=sub_df,
            y_col="clr_pre5",
            x_cols=["shock_std"],
            sample_label="v1_blind_test",
            spec_label="clr_pre5 ~ shock_std (Lead Placebo)",
            timing_label=timing_lbl,
        )
        results.append(res_lp_v1)

    # -------------------------------------------------------------
    # 2. Tier 1 Final Fit Headline (239 decisions)
    # -------------------------------------------------------------
    print("\n[2/3] Running Tier 1 Final Fit Timing Robustness (239 decisions)...")
    df_t1 = load_modeling_data("tier1", split="final_fit")
    scaler_t1 = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_t1.fit(df_t1, allow_final_fit=True)
    df_t1_s = scaler_t1.transform(df_t1)
    df_t1_s = df_t1_s.merge(ev[["event_id", "index_id", "announce_in_session", "clr_pre5"]], on=["event_id", "index_id"], how="left")

    t1_timing_groups = [
        ("Full Sample", df_t1_s),
        ("Out-of-Session (Clean, announce_in_session=0)", df_t1_s[df_t1_s["announce_in_session"] == 0]),
        ("In-Session (Contaminated Morning, announce_in_session=1)", df_t1_s[df_t1_s["announce_in_session"] == 1]),
    ]

    for timing_lbl, sub_df in t1_timing_groups:
        # Tier 1 headline: clr_5 ~ shock_raw_bp_fold_std
        res_t1_h = fit_model_robustness(
            df=sub_df,
            y_col="clr_5",
            x_cols=["shock_raw_bp_fold_std"],
            sample_label="tier1_final_fit",
            spec_label="clr_5 ~ shock_raw_bp_fold_std (Headline)",
            timing_label=timing_lbl,
        )
        results.append(res_t1_h)

        # Lead Placebo on Tier 1
        res_t1_lp = fit_model_robustness(
            df=sub_df,
            y_col="clr_pre5",
            x_cols=["shock_raw_bp_fold_std"],
            sample_label="tier1_final_fit",
            spec_label="clr_pre5 ~ shock_raw_bp_fold_std (Lead Placebo)",
            timing_label=timing_lbl,
        )
        results.append(res_t1_lp)

    # -------------------------------------------------------------
    # 3. Pooled Final Fit Headline (349 decisions)
    # -------------------------------------------------------------
    print("\n[3/3] Running Pooled Final Fit Timing Robustness (349 decisions)...")
    df_pooled = prepare_tier_sample(tier="pooled", split="final_fit")
    scaler_p = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_p.fit(df_pooled, allow_final_fit=True)
    df_p_s = scaler_p.transform(df_pooled)
    df_p_s = df_p_s.merge(ev[["event_id", "index_id", "announce_in_session", "clr_pre5"]], on=["event_id", "index_id"], how="left")

    p_timing_groups = [
        ("Full Sample", df_p_s),
        ("Out-of-Session (Clean, announce_in_session=0)", df_p_s[df_p_s["announce_in_session"] == 0]),
        ("In-Session (Contaminated Morning, announce_in_session=1)", df_p_s[df_p_s["announce_in_session"] == 1]),
    ]

    for timing_lbl, sub_df in p_timing_groups:
        # Pooled headline: clr_5 ~ shock_raw_bp_fold_std + shock_tier
        res_p_h = fit_model_robustness(
            df=sub_df,
            y_col="clr_5",
            x_cols=["shock_raw_bp_fold_std", "shock_tier"],
            sample_label="pooled_final_fit",
            spec_label="clr_5 ~ shock_raw_bp_fold_std + shock_tier (Headline)",
            timing_label=timing_lbl,
        )
        results.append(res_p_h)

        # Lead Placebo on Pooled
        res_p_lp = fit_model_robustness(
            df=sub_df,
            y_col="clr_pre5",
            x_cols=["shock_raw_bp_fold_std", "shock_tier"],
            sample_label="pooled_final_fit",
            spec_label="clr_pre5 ~ shock_raw_bp_fold_std + shock_tier (Lead Placebo)",
            timing_label=timing_lbl,
        )
        results.append(res_p_lp)

    # Save to CSV
    out_df = pd.DataFrame(results)
    out_csv = ROOT / "outputs" / "modeling" / "window_timing_robustness.csv"
    out_df.to_csv(out_csv, index=False)
    print(f"\nWrote {len(out_df)} timing robustness models to {out_csv}")

    # Print summary table
    print("\n=== SUMMARY TABLE OF WINDOW TIMING ROBUSTNESS ===")
    cols_show = ["sample", "specification", "window_timing", "outcome_col", "n_events", "n_obs", "coef_shock", "se_shock", "p_cluster", "p_wild"]
    print(out_df[cols_show].to_string(index=False))


if __name__ == "__main__":
    main()
