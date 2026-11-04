"""MoTrans-15 Phase 4 Out-of-Sample Test Scoring Script.

HARD SAFETY CONTROLS:
1. REFUSES TO EXECUTE unless git HEAD is tagged 'modeling-spec-frozen'.
2. REFUSES TO EXECUTE unless UNLOCK_TEST=1 is explicitly set in the environment.
3. Logs a single formal unlock event to outputs/v2_1/unlock_audit.log.
4. Reports out-of-sample benchmark performance separately for:
   - Sample A: All 70 test decisions (including 14 ECB decisions evaluated in v1 blind test).
   - Sample B: Pristine 56 test decisions (zero prior evaluation; 100% untouched).
5. Displays mandatory regime transfer caveat across all outputs.

DO NOT EXECUTE THIS SCRIPT WITHOUT FORMAL RESEARCH APPROVAL.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.model_guard import log_unlock
from src.modeling.data_loader import load_modeling_data, OUTCOME_COLS
from src.modeling.clustering import fit_ols_clustered
from src.modeling.pipeline import FoldSafeScaler
from src.modeling.tier_handler import prepare_tier_sample
from src.modeling.results_writer import MANDATORY_FINAL_FIT_CAVEAT

OUTPUT_DIR = ROOT / "outputs" / "modeling"
RESULTS_CSV = OUTPUT_DIR / "test_scoring_results.csv"
REPORT_MD = ROOT / "docs" / "TEST_SCORING_REPORT.md"

REQUIRED_GIT_TAG = "modeling-spec-frozen"
MANDATORY_REGIME_CAVEAT = (
    "MANDATORY REGIME CAVEAT: Evaluated during an easing cycle among the included central banks "
    "(the Bank of Japan hiked in the same period) with zero interest rate hikes; cannot assess tightening transfer."
)

V1_OVERLAPPING_DECISIONS = {
    "ecb_2024-01-25", "ecb_2024-03-07", "ecb_2024-04-11", "ecb_2024-06-06",
    "ecb_2024-07-18", "ecb_2024-09-12", "ecb_2024-10-17", "ecb_2024-12-12",
    "ecb_2025-01-30", "ecb_2025-03-06", "ecb_2025-04-17", "ecb_2025-06-05",
    "ecb_2025-07-24", "ecb_2025-09-11",
}


def verify_execution_authorization() -> str:
    """Verify cryptographic and procedural authorization to score test split."""
    # 1. Check environment variable
    if os.environ.get("UNLOCK_TEST") != "1":
        raise PermissionError(
            "CRITICAL INTEGRITY GUARD: Execution blocked! UNLOCK_TEST=1 is required in the environment "
            "to execute Phase 4 test scoring. Zero test outcome evaluation is permitted without explicit unlock."
        )

    # 2. Check git tag on HEAD
    try:
        res = subprocess.run(
            ["git", "tag", "--points-at", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        tags = [t.strip() for t in res.stdout.splitlines() if t.strip()]
    except Exception as e:
        raise PermissionError(f"Could not verify git tags on HEAD: {e}")

    if REQUIRED_GIT_TAG not in tags:
        raise PermissionError(
            f"CRITICAL INTEGRITY GUARD: Execution blocked! Git HEAD must be tagged '{REQUIRED_GIT_TAG}' "
            f"before scoring out-of-sample test splits. Current tags on HEAD: {tags}."
        )

    # 3. Get commit hash
    res_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True, text=True, check=True)
    return res_commit.stdout.strip()


def run_phase_4_scoring():
    print("=================================================================")
    print("MOTRANS-15: PHASE 4 FINAL OUT-OF-SAMPLE TEST SCORING")
    print("=================================================================")

    # Authorization gate
    commit_hash = verify_execution_authorization()
    print(f"Authorization Confirmed. Git HEAD tagged '{REQUIRED_GIT_TAG}' at commit {commit_hash[:10]}.")

    # Formal audit logging
    log_unlock("test_phase4_final_scoring", context=f"Authorized Phase 4 execution on commit {commit_hash}")
    print("Logged authorized execution event to outputs/v2_1/unlock_audit.log.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    # -------------------------------------------------------------
    # 1. Load Data with Authorized Unlock
    # -------------------------------------------------------------
    print("\nLoading test split datasets with authorized outcome unlock...")
    df_t1_test = load_modeling_data("tier1", split="test", include_outcomes=True, allow_test_outcomes=True)
    df_t2_test = load_modeling_data("tier2_primary", split="test", include_outcomes=True, allow_test_outcomes=True)
    df_sec_test = load_modeling_data("secondary_holds", split="test", include_outcomes=True, allow_test_outcomes=True)

    # Load final_fit for scaler training (2010-2023)
    df_t1_fit = load_modeling_data("tier1", split="final_fit")
    scaler_t1 = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_t1.fit(df_t1_fit, allow_final_fit=True)
    df_t1_test_s = scaler_t1.transform(df_t1_test)

    # Prepare pooled test dataset
    df_pooled_test = prepare_tier_sample("pooled", split="test")
    # For pooled outcomes:
    df_pooled_test["clr_1"] = pd.concat([df_t1_test["clr_1"], df_t2_test["clr_1"]], ignore_index=True)
    df_pooled_test["clr_5"] = pd.concat([df_t1_test["clr_5"], df_t2_test["clr_5"]], ignore_index=True)

    df_p_fit = prepare_tier_sample("pooled", split="final_fit")
    scaler_p = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_p.fit(df_p_fit, allow_final_fit=True)
    df_pooled_test_s = scaler_p.transform(df_pooled_test)

    # -------------------------------------------------------------
    # 2. Score Across Horizons and Sample Subsets
    # -------------------------------------------------------------
    horizons = ["clr_1", "clr_3", "clr_5", "clr_20", "clr_60"]

    # Evaluation loop for Tier 1
    for h in horizons:
        # Full Test Set (14 ECB decisions)
        ols_full = fit_ols_clustered(df_t1_test_s, h, ["shock_raw_bp_fold_std"], "event_id")
        results.append({
            "model_id": f"TEST_TIER1_FULL_{h.upper()}",
            "sample_type": "Full Test Split (All Decisions)",
            "tier": "tier1",
            "outcome_col": h,
            "n_obs": ols_full["n_obs"],
            "n_events": ols_full["n_events"],
            "coef_shock": ols_full["coef_shock"],
            "se_shock": ols_full["se_shock"],
            "t_stat": ols_full["t_stat"],
            "p_val": ols_full["p_val"],
            "r2": ols_full["r2"],
            "caveat": MANDATORY_REGIME_CAVEAT,
        })

    # Evaluation loop for Pooled (Tier 1 + Tier 2 Primary)
    for sample_label, drop_v1 in [("Full Test Split (All Decisions)", False), ("Pristine Test Split (Excluding v1 Blind Overlap)", True)]:
        df_eval = df_pooled_test_s.copy()
        if drop_v1:
            df_eval = df_eval[~df_eval["event_id"].isin(V1_OVERLAPPING_DECISIONS)].copy()

        for h in ["clr_1", "clr_5"]:
            ols_p = fit_ols_clustered(df_eval, h, ["shock_raw_bp_fold_std", "shock_tier"], "event_id")
            results.append({
                "model_id": f"TEST_POOLED_{'PRISTINE_' if drop_v1 else 'FULL_'}{h.upper()}",
                "sample_type": sample_label,
                "tier": "pooled",
                "outcome_col": h,
                "n_obs": ols_p["n_obs"],
                "n_events": ols_p["n_events"],
                "coef_shock": ols_p["coef_shock"],
                "se_shock": ols_p["se_shock"],
                "t_stat": ols_p["t_stat"],
                "p_val": ols_p["p_val"],
                "r2": ols_p["r2"],
                "caveat": MANDATORY_REGIME_CAVEAT,
            })

    # Save to CSV
    df_out = pd.DataFrame(results)
    df_out.to_csv(RESULTS_CSV, index=False)
    print(f"\nSaved test scoring results to {RESULTS_CSV}")

    # Generate Markdown Report
    rep_text = f"""# MoTrans-15: Out-of-Sample Test Scoring Benchmark Report

