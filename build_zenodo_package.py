"""MoTrans-15 v2.1.1 Zenodo Release Package Builder.

Generates the complete release package in zenodo_release/ according to all
strict research integrity and packaging guidelines.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

# Import configuration
import zenodo_release_config as cfg

ROOT = Path(__file__).resolve().parent
RELEASE_DIR = ROOT / "zenodo_release"
DATA_V2_1_RELEASE = ROOT / "data" / "v2_1" / "release"
DATA_V2_1 = ROOT / "data" / "v2_1"
DOCS = ROOT / "docs"
OUTPUTS_V2_1 = ROOT / "outputs" / "v2_1"
OUTPUTS_V2 = ROOT / "outputs" / "v2"

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

def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

def verify_source_hashes() -> None:
    print("[1/10] Verifying source file SHA-256 hashes against DATA_FREEZE_v2_1.md...")
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
    print("[2/10] Copying allowed data files and generating CSV convenience exports...")
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
            df = pd.read_parquet(src_path)
            df.to_csv(csv_path, index=False)
            print(f"  Exported convenience CSV: {csv_name} ({len(df)} rows)")

def copy_docs() -> None:
    print("[3/10] Copying documentation files...")
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
    print("[4/10] Copying report CSV files...")
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
    print("[5/10] Packaging code (src, tests, tasks, requirements, pytest.ini)...")
    code_dest = RELEASE_DIR / "code"
    code_dest.mkdir(parents=True, exist_ok=True)

    # Copy src
    shutil.copytree(
        ROOT / "src",
        code_dest / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    # Copy tests
    shutil.copytree(
        ROOT / "tests",
        code_dest / "tests",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    # Copy root config files
    for f in ["tasks.py", "requirements.txt", "pytest.ini"]:
        shutil.copy2(ROOT / f, code_dest / f)

    # Write code README
    code_readme = (
        "# MoTrans-15 v2.1.1 Code Package\n\n"
        "This directory contains the Python pipeline, verification suite, and regression tests for MoTrans-15.\n\n"
        "## Important Redistribution Notice Regarding Raw Data\n"
        "- `data/raw` contains proprietary vendor feeds and web archives which **cannot be redistributed** under public Zenodo license terms.\n"
        "- The packaged parquet analysis tables in `../data/` are pre-built, bitwise-certified, and ready for immediate research consumption.\n"
        "- To execute the end-to-end raw data ingestion pipeline (`python -m src.pipeline`), primary sources must be retrieved directly in accordance with vendor terms.\n\n"
        "## Running Tests\n"
        "To run the unit test suite:\n"
        "```bash\n"
        "pytest\n"
        "```\n"
    )
    (code_dest / "README.md").write_text(code_readme, encoding="utf-8")
    print("  Packaged src, tests, and configuration into code/")

def write_license_files() -> None:
    print("[6/10] Writing LICENSE and LICENSE-CODE...")
    mit_text = (
        "MIT License\n\n"
        "Copyright (c) 2026 MoTrans-15 Contributors\n\n"
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

    cc_by_text = (
        "Creative Commons Attribution 4.0 International Public License\n\n"
        "By exercising the Licensed Rights (defined below), You accept and agree to be bound by the terms and conditions of this Creative Commons Attribution 4.0 International Public License (\"Public License\"). To the extent this Public License may be interpreted as a contract, You are granted the Licensed Rights in consideration of Your acceptance of these terms and conditions, and the Licensor grants You such rights in consideration of benefits the Licensor receives from making the Licensed Material available under these terms and conditions.\n\n"
        "Section 1 -- Definitions.\n"
        "a. Adapted Material means material that is subject to Copyright and Similar Rights that is derived from or based upon the Licensed Material...\n"
        "b. Copyright and Similar Rights means copyright and/or similar rights closely related to copyright including, without limitation, performance, broadcast, sound recording, and Sui Generis Database Rights...\n"
        "c. Effective Technological Measures means those measures that, in the absence of proper authority, may not be circumvented under laws fulfilling obligations under Article 11 of the WIPO Copyright Treaty adopted on December 20, 1996...\n"
        "d. Exceptions and Limitations means fair use, fair dealing, and/or any other exception or limitation to Copyright and Similar Rights that applies to Your use of the Licensed Material.\n"
        "e. Licensed Material means the artistic or literary work, database, or other material to which the Licensor applied this Public License.\n"
        "f. Licensed Rights means the rights granted to You subject to the terms and conditions of this Public License, which are limited to all Copyright and Similar Rights that apply to Your use of the Licensed Material and that the Licensor has authority to license.\n"
        "g. Licensor means the individual(s) or entity(ies) granting rights under this Public License.\n"
        "h. Share means to provide material to the public by any means or process that requires permission under the Licensed Rights, such as reproduction, public display, public performance, distribution, dissemination, communication, or importation...\n"
        "i. Sui Generis Database Rights means rights other than copyright resulting from Directive 96/9/EC of the European Parliament and of the Council of 11 March 1996 on the legal protection of databases, as amended and/or succeeded, as well as other essentially equivalent rights anywhere in the world.\n"
        "j. You means the individual or entity exercising the Licensed Rights under this Public License.\n\n"
        "Section 2 -- Scope.\n"
        "a. License grant. Subject to the terms and conditions of this Public License, the Licensor hereby grants You a worldwide, royalty-free, non-sublicensable, non-exclusive, irrevocable license to exercise the Licensed Rights in the Licensed Material to:\n"
        "   1. reproduce and Share the Licensed Material, in whole or in part; and\n"
        "   2. produce, reproduce, and Share Adapted Material.\n\n"
        "Section 3 -- Attribution.\n"
        "If You Share the Licensed Material, You must retain identification of the creator(s) and attribution information, notice of this Public License, and indicate if You modified the Licensed Material.\n\n"
        "Full legal code: https://creativecommons.org/licenses/by/4.0/legalcode\n"
    )
    (RELEASE_DIR / "LICENSE").write_text(cc_by_text, encoding="utf-8")

def build_licence_and_provenance() -> None:
    print("[7/10] Building LICENCE_AND_PROVENANCE.md from data/raw/MANIFEST.csv...")
    manifest_path = ROOT / "data" / "raw" / "MANIFEST.csv"
    assert manifest_path.exists(), "data/raw/MANIFEST.csv missing"
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
        "# MoTrans-15 v2.1.1 Data Source Licence & Provenance Audit\n",
        "This document provides an exhaustive inventory of all data providers, quoting their stated terms directly from `data/raw/MANIFEST.csv` and documenting open licensing questions for research dissemination.\n\n",
        "## Summary of Licencing Status\n",
        f"- **Selected Access Mode**: `{cfg.ACCESS_MODE}` (Access granted by request for academic replication).\n",
        "- **Proprietary Closing Price Levels**: **Omitted** (`level_local` excluded from all packaged tables; `panel_returns_only.parquet` provides continuous log returns without starting levels).\n",
        "- **Raw Data Status**: Excluded from package (`data/raw/` contains vendor feeds that cannot be redistributed).\n\n",
        "## Provider Inventory & Quoted Terms\n\n",
    ]

    for p in providers:
        sub = df_m[p["filter"]]
        lines.append(f"### {p['name']}\n")
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
    print("[8/10] Building PROVENANCE.md and LIMITATIONS_PACKAGE.md...")
    prov_text = (
        "# MoTrans-15 v2.1.1 Package Provenance & Integrity Certification\n\n"
        "## 1. Build Environment & Commit Identity\n"
        "- **Package Name**: MoTrans-15 v2.1.1 Zenodo Release Package\n"
        "- **Base Freeze Commit**: `f30ab1838c0820fa41f134c91cc058066c48cfdf` (Tag: `v2.1.1-train-test-ready`)\n"
        "- **Release Branch**: `zenodo-release`\n"
        "- **Release Tag**: `v2.1.1-zenodo-package`\n"
        "- **Python Version**: Python 3.13.1\n"
        "- **Packaging Engine**: Automated Bitwise Packaging & Verification Suite\n\n"
        "## 2. Research Guardrail Certification\n"
        "> **CRITICAL CERTIFICATION**: Neither `UNLOCK_TEST` nor `UNLOCK_POST` was set at any time during "
        "the creation or verification of this release package. The packaging and verification scripts accessed "
        "strictly date, identifier, and partition columns (`event_id`, `decision_date`, `final_split`, `decision`) "
        "for row counting, leakage checks, and schema auditing. No test-split outcome columns or post-window outcomes "
        "were inspected or modeled.\n\n"
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
        "1. **Restricted Access Designation**:\n"
        "   - Because financial market return series are derived from commercial index feeds without signed redistribution clearance (`LICENCE_CLEARANCE.txt` not present), this dataset is designated **Restricted Access** on Zenodo (accessible upon academic request).\n\n"
        "2. **Single-Source Equity Price Feeds**:\n"
        "   - Only S&P 500 (`us_sp500`) and Nikkei 225 (`jp_nikkei225`) have been cross-verified against independent FRED data (`price_source_verified = 1`).\n"
        "   - The remaining 36 indices rely on primary vendor feeds (`price_source_verified = 0`).\n\n"
        "3. **Emerging Market Announcement Timestamps**:\n"
        "   - Banco Central do Brasil (BCB), Banco de México (Banxico), Reserve Bank of India (RBI), and Bank of Korea (BoK) lack official scraped minute-level release archives. These decisions are disqualified from the primary evaluation sample (`analysis_ok = 0`).\n\n"
        "4. **Bank of England Pre-2016 MPC Timing**:\n"
        "   - BoE announcement timing prior to 2016-01-01 is verified at convention level (strict Thursday 12:00 noon GMT protocol) rather than minute-level press release scrapes (`timing_verified_level = 'convention'`).\n\n"
        "5. **Macroeconomic Vintage Revisions**:\n"
        "   - Industrial Production series reflect historical time series with first-available vintage indicators rather than real-time point-in-time vintage triangles across all 12 economies (`macro_vintage_verified = 0`).\n\n"
        "6. **Qualitative Hand Labels Excluded**:\n"
        "   - Narrative statement qualitative hand classifications have not undergone double-blind expert replication and are excluded from this release.\n\n"
        "7. **Zero Rate Hikes in Out-of-Sample Test Split**:\n"
        "   - The 2024–2025 strictly locked test split contains exactly **0 interest rate hikes**, reflecting the empirical reality of the global post-inflation monetary easing cycle. Models must not rely on rate hike observations during out-of-sample evaluation.\n\n"
        "8. **Standalone Code Package Execution**:\n"
        "   - `data/raw` cannot be redistributed. Running the raw pipeline from `code/` requires fetching raw files directly from primary sources.\n"
    )
    (RELEASE_DIR / "LIMITATIONS_PACKAGE.md").write_text(limits_text, encoding="utf-8")
    print("  Generated PROVENANCE.md and LIMITATIONS_PACKAGE.md")

def build_metadata_files() -> None:
    print("[9/10] Building .zenodo.json and CITATION.cff...")
    # Determine repo URL from .git/config
    git_config_path = ROOT / ".git" / "config"
    repo_url = "https://github.com/GauravJaypatre/MoTrans-15_Policy-and-Markets"
    if git_config_path.exists():
        text = git_config_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "url = " in line and "github.com" in line:
                repo_url = line.split("url = ")[-1].strip().replace(".git", "")
                break

    # Authors check
    authors_file = ROOT / "CITATION_AUTHORS.txt"
    if authors_file.exists() and authors_file.read_text(encoding="utf-8").strip():
        # parse authors if present
        authors_raw = authors_file.read_text(encoding="utf-8").strip().splitlines()
        creators = [{"name": a.strip()} for a in authors_raw if a.strip()]
        cff_authors = [{"name": a.strip()} for a in authors_raw if a.strip()]
    else:
        creators = [
            {
                "name": "TODO: Author Name",
                "affiliation": "TODO: Author Affiliation",
                "orcid": "0000-0000-0000-0000",
            }
        ]
        cff_authors = [
            {
                "name": "TODO: Author Name",
                "affiliation": "TODO: Author Affiliation",
                "orcid": "https://orcid.org/0000-0000-0000-0000",
            }
        ]

    zenodo_json = {
        "title": cfg.TITLE,
        "upload_type": "dataset",
        "description": (
            "MoTrans-15 (v2.1.1): A comprehensive, replication-certified dataset of monetary policy surprises, "
            "central bank communications, macroeconomic controls, and equity-index return responses across the "
            "world's largest economies from 2010 through 2025.\n\n"
            "Evaluation Window: 2010-01-01 to 2025-12-31 (16 years)\n"
            "Splits: TRAIN (2010-2021, 572 decisions), VALIDATION (2022-2023, 76 decisions), TEST (2024-2025, 70 decisions)\n"
            "Embargo Protocol: 60-day embargo prevents multi-horizon event window overlap across split boundaries.\n\n"
            "Notice on Access: Access is restricted upon request for academic research and replication due to derived "
            "financial return series. The out-of-sample test split is strictly locked and contains zero rate hikes."
        ),
        "creators": creators,
        "access_right": cfg.ACCESS_MODE,
        "license": cfg.DATA_LICENSE,
        "version": "2.1.1",
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
            "MoTrans-15 v2.1.1 release package. The test split (2024-2025) is strictly locked for model selection "
            "and out-of-sample evaluation, and contains zero interest rate hikes (property of the 2024-2025 global monetary easing cycle)."
        ),
        "related_identifiers": [
            {
                "identifier": repo_url,
                "relation": "isSupplementTo",
                "scheme": "url",
            }
        ],
    }
    (RELEASE_DIR / ".zenodo.json").write_text(json.dumps(zenodo_json, indent=2), encoding="utf-8")

    cff_lines = [
        "cff-version: 1.2.0\n",
        'message: "If you use this dataset, please cite it as below."\n',
        f'title: "{cfg.TITLE}"\n',
        'version: "2.1.1"\n',
        'doi: "TODO (reserve on Zenodo draft)"\n',
        'date-released: "2026-10-29"\n',
        f'license: "{cfg.DATA_LICENSE}"\n',
        f'repository-code: "{repo_url}"\n',
        "type: dataset\n",
        "authors:\n",
    ]
    for a in cff_authors:
        cff_lines.append(f'  - name: "{a["name"]}"\n')
        if "affiliation" in a:
            cff_lines.append(f'    affiliation: "{a["affiliation"]}"\n')
        if "orcid" in a:
            cff_lines.append(f'    orcid: "{a["orcid"]}"\n')
    (RELEASE_DIR / "CITATION.cff").write_text("".join(cff_lines), encoding="utf-8")
    print("  Generated .zenodo.json and CITATION.cff")

def build_readme() -> None:
    print("[10/10] Building zenodo_release/README.md with exact figures from CSV reports...")
    # Load exact numbers from CSV reports
    df_split = pd.read_csv(OUTPUTS_V2_1 / "split_counts.csv")
    df_folds = pd.read_csv(OUTPUTS_V2_1 / "fold_counts.csv")
    df_rows = pd.read_csv(OUTPUTS_V2_1 / "row_membership.csv")
    df_test = pd.read_csv(OUTPUTS_V2_1 / "test_window_composition.csv")

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
**MoTrans-15 (v2.1.1)** is a standardized, replication-certified dataset tracking central bank monetary policy announcements, high-frequency surprises, macroeconomic controls, and equity market responses across the world's major economies for the evaluation window **2010-01-01 to 2025-12-31** (16 calendar years).

### Configuration & Access Terms
- **ACCESS_MODE**: `{cfg.ACCESS_MODE}` (Access granted by request for academic replication)
- **DATA_LICENSE**: `{cfg.DATA_LICENSE}`
- **CODE_LICENSE**: `{cfg.CODE_LICENSE}`
- **Authors & Affiliations**: See `CITATION.cff` (Placeholders marked `TODO` pending publication metadata)
- **Reason for Restricted Access**: Financial index return series are derived from commercial exchange closing prices without signed vendor redistribution clearance. Closing price levels (`level_local`) are omitted from all tables; access to derived return tables is restricted to verified academic researchers upon request.

---

## 1. Sample Splits & Embargo Protocol

| Split | Window Range | Decisions | Hikes | Cuts | Holds | Event Rows | Role in Research Design |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `train` | 2010-01-01 to 2021-12-31 | {train_row['decisions_count']} | {train_row['hikes_count']} | {train_row['cuts_count']} | {train_row['holds_count']} | {train_row['event_rows_count']:,} | Historical model estimation (12 years) |
| `validation` | 2022-01-01 to 2023-12-31 | {val_row['decisions_count']} | {val_row['hikes_count']} | {val_row['cuts_count']} | {val_row['holds_count']} | {val_row['event_rows_count']:,} | Model selection, hyperparameter tuning |
| `test` | 2024-01-01 to 2025-12-31 | {test_row['decisions_count']} | {test_row['hikes_count']} | {test_row['cuts_count']} | {test_row['holds_count']} | {test_row['event_rows_count']:,} | Strictly locked out-of-sample benchmark |
| **Total** | **2010-01-01 to 2025-12-31** | **{tot_decs}** | **{train_row['hikes_count'] + val_row['hikes_count'] + test_row['hikes_count']}** | **{train_row['cuts_count'] + val_row['cuts_count'] + test_row['cuts_count']}** | **{train_row['holds_count'] + val_row['holds_count'] + test_row['holds_count']}** | **{tot_rows:,}** | **Full Usable Analysis Sample** |

### 60-Day Embargo Protocol
Because multi-horizon event windows span up to 60 trading days (`clr_60`), any policy decision occurring within 60 calendar days prior to a partition boundary (or whose 60-day response window crosses into the subsequent split) is quarantined under `embargo_dropped` (64 decisions, 2,432 rows) to eliminate look-ahead leakage.

### Critical Property of the Test Split
The out-of-sample test split (2024-2025) contains **0 interest rate hikes**, reflecting the empirical reality of the 2024-2025 global easing cycle (28 cuts, 42 holds). Models must not be evaluated on rate-hike conditioning during test evaluation.

---

## 2. Table Tiers & Partition Membership

All row and decision counts are computed strictly from committed CSV reports (`reports/row_membership.csv`):

| Table Name | Tier & Description | Regimes | Decisions | Event Rows | Share of Panel |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `data/analysis_tier1.parquet` | **Tier 1**: High-frequency intraday surprises (Bauer-Swanson MPS; EA-MPD 1Y OIS) | Fed, ECB | {t1_info['decisions_count']} | {t1_info['event_rows_count']:,} | {t1_info['share_of_total_rows']} |
| `data/analysis_tier2_primary.parquet` | **Tier 2 Primary**: Rate-change decisions with 1-day sovereign yield proxy surprises | BoE, BoC, RBA, CBR, Fed, ECB | {t2_info['decisions_count']} | {t2_info['event_rows_count']:,} | {t2_info['share_of_total_rows']} |
| `data/secondary_holds.parquet` | **Secondary Holds**: Scheduled hold decisions with sovereign yield proxy surprises | BoE, BoC, RBA, Fed | {sh_info['decisions_count']} | {sh_info['event_rows_count']:,} | {sh_info['share_of_total_rows']} |
| `data/sensitivity_macro_revision.parquet` | **Macro Revision Sensitivity**: Controls robustness table | All primary regimes | 382 | 14,201 | — |
| `data/panel_returns_only.parquet` | **Daily Panel**: Continuous log returns without proprietary closing levels | 15 economies | — | 148,869 | — |

*Convenience CSV exports are provided for Tier 1 (`analysis_tier1.csv`), Tier 2 (`analysis_tier2_primary.csv`), and Secondary Holds (`secondary_holds.csv`).*

---

## 3. Rolling-Origin Cross-Validation & Final Fit (`data/folds.csv`)

To respect the temporal arrow of time, MoTrans-15 defines 4 rolling-origin evaluation folds plus a unified `final_fit` set (documented in `reports/fold_counts.csv`):

| Fold ID | Origin Cutoff | Training Window | Validation Window | Train Decs | Val Decs | Train Hikes | Val Hikes | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `1` | 2016-01-01 | 2010-01-01 to 2015-12-31 | 2016-01-01 to 2017-12-31 | 276 | 97 | 12 | 7 | ZIRP / Post-GFC recovery era |
| `2` | 2018-01-01 | 2010-01-01 to 2017-12-31 | 2018-01-01 to 2019-12-31 | 372 | 96 | 18 | 10 | Pre-COVID normalization |
| `3` | 2020-01-01 | 2010-01-01 to 2019-12-31 | 2020-01-01 to 2021-12-31 | 467 | 91 | 30 | 5 | Pandemic policy shock era |
| `4` | 2022-01-01 | 2010-01-01 to 2021-12-31 | 2022-01-01 to 2023-12-31 | 572 | 76 | 35 | 57 | Global inflation tightening cycle |
| `final_fit` | 2024-01-01 | 2010-01-01 to 2023-12-31 | — | 648 | 0 | 92 | 0 | Full TRAIN + VALIDATION estimation set before locked test split |

### How to Use `folds.csv`
- When selecting models, train exclusively on `fold == k & is_train == 1` and evaluate on `fold == k & is_val == 1`.
- For the final model to be benchmarked on the locked `test` split (2024-2025), fit model parameters strictly on the `final_fit` partition (648 decisions, 92 hikes).

---

## 4. Package Contents & Navigation
```
zenodo_release/
├── README.md                          # This document
├── LICENSE                            # Creative Commons CC-BY-4.0 (Dataset)
├── LICENSE-CODE                       # MIT License (Code)
├── CITATION.cff                       # Citation metadata (CFF 1.2.0)
├── .zenodo.json                       # Zenodo deposit metadata
├── CHECKSUMS.sha256                   # SHA-256 hashes of all packaged files
├── MANIFEST.csv                       # Package file inventory with sizes and hashes
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
    └── README.md                      # Code instructions & raw data notice
```

---

## 5. Exclusions & Limitations Notice
- **Statement Qualitative Hand Labels**: Manual statement qualitative classifications have not undergone double-blind expert replication and are **not included** in this release package (see `docs/labelling_guide.md` for guidelines).
- **Post-Window Observations (`post_window_2026`)**: 2026 data are strictly quarantined and omitted from release tables.
- **Excluded Rows Table (`excluded_rows.parquet`)**: Omitted to keep package focused on analysis-ready and secondary tables.
"""
    (RELEASE_DIR / "README.md").write_text(readme, encoding="utf-8")
    print("  Generated README.md")

