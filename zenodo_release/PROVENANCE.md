# MoTrans-15 v2.1.1 Package Provenance & Integrity Certification

## 1. Build Environment & Commit Identity
- **Package Name**: MoTrans-15 v2.1.1 Zenodo Release Package
- **Base Freeze Commit**: `f30ab1838c0820fa41f134c91cc058066c48cfdf` (Tag: `v2.1.1-train-test-ready`)
- **Release Branch**: `zenodo-release`
- **Release Tag**: `v2.1.1-zenodo-package-r3`
- **Python Version**: Python 3.13.1
- **Development Note**: Code and data pipeline were developed with AI-assisted coding tools.

## 2. Research Guardrail Certification
> **CRITICAL CERTIFICATION**: Neither `UNLOCK_TEST` nor `UNLOCK_POST` was set by any packaging script or model code. The packaging and verification scripts accessed strictly date, identifier, and partition columns (`event_id`, `decision_date`, `final_split`, `decision`) for row counting, leakage checks, and schema auditing. No test-split outcome columns or post-window outcomes were inspected or modeled. (All unlock audit events recorded during verification were triggered exclusively by unit tests in `tests/test_v2_1_tables.py` validating that the model guard security lock raises `PermissionError` when unset; see `outputs/v2_1/unlock_audit_packaging.log`).

## 3. Cryptographic Verification Summary
All data tables packaged in `data/` were verified bit-for-bit against the SHA-256 hashes certified in `docs/DATA_FREEZE_v2_1.md` before packaging:
- `analysis_tier1.parquet`: `8a6207dd0c753c7d24d0a4d091dbdb05ee38d3010913a85b4c9f87a86e44979e` (VERIFIED)
- `analysis_tier2_primary.parquet`: `c319040f687fbd88be9268d881c71152d803a0bd20357a109da049415f010a14` (VERIFIED)
- `secondary_holds.parquet`: `7235bae5b29d0e4261bc9349e32593b09f9d0bf7cd784a7f61a56a45dc9c846f` (VERIFIED)
- `sensitivity_macro_revision.parquet`: `f689bc78820520f08020d4d613fb6129a07abe15842634e2c9b428bd0f5bf794` (VERIFIED)
- `panel_returns_only.parquet`: `e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620` (VERIFIED)
- `folds.csv`: `5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee` (VERIFIED)
