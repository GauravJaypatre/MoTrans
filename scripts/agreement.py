"""Inter-Annotator Agreement Engine for MoTrans-15 Qualitative Statement Codings.

Calculates statistical reliability metrics across human annotators:
1. Cohen's Kappa (unweighted and quadratic-weighted)
2. Fleiss' Kappa (generalized for m >= 2 raters)
3. Krippendorff's Alpha (nominal, ordinal, and interval metrics)
4. Non-parametric Bootstrap 95% Confidence Intervals (1,000 resamples)
5. Adjudication workflow: extracts discrepancies and incorporates completed adjudication log

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
        return 1.0

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

    p_j = mat.sum(axis=0) / (n_items * n_raters)
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
                        pairs.append((valid_vals[i], valid_vals[j]))

    if not pairs:
        return np.nan

    values = sorted(list(values_set))
    val_to_idx = {v: i for i, v in enumerate(values)}
    v_len = len(values)

    if v_len <= 1:
        return 1.0

    coincidence = np.zeros((v_len, v_len), dtype=float)
    for c, k in pairs:
        coincidence[val_to_idx[c], val_to_idx[k]] += 1.0

    total_pairs = coincidence.sum()
    if total_pairs == 0:
        return np.nan

    marginals = coincidence.sum(axis=1)

    # Difference function delta^2(c, k)
    delta2 = np.zeros((v_len, v_len), dtype=float)
    for i, c in enumerate(values):
        for j, k in enumerate(values):
            if level_of_measurement == "nominal":
                delta2[i, j] = 0.0 if c == k else 1.0
            elif level_of_measurement == "ordinal":
                if c == k:
                    delta2[i, j] = 0.0
                else:
                    low, high = min(i, j), max(i, j)
                    # Sum of marginals between categories + half ends
                    g_sum = np.sum(marginals[low : high + 1]) - (marginals[low] + marginals[high]) / 2.0
                    delta2[i, j] = g_sum ** 2
            elif level_of_measurement == "interval":
                delta2[i, j] = (float(c) - float(k)) ** 2
            else:
                raise ValueError(f"Unsupported level of measurement: '{level_of_measurement}'")

    do = np.sum(coincidence * delta2)
    de = np.sum(np.outer(marginals, marginals) * delta2) / (total_pairs - 1.0) if total_pairs > 1 else 0.0

    if de == 0.0:
        return 1.0
    return float(1.0 - (do / de))


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

    if n < 2:
        return {
            "cohen_kappa_unweighted": (np.nan, np.nan),
            "cohen_kappa_quadratic": (np.nan, np.nan),
            "krippendorff_alpha_ordinal": (np.nan, np.nan),
        }

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


def generate_adjudication_log_from_samples(
    ann1_path: Union[str, Path],
    ann2_path: Union[str, Path],
    out_log_path: Union[str, Path],
    dimensions: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Extract discrepancies between completed annotator 1 and annotator 2 samples into adjudication_log.csv."""
    if dimensions is None:
        dimensions = ["hawkish_dovish", "inflation_concern", "growth_concern", "uncertainty", "forward_guidance_shift"]

    df1 = pd.read_csv(ann1_path).set_index("event_id")
    df2 = pd.read_csv(ann2_path).set_index("event_id")
    common_events = df1.index.intersection(df2.index)

    rows = []
    adj_id = 1
    for eid in sorted(common_events):
        r1 = df1.loc[eid]
        r2 = df2.loc[eid]
        regime = r1.get("regime", "")
        dec_date = str(r1.get("decision_date", ""))

        for dim in dimensions:
            v1 = r1.get(dim)
            v2 = r2.get(dim)
            if pd.notna(v1) and pd.notna(v2) and v1 != v2:
                diff = abs(float(v1) - float(v2))
                rows.append({
                    "adjudication_id": adj_id,
                    "event_id": eid,
                    "regime": regime,
                    "decision_date": dec_date,
                    "dimension": dim,
                    "score_annotator_1": v1,
                    "score_annotator_2": v2,
                    "discrepancy_magnitude": int(diff),
                    "adjudicated_score": np.nan,
                    "adjudicator_id": "",
                    "adjudication_timestamp": "",
                    "notes": "MAJOR DISCREPANCY" if diff >= 2 else "MINOR DISCREPANCY",
                })
                adj_id += 1

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        df_out.to_csv(out_log_path, index=False)
        print(f"Generated {len(df_out)} adjudication candidates to {out_log_path}")
    else:
        print(f"No non-null discrepancies found; keeping template at {out_log_path}")
    return df_out


def merge_adjudicated_scores(
    ann1_path: Union[str, Path],
    ann2_path: Union[str, Path],
    adj_log_path: Union[str, Path],
    dimensions: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Merge annotator scores and resolved adjudication scores into consensus dataset."""
    if dimensions is None:
        dimensions = ["hawkish_dovish", "inflation_concern", "growth_concern", "uncertainty", "forward_guidance_shift"]

    df1 = pd.read_csv(ann1_path).set_index("event_id")
    df2 = pd.read_csv(ann2_path).set_index("event_id")
    common_events = df1.index.intersection(df2.index)

    # Load adjudication log
    adj_lookup = {}
    if Path(adj_log_path).exists():
        df_adj = pd.read_csv(adj_log_path)
        if not df_adj.empty and "adjudicated_score" in df_adj.columns:
            for _, row in df_adj.dropna(subset=["adjudicated_score"]).iterrows():
                key = (row["event_id"], row["dimension"])
                adj_lookup[key] = float(row["adjudicated_score"])

    consensus_rows = []
    for eid in sorted(common_events):
        r1 = df1.loc[eid]
        r2 = df2.loc[eid]
        row_dict = {
            "event_id": eid,
            "regime": r1.get("regime", ""),
            "decision_date": r1.get("decision_date", ""),
        }
        for dim in dimensions:
            key = (eid, dim)
            if key in adj_lookup:
                row_dict[dim] = adj_lookup[key]
            else:
                v1 = r1.get(dim)
                v2 = r2.get(dim)
                if pd.notna(v1) and pd.notna(v2):
                    row_dict[dim] = float(v1 + v2) / 2.0
                elif pd.notna(v1):
                    row_dict[dim] = float(v1)
                elif pd.notna(v2):
                    row_dict[dim] = float(v2)
                else:
                    row_dict[dim] = np.nan
        consensus_rows.append(row_dict)

    return pd.DataFrame(consensus_rows)


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
    parser = argparse.ArgumentParser(description="Compute inter-annotator agreement metrics and manage adjudication.")
    parser.add_argument("--input", type=str, default=None, help="Path to double-annotation CSV")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--extract-adjudications", action="store_true", help="Extract discrepancies to adjudication log")
    parser.add_argument("--ann1", type=str, default=str(ROOT / "data" / "annotation" / "annotator_1_sample.csv"))
    parser.add_argument("--ann2", type=str, default=str(ROOT / "data" / "annotation" / "annotator_2_sample.csv"))
    parser.add_argument("--adjudication-log", type=str, default=str(ROOT / "data" / "annotation" / "adjudication_log.csv"))
    args = parser.parse_args()

    if args.extract_adjudications:
        generate_adjudication_log_from_samples(args.ann1, args.ann2, args.adjudication_log)
    elif args.input:
        report = analyze_double_annotation_csv(args.input)
        if args.output:
            Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(f"Saved agreement report to {args.output}")
        else:
            print(json.dumps(report, indent=2))
    else:
        print("Inter-Annotator Agreement Engine ready. Use --help for options.")
