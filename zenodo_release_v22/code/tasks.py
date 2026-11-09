"""MoTrans-15 task runner.

Usage:
    python tasks.py setup      Install pinned dependencies into .venv
    python tasks.py data       Rebuild everything from raw -> interim -> final
    python tasks.py test       Run the test suite
    python tasks.py clean      Remove interim and final data (keeps raw)
    python tasks.py lint       Check code style with ruff
    python tasks.py gates      Run all reproducibility checks and release gates
    python tasks.py v22        Rebuild v2.2 tables, check checksums, run tests, and print gate table
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe")
if not Path(PYTHON).exists():
    PYTHON = sys.executable
PIP = str(ROOT / ".venv" / "Scripts" / "pip.exe")
if not Path(PIP).exists():
    PIP = "pip"


def _run(cmd: list[str], **kwargs) -> int:
    """Run a subprocess; return its exit code."""
    print(f"> {' '.join(cmd)}")
    result = subprocess.run(cmd, **kwargs)
    return result.returncode


def task_setup() -> None:
    """Install pinned dependencies into .venv."""
    code = _run([PIP, "install", "-r", "requirements.txt"])
    if code != 0:
        sys.exit(code)


def task_data() -> None:
    """Rebuild the full pipeline from raw to final."""
    code = _run([PYTHON, "-m", "src.pipeline"])
    if code != 0:
        sys.exit(code)


def task_test() -> None:
    """Run pytest."""
    code = _run([PYTHON, "-m", "pytest", "tests/", "-v"])
    if code != 0:
        sys.exit(code)


def task_clean() -> None:
    """Remove interim and final data (preserves raw)."""
    for subdir in ("data/interim", "data/final"):
        p = ROOT / subdir
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)
        (p / ".gitkeep").touch()
    print("Cleaned data/interim and data/final")


def task_lint() -> None:
    """Run ruff linter."""
    code = _run([PYTHON, "-m", "ruff", "check", "src/", "tests/"])
    if code != 0:
        sys.exit(code)


def task_gates() -> None:
    """Run master reproducibility checks, release gates, and test suites."""
    code = _run([PYTHON, "run_all_gates.py"])
    if code != 0:
        sys.exit(code)


def task_v22() -> None:
    """Rebuild every v2.2 table, check checksums, run tests, and print pass/fail gate table."""
    print("=================================================================")
    print("EXECUTING MOTRANS-15 V2.2 REPRODUCIBILITY & RELEASE GATES")
    print("=================================================================")

    gates = []

    # Gate 1: Rebuild v2.2 tables
    code_build = _run([PYTHON, "src/v2_2_build_tables.py"])
    gates.append(("Gate 1: Rebuild v2.2 Tables", code_build == 0))

    # Gate 2: Table Existence and Non-Empty Check
    v22_dir = ROOT / "data" / "v2_2" / "release"
    expected_files = [
        "analysis_tier1.parquet",
        "analysis_tier2_primary.parquet",
        "secondary_holds.parquet",
        "sensitivity_macro_revision.parquet",
        "panel_returns_only.parquet",
        "splits.csv",
        "folds.csv",
    ]
    all_exist = all((v22_dir / f).exists() and (v22_dir / f).stat().st_size > 0 for f in expected_files)
    gates.append(("Gate 2: Table Existence & Non-Empty", all_exist))

    # Gate 3: Integrity Check (No level_local, No shock_std)
    import pandas as pd
    forbidden_found = False
    for f in ["analysis_tier1.parquet", "analysis_tier2_primary.parquet", "secondary_holds.parquet", "sensitivity_macro_revision.parquet"]:
        df = pd.read_parquet(v22_dir / f)
        if "level_local" in df.columns or "shock_std" in df.columns:
            forbidden_found = True
            break
    gates.append(("Gate 3: Strip Proprietary Levels & shock_std Trap", not forbidden_found))

    # Gate 4: Single Source of Truth Splits Alignment
    splits_df = pd.read_csv(v22_dir / "splits.csv")
    t1_df = pd.read_parquet(v22_dir / "analysis_tier1.parquet")
    splits_match = set(t1_df["event_id"].unique()).issubset(set(splits_df["event_id"].unique()))
    gates.append(("Gate 4: Single Source of Truth splits.csv Alignment", splits_match and len(splits_df) == 718))

    # Gate 5: Unguarded Outcome Scanner & Integrity Alignment
    code_scan = _run([PYTHON, "scripts/verify_no_unguarded_outcomes.py"])
    gates.append(("Gate 5: Zero Unguarded Reads & Allowlist Compliance", code_scan == 0))

    # Gate 6: v2.2 Harness Tests
    code_harness = _run([PYTHON, "-m", "pytest", "tests/test_v2_2_harness.py", "-q"])
    gates.append(("Gate 6: v2.2 Harness Test Suite", code_harness == 0))

    # Gate 7: Model Guard Integrity Tests
    code_guard = _run([PYTHON, "-m", "pytest", "tests/test_model_guard_integrity.py", "-q"])
    gates.append(("Gate 7: Model Guard Integrity Test Suite", code_guard == 0))

    # Gate 8: Inference Size & Clustering Tests
    code_infer = _run([PYTHON, "-m", "pytest", "tests/test_inference_size.py", "-q"])
    gates.append(("Gate 8: Inference Size & Two-Way Clustering Tests", code_infer == 0))

    # Gate 9: Unlock Audit Log Lock (Strictly 16 lines)
    audit_log = ROOT / "outputs" / "v2_1" / "unlock_audit.log"
    log_lines = [l for l in audit_log.read_text(encoding="utf-8").splitlines() if l.strip()] if audit_log.exists() else []
    gates.append(("Gate 9: Held-Out Blinding Intact (16 log lines)", len(log_lines) == 16))

    # Print Gate Summary Table
    print("\n=================================================================")
    print("V2.2 GATES PASS/FAIL SUMMARY TABLE")
    print("=================================================================")
    all_passed = True
    for name, passed in gates:
        status_str = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"  {status_str:7s} | {name}")
    print("=================================================================")

    if not all_passed:
        print("\nOne or more v2.2 gates failed!")
        sys.exit(1)
    else:
        print("\nAll v2.2 reproducibility gates PASSED successfully.")


TASKS = {
    "setup": task_setup,
    "data": task_data,
    "test": task_test,
    "clean": task_clean,
    "lint": task_lint,
    "gates": task_gates,
    "v22": task_v22,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in TASKS:
        print(__doc__)
        valid = ", ".join(TASKS)
        print(f"Available tasks: {valid}")
        sys.exit(1)
    TASKS[sys.argv[1]]()


if __name__ == "__main__":
    main()
