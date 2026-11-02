"""Clustering and Overlap Helpers for MoTrans-15 Empirical Inference.

Provides:
1. Decision-level (`event_id`) and index-level (`index_id`) cluster identifiers.
2. Contamination filtering via prior-event overlap indicators (`overlap_prior_*`).
3. Cluster-robust OLS inference using statsmodels with clustered covariance estimators.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import statsmodels.api as sm


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
    """Filter or flag events that overlap with prior policy decisions.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    horizon : str
        Window horizon: '1d', '3d', '5d', '20d', or '60d'.
    method : str
        'drop': excludes rows where overlap_prior_{horizon} == 1.
        'flag': retains rows and ensures clean indicator column.

    Returns
    -------
    pd.DataFrame
    """
    col_name = f"overlap_prior_{horizon}"
    if col_name not in df.columns:
        # Check alternative naming
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
) -> Dict[str, Union[float, int, str, np.ndarray, sm.regression.linear_model.RegressionResultsWrapper]]:
    """Estimate an OLS regression with cluster-robust standard errors.

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
    add_constant : bool
        Whether to add an intercept.

    Returns
    -------
    Dict containing regression results and model statistics.
    """
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

    # Shock coefficient (assumes primary shock is first non-constant regressor)
    shock_var = x_cols[0]
    coef = float(results.params[shock_var])
    se = float(results.bse[shock_var])
    t_stat = float(results.tvalues[shock_var])
    p_val = float(results.pvalues[shock_var])
    ci = results.conf_int().loc[shock_var]

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
        "p_val": p_val,
        "ci_lower": float(ci.iloc[0]),
        "ci_upper": float(ci.iloc[1]),
        "results_model": results,
    }

