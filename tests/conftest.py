"""Pytest configuration and global fixtures for MoTrans-15 repository tests."""

from __future__ import annotations

import os
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def redirect_audit_log(tmp_path, monkeypatch):
    """Ensure that running tests never modifies production unlock audit logs."""
    test_log = tmp_path / "test_unlock_audit.log"
    monkeypatch.setenv("MOTRANS_AUDIT_LOG", str(test_log))
