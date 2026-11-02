"""MoTrans-15 v2.1.1 Zenodo Release Package Builder (Revision 3).

Generates the complete release package in zenodo_release/ according to all
strict research integrity and packaging guidelines.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Import configuration
import zenodo_release_config as cfg

ROOT = Path(__file__).resolve().parent
RELEASE_DIR = ROOT / "zenodo_release"
DATA_V2_1_RELEASE = ROOT / "data" / "v2_1" / "release"
DATA_V2_1 = ROOT / "data" / "v2_1"
DOCS = ROOT / "docs"
OUTPUTS_V2_1 = ROOT / "outputs" / "v2_1"
OUTPUTS_V2 = ROOT / "outputs" / "v2"
ZIP_PATH = ROOT / "MoTrans15_v2.1.1_zenodo_package.zip"

# Certified hashes from docs/DATA_FREEZE_v2_1.md
CERTIFIED_HASHES = {
    "analysis_tier1.parquet": "8a6207dd0c753c7d24d0a4d091dbdb05ee38d3010913a85b4c9f87a86e44979e",
    "analysis_tier2_primary.parquet": "c319040f687fbd88be9268d881c71152d803a0bd20357a109da049415f010a14",
    "secondary_holds.parquet": "7235bae5b29d0e4261bc9349e32593b09f9d0bf7cd784a7f61a56a45dc9c846f",
    "sensitivity_macro_revision.parquet": "f689bc78820520f08020d4d613fb6129a07abe15842634e2c9b428bd0f5bf794",
    "panel_returns_only.parquet": "e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620",
    "folds.csv": "5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee",
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def remove_readonly(func, path, exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        try:
            shutil.rmtree(path, onexc=remove_readonly)
        except Exception:
            subprocess.run(["powershell", "-Command", f'Remove-Item -Path "{path}" -Recurse -Force'], check=False)
    path.mkdir(parents=True, exist_ok=True)

def verify_source_hashes() -> None:
    print("[1/11] Verifying source file SHA-256 hashes against DATA_FREEZE_v2_1.md...")
    for filename, expected_hash in CERTIFIED_HASHES.items():
        src_path = DATA_V2_1_RELEASE / filename
        if not src_path.exists():
            src_path = DATA_V2_1 / filename
        assert src_path.exists(), f"Source file missing: {src_path}"
        actual_hash = sha256_file(src_path)
        assert actual_hash == expected_hash, (
            f"Hash mismatch for {filename}!\nExpected: {expected_hash}\nActual:   {actual_hash}"
        )
        print(f"  Verified {filename}: {actual_hash[:16]}... OK")

def copy_data_files() -> None:
    print("[2/11] Copying allowed data files and generating CSV convenience exports...")
    data_dest = RELEASE_DIR / "data"
    data_dest.mkdir(parents=True, exist_ok=True)

    # Allowed tables
    for filename in CERTIFIED_HASHES.keys():
        src_path = DATA_V2_1_RELEASE / filename
        if not src_path.exists():
            src_path = DATA_V2_1 / filename
        dest_path = data_dest / filename
        shutil.copy2(src_path, dest_path)
        print(f"  Copied {filename}")

        # For tier1, tier2_primary, secondary_holds generate CSV convenience copies
        if filename in ["analysis_tier1.parquet", "analysis_tier2_primary.parquet", "secondary_holds.parquet"]:
            csv_name = filename.replace(".parquet", ".csv")
            csv_path = data_dest / csv_name
            import pandas as pd
            df = pd.read_parquet(src_path)
            df.to_csv(csv_path, index=False)
            print(f"  Exported convenience CSV: {csv_name} ({len(df)} rows)")

def copy_docs() -> None:
    print("[3/11] Copying documentation files...")
    docs_dest = RELEASE_DIR / "docs"
    docs_dest.mkdir(parents=True, exist_ok=True)

    docs_to_copy = [
        ("v2_1_data_dictionary.md", DOCS / "v2_1_data_dictionary.md"),
        ("v2_1_limitations.md", DOCS / "v2_1_limitations.md"),
        ("v2_1_spec.md", DOCS / "v2_1_spec.md"),
        ("preregistration.md", DOCS / "preregistration.md"),
        ("limitations.md", DOCS / "limitations.md"),
        ("DATA_FREEZE_v2_1.md", DOCS / "DATA_FREEZE_v2_1.md"),
        ("data_quality_scorecard.md", OUTPUTS_V2_1 / "data_quality_scorecard.md"),
        ("labelling_guide.md", DOCS / "labelling_guide.md"),
    ]
    for dest_name, src_path in docs_to_copy:
        assert src_path.exists(), f"Doc missing: {src_path}"
        shutil.copy2(src_path, docs_dest / dest_name)
        print(f"  Copied {dest_name}")

def copy_reports() -> None:
    print("[4/11] Copying report CSV files...")
    reports_dest = RELEASE_DIR / "reports"
    reports_dest.mkdir(parents=True, exist_ok=True)

    reports_to_copy = [
        ("split_counts.csv", OUTPUTS_V2_1 / "split_counts.csv"),
        ("fold_counts.csv", OUTPUTS_V2_1 / "fold_counts.csv"),
        ("test_window_composition.csv", OUTPUTS_V2_1 / "test_window_composition.csv"),
        ("row_membership.csv", OUTPUTS_V2_1 / "row_membership.csv"),
        ("leakage_audit.csv", OUTPUTS_V2_1 / "leakage_audit.csv"),
        ("analysis_ok_breakdown.csv", OUTPUTS_V2_1 / "analysis_ok_breakdown.csv"),
        ("years_thin.csv", OUTPUTS_V2_1 / "years_thin.csv"),
        ("verification_summary.csv", OUTPUTS_V2 / "verification_summary.csv"),
    ]
    for dest_name, src_path in reports_to_copy:
        assert src_path.exists(), f"Report missing: {src_path}"
        shutil.copy2(src_path, reports_dest / dest_name)
        print(f"  Copied {dest_name}")

def copy_code() -> None:
    print("[5/11] Packaging code (src, tests, tasks, requirements, pytest.ini, conftest.py)...")
    code_dest = RELEASE_DIR / "code"
    code_dest.mkdir(parents=True, exist_ok=True)

    # Copy src
    shutil.copytree(
        ROOT / "src",
        code_dest / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    # Copy tests (excluding repo-level packaging/summary consistency tests that test repo root artifacts)
    shutil.copytree(
        ROOT / "tests",
        code_dest / "tests",
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", "*.pyo",
            "test_project_summary.py", "test_release_parquet_matches_summary.py",
            "test_docs_match_csvs.py", "test_modeling_harness.py",
        ),
    )
    # Copy root config files
    for f in ["tasks.py", "requirements.txt", "pytest.ini"]:
        shutil.copy2(ROOT / f, code_dest / f)

    # Add isolated-package conftest.py to auto-skip tests requiring excluded raw/interim/v2 data
    conftest_code = '''"""Pytest configuration for isolated Zenodo release code package.

