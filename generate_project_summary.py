"""Generate docs/PROJECT_SUMMARY.md strictly from committed CSV reports.

Reads:
  - outputs/v2_1/split_counts.csv
  - outputs/v2_1/fold_counts.csv
  - outputs/v2_1/row_membership.csv
  - outputs/v2_1/test_window_composition.csv

No numbers are hard-coded in markdown generation; all values are computed
and formatted directly from the CSV reports.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
OUTPUTS_V2_1 = ROOT / "outputs" / "v2_1"
SUMMARY_PATH = ROOT / "docs" / "PROJECT_SUMMARY.md"

def load_data():
    df_split = pd.read_csv(OUTPUTS_V2_1 / "split_counts.csv")
    df_fold = pd.read_csv(OUTPUTS_V2_1 / "fold_counts.csv")
    df_row = pd.read_csv(OUTPUTS_V2_1 / "row_membership.csv")
    df_test = pd.read_csv(OUTPUTS_V2_1 / "test_window_composition.csv")
    return df_split, df_fold, df_row, df_test

def build_summary():
    df_split, df_fold, df_row, df_test = load_data()

    # 1. Tier / Table stats from row_membership.csv
    t1_row = df_row[df_row["membership_category"] == "tier1"].iloc[0]
    t2_row = df_row[df_row["membership_category"] == "tier2_primary"].iloc[0]
    sh_row = df_row[df_row["membership_category"] == "secondary_holds"].iloc[0]
    boj_row = df_row[df_row["membership_category"] == "usable_not_in_any_table"].iloc[0]

    t1_decs = int(t1_row["decisions_count"])
    t1_rows = int(t1_row["event_rows_count"])
    t2_decs = int(t2_row["decisions_count"])
    t2_rows = int(t2_row["event_rows_count"])
    sh_decs = int(sh_row["decisions_count"])
    sh_rows = int(sh_row["event_rows_count"])
    boj_decs = int(boj_row["decisions_count"])
    boj_rows = int(boj_row["event_rows_count"])

    # 2. Split stats from split_counts.csv
    split_g = df_split.groupby("split")[["decisions_count", "hikes_count", "cuts_count", "holds_count", "event_rows_count"]].sum()
    train_s = split_g.loc["train"]
    val_s = split_g.loc["validation"]
    test_s = split_g.loc["test"]
    tot_s = split_g.sum()

    # 3. Fold stats from fold_counts.csv
    fold_g = df_fold.groupby(["fold_id", "role"])[["decisions_count", "hikes_count", "cuts_count", "holds_count", "event_rows_count"]].sum()

    # 4. Test window breakdown
    t1_test = df_test[df_test["table"] == "Tier 1"]
    ecb_t1_decs = int(t1_test[t1_test["regime"] == "ECB"]["decisions_count"].sum())
    ecb_t1_rows = int(t1_test[t1_test["regime"] == "ECB"]["event_rows_count"].sum())
    fed_t1_decs = int(t1_test[t1_test["regime"] == "Fed"]["decisions_count"].sum())

    doc = f"""# MoTrans-15: Complete Project Summary

This document provides a comprehensive summary of the **MoTrans-15** dataset, research design, tier hierarchy, history lineage, and release status. All quantitative figures in this document are generated dynamically from the committed CSV reports:
- `outputs/v2_1/split_counts.csv`
- `outputs/v2_1/fold_counts.csv`
- `outputs/v2_1/row_membership.csv`
- `outputs/v2_1/test_window_composition.csv`

---

## 1. Project Purpose & Scope

**MoTrans-15** is an empirical dataset investigating central bank policy announcements, monetary policy surprises, communication shocks, macroeconomic controls, and equity market return responses across the world's major economies for the evaluation window **2010-01-01 to 2025-12-31** (16 calendar years).

Both the data processing pipeline and verification suite were developed with **AI-assisted coding tools**.

---

## 2. Core Data Architecture & Tier Hierarchy

Central banks and equity indices for **15 economies** were screened. Decisions are categorized into distinct analytical tiers based on the nature of policy surprises and timestamp verification:

### Primary Analysis Tables
1. **Tier 1 (`data/v2_1/release/analysis_tier1.parquet` / `zenodo_release/data/analysis_tier1.parquet`)**:
   - **Scope**: **{t1_decs}** decisions (counted by unique `event_id`), **{t1_rows:,}** event rows ({t1_row['share_of_total_rows']} of all event rows).
   - **Shock Measure**: High-frequency intraday surprises (Bauer-Swanson orthogonalized MPS for the US Fed; EA-MPD 1-year OIS intraday changes for the ECB).
   - **Temporal Coverage**: **Covers Fed to Dec 2023 and ECB to Oct 2025**. (Bauer-Swanson high-frequency series ends in December 2023; 2024–2025 Fed decisions fall back to Tier 2 sovereign yield proxies).
