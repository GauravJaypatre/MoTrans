# Package Archive History & Deployment Manifest

**Document ID**: `DOCS-ARCHIVE-001`  
**Package**: `MoTrans15_v2.1.1_zenodo_package.zip`  
**Date**: November 2026  
**Policy**: Only the final verified revision (r5) is authorized for Zenodo deposit. All superseded archives are strictly marked `DO NOT UPLOAD`. Intermediate revisions whose artifacts cannot be bit-for-bit reproduced from clean git checkouts are classified as `DO NOT UPLOAD (UNVERIFIABLE)`.

---

## 1. Archive Provenance Table

| Revision | Git Tag | Commit SHA | Archive File Size | SHA-256 Checksum | MD5 Checksum | Deposit Status | Rationale / Key Changes |
| :---: | :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| **r1** | `v2.1.1-zenodo-package` | `858a03f` | 8,541,209 bytes | `8ae4246e827f790e326a465e914f435e32e2a9fb5878a51b44e3cc7c97a0deb4` | `04467c6999a093be81a5a87ba025c8ee` | **DO NOT UPLOAD (SUPERSEDED)** | Initial package release. Contained self-referential zip hashes and unrefined placeholder terms. |
| **r2** | `v2.1.1-zenodo-package-r2` | `4d5b2c7` | ~8.54 MB | Multiple conflicting reported hashes: `b001d8df...` vs `b001d8d9...` | *Discrepant* | **DO NOT UPLOAD (UNVERIFIABLE)** | Refactored status wording. Rebuild from git history cannot reproduce exact zip hash due to untracked report state at packaging time. |
| **r3** | `v2.1.1-zenodo-package-r3` | `f771af7` | ~8.54 MB | Multiple conflicting reported hashes: `a577b34e...` vs `a577b344...` | *Discrepant* | **DO NOT UPLOAD (UNVERIFIABLE)** | Hardened pre-clearance restricted access notices. Rebuild from git history cannot reproduce exact zip hash due to untracked report state at packaging time. |
| **r4** | `v2.1.1-zenodo-package-r4` | `33352a8` | 8,545,963 bytes | `4b2a8448c662a0549da8b99415431abcef8e758e00ea8a16ae1b35c0d5e57e22` | `643cb75c018019fee7dda78cac1d4b0a` | **DO NOT UPLOAD (SUPERSEDED)** | Added v1 compliance diff, Nikkei T+1 convention details, and preliminary multiplicity corrections. |
| **r5** | `v2.1.1-zenodo-package-r5` | `402455f` | 8,546,255 bytes | `c43637c0cc5c208176fbc9236ac4110b2f1ff119a678211cf1e76e9f7753a67c` | `10c915381786d582357f8411509a481b` | **UPLOAD (OFFICIAL DEPOSIT)** | **Definitive Zenodo Package**. Includes Sample A ($N=70$) vs. Sample B ($N=56$ pristine) disclosure on page 1 of README; window timing robustness across in-session and out-of-session subsets; permutation distributions with exact $+1$ correction; resolution of cluster vs. wild bootstrap divergence; and full 119-model multiplicity ledger penalization. |

---

## 2. Integrity Certification
- All five revisions embed identical, bit-for-bit certified parquet tables from `DATA_FREEZE_v2_1.md`.
- No raw price levels (`level_local`) exist in any version of the archive.
- Revisions reflect strictly metadata, documentation, and verification hardening.
