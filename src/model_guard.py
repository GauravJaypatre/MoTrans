"""Model Guardrail — MoTrans-15 v2.0.

Enforces strict temporal isolation and prevents data leakage:
1. Rejects any model training on 'final_holdout' (final 12 months of available data).
2. Rejects any model training on 'blind_test' (held out for v1.0 pre-registered evaluation).
3. Verifies that time-ordered validation sets enforce an embargo of at least 60 trading days.
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import pandas as pd

# Final 12 months of available data (2026-10-13 minus 365 days)
FINAL_HOLDOUT_START = dt.date(2025, 10, 14)


V2_WINDOW_START = dt.date(2010, 1, 1)


def split_tag_v2(date: dt.date | str) -> str:
    """Return split tag for v2.0 exploratory time-series modeling."""
    if isinstance(date, str):
        date = dt.date.fromisoformat(str(date)[:10])
    elif isinstance(date, pd.Timestamp):
        date = date.date()

    if date < V2_WINDOW_START:
        return "pre2010_robustness"
    if date >= FINAL_HOLDOUT_START:
        return "final_holdout"
    return "model_train_val"


def assert_no_holdout(df: pd.DataFrame, allow_holdout: bool = False, allow_blind_test: bool = False) -> None:
    """Assert that a dataset passed to a training model contains zero holdout or blind-test observations."""
    unlock_holdout = allow_holdout or os.environ.get("UNLOCK_HOLDOUT") == "1"
    unlock_blind = allow_blind_test or os.environ.get("UNLOCK_BLIND") == "1"

    if not unlock_holdout:
        if "split_tag" in df.columns:
            if (df["split_tag"] == "final_holdout").any():
                raise PermissionError("Access to 'final_holdout' is locked by model_guard.py. Training on holdout data is strictly forbidden without UNLOCK_HOLDOUT=1.")
        if "date" in df.columns:
            d_col = pd.to_datetime(df["date"]).dt.date
            if (d_col >= FINAL_HOLDOUT_START).any():
                raise PermissionError("Dates >= 2025-10-14 belong to 'final_holdout' and are locked by model_guard.py. Set UNLOCK_HOLDOUT=1 to override.")
        if "decision_date" in df.columns:
            d_col = pd.to_datetime(df["decision_date"]).dt.date
            if (d_col >= FINAL_HOLDOUT_START).any():
                raise PermissionError("Decision dates >= 2025-10-14 belong to 'final_holdout' and are locked by model_guard.py. Set UNLOCK_HOLDOUT=1 to override.")

    if not unlock_blind:
        if "split_tag" in df.columns:
            if (df["split_tag"] == "blind_test").any():
                raise PermissionError("Access to 'blind_test' is locked for exploratory training. Pre-registered blind test data cannot be accessed without UNLOCK_BLIND=1.")


def verify_embargo(train_dates: pd.Series | list | dt.date | str, val_dates: pd.Series | list | dt.date | str, min_embargo_days: int = 60) -> bool:
    """Verify that validation dates start at least min_embargo_days after the maximum training date."""
    if isinstance(train_dates, (pd.Series, pd.Index, list, tuple)):
        max_train = pd.to_datetime(train_dates).max()
    else:
        max_train = pd.to_datetime(train_dates)

    if isinstance(val_dates, (pd.Series, pd.Index, list, tuple)):
        min_val = pd.to_datetime(val_dates).min()
    else:
        min_val = pd.to_datetime(val_dates)

    gap = (min_val - max_train).days
    if gap < min_embargo_days:
        raise ValueError(f"Temporal leak detected: validation starts only {gap} days after training (required embargo >= {min_embargo_days} days).")
    return True
