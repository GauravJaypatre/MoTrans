"""Unit and regression tests verifying docs/PROJECT_SUMMARY.md against committed CSVs.

Fails if any quantitative figure in docs/PROJECT_SUMMARY.md differs from
the source CSV reports:
  - outputs/v2_1/split_counts.csv
  - outputs/v2_1/fold_counts.csv
  - outputs/v2_1/row_membership.csv
  - outputs/v2_1/test_window_composition.csv
"""

from __future__ import annotations

import re
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUTPUTS = ROOT / "outputs" / "v2_1"
SUMMARY_FILE = DOCS / "PROJECT_SUMMARY.md"

@pytest.fixture(scope="module")
def summary_text():
    assert SUMMARY_FILE.exists(), f"Missing file: {SUMMARY_FILE}"
    text = SUMMARY_FILE.read_text(encoding="utf-8")
    assert text.strip(), "PROJECT_SUMMARY.md is empty!"
    return text

def test_summary_exists(summary_text):
    assert len(summary_text) > 500

def test_tier_counts_match_row_membership_csv(summary_text):
    """Requirement 1: Tier 1 = 253 decs / 9,350 rows; Tier 2 = 130 / 4,851; Secondary holds = 335 / 12,454."""
    df_row = pd.read_csv(OUTPUTS / "row_membership.csv")
    
    t1 = df_row[df_row["membership_category"] == "tier1"].iloc[0]
    t2 = df_row[df_row["membership_category"] == "tier2_primary"].iloc[0]
    sh = df_row[df_row["membership_category"] == "secondary_holds"].iloc[0]
    boj = df_row[df_row["membership_category"] == "usable_not_in_any_table"].iloc[0]

    # Verify exact CSV baseline figures
    assert t1["decisions_count"] == 253
    assert t1["event_rows_count"] == 9350
    assert t2["decisions_count"] == 130
    assert t2["event_rows_count"] == 4851
    assert sh["decisions_count"] == 335
    assert sh["event_rows_count"] == 12454
    assert boj["decisions_count"] == 162
    assert boj["event_rows_count"] == 5924

    # Check presence in PROJECT_SUMMARY.md
    assert f"**{t1['decisions_count']}** decisions" in summary_text
    assert f"**{t1['event_rows_count']:,}** event rows" in summary_text

    assert f"**{t2['decisions_count']}** decisions" in summary_text
    assert f"**{t2['event_rows_count']:,}** event rows" in summary_text

    assert f"**{sh['decisions_count']}** decisions" in summary_text
    assert f"**{sh['event_rows_count']:,}** event rows" in summary_text

    assert f"**{boj['decisions_count']} clean, usable decisions ({boj['event_rows_count']:,} event rows)**" in summary_text

def test_split_counts_match_split_counts_csv(summary_text):
    """Requirement 2: split table computed from split_counts.csv:

    train 21,247 rows, validation 2,818, test 2,590, total 26,655.
    """
    df_split = pd.read_csv(OUTPUTS / "split_counts.csv")
    g = df_split.groupby("split")[["decisions_count", "hikes_count", "cuts_count", "holds_count", "event_rows_count"]].sum()

    train_s = g.loc["train"]
    val_s = g.loc["validation"]
    test_s = g.loc["test"]
    tot_s = g.sum()

    # Exact figures check from CSV
    assert train_s["event_rows_count"] == 21247
    assert val_s["event_rows_count"] == 2818
    assert test_s["event_rows_count"] == 2590
    assert tot_s["event_rows_count"] == 26655

    # Check table rows in summary
    train_pattern = (
        rf"\| `train` \| 2010-01-01 to 2021-12-31 \| {train_s['decisions_count']} \| "
        rf"{train_s['hikes_count']} \| {train_s['cuts_count']} \| {train_s['holds_count']} \| "
        rf"{train_s['event_rows_count']:,} \|"
    )
    val_pattern = (
        rf"\| `validation` \| 2022-01-01 to 2023-12-31 \| {val_s['decisions_count']} \| "
        rf"{val_s['hikes_count']} \| {val_s['cuts_count']} \| {val_s['holds_count']} \| "
        rf"{val_s['event_rows_count']:,} \|"
    )
    test_pattern = (
        rf"\| `test` \| 2024-01-01 to 2025-12-31 \| {test_s['decisions_count']} \| "
        rf"{test_s['hikes_count']} \| {test_s['cuts_count']} \| {test_s['holds_count']} \| "
        rf"{test_s['event_rows_count']:,} \|"
    )
    tot_pattern = (
        rf"\| \*\*Total\*\* \| \*\*2010-01-01 to 2025-12-31\*\* \| \*\*{tot_s['decisions_count']}\*\* \| "
        rf"\*\*{tot_s['hikes_count']}\*\* \| \*\*{tot_s['cuts_count']}\*\* \| \*\*{tot_s['holds_count']}\*\* \| "
        rf"\*\*{tot_s['event_rows_count']:,}\*\* \|"
    )

    assert re.search(train_pattern, summary_text), "train split row mismatch in PROJECT_SUMMARY.md!"
    assert re.search(val_pattern, summary_text), "validation split row mismatch in PROJECT_SUMMARY.md!"
    assert re.search(test_pattern, summary_text), "test split row mismatch in PROJECT_SUMMARY.md!"
    assert re.search(tot_pattern, summary_text), "total split row mismatch in PROJECT_SUMMARY.md!"

