"""MoTrans-15 v2.2.0 Zenodo Release Package Builder.

Builds the official v2.2 release package in zenodo_release_v22/ and packages it
into a deterministic zip archive MoTrans15_v2.2.0_zenodo_package.zip.
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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = ROOT / "zenodo_release_v22"
DATA_V2_2_RELEASE = ROOT / "data" / "v2_2" / "release"
DOCS = ROOT / "docs"
OUTPUTS_MODELING = ROOT / "outputs" / "modeling"
ZIP_PATH = ROOT / "MoTrans15_v2.2.0_zenodo_package.zip"

CERTIFIED_DATA_HASHES = {
    "analysis_tier1.parquet": "37ca577bb6520825428c6cefc185ca7f936e042f5547f400141dd8e8b344eb2c",
    "analysis_tier2_primary.parquet": "8127036a7d0e6fd2f92d1ae878e81e028e6b65646b68421ccb1ba14005f96ca2",
    "secondary_holds.parquet": "fce39831717f1403ff6463cf288b55ceb9e57aa08ab94d8ef78dc7d6de1706ec",
    "sensitivity_macro_revision.parquet": "d6daec49e2dd4fc304c6227df19508f44c32186077fa0b4849a6eb193969c58e",
    "panel_returns_only.parquet": "e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620",
    "splits.csv": "f362ad426f1d6dbfe7294d4320e932e89c39273f81f3154936022096bc52b1b6",
    "folds.csv": "5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def remove_readonly(func, path, exc):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, onerror=remove_readonly)
    path.mkdir(parents=True, exist_ok=True)


def build_package() -> None:
    print("=================================================================")
    print("BUILDING MOTRANS-15 V2.2 ZENODO RELEASE PACKAGE")
    print("=================================================================")

    ensure_clean_dir(RELEASE_DIR)

    # 1. Verify source hashes in data/v2_2/release/
    print("[1/9] Verifying source data hashes...")
    for fname, expected_hash in CERTIFIED_DATA_HASHES.items():
        fpath = DATA_V2_2_RELEASE / fname
        assert fpath.exists(), f"Missing release table: {fpath}"
        actual = sha256_file(fpath)
        assert actual == expected_hash, f"Hash mismatch for {fname}: got {actual}, expected {expected_hash}"

    # 2. Copy data files
    print("[2/9] Copying release data tables...")
    dest_data = RELEASE_DIR / "data"
    dest_data.mkdir(parents=True, exist_ok=True)
    for fname in CERTIFIED_DATA_HASHES:
        shutil.copy2(DATA_V2_2_RELEASE / fname, dest_data / fname)
    if (DATA_V2_2_RELEASE / "README.md").exists():
        shutil.copy2(DATA_V2_2_RELEASE / "README.md", dest_data / "README.md")

    # 3. Copy documentation
    print("[3/9] Packaging documentation...")
    dest_docs = RELEASE_DIR / "docs"
    dest_docs.mkdir(parents=True, exist_ok=True)
    doc_files = [
        "DATA_FREEZE_v2_2.md",
        "DATA_DICTIONARY_v2_1.md",
        "NATURE_READINESS.md",
        "V22_EVAL_PROTOCOL.md",
        "OPEN_RELEASE_PLAN.md",
        "INTEGRITY_AUDIT.md",
        "MANUSCRIPT_FRAMING.md",
        "LANGUAGE_PREANALYSIS_PLAN.md",
        "DEVIATIONS_LOG.md",
        "NEGATIVE_RESULTS.md",
    ]
    for df_name in doc_files:
        src_df = DOCS / df_name
        if src_df.exists():
            shutil.copy2(src_df, dest_docs / df_name)
    shutil.copy2(DOCS / "DATA_FREEZE_v2_2.md", RELEASE_DIR / "DATA_FREEZE_v2_2.md")

    # 4. Copy reports
    print("[4/9] Packaging model outputs and verification reports...")
    dest_reports = RELEASE_DIR / "reports"
    dest_reports.mkdir(parents=True, exist_ok=True)
    report_files = [
        "ledger.csv",
        "power_analysis_mde.csv",
        "pooled_influence_trim_sensitivity.csv",
        "window_timing_robustness.csv",
        "v1_compliance_diff.csv",
        "v1_blind_test_results.csv",
    ]
    for rf_name in report_files:
        src_rf = OUTPUTS_MODELING / rf_name
        if src_rf.exists():
            shutil.copy2(src_rf, dest_reports / rf_name)

    # 5. Copy code for isolated testing
    print("[5/9] Packaging reproducible code...")
    code_dest = RELEASE_DIR / "code"
    code_dest.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        ROOT / "src",
        code_dest / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    shutil.copytree(
        ROOT / "tests",
        code_dest / "tests",
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", "*.pyo",
            "test_project_summary.py", "test_release_parquet_matches_summary.py",
            "test_docs_match_csvs.py", "test_modeling_harness.py",
            "test_model_guard_integrity.py", "test_agreement.py",
            "test_inference_size.py", "test_v2_2_harness.py",
        ),
    )
    for f in ["tasks.py", "requirements.txt", "pytest.ini"]:
        shutil.copy2(ROOT / f, code_dest / f)

    # Copy conftest.py from zenodo_release/code/conftest.py
    shutil.copy2(ROOT / "zenodo_release" / "code" / "conftest.py", code_dest / "conftest.py")
    if (ROOT / "tests" / "conftest.py").exists():
        shutil.copy2(ROOT / "tests" / "conftest.py", code_dest / "tests" / "conftest.py")

    # 6. Build root package documents
    print("[6/9] Writing root metadata and license documents...")

    # .zenodo.json
    zenodo_json = {
        "title": "MoTrans-15: Monetary policy surprises and equity-index responses for the largest economies, 2010-2025 (v2.2.0)",
        "version": "2.2.0",
        "upload_type": "dataset",
        "publication_date": "2026-11-04",
        "description": "Cryptographically frozen multi-country benchmark dataset linking high-frequency and daily monetary policy surprises from six major central banks to international equity returns (2010-2025). Restricted access deposit due to commercial vendor copyright for financial index return series.",
        "access_right": "restricted",
        "access_conditions": "Available upon request for non-commercial academic research replication only, subject to index provider licensing compliance.",
        "creators": [
            {"name": "MoTrans-15 Research Consortium", "affiliation": "Academic Research Collaboration"}
        ],
        "keywords": [
            "monetary policy", "equity indices", "central bank surprises",
            "high-frequency identification", "international spillovers",
            "reproducible benchmark", "leakage prevention"
        ],
        "notes": "Version 2.2.0 incorporates fold-safe scaling, window timing filters (clr_1_clean), single source of truth splits architecture, robust influence handling, and Sample A/B test split partitions."
    }
    (RELEASE_DIR / ".zenodo.json").write_text(json.dumps(zenodo_json, indent=2), encoding="utf-8")

    # CITATION.cff
    citation_cff = """cff-version: 1.2.0
