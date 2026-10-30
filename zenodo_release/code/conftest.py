"""Pytest configuration for isolated Zenodo release code package.

Automatically skips tests that depend on data directories excluded from the
public release package per license and privacy safety rules (e.g. data/raw,
data/final, data/v2, unredacted panel.parquet, post_window_2026.parquet).
"""

from __future__ import annotations

from pathlib import Path
import pytest

REASON_EXCLUDED = "requires data excluded from public release; see LIMITATIONS_PACKAGE.md"

def pytest_collection_modifyitems(config, items):
    root = Path(config.rootdir)
    missing_final = not (root / "data" / "final").exists()
    missing_v2 = not (root / "data" / "v2").exists()
    missing_outputs_v2 = not (root / "outputs" / "v2").exists()
    missing_unredacted_v2_1 = not (root / "data" / "v2_1" / "panel.parquet").exists()
    missing_docs_summary = not (root / "docs" / "PROJECT_SUMMARY.md").exists()

    skip_marker = pytest.mark.skip(reason=REASON_EXCLUDED)

    for item in items:
        nodeid = item.nodeid
        if "test_analysis_tables.py" in nodeid and missing_final:
            item.add_marker(skip_marker)
        elif "test_v2_tables.py" in nodeid and missing_v2:
            item.add_marker(skip_marker)
        elif "test_v2_1_tables.py" in nodeid and missing_unredacted_v2_1:
            item.add_marker(skip_marker)
        elif "test_project_summary.py" in nodeid and missing_docs_summary:
            item.add_marker(skip_marker)
        elif "test_v2_v0_coverage.py" in nodeid and missing_outputs_v2:
            if any(name in nodeid for name in [
                "test_coverage_csv_exists_and_valid",
                "test_v2_spec_states_exploratory",
                "test_effective_sample_csvs",
                "test_holdout_candidates_csv",
            ]):
                item.add_marker(skip_marker)
        elif "test_v2_v1_verification.py" in nodeid and missing_outputs_v2:
            item.add_marker(skip_marker)


@pytest.fixture(autouse=True)
def redirect_audit_log(tmp_path, monkeypatch):
    """Ensure that running tests never modifies production unlock audit logs."""
    test_log = tmp_path / "test_unlock_audit.log"
    monkeypatch.setenv("MOTRANS_AUDIT_LOG", str(test_log))