def test_fold_counts_match_fold_counts_csv(summary_text):
    """Verify rolling-origin cross-validation fold counts."""
    df_fold = pd.read_csv(OUTPUTS / "fold_counts.csv")
    g = df_fold.groupby(["fold_id", "role"])[["decisions_count", "event_rows_count"]].sum()

    for fold_id in [1, 2, 3, 4]:
        train_decs = g.loc[(fold_id, "train"), "decisions_count"]
        val_decs = g.loc[(fold_id, "val"), "decisions_count"]
        train_rows = g.loc[(fold_id, "train"), "event_rows_count"]
        val_rows = g.loc[(fold_id, "val"), "event_rows_count"]

        assert str(train_decs) in summary_text
        assert str(val_decs) in summary_text
        assert f"{train_rows:,}" in summary_text
        assert f"{val_rows:,}" in summary_text

def test_all_row_membership_entries_match_csv(summary_text):
    """Verify all 11 categories in row_membership.csv appear with exact numbers."""
    df_row = pd.read_csv(OUTPUTS / "row_membership.csv")
    for _, r in df_row.iterrows():
        decs_str = f"{int(r['decisions_count']):,}"
        rows_str = f"{int(r['event_rows_count']):,}"
        share_str = str(r["share_of_total_rows"])
        
        # Check that table contains the exact line
        row_regex = rf"\| `{r['membership_category']}` \| `{r['reason_or_table']}` \| .* \| {decs_str} \| {rows_str} \| {share_str} \|"
        assert re.search(row_regex, summary_text), f"Missing or mismatched row in membership table for {r['reason_or_table']}"

def test_required_phrasings_and_disclosures(summary_text):
    # Requirement 3: state that Tier 1 covers Fed to Dec 2023 and ECB to Oct 2025
    assert "Covers Fed to Dec 2023 and ECB to Oct 2025" in summary_text or "covers Fed to Dec 2023 and ECB to Oct 2025" in summary_text

    # Requirement 4: replace 'tags are permanent and immutable' with accurate description of history rewrite and commit table
    assert "tags are permanent and immutable" not in summary_text
    assert "git-filter-repo" in summary_text
    assert "Pre-Rewrite Commit Hash" in summary_text
    assert "2f83d70f97bf134e5e75cb0055478208047814ed" in summary_text
    assert "f30ab1838c0820fa41f134c91cc058066c48cfdf" in summary_text

    # Requirement 5: correct BoJ description and file names
    assert "162 clean, usable decisions (5,924 event rows)" in summary_text
    assert "data/v2_1/release/analysis_tier1.parquet" in summary_text
    assert "data/v2_1/panel.parquet" in summary_text

    # Requirement 6: remove 'ready for deposit' until open items closed, and list them
    assert "ready for deposit" not in summary_text.lower()
    assert "Status at packaging, 2026-10-31" in summary_text
    assert "Licence Review by Supervisor / Library" in summary_text
    assert "Vendor Redistribution Clearance" in summary_text
    assert "NOT ready to publish" in summary_text

    # Requirement 7: remove stale statements on publication
    assert "were pushed" not in summary_text
    assert "DOI assignment" not in summary_text
    assert "repo set to private" not in summary_text.lower()

