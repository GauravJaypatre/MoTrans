"""Update the full modeling ledger with all runs from current and prior passes.

Task 4c:
- Add every run from this and prior pass:
  (1) Compliance diff runs (pre-registered overlap spec for v1 blind test)
  (2) Window timing robustness runs (out-of-session, in-session, and lead placebos)
  (3) Inference variants from Task 1 (alternative clustering structures, wild bootstrap)
- Recompute Holm-Bonferroni and Benjamini-Hochberg FDR adjustments over the expanded ledger.
- Report old (61) and new model counts, and print summary statistics.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LEDGER_CSV = ROOT / "outputs" / "modeling" / "ledger.csv"


def holm_bonferroni(p_vals: np.ndarray) -> np.ndarray:
    """Compute Holm-Bonferroni step-down adjusted p-values."""
    p = np.asarray(p_vals, dtype=float)
    m = len(p)
    sort_idx = np.argsort(p)
    sorted_p = p[sort_idx]
    adj_p = np.empty(m, dtype=float)
    current_max = 0.0
    for i in range(m):
        rank = i + 1
        val = (m - rank + 1) * sorted_p[i]
        current_max = max(current_max, val)
        adj_p[i] = min(1.0, current_max)
    out = np.empty(m, dtype=float)
    out[sort_idx] = adj_p
    return out


def benjamini_hochberg(p_vals: np.ndarray) -> np.ndarray:
    """Compute Benjamini-Hochberg FDR adjusted p-values."""
    p = np.asarray(p_vals, dtype=float)
    m = len(p)
    sort_idx = np.argsort(p)
    sorted_p = p[sort_idx]
    adj_p = np.empty(m, dtype=float)
    current_min = 1.0
    for i in range(m - 1, -1, -1):
        rank = i + 1
        val = (m / rank) * sorted_p[i]
        current_min = min(current_min, val)
        adj_p[i] = min(1.0, current_min)
    out = np.empty(m, dtype=float)
    out[sort_idx] = adj_p
    return out


def main():
    print("=================================================================")
    print("UPDATING MODELING LEDGER ACROSS ALL EXPANDED RUNS")
    print("=================================================================")

    if not LEDGER_CSV.exists():
        raise FileNotFoundError(f"Ledger file not found at {LEDGER_CSV}")

    ledger = pd.read_csv(LEDGER_CSV)
    old_count = len(ledger)
    existing_ids = set(ledger["model_id"].tolist())
    print(f"Loaded existing ledger: {old_count} models.")

    ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_rows: List[Dict[str, Any]] = []

    # 1. Compliance diff runs (pre-registered overlap models from v1_compliance_diff.csv)
    comp_path = ROOT / "outputs" / "modeling" / "v1_compliance_diff.csv"
    if comp_path.exists():
        df_comp = pd.read_csv(comp_path)
        for _, r in df_comp.iterrows():
            if "Pre-Registered" in r["spec_type"]:
                mid = f"V1_BLIND_PREREG_OVERLAP_{r['horizon'].upper()}"
                if mid not in existing_ids:
                    h = r["horizon"]
                    se = float(r["cluster_se"])
                    b = float(r["beta"])
                    new_rows.append({
                        "model_id": mid,
                        "timestamp_utc": ts_now,
                        "model_name": f"v1_blind_prereg_{h}",
                        "tier": "tier1",
                        "sample": "blind_test",
                        "fold": "none",
                        "outcome_col": h,
                        "shock_col": "shock_std",
                        "specification": r["specification"],
                        "n_obs": 1786,
                        "n_events": 47,
                        "n_clusters": 47,
                        "coef_shock": b,
                        "se_shock": se,
                        "t_stat": b / se if se > 0 else 0.0,
                        "p_val": float(r["p_cluster"]),
                        "ci_lower": b - 1.96 * se,
                        "ci_upper": b + 1.96 * se,
                        "r2": np.nan,
                        "caveats": "pre-registered confirmatory with forward window overlap control",
                    })
                    existing_ids.add(mid)

    # 2. Window timing robustness runs (from window_timing_robustness.csv)
    timing_path = ROOT / "outputs" / "modeling" / "window_timing_robustness.csv"
    if timing_path.exists():
        df_timing = pd.read_csv(timing_path)
        for idx, r in df_timing.iterrows():
            # Build unique model id based on sample, timing, spec, and outcome
            timing_tag = "OUTSESS" if "Out-of-Session" in r["window_timing"] else ("INSESS" if "In-Session" in r["window_timing"] else "FULL")
            s_tag = "V1" if r["sample"] == "v1_blind_test" else ("T1" if r["sample"] == "tier1_final_fit" else "POOL")
            spec_tag = "LEAD" if "Lead" in r["specification"] else ("PREREG" if "Pre-registered" in r["specification"] else "BIV")
            h_tag = r["outcome_col"].upper()

            mid = f"ROBUST_{s_tag}_{timing_tag}_{spec_tag}_{h_tag}"
            if mid not in existing_ids:
                b = float(r["coef_shock"])
                se = float(r["se_shock"])
                new_rows.append({
                    "model_id": mid,
                    "timestamp_utc": ts_now,
                    "model_name": f"robust_timing_{s_tag.lower()}_{timing_tag.lower()}_{h_tag.lower()}",
                    "tier": "tier1" if s_tag in ["V1", "T1"] else "pooled",
                    "sample": r["sample"],
                    "fold": "none",
                    "outcome_col": r["outcome_col"],
                    "shock_col": r["shock_col"],
                    "specification": f"{r['specification']} [{r['window_timing']}]",
                    "n_obs": int(r["n_obs"]),
                    "n_events": int(r["n_events"]),
                    "n_clusters": int(r["n_events"]),
                    "coef_shock": b,
                    "se_shock": se,
                    "t_stat": float(r["t_stat"]),
                    "p_val": float(r["p_cluster"]),
                    "ci_lower": b - 1.96 * se,
                    "ci_upper": b + 1.96 * se,
                    "r2": np.nan,
                    "caveats": f"window timing robustness: {r['window_timing']}; wild_p={r['p_wild']:.4f}",
                })
                existing_ids.add(mid)

    # 3. Inference clustering comparison runs (from inference_clustering_comparison.csv)
    inf_path = ROOT / "outputs" / "modeling" / "inference_clustering_comparison.csv"
    if inf_path.exists():
        df_inf = pd.read_csv(inf_path)
        for idx, r in df_inf.iterrows():
            scheme = r["clustering_scheme"]
            # Exclude unclustered OLS as invalid, but log other genuine cluster structures
            if "Unclustered" in scheme or "primary baseline" in scheme:
                continue
            m_label = "T1" if "Tier 1" in r["model"] else "POOL"
            c_tag = "TWOWAY" if "Two-Way" in scheme else ("MONTH" if "decision_month" in scheme else ("REGYEAR" if "regime_year" in scheme else "WILD"))
            mid = f"INFER_{m_label}_{c_tag}_CLR5"
            if mid not in existing_ids:
                b = float(r["coef"])
                se = float(r["se"])
                new_rows.append({
                    "model_id": mid,
                    "timestamp_utc": ts_now,
                    "model_name": f"infer_cluster_{m_label.lower()}_{c_tag.lower()}_clr5",
                    "tier": "tier1" if m_label == "T1" else "pooled",
                    "sample": "final_fit",
                    "fold": "none",
                    "outcome_col": "clr_5",
                    "shock_col": "shock_raw_bp_fold_std",
                    "specification": f"clr_5 ~ shock_raw_bp_fold_std [{scheme}]",
                    "n_obs": 8832 if m_label == "T1" else 12943,
                    "n_events": 239 if m_label == "T1" else 349,
                    "n_clusters": int(r["n_clusters"]),
                    "coef_shock": b,
                    "se_shock": se,
                    "t_stat": float(r["t_stat"]),
                    "p_val": float(r["p_val"]),
                    "ci_lower": b - 1.96 * se,
                    "ci_upper": b + 1.96 * se,
                    "r2": np.nan,
                    "caveats": f"inference sensitivity: {scheme}",
                })
                existing_ids.add(mid)

    if new_rows:
        df_new = pd.DataFrame(new_rows)
        # Ensure all columns match
        for col in ledger.columns:
            if col not in df_new.columns:
                df_new[col] = np.nan
        df_new = df_new[ledger.columns.drop(["p_val_holm", "p_val_bh_fdr"])]
        combined = pd.concat([ledger.drop(columns=["p_val_holm", "p_val_bh_fdr"]), df_new], ignore_index=True)
    else:
        combined = ledger.drop(columns=["p_val_holm", "p_val_bh_fdr"]).copy()

    # Recompute multiplicity corrections over the ENTIRE expanded ledger
    p_vals = combined["p_val"].values
    combined["p_val_holm"] = holm_bonferroni(p_vals)
    combined["p_val_bh_fdr"] = benjamini_hochberg(p_vals)

    combined.to_csv(LEDGER_CSV, index=False)
    new_count = len(combined)

    print(f"\nExpanded Ledger updated successfully:")
    print(f"  Old model count: {old_count}")
    print(f"  New models added: {len(new_rows)}")
    print(f"  New total model count: {new_count}")

    # Summary statistics
    n_raw_sig = int((combined["p_val"] < 0.05).sum())
    n_holm_sig = int((combined["p_val_holm"] < 0.05).sum())
    n_bh_sig = int((combined["p_val_bh_fdr"] < 0.05).sum())

    print(f"\nMultiplicity Summary across {new_count} models in ledger:")
    print(f"  Raw p < 0.05:      {n_raw_sig} / {new_count} ({n_raw_sig/new_count*100:.1f}%)")
    print(f"  Holm p < 0.05:     {n_holm_sig} / {new_count} ({n_holm_sig/new_count*100:.1f}%)")
    print(f"  BH-FDR p < 0.05:   {n_bh_sig} / {new_count} ({n_bh_sig/new_count*100:.1f}%)")


if __name__ == "__main__":
    main()
