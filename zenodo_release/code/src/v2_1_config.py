"""MoTrans-15 v2.1 Configuration and Split Parameters.

Single source of truth for dataset parameters, time horizons, splits, embargo, and folds.
"""

from __future__ import annotations

import datetime as dt

# Dataset Global Boundaries
WINDOW_START = "2010-01-01"
WINDOW_END = "2025-12-31"

# Primary Splits
TRAIN_START = "2010-01-01"
TRAIN_END = "2021-12-31"

VAL_START = "2022-01-01"
VAL_END = "2023-12-31"

TEST_START = "2024-01-01"
TEST_END = "2025-12-31"

POST_WINDOW_START = "2026-01-01"

# Embargo Parameter (Trading days / calendar window for clr_60)
EMBARGO_DAYS = 60

# Rolling-origin development folds inside TRAIN + VALIDATION (TEST is strictly locked)
FOLD_ORIGINS = [
    "2016-01-01",
    "2018-01-01",
    "2020-01-01",
    "2022-01-01",
]

# Split definitions mapping
SPLIT_BOUNDARIES = {
    "train": (TRAIN_START, TRAIN_END),
    "validation": (VAL_START, VAL_END),
    "test": (TEST_START, TEST_END),
    "post_window": (POST_WINDOW_START, "2099-12-31"),
}