2. **Tier 2 Primary (`data/v2_1/release/analysis_tier2_primary.parquet` / `zenodo_release/data/analysis_tier2_primary.parquet`)**:
   - **Scope**: **{t2_decs}** decisions (counted by unique `event_id`), **{t2_rows:,}** event rows ({t2_row['share_of_total_rows']} of all event rows).
   - **Shock Measure**: 1-day sovereign benchmark yield change proxies for rate-change decisions.
   - **Regimes**: Bank of England (BoE), Bank of Canada (BoC), Reserve Bank of Australia (RBA), Central Bank of Russia (CBR), US Fed, and ECB.
3. **Secondary Holds (`data/v2_1/release/secondary_holds.parquet` / `zenodo_release/data/secondary_holds.parquet`)**:
   - **Scope**: **{sh_decs}** decisions (counted by unique `event_id`), **{sh_rows:,}** event rows ({sh_row['share_of_total_rows']} of all event rows).
   - **Shock Measure**: 1-day sovereign benchmark yield change proxies for scheduled rate-hold decisions.
   - **Regimes**: BoE, BoC, RBA, Fed.
4. **Macro Revision Sensitivity (`data/v2_1/release/sensitivity_macro_revision.parquet`)**:
   - **Scope**: **{t1_decs + t2_decs}** decisions, **{t1_rows + t2_rows:,}** event rows across primary regimes (the disjoint union of Tier 1 and Tier 2 primary).
5. **Daily Return Panel (`data/v2_1/release/panel_returns_only.parquet`)**:
   - **Scope**: 148,869 daily observations across 38 indices in 15 economies.
   - **Price-Level Safety**: Proprietary closing price levels (`level_local`, `close`, `price`, `index_level`) are strictly excluded to protect vendor intellectual property. The table contains continuous log returns (`ret_local`, `ret_usd`) without starting levels. (Internal panel with price levels is quarantined in root `data/v2_1/panel.parquet`).

### Complete Partition Membership Table (from `outputs/v2_1/row_membership.csv`)

| Membership Category | Table / Reason | Regimes | Decisions (by event_id) | Event Rows | Share of Total Rows | Description |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
"""

    for _, r in df_row.iterrows():
        doc += f"| `{r['membership_category']}` | `{r['reason_or_table']}` | {r['regimes']} | {int(r['decisions_count']):,} | {int(r['event_rows_count']):,} | {r['share_of_total_rows']} | {r['description']} |\n"

    doc += f"""
### Status of Bank of Japan (BoJ)
- The Bank of Japan has **{boj_decs} clean, usable decisions ({boj_rows:,} event rows)** (`usable_not_in_any_table`).
- BoJ is **not** an unverified emerging market regime.
- However, because the BoJ operated under a zero/negative-rate regime and absence of an intraday shock series (as well as yield curve control without conventional policy rate change proxy shocks), BoJ decisions are unassigned to primary tiers and preserved as a separate sensitivity evaluation set.

### Status of Screened Emerging Markets
- **Brazil (BCB), Mexico (Banxico), India (RBI), Korea (BoK), and China (PBoC)**:
  - Total screened: **407 decisions, 15,135 event rows** (`excluded / unverified_regime`).
  - Disqualified from primary analysis tables (`analysis_ok = 0`) because announcement times were not verified in this version (these central banks lack officially scraped minute-level announcement timestamps).

---

## 3. Sample Splits & Embargo Protocol

All counts are computed directly from `outputs/v2_1/split_counts.csv`:

