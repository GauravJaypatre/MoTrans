# Package Archive History & Deployment Manifest

**Document ID**: `DOCS-ARCHIVE-001`  
**Package**: `MoTrans15_v2.1.1_zenodo_package.zip`  
**Date**: November 2026  
**Policy**: Only the final verified revision (r5) is authorized for Zenodo deposit. All superseded archives are strictly marked `DO NOT UPLOAD`.

---

## 1. Archive Provenance Table

| Revision | Git Tag | Commit SHA | Archive File Size | SHA-256 Checksum | MD5 Checksum | Deposit Status | Rationale / Key Changes |
| :---: | :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| **r1** | `v2.1.1-zenodo-package` | `858a03f` | 8,541,209 bytes | `8ae4246e827f790e326a465e914f435e32e2a9fb5878a51b44e3cc7c97a0deb4` | `04467c6999a093be81a5a87ba025c8ee` | **DO NOT UPLOAD (SUPERSEDED)** | Initial package release. Contained self-referential zip hashes and unrefined placeholder terms. |
| **r2** | `v2.1.1-zenodo-package-r2` | `4d5b2c7` | 8,542,104 bytes | `b001d8d9bfa332fa189c445a6ae5fbcaeb9055e82b7cf02a3a54b38bf213d283` | `7a13c9e992144d2d48c8bfa2e414c120` | **DO NOT UPLOAD (SUPERSEDED)** | Refactored status wording; removed branch/tag references from provenance. |
| **r3** | `v2.1.1-zenodo-package-r3` | `f771af7` | 8,543,012 bytes | `a577b34438343f7ec165aa8784fc2e4a66a7bca35df6f709117fe43dc13e3b38` | `81f8c67a3dfc4bc819b5d278b8a5d411` | **DO NOT UPLOAD (SUPERSEDED)** | Hardened pre-clearance restricted access notices and removed private repo GitHub links. |
| **r4** | `v2.1.1-zenodo-package-r4` | `33352a8` | 8,545,963 bytes | `4b2a8448c662a0549da8b99415431abcef8e758e00ea8a16ae1b35c0d5e57e22` | `643cb75c018019fee7dda78cac1d4b0a` | **DO NOT UPLOAD (SUPERSEDED)** | Added v1 compliance diff, Nikkei T+1 convention details, and preliminary multiplicity corrections. |
| **r5** | `v2.1.1-zenodo-package-r5` | *(Active HEAD)* | 8,546,255 bytes | `c43637c0cc5c208176fbc9236ac4110b2f1ff119a678211cf1e76e9f7753a67c` | `10c915381786d582357f8411509a481b` | **UPLOAD (OFFICIAL DEPOSIT)** | **Definitive Zenodo Package**. Includes Sample A ($N=70$) vs. Sample B ($N=56$ pristine) disclosure on page 1 of README; window timing robustness across in-session and out-of-session subsets; permutation distributions with exact $+1$ correction; resolution of cluster vs. wild bootstrap divergence; and full 119-model multiplicity ledger penalization. |

---

## 2. Integrity Certification
- All five revisions embed identical, bit-for-bit certified parquet tables from `DATA_FREEZE_v2_1.md`.
- No raw price levels (`level_local`) exist in any version of the archive.
- Revisions reflect strictly metadata, documentation, and verification hardening.
