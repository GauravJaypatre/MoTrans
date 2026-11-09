"""Central bank statement label agreement toolkit — MoTrans-15.

Computes inter-annotator reliability metrics between two annotators' filled sheets:
  - Cohen's kappa (unweighted and quadratic-weighted)
  - Spearman rank correlation
  - Pearson correlation
  - Exact agreement (%) and tolerance agreement (+/-1 point %)

Dimensions:
  - hawkish_dovish (-2 to +2)
  - inflation_concern (0 to 3)
  - growth_concern (0 to 3)
  - uncertainty (0 to 3)
  - forward_guidance_shift (-2 to +2)

NOTE: In accordance with project instructions, label columns in final/docs datasets
remain empty pending completion of human annotation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

try:
    from sklearn.metrics import cohen_kappa_score
except ImportError:
    cohen_kappa_score = None

try:
    from scipy.stats import spearmanr, pearsonr
except ImportError:
    spearmanr = None
    pearsonr = None

LABEL_DIMENSIONS = [
    "hawkish_dovish",
    "inflation_concern",
    "growth_concern",
    "uncertainty",
    "forward_guidance_shift",
]


def _numpy_cohen_kappa(y1: np.ndarray, y2: np.ndarray, weights: str | None = None) -> float:
    """Fallback implementation of Cohen's kappa if scikit-learn is not available."""
    categories = np.unique(np.concatenate([y1, y2]))
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    n_cat = len(categories)
    n = len(y1)
    if n == 0 or n_cat <= 1:
        return 1.0

    conf_mat = np.zeros((n_cat, n_cat), dtype=float)
    for a, b in zip(y1, y2):
        conf_mat[cat_to_idx[a], cat_to_idx[b]] += 1

    p_observed = np.trace(conf_mat) / n
    row_sums = conf_mat.sum(axis=1) / n
    col_sums = conf_mat.sum(axis=0) / n
    p_expected = np.sum(row_sums * col_sums)

    if weights is None:
        if p_expected == 1.0:
            return 1.0
        return float((p_observed - p_expected) / (1.0 - p_expected))
    elif weights == "quadratic":
        w = np.zeros((n_cat, n_cat), dtype=float)
        for i in range(n_cat):
            for j in range(n_cat):
                w[i, j] = ((i - j) ** 2) / ((n_cat - 1) ** 2)
        po = np.sum(w * conf_mat) / n
        pe = np.sum(w * np.outer(row_sums, col_sums))
        if pe == 0.0:
            return 1.0
        return float(1.0 - po / pe)
    return float((p_observed - p_expected) / (1.0 - p_expected))