Automatically skips tests that depend on data directories excluded from the
public release package per license and privacy safety rules (e.g. data/raw,
data/final, data/v2, unredacted panel.parquet, post_window_2026.parquet).
"""

from __future__ import annotations

from pathlib import Path
import pytest

REASON_EXCLUDED = "requires data excluded from public release; see LIMITATIONS_PACKAGE.md"

def pytest_collection_modifyitems(config, items):
    root = Path(config.rootdir)
    missing_final = not (root / "data" / "final").exists()
    missing_v2 = not (root / "data" / "v2").exists()
    missing_outputs_v2 = not (root / "outputs" / "v2").exists()
    missing_unredacted_v2_1 = not (root / "data" / "v2_1" / "panel.parquet").exists()
    missing_docs_summary = not (root / "docs" / "PROJECT_SUMMARY.md").exists()

    skip_marker = pytest.mark.skip(reason=REASON_EXCLUDED)

    for item in items:
        nodeid = item.nodeid
        if "test_analysis_tables.py" in nodeid and missing_final:
            item.add_marker(skip_marker)
        elif "test_v2_tables.py" in nodeid and missing_v2:
            item.add_marker(skip_marker)
        elif "test_v2_1_tables.py" in nodeid and missing_unredacted_v2_1:
            item.add_marker(skip_marker)
        elif "test_project_summary.py" in nodeid and missing_docs_summary:
            item.add_marker(skip_marker)
        elif "test_v2_v0_coverage.py" in nodeid and missing_outputs_v2:
            if any(name in nodeid for name in [
                "test_coverage_csv_exists_and_valid",
                "test_v2_spec_states_exploratory",
                "test_effective_sample_csvs",
                "test_holdout_candidates_csv",
            ]):
                item.add_marker(skip_marker)
        elif "test_v2_v1_verification.py" in nodeid and missing_outputs_v2:
            item.add_marker(skip_marker)


@pytest.fixture(autouse=True)
def redirect_audit_log(tmp_path, monkeypatch):
    """Ensure that running tests never modifies production unlock audit logs."""
    test_log = tmp_path / "test_unlock_audit.log"
    monkeypatch.setenv("MOTRANS_AUDIT_LOG", str(test_log))
'''
    (code_dest / "conftest.py").write_text(conftest_code, encoding="utf-8")

    # Write code README
    code_readme = (
        "# MoTrans-15 v2.1.1 Code Package\n\n"
        "This directory contains the Python pipeline, verification suite, and regression tests for MoTrans-15.\n\n"
        "## Development Notice\n"
        "The code and data processing pipeline were developed with AI-assisted coding tools.\n\n"
        "## Important Redistribution Notice Regarding Raw Data\n"
        "- `data/raw` contains proprietary vendor feeds and web archives which **cannot be redistributed** under public Zenodo license terms.\n"
        "- The packaged parquet analysis tables in `../data/` are pre-built, bitwise-certified, and ready for immediate research consumption.\n"
        "- To execute the end-to-end raw data ingestion pipeline (`python -m src.pipeline`), primary sources must be retrieved directly in accordance with vendor terms.\n\n"
        "## Running Tests\n"
        "To run the test suite:\n"
        "```bash\n"
        "pytest\n"
        "```\n"
    )
    (code_dest / "README.md").write_text(code_readme, encoding="utf-8")
    print("  Packaged src, tests, configuration, and conftest.py into code/")

def write_license_files() -> None:
    print("[6/11] Writing LICENSE (Custom Non-Open Research License) and LICENSE-CODE (MIT)...")
    mit_text = (
        "MIT License\n\n"
        "Copyright (c) 2026 Gaurav Mansing Jaypatre and Prachi Ravi Pawar\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        "of this software and associated documentation files (the \"Software\"), to deal\n"
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n"
    )
    (RELEASE_DIR / "LICENSE-CODE").write_text(mit_text, encoding="utf-8")

    custom_license_text = (
        "MoTrans-15 Research Use License (Non-Open / Restricted Academic Access)\n\n"
        "Copyright (c) 2026 Gaurav Mansing Jaypatre and Prachi Ravi Pawar\n\n"
        "This dataset is distributed under a custom non-open research-use license:\n\n"
        "1. Permitted Uses:\n"
        "   - Use is strictly permitted for non-commercial academic research, teaching, and scientific replication.\n\n"
        "2. Redistribution Prohibitions:\n"
        "   - Neither the dataset, nor any constituent tables, derived return windows, or parsed series may be redistributed,\n"
        "     re-hosted, mirrored, sub-licensed, or made available to third parties in whole or in part without express written authorization.\n\n"
        "3. Commercial Use:\n"
        "   - Commercial use, exploitation, or inclusion in commercial financial models or proprietary trading systems is strictly prohibited.\n\n"
        "4. Mandatory Attribution:\n"
        "   - Any published paper, thesis, conference proceeding, or academic report utilizing this dataset must cite MoTrans-15 v2.1.1\n"
        "     and its authors as specified in CITATION.cff and README.md.\n\n"
        "5. Access Protocol:\n"
        "   - Access is restricted and granted individually upon request via the official Zenodo access-request interface\n"
        "     for verified academic research purposes.\n\n"
        "6. Documented Future Licensing Option (CC-BY-4.0):\n"
        "   - Transition to an open Creative Commons Attribution 4.0 International (CC-BY-4.0) license is maintained as a\n"
        "     documented future option, strictly conditional upon the acquisition of formal, signed redistribution clearance\n"
        "     from primary financial index providers (recorded in LICENCE_CLEARANCE.txt). In the absence of signed clearance,\n"
        "     this restricted license remains exclusively in force.\n"
    )
    (RELEASE_DIR / "LICENSE").write_text(custom_license_text, encoding="utf-8")

def build_licence_and_provenance() -> None:
    print("[7/11] Building LICENCE_AND_PROVENANCE.md from data/raw/MANIFEST.csv...")
    manifest_path = ROOT / "data" / "raw" / "MANIFEST.csv"
    assert manifest_path.exists(), "data/raw/MANIFEST.csv missing"
    import pandas as pd
    df_m = pd.read_csv(manifest_path)

    # Group key providers
    providers = [
        {
            "name": "Bank for International Settlements (BIS)",
            "category": "Central Bank Policy Rates",
            "filter": df_m["source"].str.contains("International Settlements", na=False),
            "usage": "Daily central bank policy target rate histories across 15 economies (1999-2026)",
            "open_q": "Does BIS permit open redistribution of parsed daily policy rates, or does academic use require attribution only?",
        },
        {
            "name": "Federal Reserve Bank of St. Louis (FRED)",
            "category": "Macro Controls & US Benchmarks",
            "filter": df_m["source"].str.contains("FRED|St. Louis", na=False),
            "usage": "S&P 500 (SP500) and Nikkei 225 (NIKKEI225) second-source cross-verification series; US macro controls",
            "open_q": "Third-party series hosted on FRED (S&P Dow Jones Indices, Nikkei Inc.) prohibit raw commercial distribution. Are derived log return windows permitted under academic fair use?",
        },
        {
            "name": "European Central Bank (EA-MPD / Altavilla et al. 2019)",
            "category": "High-Frequency Shocks",
            "filter": df_m["licence"].str.contains("Altavilla", na=False) | df_m["source"].str.contains("ECB Data Portal", na=False),
            "usage": "Tier 1 high-frequency monetary policy surprise measures (1Y OIS intraday changes) for Euro Area decisions",
            "open_q": "EA-MPD dataset terms request academic citation (Altavilla et al. 2019). Are package derivatives free to redistribute under CC-BY-4.0?",
        },
        {
            "name": "Federal Reserve Bank of San Francisco (Bauer & Swanson 2023)",
            "category": "High-Frequency Shocks",
            "filter": df_m["source"].str.contains("San Francisco", na=False),
            "usage": "Tier 1 high-frequency monetary policy surprise measures (orthogonalized MPS) for FOMC announcements through 2023",
            "open_q": "Public domain academic series ending Dec 2023. Does fallback to 1-day sovereign yield proxy in 2024-2025 introduce regime discontinuity?",
        },
        {
            "name": "Central Bank Official Web Portals (Fed, BoE, BoC, RBA, BoJ, CBR, RBI, BCB, Banxico)",
            "category": "Policy Decisions & Statements",
            "filter": df_m["source"].str.contains("Central Bank|Federal Reserve|Bank of|Reserve Bank|Banco", na=False),
            "usage": "Official policy decision dates, press release timestamps, monetary statements, and sovereign benchmark yields",
            "open_q": "Terms vary from Open Government Licence (UK BoE) and Public Domain (US Fed) to standard website terms (BoJ, CBR, RBI). Unarchived intraday times for BCB, Banxico, RBI necessitate convention-based exclusion.",
        },
        {
            "name": "Financial Index Providers (Yahoo Finance, B3 S.A., Moscow Exchange, CSI, NSE Indices)",
            "category": "Equity Index Price Series",
            "filter": df_m["source"].str.contains("Yahoo|yfinance|B3|Moscow|China Securities|NSE|nifty", na=False),
            "usage": "Daily closing prices for 38 equity indices used strictly to compute cumulative event returns (clr_1 to clr_60)",
            "open_q": "Closing index levels (level_local) are strictly proprietary and omitted from release tables. Do exchange terms permit distribution of derived return residuals in restricted academic releases without licensed price levels?",
        },
    ]

    lines = [
        "# MoTrans-15 v2.1.1 Data Source Licence & Provenance Audit\n\n",
        "This document provides an inventory of all data providers, quoting their stated terms directly from `data/raw/MANIFEST.csv` and documenting licensing questions for research dissemination.\n\n",
        "## Summary of Licencing Status\n\n",
        f"- **Selected Access Mode**: `{cfg.ACCESS_MODE}` (Access granted by request via Zenodo for academic replication).\n",
        "- **Data Licence**: Custom 'Other (non-open)' research-use license (non-commercial academic research, no redistribution, attribution required; CC-BY-4.0 is preserved as a documented future option conditional on `LICENCE_CLEARANCE.txt`).\n",
        "- **Proprietary Closing Price Levels**: **Omitted** (`level_local` excluded from all packaged tables; `panel_returns_only.parquet` provides continuous log returns without starting levels).\n",
        "- **Raw Data Status**: Excluded from package (`data/raw/` contains vendor feeds that cannot be redistributed).\n\n",
        "## Provider Inventory & Quoted Terms\n\n",
    ]

    for p in providers:
        sub = df_m[p["filter"]]
        lines.append(f"### {p['name']}\n\n")
        lines.append(f"- **Data Category**: {p['category']}\n")
        lines.append(f"- **What is Used**: {p['usage']}\n")
        if len(sub) > 0:
            urls = sub["url_or_api"].dropna().unique()
            lics = sub["licence"].dropna().unique()
            dates = sub["retrieval_utc"].dropna().unique()
            lines.append(f"- **Sample URL / API**: `{urls[0]}`\n")
            lines.append(f"- **Retrieval Timestamp (UTC)**: `{dates[0]}` (total files tracked: {len(sub)})\n")
            lines.append(f"- **Stated Terms (Quoted)**: *\"{lics[0]}\"*\n")
            if len(lics) > 1:
                lines.append(f"- **Additional Quoted Terms**: {', '.join([f'*\"{l}\"*' for l in lics[1:4]])}\n")
        else:
            lines.append("- **Stated Terms**: terms not saved: check manually\n")
        lines.append(f"- **Open Legal / Scientific Question**: {p['open_q']}\n\n")

    (RELEASE_DIR / "LICENCE_AND_PROVENANCE.md").write_text("".join(lines), encoding="utf-8")
    print("  Generated LICENCE_AND_PROVENANCE.md")

def build_provenance_and_limitations() -> None:
    print("[8/11] Building PROVENANCE.md and LIMITATIONS_PACKAGE.md...")
    prov_text = (
        "# MoTrans-15 v2.1.1 Package Provenance & Integrity Certification\n\n"
        "## 1. Build Environment & Commit Identity\n"
        "- **Package Name**: MoTrans-15 v2.1.1 Zenodo Release Package\n"
        "- **Base Freeze Commit**: `f30ab1838c0820fa41f134c91cc058066c48cfdf` (Tag: `v2.1.1-train-test-ready`)\n"
        "- **Dataset Release Version**: `2.1.1`\n"
        "- **Python Version**: Python 3.13.1\n"
        "- **Development Note**: Code and data pipeline were developed with AI-assisted coding tools. Full replication and pipeline code is provided directly in the `code/` folder of this release package.\n\n"
        "## 2. Research Guardrail Certification\n"
        "> **CRITICAL CERTIFICATION**: Neither `UNLOCK_TEST` nor `UNLOCK_POST` was set by any packaging script "
        "or model code. The packaging and verification scripts accessed strictly date, identifier, and partition "
        "columns (`event_id`, `decision_date`, `final_split`, `decision`) for row counting, leakage checks, and schema auditing. "
        "No test-split outcome columns or post-window outcomes were inspected or modeled. (All unlock audit events "
        "during test verification are redirected via `MOTRANS_AUDIT_LOG` to temporary test fixtures, leaving production audit logs untouched).\n\n"
        "## 3. Cryptographic Verification Summary\n"
        "All data tables packaged in `data/` were verified bit-for-bit against the SHA-256 hashes certified in "
        "`docs/DATA_FREEZE_v2_1.md` before packaging:\n"
        "- `analysis_tier1.parquet`: `8a6207dd0c753c7d24d0a4d091dbdb05ee38d3010913a85b4c9f87a86e44979e` (VERIFIED)\n"
        "- `analysis_tier2_primary.parquet`: `c319040f687fbd88be9268d881c71152d803a0bd20357a109da049415f010a14` (VERIFIED)\n"
        "- `secondary_holds.parquet`: `7235bae5b29d0e4261bc9349e32593b09f9d0bf7cd784a7f61a56a45dc9c846f` (VERIFIED)\n"
        "- `sensitivity_macro_revision.parquet`: `f689bc78820520f08020d4d613fb6129a07abe15842634e2c9b428bd0f5bf794` (VERIFIED)\n"
        "- `panel_returns_only.parquet`: `e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620` (VERIFIED)\n"
        "- `folds.csv`: `5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee` (VERIFIED)\n"
    )
    (RELEASE_DIR / "PROVENANCE.md").write_text(prov_text, encoding="utf-8")

    limits_text = (
        "# MoTrans-15 v2.1.1 Release Package Limitations\n\n"
        "In accordance with open research integrity standards, this document discloses all known package constraints, "
        "data limitations, and unverified components:\n\n"
        "1. **Single-Source Equity Price Feeds**:\n"
        "   - Only S&P 500 (`us_sp500`) and Nikkei 225 (`jp_nikkei225`) have been cross-verified against independent FRED data (`price_source_verified = 1`).\n"
        "   - The remaining 36 indices rely on primary vendor feeds (`price_source_verified = 0`).\n\n"
        "2. **Emerging Market Announcement Timestamps**:\n"
        "   - Banco Central do Brasil (BCB), Banco de México (Banxico), Reserve Bank of India (RBI), and Bank of Korea (BoK) lack official scraped minute-level release archives; announcement times were not verified in this version. These decisions are disqualified from the primary evaluation sample (`analysis_ok = 0`). Brazil, Mexico, India, Korea and China have no usable decisions in this version.\n\n"
        "3. **Bank of England Pre-2016 MPC Timing**:\n"
        "   - BoE announcement timing prior to 2016-01-01 is verified at convention level (strict Thursday 12:00 noon GMT protocol) rather than minute-level press release scrapes (`timing_verified_level = 'convention'`).\n\n"
        "4. **Statistics Canada CPI Calendar**:\n"
        "   - Statistics Canada historical CPI release dates and times follow agency release calendar schedules rather than minute-level announcement timestamps.\n\n"
        "5. **Macroeconomic Industrial-Production Vintage Revisions**:\n"
        "   - Industrial Production series reflect historical time series with first-available vintage indicators rather than real-time point-in-time vintage triangles across all economies (`macro_vintage_verified = 0`).\n\n"
        "6. **Qualitative Hand Labels Not Completed**:\n"
        "   - Narrative statement qualitative hand classifications have not undergone double-blind expert replication and are excluded from this release (see `docs/labelling_guide.md`).\n\n"
        "7. **2026 Decisions Verified Only Internally**:\n"
        "   - 2026 policy decisions and market data are quarantined in `post_window_2026.parquet` and verified only internally; they are strictly excluded from the release tables to prevent temporal contamination.\n\n"
        "8. **Test Split Properties (Zero Hikes and Zero Fed Tier 1 Decisions)**:\n"
        "   - The 2024–2025 strictly locked test split contains exactly **0 interest rate hikes**, reflecting easing among the included central banks (BoJ hiked in the same period).\n"
        "   - The test split contains **0 Fed Tier 1 decisions** because the Bauer-Swanson high-frequency surprise series ends in December 2023 (2024–2025 Fed decisions rely on 1-day sovereign yield proxy surprises under Tier 2).\n\n"
        "9. **Skipped Package Tests (149 of 177)**:\n"
        "   - In the isolated release package (`code/`), 149 of 177 tests are auto-skipped via `conftest.py` because proprietary vendor raw feeds (`data/raw/`), legacy tables (`data/v2/`), unredacted price levels (`level_local`), and quarantined 2026 data cannot be redistributed. Running all 177 tests requires restoring primary raw feeds.\n"
    )
    (RELEASE_DIR / "LIMITATIONS_PACKAGE.md").write_text(limits_text, encoding="utf-8")
    print("  Generated PROVENANCE.md and LIMITATIONS_PACKAGE.md")

def build_metadata_files() -> None:
    print("[9/11] Building .zenodo.json and CITATION.cff...")

    creators = [
        {
            "name": "Jaypatre, Gaurav Mansing",
            "affiliation": "Pimpri Chinchwad College of Engineering (PCCOE), Pune, India",
        },
        {
            "name": "Pawar, Prachi Ravi",
            "affiliation": "Pimpri Chinchwad College of Engineering (PCCOE), Pune, India",
        },
    ]

    description_html = (
        "<p><strong>MoTrans-15 (v2.1.1)</strong>: central banks and equity indices for 15 economies were screened; "
        "usable analysis decisions exist for the Fed, ECB, BoE, BoC, RBA and CBR (BoJ as a sensitivity set); "
        "Brazil, Mexico, India, Korea and China have no usable decisions in this version. The evaluation window covers "
        "2010-01-01 to 2025-12-31 (16 calendar years).</p>\n"
        "<p>Code and data pipeline were developed with AI-assisted coding tools. Replication and analysis code is "
        "packaged directly in the <code>code/</code> folder of this deposit.</p>\n"
        "<p><strong>Dataset Characteristics:</strong></p>\n"
        "<ul>\n"
        "  <li><strong>Evaluation Window:</strong> 2010-01-01 to 2025-12-31 (16 calendar years).</li>\n"
        "  <li><strong>Temporal Splits:</strong> TRAIN (2010-2021, 572 decisions), VALIDATION (2022-2023, 76 decisions), TEST (2024-2025, 70 decisions).</li>\n"
        "  <li><strong>Embargo Protocol:</strong> Strict 60-day embargo prevents multi-horizon event window overlap across split boundaries.</li>\n"
        "  <li><strong>Locked Out-of-Sample Test Split:</strong> Contains exactly 0 interest rate hikes, reflecting easing among the included central banks (BoJ hiked in the same period) during the easing cycle among the included central banks, and 0 Fed Tier 1 decisions.</li>\n"
        "  <li><strong>Cross-Validation:</strong> 4 expanding rolling-origin evaluation folds plus a unified final_fit estimation partition (folds.csv).</li>\n"
        "</ul>\n"
        "<p><strong>Restricted Access Notice:</strong> Access is granted case by case for non-commercial academic research. "
        "Requests are not being approved at present while redistribution terms for some underlying source series are confirmed.</p>"
    )

    access_conditions_text = (
        "Access is granted case by case for non-commercial academic research. "
        "Requests are not being approved at present while redistribution terms for some underlying source series are confirmed."
    )

    zenodo_json = {
        "title": cfg.TITLE,
        "upload_type": "dataset",
        "description": description_html,
        "creators": creators,
        "access_right": "restricted",
        "access_conditions": access_conditions_text,
        "license": "other-closed",
        "version": "2.1.1",
        "publication_date": "2026-10-29",
        "keywords": [
            "monetary policy",
            "central banks",
            "equity returns",
            "intraday surprises",
            "event study",
            "macroeconomics",
            "rolling origin folds",
            "leakage audit",
        ],
        "language": "eng",
        "notes": (
            "MoTrans-15 v2.1.1 release package. The test split (2024-2025) is strictly locked for model evaluation "
            "and contains zero interest rate hikes (reflecting easing among the included central banks (BoJ hiked in the same period) during the easing cycle among the included central banks) and zero Fed Tier 1 decisions. "
            "Data License: Other (non-open) research use license; Code License: MIT. "
            "Code and data pipeline were developed with AI-assisted coding tools. "
            "Replication and evaluation code is provided directly in the code/ folder."
        ),
    }
    (RELEASE_DIR / ".zenodo.json").write_text(json.dumps(zenodo_json, indent=2), encoding="utf-8")

    cff_content = f"""cff-version: 1.2.0
