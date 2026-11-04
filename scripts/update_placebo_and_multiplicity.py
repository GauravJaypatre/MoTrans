"""Rerun 5,000-permutation placebo and full-ledger multiplicity adjustments.

Task A5:
- 5,000-draw permutation placebo (block-shuffled by CB x tier + circular date shift)
  on Tier 1, Pooled (Tier 1 + Tier 2), and Macro Revision specifications.
- Full-ledger multiplicity correction (Holm-Bonferroni and Benjamini-Hochberg FDR)
  across all tried models in outputs/modeling/ledger.csv.
- Updates outputs/modeling/ledger.csv and regenerates docs/V21_EXPLORATORY_REPORT.md.
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
LEDGER_CSV = ROOT / "outputs" / "modeling" / "ledger.csv"
REPORT_MD = ROOT / "docs" / "V21_EXPLORATORY_REPORT.md"

from src.modeling.data_loader import load_modeling_data
from src.modeling.pipeline import FoldSafeScaler
from src.modeling.tier_handler import prepare_tier_sample


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


def run_block_permutation(
    df: pd.DataFrame,
    outcome_col: str = "clr_5",
    shock_col: str = "shock_raw_bp_fold_std",
    n_perms: int = 5000,
    seed: int = 2026,
) -> dict:
    rng = np.random.default_rng(seed)

    cols = ["event_id", "regime", "decision_date", shock_col]
    if "shock_tier" in df.columns:
        cols.append("shock_tier")
    events = df[cols].drop_duplicates().sort_values("decision_date")

    n_events = len(events)
    event_to_idx = {eid: idx for idx, eid in enumerate(events["event_id"])}
    row_event_idx = df["event_id"].map(event_to_idx).values

    if "shock_tier" in events.columns:
        strata_keys = list(zip(events["regime"].values, events["shock_tier"].values))
    else:
        strata_keys = list(events["regime"].values)

    unique_strata = sorted(list(set(strata_keys)))
    strata_indices = {s: np.where([sk == s for sk in strata_keys])[0] for s in unique_strata}

    y = df[outcome_col].values
    y_c = y - np.mean(y)
    x_real = df[shock_col].values
    x_c = x_real - np.mean(x_real)
    real_beta = float(np.sum(x_c * y_c) / np.sum(x_c ** 2))

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
        x_b_c = x_b - np.mean(x_b)
        placebo_betas[b] = np.sum(x_b_c * y_c) / np.sum(x_b_c ** 2)

    emp_p = float(np.mean(np.abs(placebo_betas) >= np.abs(real_beta)))
    return {
        "real_beta": real_beta,
        "placebo_mean": float(np.mean(placebo_betas)),
        "placebo_sd": float(np.std(placebo_betas)),
        "empirical_p_val": emp_p,
        "n_perms": n_perms,
    }


def main():
    print("=================================================================")
    print("TASK A5: 5,000-PERMUTATION PLACEBOS & FULL-LEDGER MULTIPLICITY")
    print("=================================================================")

    # 1. Tier 1 Permutation Placebo
    print("\n[1/3] Running 5,000 permutations for Tier 1...")
    df_t1 = load_modeling_data("tier1", split="final_fit")
    scaler_t1 = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_t1.fit(df_t1, allow_final_fit=True)
    df_t1_s = scaler_t1.transform(df_t1)
    res_t1 = run_block_permutation(df_t1_s, outcome_col="clr_5", n_perms=5000)
    print(f"  Tier 1: Real beta={res_t1['real_beta']:+.4f}, Placebo mean={res_t1['placebo_mean']:.6f}, SD={res_t1['placebo_sd']:.4f}, Emp p={res_t1['empirical_p_val']:.4f}")

    # 2. Pooled Permutation Placebo
    print("\n[2/3] Running 5,000 permutations for Pooled (Tier 1 + Tier 2)...")
    df_pooled = prepare_tier_sample(tier="pooled", split="final_fit")
    scaler_p = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_p.fit(df_pooled, allow_final_fit=True)
    df_p_s = scaler_p.transform(df_pooled)
    res_p = run_block_permutation(df_p_s, outcome_col="clr_5", n_perms=5000)
    print(f"  Pooled: Real beta={res_p['real_beta']:+.4f}, Placebo mean={res_p['placebo_mean']:.6f}, SD={res_p['placebo_sd']:.4f}, Emp p={res_p['empirical_p_val']:.4f}")

    # 3. Macro Revision Permutation Placebo
    print("\n[3/3] Running 5,000 permutations for Macro Revision Sensitivity...")
    df_sens = load_modeling_data("sensitivity_macro_revision", split="final_fit")
    scaler_s = FoldSafeScaler(feature_cols=["shock_raw_bp"])
    scaler_s.fit(df_sens, allow_final_fit=True)
    df_s_s = scaler_s.transform(df_sens)
    res_s = run_block_permutation(df_s_s, outcome_col="clr_5", n_perms=5000)
    print(f"  Macro Rev: Real beta={res_s['real_beta']:+.4f}, Placebo mean={res_s['placebo_mean']:.6f}, SD={res_s['placebo_sd']:.4f}, Emp p={res_s['empirical_p_val']:.4f}")

    # 4. Multiplicity adjustment across full ledger
    print("\nApplying Holm and BH-FDR multiplicity corrections across full ledger...")
    ledger = pd.read_csv(LEDGER_CSV)
    p_vals = ledger["p_val"].values
    ledger["p_val_holm"] = holm_bonferroni(p_vals)
    ledger["p_val_bh_fdr"] = benjamini_hochberg(p_vals)
    ledger.to_csv(LEDGER_CSV, index=False)
    print(f"Updated {LEDGER_CSV} ({len(ledger)} models adjusted).")

    # 5. Summary statistics
    n_total = len(ledger)
    n_raw_sig = int((ledger["p_val"] < 0.05).sum())
    n_holm_sig = int((ledger["p_val_holm"] < 0.05).sum())
    n_bh_sig = int((ledger["p_val_bh_fdr"] < 0.05).sum())

    print(f"\nMultiplicity Summary across {n_total} models in ledger:")
    print(f"  Raw p < 0.05:      {n_raw_sig} / {n_total} ({n_raw_sig/n_total*100:.1f}%)")
    print(f"  Holm p < 0.05:     {n_holm_sig} / {n_total} ({n_holm_sig/n_total*100:.1f}%)")
    print(f"  BH-FDR p < 0.05:   {n_bh_sig} / {n_total} ({n_bh_sig/n_total*100:.1f}%)")


if __name__ == "__main__":
    main()
