"""Phase C checks: full panel, controls without look-ahead, 12-regime decisions, events.

Skipped on a fresh clone until `python tasks.py data` has built data/final/.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"
built = pytest.mark.skipif(not (FINAL / "events.parquet").exists(), reason="run python tasks.py data first")
COUNTRIES = {"US", "CN", "DE", "IN", "JP", "GB", "FR", "IT", "RU", "CA", "BR", "ES", "MX", "AU", "KR"}


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_parquet(FINAL / "panel_daily.parquet")


@pytest.fixture(scope="module")
def controls() -> pd.DataFrame:
    return pd.read_parquet(INTERIM / "controls_long.parquet")


@pytest.fixture(scope="module")
def policy() -> pd.DataFrame:
    return pd.read_csv(FINAL / "policy_decisions.csv", dtype={"decision_date": str})


@pytest.fixture(scope="module")
def events() -> pd.DataFrame:
    return pd.read_parquet(FINAL / "events.parquet")


@built
class TestPanel:
    def test_all_fifteen_countries(self, panel):
        assert COUNTRIES <= set(panel.country)

    def test_three_series_where_available(self, panel):
        per = panel.groupby("country").index_id.nunique()
        # GB and MX miss free bank / small-cap series; FR/IT/ES share euro-area ETFs (EA).
        assert per.drop(["GB", "MX", "FR", "IT", "ES", "EA", "DE"]).min() >= 3

    def test_unique_rows(self, panel):
        assert not panel.duplicated(["index_id", "date"]).any()

    def test_us_returns_are_already_usd(self, panel):
        us = panel[(panel.country == "US") & panel.ret_usd.notna()]
        assert np.allclose(us.ret_usd, us.ret_local)

    def test_usd_return_identity(self, panel):
        jp = panel[(panel.index_id == "jp_nikkei225") & panel.level_local.notna()].sort_values("date")
        fx_change = np.log(jp.fx_lcu_per_usd / jp.fx_lcu_per_usd.shift(1))
        ok = jp.ret_usd.notna()
        assert np.allclose(jp.ret_usd[ok], (jp.ret_local - fx_change)[ok])

    def test_halt_rows_only_russia_2022(self, panel):
        halts = panel[panel.halt_flag == 1]
        assert set(halts.country) == {"RU"}
        assert halts.date.min() >= dt.date(2022, 2, 24) and halts.date.max() <= dt.date(2022, 3, 31)
        assert halts.level_local.isna().all()

    def test_russia_flag(self, panel):
        ru = panel[panel.country == "RU"]
        assert (ru.russia_post_feb2022 == (ru.date >= dt.date(2022, 2, 24)).astype(int)).all()
        assert panel.loc[panel.country != "RU", "russia_post_feb2022"].eq(0).all()

    def test_split_tags(self, panel):
        assert set(panel.split_tag) == {"train", "crisis", "blind_test"}


@built
class TestNoLookAhead:
    @pytest.mark.parametrize("var", ["cpi", "ind_prod", "yield_1y"])
    def test_value_is_latest_available(self, panel, controls, var):
        c = controls[controls.variable == var]
        sample = panel[panel[var].notna()].sample(300, random_state=1)
        for r in sample.itertuples():
            avail = c[(c.country == r.country) & (c.available_from <= r.date)]
            expected = avail.sort_values("available_from").value.iloc[-1]
            assert np.isclose(getattr(r, var), expected)

    def test_monthly_lag_is_two_months(self, controls):
        cpi = controls[controls.variable == "cpi"]
        lag = (pd.to_datetime(cpi.available_from) - pd.to_datetime(cpi.date)).dt.days
        assert lag.between(59, 62).all()


@built
class TestDecisions:
    def test_twelve_regimes(self, policy):
        assert set(policy.regime) == {"Fed", "ECB", "RBI", "BoJ", "BoE", "PBoC", "CBR", "BoC", "BCB",
                                      "Banxico", "RBA", "BoK"}

    def test_windows_everywhere(self, policy):
        assert policy.window_start_utc.notna().all() and (policy.window_start_utc <= policy.window_end_utc).all()

    def test_holds_for_regimes_with_meeting_lists(self, policy):
        holds = policy[policy.decision == "hold"].groupby("regime").size()
        assert holds.reindex(["Fed", "ECB", "RBI", "BoJ", "BCB", "Banxico"]).gt(10).all()

    def test_brazil_known_cycle(self, policy):
        # Copom raised the Selic at its 16 Mar 2022 meeting (BIS rate 10.75 -> 11.75).
        e = policy[(policy.regime == "BCB") & (policy.decision_date == "2022-03-16")].iloc[0]
        assert (e.decision, e.size_bp) == ("hike", 100)


@built
class TestEvents:
    def test_home_markets(self, events):
        home = events[events.home_market == 1].groupby("regime").country.agg(set).to_dict()
        assert home["ECB"] == {"DE", "FR", "IT", "ES", "EA"} and home["Fed"] == {"US"} and home["BCB"] == {"BR"}

    def test_baseline_before_reaction(self, events):
        assert (events.baseline_obs_date < events.react_obs_date).all()

    def test_every_regime_has_events(self, events):
        assert events.regime.nunique() == 12