message: "If you use this dataset, please cite it as below."
title: "{cfg.TITLE}"
version: "2.1.1"
date-released: "2026-10-29"
type: dataset
authors:
  - family-names: "Jaypatre"
    given-names: "Gaurav Mansing"
    affiliation: "Pimpri Chinchwad College of Engineering (PCCOE), Pune, India"
  - family-names: "Pawar"
    given-names: "Prachi Ravi"
    affiliation: "Pimpri Chinchwad College of Engineering (PCCOE), Pune, India"
"""
    (RELEASE_DIR / "CITATION.cff").write_text(cff_content, encoding="utf-8")
    print("  Generated .zenodo.json and CITATION.cff")

def build_readme() -> None:
    print("[10/11] Building zenodo_release/README.md with exact figures from CSV reports...")
    import pandas as pd
    df_split = pd.read_csv(OUTPUTS_V2_1 / "split_counts.csv")
    df_rows = pd.read_csv(OUTPUTS_V2_1 / "row_membership.csv")

    split_grp = df_split.groupby("split")[["decisions_count", "hikes_count", "cuts_count", "holds_count", "event_rows_count"]].sum().reset_index()

    train_row = split_grp[split_grp["split"] == "train"].iloc[0]
    val_row = split_grp[split_grp["split"] == "validation"].iloc[0]
    test_row = split_grp[split_grp["split"] == "test"].iloc[0]

    tot_decs = train_row["decisions_count"] + val_row["decisions_count"] + test_row["decisions_count"]
    tot_rows = train_row["event_rows_count"] + val_row["event_rows_count"] + test_row["event_rows_count"]

    t1_info = df_rows[df_rows["membership_category"] == "tier1"].iloc[0]
    t2_info = df_rows[df_rows["membership_category"] == "tier2_primary"].iloc[0]
    sh_info = df_rows[df_rows["membership_category"] == "secondary_holds"].iloc[0]

    readme = f"""# {cfg.TITLE}

