"""Phase D / Analysis Preparation: build analysis-ready parquets for Tier 1 and Tier 2 Primary.

Derived strictly from frozen data (events.parquet and controls_long.parquet) with zero look-ahead:
  - data/final/analysis_tier1.parquet:
      One row per Tier 1 decision x reacting index (ECB and Fed consensus high-frequency surprises).
      Contains: shock_std, shock_std_w, shock_measure_type, split_tag, clr_1/3/5/20/60, home_market,
      overlap flags/counts, and macro/financial controls matched where available_from <= decision_date.
  - data/final/analysis_tier2_primary.parquet:
      One row per Tier 2 rate-change decision x reacting index with analysis_ready_timing == 1 and
      shock_primary == 1 (BoC, BoE, CBR, ECB, Fed, RBA).
"""

from __future__ import annotations

from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"

# Maximum age in days before carried-forward control value is treated as missing (no stale carry-forward)
MAX_AGE_DAYS = {
    "fx_lcu_per_usd": 7,
    "policy_rate": 7,
    "yield_1y": 7,
    "yield_2y": 7,
    "vix": 7,
    "cpi": 62,
    "ind_prod": 62,
}

ANALYSIS_COLS = [
    # Identifiers
    "event_id",
    "regime",
    "decision_date",
    "event_type",
    "scheduled",
    "decision",
    "size_bp",
    "new_rate_pct",
    # Index & Market
    "country",
    "index_id",
    "index_class",
    "home_market",
    # Timing & Event Windows
    "time_quality",
    "announce_ts_utc",
    "baseline_date",
    "reacting_session_date",
    "announce_in_session",
    "timing_ambiguous",
    "analysis_ready_timing",
    # Shocks
    "shock_std",
    "shock_std_w",
    "shock_measure_type",
    "shock_tier",
    "shock_grade",
    "shock_source",
    "shock_usable",
    "shock_primary",
    "shock_secondary",
    "shock_primary_rescaled",
    "shock_proxy_tenor",
    # Sample Split Tag
    "split_tag",
    # Event Window Cumulative Log Returns
    "clr_1",
    "clr_3",
    "clr_5",
    "clr_20",
    "clr_60",
    # Overlap Contamination Tracking
    "overlap_1d",
    "overlap_3d",
    "overlap_5d",
    "overlap_20d",
    "overlap_60d",
    "overlap_count_1d",
    "overlap_count_3d",
    "overlap_count_5d",
    "overlap_count_20d",
    "overlap_count_60d",
    # Merged Controls (available_from <= decision_date)
    "ctrl_cpi",
    "ctrl_ind_prod",
    "ctrl_policy_rate",
    "ctrl_fx_lcu_per_usd",
    "ctrl_yield_1y",
    "ctrl_yield_2y",
    "ctrl_yield_short",
    "ctrl_vix",
]


def attach_controls(df: pd.DataFrame, controls: pd.DataFrame) -> pd.DataFrame:
    """Attach local macro/financial controls and global VIX where available_from <= decision_date."""
    out = df.copy()
    out["_d"] = pd.to_datetime(out["decision_date"])
    out["_orig_idx"] = np.arange(len(out))

    # 1. Merge local country-level controls
    for var in ["cpi", "ind_prod", "policy_rate", "fx_lcu_per_usd", "yield_1y", "yield_2y"]:
        sub = controls[controls["variable"] == var][["country", "available_from", "value"]].copy()
        sub["available_from"] = pd.to_datetime(sub["available_from"])
        sub = sub.sort_values("available_from")

        merged = pd.merge_asof(
            out.sort_values("_d"),
            sub,
            left_on="_d",
            right_on="available_from",
            by="country",
            direction="backward",
            tolerance=pd.Timedelta(days=MAX_AGE_DAYS[var]),
        )
        out[f"ctrl_{var}"] = merged.sort_values("_orig_idx")["value"].to_numpy()

    # US local currency per USD is identically 1.0
    out.loc[out["country"] == "US", "ctrl_fx_lcu_per_usd"] = 1.0

    # Composite short sovereign yield (1Y where available, 2Y fallback where 1Y unavailable)
    out["ctrl_yield_short"] = out["ctrl_yield_1y"].fillna(out["ctrl_yield_2y"])

    # 2. Merge global risk control (CBOE VIX, US series)
    vix = controls[controls["variable"] == "vix"][["available_from", "value"]].copy()
    vix["available_from"] = pd.to_datetime(vix["available_from"])
    vix = vix.sort_values("available_from")

    merged_vix = pd.merge_asof(
        out.sort_values("_d"),
        vix,
        left_on="_d",
        right_on="available_from",
        direction="backward",
        tolerance=pd.Timedelta(days=MAX_AGE_DAYS["vix"]),
    )
    out["ctrl_vix"] = merged_vix.sort_values("_orig_idx")["value"].to_numpy()

    out = out.drop(columns=["_d", "_orig_idx"])
    return out[ANALYSIS_COLS]


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    events = pd.read_parquet(FINAL / "events.parquet")
    controls = pd.read_parquet(INTERIM / "controls_long.parquet")

    # 1. Tier 1: All Tier 1 decisions x index (ECB and Fed consensus high-frequency shocks)
    t1_events = events[events["shock_tier"] == 1].copy()
    tier1 = attach_controls(t1_events, controls)
    tier1 = tier1.sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    tier1.to_parquet(FINAL / "analysis_tier1.parquet", index=False)

    # 2. Tier 2 Primary: Tier 2 rate-change decisions x index with analysis_ready_timing == 1 and shock_primary == 1
    t2_events = events[
        (events["shock_tier"] == 2)
        & (events["decision"].isin(["hike", "cut"]))
        & (events["analysis_ready_timing"] == 1)
        & (events["shock_primary"] == 1)
    ].copy()
    tier2 = attach_controls(t2_events, controls)
    tier2 = tier2.sort_values(["regime", "decision_date", "index_id"]).reset_index(drop=True)
    tier2.to_parquet(FINAL / "analysis_tier2_primary.parquet", index=False)

    return tier1, tier2


def main() -> None:
    t1, t2 = build()
    print("=" * 60)
    print(f"Built data/final/analysis_tier1.parquet: {len(t1):,} rows")
    print("Tier 1 Row Counts by Regime:")
    print(t1["regime"].value_counts().to_string())
    print("\nTier 1 Row Counts by Split:")
    print(t1["split_tag"].value_counts().to_string())
    print("\nTier 1 Decisions by Regime x Split:")
    print(t1.groupby(["regime", "split_tag"])["decision_date"].nunique().unstack(fill_value=0).to_string())

    print("=" * 60)
    print(f"Built data/final/analysis_tier2_primary.parquet: {len(t2):,} rows")
    print("Tier 2 Primary Row Counts by Regime:")
    print(t2["regime"].value_counts().to_string())
    print("\nTier 2 Primary Row Counts by Split:")
    print(t2["split_tag"].value_counts().to_string())
    print("\nTier 2 Primary Decisions by Regime x Split:")
    print(t2.groupby(["regime", "split_tag"])["decision_date"].nunique().unstack(fill_value=0).to_string())
    print("=" * 60)


if __name__ == "__main__":
    main()
