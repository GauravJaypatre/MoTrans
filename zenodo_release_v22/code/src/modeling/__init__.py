"""MoTrans-15 Leakage-Proof Modeling Harness.

Provides temporal isolation, fold-safe preprocessing, cluster-robust inference,
tier separation enforcement, and results ledger logging.
"""

from __future__ import annotations

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
)

__all__ = [
    "OUTCOME_COLS",
    "load_modeling_data",
    "load_fold_data",
    "FoldSafeScaler",
    "standardize_by_fold",
    "get_cluster_ids",
    "filter_overlap",
    "fit_ols_clustered",
    "validate_tier_spec",
    "prepare_tier_sample",
    "ResultsLedger",
    "log_model_result",
]

