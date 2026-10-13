"""MoTrans-15 data pipeline — end-to-end rebuild from raw to final.

Each collector reuses files already in data/raw/ and only downloads what is missing.
"""

from src import audit_pilot, collect_indices, collect_policy


def main() -> None:
    """Run the pipeline steps implemented so far (Phase B1 pilot)."""
    collect_indices.main()
    collect_policy.main()
    audit_pilot.main()


if __name__ == "__main__":
    main()
