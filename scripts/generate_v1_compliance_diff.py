"""Generate pre-registration compliance side-by-side comparison for v1 blind test.

Compares:
1. Executed bivariate specification: clr_W ~ shock_std
2. Pre-registered overlap specification: clr_W ~ shock_std + overlap_Wd
Across all five pre-registered horizons: W in {1, 3, 5, 20, 60}.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.clustering import fit_ols_clustered
from src.modeling.uncertainty import wild_cluster_bootstrap, compute_effective_n


def run_compliance_diff() -> pd.DataFrame:
    parquet_path = ROOT / "data" / "final" / "analysis_tier1.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing {parquet_path}")

    df = pd.read_parquet(parquet_path)
    bt = df[df["split_tag"] == "blind_test"].copy().reset_index(drop=True)

    n_decs = bt["event_id"].nunique()
    assert n_decs == 47, f"Expected 47 decisions, got {n_decs}"

    horizons = [("clr_1", 1), ("clr_3", 3), ("clr_5", 5), ("clr_20", 20), ("clr_60", 60)]
    records = []

    for h, w in horizons:
        ov_col = f"overlap_{w}d"
        eff_n = compute_effective_n(bt[h], bt["event_id"])

        # 1. Bivariate specification (executed deviation)
        ols_biv = fit_ols_clustered(bt, h, ["shock_std"], cluster_col="event_id")
        wild_biv = wild_cluster_bootstrap(bt, h, ["shock_std"], cluster_col="event_id", n_boot=999, seed=42)

        # 2. Pre-registered overlap specification
        if bt[ov_col].nunique() > 1:
            ols_ov = fit_ols_clustered(bt, h, ["shock_std", ov_col], cluster_col="event_id")
            wild_ov = wild_cluster_bootstrap(bt, h, ["shock_std", ov_col], cluster_col="event_id", n_boot=999, seed=42)
        else:
            # When overlap_Wd is constant across sample (W=20, 60), it is collinear with intercept
            ols_ov = ols_biv
            wild_ov = wild_biv

        records.append({
            "horizon": h,
            "spec_type": "Executed Deviation (Bivariate)",
            "specification": f"{h} ~ shock_std",
            "beta": ols_biv["coef_shock"],
            "cluster_se": ols_biv["se_shock"],
            "p_cluster": ols_biv["p_val"],
            "p_wild": wild_biv["p_val_wild"],
            "n_eff": eff_n["n_eff"],
        })
        records.append({
            "horizon": h,
            "spec_type": "Pre-Registered (Overlap Controlled)",
            "specification": f"{h} ~ shock_std + {ov_col}",
            "beta": ols_ov["coef_shock"],
            "cluster_se": ols_ov["se_shock"],
            "p_cluster": ols_ov["p_val"],
            "p_wild": wild_ov["p_val_wild"],
            "n_eff": eff_n["n_eff"],
        })

    df_res = pd.DataFrame(records)
    return df_res


def main():
    print("=================================================================")
    print("V1 BLIND TEST: PRE-REGISTRATION SPECIFICATION COMPARISON")
    print("=================================================================")
    df_res = run_compliance_diff()

    print("\nSide-by-Side Specification Table:")
    print(df_res.to_string(index=False))

    out_csv = ROOT / "outputs" / "modeling" / "v1_compliance_diff.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_res.to_csv(out_csv, index=False)
    print(f"\nSaved results to {out_csv}")


if __name__ == "__main__":
    main()
