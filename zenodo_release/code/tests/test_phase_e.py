"""Phase E checks: statement corpus alignment, text quality and the hand-label sample."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
STATEMENTS = ROOT / "data" / "final" / "statements.parquet"
SAMPLE = ROOT / "docs" / "hand_label_sample.csv"
LABELS = ["hawkish_dovish", "inflation_concern", "growth_concern", "uncertainty", "forward_guidance_shift"]
pytestmark = pytest.mark.skipif(not STATEMENTS.exists(), reason="run src.collect_statements first")


@pytest.fixture(scope="module")
def statements() -> pd.DataFrame:
    return pd.read_parquet(STATEMENTS)


def test_every_statement_is_a_decision(statements):
    policy = pd.read_csv(ROOT / "data" / "final" / "policy_decisions.csv", dtype={"decision_date": str})
    ids = set(policy.regime.str.lower() + "_" + policy.decision_date)
    assert set(statements.event_id) <= ids and statements.event_id.is_unique


def test_regimes_and_language(statements):
    assert set(statements.regime) == {"Fed", "ECB", "BoJ", "RBI"}
    assert (statements.language == "en").all()


def test_texts_look_like_statements(statements):
    assert statements.word_count.min() >= 40
    keywords = statements.text.str.contains(r"inflation|interest rate|policy|price", case=False)
    assert keywords.mean() > 0.95


def test_coverage_is_substantial(statements):
    # Fed/ECB/BoJ are near-complete; RBI has statements for 90 of its 140 archive dates (ISS-027).
    per = statements.groupby("regime").size()
    assert (per >= 80).all() and per.drop("RBI").min() >= 200


def test_provenance(statements):
    assert statements.source_url.str.startswith("http").all()
    assert (statements.retrieval_utc != "").mean() > 0.99


def test_hand_label_sample_is_unlabelled():
    sample = pd.read_csv(SAMPLE)
    assert 150 <= len(sample) <= 200
    assert sample[LABELS].isna().all().all()  # labels are for the Text lead, never filled by code
    assert sample.groupby("regime").size().min() >= 10