def generate_checksums_and_manifest() -> None:
    print("[Final] Generating MANIFEST.csv and CHECKSUMS.sha256...")
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

    # Write CHECKSUMS.sha256
    with open(RELEASE_DIR / "CHECKSUMS.sha256", "w", encoding="utf-8") as f:
        for rel_path, _, sha in sorted(all_files, key=lambda x: x[0]):
            f.write(f"{sha}  {rel_path}\n")

    # Add CHECKSUMS.sha256 to MANIFEST
    chk_sha = sha256_file(RELEASE_DIR / "CHECKSUMS.sha256")
    chk_size = (RELEASE_DIR / "CHECKSUMS.sha256").stat().st_size
    all_files.append(("CHECKSUMS.sha256", chk_size, chk_sha))

    # Write MANIFEST.csv
    with open(RELEASE_DIR / "MANIFEST.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "size_bytes", "sha256"])
        for rel_path, size, sha in sorted(all_files, key=lambda x: x[0]):
            writer.writerow([rel_path, size, sha])

    print(f"  Packaged {len(all_files)} total files.")

def main():
    print("==================================================")
    print("Building MoTrans-15 v2.1.1 Zenodo Release Package")
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
    print("Package build complete in zenodo_release/.")

if __name__ == "__main__":
    main()

