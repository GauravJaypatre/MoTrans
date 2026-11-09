"""Fix RBA 2026-09-29 Policy Decision from Saved Official Raw HTML.

Official page confirmation:
data/raw/official_decisions/rba_statement_2026_09_29.html (RBA Media Release 2026-27):
"At its meeting today, the Board decided to increase the cash rate target by 25 basis points to 4.60 per cent."

Fixes:
- data/final/policy_decisions.csv (row 2327)
- data/final/events.parquet (38 event rows for RBA 2026-09-29)
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

# 1. Update policy_decisions.csv
p_pol = ROOT / "data" / "final" / "policy_decisions.csv"
df_pol = pd.read_csv(p_pol)

mask_pol = (df_pol["regime"] == "RBA") & (df_pol["decision_date"] == "2026-09-29")
print("Before in policy_decisions.csv:")
print(df_pol[mask_pol][["regime", "decision_date", "decision", "size_bp", "new_rate_pct"]])

df_pol.loc[mask_pol, "decision"] = "hike"
df_pol.loc[mask_pol, "size_bp"] = 25.0
df_pol.loc[mask_pol, "new_rate_pct"] = 4.60

df_pol.to_csv(p_pol, index=False)
print("After in policy_decisions.csv:")
print(df_pol[mask_pol][["regime", "decision_date", "decision", "size_bp", "new_rate_pct"]])

# 2. Update events.parquet
p_ev = ROOT / "data" / "final" / "events.parquet"
df_ev = pd.read_parquet(p_ev)

mask_ev = (df_ev["regime"] == "RBA") & (df_ev["decision_date"] == "2026-09-29")
print(f"\nUpdating {mask_ev.sum()} rows in events.parquet...")

df_ev.loc[mask_ev, "decision"] = "hike"
df_ev.loc[mask_ev, "size_bp"] = 25.0
df_ev.loc[mask_ev, "new_rate_pct"] = 4.60

df_ev.to_parquet(p_ev, index=False)
print("Successfully updated events.parquet.")
