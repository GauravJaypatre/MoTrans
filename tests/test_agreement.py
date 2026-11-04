"""Unit tests for inter-annotator agreement engine (scripts/agreement.py).

All tests utilize pure synthetic test fixtures with known mathematical properties.
Zero human labels or real statements are evaluated in this suite.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.agreement import (
    cohen_kappa,
    fleiss_kappa,
    krippendorff_alpha,
    bootstrap_agreement_ci,
    extract_adjudication_candidates,
)


def test_cohen_kappa_perfect_agreement():
    """Identical ratings must yield kappa = 1.0."""
    r1 = np.array([1, 2, 0, -1, -2, 2, 1, 0])
    r2 = np.array([1, 2, 0, -1, -2, 2, 1, 0])

    k_raw = cohen_kappa(r1, r2, weights=None)
    k_quad = cohen_kappa(r1, r2, weights="quadratic")

    assert pytest.approx(k_raw, abs=1e-5) == 1.0
    assert pytest.approx(k_quad, abs=1e-5) == 1.0


def test_cohen_kappa_systematic_disagreement():
    """Opposite ratings must yield negative kappa."""
    r1 = np.array([1, 1, 1, 1, -1, -1, -1, -1])
    r2 = np.array([-1, -1, -1, -1, 1, 1, 1, 1])

    k_raw = cohen_kappa(r1, r2, weights=None)
    assert k_raw < 0.0


def test_cohen_kappa_quadratic_weights_penalize_distance():
    """Quadratic kappa should be higher than unweighted kappa when errors are small (adjacent)."""
    # Raters differ by only 1 step
    r1 = np.array([0, 1, 2, 1, 0, -1, -2, 0])
    r2 = np.array([1, 2, 1, 0, 1, 0, -1, -1])

    k_raw = cohen_kappa(r1, r2, weights=None)
    k_quad = cohen_kappa(r1, r2, weights="quadratic")

    assert k_quad > k_raw


def test_fleiss_kappa_known_synthetic():
    """Test Fleiss' Kappa with 14 items, 5 categories, 4 raters."""
    # Matrix of shape (items, categories)
    # Perfect agreement case
    mat_perfect = np.array([
        [4, 0, 0],
        [0, 4, 0],
        [0, 0, 4],
        [4, 0, 0],
    ])
    assert pytest.approx(fleiss_kappa(mat_perfect), abs=1e-5) == 1.0


def test_krippendorff_alpha_nominal_and_ordinal():
    """Test Krippendorff's alpha on synthetic paired data."""
    # Perfect agreement
    r1 = np.array([1, 2, 3, 4, 5])
    r2 = np.array([1, 2, 3, 4, 5])
    data = np.vstack([r1, r2])

    a_nom = krippendorff_alpha(data, level_of_measurement="nominal")
    a_ord = krippendorff_alpha(data, level_of_measurement="ordinal")
    assert pytest.approx(a_nom, abs=1e-5) == 1.0
    assert pytest.approx(a_ord, abs=1e-5) == 1.0


def test_bootstrap_agreement_ci_validity():
    """Bootstrap CI should contain the point estimate and produce lower <= upper."""
    np.random.seed(42)
    r1 = np.array([1, 1, 2, 0, -1, 2, 1, 0, -2, 1, 0, 2] * 4)
    r2 = np.array([1, 2, 2, 0, -1, 1, 1, 0, -1, 1, 0, 2] * 4)

    ci = bootstrap_agreement_ci(r1, r2, n_boot=200, seed=42)

    for metric_name, (low, high) in ci.items():
        assert low <= high, f"Inverted CI for {metric_name}: [{low}, {high}]"
        assert -1.0 <= low <= 1.0
        assert -1.0 <= high <= 1.0


def test_extract_adjudication_candidates():
    """Discrepancies >= 2 should be flagged as MAJOR and adjudication_required = 1."""
    synthetic_rows = [
        {"statement_id": "test_01", "regime": "Fed", "decision_date": "2023-01-01", "coder_id": "c1", "hawkish_dovish": 1, "inflation_concern": 2, "growth_concern": 0, "uncertainty": 1, "forward_guidance_shift": 0},
        {"statement_id": "test_01", "regime": "Fed", "decision_date": "2023-01-01", "coder_id": "c2", "hawkish_dovish": -1, "inflation_concern": 2, "growth_concern": 1, "uncertainty": 1, "forward_guidance_shift": 0},
        {"statement_id": "test_02", "regime": "ECB", "decision_date": "2023-02-01", "coder_id": "c1", "hawkish_dovish": 0, "inflation_concern": 1, "growth_concern": 1, "uncertainty": 0, "forward_guidance_shift": 0},
        {"statement_id": "test_02", "regime": "ECB", "decision_date": "2023-02-01", "coder_id": "c2", "hawkish_dovish": 0, "inflation_concern": 1, "growth_concern": 1, "uncertainty": 0, "forward_guidance_shift": 0},
    ]
    df = pd.DataFrame(synthetic_rows)
    disc = extract_adjudication_candidates(df, coder1_col="c1", coder2_col="c2")

    # test_01 hawkish_dovish diff is |1 - (-1)| = 2 -> MAJOR
    major = disc[disc["severity"] == "MAJOR"]
    assert len(major) == 1
    assert major.iloc[0]["statement_id"] == "test_01"
    assert major.iloc[0]["dimension"] == "hawkish_dovish"
    assert major.iloc[0]["adjudication_required"] == 1

    # test_01 growth_concern diff is |0 - 1| = 1 -> MINOR
    minor = disc[disc["severity"] == "MINOR"]
    assert len(minor) == 1
    assert minor.iloc[0]["dimension"] == "growth_concern"
    assert minor.iloc[0]["adjudication_required"] == 0