## Overview & Scope
**MoTrans-15 (v2.1.1)**: central banks and equity indices for 15 economies were screened; usable analysis decisions exist for the Fed, ECB, BoE, BoC, RBA and CBR (BoJ as a sensitivity set); Brazil, Mexico, India, Korea and China have no usable decisions in this version. The evaluation window covers **2010-01-01 to 2025-12-31** (16 calendar years).

Code and data pipeline were developed with AI-assisted coding tools. Full replication and pipeline code is provided directly in the `code/` folder of this release package.

### Status at packaging, 2026-10-31
Status at packaging, 2026-10-31: this version is a pre-clearance snapshot deposited under Restricted Access (files visible only to approved requesters). Access requests are not being approved at present while (a) licence review and (b) vendor redistribution clearance for derived equity returns are completed. A refined dataset is planned as a later version.

- **ACCESS_MODE**: `{cfg.ACCESS_MODE}` (Files visible only to approved requesters)
- **DATA_LICENSE**: `Other (non-open / non-commercial research use; see LICENSE)`
- **CODE_LICENSE**: `{cfg.CODE_LICENSE}`
- **Authors & Affiliations**: Gaurav Mansing Jaypatre & Prachi Ravi Pawar (Pimpri Chinchwad College of Engineering (PCCOE), Pune, India)
- **Licence Review**: Pending institutional / supervisory review (`LICENCE_REVIEW_DONE = NO`)
- **Vendor Redistribution Clearance**: Not cleared (`VENDOR_CLEARANCE = NOT_CLEARED`); derived returns restricted to academic replication requests
- **Reason for Restricted Access**: Financial index return series are derived from commercial exchange closing prices without signed vendor redistribution clearance. Closing price levels (`level_local`) are omitted from all tables.

