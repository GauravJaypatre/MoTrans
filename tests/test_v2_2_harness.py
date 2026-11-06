"""Unit tests verifying MoTrans-15 v2.2 table schemas, splits metadata, and safe loaders."""

from __future__ import annotations

import ast
from pathlib import Path
import pytest
import pandas as pd

from src.modeling.data_loader import (
    load_modeling_data,
    load_splits_metadata,
    OUTCOME_COLS,
)
from src.modeling.tier_handler import prepare_tier_sample

ROOT = Path(__file__).resolve().parent.parent


def test_splits_csv_structure_and_counts():
    """Verify data/v2_2/splits.csv adheres strictly to Single Source of Truth specification."""
    splits = load_splits_metadata(version="v2_2")
    assert len(splits) == 718, f"Expected 718 decisions, got {len(splits)}"

    # Required columns
    expected_cols = {
        "event_id", "regime", "decision_date", "decision", "split",
        "fold_1", "fold_2", "fold_3", "fold_4", "embargo_dropped",
        "tier", "read_by_v1", "read_by_prior_analysis", "home_in_session",
        "timing_verified_level"
    }
    assert expected_cols.issubset(set(splits.columns))

    # Split breakdown
    split_counts = splits["split"].value_counts().to_dict()
    assert split_counts["train"] == 572
    assert split_counts["validation"] == 76
    assert split_counts["test"] == 70

    # Pristine test isolation
    test_split = splits[splits["split"] == "test"]
    assert len(test_split) == 70
    pristine_test = test_split[test_split["read_by_prior_analysis"] == 0]
    prior_exposed_test = test_split[test_split["read_by_prior_analysis"] == 1]
    assert len(pristine_test) == 56
    assert len(prior_exposed_test) == 14


def test_v2_2_tables_eliminate_shock_std_trap():
    """Verify v2.2 tables contain shock_raw_bp and shock_descriptive_2019, but NOT shock_std."""
    df_t1 = load_modeling_data("tier1", split="final_fit", version="v2_2")
    assert "shock_raw_bp" in df_t1.columns
    assert "shock_descriptive_2019" in df_t1.columns
    assert "shock_std" not in df_t1.columns

    # Verify window timing columns
    assert "in_session" in df_t1.columns
    assert "clr_1_clean" in df_t1.columns
    assert "clr_1" in df_t1.columns


def test_pristine_only_filter_in_loader():
    """Verify pristine_only=True correctly excludes prior-exposed decisions."""
    # Without pristine_only, test split has 70 decisions
    df_test_all = load_modeling_data("tier1", split="test", include_outcomes=False, pristine_only=False, version="v2_2")
    assert df_test_all["event_id"].nunique() == 14  # Tier 1 has 14 test decisions, all ECB

    # With pristine_only=True, Tier 1 has 0 test decisions (all 14 were evaluated in v1)
    df_test_pristine = load_modeling_data("tier1", split="test", include_outcomes=False, pristine_only=True, version="v2_2")
    assert df_test_pristine.empty

    # In Tier 2 primary, all 20 test decisions are pristine
    df_t2_pristine = load_modeling_data("tier2_primary", split="test", include_outcomes=False, pristine_only=True, version="v2_2")
    assert df_t2_pristine["event_id"].nunique() == 20


def test_clr_1_clean_is_blocked_on_test_by_default(tmp_path, monkeypatch):
    """Verify clr_1_clean is treated as an outcome column and blocked on test split without unlock."""
    log_file = tmp_path / "test_audit.log"
    monkeypatch.setenv("MOTRANS_AUDIT_LOG", str(log_file))
    monkeypatch.delenv("UNLOCK_TEST", raising=False)

    with pytest.raises(PermissionError, match="strictly locked"):
        load_modeling_data("tier1", split="test", include_outcomes=True, version="v2_2")


def test_no_modeling_script_reads_descriptive_shocks():
    """Static AST scan ensuring no modeling script in src/modeling/ accesses shock_descriptive_2019 or shock_std."""
    modeling_dir = ROOT / "src" / "modeling"
    prohibited_strings = {"shock_descriptive_2019", "shock_std"}
    
    violations = []
    for py_file in modeling_dir.glob("*.py"):
        if py_file.name in ["run_v1_blind_test.py"]:
            continue  # Historical v1 script operates on v1 data
        text = py_file.read_text(encoding="utf-8")
        for bad in prohibited_strings:
            # Check if used in regression formulas or feature_cols
            if f'"{bad}"' in text or f"'{bad}'" in text:
                violations.append(f"{py_file.name} references '{bad}'")

    assert not violations, f"Prohibited descriptive shock references found in modeling code: {violations}"
