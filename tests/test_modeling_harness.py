"""Unit and integration test suite for MoTrans-15 Modeling Harness.

Verifies:
1. Leakage prevention: physical blocking of test outcomes unless unlocked.
2. Fold-safe preprocessing: scaler fit on validation or test raises ValueError.
3. Cluster helpers & overlap filtering.
4. Tier separation: pooled estimation requires tier dummy; secondary holds require sensitivity flag.
5. Ledger logging & automatic caveat enforcement on final_fit.
"""

from __future__ import annotations

import os
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.modeling.data_loader import (
    OUTCOME_COLS,
    load_modeling_data,
    load_fold_data,
)
from src.modeling.pipeline import (
    FoldSafeScaler,
    standardize_by_fold,
)
from src.modeling.clustering import (
    get_cluster_ids,
    filter_overlap,
    fit_ols_clustered,
)
from src.modeling.tier_handler import (
    validate_tier_spec,
    prepare_tier_sample,
)
from src.modeling.results_writer import (
    ResultsLedger,
    log_model_result,
    MANDATORY_FINAL_FIT_CAVEAT,
)


def test_data_loader_blocks_test_outcomes_by_default(monkeypatch):
    """Test split outcomes must be strictly blocked unless explicitly unlocked."""
    monkeypatch.delenv("UNLOCK_TEST", raising=False)

    # 1. Attempting to load test split with outcomes must raise PermissionError
    with pytest.raises(PermissionError, match="strictly locked"):
        load_modeling_data(table="tier1", split="test", include_outcomes=True)

    # 2. Loading test split WITHOUT outcomes is permitted (for feature-only inspection)
    df_test_features = load_modeling_data(table="tier1", split="test", include_outcomes=False)
    assert not df_test_features.empty
    for col in OUTCOME_COLS:
        assert col not in df_test_features.columns

    # 3. Unlocked access succeeds when both UNLOCK_TEST=1 and allow_test_outcomes=True
    monkeypatch.setenv("UNLOCK_TEST", "1")
    df_unlocked = load_modeling_data(
        table="tier1",
        split="test",
        include_outcomes=True,
        allow_test_outcomes=True,
    )
    assert not df_unlocked.empty
    assert "clr_5" in df_unlocked.columns


def test_data_loader_train_val_and_folds():
    """Verify normal loading of train, validation, and fold subsets."""
    df_tv = load_modeling_data(table="tier1", split="train_val")
    assert not df_tv.empty
    assert (df_tv["final_split"].isin(["train", "validation"])).all()
    assert (df_tv["embargo_dropped"] == 0).all()

    # Load Fold 1
    fold1_train = load_fold_data(fold_id=1, table="tier1", role="train")
    fold1_val = load_fold_data(fold_id=1, table="tier1", role="val")
    assert not fold1_train.empty
    assert not fold1_val.empty
    assert (fold1_train["fold_1"] == "train").all()
    assert (fold1_val["fold_1"] == "val").all()


def test_fold_safe_scaler_leakage_rejection():
    """Scaler fit must strictly reject validation or test observations."""
    scaler = FoldSafeScaler(feature_cols=["shock_raw_bp"])

    # Construct sample dataframe containing train and validation
    df = pd.DataFrame({
        "shock_raw_bp": [10.0, -5.0, 2.5, 7.0],
        "final_split": ["train", "train", "validation", "train"],
    })

    # Attempting to fit without mask when validation is present must raise ValueError
    with pytest.raises(ValueError, match="Data leakage detected"):
        scaler.fit(df)

    # Explicit mask that mistakenly includes validation row must also raise ValueError
    bad_mask = pd.Series([True, True, True, False])
    with pytest.raises(ValueError, match="Data leakage detected"):
        scaler.fit(df, is_train_mask=bad_mask)

    # Clean training mask succeeds
    good_mask = pd.Series([True, True, False, True])
    scaler.fit(df, is_train_mask=good_mask)
    assert scaler.is_fitted_

    transformed = scaler.transform(df)
    assert "shock_raw_bp_fold_std" in transformed.columns
    # Check that training mean is zero
    train_transformed = transformed.loc[good_mask, "shock_raw_bp_fold_std"]
    assert np.isclose(train_transformed.mean(), 0.0, atol=1e-7)