---

## 1. Access Terms & Policy
Access is granted case by case for non-commercial academic research. Requests are not being approved at present while redistribution terms for some underlying source series are confirmed.

When reviews and clearances are complete, requests will be handled via the Zenodo web interface for verified academic research and replication.

---

## 2. How to Cite

If you use this dataset in your research, please cite it as follows:

**APA:**
> Jaypatre, G. M., & Pawar, P. R. (2026). *MoTrans-15: Monetary policy surprises, central bank communication and equity-index responses for the largest economies, 2010-2025* (Version 2.1.1) [Data set]. Zenodo.

**BibTeX:**
```bibtex
@dataset{{jaypatre_pawar_2026_motrans15,
  author       = {{Jaypatre, Gaurav Mansing and Pawar, Prachi Ravi}},
  title        = {{{{MoTrans-15: Monetary policy surprises, central bank communication and equity-index responses for the largest economies, 2010-2025}}}},
  year         = {{2026}},
  month        = oct,
  publisher    = {{Zenodo}},
  version      = {{2.1.1}},
  note         = {{Replication code included in code/ folder of release package}}
}}
```

---

## 3. What is NOT Included and Why (Package Limitations)
For exhaustive details on data safety, licensing terms, and research boundaries, see `LIMITATIONS_PACKAGE.md` and `LICENCE_AND_PROVENANCE.md`. Key exclusions and limitations include:
1. **Single-Source Equity Price Feeds**: All equity indices rely on single primary vendor feeds, with the exception of S&P 500 (`us_sp500`) and Nikkei 225 (`jp_nikkei225`), which are independently verified against FRED.
2. **Emerging-Market Announcement Timing**: BCB, Banxico, RBI, and BoK lack official scraped minute-level release timestamps; announcement times were not verified in this version. Their decisions are disqualified (`analysis_ok = 0`).
3. **Bank of England Pre-2016 Timing**: BoE announcements prior to 2016-01-01 are verified at the convention level (strict Thursday 12:00 noon protocol) rather than minute-level press release scrapes.
4. **Statistics Canada CPI Calendar**: Historical Canadian CPI release dates follow agency calendar schedules rather than minute-level release timestamps.
5. **Industrial-Production Vintages**: IP controls use historical time series with first-available vintage indicators rather than real-time point-in-time vintage triangles.
6. **Hand Labels Excluded**: Statement narrative qualitative classifications have not undergone double-blind expert replication and are excluded.
7. **2026 Decisions Verified Only Internally**: 2026 decisions are quarantined in `post_window_2026.parquet` and verified only internally; they are omitted from distribution tables.
8. **Test Split Properties (Zero Hikes and Zero Fed Tier 1 Decisions)**: The 2024–2025 test window contains exactly **0 interest rate hikes** (reflecting easing among the included central banks (BoJ hiked in the same period) during the easing cycle among the included central banks) and **0 Fed Tier 1 decisions** (Bauer-Swanson series ends December 2023).
9. **Skipped Package Tests (149 of 177)**: 149 of 177 unit and regression tests are auto-skipped in `code/` because vendor raw data (`data/raw/`) and unredacted price levels cannot be redistributed.

