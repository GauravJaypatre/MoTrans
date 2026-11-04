# MoTrans-15: Errata & Data Dictionary Clarifications (v2.1.1)

**Date**: 2026-11-04  
**Applies To**: `docs/v2_1_data_dictionary.md`, `docs/v2_1_spec.md`  
**Frozen Status**: Retained without modifying frozen tables or freeze certificates.

---

## 1. Provenance Level Classification (`timing_verified_level`)

### Data Dictionary Entry
In `docs/v2_1_data_dictionary.md` (Table 1):
```markdown
| `timing_verified_level` | string | `event` / `convention` / `none` | Verification audit | Independent timing provenance level. Pre-2016 BoE is `convention`; BCB/Banxico/RBI are `none`. |
```

### Empirical Distribution Across Committed Parquet Tables
An exhaustive audit across all 7 parquet files in `data/v2_1/` reveals the following exact distribution of `timing_verified_level`:

| Table Name | `convention` | `event` | `none` | Total Rows | Total Decisions | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `analysis_tier1.parquet` | 9,017 | 333 | 0 | 9,350 | 253 | `event` = 9 Fed intermeeting/crisis events; `convention` = 244 Fed/ECB decisions |
| `analysis_tier2_primary.parquet` | 4,851 | 0 | 0 | 4,851 | 130 | 100% `convention` (BoC: 28, BoE: 23, CBR: 39, Fed: 4, RBA: 36) |
| `secondary_holds.parquet` | 12,454 | 0 | 0 | 12,454 | 333 | 100% `convention` across all held regimes |
| `sensitivity_macro_revision.parquet` | 13,868 | 333 | 0 | 14,201 | 383 | Disjoint union of Tier 1 and Tier 2 primary |
| `excluded_rows.parquet` | 5,618 | 0 | 7,104 | 12,722 | 344 | `none` contains BCB, Banxico, RBI decisions; `convention` contains BoJ and thin years |
| `post_window_2026.parquet` | 407 | 0 | 740 | 1,147 | 31 | Quarantined 2026 observations |
| `panel.parquet` | 105,420 | 2,331 | 55,422 | 163,173 | — | Full panel matching event row provenance |

### Clarification & Errata Note
1. **Scope of `'none'`**: The level `'none'` does not appear in the four core analysis tables (`analysis_tier1`, `analysis_tier2_primary`, `secondary_holds`, `sensitivity_macro_revision`). It is present exclusively in `excluded_rows.parquet` and `post_window_2026.parquet`, covering emerging market central banks (BCB, Banxico, RBI) whose announcement timestamps were not verified in this release.
2. **Bank of England Coverage**: In `analysis_tier2_primary`, all 23 Bank of England decisions carry `timing_verified_level = "convention"`. While the 2016–present MPC operates under an official 12:00 noon Thursday announcement rule, granular per-event time-audit certificates were not assigned to individual BoE events; hence all BoE decisions are classified as `convention` rather than `event`.
3. **Federal Reserve `'event'` Designation**: The 9 decisions with `timing_verified_level = "event"` in Tier 1 correspond strictly to unscheduled FOMC actions and emergency rate cut announcements (e.g. 2020-03-03 and 2020-03-15) where exact minute-level release stamps were verified against official Federal Reserve press releases.