message: "If you use this dataset or benchmark software, please cite it as below."
title: "MoTrans-15: Monetary policy surprises and equity-index responses for the largest economies, 2010-2025"
version: 2.2.0
date-released: 2026-11-04
authors:
  - family-names: "Jaypatre"
    given-names: "Gaurav Mansing"
    affiliation: "Pimpri Chinchwad College of Engineering (PCCOE), Pune, India"
  - family-names: "Pawar"
    given-names: "Prachi Ravi"
    affiliation: "Pimpri Chinchwad College of Engineering (PCCOE), Pune, India"
abstract: "Standardized multi-country financial research benchmark providing monetary policy surprise series and equity index cumulative log return panels for six major central banks and 38 equity index series across 15 economies (2010-2025)."
repository-code: "https://github.com/motrans15/motrans-15"
"""
    (RELEASE_DIR / "CITATION.cff").write_text(citation_cff, encoding="utf-8")

    # LICENCE_AND_PROVENANCE.md
    licence_prov = """# MoTrans-15: Licensing, Provenance & Terms of Access

**Dataset Version**: 2.2.0  
**Release Tag**: `v2.2.0-package`  
**Deposit Type**: Zenodo Restricted Access (`access_right: restricted`)  

---

## 1. Dual Licensing Model

The MoTrans-15 research package operates under a strict dual licensing architecture:
1. **Maintainer Software & Metadata (Permissive Open Terms)**:
   - Pipeline code (`code/src/`), evaluation tests (`code/tests/`), runner (`tasks.py`), pre-analysis plans, data dictionaries, and summary reports are distributed under the **MIT License** and **CC-BY-4.0**.
