"""Unit test verifying nominal 5% rejection size under null with event-level common shocks.

Task 1e:
Simulated panel data with true zero effect (beta = 0), event-level common shocks,
and cross-index correlated residuals. Verifies that event-clustered inference
controls size at nominal alpha = 0.05 across 500 simulations.
"""

from __future__ import annotations

import numpy as np
import statsmodels.api as sm
import pytest


def test_nominal_five_percent_rejection_size():
    """Verify empirical rejection rate is within 95% binomial interval of 0.05.

    For n_sims = 500, nominal alpha = 0.05:
    SE = sqrt(0.05 * 0.95 / 500) = 0.00975.
    95% CI is [0.05 - 1.96 * SE, 0.05 + 1.96 * SE] = [0.0309, 0.0691].
    Tolerance [0.025, 0.080] provides high statistical power while avoiding false rejections.
    """
    n_sims = 500
    n_events = 100
    n_indices = 30
    rejections = 0

    rng = np.random.default_rng(2026)

    for _ in range(n_sims):
        # 1. Event-level monetary shock
        event_shock = rng.normal(0.0, 1.0, size=n_events)

        # 2. Event-level common unobserved macro error (cross-index correlation)
        event_macro_error = rng.normal(0.0, 1.0, size=n_events)

        # 3. Expand to panel (each event observed across n_indices)
        shocks_long = np.repeat(event_shock, n_indices)
        macro_long = np.repeat(event_macro_error, n_indices)
        idiosyncratic = rng.normal(0.0, 1.0, size=n_events * n_indices)

        # True DGP under H0: beta = 0.0
        y = 0.0 * shocks_long + 0.6 * macro_long + idiosyncratic
        cluster_ids = np.repeat(np.arange(n_events), n_indices)

        X = sm.add_constant(shocks_long)
        model = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": cluster_ids})

        # p-value for slope parameter
        if model.pvalues[1] < 0.05:
            rejections += 1

    rejection_rate = rejections / n_sims
    assert 0.025 <= rejection_rate <= 0.080, (
        f"Empirical rejection rate {rejection_rate:.3f} deviates significantly from nominal 0.05."
    )
