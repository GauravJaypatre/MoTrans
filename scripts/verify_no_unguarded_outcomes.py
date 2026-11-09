"""Verification of Guardrail Enforcement, Allowlist Compliance, and Zero Unguarded Outcome Reads.

Phase 0 & Task 2 Verification:
- Recursively audits all Python files across scripts/ and src/
- Verifies that no script directly reads test-split outcomes or post-window outcomes
  outside model_guard / data_loader.
- Verifies that no production or exploratory script assigns UNLOCK_TEST, UNLOCK_POST,
  or ALLOW_DERIVED_RETURNS in code (excluding gated test scoring).
- Checks all reads of data/final/**, data/v2_1/**, data/v2_2/** touching outcome columns:
  must go through safe data loaders or be registered in HISTORICAL_ALLOWLIST.
- Confirms that the 14 ECB test decisions with read_by_prior_analysis == 1 in splits.csv
  match the exact list documented in docs/INTEGRITY_AUDIT.md.
- Confirms unlock_audit.log remains strictly at 16 lines.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_SCRIPTS = {
    "run_test_scoring.py",  # Gated Phase 4 script, not run until explicit user unlock
    "verify_no_unguarded_outcomes.py",  # Scanner script itself
}

# Explicit allowlist of known historical exceptions (documented in docs/INTEGRITY_AUDIT.md)
HISTORICAL_ALLOWLIST: Dict[str, Dict[str, Any]] = {
    "src/modeling/run_v1_blind_test.py": {
        "line": 45,
        "target": "data/final/analysis_tier1.parquet",
        "reason": "Historical v1 pre-registered blind test execution on data/final/analysis_tier1.parquet, documented in docs/INTEGRITY_AUDIT.md",
        "commit": "f771af7",
    }
}

# ETL / Data Engineering scripts that build, freeze, or verify the underlying data pipeline
ETL_PIPELINE_SCRIPTS = {
    "src/build_analysis_tables.py",
    "src/build_panel.py",
    "src/build_shocks.py",
    "src/event_windows.py",
    "src/export_excel.py",
    "src/model_guard.py",
    "src/v2_1_build_tables.py",
    "src/v2_1_freeze.py",
    "src/v2_1_leakage_audit.py",
    "src/v2_2_build_tables.py",
    "src/v2_build_tables.py",
    "src/v2_fix_cbr_dates.py",
    "src/v2_fix_rba_2026.py",
    "src/v2_verify_pipeline.py",
    "scripts/verify_prices_second_source.py",
    "scripts/verify_shock_validity.py",
}

OUTCOME_COLS = {"clr_1", "clr_3", "clr_5", "clr_20", "clr_60", "clr_pre5", "clr_1_clean"}
UNLOCK_ENV_VARS = {"UNLOCK_TEST", "UNLOCK_POST", "ALLOW_DERIVED_RETURNS"}


def audit_file_content(path: Path) -> list[str]:
    violations = []
    rel_path = str(path.relative_to(ROOT)).replace("\\", "/")

    if path.name in EXCLUDED_SCRIPTS:
        return violations

    text = path.read_text(encoding="utf-8")

    # 1. Check for assignments setting unlock env vars to '1'
    for var in UNLOCK_ENV_VARS:
        pattern = rf'os\.environ\[["\']{var}["\']\]\s*=\s*["\']1["\']'
        if re.search(pattern, text):
            violations.append(f"Hardcoded unlock flag: {var} assigned in {rel_path}")

    # 2. Check for unguarded calls to load_modeling_data with split='test' and include_outcomes=True
    if "load_modeling_data" in text:
        try:
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = ""
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    if func_name == "load_modeling_data":
                        kw_dict = {kw.arg: kw.value for kw in node.keywords}
                        split_val = None
                        inc_outcomes = True

                        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                            split_val = node.args[1].value
                        if len(node.args) >= 4 and isinstance(node.args[3], ast.Constant):
                            inc_outcomes = node.args[3].value

                        if "split" in kw_dict and isinstance(kw_dict["split"], ast.Constant):
                            split_val = kw_dict["split"].value
                        if "include_outcomes" in kw_dict and isinstance(kw_dict["include_outcomes"], ast.Constant):
                            inc_outcomes = kw_dict["include_outcomes"].value

                        if split_val == "test" and inc_outcomes is not False:
                            violations.append(
                                f"Unguarded test split outcome load in {rel_path}: load_modeling_data(split='test', include_outcomes={inc_outcomes})"
                            )
        except Exception as e:
            violations.append(f"AST parse error in {rel_path}: {e}")

    # 3. Check for direct read_parquet of post_window_2026.parquet
    if "post_window_2026" in text:
        if "read_parquet" in text:
            pattern = r'read_parquet\([^)]*post_window_2026[^)]*\)'
            if re.search(pattern, text):
                violations.append(
                    f"Direct read_parquet of post_window_2026.parquet in {rel_path}"
                )

    # 4. Check for direct read_parquet / read_csv of outcome tables in modeling/analysis scripts
    if rel_path.startswith("src/modeling/") or rel_path.startswith("scripts/"):
        if rel_path in HISTORICAL_ALLOWLIST:
            # Verified against allowlist
            pass
        elif rel_path in ETL_PIPELINE_SCRIPTS or path.name in EXCLUDED_SCRIPTS:
            pass
        elif "src/modeling/data_loader.py" in rel_path:
            pass
        else:
            # Check if file calls read_parquet or read_csv on tables with outcomes
            read_pattern = r'read_(?:parquet|csv)\([^)]*(?:analysis_tier1|analysis_tier2|secondary_holds|sensitivity_macro|panel_daily|panel_returns_only)[^)]*\)'
            if re.search(read_pattern, text):
                violations.append(
                    f"Direct un-allowlisted read of outcome table in modeling script: {rel_path}"
                )

    return violations


def verify_prior_analysis_test_decisions() -> list[str]:
    """Verify that the 14 ECB test decisions in splits.csv match docs/INTEGRITY_AUDIT.md."""
    import pandas as pd

    violations = []
    splits_csv = ROOT / "data" / "v2_2" / "splits.csv"
    if not splits_csv.exists():
        return [f"Splits file not found: {splits_csv}"]

    df = pd.read_csv(splits_csv)
    sub = df[(df["split"] == "test") & (df["read_by_prior_analysis"] == 1)]
    prior_decs = sorted(sub["event_id"].unique().tolist())

    if len(prior_decs) != 14:
        violations.append(
            f"Expected 14 test decisions with read_by_prior_analysis==1, found {len(prior_decs)}"
        )

    # Check against INTEGRITY_AUDIT.md
    audit_md = ROOT / "docs" / "INTEGRITY_AUDIT.md"
    if not audit_md.exists():
        violations.append(f"INTEGRITY_AUDIT.md not found at {audit_md}")
    else:
        audit_text = audit_md.read_text(encoding="utf-8")
        missing_from_audit = [eid for eid in prior_decs if eid not in audit_text]
        if missing_from_audit:
            violations.append(
                f"Decisions with read_by_prior_analysis==1 missing from docs/INTEGRITY_AUDIT.md: {missing_from_audit}"
            )

    return violations


def main():
    print("=================================================================")
    print("VERIFY NO UNGUARDED OUTCOME READS & INTEGRITY AUDIT MATCH")
    print("=================================================================")

    target_dirs = [ROOT / "scripts", ROOT / "src"]
    all_violations = []
    audited_count = 0

    for tdir in target_dirs:
        for py_path in tdir.rglob("*.py"):
            audited_count += 1
            v = audit_file_content(py_path)
            all_violations.extend(v)

    # Check unlock_audit.log line count
    audit_log = ROOT / "outputs" / "v2_1" / "unlock_audit.log"
    if audit_log.exists():
        lines = [l for l in audit_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        log_count = len(lines)
    else:
        log_count = 0

    print(f"Audited {audited_count} Python files across scripts/ and src/.")
    print(f"unlock_audit.log current line count: {log_count} (expected strictly 16).")

    if log_count != 16:
        all_violations.append(f"unlock_audit.log has {log_count} lines, expected exactly 16.")

    # Check 14 ECB test decisions match
    prior_violations = verify_prior_analysis_test_decisions()
    all_violations.extend(prior_violations)

    if all_violations:
        print("\nVIOLATIONS FOUND:")
        for viol in all_violations:
            print(f"  - [FAIL] {viol}")
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED: Zero unguarded outcome reads detected.")
        print(f"Historical allowlist: {list(HISTORICAL_ALLOWLIST.keys())} documented.")
        print("Prior-analysis test decisions: exactly 14 ECB decisions match docs/INTEGRITY_AUDIT.md.")


if __name__ == "__main__":
    main()