2. **Derived Financial Index Return Tables (Restricted Research Access)**:
   - Tables containing continuous log return differences (`analysis_tier1.parquet`, `analysis_tier2_primary.parquet`, `secondary_holds.parquet`, `sensitivity_macro_revision.parquet`, `panel_returns_only.parquet`) are derived from commercial financial exchange closing price series.
   - All nominal price levels (`level_local`) have been strictly purged.
   - Due to commercial market data vendor terms, derived return tables are deposited under **Restricted Access** on Zenodo. No open redistribution (such as CC-BY) is permitted without explicit written licensor approval.

---

## 2. Status of Vendor Redistribution Clearance

- **Licensor Approvals**: **NO PERMISSION HAS BEEN GRANTED** by primary commercial exchange licensors to redistribute derived returns under an open license.
- **Deposit Policy**: The dataset remains permanently restricted on Zenodo unless commercial licensors grant formal exemptions.
"""
    (RELEASE_DIR / "LICENCE_AND_PROVENANCE.md").write_text(licence_prov, encoding="utf-8")

    # LIMITATIONS
    limitations_text = """# MoTrans-15: Scientific Limitations & Scope Boundaries

1. **Held-Out Test Split Regime Asymmetry**:
   The held-out test split (2024-2025) coincides exclusively with a global easing and hold regime (0 policy rate hikes). Out-of-sample validity for contractionary tightening cycles is unverified.
2. **High-Frequency Identification Boundaries**:
   Official high-frequency intraday surprises for the Federal Reserve terminate on December 13, 2023. Subsequent Fed surprises rely on daily Treasury yield changes.
3. **Daily Yield Proxy Noise**:
   Daily sovereign bond yield proxies contain ~67% non-monetary background market noise ($R^2 = 0.3305$ vs intraday HFI on common decisions).
4. **Market Session Alignment**:
   Approximately 21% of decision-index pairs announce during local equity trading hours (`announce_in_session == 1`), introducing pre-announcement trading hours into standard 1-day cumulative returns. Researchers must use `clr_1_clean` for clean out-of-session reactions.
5. **Statistical Power**:
   Robust headline Minimum Detectable Effect (MDE) for the pooled specification is 119.10 bp. Clean Tier 1 MDE is 101.27 bp.
6. **Outlier Leverage Sensitivity**:
   The emergency rate hike by the Bank of Russia (`cbr_2014-12-16`, +499 bp) exerts substantial econometric leverage. All headline models must report pre-declared sensitivity checks excluding this event.
7. **Qualitative Text Labels**:
   Human qualitative statement coding requires formal double annotation and adjudication. Qualitative features are quarantined until human annotation is completed.
"""
    (RELEASE_DIR / "LIMITATIONS").write_text(limitations_text, encoding="utf-8")
    (RELEASE_DIR / "LIMITATIONS.md").write_text(limitations_text, encoding="utf-8")

    # README.md
    readme_text = """# MoTrans-15: Monetary Policy Surprises and Equity-Index Responses (v2.2.0)

**Version**: 2.2.0  
**Deposit Type**: Zenodo Restricted Access  
**Release Tag**: `v2.2.0-package`  
**License**: MIT (Code) / Restricted Non-Open Research License (Derived Returns)  

---

## Critical Disclosure: Test Split Partitions (Sample A vs. Sample B)

The held-out evaluation window (2024–2025, 70 decisions) is partitioned into two distinct evaluation samples in `data/splits.csv`:

