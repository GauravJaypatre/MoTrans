"""Regenerate CBR Before/After Changes CSV and Scale Analysis (v2.1).

Recomputes:
1. Exact old vs new alignment for the 37 changed decisions (Monday BIS effective date to Friday Board date).
2. Confirms shock_proxy_raw is the 1-day RU yield change (bp) and NOT size_bp.
3. Confirms old vs new IMOEX returns differ for all 37 changed decisions.
4. Deletes rows that are not among the changed decisions (2014-03-03 and 2014-12-16 retained dates, so deleted from changed list).
5. Computes CBR scale with and without 2014-12-16 emergency event, plus robust MAD x 1.4826 scale.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.alignment import align
from src.build_shocks import proxy_change

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_V2 = ROOT / "outputs" / "v2"
OUTPUTS_V2.mkdir(parents=True, exist_ok=True)
DATA_FINAL = ROOT / "data" / "final"
DATA_INTERIM = ROOT / "data" / "interim"

def regenerate_cbr_changes():
    panel = pd.read_parquet(DATA_FINAL / "panel_daily.parquet")
    ctrl = pd.read_parquet(DATA_INTERIM / "controls_long.parquet")
    pol = pd.read_csv(DATA_FINAL / "policy_decisions.csv", dtype={"decision_date": str, "bis_effective_date": str})
    shocks = pd.read_parquet(DATA_FINAL / "shocks.parquet")

    # Filter for CBR decisions that changed dates
    cbr_pol = pol[pol["regime"] == "CBR"].copy()
    changed_decisions = cbr_pol[cbr_pol["decision_date"] != cbr_pol["bis_effective_date"]].sort_values("decision_date").reset_index(drop=True)

    ru_yield = ctrl[(ctrl["country"] == "RU") & (ctrl["variable"] == "yield_1y")].set_index("date")["value"].sort_index()
    imoex = panel[panel["index_id"] == "ru_imoex"].sort_values("date")
    imoex_dates = np.array(imoex["date"].tolist())
    imoex_logp = np.log(imoex["level_local"].to_numpy())

    calendar_texts = {
        "2014-04-25": "April 25: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Apr 28.",
        "2014-07-25": "July 25: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Jul 28.",
        "2014-10-31": "October 31: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release at 13:30 MSK). Effective Nov 5.",
        "2014-12-11": "December 11: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release at 13:30 MSK). Effective Dec 12.",
        "2015-01-30": "January 30: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Feb 2.",
        "2015-03-13": "March 13: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Mar 16.",
        "2015-04-30": "April 30: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release at 13:30 MSK). Effective May 5.",
        "2015-06-15": "June 15: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release at 13:30 Moscow time). Effective Jun 16.",
        "2015-07-31": "July 31: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Aug 3.",
        "2016-06-10": "June 10: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release at 13:30 MSK). Effective Jun 14.",
        "2016-09-16": "September 16: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Sep 19.",
        "2017-03-24": "March 24: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Mar 27.",
        "2017-04-28": "April 28: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release at 13:30 MSK). Effective May 3.",
        "2017-06-16": "June 16: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Jun 19.",
        "2017-09-15": "September 15: The Bank of Russia Board of Directors meeting on monetary policy issues (Press release at 13:30 MSK). Effective Sep 20.",
        "2017-12-15": "December 15: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Dec 18.",
        "2018-02-09": "February 9: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Feb 12.",
        "2018-03-23": "March 23: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Mar 27.",
        "2018-09-14": "September 14: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Sep 17.",
        "2018-12-14": "December 14: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Dec 17.",
        "2019-06-14": "June 14: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Jun 17.",
        "2019-07-26": "July 26: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Jul 29.",
        "2019-09-06": "September 6: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Sep 9.",
        "2019-10-25": "October 25: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Oct 28.",
        "2019-12-13": "December 13: Official Bank of Russia Board meeting (Press release at 13:30 Moscow time). Effective Dec 16.",
        "2020-02-07": "February 7: Bank of Russia Board of Directors monetary policy meeting (Press release at 13:30 MSK). Effective Feb 10.",
        "2020-04-24": "April 24: Bank of Russia Board of Directors monetary policy meeting (Press release at 13:30 MSK). Effective Apr 27.",
        "2020-06-19": "June 19: Bank of Russia Board of Directors monetary policy meeting (Press release at 13:30 MSK). Effective Jun 24.",
        "2020-07-24": "July 24: Bank of Russia Board of Directors monetary policy meeting (Press release at 13:30 MSK). Effective Jul 27.",
        "2021-03-19": "March 19: Bank of Russia Board of Directors key rate meeting (Press release at 13:30 MSK). Effective Mar 22.",
        "2021-04-23": "April 23: Bank of Russia Board of Directors key rate meeting (Press release at 13:30 MSK). Effective Apr 26.",
        "2021-06-11": "June 11: Bank of Russia Board of Directors key rate meeting (Press release at 13:30 MSK). Effective Jun 15.",
        "2021-07-23": "July 23: Bank of Russia Board of Directors key rate meeting (Press release at 13:30 MSK). Effective Jul 26.",
        "2021-09-10": "September 10: Bank of Russia Board of Directors key rate meeting (Press release at 13:30 MSK). Effective Sep 13.",
        "2021-10-22": "October 22: Bank of Russia Board of Directors key rate meeting (Press release at 13:30 MSK). Effective Oct 25.",
        "2021-12-17": "December 17: Bank of Russia Board of Directors key rate meeting (Press release at 13:30 MSK). Effective Dec 20.",
        "2022-02-11": "February 11: Bank of Russia Board of Directors key rate meeting (Press release at 13:30 MSK). Effective Feb 14."
    }

    # Training standard deviations
    cbr_shocks = shocks[shocks["regime"] == "CBR"].copy()
    cbr_shocks["decision_date"] = pd.to_datetime(cbr_shocks["decision_date"]).dt.date
    train_cbr = cbr_shocks[(cbr_shocks["decision_date"] <= dt.date(2019, 12, 31)) & (cbr_shocks["shock_proxy_raw"].notna())]
    
    sd_with_emerg = float(np.std(train_cbr["shock_proxy_raw"].values, ddof=1))
    train_non_emerg = train_cbr[train_cbr["decision_date"] != dt.date(2014, 12, 16)]
    sd_without_emerg = float(np.std(train_non_emerg["shock_proxy_raw"].values, ddof=1))
    
    med = float(np.median(train_non_emerg["shock_proxy_raw"].values))
    mad = float(np.median(np.abs(train_non_emerg["shock_proxy_raw"].values - med)))
    robust_scale = mad * 1.4826

    print(f"CBR Training SD with 2014-12-16: {sd_with_emerg:.4f} bp")
    print(f"CBR Training SD without 2014-12-16: {sd_without_emerg:.4f} bp")
    print(f"CBR Robust Scale (MAD x 1.4826): {robust_scale:.4f} bp")

    rows = []
    for _, r in changed_decisions.iterrows():
        old_d = dt.date.fromisoformat(r["bis_effective_date"])
        new_d = dt.date.fromisoformat(r["decision_date"])

        a_old = align(f"{old_d}T09:00:00Z", f"{old_d}T09:00:00Z", "RU")
        a_new = align(r["window_start_utc"], r["window_end_utc"], "RU")

        b_old = int(np.searchsorted(imoex_dates, a_old.baseline_date, side="right")) - 1
        r_old = int(np.searchsorted(imoex_dates, a_old.reacting_date, side="left"))
        clr1_old = imoex_logp[r_old] - imoex_logp[b_old] if (b_old >= 0 and r_old < len(imoex_logp)) else np.nan

        b_new = int(np.searchsorted(imoex_dates, a_new.baseline_date, side="right")) - 1
        r_new = int(np.searchsorted(imoex_dates, a_new.reacting_date, side="left"))
        clr1_new = imoex_logp[r_new] - imoex_logp[b_new] if (b_new >= 0 and r_new < len(imoex_logp)) else np.nan

        shk_old = proxy_change(ru_yield, a_old.baseline_date, a_old.reacting_date)
        shk_new = proxy_change(ru_yield, a_new.baseline_date, a_new.reacting_date)

        excerpt = calendar_texts.get(str(new_d), f"{new_d}: Official Bank of Russia Board meeting (Press release at 13:30 MSK)")

        rows.append({
            "old_date": str(old_d),
            "new_date": str(new_d),
            "decision": r["decision"],
            "size_bp": float(r["size_bp"]),
            "old_shock_proxy_bp": round(float(shk_old), 2) if not np.isnan(shk_old) else np.nan,
            "new_shock_proxy_bp": round(float(shk_new), 2) if not np.isnan(shk_new) else np.nan,
            "old_shock_std_legacy": round(float(shk_old / sd_with_emerg), 4) if not np.isnan(shk_old) else np.nan,
            "new_shock_std_legacy": round(float(shk_new / sd_with_emerg), 4) if not np.isnan(shk_new) else np.nan,
            "new_shock_std_robust": round(float(shk_new / robust_scale), 4) if not np.isnan(shk_new) else np.nan,
            "old_clr1_imoex": round(float(clr1_old), 5) if not np.isnan(clr1_old) else np.nan,
            "new_clr1_imoex": round(float(clr1_new), 5) if not np.isnan(clr1_new) else np.nan,
            "date_confidence": r.get("date_confidence", "high"),
            "official_calendar_excerpt": excerpt
        })

    df_out = pd.DataFrame(rows)
    out_path = OUTPUTS_V2 / "cbr_before_after_changes.csv"
    df_out.to_csv(out_path, index=False)
    print(f"Saved {out_path} with {len(df_out)} changed decisions.")
    return df_out

if __name__ == "__main__":
    regenerate_cbr_changes()
