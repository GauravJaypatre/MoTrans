"""Test suite to ensure docs/PROJECT_SUMMARY.md and zenodo_release/README.md

strictly match outputs/v2_1/split_counts.csv and row_membership.csv with zero drift.
"""

from __future__ import annotations

import re
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS_SUMMARY = ROOT / "docs" / "PROJECT_SUMMARY.md"
ZENODO_README = ROOT / "zenodo_release" / "README.md"
OUTPUTS = ROOT / "outputs" / "v2_1"


@pytest.fixture(scope="module")
def project_summary_text():
    assert DOCS_SUMMARY.exists(), f"Missing {DOCS_SUMMARY}"
    return DOCS_SUMMARY.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def zenodo_readme_text():
    assert ZENODO_README.exists(), f"Missing {ZENODO_README}"
    return ZENODO_README.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def csv_data():
    df_split = pd.read_csv(OUTPUTS / "split_counts.csv")
    df_row = pd.read_csv(OUTPUTS / "row_membership.csv")
    return df_split, df_row


def test_split_counts_exact_match(csv_data, project_summary_text, zenodo_readme_text):
    df_split, _ = csv_data
    g = df_split.groupby("split")[["decisions_count", "hikes_count", "cuts_count", "holds_count", "event_rows_count"]].sum()

    train = g.loc["train"]
    val = g.loc["validation"]
    test = g.loc["test"]
    tot = g.sum()

    assert train["hikes_count"] == 35
    assert train["cuts_count"] == 63
    assert train["holds_count"] == 474
    assert train["decisions_count"] == 572
    assert train["event_rows_count"] == 21247

    assert val["hikes_count"] == 57
    assert val["cuts_count"] == 0
    assert val["holds_count"] == 19
    assert val["decisions_count"] == 76
    assert val["event_rows_count"] == 2818

    assert test["hikes_count"] == 0
    assert test["cuts_count"] == 28
    assert test["holds_count"] == 42
    assert test["decisions_count"] == 70
    assert test["event_rows_count"] == 2590

    assert tot["hikes_count"] == 92
    assert tot["cuts_count"] == 91
    assert tot["holds_count"] == 535
    assert tot["decisions_count"] == 718
    assert tot["event_rows_count"] == 26655

    for doc_text, doc_name in [(project_summary_text, "docs/PROJECT_SUMMARY.md"), (zenodo_readme_text, "zenodo_release/README.md")]:
        assert f"| `train` | 2010-01-01 to 2021-12-31 | {train['decisions_count']} | {train['hikes_count']} | {train['cuts_count']} | {train['holds_count']} | {train['event_rows_count']:,} |" in doc_text, f"Mismatch in {doc_name} train row"
        assert f"| `validation` | 2022-01-01 to 2023-12-31 | {val['decisions_count']} | {val['hikes_count']} | {val['cuts_count']} | {val['holds_count']} | {val['event_rows_count']:,} |" in doc_text, f"Mismatch in {doc_name} val row"
        assert f"| `test` | 2024-01-01 to 2025-12-31 | {test['decisions_count']} | {test['hikes_count']} | {test['cuts_count']} | {test['holds_count']} | {test['event_rows_count']:,} |" in doc_text, f"Mismatch in {doc_name} test row"
        assert f"| **Total** | **2010-01-01 to 2025-12-31** | **{tot['decisions_count']}** | **{tot['hikes_count']}** | **{tot['cuts_count']}** | **{tot['holds_count']}** | **{tot['event_rows_count']:,}** |" in doc_text, f"Mismatch in {doc_name} total row"


def test_row_membership_and_tier_counts(csv_data, project_summary_text, zenodo_readme_text):
    _, df_row = csv_data

    t1 = df_row[df_row["membership_category"] == "tier1"].iloc[0]
    t2 = df_row[df_row["membership_category"] == "tier2_primary"].iloc[0]
    sh = df_row[df_row["membership_category"] == "secondary_holds"].iloc[0]

    assert t1["decisions_count"] == 253
    assert t1["event_rows_count"] == 9350
    assert t2["decisions_count"] == 130
    assert t2["event_rows_count"] == 4851
    assert sh["decisions_count"] == 335
    assert sh["event_rows_count"] == 12454

    sens_decs = t1["decisions_count"] + t2["decisions_count"]
    sens_rows = t1["event_rows_count"] + t2["event_rows_count"]
    assert sens_decs == 383
    assert sens_rows == 14201

    # Check sensitivity table has 383 decisions and 14,201 rows
    assert "383" in project_summary_text
    assert "14,201" in project_summary_text
    assert "383" in zenodo_readme_text
    assert "14,201" in zenodo_readme_text

    # Legacy typo 382 must not appear in relation to sensitivity decisions
    assert "382 decisions" not in project_summary_text
    assert "| 382 | 14,201 |" not in zenodo_readme_text


def test_required_phrasings(project_summary_text, zenodo_readme_text):
    # Easing wording
    assert "an easing cycle among the included central banks (the Bank of Japan hiked in the same period)" in project_summary_text
    assert "an easing cycle among the included central banks (the Bank of Japan hiked in the same period)" in zenodo_readme_text

    # BoJ reason in PROJECT_SUMMARY
    assert "zero/negative-rate regime and absence of an intraday shock series" in project_summary_text

    # Emerging markets reason
    assert "announcement times were not verified in this version" in project_summary_text
    assert "announcement times were not verified in this version" in zenodo_readme_text

    # Unlock guard wording
    assert "raises an error AND logs" in project_summary_text
    assert "raises an error AND logs" in zenodo_readme_text

    # Fold standardization instruction
    assert "standardize `shock_raw_bp` strictly fold-by-fold" in project_summary_text
    assert "standardize `shock_raw_bp` strictly fold-by-fold" in zenodo_readme_text

