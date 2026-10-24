"""MoTrans-15 data pipeline — end-to-end rebuild from raw to final.

Each collector reuses files already in data/raw/ and only downloads what is missing.
"""

import sys

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src import (
    audit_pilot,
    build_analysis_tables,
    build_panel,
    build_shocks,
    collect_controls,
    collect_indices,
    collect_policy,
    collect_policy_more,
    collect_statements,
    event_windows,
    hand_check,
)


def main() -> None:
    # Phase B pilot (kept so the signed-off hand-check stays reproducible)
    collect_indices.main()      # all equity series (+ pilot subset)
    collect_policy.main()       # Fed, ECB, RBI, BoJ decisions + announcement windows
    audit_pilot.main()
    event_windows.main()        # pilot event windows
    hand_check.main()           # never overwrites a signed workbook
    # Phase C full dataset
    collect_policy_more.main()  # BoE, PBoC, CBR, BoC, BCB, Banxico, RBA, BoK
    collect_controls.main()     # FX, policy rate, CPI, industrial production, 1y yield, VIX
    build_panel.main()          # data/final/panel_daily.parquet + docs/data_quality_report.md
    event_windows.main_full()   # data/final/events.parquet + policy_decisions.csv
    # Phase D shocks
    build_shocks.main()         # data/final/shocks.parquet, shock columns in events, docs/shock_validation.md
    # Phase E statement corpus
    collect_statements.main()   # data/final/statements.parquet, coverage, hand-label sample
    # Analysis tables
    build_analysis_tables.main() # data/final/analysis_tier1.parquet, analysis_tier2_primary.parquet


if __name__ == "__main__":
    main()
