"""Policy Decision Overlap and Event Contamination Analysis Script.

Usage:
    python outputs/overlap_analysis.py

Output:
    outputs/overlap_stats.csv

Procedure:
    For each horizon W in {1, 3, 5, 20, 60} trading days:
    1. Loads shocks.parquet.
    2. Uses columns overlap_{W}d and overlap_count_{W}d to measure the count and share
       of policy decisions where at least one other central bank policy decision occurs
       within the forward event window [t, t + W - 1].
    3. Outputs contamination rate, mean number of overlapping decisions, and max count.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

shocks = pd.read_parquet(FINAL / "shocks.parquet")

overlap_rows = []
for W in [1, 3, 5, 20, 60]:
    flag_col = f"overlap_{W}d"
    cnt_col = f"overlap_count_{W}d"
    contam = int(shocks[flag_col].sum())
    n_tot = len(shocks)
    pct = round((contam / n_tot) * 100, 2)
    mean_c = round(float(shocks[cnt_col].mean()), 2)
    max_c = int(shocks[cnt_col].max())
    overlap_rows.append({
        "window_days": W,
        "horizon_label": f"clr_{W}",
        "contaminated_events": contam,
        "total_events": n_tot,
        "contamination_share_pct": pct,
        "mean_other_decisions": mean_c,
        "max_other_decisions": max_c,
    })

df = pd.DataFrame(overlap_rows)
df.to_csv(OUT / "overlap_stats.csv", index=False)
print("Saved outputs/overlap_stats.csv")