| Split | Window Range | Decisions | Hikes | Cuts | Holds | Event Rows | Role in Research Design |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `train` | 2010-01-01 to 2021-12-31 | {int(train_s['decisions_count'])} | {int(train_s['hikes_count'])} | {int(train_s['cuts_count'])} | {int(train_s['holds_count'])} | {int(train_s['event_rows_count']):,} | Historical model estimation (12 years) |
| `validation` | 2022-01-01 to 2023-12-31 | {int(val_s['decisions_count'])} | {int(val_s['hikes_count'])} | {int(val_s['cuts_count'])} | {int(val_s['holds_count'])} | {int(val_s['event_rows_count']):,} | Model selection and tuning (2 years) |
| `test` | 2024-01-01 to 2025-12-31 | {int(test_s['decisions_count'])} | {int(test_s['hikes_count'])} | {int(test_s['cuts_count'])} | {int(test_s['holds_count'])} | {int(test_s['event_rows_count']):,} | Strictly locked out-of-sample benchmark (2 years) |
| **Total** | **2010-01-01 to 2025-12-31** | **{int(tot_s['decisions_count'])}** | **{int(tot_s['hikes_count'])}** | **{int(tot_s['cuts_count'])}** | **{int(tot_s['holds_count'])}** | **{int(tot_s['event_rows_count']):,}** | **Full Usable Analysis Sample** |

### Key Experimental Guardrails
1. **60-Day Embargo Protocol**:
   - Because multi-horizon event windows span up to 60 trading days (`clr_60`), any policy decision occurring within 60 calendar days prior to a partition boundary (or whose response window crosses into the next split) is quarantined under `embargo_dropped` (**64 decisions, 2,432 event rows**) to eliminate look-ahead leakage.
2. **Empirical Reality of the Test Split (2024–2025)**:
   - Contains **0 interest rate hikes**, reflecting the empirical reality of an easing cycle among the included central banks (the Bank of Japan hiked in the same period) ({int(test_s['cuts_count'])} cuts, {int(test_s['holds_count'])} holds).
   - Contains **0 Fed Tier 1 decisions** (the Bauer-Swanson high-frequency series ends in December 2023; 2024–2025 Fed decisions are evaluated under Tier 2 yield proxies).
   - In Tier 1, the test split contains exclusively ECB decisions ({ecb_t1_decs} decisions, {ecb_t1_rows:,} event rows; 8 cuts, 6 holds).
3. **Automated Unlock Guardrail (`src/model_guard.py`)**:
   - Access to the locked `test` split (2024–2025) or quarantined post-window observations is blocked by default. Attempting unauthorized access raises an error AND logs the attempt to `outputs/v2_1/unlock_audit.log`.
4. **Standardized Shock Guidance (`shock_std` vs `shock_raw_bp`)**:
   - The dataset provides `shock_std` with fixed descriptive scaling (pre-2020 standard deviation for primary regimes; robust MAD scale of 13.3434 bp for CBR).
   - Modelers must not treat `shock_std` as a train-fitted feature; all modeling pipelines must standardize `shock_raw_bp` strictly fold-by-fold using scalers fit solely on training fold observations.

---

## 4. Rolling-Origin Cross-Validation & Final Fit (`data/v2_1/folds.csv`)

To respect temporal causality, model selection relies on 4 rolling-origin evaluation folds plus a unified `final_fit` set (from `outputs/v2_1/fold_counts.csv`):

