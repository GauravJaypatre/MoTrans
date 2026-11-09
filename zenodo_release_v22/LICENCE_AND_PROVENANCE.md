# MoTrans-15: Licensing, Provenance & Terms of Access

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
