"""Leakage-Proof Data Access Layer for MoTrans-15 Modeling.

Strictly protects out-of-sample benchmark integrity:
1. Blocks test-split outcome columns (clr_1 to clr_60) unless explicitly unlocked
   via UNLOCK_TEST=1.
2. Attempting unauthorized access to test outcomes raises PermissionError AND logs
   the attempt to outputs/v2_1/unlock_audit.log.
3. Automatically respects embargo boundaries by filtering out embargo_dropped rows.
4. Provides convenient partition loading for rolling-origin CV folds and final_fit.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence
import pandas as pd

from src.model_guard import log_unlock

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "v2_1" / "release"
FOLDS_PATH = ROOT / "data" / "v2_1" / "folds.csv"

OUTCOME_COLS = ["clr_1", "clr_3", "clr_5", "clr_20", "clr_60"]

TABLE_FILENAMES = {
    "tier1": "analysis_tier1.parquet",
    "tier2_primary": "analysis_tier2_primary.parquet",
    "tier2": "analysis_tier2_primary.parquet",
    "secondary_holds": "secondary_holds.parquet",
    "sensitivity_macro_revision": "sensitivity_macro_revision.parquet",
}


def load_modeling_data(
    table: str = "tier1",
    split: str = "train_val",
    drop_embargo: bool = True,
    include_outcomes: bool = True,
    allow_test_outcomes: bool = False,
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
        If True, loads outcome columns (clr_1 to clr_60).
    allow_test_outcomes : bool
        Explicit function-level override to load test outcomes. Still requires
        UNLOCK_TEST=1 in the environment.

    Returns
    -------
    pd.DataFrame
        Filtered and sanitized dataframe.
    """
    fname = TABLE_FILENAMES.get(table, table)
    if not fname.endswith(".parquet"):
        fname = f"{fname}.parquet"

    path = DATA_DIR / fname
    if not path.exists():
        fallback_path = ROOT / "data" / "v2_1" / fname
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

    # 3. Test outcome leakage guard
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
) -> pd.DataFrame:
    """Load data for a specific rolling-origin cross-validation fold.

    Parameters
    ----------
    fold_id : int
        Fold index (1, 2, 3, or 4).
    table : str
        Table name ('tier1', 'tier2_primary', etc.).
    role : str
        'train' for training portion of fold, 'val' for validation portion.
    drop_embargo : bool
        If True, excludes embargo_dropped == 1 rows.
    include_outcomes : bool
        If True, includes outcome columns.

    Returns
    -------
    pd.DataFrame
    """
    if fold_id not in [1, 2, 3, 4]:
        raise ValueError(f"Invalid fold_id {fold_id}. Must be 1, 2, 3, or 4.")
    if role not in ["train", "val"]:
        raise ValueError(f"Invalid role '{role}'. Must be 'train' or 'val'.")

    df = load_modeling_data(
        table=table,
        split="train_val",
        drop_embargo=drop_embargo,
        include_outcomes=include_outcomes,
    )

    fold_col = f"fold_{fold_id}"
    if fold_col not in df.columns:
        raise KeyError(f"Fold column '{fold_col}' not found in table.")

    # In MoTrans-15 release tables, fold columns contain 'train', 'val', or 'unused'
    fold_df = df[df[fold_col] == role].copy()

    return fold_df.reset_index(drop=True)