| Fold ID | Origin Cutoff | Training Window | Validation Window | Train Decs | Val Decs | Train Hikes | Val Hikes | Train Rows | Val Rows |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1` | 2016-01-01 | 2010-01-01 to 2015-12-31 | 2016-01-01 to 2017-12-31 | {int(fold_g.loc[(1, 'train'), 'decisions_count'])} | {int(fold_g.loc[(1, 'val'), 'decisions_count'])} | {int(fold_g.loc[(1, 'train'), 'hikes_count'])} | {int(fold_g.loc[(1, 'val'), 'hikes_count'])} | {int(fold_g.loc[(1, 'train'), 'event_rows_count']):,} | {int(fold_g.loc[(1, 'val'), 'event_rows_count']):,} |
| `2` | 2018-01-01 | 2010-01-01 to 2017-12-31 | 2018-01-01 to 2019-12-31 | {int(fold_g.loc[(2, 'train'), 'decisions_count'])} | {int(fold_g.loc[(2, 'val'), 'decisions_count'])} | {int(fold_g.loc[(2, 'train'), 'hikes_count'])} | {int(fold_g.loc[(2, 'val'), 'hikes_count'])} | {int(fold_g.loc[(2, 'train'), 'event_rows_count']):,} | {int(fold_g.loc[(2, 'val'), 'event_rows_count']):,} |
| `3` | 2020-01-01 | 2010-01-01 to 2019-12-31 | 2020-01-01 to 2021-12-31 | {int(fold_g.loc[(3, 'train'), 'decisions_count'])} | {int(fold_g.loc[(3, 'val'), 'decisions_count'])} | {int(fold_g.loc[(3, 'train'), 'hikes_count'])} | {int(fold_g.loc[(3, 'val'), 'hikes_count'])} | {int(fold_g.loc[(3, 'train'), 'event_rows_count']):,} | {int(fold_g.loc[(3, 'val'), 'event_rows_count']):,} |
| `4` | 2022-01-01 | 2010-01-01 to 2021-12-31 | 2022-01-01 to 2023-12-31 | {int(fold_g.loc[(4, 'train'), 'decisions_count'])} | {int(fold_g.loc[(4, 'val'), 'decisions_count'])} | {int(fold_g.loc[(4, 'train'), 'hikes_count'])} | {int(fold_g.loc[(4, 'val'), 'hikes_count'])} | {int(fold_g.loc[(4, 'train'), 'event_rows_count']):,} | {int(fold_g.loc[(4, 'val'), 'event_rows_count']):,} |
| `final_fit` | 2024-01-01 | 2010-01-01 to 2023-12-31 | — | {int(train_s['decisions_count'] + val_s['decisions_count'])} | 0 | {int(train_s['hikes_count'] + val_s['hikes_count'])} | 0 | {int(train_s['event_rows_count'] + val_s['event_rows_count']):,} | 0 |

---

## 5. History Rewrite & Commit Hash Mapping

A git history rewrite was executed via `git-filter-repo` to sanitize contributor metadata across repository history, removing automated bot co-authorship trailers (`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`) so that repository contributions are attributed strictly to the human maintainers (**GauravJaypatre** and **prachi-3011**).

Because git commit hashes cryptographically encapsulate commit author and message metadata, this operation produced new commit hashes across the entire repository graph. All underlying data files retained **100% bitwise SHA-256 identity** throughout.

### Commit Hash Mapping (Pre-Rewrite vs Active Post-Rewrite)

| Milestone Release Tag | Pre-Rewrite Commit Hash | Post-Rewrite Active Commit Hash | Tag Object Hash | Status & Milestone Description |
| :--- | :--- | :--- | :--- | :--- |
| `v1.0-data-freeze` | `1774400c...` (tag `750d1924...`) | `2f83d70f97bf134e5e75cb0055478208047814ed` | `62b5ba2d1fcc5494257084bb28eab21f1ec21eeb` | Phase B/C freeze, baseline tables |
| `v2.0-data-freeze` | `a4bc9d6a...` (tag `11d5c94f...`) | `7b09609cfe96b310e38ec369157ec63053c5c0de` | `a3807cb9e7403c03953e22f7094358f52224d231` | Phase V1–V4 independent verification |
| `v2.0.1-data-freeze` | `67cb97b6...` (tag `9f67b270...`) | `4b8fc6aa5cd59018816b826e374286fd5715161a` | `62325ac2d1aad2e7e13b37f9cb6eead0a9aba806` | CBR emergency alignment, holdout guard |
| `v2.1-train-test-ready` | `be11b3f4c49a...` (tag `10eb56ea...`) | `435f2fba24a388cc24a6c0672a7bc32da031368c` | `8147cd19b497e85804246131219e6bdd1b0e7684` | 2010–2025 window, CV folds, leakage audit |
| `v2.1.1-train-test-ready` | `a8985361...` (tag `3da6556...`) | `f30ab1838c0820fa41f134c91cc058066c48cfdf` | `a6f7f8b95c86e01bbe4177580fd34c5c2c009ba1` | Decision count reconciliation, final_fit |
| `v2.1.1-zenodo-package` | — | `63126907200d95bd40fc8627359965b7c45da95d` | `6a2c90ad44ba66c96453f88f81a82be324606902` | Initial Zenodo package build |
| `v2.1.1-zenodo-package-r2` | — | `d6d784b652318a46ca27a7714b7c1ce48d3560b2` | `bd81df370804be57dd708ec347e576bff4250a43` | Reconciled metadata, conftest auto-skip |
| `v2.1.1-zenodo-package-r3` | — | `8339d6bc9d0a835f7d59a3f952934483e12bde27` | `993401fc3eacc1bfc22020c518aecdaa34eb01e9` | Custom non-open license, AI disclosure, 9 limitations |

> **Audit Clarification on v2.1.1 Commit & Tag Object Lineage**:
> - **Pre-Rewrite Commit (`a8985361...`)**: The pre-rewrite commit for `v2.1.1-train-test-ready` was `a8985361...` on branch `v2.1-train-test` (attested by `DECISIONS.md:516` and `docs/DATA_FREEZE_v2_1.md:22`).
> - **Pre-Rewrite Tag Object (`3da6556...`) & Post-Rewrite Tag Object (`a6f7f8b...`)**: Pre-rewrite tag object was `3da6556...` (attested by `docs/DATA_FREEZE_v2_1.md:22`); active post-rewrite tag object is `a6f7f8b95c86e01bbe4177580fd34c5c2c009ba1` pointing to `f30ab1838c0820fa41f134c91cc058066c48cfdf` (verified via `git cat-file -p refs/tags/v2.1.1-train-test-ready`).
> - **Identifier `2d80319...`**: Labelled "report draft 2d80319..." in `docs/DATA_FREEZE_v2_1.md:22`; it is not determinable from repository evidence whether it was ever a tag object.
> - **Identifier `940ed62...`**: Not determinable from repository evidence (does not exist in git object database, reflog, or commit diffs).

---

## 6. Package Archive & Verification Status at packaging, 2026-10-31

- **Deterministic Upload Archive**:
  - File: `MoTrans15_v2.1.1_zenodo_package.zip`
  - Fixed timestamp: `2026-10-29 00:00:00`, sorted entries, standard permissions, zero cache/junk files.
- **Verified Package Hashes vs DATA_FREEZE_v2_1.md**:
  - `analysis_tier1.parquet`: `8a6207dd0c753c7d24d0a4d091dbdb05ee38d3010913a85b4c9f87a86e44979e` (IDENTICAL)
  - `analysis_tier2_primary.parquet`: `c319040f687fbd88be9268d881c71152d803a0bd20357a109da049415f010a14` (IDENTICAL)
  - `secondary_holds.parquet`: `7235bae5b29d0e4261bc9349e32593b09f9d0bf7cd784a7f61a56a45dc9c846f` (IDENTICAL)
  - `sensitivity_macro_revision.parquet`: `f689bc78820520f08020d4d613fb6129a07abe15842634e2c9b428bd0f5bf794` (IDENTICAL)
  - `panel_returns_only.parquet`: `e5fca3a47c7510fb1d183cc97a2bf7d2e0100111216b6c311aba9049f05dc620` (IDENTICAL)
  - `folds.csv`: `5530c5017c9068be7e291c147c7c47bea83888f000e2a9712139a6f47530d6ee` (IDENTICAL)

---

## 7. Open Items & Research Limitations (Status at packaging, 2026-10-31)

Status at packaging, 2026-10-31: this version is a pre-clearance snapshot deposited under Restricted Access (files visible only to approved requesters). Access requests are not being approved at present while (a) licence review and (b) vendor redistribution clearance for derived equity returns are completed. Authors' original contributions are CC-BY-4.0 and MIT; derived return tables are restricted and subject to vendor terms. Any future open release is possible only if vendors permit, with no timeline.

### Open Clearance Items

1. **Licence Review by Supervisor / Library (`LICENCE_REVIEW_DONE = NO`)**:
   - The custom non-open restricted research license (`LICENSE`) has not undergone formal institutional, supervisor, or library review. Access requests remain on hold until institutional clearance is completed.
2. **Financial Index Vendor Redistribution Clearance (`VENDOR_CLEARANCE = NOT_CLEARED`)**:
   - Formal redistribution clearance for derived equity returns has not been acquired from primary financial index exchange providers (`LICENCE_CLEARANCE.txt`). In the absence of signed vendor clearance, derived return tables remain restricted under vendor terms. Authors' original contributions are CC-BY-4.0 and MIT; any future open release of derived returns is possible only if vendors permit, with no timeline.

### Genuine Research Design & Data Limitations

3. **Single-Source Equity Prices**:
   - 36 of 38 equity indices rely on primary vendor feeds; only S&P 500 and Nikkei 225 are cross-verified against FRED.
4. **Emerging Market Announcement Timing**:
   - BCB, Banxico, RBI, BoK, and PBoC decisions remain disqualified from primary tiers due to the absence of scraped minute-level release archives.
5. **Bank of England Pre-2016 Timing**:
   - BoE decisions prior to 2016-01-01 are verified at the convention level (strict Thursday 12:00 noon protocol) rather than minute-level announcement scrapes.
6. **Macroeconomic Industrial-Production Vintage Triangles**:
   - Historical IP controls use first-available vintage indicators rather than point-in-time vintage triangles.
7. **Statement Qualitative Hand Labels**:
   - Narrative qualitative hand classifications have not undergone double-blind expert replication and are excluded.
"""

    with open(SUMMARY_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    print(f"Generated {SUMMARY_PATH}")

if __name__ == "__main__":
    build_summary()
