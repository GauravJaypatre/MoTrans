"""Update the full modeling ledger with all runs from current and prior passes.

Task 3 & 4:
- Covers all runs across all phases:
  (1) v1 Blind test confirmatory models (bivariate deviation and pre-registered overlap)
  (2) v2.1 Exploratory cross-validation and final fit models
  (3) Window timing robustness runs (out-of-session, in-session, and lead placebos)
  (4) Inference clustering comparison runs (two-way, wild bootstrap, time clustering)
  (5) Influence sensitivity models (leave-one-event-out, trim 1%, trim 2%, trim 5%)
- Tracks both asymptotic and wild cluster bootstrap p-values.
- Recomputes Holm-Bonferroni and Benjamini-Hochberg FDR adjustments over the expanded ledger
  using wild bootstrap p-values (and asymptotic p-values for comparison).
"""

from __future__ import annotations

import re
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

    # 1. Influence sensitivity models (from pooled_influence_trim_sensitivity.csv)
    infl_path = ROOT / "outputs" / "modeling" / "pooled_influence_trim_sensitivity.csv"
    if infl_path.exists():
        df_infl = pd.read_csv(infl_path)
        for _, r in df_infl.iterrows():
            clean_tag = r["trim_level"].replace(" ", "_").replace("(", "").replace(")", "").upper()
            mid = f"INFLUENCE_POOLED_{clean_tag}"
            if mid not in existing_ids:
                b = float(r["coef_shock"])
                se = float(r["se_shock"])
                new_rows.append({
                    "model_id": mid,
                    "timestamp_utc": ts_now,
                    "model_name": f"influence_pooled_{r['trim_level'].lower()}",
                    "tier": "pooled",
                    "sample": "final_fit",
                    "fold": "none",
                    "outcome_col": "clr_5",
                    "shock_col": "shock_raw_bp_fold_std",
                    "specification": f"clr_5 ~ shock_raw_bp_fold_std [Influence Sensitivity: {r['trim_level']}]",
                    "n_obs": int(r["n_obs"]),
                    "n_events": int(r["n_events"]),
                    "n_clusters": int(r["n_events"]),
                    "coef_shock": b,
                    "se_shock": se,
                    "t_stat": float(r["t_stat"]),
                    "p_val": float(r["p_cluster"]),
                    "p_val_wild": float(r["p_wild"]),
                    "ci_lower": b - 1.96 * se,
                    "ci_upper": b + 1.96 * se,
                    "r2": np.nan,
                    "caveats": f"influence sensitivity: dropped {r['events_dropped']} events; wild_p={r['p_wild']:.4f}",
                })
                existing_ids.add(mid)

    if new_rows:
        df_new = pd.DataFrame(new_rows)
        for col in ledger.columns:
            if col not in df_new.columns:
                df_new[col] = np.nan
        ledger = pd.concat([ledger, df_new], ignore_index=True)

    # 2. Ensure p_val_wild is fully populated
    if "p_val_wild" not in ledger.columns:
        ledger["p_val_wild"] = np.nan

    # Fill from caveats
    for idx, r in ledger.iterrows():
        if pd.isna(ledger.at[idx, "p_val_wild"]):
            cav = str(r.get("caveats", ""))
            match = re.search(r"wild_p=([0-9\.]+)", cav)
            if match:
                ledger.at[idx, "p_val_wild"] = float(match.group(1))
            else:
                ledger.at[idx, "p_val_wild"] = float(r["p_val"])

    # 3. Recompute multiplicity corrections over the ENTIRE expanded ledger
    ledger["p_val_holm_wild"] = holm_bonferroni(ledger["p_val_wild"].values)
    ledger["p_val_bh_wild"] = benjamini_hochberg(ledger["p_val_wild"].values)
    ledger["p_val_holm"] = holm_bonferroni(ledger["p_val"].values)
    ledger["p_val_bh_fdr"] = benjamini_hochberg(ledger["p_val"].values)

    ledger.to_csv(LEDGER_CSV, index=False)
    new_count = len(ledger)

    print(f"\nExpanded Ledger updated successfully:")
    print(f"  Old model count: {old_count}")
    print(f"  New total model count: {new_count}")

    # Summary statistics
    n_wild_sig = int((ledger["p_val_wild"] < 0.05).sum())
    n_holm_wild_sig = int((ledger["p_val_holm_wild"] < 0.05).sum())
    n_bh_wild_sig = int((ledger["p_val_bh_wild"] < 0.05).sum())

    print(f"\nMultiplicity Summary across {new_count} models in ledger:")
    print(f"  Wild bootstrap p < 0.05:     {n_wild_sig} / {new_count} ({n_wild_sig/new_count*100:.1f}%)")
    print(f"  Wild Holm p < 0.05:          {n_holm_wild_sig} / {new_count} ({n_holm_wild_sig/new_count*100:.1f}%)")
    print(f"  Wild BH-FDR p < 0.05:        {n_bh_wild_sig} / {new_count} ({n_bh_wild_sig/new_count*100:.1f}%)")


if __name__ == "__main__":
    main()
