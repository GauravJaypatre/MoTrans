"""V0 Addendum: Effective Sample Breakdown for MoTrans-15 v2.0.

Produces:
- outputs/v2/effective_by_year.csv
- outputs/v2/effective_by_period.csv
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REGIMES = ["Fed", "ECB", "BoE", "BoC", "RBA", "CBR", "BoJ"]
YEARS = list(range(2010, 2027))


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


def build_effective_by_year(df_pol: pd.DataFrame) -> pd.DataFrame:
    df_pol["decision_date"] = pd.to_datetime(df_pol["decision_date"])
    df2010 = df_pol[(df_pol["decision_date"] >= "2010-01-01") & (df_pol["regime"].isin(REGIMES))].copy()
    df2010["year"] = df2010["decision_date"].dt.year

    df2010["is_hike"] = (df2010["decision"] == "hike").astype(int)
    df2010["is_cut"] = (df2010["decision"] == "cut").astype(int)
    df2010["is_hold"] = (df2010["decision"] == "hold").astype(int)
    df2010["nonzero_change"] = (df2010["size_bp"] != 0).astype(int)
    df2010["effective"] = ((df2010["shock_primary"] == 1) & (df2010["analysis_ready_timing"] == 1)).astype(int)

    rows = []
    for reg in REGIMES:
        reg_sub = df2010[df2010["regime"] == reg]
        for yr in YEARS:
            sub = reg_sub[reg_sub["year"] == yr]
            n_dec = len(sub)
            n_hike = int(sub["is_hike"].sum())
            n_cut = int(sub["is_cut"].sum())
            n_hold = int(sub["is_hold"].sum())
            n_nonz = int(sub["nonzero_change"].sum())
            t_str = fmt_tiers(sub["shock_tier"])
            m_str = fmt_types(sub["shock_measure_type"])
            n_prim = int(sub["shock_primary"].sum())
            n_time = int(sub["analysis_ready_timing"].sum())
            n_eff = int(sub["effective"].sum())

            notes = []
            if reg == "CBR" and yr <= 2013:
                notes.append(f"Pre-Key Rate era: {n_prim} primary shocks vs {n_time} timing-ready")
            elif reg == "BoE" and yr <= 2015:
                notes.append("Prolonged hold at 0.50%; timing approximate")
            elif reg == "BoC" and yr <= 2012:
                notes.append(f"Timing unverified pre-2013 ({n_prim} primary vs {n_time} timing-ready)")
            elif reg == "BoJ":
                notes.append("Excluded from primary due to ZIRP/YCC peg (0 primary)")
            elif reg == "Fed" and yr >= 2024:
                notes.append(f"Post-HF transition to Tier 2 yield proxy ({n_prim} primary rate changes)")
            elif reg == "ECB" and yr == 2026:
                notes.append(f"Post-HF transition to Tier 2 yield proxy ({n_prim} primary rate changes)")

            rows.append({
                "regime": reg,
                "year": str(yr),
                "decisions": n_dec,
                "hikes": n_hike,
                "cuts": n_cut,
                "holds": n_hold,
                "nonzero_changes": n_nonz,
                "shock_tier": t_str,
                "shock_measure_type": m_str,
                "shock_primary": n_prim,
                "analysis_ready_timing": n_time,
                "effective_decisions": n_eff,
                "notes": "; ".join(notes) if notes else "",
            })

        # Total row per regime
        t_reg_tier = fmt_tiers(reg_sub["shock_tier"])
        t_reg_type = fmt_types(reg_sub["shock_measure_type"])
        reg_notes = ""
        if reg == "CBR":
            reg_notes = "CBR has 51 primary shocks but only 41 timing-ready decisions in 2010+; effective = 41"
        elif reg == "BoC":
            reg_notes = "BoC has 32 primary shocks but 3 in 2010 had unverified timing; effective = 29"
        elif reg == "BoJ":
            reg_notes = "BoJ excluded from primary (0 effective)"

        rows.append({
            "regime": reg,
            "year": "Total",
            "decisions": len(reg_sub),
            "hikes": int(reg_sub["is_hike"].sum()),
            "cuts": int(reg_sub["is_cut"].sum()),
            "holds": int(reg_sub["is_hold"].sum()),
            "nonzero_changes": int(reg_sub["nonzero_change"].sum()),
            "shock_tier": t_reg_tier,
            "shock_measure_type": t_reg_type,
            "shock_primary": int(reg_sub["shock_primary"].sum()),
            "analysis_ready_timing": int(reg_sub["analysis_ready_timing"].sum()),
            "effective_decisions": int(reg_sub["effective"].sum()),
            "notes": reg_notes,
        })

    # All regimes grand total
    rows.append({
        "regime": "All Regimes",
        "year": "Grand Total",
        "decisions": len(df2010),
        "hikes": int(df2010["is_hike"].sum()),
        "cuts": int(df2010["is_cut"].sum()),
        "holds": int(df2010["is_hold"].sum()),
        "nonzero_changes": int(df2010["nonzero_change"].sum()),
        "shock_tier": "Tier 1, Tier 2",
        "shock_measure_type": "Various",
        "shock_primary": int(df2010["shock_primary"].sum()),
        "analysis_ready_timing": int(df2010["analysis_ready_timing"].sum()),
        "effective_decisions": int(df2010["effective"].sum()),
        "notes": "Effective decisions require both shock_primary==1 AND analysis_ready_timing==1",
    })

    return pd.DataFrame(rows)


def build_effective_by_period(df_pol: pd.DataFrame) -> pd.DataFrame:
    df_pol["decision_date"] = pd.to_datetime(df_pol["decision_date"])
    df2010 = df_pol[(df_pol["decision_date"] >= "2010-01-01") & (df_pol["regime"].isin(REGIMES))].copy()
    eff = df2010[(df2010["shock_primary"] == 1) & (df2010["analysis_ready_timing"] == 1)].copy()

    def get_period(d):
        dt_str = d.strftime("%Y-%m-%d")
        if "2025-10-14" <= dt_str <= "2026-10-13":
            return "final_holdout (2025-10-14 to 2026-10-13)"
        elif "2010-01-01" <= dt_str <= "2014-12-31":
            return "2010-2014"
        elif "2015-01-01" <= dt_str <= "2019-12-31":
            return "2015-2019"
        elif "2020-01-01" <= dt_str <= "2021-12-31":
            return "2020-2021"
        elif "2022-01-01" <= dt_str <= "2025-10-13":
            return "2022-2025 (pre-holdout)"
        return "other"

    eff["period"] = eff["decision_date"].apply(get_period)

    period_order = [
        "2010-2014",
        "2015-2019",
        "2020-2021",
        "2022-2025 (pre-holdout)",
        "final_holdout (2025-10-14 to 2026-10-13)",
    ]

    rows = []
    for p in period_order:
        p_sub = eff[eff["period"] == p]
        for tier in [1.0, 2.0]:
            t_sub = p_sub[p_sub["shock_tier"] == tier]
            rows.append({
                "period": p,
                "tier": f"Tier {int(tier)}",
                "hikes": int((t_sub["decision"] == "hike").sum()),
                "cuts": int((t_sub["decision"] == "cut").sum()),
                "holds": int((t_sub["decision"] == "hold").sum()),
                "total_effective": len(t_sub),
            })
        # Subtotal for period
        rows.append({
            "period": p,
            "tier": "All Tiers",
            "hikes": int((p_sub["decision"] == "hike").sum()),
            "cuts": int((p_sub["decision"] == "cut").sum()),
            "holds": int((p_sub["decision"] == "hold").sum()),
            "total_effective": len(p_sub),
        })

    # Grand total
    rows.append({
        "period": "Total (2010 to 2026-10-13)",
        "tier": "Tier 1",
        "hikes": int((eff[eff["shock_tier"] == 1.0]["decision"] == "hike").sum()),
        "cuts": int((eff[eff["shock_tier"] == 1.0]["decision"] == "cut").sum()),
        "holds": int((eff[eff["shock_tier"] == 1.0]["decision"] == "hold").sum()),
        "total_effective": len(eff[eff["shock_tier"] == 1.0]),
    })
    rows.append({
        "period": "Total (2010 to 2026-10-13)",
        "tier": "Tier 2",
        "hikes": int((eff[eff["shock_tier"] == 2.0]["decision"] == "hike").sum()),
        "cuts": int((eff[eff["shock_tier"] == 2.0]["decision"] == "cut").sum()),
        "holds": int((eff[eff["shock_tier"] == 2.0]["decision"] == "hold").sum()),
        "total_effective": len(eff[eff["shock_tier"] == 2.0]),
    })
    rows.append({
        "period": "Total (2010 to 2026-10-13)",
        "tier": "All Tiers",
        "hikes": int((eff["decision"] == "hike").sum()),
        "cuts": int((eff["decision"] == "cut").sum()),
        "holds": int((eff["decision"] == "hold").sum()),
        "total_effective": len(eff),
    })

    return pd.DataFrame(rows)


def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_final = base_dir / "data" / "final"
    out_dir = base_dir / "outputs" / "v2"
    out_dir.mkdir(parents=True, exist_ok=True)

    df_pol = pd.read_csv(data_final / "policy_decisions.csv")

    eff_year = build_effective_by_year(df_pol)
    eff_year_path = out_dir / "effective_by_year.csv"
    eff_year.to_csv(eff_year_path, index=False)
    print(f"Saved: {eff_year_path}")

    eff_period = build_effective_by_period(df_pol)
    eff_period_path = out_dir / "effective_by_period.csv"
    eff_period.to_csv(eff_period_path, index=False)
    print(f"Saved: {eff_period_path}")


if __name__ == "__main__":
    main()
