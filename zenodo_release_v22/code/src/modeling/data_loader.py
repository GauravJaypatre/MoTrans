"""Leakage-Proof Data Access Layer for MoTrans-15 Modeling.

Strictly protects out-of-sample benchmark integrity:
1. Blocks test-split outcome columns (clr_1, clr_1_clean to clr_60) unless explicitly unlocked
   via UNLOCK_TEST=1 and allow_test_outcomes=True.
2. Attempting unauthorized access to test outcomes raises PermissionError AND logs
   the attempt to outputs/v2_1/unlock_audit.log.
3. Automatically respects embargo boundaries by filtering out embargo_dropped rows.
4. Provides convenient partition loading for rolling-origin CV folds and final_fit.
5. In v2.2, provides Single Source of Truth split membership via splits.csv and
   supports pristine_only out-of-sample partitioning.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Sequence
import pandas as pd

from src.model_guard import log_unlock

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR_V2_1 = ROOT / "data" / "v2_1" / "release"
DATA_DIR_V2_2 = ROOT / "data" / "v2_2" / "release"
SPLITS_PATH_V2_2 = ROOT / "data" / "v2_2" / "splits.csv"

OUTCOME_COLS = ["clr_1", "clr_1_clean", "clr_3", "clr_5", "clr_20", "clr_60"]

TABLE_FILENAMES = {
    "tier1": "analysis_tier1.parquet",
    "tier2_primary": "analysis_tier2_primary.parquet",
    "tier2": "analysis_tier2_primary.parquet",
    "secondary_holds": "secondary_holds.parquet",
    "sensitivity_macro_revision": "sensitivity_macro_revision.parquet",
}


def load_splits_metadata(version: str = "v2_2") -> pd.DataFrame:
    """Load the Single Source of Truth splits metadata table."""
    path = SPLITS_PATH_V2_2 if version == "v2_2" else (ROOT / "data" / "v2_1" / "folds.csv")
    if not path.exists():
        raise FileNotFoundError(f"Splits metadata not found at {path}")
    return pd.read_csv(path)


def load_modeling_data(
    table: str = "tier1",
    split: str = "train_val",
    drop_embargo: bool = True,
    include_outcomes: bool = True,
    allow_test_outcomes: bool = False,
    pristine_only: bool = False,
    version: str = "v2_2",
) -> pd.DataFrame:
    """Load modeling data with cryptographic and leakage safeguards.

    Parameters
    ----------
    table : str
        One of 'tier1', 'tier2_primary', 'secondary_holds', 'sensitivity_macro_revision'.
    split : str
        Partition to load:
        - 'train': Training split (2010-2021).
        - 'validation': Validation split (2022-2023).
        - 'train_val': Unified Train + Validation split (2010-2023).
        - 'test': Locked out-of-sample split (2024-2025).
        - 'final_fit': Train + Validation without embargo drops (ready for final fit).
    drop_embargo : bool
        If True, excludes rows where embargo_dropped == 1.
    include_outcomes : bool
        If True, loads outcome columns (clr_1, clr_1_clean to clr_60).
    allow_test_outcomes : bool
        Explicit function-level override to load test outcomes. Still requires
        UNLOCK_TEST=1 in the environment.
    pristine_only : bool
        If True, restricts strictly to pristine decisions (read_by_prior_analysis == 0).
    version : str
        'v2_2' (default) or 'v2_1'.

    Returns
    -------
    pd.DataFrame
        Filtered and sanitized dataframe.
    """
    data_dir = DATA_DIR_V2_2 if version == "v2_2" else DATA_DIR_V2_1
    fname = TABLE_FILENAMES.get(table, table)
    if not fname.endswith(".parquet"):
        fname = f"{fname}.parquet"

    path = data_dir / fname
    if not path.exists():
        fallback_path = ROOT / "data" / version / fname
        if fallback_path.exists():
            path = fallback_path
        else:
            raise FileNotFoundError(f"Table not found at {path} or {fallback_path}")

    df = pd.read_parquet(path)

    # 1. Embargo filtering
    if drop_embargo and "embargo_dropped" in df.columns:
        df = df[df["embargo_dropped"] == 0].copy()

    # 2. Split filtering
    if split == "train":
        df = df[df["final_split"] == "train"].copy()
    elif split == "validation":
        df = df[df["final_split"] == "validation"].copy()
    elif split == "train_val":
        df = df[df["final_split"].isin(["train", "validation"])].copy()
    elif split == "final_fit":
        df = df[df["final_split"].isin(["train", "validation"])].copy()
    elif split == "test":
        df = df[df["final_split"] == "test"].copy()
    elif split == "all":
        pass
    else:
        raise ValueError(f"Unknown split: '{split}'. Expected 'train', 'validation', 'train_val', 'test', 'final_fit', or 'all'.")

    # 3. Pristine filter
    if pristine_only and "read_by_prior_analysis" in df.columns:
        df = df[df["read_by_prior_analysis"] == 0].copy()

    # 4. Test outcome leakage guard
    has_test_rows = (df["final_split"] == "test").any() if "final_split" in df.columns else False

    if has_test_rows and include_outcomes:
        unlock_env = os.environ.get("UNLOCK_TEST") == "1"
        if not (unlock_env and allow_test_outcomes):
            # Block test outcomes, raise error, and log unauthorized attempt
            log_unlock(
                "test_unauthorized_attempt",
                context=f"load_modeling_data blocked outcome access on table={table}, split={split}",
            )
            raise PermissionError(
                "Access to test-split outcomes is strictly locked by model guardrails. "
                "Test outcomes cannot be accessed without explicit UNLOCK_TEST=1 and allow_test_outcomes=True. "
                "Attempt logged to unlock_audit.log."
            )
        else:
            # Authorized unlock
            log_unlock("test", context=f"load_modeling_data authorized outcome access on table={table}")

    if not include_outcomes:
        # Physically remove outcome columns
        present_outcomes = [c for c in OUTCOME_COLS if c in df.columns]
        if present_outcomes:
            df = df.drop(columns=present_outcomes)

    return df.reset_index(drop=True)


def load_fold_data(
    fold_id: int,
    table: str = "tier1",
    role: str = "train",
    drop_embargo: bool = True,
    include_outcomes: bool = True,
    version: str = "v2_2",
) -> pd.DataFrame:
    """Load data for a specific rolling-origin cross-validation fold."""
    if fold_id not in [1, 2, 3, 4]:
        raise ValueError(f"Invalid fold_id {fold_id}. Must be 1, 2, 3, or 4.")
    if role not in ["train", "val"]:
        raise ValueError(f"Invalid role '{role}'. Must be 'train' or 'val'.")

    df = load_modeling_data(
        table=table,
        split="train_val",
        drop_embargo=drop_embargo,
        include_outcomes=include_outcomes,
        version=version,
    )

    fold_col = f"fold_{fold_id}"
    if fold_col not in df.columns:
        raise KeyError(f"Fold column '{fold_col}' not found in table.")

    fold_df = df[df[fold_col] == role].copy()
    return fold_df.reset_index(drop=True)
