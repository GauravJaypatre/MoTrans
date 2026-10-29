"""Phase D checks: shock series, grades, standardisation and known episodes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
SHOCKS = ROOT / "data" / "final" / "shocks.parquet"
pytestmark = pytest.mark.skipif(not SHOCKS.exists(), reason="run python tasks.py data first")


@pytest.fixture(scope="module")
def shocks() -> pd.DataFrame:
    return pd.read_parquet(SHOCKS)


def value(shocks, event_id):
    return shocks.loc[shocks.event_id == event_id, "shock_std"].iloc[0]


def test_one_row_per_decision(shocks):
    policy = pd.read_csv(ROOT / "data" / "final" / "policy_decisions.csv")
    assert len(shocks) == len(policy) and shocks.event_id.is_unique


def test_grades(shocks):
    assert set(shocks.shock_grade) <= {"A", "B", "C"}
    assert set(shocks.loc[shocks.shock_grade == "A", "regime"]) == {"Fed", "ECB"}
    assert shocks.loc[shocks.shock_grade == "C", "shock_std"].isna().all()
    assert shocks.loc[shocks.shock_grade != "C", "shock_std"].notna().all()


def test_training_period_sd_is_one(shocks):
    train = shocks[shocks.decision_date <= pd.Timestamp("2019-12-31").date()]
    for col in ("shock_hf_std", "shock_proxy_std"):
        sd = train.groupby("regime")[col].std().dropna()
        assert np.allclose(sd, 1.0)


def test_known_signs(shocks):
    assert value(shocks, "fed_2020-03-15") < -1 and value(shocks, "fed_2020-03-03") < -1
    assert value(shocks, "fed_2022-03-16") > 1 and value(shocks, "fed_2022-09-21") > 1
    assert value(shocks, "ecb_2022-07-21") > 1 and value(shocks, "ecb_2022-09-08") > 1


def test_hf_and_proxy_agree(shocks):
    for regime in ("Fed", "ECB"):
        g = shocks[(shocks.regime == regime) & shocks.shock_hf_std.notna() & shocks.shock_proxy_std.notna()]
        assert g.shock_hf_std.corr(g.shock_proxy_std) > 0.4


def test_events_carry_shocks(shocks):
    events = pd.read_parquet(ROOT / "data" / "final" / "events.parquet")
    merged = events[["event_id", "shock_std"]].drop_duplicates("event_id").merge(
        shocks[["event_id", "shock_std"]], on="event_id", suffixes=("", "_s"))
    assert np.allclose(merged.shock_std, merged.shock_std_s, equal_nan=True)
