"""MoTrans-15 data pipeline — end-to-end rebuild from raw to final.

Each collector reuses files already in data/raw/ and only downloads what is missing.
"""

from src import (
    audit_pilot,
    build_panel,
    collect_controls,
    collect_indices,
    collect_policy,
    collect_policy_more,
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


if __name__ == "__main__":
    main()