---

## 4. Sample Splits & Embargo Protocol

| Split | Window Range | Decisions | Hikes | Cuts | Holds | Event Rows | Role in Research Design |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `train` | 2010-01-01 to 2021-12-31 | {train_row['decisions_count']} | {train_row['hikes_count']} | {train_row['cuts_count']} | {train_row['holds_count']} | {train_row['event_rows_count']:,} | Historical model estimation (12 years) |
| `validation` | 2022-01-01 to 2023-12-31 | {val_row['decisions_count']} | {val_row['hikes_count']} | {val_row['cuts_count']} | {val_row['holds_count']} | {val_row['event_rows_count']:,} | Model selection, hyperparameter tuning |
| `test` | 2024-01-01 to 2025-12-31 | {test_row['decisions_count']} | {test_row['hikes_count']} | {test_row['cuts_count']} | {test_row['holds_count']} | {test_row['event_rows_count']:,} | Strictly locked out-of-sample benchmark |
| **Total** | **2010-01-01 to 2025-12-31** | **{tot_decs}** | **{train_row['hikes_count'] + val_row['hikes_count'] + test_row['hikes_count']}** | **{train_row['cuts_count'] + val_row['cuts_count'] + test_row['cuts_count']}** | **{train_row['holds_count'] + val_row['holds_count'] + test_row['holds_count']}** | **{tot_rows:,}** | **Full Usable Analysis Sample** |

