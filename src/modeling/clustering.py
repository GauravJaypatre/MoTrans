"""Clustering and Overlap Helpers for MoTrans-15 Empirical Inference.

Provides:
1. Decision-level (`event_id`) cluster identifier extraction.
2. Contamination filtering via prior-event overlap indicators (`overlap_prior_*`).
3. Cluster-robust OLS inference enforcing event-level or two-way clustering, with
   default restricted wild cluster bootstrap p-values.
4. Strict prohibition of unclustered or index-only clustered routines from the public API.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.modeling.uncertainty import wild_cluster_bootstrap


def get_cluster_ids(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """Extract decision-level and index-level cluster identifier series.

    Returns
    -------
    Tuple[pd.Series, pd.Series]
        (cluster_decision, cluster_index)
    """
    if "event_id" not in df.columns:
        raise KeyError("Dataframe missing required 'event_id' column for decision clustering.")
    if "index_id" not in df.columns:
        raise KeyError("Dataframe missing required 'index_id' column for index clustering.")

    cluster_event = df["event_id"].astype(str)
    cluster_index = df["index_id"].astype(str)
    return cluster_event, cluster_index


def filter_overlap(
    df: pd.DataFrame,
    horizon: str = "5d",
    method: str = "drop",
) -> pd.DataFrame:
    """Filter or flag events that overlap with prior policy decisions."""
    col_name = f"overlap_prior_{horizon}"
    if col_name not in df.columns:
        alt_name = f"overlap_prior_{horizon.replace('d', '')}d"
        if alt_name in df.columns:
            col_name = alt_name
        else:
            raise KeyError(f"Overlap indicator '{col_name}' not present in dataframe columns.")

    if method == "drop":
        clean_df = df[df[col_name] == 0].copy()
        return clean_df.reset_index(drop=True)
    elif method == "flag":
        return df.copy()
    else:
        raise ValueError(f"Unknown method '{method}'. Expected 'drop' or 'flag'.")


def fit_ols_clustered(
    df: pd.DataFrame,
    y_col: str,
    x_cols: List[str],
    cluster_col: str = "event_id",
    add_constant: bool = True,
    compute_wild_p: bool = True,
    n_boot: int = 999,
    seed: int = 42,
) -> Dict[str, Union[float, int, str, np.ndarray, sm.regression.linear_model.RegressionResultsWrapper]]:
    """Estimate an OLS regression with cluster-robust standard errors and wild bootstrap.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    y_col : str
        Dependent variable name.
    x_cols : List[str]
        List of explanatory variables.
    cluster_col : str
        Grouping variable for clustered covariance (default 'event_id').
        Index-only or unclustered estimation is strictly rejected.
    add_constant : bool
        Whether to add an intercept.
    compute_wild_p : bool
        Whether to compute restricted wild cluster bootstrap p-value.
    n_boot : int
        Number of bootstrap replications.
    seed : int
        RNG seed for reproducibility.

    Returns
    -------
    Dict containing regression results, cluster statistics, and p_val_wild.
    """
    if cluster_col is None or str(cluster_col).lower() in ["none", ""]:
        raise ValueError(
            "Unclustered OLS is prohibited in MoTrans-15 due to massive size distortion "
            "under common event shocks. Inference must be clustered at event_id or coarser."
        )

    if cluster_col == "index_id":
        raise ValueError(
            "Index-only clustering ('index_id') is methodologically prohibited: monetary shocks "
            "vary at the event_id level, leaving cross-index correlation within an event unaddressed. "
            "Cluster at 'event_id' (or use fit_twoway_clustered() for two-way clustering)."
        )

    required_cols = [y_col] + x_cols + [cluster_col]
    clean_df = df.dropna(subset=required_cols).copy()
    if clean_df.empty:
        raise ValueError("No valid observations remaining after dropping missing values.")

    Y = clean_df[y_col]
    X = clean_df[x_cols]
    if add_constant:
        X = sm.add_constant(X)

    groups = clean_df[cluster_col]

    model = sm.OLS(Y, X)
    results = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

    shock_var = x_cols[0]
    coef = float(results.params[shock_var])
    se = float(results.bse[shock_var])
    t_stat = float(results.tvalues[shock_var])
    p_val_analytic = float(results.pvalues[shock_var])
    ci = results.conf_int().loc[shock_var]

    p_val_wild = np.nan
    if compute_wild_p:
        try:
            wb = wild_cluster_bootstrap(
                clean_df,
                y_col=y_col,
                x_cols=x_cols,
                cluster_col=cluster_col,
                target_var=shock_var,
                n_boot=n_boot,
                seed=seed,
            )
            p_val_wild = float(wb["p_val_wild"])
        except Exception:
            p_val_wild = np.nan

    return {
        "n_obs": int(results.nobs),
        "n_events": int(clean_df["event_id"].nunique()) if "event_id" in clean_df.columns else int(groups.nunique()),
        "n_clusters": int(groups.nunique()),
        "r2": float(results.rsquared),
        "r2_adj": float(results.rsquared_adj),
        "f_stat": float(results.fvalue) if results.fvalue is not None else np.nan,
        "coef_shock": coef,
        "se_shock": se,
        "t_stat": t_stat,
        "p_val": p_val_analytic,
        "p_val_wild": p_val_wild,
        "p_val_primary": p_val_wild if not np.isnan(p_val_wild) else p_val_analytic,
        "ci_lower": float(ci.iloc[0]),
        "ci_upper": float(ci.iloc[1]),
        "results_model": results,
    }
