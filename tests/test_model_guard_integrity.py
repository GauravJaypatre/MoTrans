"""Integrity test suite verifying model guardrails and leakage prevention.

Ensures:
1. Test-split outcome columns (clr_1 to clr_60) are physically blocked unless unlocked.
2. Unauthorized attempts raise PermissionError and append to the audit log.
3. Production modeling scripts rely on model_guard / data_loader rather than bypassing.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
import pandas as pd

from src.model_guard import load_v2_1_table, assert_no_test_or_post
from src.modeling.data_loader import (
    load_modeling_data,
    OUTCOME_COLS,
)

ROOT = Path(__file__).resolve().parent.parent


def test_data_loader_blocks_test_outcomes_by_default(tmp_path, monkeypatch):
    """Attempting to load test split with outcomes must raise PermissionError."""
    log_file = tmp_path / "test_audit.log"
    monkeypatch.setenv("MOTRANS_AUDIT_LOG", str(log_file))
    monkeypatch.delenv("UNLOCK_TEST", raising=False)

    with pytest.raises(PermissionError, match="strictly locked"):
        load_modeling_data(table="tier1", split="test", include_outcomes=True)

    # Verify that the unauthorized attempt was recorded in the redirected log
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "UNLOCK_TEST_UNAUTHORIZED_ATTEMPT" in content


def test_data_loader_requires_both_env_and_argument(tmp_path, monkeypatch):
    """Both UNLOCK_TEST=1 and allow_test_outcomes=True are required to access test outcomes."""
    log_file = tmp_path / "test_audit.log"
    monkeypatch.setenv("MOTRANS_AUDIT_LOG", str(log_file))

    # Case 1: UNLOCK_TEST=1 in env, but allow_test_outcomes=False in code
    monkeypatch.setenv("UNLOCK_TEST", "1")
    with pytest.raises(PermissionError, match="strictly locked"):
        load_modeling_data(table="tier1", split="test", include_outcomes=True, allow_test_outcomes=False)

    # Case 2: UNLOCK_TEST unset in env, but allow_test_outcomes=True in code
    monkeypatch.delenv("UNLOCK_TEST", raising=False)
    with pytest.raises(PermissionError, match="strictly locked"):
        load_modeling_data(table="tier1", split="test", include_outcomes=True, allow_test_outcomes=True)


def test_data_loader_allows_features_without_outcomes(monkeypatch):
    """Loading test split without outcomes is permitted for feature distribution inspection."""
    monkeypatch.delenv("UNLOCK_TEST", raising=False)
    df_test = load_modeling_data(table="tier1", split="test", include_outcomes=False)
    assert not df_test.empty
    for col in OUTCOME_COLS:
        assert col not in df_test.columns


def test_model_guard_load_table_blocks_test_by_default(tmp_path, monkeypatch):
    """load_v2_1_table with split='test' must raise PermissionError if unlocked flag is absent."""
    log_file = tmp_path / "test_audit.log"
    monkeypatch.setenv("MOTRANS_AUDIT_LOG", str(log_file))
    monkeypatch.delenv("UNLOCK_TEST", raising=False)

    with pytest.raises(PermissionError, match="locked"):
        load_v2_1_table("analysis_tier1", split="test")


def test_production_modeling_scripts_use_safe_loaders():
    """Verify that exploratory modeling scripts do not hardcode assignment to UNLOCK_TEST."""
    modeling_dir = ROOT / "src" / "modeling"
    for py_file in modeling_dir.glob("*.py"):
        if py_file.name in ["run_v1_blind_test.py"]:
            continue  # v1 historical script operates on v1 data/final
        text = py_file.read_text(encoding="utf-8")
        assert 'os.environ["UNLOCK_TEST"] = "1"' not in text, f"Illegal hardcoded unlock assignment in {py_file.name}"
        assert "os.environ['UNLOCK_TEST'] = '1'" not in text, f"Illegal hardcoded unlock assignment in {py_file.name}"
