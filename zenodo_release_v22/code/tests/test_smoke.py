"""Smoke tests — verify basic project setup and conventions."""

from __future__ import annotations

import datetime

import src
from src import download, split_tag


class TestSplitTagBoundaries:
    """Verify the sample-split boundaries defined in PROJECT_SPEC.md."""

    def test_train_end(self):
        assert split_tag(datetime.date(2019, 12, 31)) == "train"

    def test_crisis_start(self):
        assert split_tag(datetime.date(2020, 1, 1)) == "crisis"

    def test_crisis_end(self):
        assert split_tag(datetime.date(2021, 12, 31)) == "crisis"

    def test_blind_test_start(self):
        assert split_tag(datetime.date(2022, 1, 1)) == "blind_test"

    def test_deep_history_is_train(self):
        assert split_tag(datetime.date(2000, 1, 1)) == "train"

    def test_recent_date_is_blind_test(self):
        assert split_tag(datetime.date(2026, 10, 12)) == "blind_test"


class TestModuleImports:
    """Verify that core modules are importable."""

    def test_src_package_importable(self):
        assert hasattr(src, "split_tag")

    def test_download_module_importable(self):
        assert hasattr(download, "save_raw_file")
        assert hasattr(download, "MANIFEST_PATH")
