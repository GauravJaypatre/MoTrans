"""Regression tests verifying zenodo_release/data/*.parquet directly against certified counts.

This test loads parquet files directly from zenodo_release/data/ (never CSVs)
and verifies that decision counts, row counts, and split distributions
match the certified project summary and freeze specifications.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
ZENODO_DATA = ROOT / "zenodo_release" / "data"
RELEASE_DATA = ROOT / "data" / "v2_1" / "release"

CERTIFIED_HASHES = {
    "analysis_tier1.parquet": "8a6207dd0c753c7d24d0a4d091dbdb05ee38d3010913a85b4c9f87a86e44979e",
    "analysis_tier2_primary.parquet": "c319040f687fbd88be9268d881c71152d803a0bd20357a109da049415f010a14",
    "secondary_holds.parquet": "7235bae5b29d0e4261bc9349e32593b09f9d0bf7cd784a7f61a56a45dc9c846f",
    "sensitivity_macro_revision.parquet": "f689bc78820520f08020d4d613fb6129a07abe15842634e2c9b428bd0f5bf794",
    "panel_returns_only.parquet": "e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620",
}

needs_zenodo_data = pytest.mark.skipif(
    not (ZENODO_DATA / "analysis_tier1.parquet").exists(),
    reason="zenodo_release/data/ not assembled",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@needs_zenodo_data
def test_zenodo_parquet_hashes_match_freeze():
    """Verify zenodo_release/data/*.parquet match certified DATA_FREEZE_v2_1.md hashes."""
    for filename, expected_hash in CERTIFIED_HASHES.items():
        p = ZENODO_DATA / filename
        assert p.exists(), f"Missing file: {p}"
        assert sha256_file(p) == expected_hash, f"Hash mismatch for {filename}"


@needs_zenodo_data
def test_zenodo_parquet_tier1_counts_and_splits():
    """Verify analysis_tier1.parquet has exactly 253 decisions, 9,350 rows, and certified splits."""
    df = pd.read_parquet(ZENODO_DATA / "analysis_tier1.parquet")
    assert df["event_id"].nunique() == 253
    assert len(df) == 9350

    splits = (
        df.drop_duplicates("event_id")
        .groupby("final_split")["decision"]
        .value_counts()
        .to_dict()
    )
    expected = {
        ("train", "hold"): 187,
        ("train", "cut"): 13,
        ("train", "hike"): 11,
        ("validation", "hike"): 21,
        ("validation", "hold"): 7,
        ("test", "cut"): 8,
        ("test", "hold"): 6,
    }
    assert splits == expected


@needs_zenodo_data
def test_zenodo_parquet_tier2_primary_counts_and_splits():
    """Verify analysis_tier2_primary.parquet has exactly 130 decisions, 4,851 rows, and certified splits."""
    df = pd.read_parquet(ZENODO_DATA / "analysis_tier2_primary.parquet")
    assert df["event_id"].nunique() == 130
    assert len(df) == 4851

    splits = (
        df.drop_duplicates("event_id")
        .groupby("final_split")["decision"]
        .value_counts()
        .to_dict()
    )
    expected = {
        ("train", "cut"): 50,
        ("train", "hike"): 24,
        ("validation", "hike"): 36,
        ("test", "cut"): 20,
    }
    assert splits == expected


@needs_zenodo_data
def test_zenodo_parquet_secondary_holds_counts_and_splits():
    """Verify secondary_holds.parquet has exactly 335 decisions, 12,454 rows, and certified splits."""
    df = pd.read_parquet(ZENODO_DATA / "secondary_holds.parquet")
    assert df["event_id"].nunique() == 335
    assert len(df) == 12454

    splits = (
        df.drop_duplicates("event_id")
        .groupby("final_split")["decision"]
        .value_counts()
        .to_dict()
    )
    expected = {
        ("train", "hold"): 287,
        ("validation", "hold"): 12,
        ("test", "hold"): 36,
    }
    assert splits == expected
