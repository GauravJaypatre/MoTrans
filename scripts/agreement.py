"""Inter-Annotator Agreement Engine for MoTrans-15 Qualitative Statement Codings.

Calculates statistical reliability metrics across human annotators:
1. Cohen's Kappa (unweighted and quadratic-weighted)
2. Fleiss' Kappa (generalized for m >= 2 raters)
3. Krippendorff's Alpha (nominal, ordinal, and interval metrics)
4. Non-parametric Bootstrap 95% Confidence Intervals (1,000 resamples)
5. Adjudication extraction: flags discrepancies (|score1 - score2| >= 1 and >= 2)

Note: Production human coding is marked TODO-HUMAN. All mathematical functions
are validated against synthetic fixtures in tests/test_agreement.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def cohen_kappa(
    rater1: Union[np.ndarray, list],
    rater2: Union[np.ndarray, list],
    weights: Optional[str] = None,
) -> float:
    """Calculate Cohen's Kappa for two raters.

    Parameters
    ----------
    rater1, rater2 : array-like
        Ratings from coder 1 and coder 2.
    weights : None, 'linear', or 'quadratic'
        Weighting scheme for ordinal distance.

    Returns
    -------
    float : Kappa coefficient.
    """
    r1 = np.asarray(rater1)
    r2 = np.asarray(rater2)

    valid = ~pd.isna(r1) & ~pd.isna(r2)
    r1 = r1[valid]
    r2 = r2[valid]

    n = len(r1)
    if n == 0:
        return np.nan

    categories = np.unique(np.concatenate([r1, r2]))
    k = len(categories)
    if k <= 1:
        return 1.0  # Perfect agreement on single category

    cat_to_idx = {c: i for i, c in enumerate(categories)}
    idx1 = np.array([cat_to_idx[c] for c in r1])
    idx2 = np.array([cat_to_idx[c] for c in r2])

    # Confusion matrix
    conf = np.zeros((k, k), dtype=float)
    for i in range(n):
        conf[idx1[i], idx2[i]] += 1.0
    conf /= n

    # Marginals
    p1 = conf.sum(axis=1)
    p2 = conf.sum(axis=0)
    pe_matrix = np.outer(p1, p2)

    if weights is None:
        po = np.trace(conf)
        pe = np.trace(pe_matrix)
    else:
        # Distance weight matrix
        w = np.zeros((k, k), dtype=float)
        for i in range(k):
            for j in range(k):
                diff = abs(i - j)
                if weights == "linear":
                    w[i, j] = 1.0 - diff / (k - 1)
                elif weights == "quadratic":
                    w[i, j] = 1.0 - (diff ** 2) / ((k - 1) ** 2)
                else:
                    raise ValueError(f"Unknown weights: '{weights}'")
        po = np.sum(w * conf)
        pe = np.sum(w * pe_matrix)

    if pe >= 1.0:
        return 1.0
    return float((po - pe) / (1.0 - pe))


def fleiss_kappa(ratings_matrix: np.ndarray) -> float:
    """Calculate Fleiss' Kappa for m raters per item.

    Parameters
    ----------
    ratings_matrix : np.ndarray of shape (N, K)
        Where entry (i, j) is the count of raters who assigned category j to item i.

    Returns
    -------
    float : Fleiss' Kappa coefficient.
    """
    mat = np.asarray(ratings_matrix, dtype=float)
    n_items, n_cats = mat.shape

    m = mat.sum(axis=1)
    n_raters = m[0]
    if not np.allclose(m, n_raters):
        raise ValueError("Fleiss' Kappa requires constant number of raters per item.")
    if n_raters <= 1:
        return np.nan

    # Proportion of all assignments to each category
    p_j = mat.sum(axis=0) / (n_items * n_raters)

    # Degree of agreement for each item
    p_i = (np.sum(mat ** 2, axis=1) - n_raters) / (n_raters * (n_raters - 1))

    mean_p = np.mean(p_i)
    pe = np.sum(p_j ** 2)

    if pe >= 1.0:
        return 1.0
    return float((mean_p - pe) / (1.0 - pe))


def krippendorff_alpha(
    data: np.ndarray,
    level_of_measurement: str = "ordinal",
) -> float:
    """Calculate Krippendorff's Alpha.

    Parameters
    ----------
    data : np.ndarray of shape (raters, items)
        Array of ratings; missing values represented by np.nan.
    level_of_measurement : 'nominal', 'ordinal', or 'interval'

    Returns
    -------
    float : Alpha coefficient.
    """
    mat = np.asarray(data, dtype=float)
    n_raters, n_items = mat.shape

    # Collect pairs for coincidence matrix
    pairs = []
    values_set = set()
    for col in range(n_items):
        item_vals = mat[:, col]
        valid_vals = item_vals[~np.isnan(item_vals)]
        m_u = len(valid_vals)
        if m_u >= 2:
            values_set.update(valid_vals)
            for i in range(m_u):
                for j in range(m_u):
                    if i != j:
                        pairs.append((valid_vals[i], valid_vals[j], 1.0 / (m_u - 1)))

    if not pairs:
        return np.nan

    values = sorted(list(values_set))
    k = len(values)
    if k <= 1:
        return 1.0

    val_to_idx = {v: i for i, v in enumerate(values)}

    # Build coincidence matrix
    coin = np.zeros((k, k), dtype=float)
    for v1, v2, wt in pairs:
        coin[val_to_idx[v1], val_to_idx[v2]] += wt

    total_pairs = coin.sum()
    if total_pairs == 0:
        return np.nan

    # Marginals
    n_c = coin.sum(axis=1)

    # Metric distance function
    diff = np.zeros((k, k), dtype=float)
    if level_of_measurement == "nominal":
        for i in range(k):
            for j in range(k):
                diff[i, j] = 0.0 if i == j else 1.0
    elif level_of_measurement == "ordinal":
        # Ordinal distance using cumulative frequencies
        for i in range(k):
            for j in range(k):
                if i != j:
                    low, high = min(i, j), max(i, j)
                    # Sum between low and high
                    mid = np.sum(n_c[low : high + 1]) - (n_c[low] + n_c[high]) / 2.0
                    diff[i, j] = mid ** 2
    elif level_of_measurement == "interval":
        for i in range(k):
            for j in range(k):
                diff[i, j] = (values[i] - values[j]) ** 2
    else:
        raise ValueError(f"Unsupported measurement level: '{level_of_measurement}'")

    do = np.sum(coin * diff) / total_pairs

    de = 0.0
    for i in range(k):
        for j in range(k):
            de += n_c[i] * n_c[j] * diff[i, j]
    de /= (total_pairs * (total_pairs - 1.0)) if total_pairs > 1 else total_pairs

    if de == 0:
        return 1.0 if do == 0 else 0.0
    return float(1.0 - do / de)


def bootstrap_agreement_ci(
    rater1: np.ndarray,
    rater2: np.ndarray,
    n_boot: int = 1000,
    seed: int = 2026,
    alpha: float = 0.05,
) -> Dict[str, Tuple[float, float]]:
    """Compute non-parametric bootstrap 95% confidence intervals for agreement statistics."""
    rng = np.random.default_rng(seed)
    r1 = np.asarray(rater1)
    r2 = np.asarray(rater2)

    valid = ~pd.isna(r1) & ~pd.isna(r2)
    r1 = r1[valid]
    r2 = r2[valid]
    n = len(r1)

    boot_ck = np.empty(n_boot)
    boot_ck_w = np.empty(n_boot)
    boot_alpha = np.empty(n_boot)

    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        b_r1 = r1[idx]
        b_r2 = r2[idx]

        boot_ck[b] = cohen_kappa(b_r1, b_r2, weights=None)
        boot_ck_w[b] = cohen_kappa(b_r1, b_r2, weights="quadratic")
        data_pair = np.vstack([b_r1, b_r2])
        boot_alpha[b] = krippendorff_alpha(data_pair, level_of_measurement="ordinal")

    low_q = alpha / 2.0 * 100
    high_q = (1.0 - alpha / 2.0) * 100

    return {
        "cohen_kappa_unweighted": (float(np.percentile(boot_ck, low_q)), float(np.percentile(boot_ck, high_q))),
        "cohen_kappa_quadratic": (float(np.percentile(boot_ck_w, low_q)), float(np.percentile(boot_ck_w, high_q))),
        "krippendorff_alpha_ordinal": (float(np.percentile(boot_alpha, low_q)), float(np.percentile(boot_alpha, high_q))),
    }


def extract_adjudication_candidates(
    df: pd.DataFrame,
    coder1_col: str = "coder_01",
    coder2_col: str = "coder_02",
    dimensions: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Extract statements and dimensions requiring adjudication."""
    if dimensions is None:
        dimensions = ["hawkish_dovish", "inflation_concern", "growth_concern", "uncertainty", "forward_guidance_shift"]

    discrepancies = []
    # Pivot coder ratings
    pivoted = df.pivot(index=["statement_id", "regime", "decision_date"], columns="coder_id", values=dimensions)

    for dim in dimensions:
        c1 = pivoted[dim][coder1_col]
        c2 = pivoted[dim][coder2_col]
        diff = (c1 - c2).abs()

        for idx, d_val in diff.items():
            if pd.notna(d_val) and d_val >= 1:
                discrepancies.append({
                    "statement_id": idx[0],
                    "regime": idx[1],
                    "decision_date": str(idx[2]),
                    "dimension": dim,
                    "score_coder1": c1.loc[idx],
                    "score_coder2": c2.loc[idx],
                    "discrepancy_magnitude": int(d_val),
                    "severity": "MAJOR" if d_val >= 2 else "MINOR",
                    "adjudication_required": int(d_val >= 2),
                })

    return pd.DataFrame(discrepancies)


