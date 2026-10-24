"""MoTrans-15 task runner.

Usage:
    python tasks.py setup      Install pinned dependencies into .venv
    python tasks.py data       Rebuild everything from raw → interim → final
    python tasks.py test       Run the test suite
    python tasks.py clean      Remove interim and final data (keeps raw)
    python tasks.py lint       Check code style with ruff
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe")
PIP = str(ROOT / ".venv" / "Scripts" / "pip.exe")


def _run(cmd: list[str], **kwargs) -> None:
    """Run a subprocess; exit with its return code on failure."""
    print(f"> {' '.join(cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        sys.exit(result.returncode)


def task_setup() -> None:
    """Install pinned dependencies into .venv."""
    _run([PIP, "install", "-r", "requirements.txt"])


def task_data() -> None:
    """Rebuild the full pipeline from raw to final."""
    _run([PYTHON, "-m", "src.pipeline"])


def task_test() -> None:
    """Run pytest."""
    _run([PYTHON, "-m", "pytest", "tests/", "-v"])


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
    _run([PYTHON, "-m", "ruff", "check", "src/", "tests/"])


TASKS = {
    "setup": task_setup,
    "data": task_data,
    "test": task_test,
    "clean": task_clean,
    "lint": task_lint,
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
