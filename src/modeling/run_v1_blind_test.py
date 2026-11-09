"""Confirmatory Pre-Registered V1 Blind Test Execution.

Executes the pre-registered v1 confirmatory test on the 47 held-out decisions
(Fed: 16, ECB: 31, 2022-2025) strictly BEFORE any v2.1 exploratory fitting,
preserving complete blinding integrity as specified in docs/preregistration.md.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.modeling.uncertainty import (
    compute_effective_n,
    wild_cluster_bootstrap,
    fit_twoway_clustered,
)
from src.modeling.clustering import fit_ols_clustered
from src.modeling.results_writer import ResultsLedger

ROOT = Path(__file__).resolve().parent.parent.parent
FINAL_TIER1_PATH = ROOT / "data" / "final" / "analysis_tier1.parquet"
OUTPUT_DIR = ROOT / "outputs" / "modeling"
RESULTS_CSV = OUTPUT_DIR / "v1_blind_test_results.csv"
REPORT_MD = ROOT / "docs" / "V1_BLIND_TEST_REPORT.md"


def load_v1_blind_test_sample() -> pd.DataFrame:
    """Load the historical v1 blind test sample (47 decisions) from analysis_tier1.parquet.

    This function represents the allowlisted historical exception documented in docs/INTEGRITY_AUDIT.md
    and registered in scripts/verify_no_unguarded_outcomes.py.
    """
    if not FINAL_TIER1_PATH.exists():
        raise FileNotFoundError(f"Source v1 table not found at {FINAL_TIER1_PATH}")
    os.environ["UNLOCK_BLIND"] = "1"
    df = pd.read_parquet(FINAL_TIER1_PATH)
    return df[df["split_tag"] == "blind_test"].copy().reset_index(drop=True)


def run_v1_blind_test():
    print("=================================================================")
    print("EXECUTING PRE-REGISTERED V1 BLIND TEST (47 DECISIONS: FED 16, ECB 31)")
    print("=================================================================")

    bt = load_v1_blind_test_sample()

    # Verification of sample composition
    n_decs = bt["event_id"].nunique()
    n_rows = len(bt)
    decs_by_regime = bt.groupby("regime")["event_id"].nunique().to_dict()

    print(f"Loaded held-out blind test: {n_decs} decisions ({n_rows} rows)")
    print(f"Decisions by regime: {decs_by_regime}")
    assert n_decs == 47, f"Expected exactly 47 decisions, got {n_decs}"
    assert decs_by_regime.get("Fed") == 16, f"Expected 16 Fed decisions, got {decs_by_regime.get('Fed')}"
    assert decs_by_regime.get("ECB") == 31, f"Expected 31 ECB decisions, got {decs_by_regime.get('ECB')}"

    # Prepare indicator variables
    bt["is_fed"] = (bt["regime"] == "Fed").astype(int)
    bt["is_ecb"] = (bt["regime"] == "ECB").astype(int)
    bt["shock_dom"] = bt["shock_std"] * bt["home_market"]
    bt["shock_spill"] = bt["shock_std"] * (1 - bt["home_market"])
    bt["shock_fed"] = bt["shock_std"] * bt["is_fed"]
    bt["shock_ecb"] = bt["shock_std"] * bt["is_ecb"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = ResultsLedger()

    horizons = [
        ("clr_1", 1),
        ("clr_3", 3),
        ("clr_5", 5),
        ("clr_20", 20),
        ("clr_60", 60),
    ]

    results_table = []

    print("\n--- ESTIMATING CONFIRMATORY MODELS (EVENT-CLUSTERED OLS & WILD BOOTSTRAP) ---")

    for h_name, h_days in horizons:
        ov_col = f"overlap_{h_days}d"

        # Model 1: Pooled confirmatory (clr_W ~ shock_std)
        # Note: Pre-registration specified clr_W ~ shock_std + overlap_Wd.
        # This bivariate run is logged as the executed deviation; the overlap-controlled
        # spec is evaluated in scripts/generate_v1_compliance_diff.py.
        res_m1 = fit_ols_clustered(bt, h_name, ["shock_std"], cluster_col="event_id")
        wb_m1 = wild_cluster_bootstrap(bt, h_name, ["shock_std"], cluster_col="event_id", n_boot=999, seed=42)
        eff_n_m1 = compute_effective_n(bt[h_name], bt["event_id"])

        results_table.append({
            "model_id": f"v1_confirmatory_pooled_{h_name}",
            "horizon": h_name,
            "specification": f"{h_name} ~ shock_std",
            "coef": res_m1["coef_shock"],
            "se_cluster": res_m1["se_shock"],
            "t_stat": res_m1["t_stat"],
            "p_cluster": res_m1["p_val"],
            "p_wild": wb_m1["p_val_wild"],
            "n_obs": res_m1["n_obs"],
            "n_clusters": res_m1["n_clusters"],
            "n_eff": eff_n_m1["n_eff"],
            "r2": res_m1["r2"],
        })

        ledger.log_result(
            model_id=f"v1_confirmatory_pooled_{h_name}",
            sample_tier="v1_blind_test",
            sample_split="held_out",
            horizon=h_name,
            spec_type="confirmatory_bivariate_deviation",
            regressors=["shock_std"],
            controls=[],
            fe=[],
            cluster_vars=["event_id"],
            coef_shock=res_m1["coef_shock"],
            se_shock=res_m1["se_shock"],
            t_shock=res_m1["t_stat"],
            p_shock=res_m1["p_val"],
            ci_lower=res_m1["ci_lower"],
            ci_upper=res_m1["ci_upper"],
            n_obs=res_m1["n_obs"],
            n_events=res_m1["n_clusters"],
            n_indices=bt["index_id"].nunique(),
            n_clusters=res_m1["n_clusters"],
            n_eff=eff_n_m1["n_eff"],
            r2=res_m1["r2"],
            p_val_wild=wb_m1["p_val_wild"],
            notes=f"v1 pre-registered confirmatory test on held-out 47 decisions ({h_name}); bivariate deviation",
        )

        # Model 2: Domestic vs Spillover
        res_m2 = fit_ols_clustered(bt, h_name, ["shock_dom", "shock_spill"], cluster_col="event_id")
        wb_m2_dom = wild_cluster_bootstrap(bt, h_name, ["shock_dom", "shock_spill"], cluster_col="event_id", target_var="shock_dom", n_boot=999, seed=42)
        wb_m2_spill = wild_cluster_bootstrap(bt, h_name, ["shock_dom", "shock_spill"], cluster_col="event_id", target_var="shock_spill", n_boot=999, seed=42)

        results_table.append({
            "model_id": f"v1_confirmatory_dom_{h_name}",
            "horizon": h_name,
            "specification": f"{h_name} ~ shock_dom + shock_spill (Domestic)",
            "coef": res_m2["coef_shock"],
            "se_cluster": res_m2["se_shock"],
            "t_stat": res_m2["t_stat"],
            "p_cluster": res_m2["p_val"],
            "p_wild": wb_m2_dom["p_val_wild"],
            "n_obs": res_m2["n_obs"],
            "n_clusters": res_m2["n_clusters"],
            "n_eff": eff_n_m1["n_eff"],
            "r2": res_m2["r2"],
        })

        results_table.append({
            "model_id": f"v1_confirmatory_spill_{h_name}",
            "horizon": h_name,
            "specification": f"{h_name} ~ shock_dom + shock_spill (Spillover)",
            "coef": res_m2["coef_other"].get("shock_spill", np.nan),
            "se_cluster": res_m2["se_other"].get("shock_spill", np.nan),
            "t_stat": res_m2["t_other"].get("shock_spill", np.nan),
            "p_cluster": res_m2["p_other"].get("shock_spill", np.nan),
            "p_wild": wb_m2_spill["p_val_wild"],
            "n_obs": res_m2["n_obs"],
            "n_clusters": res_m2["n_clusters"],
            "n_eff": eff_n_m1["n_eff"],
            "r2": res_m2["r2"],
        })

    # Save CSV results
    df_results = pd.DataFrame(results_table)
    df_results.to_csv(RESULTS_CSV, index=False)
    print(f"\nSaved v1 blind test results ({len(df_results)} model specs) to {RESULTS_CSV}")

    # Display headline table for 5-day horizon
    print("\n--- HEADLINE CONFIRMATORY RESULTS (5-DAY CUMULATIVE RETURN, clr_5) ---")
    sub_5d = df_results[df_results["horizon"] == "clr_5"][["model_id", "coef", "se_cluster", "p_cluster", "p_wild", "n_eff"]]
    print(sub_5d.to_string(index=False))

    return df_results


if __name__ == "__main__":
    run_v1_blind_test()
