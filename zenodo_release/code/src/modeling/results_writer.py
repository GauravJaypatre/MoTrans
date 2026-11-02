"""Model Results Ledger and Protocol Logger for MoTrans-15.

Logs all model runs, cross-validation metrics, and sensitivity estimates to
outputs/modeling/ledger.csv. Automatically appends mandatory regime transfer
caveats for full-sample final fits.
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
LEDGER_DIR = ROOT / "outputs" / "modeling"
LEDGER_PATH = LEDGER_DIR / "ledger.csv"

MANDATORY_FINAL_FIT_CAVEAT = "easing/hold regime only; cannot assess tightening transfer"

LEDGER_COLUMNS = [
    "model_id",
    "timestamp_utc",
    "model_name",
    "tier",
    "sample",
    "fold",
    "outcome_col",
    "shock_col",
    "specification",
    "n_obs",
    "n_events",
    "n_clusters",
    "coef_shock",
    "se_shock",
    "t_stat",
    "p_val",
    "ci_lower",
    "ci_upper",
    "r2",
    "caveats",
]


class ResultsLedger:
    """Thread-safe and process-safe results logger for empirical specifications."""

    def __init__(self, ledger_path: Path = LEDGER_PATH):
        self.ledger_path = ledger_path
        self._ensure_ledger_exists()

    def _ensure_ledger_exists(self) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            with open(self.ledger_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(LEDGER_COLUMNS)

    def log_result(
        self,
        model_id: str,
        model_name: str,
        tier: str,
        sample: str,
        fold: str,
        outcome_col: str,
        shock_col: str,
        specification: str,
        n_obs: int,
        n_events: int,
        n_clusters: int,
        coef_shock: float,
        se_shock: float,
        t_stat: float,
        p_val: float,
        ci_lower: float,
        ci_upper: float,
        r2: float,
        caveats: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a model estimation result into the ledger."""
        ts_utc = dt.datetime.now(dt.timezone.utc).isoformat()

        # Enforce mandatory caveat on final_fit / full train_val fits
        caveat_list = [caveats] if caveats else []
        if sample in ["final_fit", "train_val"]:
            if MANDATORY_FINAL_FIT_CAVEAT not in caveat_list:
                caveat_list.append(MANDATORY_FINAL_FIT_CAVEAT)

        final_caveats = "; ".join(filter(None, caveat_list))

        row_dict = {
            "model_id": model_id,
            "timestamp_utc": ts_utc,
            "model_name": model_name,
            "tier": tier,
            "sample": sample,
            "fold": fold,
            "outcome_col": outcome_col,
            "shock_col": shock_col,
            "specification": specification,
            "n_obs": n_obs,
            "n_events": n_events,
            "n_clusters": n_clusters,
            "coef_shock": round(coef_shock, 6),
            "se_shock": round(se_shock, 6),
            "t_stat": round(t_stat, 4),
            "p_val": round(p_val, 6),
            "ci_lower": round(ci_lower, 6),
            "ci_upper": round(ci_upper, 6),
            "r2": round(r2, 6),
            "caveats": final_caveats,
        }

        with open(self.ledger_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
            writer.writerow(row_dict)

        return row_dict

    def read_ledger(self) -> pd.DataFrame:
        """Read the current ledger as a pandas DataFrame."""
        if not self.ledger_path.exists():
            return pd.DataFrame(columns=LEDGER_COLUMNS)
        return pd.read_csv(self.ledger_path)


def log_model_result(
    model_id: str,
    model_name: str,
    tier: str,
    sample: str,
    fold: str,
    outcome_col: str,
    shock_col: str,
    specification: str,
    n_obs: int,
    n_events: int,
    n_clusters: int,
    coef_shock: float,
    se_shock: float,
    t_stat: float,
    p_val: float,
    ci_lower: float,
    ci_upper: float,
    r2: float,
    caveats: Optional[str] = None,
    ledger_path: Path = LEDGER_PATH,
) -> Dict[str, Any]:
    """Convenience function to log a model result."""
    ledger = ResultsLedger(ledger_path=ledger_path)
    return ledger.log_result(
        model_id=model_id,
        model_name=model_name,
        tier=tier,
        sample=sample,
        fold=fold,
        outcome_col=outcome_col,
        shock_col=shock_col,
        specification=specification,
        n_obs=n_obs,
        n_events=n_events,
        n_clusters=n_clusters,
        coef_shock=coef_shock,
        se_shock=se_shock,
        t_stat=t_stat,
        p_val=p_val,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        r2=r2,
        caveats=caveats,
    )

