# Package Archive History & Deployment Manifest

**Document ID**: `DOCS-ARCHIVE-001`  
**Package**: `MoTrans15_v2.2.0_zenodo_package.zip`  
**Date**: November 2026  
**Policy**: Only the final verified v2.2 release package is authorized for Zenodo deposit (`OFFICIAL RELEASE DEPOSIT`). All prior archives are strictly marked `DO NOT UPLOAD` or `SUPERSEDED`.

---

## 1. Archive Provenance Table

| Revision | Git Tag | Commit SHA | Archive File Size | SHA-256 Checksum | MD5 Checksum | Deposit Status | Rationale / Key Changes |
| :---: | :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| **r1** | `v2.1.1-zenodo-package` | `858a03f` | 8,541,209 bytes | `8ae4246e827f790e326a465e914f435e32e2a9fb5878a51b44e3cc7c97a0deb4` | `04467c6999a093be81a5a87ba025c8ee` | **DO NOT UPLOAD (SUPERSEDED)** | Initial package release. Contained self-referential zip hashes and unrefined placeholder terms. |
| **r2** | `v2.1.1-zenodo-package-r2` | `4d5b2c7` | ~8.54 MB | Multiple conflicting reported hashes: `b001d8df...` vs `b001d8d9...` | *Discrepant* | **DO NOT UPLOAD (UNVERIFIABLE)** | Refactored status wording. Rebuild from git history cannot reproduce exact zip hash due to untracked report state at packaging time. |
| **r3** | `v2.1.1-zenodo-package-r3` | `f771af7` | ~8.54 MB | Multiple conflicting reported hashes: `a577b34e...` vs `a577b344...` | *Discrepant* | **DO NOT UPLOAD (UNVERIFIABLE)** | Hardened pre-clearance restricted access notices. Rebuild from git history cannot reproduce exact zip hash due to untracked report state at packaging time. |
| **r4** | `v2.1.1-zenodo-package-r4` | `33352a8` | 8,545,963 bytes | `4b2a8448c662a0549da8b99415431abcef8e758e00ea8a16ae1b35c0d5e57e22` | `643cb75c018019fee7dda78cac1d4b0a` | **DO NOT UPLOAD (SUPERSEDED)** | Added v1 compliance diff, Nikkei T+1 convention details, and preliminary multiplicity corrections. |
| **r5** | `v2.1.1-zenodo-package-r5` | `402455f` | 8,546,255 bytes | `c43637c0cc5c208176fbc9236ac4110b2f1ff119a678211cf1e76e9f7753a67c` | `10c915381786d582357f8411509a481b` | **DO NOT UPLOAD (SUPERSEDED: CONTAINS SHOCK_STD)** | Superseded by v2.2. Included full-sample standardized `shock_std` trap and unaddressed outlier leverage distortion. |
| **v2.2.0** | `v2.2.0-package` | `cd0389d` | 8,635,256 bytes | `b6a8dd241c4ae1082c10a52c0e65d2061633d9c933b027a9f5ff0ec7ff7696ed` | `3746ec23ebf69e2a103c5339818db2a8` | **OFFICIAL RELEASE DEPOSIT** | **Official Zenodo Package**. Purges `shock_std` trap (adds `shock_raw_bp` and `shock_descriptive_2019`); adds `clr_1_clean` and timing indicators; formalizes Single Source of Truth `splits.csv` (718 decisions); separates Sample A ($N=70$) from Pristine Sample B ($N=56$, 0 hikes); documents CBR leverage sensitivity (119.10 bp conservative headline MDE after trimming top 1% vs 18.35 bp asymptotic); registers full 123-model multiplicity ledger; passes all 12 package gates. |

---

## 2. Integrity Certification
- All v2.2 tables are cryptographically frozen in `docs/DATA_FREEZE_v2_2.md`.
- No raw price levels (`level_local`) exist in any version of the archive.
- Revisions reflect strictly metadata, documentation, and verification hardening.