def compute_agreement(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Compute agreement metrics between two annotators on shared event_ids."""
    if "event_id" not in df1.columns or "event_id" not in df2.columns:
        raise ValueError("Both dataframes must contain an 'event_id' column.")

    merged = pd.merge(df1, df2, on="event_id", suffixes=("_1", "_2"))
    results = []

    for dim in LABEL_DIMENSIONS:
        c1 = f"{dim}_1"
        c2 = f"{dim}_2"
        if c1 not in merged.columns or c2 not in merged.columns:
            continue

        valid = merged[[c1, c2]].dropna()
        n_obs = len(valid)

        if n_obs == 0:
            results.append({
                "dimension": dim,
                "n_annotated": 0,
                "exact_agreement_pct": np.nan,
                "within_1pt_pct": np.nan,
                "cohen_kappa_unweighted": np.nan,
                "cohen_kappa_quadratic": np.nan,
                "spearman_rho": np.nan,
                "pearson_r": np.nan,
            })
            continue

        y1 = valid[c1].to_numpy()
        y2 = valid[c2].to_numpy()

        exact = np.mean(y1 == y2) * 100.0
        within_1 = np.mean(np.abs(y1 - y2) <= 1) * 100.0

        # Cohen's kappa
        if cohen_kappa_score is not None:
            try:
                kappa_unweighted = cohen_kappa_score(y1, y2)
                kappa_quadratic = cohen_kappa_score(y1, y2, weights="quadratic")
            except Exception:
                kappa_unweighted = _numpy_cohen_kappa(y1, y2)
                kappa_quadratic = _numpy_cohen_kappa(y1, y2, weights="quadratic")
        else:
            kappa_unweighted = _numpy_cohen_kappa(y1, y2)
            kappa_quadratic = _numpy_cohen_kappa(y1, y2, weights="quadratic")

        # Correlations
        if spearmanr is not None and len(np.unique(y1)) > 1 and len(np.unique(y2)) > 1:
            s_rho, _ = spearmanr(y1, y2)
            p_r, _ = pearsonr(y1, y2)
        else:
            # Fallback
            if np.std(y1) > 0 and np.std(y2) > 0:
                p_r = np.corrcoef(y1, y2)[0, 1]
                s_rho = p_r
            else:
                p_r = np.nan
                s_rho = np.nan

        results.append({
            "dimension": dim,
            "n_annotated": n_obs,
            "exact_agreement_pct": round(exact, 2),
            "within_1pt_pct": round(within_1, 2),
            "cohen_kappa_unweighted": round(float(kappa_unweighted), 4),
            "cohen_kappa_quadratic": round(float(kappa_quadratic), 4),
            "spearman_rho": round(float(s_rho), 4) if pd.notna(s_rho) else np.nan,
            "pearson_r": round(float(p_r), 4) if pd.notna(p_r) else np.nan,
        })

    return pd.DataFrame(results)


def self_test() -> None:
    """Run verification self-test on synthetic dual-annotator data."""
    print("Running self_test on synthetic dual-annotator sample...")
    np.random.seed(42)
    n = 100
    events = [f"event_{i:03d}" for i in range(n)]

    # Generate synthetic annotations with realistic high correlation
    data1 = {"event_id": events}
    data2 = {"event_id": events}

    for dim in LABEL_DIMENSIONS:
        if dim in ("hawkish_dovish", "forward_guidance_shift"):
            base = np.random.choice([-2, -1, 0, 1, 2], size=n, p=[0.1, 0.2, 0.4, 0.2, 0.1])
            noise = np.random.choice([-1, 0, 1], size=n, p=[0.15, 0.70, 0.15])
            val2 = np.clip(base + noise, -2, 2)
        else:
            base = np.random.choice([0, 1, 2, 3], size=n, p=[0.25, 0.4, 0.25, 0.1])
            noise = np.random.choice([-1, 0, 1], size=n, p=[0.15, 0.70, 0.15])
            val2 = np.clip(base + noise, 0, 3)

        data1[dim] = base
        data2[dim] = val2

    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)

    res = compute_agreement(df1, df2)
    print("Inter-Annotator Reliability Evaluation (Synthetic Benchmark Test):")
    print(res.to_string(index=False))
    assert (res["exact_agreement_pct"] > 50).all()
    assert (res["within_1pt_pct"] >= 95).all()
    assert (res["cohen_kappa_quadratic"] > 0.60).all()
    print("Self-test passed successfully: all metrics computed and verified.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate inter-annotator agreement on MoTrans-15 statements.")
    parser.add_argument("--annotator1", type=str, help="Path to CSV filled by Annotator 1")
    parser.add_argument("--annotator2", type=str, help="Path to CSV filled by Annotator 2")
    parser.add_argument("--output", type=str, help="Path to save output agreement summary CSV")
    args = parser.parse_args()

    if not args.annotator1 or not args.annotator2:
        print("No input annotator files provided. Running verification self-test:")
        self_test()
        return

    df1 = pd.read_csv(args.annotator1)
    df2 = pd.read_csv(args.annotator2)

    report = compute_agreement(df1, df2)
    print("\nInter-Annotator Agreement Report:")
    print(report.to_string(index=False))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report.to_csv(out_path, index=False)
        print(f"\nSaved agreement report to {out_path}")


if __name__ == "__main__":
    main()
