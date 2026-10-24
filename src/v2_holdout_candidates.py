"""Generate holdout candidates and holdout decisions for MoTrans-15 v2.0.

Produces:
- outputs/v2/holdout_candidates.csv
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
BOUNDARIES = ["2022-01-01", "2024-01-01", "2025-01-01", "2025-10-14"]


def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_final = base_dir / "data" / "final"
    out_dir = base_dir / "outputs" / "v2"
    out_dir.mkdir(parents=True, exist_ok=True)

    df_pol = pd.read_csv(data_final / "policy_decisions.csv")
    df_pol["decision_date"] = pd.to_datetime(df_pol["decision_date"])
    
    # Exclude non_decision events (e.g. Jackson Hole speech)
    df_pol = df_pol[df_pol["event_type"] != "non_decision"].copy()

    df2010 = df_pol[(df_pol["decision_date"] >= "2010-01-01") & (df_pol["regime"].isin(REGIMES))].copy()
    eff = df2010[(df2010["shock_primary"] == 1) & (df2010["analysis_ready_timing"] == 1)].copy()

    rows = []

    # Section 1: Candidate boundaries
    for b in BOUNDARIES:
        b_dt = pd.to_datetime(b)
        sub = eff[eff["decision_date"] >= b_dt].copy()
        
        n_tot = len(sub)
        n_t1 = int((sub["shock_tier"] == 1.0).sum())
        n_t2 = int((sub["shock_tier"] == 2.0).sum())
        n_hike = int((sub["decision"] == "hike").sum())
        n_cut = int((sub["decision"] == "cut").sum())
        n_hold = int((sub["decision"] == "hold").sum())

        for reg in REGIMES:
            r_sub = sub[sub["regime"] == reg]
            r_tot = len(r_sub)
            r_t1 = int((r_sub["shock_tier"] == 1.0).sum())
            r_t2 = int((r_sub["shock_tier"] == 2.0).sum())
            r_hike = int((r_sub["decision"] == "hike").sum())
            r_cut = int((r_sub["decision"] == "cut").sum())
            r_hold = int((r_sub["decision"] == "hold").sum())

            rows.append({
                "section": "boundary_summary",
                "boundary": b,
                "regime": reg,
                "total_effective_after": r_tot,
                "tier_1_count": r_t1,
                "tier_2_count": r_t2,
                "hikes": r_hike,
                "cuts": r_cut,
                "holds": r_hold,
                "decision_date": "",
                "decision": "",
                "size_bp": "",
                "shock_tier": "",
            })

        # All regimes total for this boundary
        rows.append({
            "section": "boundary_summary",
            "boundary": b,
            "regime": "All Regimes",
            "total_effective_after": n_tot,
            "tier_1_count": n_t1,
            "tier_2_count": n_t2,
            "hikes": n_hike,
            "cuts": n_cut,
            "holds": n_hold,
            "decision_date": "",
            "decision": "",
            "size_bp": "",
            "shock_tier": "",
        })

    # Section 2: Current 11 final_holdout decisions (2025-10-14 to 2026-10-13)
    holdout = eff[(eff["decision_date"] >= "2025-10-14") & (eff["decision_date"] <= "2026-10-13")].sort_values("decision_date")
    for _, h_row in holdout.iterrows():
        rows.append({
            "section": "final_holdout_decisions",
            "boundary": "2025-10-14 to 2026-10-13",
            "regime": h_row["regime"],
            "total_effective_after": "",
            "tier_1_count": "",
            "tier_2_count": "",
            "hikes": "",
            "cuts": "",
            "holds": "",
            "decision_date": h_row["decision_date"].strftime("%Y-%m-%d"),
            "decision": h_row["decision"],
            "size_bp": h_row["size_bp"],
            "shock_tier": f"Tier {int(h_row['shock_tier'])}",
        })

    out_df = pd.DataFrame(rows)
    out_path = out_dir / "holdout_candidates.csv"
    out_df.to_csv(out_path, index=False)
    print(f"Saved: {out_path} ({len(out_df)} rows)")


if __name__ == "__main__":
    main()
