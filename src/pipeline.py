"""MoTrans-15 data pipeline — end-to-end rebuild from raw to final.

Each collector reuses files already in data/raw/ and only downloads what is missing.
"""

from src import audit_pilot, collect_indices, collect_policy, event_windows, hand_check


def main() -> None:
    """Run the pipeline steps implemented so far (Phase B pilot)."""
    collect_indices.main()   # B1: equity levels and returns
    collect_policy.main()    # B1: policy decisions + announcement windows
    audit_pilot.main()       # B1: coverage summary
    event_windows.main()     # B2: session alignment and event-window returns
    hand_check.main()        # B gate: 10-event sheet for manual checking


if __name__ == "__main__":
    main()