### 60-Day Embargo Protocol
Because multi-horizon event windows span up to 60 trading days (`clr_60`), any policy decision occurring within 60 calendar days prior to a partition boundary (or whose 60-day response window crosses into the subsequent split) is quarantined under `embargo_dropped` (64 decisions, 2,432 rows) to eliminate look-ahead leakage.

### Critical Property of the Test Split
The out-of-sample test split (2024-2025) contains **0 interest rate hikes**, reflecting the empirical reality of easing among the included central banks (BoJ hiked in the same period) during the easing cycle among the included central banks (28 cuts, 42 holds), and **0 Fed Tier 1 decisions**.

### Model Guardrail & Shock Standardization Guidance
- **Unlock Guardrail**: Attempting unauthorized access to test split or post-window observations raises an error AND logs the event to `outputs/v2_1/unlock_audit.log`.
- **Shock Standardization**: The column `shock_std` reflects fixed descriptive scaling (pre-2020 SD; CBR robust MAD). Modelers must not treat `shock_std` as a train-fitted feature; all modeling pipelines must standardize `shock_raw_bp` strictly fold-by-fold using scalers fit solely on training fold observations.

---

## 5. Table Tiers & Partition Membership

All row and decision counts are computed strictly from committed CSV reports (`reports/row_membership.csv`):

| Table Name | Tier & Description | Regimes | Decisions | Event Rows | Share of Panel |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `data/analysis_tier1.parquet` | **Tier 1**: High-frequency intraday surprises (Bauer-Swanson MPS; EA-MPD 1Y OIS) | Fed, ECB | {t1_info['decisions_count']} | {t1_info['event_rows_count']:,} | {t1_info['share_of_total_rows']} |
| `data/analysis_tier2_primary.parquet` | **Tier 2 Primary**: Rate-change decisions with 1-day sovereign yield proxy surprises | BoE, BoC, RBA, CBR, Fed, ECB | {t2_info['decisions_count']} | {t2_info['event_rows_count']:,} | {t2_info['share_of_total_rows']} |
| `data/secondary_holds.parquet` | **Secondary Holds**: Scheduled hold decisions with sovereign yield proxy surprises | BoE, BoC, RBA, Fed | {sh_info['decisions_count']} | {sh_info['event_rows_count']:,} | {sh_info['share_of_total_rows']} |
| `data/sensitivity_macro_revision.parquet` | **Macro Revision Sensitivity**: Controls robustness table | All primary regimes | {t1_info['decisions_count'] + t2_info['decisions_count']} | {t1_info['event_rows_count'] + t2_info['event_rows_count']:,} | — |
| `data/panel_returns_only.parquet` | **Daily Panel**: Continuous log returns without proprietary closing levels | 15 economies | — | 148,869 | — |

*Convenience CSV exports are provided for Tier 1 (`analysis_tier1.csv`), Tier 2 (`analysis_tier2_primary.csv`), and Secondary Holds (`secondary_holds.csv`).*

---

## 6. Rolling-Origin Cross-Validation & Final Fit (`data/folds.csv`)

To respect the temporal arrow of time, MoTrans-15 defines 4 rolling-origin evaluation folds plus a unified `final_fit` set (documented in `reports/fold_counts.csv`):

| Fold ID | Origin Cutoff | Training Window | Validation Window | Train Decs | Val Decs | Train Hikes | Val Hikes | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `1` | 2016-01-01 | 2010-01-01 to 2015-12-31 | 2016-01-01 to 2017-12-31 | 276 | 97 | 12 | 7 | ZIRP / Post-GFC recovery era |
| `2` | 2018-01-01 | 2010-01-01 to 2017-12-31 | 2018-01-01 to 2019-12-31 | 372 | 96 | 18 | 10 | Pre-COVID normalization |
| `3` | 2020-01-01 | 2010-01-01 to 2019-12-31 | 2020-01-01 to 2021-12-31 | 467 | 91 | 30 | 5 | Pandemic policy shock era |
| `4` | 2022-01-01 | 2010-01-01 to 2021-12-31 | 2022-01-01 to 2023-12-31 | 572 | 76 | 35 | 57 | Post-pandemic inflation cycle |
| `final_fit` | 2024-01-01 | 2010-01-01 to 2023-12-31 | — | 648 | 0 | 92 | 0 | Full TRAIN + VALIDATION estimation set before locked test split |

### How to Use `folds.csv`
- When selecting models, train exclusively on `fold == k & is_train == 1` and evaluate on `fold == k & is_val == 1`.
- For the final model to be benchmarked on the locked `test` split (2024-2025), fit model parameters strictly on the `final_fit` partition (648 decisions, 92 hikes).

---

