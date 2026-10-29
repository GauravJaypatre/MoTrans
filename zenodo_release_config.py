"""Configuration for MoTrans-15 v2.1.1 Zenodo release package builder.

All package settings are controlled exclusively from this file.
"""

ACCESS_MODE = "restricted"  # "restricted" or "open"
DATA_LICENSE = "CC-BY-4.0"
CODE_LICENSE = "MIT"
TITLE = (
    "MoTrans-15: Monetary policy surprises, central bank communication and equity-index "
    "responses for the largest economies, 2010-2025 (v2.1.1)"
)

# License safety gates
ALLOW_DERIVED_RETURNS = False  # Set to True only if LICENCE_CLEARANCE.txt exists and is non-empty
INCLUDE_POST_WINDOW = False    # Exclude post_window_2026.parquet (quarantined 2026 data)
INCLUDE_EXCLUDED_ROWS = False  # Exclude excluded_rows.parquet

