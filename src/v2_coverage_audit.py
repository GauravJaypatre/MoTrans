"""Phase V0 Coverage Audit for MoTrans-15 v2.0 (2010-to-latest).

Produces:
- outputs/v2/coverage_2010plus.csv (unified coverage for regimes and indices)
- outputs/v2/regime_coverage_2010plus.csv
- outputs/v2/index_coverage_2010plus.csv
- outputs/v2/weak_coverage_2010plus.csv
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import pandas as pd
import exchange_calendars as xcals

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REGIME_COUNTRY = {
    "Fed": "US",
    "ECB": "EA",
    "BoE": "GB",
    "BoJ": "JP",
    "BoC": "CA",
    "RBA": "AU",
    "BCB": "BR",
    "Banxico": "MX",
    "BoK": "KR",
    "CBR": "RU",
    "PBoC": "CN",
    "RBI": "IN",
}

COUNTRY_TO_ISO = {
    "AU": "XASX",
    "BR": "BVMF",
    "CA": "XTSE",
    "CN": "XSHG",
    "DE": "XFRA",
    "EA": "XPAR",
    "ES": "XMAD",
    "FR": "XPAR",
    "GB": "XLON",
    "IN": "XBOM",
    "IT": "XMIL",
    "JP": "XTKS",
    "KR": "XKRX",
    "MX": "XMEX",
    "RU": "XMOS",
    "US": "XNYS",
}

YEARS = list(range(2010, 2027))  # 2010 to 2026 inclusive


def fmt_tiers(s: pd.Series) -> str:
    u = sorted(s.dropna().unique())
    if not u:
        return "None"
    return ", ".join([f"Tier {int(x)}" for x in u])


def fmt_types(s: pd.Series) -> str:
    u = sorted(s.dropna().unique())
    if not u:
        return "None"
    return ", ".join([str(x) for x in u])


def audit_regimes(policy_path: Path) -> pd.DataFrame:
    df_pol = pd.read_csv(policy_path)
    df_pol["decision_date"] = pd.to_datetime(df_pol["decision_date"])
    df_pol_2010 = df_pol[df_pol["decision_date"] >= "2010-01-01"].copy()
    df_pol_2010["year"] = df_pol_2010["decision_date"].dt.year

    # Aggregate existing data
    agg = df_pol_2010.groupby(["regime", "year"]).agg(
        decisions=("decision", "count"),
        tier=("shock_tier", fmt_tiers),
        shock_measure_type=("shock_measure_type", fmt_types),
        analysis_ready_timing=("analysis_ready_timing", "sum"),
        shock_primary=("shock_primary", "sum"),
        shock_usable=("shock_usable", "sum"),
    ).reset_index()

    # Create full Cartesian product for 12 regimes x 17 years = 204 rows
    all_regimes = sorted(REGIME_COUNTRY.keys())
    full_idx = pd.MultiIndex.from_product([all_regimes, YEARS], names=["regime", "year"]).to_frame().reset_index(drop=True)
    merged = pd.merge(full_idx, agg, on=["regime", "year"], how="left")

    merged["decisions"] = merged["decisions"].fillna(0).astype(int)
    merged["tier"] = merged["tier"].fillna("None")
    merged["shock_measure_type"] = merged["shock_measure_type"].fillna("None")
    merged["analysis_ready_timing"] = merged["analysis_ready_timing"].fillna(0).astype(int)
    merged["shock_primary"] = merged["shock_primary"].fillna(0).astype(int)
    merged["shock_usable"] = merged["shock_usable"].fillna(0).astype(int)
    merged["country"] = merged["regime"].map(REGIME_COUNTRY)

    # Determine weak coverage
    weak_flags = []
    weak_reasons = []

    for _, row in merged.iterrows():
        reasons = []
        if row["decisions"] == 0:
            reasons.append("Zero decisions recorded")
        elif row["decisions"] < 8:
            reasons.append(f"Low decisions count ({row['decisions']}/yr)")

        if row["shock_primary"] == 0:
            reasons.append("Zero primary shocks (missing proxy/pegged/hold)")
        elif row["shock_primary"] < row["decisions"] * 0.5:
            reasons.append(f"Low primary shocks ({row['shock_primary']}/{row['decisions']})")

        if row["analysis_ready_timing"] == 0:
            reasons.append("Unverified announcement timing (0 ready)")
        elif row["analysis_ready_timing"] < row["decisions"]:
            reasons.append(f"Incomplete timing verification ({row['analysis_ready_timing']}/{row['decisions']})")

        is_weak = 1 if len(reasons) > 0 else 0
        weak_flags.append(is_weak)
        weak_reasons.append("; ".join(reasons) if reasons else "Full coverage")

    merged["weak_coverage"] = weak_flags
    merged["weak_reasons"] = weak_reasons
    merged["entity_type"] = "regime"
    merged["entity_id"] = merged["regime"]

    return merged


def audit_indices(panel_path: Path) -> pd.DataFrame:
    df_pan = pd.read_parquet(panel_path)
    df_pan["date"] = pd.to_datetime(df_pan["date"])
    df_pan_2010 = df_pan[df_pan["date"] >= "2010-01-01"].copy()
    df_pan_2010["year"] = df_pan_2010["date"].dt.year

    max_date = df_pan_2010["date"].max()

    # Pre-instantiate calendars
    cals = {}
    for cty, iso in COUNTRY_TO_ISO.items():
        cals[cty] = xcals.get_calendar(iso, start="2000-01-01", end="2026-12-31")

    # Group by index_id and year
    agg = df_pan_2010.groupby(["index_id", "year"]).agg(
        trading_days=("date", "count"),
        country=("country", "first"),
        stale_flags=("stale_flag", "sum"),
        outlier_flags=("outlier_flag", "sum"),
    ).reset_index()

    all_indices = sorted(df_pan_2010["index_id"].unique())
    index_country_map = df_pan_2010.groupby("index_id")["country"].first().to_dict()

    # Full Cartesian product for 38 indices x 17 years = 646 rows
    full_idx = pd.MultiIndex.from_product([all_indices, YEARS], names=["index_id", "year"]).to_frame().reset_index(drop=True)
    merged = pd.merge(full_idx, agg, on=["index_id", "year"], how="left")

    merged["trading_days"] = merged["trading_days"].fillna(0).astype(int)
    merged["stale_flags"] = merged["stale_flags"].fillna(0).astype(int)
    merged["outlier_flags"] = merged["outlier_flags"].fillna(0).astype(int)
    merged["country"] = merged["index_id"].map(index_country_map)

    # Compute calendar days and missing days
    cal_days = []
    missing_days = []
    weak_flags = []
    weak_reasons = []

    for _, row in merged.iterrows():
        cty = row["country"]
        yr = row["year"]
        cal = cals[cty]

        if yr == 2026:
            # End calendar at latest dataset date
            sessions = cal.sessions_in_range("2026-01-01", max_date.strftime("%Y-%m-%d"))
        else:
            sessions = cal.sessions_in_range(f"{yr}-01-01", f"{yr}-12-31")

        n_cal = len(sessions)
        cal_days.append(n_cal)
        n_miss = max(0, n_cal - row["trading_days"])
        missing_days.append(n_miss)

        reasons = []
        if row["trading_days"] == 0:
            reasons.append("Zero trading days (pre-inception/inactive)")
        elif n_miss > 20:
            reasons.append(f"High missing sessions ({n_miss} missing of {n_cal})")

        if row["stale_flags"] > 5:
            reasons.append(f"Stale price ({row['stale_flags']} stale days)")

        if row["outlier_flags"] > 5:
            reasons.append(f"Outlier anomalies ({row['outlier_flags']} outlier flags)")

        is_weak = 1 if len(reasons) > 0 else 0
        weak_flags.append(is_weak)
        weak_reasons.append("; ".join(reasons) if reasons else "Full coverage")

    merged["calendar_days"] = cal_days
    merged["missing_days"] = missing_days
    merged["weak_coverage"] = weak_flags
    merged["weak_reasons"] = weak_reasons
    merged["entity_type"] = "index"
    merged["entity_id"] = merged["index_id"]

    return merged


def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_final = base_dir / "data" / "final"
    out_dir = base_dir / "outputs" / "v2"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Auditing Regimes (2010+)...")
    reg_df = audit_regimes(data_final / "policy_decisions.csv")
    print(f"Total regime-years: {len(reg_df)}, Weak regime-years: {reg_df['weak_coverage'].sum()}")

    print("Auditing Indices (2010+)...")
    idx_df = audit_indices(data_final / "panel_daily.parquet")
    print(f"Total index-years: {len(idx_df)}, Weak index-years: {idx_df['weak_coverage'].sum()}")

    # Save individual audit tables
    reg_csv_path = out_dir / "regime_coverage_2010plus.csv"
    reg_cols = [
        "regime", "year", "country", "decisions", "tier", "shock_measure_type",
        "analysis_ready_timing", "shock_primary", "shock_usable", "weak_coverage", "weak_reasons"
    ]
    reg_df[reg_cols].to_csv(reg_csv_path, index=False)
    print(f"Saved: {reg_csv_path}")

    idx_csv_path = out_dir / "index_coverage_2010plus.csv"
    idx_cols = [
        "index_id", "year", "country", "trading_days", "calendar_days", "missing_days",
        "stale_flags", "outlier_flags", "weak_coverage", "weak_reasons"
    ]
    idx_df[idx_cols].to_csv(idx_csv_path, index=False)
    print(f"Saved: {idx_csv_path}")

    # Unified coverage table
    unified_cols = [
        "entity_type", "entity_id", "year", "country",
        "decisions", "tier", "shock_measure_type", "analysis_ready_timing", "shock_primary",
        "trading_days", "calendar_days", "missing_days", "stale_flags", "outlier_flags",
        "weak_coverage", "weak_reasons"
    ]
    unified_df = pd.concat([reg_df, idx_df], ignore_index=True)[unified_cols]
    unified_path = out_dir / "coverage_2010plus.csv"
    unified_df.to_csv(unified_path, index=False)
    print(f"Saved unified coverage: {unified_path}")

    # Weak coverage slice
    weak_df = unified_df[unified_df["weak_coverage"] == 1].copy()
    weak_path = out_dir / "weak_coverage_2010plus.csv"
    weak_df.to_csv(weak_path, index=False)
    print(f"Saved weak coverage slice: {weak_path} ({len(weak_df)} rows)")


if __name__ == "__main__":
    main()