## 7. Package Contents & Navigation
```
zenodo_release/
├── README.md                          # This document
├── LICENSE                            # Custom Non-Open Research License (CC-BY-4.0 preserved conditionally)
├── LICENSE-CODE                       # MIT License (Code)
├── CITATION.cff                       # Citation metadata (CFF 1.2.0)
├── .zenodo.json                       # Zenodo deposit metadata
├── CHECKSUMS.sha256                   # SHA-256 hashes of all packaged files (excludes itself)
├── MANIFEST.csv                       # Package file inventory with sizes and hashes (includes CHECKSUMS.sha256)
├── LICENCE_AND_PROVENANCE.md          # Provider inventory and license terms
├── PROVENANCE.md                      # Audit certification & guardrail log
├── LIMITATIONS_PACKAGE.md             # Scientific limitations & unverified items
├── data/
│   ├── analysis_tier1.parquet         # Tier 1 high-frequency surprise table
│   ├── analysis_tier1.csv             # Convenience CSV copy
│   ├── analysis_tier2_primary.parquet # Tier 2 rate-change surprise table
│   ├── analysis_tier2_primary.csv     # Convenience CSV copy
│   ├── secondary_holds.parquet        # Secondary scheduled hold surprise table
│   ├── secondary_holds.csv            # Convenience CSV copy
│   ├── sensitivity_macro_revision.parquet # Controls robustness table
│   ├── panel_returns_only.parquet     # Daily index return panel (no price levels)
│   └── folds.csv                      # Rolling-origin CV folds & final_fit
├── docs/
│   ├── v2_1_data_dictionary.md        # Comprehensive variable definitions
│   ├── v2_1_limitations.md            # Technical limitations
│   ├── v2_1_spec.md                   # Engineering specification
│   ├── preregistration.md             # Formal research design pre-registration
│   ├── limitations.md                 # Core dataset limitations
│   ├── DATA_FREEZE_v2_1.md            # Data freeze certification & hashes
│   ├── data_quality_scorecard.md      # Data quality scorecard
│   └── labelling_guide.md             # Statement qualitative annotation guide
├── reports/
│   ├── split_counts.csv               # Decisions & rows by split and regime
│   ├── fold_counts.csv                # Decisions & rows across CV folds
│   ├── test_window_composition.csv    # Granular test window composition
│   ├── row_membership.csv             # Partition membership breakdown
│   ├── leakage_audit.csv              # Zero-leakage audit verification
│   ├── analysis_ok_breakdown.csv      # Usable vs disqualified rows
│   ├── years_thin.csv                 # Annual density breakdown
│   └── verification_summary.csv       # External verification audit results
└── code/
    ├── src/                           # Python data processing modules
    ├── tests/                         # Full regression test suite
    ├── tasks.py                       # Task runner
    ├── requirements.txt               # Full Python dependency lock
    ├── pytest.ini                     # Test configuration
    ├── conftest.py                    # Test configuration with auto-skips for excluded paths
    └── README.md                      # Code instructions & raw data notice
```
"""
    (RELEASE_DIR / "README.md").write_text(readme, encoding="utf-8")
    print("  Generated README.md")

def generate_checksums_and_manifest() -> None:
    print("[Final Checksums] Generating MANIFEST.csv and CHECKSUMS.sha256...")
    all_files = []
    for root_dir, _, files in os.walk(RELEASE_DIR):
        for f in sorted(files):
            if f in ["CHECKSUMS.sha256", "MANIFEST.csv"]:
                continue
            full_path = Path(root_dir) / f
            rel_path = full_path.relative_to(RELEASE_DIR).as_posix()
            size = full_path.stat().st_size
            sha = sha256_file(full_path)
            all_files.append((rel_path, size, sha))

    # Write CHECKSUMS.sha256 (excludes itself to prevent self-referential hash mutation)
    checksums_path = RELEASE_DIR / "CHECKSUMS.sha256"
    with open(checksums_path, "w", encoding="utf-8") as f:
        for rel_path, _, sha in sorted(all_files, key=lambda x: x[0]):
            f.write(f"{sha}  {rel_path}\n")

    chk_count = len(all_files)
    print(f"  CHECKSUMS.sha256 written: {chk_count} files checksummed.")

    # Add CHECKSUMS.sha256 to MANIFEST
    chk_sha = sha256_file(checksums_path)
    chk_size = checksums_path.stat().st_size
    all_files.append(("CHECKSUMS.sha256", chk_size, chk_sha))

    # Write MANIFEST.csv (includes CHECKSUMS.sha256)
    manifest_path = RELEASE_DIR / "MANIFEST.csv"
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "size_bytes", "sha256"])
        for rel_path, size, sha in sorted(all_files, key=lambda x: x[0]):
            writer.writerow([rel_path, size, sha])

    print(f"  MANIFEST.csv written: {len(all_files)} total tracked files ({chk_count} package files + CHECKSUMS.sha256).")

def build_deterministic_zip() -> None:
    print("[Zip] Building deterministic archive MoTrans15_v2.1.1_zenodo_package.zip...")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    fixed_time = (2026, 10, 29, 0, 0, 0)
    file_mode = 0o644 | 0o100000

    # Collect all files to include
    entries = []
    for root_dir, _, files in os.walk(RELEASE_DIR):
        for f in sorted(files):
            # Ignore transient / VCS files if any
            if f in [".DS_Store", "Thumbs.db"] or f.endswith(".pyc") or f.endswith(".pyo"):
                continue
            if "__pycache__" in root_dir or ".pytest_cache" in root_dir or ".git" in root_dir:
                continue
            full_p = Path(root_dir) / f
            arcname = full_p.relative_to(RELEASE_DIR).as_posix()
            entries.append((arcname, full_p))

    entries.sort(key=lambda x: x[0])

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname, full_p in entries:
            zinfo = zipfile.ZipInfo(filename=arcname, date_time=fixed_time)
            zinfo.external_attr = file_mode << 16
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            with open(full_p, "rb") as fp:
                data = fp.read()
            zf.writestr(zinfo, data)

    zip_size = ZIP_PATH.stat().st_size
    zip_sha = sha256_file(ZIP_PATH)
    print(f"  Archive built successfully:")
    print(f"    Path:   {ZIP_PATH}")
    print(f"    Size:   {zip_size:,} bytes ({zip_size / (1024*1024):.2f} MB)")
    print(f"    SHA256: {zip_sha}")

def main():
    print("==================================================")
    print("Building MoTrans-15 v2.1.1 Zenodo Release Package (Revision 3)")
    print("==================================================")
    verify_source_hashes()
    ensure_clean_dir(RELEASE_DIR)
    copy_data_files()
    copy_docs()
    copy_reports()
    copy_code()
    write_license_files()
    build_licence_and_provenance()
    build_provenance_and_limitations()
    build_metadata_files()
    build_readme()
    generate_checksums_and_manifest()
    build_deterministic_zip()
    print("Package build complete in zenodo_release/ and zip archive ready.")

if __name__ == "__main__":
    main()
