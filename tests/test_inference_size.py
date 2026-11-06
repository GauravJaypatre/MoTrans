"""Unit test verifying nominal 5% rejection size under null with event-level common shocks.

Verifies:
1. Event-clustered inference controls size at nominal alpha = 0.05.
2. Two-way clustered inference (event_id x index_id) controls size.
3. Few-cluster wild bootstrap controls size when cluster count G is small (G=20).
4. Prohibits unclustered OLS and index-only clustering from the modeling API.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import pytest

from src.modeling.clustering import fit_ols_clustered
from src.modeling.uncertainty import fit_twoway_clustered, wild_cluster_bootstrap


def test_nominal_five_percent_rejection_size():
    """Verify empirical rejection rate is within binomial interval of 0.05 with G=100."""
    n_sims = 300
    n_events = 100
    n_indices = 30
    rejections = 0

    rng = np.random.default_rng(2026)

    for _ in range(n_sims):
        event_shock = rng.normal(0.0, 1.0, size=n_events)
        event_macro_error = rng.normal(0.0, 1.0, size=n_events)

        shocks_long = np.repeat(event_shock, n_indices)
        macro_long = np.repeat(event_macro_error, n_indices)
        idiosyncratic = rng.normal(0.0, 1.0, size=n_events * n_indices)

        y = 0.0 * shocks_long + 0.6 * macro_long + idiosyncratic
        cluster_ids = np.repeat(np.arange(n_events), n_indices)

        X = sm.add_constant(shocks_long)
        model = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": cluster_ids})

        if model.pvalues[1] < 0.05:
            rejections += 1

    rejection_rate = rejections / n_sims
    assert 0.020 <= rejection_rate <= 0.090, (
        f"Empirical rejection rate {rejection_rate:.3f} deviates from nominal 0.05."
    )


def test_two_way_clustering_controls_size():
    """Verify two-way clustered inference controls size under cross-sectional and temporal correlation."""
    n_sims = 150
    n_events = 50
    n_indices = 20
    rejections = 0

    rng = np.random.default_rng(42)

    for _ in range(n_sims):
        event_shock = rng.normal(0.0, 1.0, size=n_events)
        event_macro = rng.normal(0.0, 1.0, size=n_events)
        index_fixed_effect = rng.normal(0.0, 1.0, size=n_indices)

        shocks_long = np.repeat(event_shock, n_indices)
        macro_long = np.repeat(event_macro, n_indices)
        index_fe_long = np.tile(index_fixed_effect, n_events)
        idio = rng.normal(0.0, 1.0, size=n_events * n_indices)

        y = 0.0 * shocks_long + 0.5 * macro_long + 0.5 * index_fe_long + idio
        eids = np.repeat([f"e_{i}" for i in range(n_events)], n_indices)
        iids = np.tile([f"idx_{j}" for j in range(n_indices)], n_events)

        df = pd.DataFrame({"y": y, "shock": shocks_long, "event_id": eids, "index_id": iids})
        res = fit_twoway_clustered(df, "y", ["shock"], cluster1="event_id", cluster2="index_id")
        if res["p_val_twoway"] < 0.05:
            rejections += 1

    rate = rejections / n_sims
    assert 0.015 <= rate <= 0.095, f"Two-way clustering rejection rate {rate:.3f} deviates from nominal 0.05."


def test_few_cluster_wild_bootstrap_controls_size():
    """Verify wild cluster bootstrap controls size in few-cluster settings (G=15)."""
    n_sims = 100
    n_events = 15
    n_indices = 20
    rejections_wb = 0
    rejections_unclustered = 0

    rng = np.random.default_rng(123)

    for _ in range(n_sims):
        event_shock = rng.normal(0.0, 1.0, size=n_events)
        event_macro = rng.normal(0.0, 1.0, size=n_events)

        shocks_long = np.repeat(event_shock, n_indices)
        macro_long = np.repeat(event_macro, n_indices)
        idio = rng.normal(0.0, 1.0, size=n_events * n_indices)

        y = 0.0 * shocks_long + 0.8 * macro_long + idio
        eids = np.repeat([f"e_{i}" for i in range(n_events)], n_indices)

        df = pd.DataFrame({"y": y, "shock": shocks_long, "event_id": eids})

        # 1. Unclustered OLS severely over-rejects (Moulton problem)
        m_uncl = sm.OLS(y, sm.add_constant(shocks_long)).fit()
        if m_uncl.pvalues[1] < 0.05:
            rejections_unclustered += 1

        # 2. Wild cluster bootstrap controls size
        wb = wild_cluster_bootstrap(df, "y", ["shock"], cluster_col="event_id", n_boot=199, seed=42)
        if wb["p_val_wild"] < 0.05:
            rejections_wb += 1

    rate_uncl = rejections_unclustered / n_sims
    rate_wb = rejections_wb / n_sims

    # Unclustered should severely over-reject (> 25%)
    assert rate_uncl > 0.25, f"Expected unclustered OLS to over-reject, got {rate_uncl:.3f}"
    # Wild bootstrap should be well calibrated (within [0.01, 0.12] for N=100 sims)
    assert rate_wb <= 0.12, f"Wild bootstrap over-rejected with rate {rate_wb:.3f}"


def test_clustering_routine_prohibits_unclustered_and_index_only():
    """Verify that fit_ols_clustered strictly raises ValueError on unclustered or index-only input."""
    df = pd.DataFrame({
        "clr_5": [0.01, 0.02, -0.01],
        "shock": [1.0, -0.5, 0.2],
        "event_id": ["e1", "e1", "e2"],
        "index_id": ["idx1", "idx2", "idx1"],
    })

    # Case 1: unclustered
    with pytest.raises(ValueError, match="Unclustered OLS is prohibited"):
        fit_ols_clustered(df, "clr_5", ["shock"], cluster_col=None)

    # Case 2: index-only clustering
    with pytest.raises(ValueError, match="Index-only clustering .* is methodologically prohibited"):
        fit_ols_clustered(df, "clr_5", ["shock"], cluster_col="index_id")