def test_standardize_by_fold_helper():
    df_train = pd.DataFrame({"shock_raw_bp": [10.0, 20.0, 30.0], "final_split": ["train"] * 3})
    df_val = pd.DataFrame({"shock_raw_bp": [15.0, 25.0], "final_split": ["validation"] * 2})

    scaled_train, scaled_val, scaler = standardize_by_fold(df_train, df_val)
    assert scaler.is_fitted_
    assert np.isclose(scaled_train["shock_raw_bp_fold_std"].mean(), 0.0)
    assert np.isclose(scaled_train["shock_raw_bp_fold_std"].std(ddof=1), 1.0)
    # Validation is transformed using train parameters (mean=20, std=10)
    # Val 15 -> (15-20)/10 = -0.5
    assert np.isclose(scaled_val["shock_raw_bp_fold_std"].iloc[0], -0.5)


def test_clustering_and_overlap_helpers():
    df = load_modeling_data(table="tier1", split="train")

    c_event, c_index = get_cluster_ids(df)
    assert len(c_event) == len(df)
    assert len(c_index) == len(df)

    # Overlap filter
    clean_df = filter_overlap(df, horizon="5d", method="drop")
    assert len(clean_df) <= len(df)
    assert (clean_df["overlap_prior_5d"] == 0).all()

    # Clustered OLS fit
    fit_res = fit_ols_clustered(
        df=df,
        y_col="clr_5",
        x_cols=["shock_raw_bp", "ctrl_vix"],
        cluster_col="event_id",
    )
    assert fit_res["n_obs"] > 0
    assert fit_res["n_events"] > 0
    assert fit_res["n_clusters"] > 0
    assert "coef_shock" in fit_res
    assert "se_shock" in fit_res
    assert not np.isnan(fit_res["p_val"])


def test_tier_discipline_enforcement():
    # 1. Secondary holds without sensitivity flag must fail
    with pytest.raises(ValueError, match="Secondary holds cannot be modeled as primary evidence"):
        validate_tier_spec("secondary_holds", is_sensitivity=False)

    validate_tier_spec("secondary_holds", is_sensitivity=True)  # passes

    # 2. Pooling Tier 1 and Tier 2 without shock_tier indicator must fail
    with pytest.raises(ValueError, match="cannot be pooled into a common sample without"):
        validate_tier_spec("pooled", feature_cols=["shock_raw_bp", "ctrl_vix"])

    validate_tier_spec("pooled", feature_cols=["shock_raw_bp", "shock_tier", "ctrl_vix"])  # passes

    # 3. prepare_tier_sample produces correct columns
    df_pooled = prepare_tier_sample(tier="pooled", split="train")
    assert "shock_tier" in df_pooled.columns
    assert set(df_pooled["shock_tier"].unique()) == {1, 2}


def test_results_ledger_and_caveat_append(tmp_path):
    ledger_file = tmp_path / "test_ledger.csv"
    ledger = ResultsLedger(ledger_path=ledger_file)

    # 1. Log a fold run
    res1 = ledger.log_result(
        model_id="MOD_001",
        model_name="baseline_tier1_fold1",
        tier="tier1",
        sample="train",
        fold="fold_1",
        outcome_col="clr_5",
        shock_col="shock_raw_bp_fold_std",
        specification="clr_5 ~ shock_raw_bp_fold_std + ctrl_vix",
        n_obs=1000,
        n_events=120,
        n_clusters=120,
        coef_shock=-0.015,
        se_shock=0.005,
        t_stat=-3.0,
        p_val=0.0027,
        ci_lower=-0.025,
        ci_upper=-0.005,
        r2=0.045,
        caveats="pre-COVID origin",
    )
    assert res1["caveats"] == "pre-COVID origin"

    # 2. Log a final_fit run: MUST automatically append mandatory caveat
    res2 = ledger.log_result(
        model_id="MOD_002",
        model_name="baseline_tier1_final_fit",
        tier="tier1",
        sample="final_fit",
        fold="none",
        outcome_col="clr_5",
        shock_col="shock_raw_bp_fold_std",
        specification="clr_5 ~ shock_raw_bp_fold_std + ctrl_vix",
        n_obs=5000,
        n_events=300,
        n_clusters=300,
        coef_shock=-0.012,
        se_shock=0.004,
        t_stat=-3.0,
        p_val=0.0027,
        ci_lower=-0.020,
        ci_upper=-0.004,
        r2=0.041,
        caveats="robustness check",
    )
    assert MANDATORY_FINAL_FIT_CAVEAT in res2["caveats"]

    df_l = ledger.read_ledger()
    assert len(df_l) == 2
    assert df_l.iloc[1]["sample"] == "final_fit"
    assert MANDATORY_FINAL_FIT_CAVEAT in df_l.iloc[1]["caveats"]