1. **Sample A: Full Test Split ($N=70$ decisions, 2,590 event rows)**:
   - Spans all qualifying policy decisions from 2024 to 2025 across Tier 1, Tier 2 Primary Actions, and Secondary Holds.
   - **Prior Exposure Notice**: Exactly **14 decisions (20.0%)**—all ECB Tier 1 announcements—had return outcomes evaluated during the pre-registered v1 confirmatory blind test (`src/modeling/run_v1_blind_test.py`, documented in `docs/INTEGRITY_AUDIT.md`).
   - Flagged in `splits.csv` as `read_by_prior_analysis == 1`.

2. **Sample B: Pristine Held-Out Test Split ($N=56$ decisions, 2,072 event rows)**:
   - Selected by filtering `splits.csv` for `split == 'test' and read_by_prior_analysis == 0`.
   - **Zero Prior Exposure**: Evaluates exclusively decisions with zero model exposure or outcome reads in prior project phases.
   - **Regime Limitation Notice**: Sample B contains **ZERO interest rate hikes** (0 tightening decisions). It comprises exclusively **holds (36 decisions) and rate cuts (20 decisions)** from Tier 2 central banks (BoE, BoC, RBA, CBR).

Researchers evaluating out-of-sample model generalization must report Sample A and Sample B side by side.

---

## Package Contents

- `data/`: Certified cryptographic release tables (all `level_local` price levels and `shock_std` traps removed).
- `docs/`: Data freeze certificates, pre-analysis plans, eval protocols, and audit logs.
- `reports/`: Complete 123-model results ledger, outlier leverage audits, and power analysis.
- `code/`: Reproducible estimation and testing pipeline.
"""
    (RELEASE_DIR / "README.md").write_text(readme_text, encoding="utf-8")

    # 7. Generate CHECKSUMS.sha256 and MANIFEST.csv
    print("[7/9] Generating CHECKSUMS.sha256 and MANIFEST.csv...")
    checksum_lines = []
    manifest_rows = []

    for p in sorted(RELEASE_DIR.rglob("*")):
        if p.is_file() and p.name not in ["CHECKSUMS.sha256", "MANIFEST.csv"]:
            rel = str(p.relative_to(RELEASE_DIR)).replace("\\", "/")
            fsize = p.stat().st_size
            h_val = sha256_file(p)
            checksum_lines.append(f"{h_val}  {rel}")

            desc = "Data table" if rel.startswith("data/") else ("Documentation" if rel.startswith("docs/") else ("Code" if rel.startswith("code/") else "Package Metadata"))
            lic = "Restricted Research" if rel.startswith("data/") and rel.endswith(".parquet") else "MIT / CC-BY-4.0"
            src = "MoTrans-15 Pipeline" if rel.startswith("data/") else "Authors"

            manifest_rows.append({
                "filename": rel,
                "size_bytes": fsize,
                "sha256": h_val,
                "description": desc,
                "source": src,
                "licence": lic,
            })

    (RELEASE_DIR / "CHECKSUMS.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    manifest_csv = RELEASE_DIR / "MANIFEST.csv"
    with open(manifest_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "size_bytes", "sha256", "description", "source", "licence"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    # 8. Deterministic Zip creation
    print("[8/9] Building deterministic zip archive...")
    fixed_time = (2026, 11, 4, 12, 0, 0)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(RELEASE_DIR.rglob("*")):
            if p.is_file():
                rel_path = str(p.relative_to(RELEASE_DIR)).replace("\\", "/")
                zinfo = zipfile.ZipInfo(rel_path, date_time=fixed_time)
                zinfo.external_attr = 0o644 << 16
                with open(p, "rb") as f_in:
                    zf.writestr(zinfo, f_in.read())

    zip_size = ZIP_PATH.stat().st_size
    zip_sha = sha256_file(ZIP_PATH)
    h_md5 = hashlib.md5(ZIP_PATH.read_bytes()).hexdigest()

    print(f"\nSuccessfully built {ZIP_PATH.name}:")
    print(f"  Size:   {zip_size:,} bytes")
    print(f"  SHA256: {zip_sha}")
    print(f"  MD5:    {h_md5}")

    print("\n[9/9] Package build complete.")


if __name__ == "__main__":
    build_package()