def analyze_double_annotation_csv(file_path: Union[str, Path]) -> Dict[str, object]:
    """Perform full reliability analysis on a double-annotation CSV file."""
    df = pd.read_csv(file_path)
    coders = df["coder_id"].unique()
    dimensions = ["hawkish_dovish", "inflation_concern", "growth_concern", "uncertainty", "forward_guidance_shift"]

    if len(coders) < 2:
        return {"error": "At least 2 distinct coder_ids required for agreement analysis."}

    results = {"coders": list(coders), "n_records": len(df), "dimensions": {}}

    c1_name, c2_name = coders[0], coders[1]
    df_c1 = df[df["coder_id"] == c1_name].set_index("statement_id")
    df_c2 = df[df["coder_id"] == c2_name].set_index("statement_id")
    common_ids = df_c1.index.intersection(df_c2.index)

    for dim in dimensions:
        if dim not in df.columns:
            continue
        v1 = df_c1.loc[common_ids, dim].values
        v2 = df_c2.loc[common_ids, dim].values

        ck_raw = cohen_kappa(v1, v2, weights=None)
        ck_quad = cohen_kappa(v1, v2, weights="quadratic")
        k_alpha = krippendorff_alpha(np.vstack([v1, v2]), level_of_measurement="ordinal")
        ci = bootstrap_agreement_ci(v1, v2, n_boot=500)

        results["dimensions"][dim] = {
            "n_paired": len(common_ids),
            "cohen_kappa_unweighted": ck_raw,
            "cohen_kappa_quadratic": ck_quad,
            "krippendorff_alpha_ordinal": k_alpha,
            "bootstrap_ci_95": ci,
        }

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute inter-annotator agreement metrics.")
    parser.add_argument("--input", type=str, required=True, help="Path to double-annotation CSV")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    report = analyze_double_annotation_csv(args.input)
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Saved agreement report to {args.output}")
    else:
        print(json.dumps(report, indent=2))
