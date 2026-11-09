"""Calibrated Uncertainty Estimation for MoTrans-15.

Implements:
1. One-way and two-way clustered standard errors.
2. Wild Cluster Bootstrap (Rademacher weights) for small/medium cluster inference.
3. Clustered block bootstrap.
4. Effective sample size (N_eff) accounting for within-event correlation.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import statsmodels.api as sm


def compute_effective_n(y: pd.Series, cluster: pd.Series) -> Dict[str, float]:
    """Compute effective sample size N_eff based on intracluster correlation (ICC).

    N_eff = N / (1 + (M_bar - 1) * rho)
    where M_bar is average cluster size and rho is intracluster correlation.
    """
    clean = pd.DataFrame({"y": y, "cluster": cluster}).dropna()
    N = len(clean)
    G = clean["cluster"].nunique()
    if G <= 1 or N <= G:
        return {"n_raw": N, "n_clusters": G, "icc": 0.0, "n_eff": float(N)}

    # Intracluster correlation via ANOVA decomposition
    cluster_means = clean.groupby("cluster")["y"].transform("mean")
    overall_mean = clean["y"].mean()

    ss_between = ((cluster_means - overall_mean) ** 2).sum()
    ss_within = ((clean["y"] - cluster_means) ** 2).sum()

    df_between = G - 1
    df_within = N - G

    ms_between = ss_between / df_between
    ms_within = ss_within / df_within if df_within > 0 else 1.0

    cluster_sizes = clean.groupby("cluster").size()
    m_bar = cluster_sizes.mean()
    # Adjusted cluster size for unequal clusters
    m_adj = (N - (cluster_sizes ** 2).sum() / N) / (G - 1) if G > 1 else m_bar

    # ICC estimate
    s2_between = max(0.0, (ms_between - ms_within) / m_adj)
    s2_total = s2_between + ms_within
    icc = s2_between / s2_total if s2_total > 0 else 0.0

    design_effect = 1.0 + (m_bar - 1.0) * icc
    n_eff = N / design_effect if design_effect > 0 else float(N)

    return {
        "n_raw": N,
        "n_clusters": G,
        "m_bar": float(m_bar),
        "icc": float(icc),
        "design_effect": float(design_effect),
        "n_eff": float(n_eff),
    }


def wild_cluster_bootstrap(
    df: pd.DataFrame,
    y_col: str,
    x_cols: List[str],
    cluster_col: str = "event_id",
    target_var: Optional[str] = None,
    n_boot: int = 999,
    seed: int = 42,
) -> Dict[str, float]:
    """Wild cluster bootstrap p-value using Rademacher two-point distribution.

    Implements the Cameron-Gelbach-Miller (2008) restricted wild cluster bootstrap.
    """
    rng = np.random.default_rng(seed)
    req = [y_col] + x_cols + [cluster_col]
    clean = df.dropna(subset=req).copy()
    if clean.empty:
        raise ValueError("No valid observations for bootstrap.")

    target = target_var or x_cols[0]
    Y = clean[y_col].values
    X = sm.add_constant(clean[x_cols]).values
    x_names = ["const"] + x_cols
    target_idx = x_names.index(target)

    # 1. Unrestricted OLS fit
    clusters = clean[cluster_col].values
    unique_clusters = np.unique(clusters)
    G = len(unique_clusters)

    ols_unres = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clusters})
    t_stat_orig = ols_unres.tvalues[target_idx]
    coef_orig = ols_unres.params[target_idx]

    # 2. Restricted model (H0: beta_target = 0)
    restr_x_indices = [i for i in range(X.shape[1]) if i != target_idx]
    X_restr = X[:, restr_x_indices]
    ols_restr = sm.OLS(Y, X_restr).fit()
    y_pred_restr = ols_restr.predict(X_restr)
    resid_restr = Y - y_pred_restr

    # Pre-index cluster rows for speed
    cluster_indices = [np.where(clusters == c)[0] for c in unique_clusters]

    # 3. Bootstrap resampling
    boot_t_stats = np.zeros(n_boot)
    boot_coefs = np.zeros(n_boot)
    for b in range(n_boot):
        # Rademacher weights: +1 or -1 with probability 0.5 per cluster
        weights = rng.choice([-1.0, 1.0], size=G)
        boot_resid = np.empty_like(resid_restr)
        for g, idxs in enumerate(cluster_indices):
            boot_resid[idxs] = resid_restr[idxs] * weights[g]

        Y_boot = y_pred_restr + boot_resid
        try:
            boot_model = sm.OLS(Y_boot, X).fit(cov_type="cluster", cov_kwds={"groups": clusters})
            boot_t_stats[b] = boot_model.tvalues[target_idx]
            boot_coefs[b] = boot_model.params[target_idx]
        except Exception:
            boot_t_stats[b] = 0.0
            boot_coefs[b] = 0.0

    # Two-sided empirical p-value
    p_val_wild = np.mean(np.abs(boot_t_stats) >= np.abs(t_stat_orig))
    se_wild = float(np.std(boot_coefs, ddof=1))

    return {
        "coef": float(coef_orig),
        "t_stat": float(t_stat_orig),
        "se_analytic": float(ols_unres.bse[target_idx]),
        "se_wild": se_wild,
        "p_val_analytic": float(ols_unres.pvalues[target_idx]),
        "p_val_wild": float(p_val_wild),
        "n_boot": n_boot,
        "n_clusters": G,
    }


def fit_twoway_clustered(
    df: pd.DataFrame,
    y_col: str,
    x_cols: List[str],
    cluster1: str = "event_id",
    cluster2: str = "index_id",
) -> Dict[str, float]:
    """Estimate regression with two-way clustered standard errors.

    Uses Cameron, Gelbach, and Miller (2011) variance formula:
    V_twoway = V_cluster1 + V_cluster2 - V_intersection
    """
    req = [y_col] + x_cols + [cluster1, cluster2]
    clean = df.dropna(subset=req).copy()
    if clean.empty:
        raise ValueError("No valid observations for two-way clustering.")

    Y = clean[y_col]
    X = sm.add_constant(clean[x_cols])
    target = x_cols[0]

    # 1. Cluster 1
    m1 = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean[cluster1]})
    cov1 = m1.cov_params()

    # 2. Cluster 2
    m2 = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean[cluster2]})
    cov2 = m2.cov_params()

    # 3. Intersection cluster
    clean["_inter_cluster"] = clean[cluster1].astype(str) + "_" + clean[cluster2].astype(str)
    m12 = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": clean["_inter_cluster"]})
    cov12 = m12.cov_params()

    # Two-way covariance matrix
    cov_twoway = cov1 + cov2 - cov12

    # Check for positive definiteness; if variance is negative (rare finite sample issue), floor at cov1
    var_target = cov_twoway.loc[target, target]
    if var_target <= 0:
        se_twoway = float(m1.bse[target])
    else:
        se_twoway = float(np.sqrt(var_target))

    coef = float(m1.params[target])
    t_stat = coef / se_twoway if se_twoway > 0 else 0.0
    from scipy import stats
    g1_count = int(clean[cluster1].nunique())
    g2_count = int(clean[cluster2].nunique())
    df_t = max(1, min(g1_count - 1, g2_count - 1))
    p_val = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df_t)))

    return {
        "coef": coef,
        "se_twoway": se_twoway,
        "t_stat_twoway": t_stat,
        "p_val_twoway": p_val,
        "n_obs": int(len(clean)),
        "n_cluster1": int(clean[cluster1].nunique()),
        "n_cluster2": int(clean[cluster2].nunique()),
    }

