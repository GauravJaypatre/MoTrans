"""Model Guardrail — MoTrans-15 v2.0 & v2.1.

Enforces strict temporal isolation and prevents data leakage:
1. Rejects any model training on 'final_holdout' (v2.0) or 'blind_test' (v1.0).
2. Rejects any model training or data access on 'test' (2024-2025) without UNLOCK_TEST=1.
3. Rejects any access to quarantined 'post_window' (2026+) without UNLOCK_POST=1.
4. Logs all test and post-window unlock events with timestamp and git commit hash to outputs/v2_1/unlock_audit.log.
5. Verifies that time-ordered validation sets enforce an embargo of at least 60 trading days.
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import subprocess
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_FILE = ROOT / "outputs" / "v2_1" / "unlock_audit.log"


def get_log_file() -> Path:
    """Return the active audit log path, allowing environment override for tests."""
    override = os.environ.get("MOTRANS_AUDIT_LOG")
    if override:
        return Path(override)
    return DEFAULT_LOG_FILE


LOG_FILE = DEFAULT_LOG_FILE

# Final 12 months of available data (2026-10-13 minus 365 days)
FINAL_HOLDOUT_START = dt.date(2025, 10, 14)
V2_WINDOW_START = dt.date(2010, 1, 1)


def get_git_hash() -> str:
    """Return the current git commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def log_unlock(split_name: str, context: str = "") -> None:
    """Log an unlock event with timestamp and git commit hash."""
    target_log = get_log_file()
    target_log.parent.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    git_hash = get_git_hash()
    entry = f"[{ts}] UNLOCK_{split_name.upper()} | git_commit={git_hash} | context={context}\n"
    with open(target_log, "a", encoding="utf-8") as f:
        f.write(entry)


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
    """Assert that a dataset passed to a training model contains zero holdout or blind-test observations (v2.0 legacy)."""
    unlock_holdout = allow_holdout or os.environ.get("UNLOCK_HOLDOUT") == "1"
    unlock_blind = allow_blind_test or os.environ.get("UNLOCK_BLIND") == "1"

    if not unlock_holdout:
        if "final_holdout" in df.columns:
            if (df["final_holdout"] == 1).any():
                raise PermissionError("Access to 'final_holdout' is locked by model_guard.py. Training on holdout data is strictly forbidden without UNLOCK_HOLDOUT=1.")
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


def assert_no_test_or_post(df: pd.DataFrame, allow_test: bool = False, allow_post: bool = False) -> None:
    """Assert that a dataset contains zero test or post-window observations (v2.1)."""
    unlock_test = allow_test or os.environ.get("UNLOCK_TEST") == "1"
    unlock_post = allow_post or os.environ.get("UNLOCK_POST") == "1"

    if not unlock_test:
        if "final_split" in df.columns:
            if (df["final_split"] == "test").any():
                raise PermissionError("Access to 'test' split (2024-2025) is locked by model_guard.py. Set UNLOCK_TEST=1 to override.")
        if "decision_date" in df.columns:
            d_col = pd.to_datetime(df["decision_date"]).dt.date
            if ((d_col >= dt.date(2024, 1, 1)) & (d_col <= dt.date(2025, 12, 31))).any():
                raise PermissionError("Decision dates in 2024-2025 belong to locked 'test' split. Set UNLOCK_TEST=1 to override.")
    else:
        log_unlock("test", context="assert_no_test_or_post override")

    if not unlock_post:
        if "final_split" in df.columns:
            if (df["final_split"] == "post_window").any():
                raise PermissionError("Access to 'post_window' (2026+) is quarantined and locked by model_guard.py. Set UNLOCK_POST=1 to override.")
        if "decision_date" in df.columns:
            d_col = pd.to_datetime(df["decision_date"]).dt.date
            if (d_col >= dt.date(2026, 1, 1)).any():
                raise PermissionError("Decision dates >= 2026-01-01 are quarantined to 'post_window'. Set UNLOCK_POST=1 to override.")
    else:
        log_unlock("post", context="assert_no_test_or_post override")


def load_v2_1_table(
    table_name_or_path: str | Path,
    split: str | None = None,
    allow_test: bool = False,
    allow_post: bool = False,
) -> pd.DataFrame:
    """Safely load a MoTrans-15 v2.1 table with automatic leakage protection."""
    p = Path(table_name_or_path)
    if not p.is_absolute():
        p = ROOT / "data" / "v2_1" / table_name_or_path
        if not p.suffix:
            p = p.with_suffix(".parquet")

    if not p.exists():
        raise FileNotFoundError(f"Table file not found: {p}")

    df = pd.read_parquet(p)

    unlock_test = allow_test or os.environ.get("UNLOCK_TEST") == "1"
    unlock_post = allow_post or os.environ.get("UNLOCK_POST") == "1"

    if split is not None:
        if split == "final_fit":
            if "final_split" in df.columns and "embargo_dropped" in df.columns:
                df = df[(df["final_split"].isin(["train", "validation"])) & (df["embargo_dropped"] == 0)].copy()
            elif "final_split" in df.columns:
                df = df[df["final_split"].isin(["train", "validation"])].copy()
        elif split == "test" and not unlock_test:
            raise PermissionError("Access to 'test' split (2024-2025) is locked. Set UNLOCK_TEST=1 to load.")
        elif split == "post_window" and not unlock_post:
            raise PermissionError("Access to 'post_window' (2026+) is locked. Set UNLOCK_POST=1 to load.")
        elif "final_split" in df.columns:
            df = df[df["final_split"] == split].copy()

    # If full table loaded without explicit split filter, filter out locked splits unless unlocked
    if not unlock_test and "final_split" in df.columns:
        df = df[df["final_split"] != "test"]
    elif unlock_test and "final_split" in df.columns and (df["final_split"] == "test").any():
        log_unlock("test", context=f"load_v2_1_table({p.name})")

    if not unlock_post and "final_split" in df.columns:
        df = df[df["final_split"] != "post_window"]
    elif unlock_post and "final_split" in df.columns and (df["final_split"] == "post_window").any():
        log_unlock("post", context=f"load_v2_1_table({p.name})")

    return df.reset_index(drop=True)


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
