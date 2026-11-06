"""Verification of Guardrail Enforcement and Zero Unguarded Outcome Reads.

Phase 0 Item (f):
- Recursively audits all Python files across scripts/ and src/
- Verifies that no script directly reads test-split outcomes or post-window outcomes
  outside model_guard / data_loader.
- Verifies that no production or exploratory script assigns UNLOCK_TEST, UNLOCK_POST,
  or ALLOW_DERIVED_RETURNS in code (excluding gated test scoring).
- Confirms unlock_audit.log remains strictly at 16 lines.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_SCRIPTS = {
    "run_test_scoring.py",  # Gated Phase 4 script, not run until explicit user unlock
    "verify_no_unguarded_outcomes.py",  # Scanner script itself
}

OUTCOME_COLS = {"clr_1", "clr_3", "clr_5", "clr_20", "clr_60", "clr_pre5"}
UNLOCK_ENV_VARS = {"UNLOCK_TEST", "UNLOCK_POST", "ALLOW_DERIVED_RETURNS"}


def audit_file_content(path: Path) -> list[str]:
    violations = []
    text = path.read_text(encoding="utf-8")

    # 1. Check for assignments setting unlock env vars to '1'
    for var in UNLOCK_ENV_VARS:
        pattern = rf'os\.environ\[["\']{var}["\']\]\s*=\s*["\']1["\']'
        if re.search(pattern, text) and path.name not in EXCLUDED_SCRIPTS:
            violations.append(f"Hardcoded unlock flag: {var} assigned in {path.relative_to(ROOT)}")

    # 2. Check for unguarded calls to load_modeling_data with split='test' and include_outcomes=True
    if "load_modeling_data" in text and path.name not in EXCLUDED_SCRIPTS:
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
                                f"Unguarded test split outcome load in {path.relative_to(ROOT)}: load_modeling_data(split='test', include_outcomes={inc_outcomes})"
                            )
        except Exception as e:
            violations.append(f"AST parse error in {path.relative_to(ROOT)}: {e}")

    # 3. Check for direct read_parquet of post_window_2026.parquet
    if "post_window_2026" in text and path.name not in EXCLUDED_SCRIPTS:
        if "read_parquet" in text:
            # Check if read_parquet is actually called on post_window
            pattern = r'read_parquet\([^)]*post_window_2026[^)]*\)'
            if re.search(pattern, text):
                violations.append(
                    f"Direct read_parquet of post_window_2026.parquet in {path.relative_to(ROOT)}"
                )

    return violations


def main():
    print("=================================================================")
    print("PHASE 0 (f): VERIFY NO UNGUARDED OUTCOME READS IN SCRIPTS & SRC")
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

    if all_violations:
        print("\nVIOLATIONS FOUND:")
        for viol in all_violations:
            print(f"  - [FAIL] {viol}")
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED: Zero unguarded outcome reads detected. Guard integrity intact.")


if __name__ == "__main__":
    main()