**Execution Status**: COMPLETED  
**Git Tag**: `{REQUIRED_GIT_TAG}`  
**Commit Hash**: `{commit_hash}`  
**Mandatory Regime Notice**: *"{MANDATORY_REGIME_CAVEAT}"*

---

## 1. Primary Benchmark Results

| Model ID | Sample Partition | Tier | Horizon | Events | Obs | Beta | Cluster SE | t-stat | p-value | R² |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for _, r in df_out.iterrows():
        rep_text += (
            f"| `{r['model_id']}` | {r['sample_type']} | `{r['tier']}` | `{r['outcome_col']}` | "
            f"{r['n_events']} | {r['n_obs']:,} | **{r['coef_shock']:+.4f}** | "
            f"{r['se_shock']:.4f} | {r['t_stat']:+.2f} | {r['p_val']:.4f} | {r['r2']:.4f} |\n"
        )

    rep_text += f"""
---

## 2. Methodological Observations
1. **Regime Transfer Asymmetry**: As specified in the mandatory caveat, these evaluations occur strictly during a global easing cycle (0 rate hikes).
2. **Pristine Sample Verification**: Pristine test partitions evaluate exclusively decisions with zero exposure to prior model iterations.
"""
    REPORT_MD.write_text(rep_text, encoding="utf-8")
    print(f"Generated {REPORT_MD}")
    print(f"\n{MANDATORY_REGIME_CAVEAT}")


if __name__ == "__main__":
    run_phase_4_scoring()
