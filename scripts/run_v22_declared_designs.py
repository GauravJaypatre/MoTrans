"""Execution script for MoTrans-15 v2.2 Pre-Declared Designs (Task 3).

Executes strictly on Train + Validation splits (2010-2023):
- Design 1: Regime-Stratified Forward Chaining (Train <= Y, Score Y+1 for Y in {2011, 2017, 2018, 2022})
- Design 2: Leave-One-Tightening-Episode-Out (LOTEO) across E1 (2011), E2 (2015-2018), E3 (2022-2023)
- Design 3: Restatement of v1 Blind Test Results (Confirmatory Overlap vs Bivariate Deviation)

Reports:
- N decisions, N rows, beta, clustered SE, wild bootstrap p, 95% CI, MDE
- Sensitivity with and without #1 influential event (cbr_2014-12-16)
- Tier 1 only vs Pooled
- Updates outputs/modeling/ledger.csv with Holm and BH adjustments
- Outputs detailed summary tables for docs/V22_RESULTS.md

STRICT SAFETY: Zero test split rows loaded (unlock_audit.log stays at 16 lines).
"""

from __future__ import annotations

import sys
import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.clustering import fit_ols_clustered
from src.modeling.uncertainty import wild_cluster_bootstrap
from src.modeling.pipeline import FoldSafeScaler
from src.modeling.tier_handler import prepare_tier_sample
from src.modeling.run_v1_blind_test import load_v1_blind_test_sample

OUTPUTS_DIR = ROOT / "outputs" / "modeling"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
LEDGER_PATH = OUTPUTS_DIR / "ledger.csv"


def compute_mde(se: float, df_t: int = 100, alpha: float = 0.05, power: float = 0.80) -> float:
    """Compute Minimum Detectable Effect in basis points."""
    t_alpha = stats.t.ppf(1 - alpha / 2, df=df_t)
    t_beta = stats.t.ppf(power, df=df_t)
    factor = t_alpha + t_beta
    return factor * se * 10000.0  # in bp per 1 SD shock


def run_design_1(df_t1: pd.DataFrame, df_pool: pd.DataFrame) -> list[dict]:
    """Design 1: Regime-Stratified Forward Chaining.
    Train <= Y, Score Y+1 for Y in {2011, 2017, 2018, 2022}.
    """
    print("\n=======================================================")
    print("RUNNING DESIGN 1: REGIME-STRATIFIED FORWARD CHAINING")
    print("=======================================================")

    years = [2011, 2017, 2018, 2022]
    records = []

    configs = [
        ("Tier 1", df_t1, ["shock_raw_bp_fold_std"], "tier1"),
        ("Pooled", df_pool, ["shock_raw_bp_fold_std", "shock_tier"], "pooled"),
    ]

    for c_label, df_full, feat_cols, tier_str in configs:
        for Y in years:
            for drop_cbr in [False, True]:
                sub = df_full.copy()
                if drop_cbr:
                    sub = sub[sub["event_id"] != "cbr_2014-12-16"].copy()

                train_data = sub[sub["year"] <= Y].copy()
                eval_data = sub[sub["year"] == (Y + 1)].copy()

                n_train_hikes = (train_data[train_data["size_bp"] > 0]["event_id"].nunique())
                if n_train_hikes == 0:
                    continue  # Only evaluate years whose training data contain hikes

                # Fit scaler on training data
                scaler = FoldSafeScaler(feature_cols=["shock_raw_bp"])
                scaler.fit(train_data, allow_final_fit=True)
                train_data = scaler.transform(train_data)
                eval_data = scaler.transform(eval_data)

                # Train model fit
                ols_train = fit_ols_clustered(train_data, "clr_5", feat_cols, cluster_col="event_id")
                wild_train = wild_cluster_bootstrap(train_data, "clr_5", feat_cols, cluster_col="event_id", n_boot=999, seed=42)

                df_deg = max(1, ols_train["n_clusters"] - len(feat_cols) - 1)
                mde_val = compute_mde(ols_train["se_shock"], df_t=df_deg)

                # Out of sample prediction on Y+1
                y_true = eval_data["clr_5"].values
                x_eval = eval_data[feat_cols].values
                # Intercept + betas
                beta_vec = np.array([ols_train["results_model"].params[col] for col in feat_cols])
                intercept = ols_train["results_model"].params["const"]
                y_pred = intercept + x_eval @ beta_vec

                rmse_oos = np.sqrt(np.mean((y_true - y_pred) ** 2)) if len(y_true) > 0 else np.nan
                dir_acc = np.mean(np.sign(y_true) == np.sign(y_pred)) if len(y_true) > 0 else np.nan
                ss_res = np.sum((y_true - y_pred) ** 2)
                ss_tot = np.sum((y_true - np.mean(train_data["clr_5"])) ** 2)
                r2_oos = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else np.nan

                # Also fit OLS directly on Y+1 as evaluation slice
                ols_eval = fit_ols_clustered(eval_data, "clr_5", feat_cols, cluster_col="event_id") if eval_data["event_id"].nunique() >= 3 else None
                wild_eval = wild_cluster_bootstrap(eval_data, "clr_5", feat_cols, cluster_col="event_id", n_boot=999, seed=42) if eval_data["event_id"].nunique() >= 3 else {"p_val_wild": np.nan}

                drop_str = " (No CBR-2014)" if drop_cbr else ""
                model_id = f"D1_FC_{tier_str.upper()}_LE{Y}_TO_{Y+1}{'_NOCBR' if drop_cbr else ''}"

                records.append({
                    "design": "Design 1: Forward Chaining",
                    "model_id": model_id,
                    "tier": tier_str,
                    "train_end_year": Y,
                    "eval_year": Y + 1,
                    "sample": f"Train <= {Y}, Score {Y+1}{drop_str}",
                    "drop_cbr_2014": drop_cbr,
                    "n_train_events": ols_train["n_events"],
                    "n_train_obs": ols_train["n_obs"],
                    "n_train_hikes": n_train_hikes,
                    "n_eval_events": eval_data["event_id"].nunique(),
                    "n_eval_obs": len(eval_data),
                    "coef_shock": ols_train["coef_shock"],
                    "se_shock": ols_train["se_shock"],
                    "t_stat": ols_train["t_stat"],
                    "p_val_cluster": ols_train["p_val"],
                    "p_val_wild": wild_train["p_val_wild"],
                    "ci_lower": ols_train["ci_lower"],
                    "ci_upper": ols_train["ci_upper"],
                    "r2_train": ols_train["r2"],
                    "mde_bp": mde_val,
                    "rmse_oos": rmse_oos,
                    "directional_accuracy_oos": dir_acc,
                    "r2_oos": r2_oos,
                    "eval_slice_beta": ols_eval["coef_shock"] if ols_eval else np.nan,
                    "eval_slice_se": ols_eval["se_shock"] if ols_eval else np.nan,
                    "eval_slice_wild_p": wild_eval["p_val_wild"],
                    "specification": f"clr_5 ~ {' + '.join(feat_cols)}",
                })

                print(f"  [{c_label}{drop_str}] Train <= {Y} (N={ols_train['n_events']}) -> Score {Y+1}: "
                      f"beta={ols_train['coef_shock']:.4f}, wild_p={wild_train['p_val_wild']:.4f}, MDE={mde_val:.1f} bp, "
                      f"R2_oos={r2_oos:.4f}, DirAcc={dir_acc:.2%}")

    return records


def run_design_2(df_t1: pd.DataFrame, df_pool: pd.DataFrame) -> list[dict]:
    """Design 2: Leave-One-Tightening-Episode-Out (LOTEO).
    E1: 2011 (ECB Trichet hikes)
    E2: 2015-2018 (Fed post-ZIRP tightening)
    E3: 2022-2023 (Synchronized global inflation tightening)
    """
    print("\n=======================================================")
    print("RUNNING DESIGN 2: LEAVE-ONE-TIGHTENING-EPISODE-OUT (LOTEO)")
    print("=======================================================")

    episodes = [
        ("E1_2011", [2011], "Episode 1: 2011 (ECB Trichet Hikes)"),
        ("E2_2015_2018", [2015, 2016, 2017, 2018], "Episode 2: 2015-2018 (Fed Post-ZIRP Cycle)"),
        ("E3_2022_2023", [2022, 2023], "Episode 3: 2022-2023 (Global Synchronized Inflation Hikes)"),
    ]

    records = []

    configs = [
        ("Tier 1", df_t1, ["shock_raw_bp_fold_std"], "tier1"),
        ("Pooled", df_pool, ["shock_raw_bp_fold_std", "shock_tier"], "pooled"),
    ]

    for c_label, df_full, feat_cols, tier_str in configs:
        for ep_key, ep_years, ep_desc in episodes:
            for drop_cbr in [False, True]:
                sub = df_full.copy()
                if drop_cbr:
                    sub = sub[sub["event_id"] != "cbr_2014-12-16"].copy()

                # Train = everything except episode years
                train_data = sub[~sub["year"].isin(ep_years)].copy()
                holdout_data = sub[sub["year"].isin(ep_years)].copy()

                # Fit scaler on remaining train
                scaler = FoldSafeScaler(feature_cols=["shock_raw_bp"])
                scaler.fit(train_data, allow_final_fit=True)
                train_data = scaler.transform(train_data)
                holdout_data = scaler.transform(holdout_data)

                ols_train = fit_ols_clustered(train_data, "clr_5", feat_cols, cluster_col="event_id")
                wild_train = wild_cluster_bootstrap(train_data, "clr_5", feat_cols, cluster_col="event_id", n_boot=999, seed=42)

                df_deg = max(1, ols_train["n_clusters"] - len(feat_cols) - 1)
                mde_val = compute_mde(ols_train["se_shock"], df_t=df_deg)

                # Out-of-episode evaluation
                y_true = holdout_data["clr_5"].values
                x_eval = holdout_data[feat_cols].values
                beta_vec = np.array([ols_train["results_model"].params[col] for col in feat_cols])
                intercept = ols_train["results_model"].params["const"]
                y_pred = intercept + x_eval @ beta_vec

                rmse_oos = np.sqrt(np.mean((y_true - y_pred) ** 2)) if len(y_true) > 0 else np.nan
                dir_acc = np.mean(np.sign(y_true) == np.sign(y_pred)) if len(y_true) > 0 else np.nan
                ss_res = np.sum((y_true - y_pred) ** 2)
                ss_tot = np.sum((y_true - np.mean(train_data["clr_5"])) ** 2)
                r2_oos = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else np.nan

                # Fit OLS directly on the holdout episode
                ols_ep = fit_ols_clustered(holdout_data, "clr_5", feat_cols, cluster_col="event_id")
                wild_ep = wild_cluster_bootstrap(holdout_data, "clr_5", feat_cols, cluster_col="event_id", n_boot=999, seed=42)

                drop_str = " (No CBR-2014)" if drop_cbr else ""
                model_id = f"D2_LOTEO_{tier_str.upper()}_{ep_key}{'_NOCBR' if drop_cbr else ''}"

                records.append({
                    "design": "Design 2: LOTEO",
                    "model_id": model_id,
                    "tier": tier_str,
                    "episode_key": ep_key,
                    "episode_desc": ep_desc,
                    "sample": f"Holdout {ep_key}{drop_str}",
                    "drop_cbr_2014": drop_cbr,
                    "n_train_events": ols_train["n_events"],
                    "n_train_obs": ols_train["n_obs"],
                    "n_holdout_events": ols_ep["n_events"],
                    "n_holdout_obs": ols_ep["n_obs"],
                    "coef_shock": ols_train["coef_shock"],
                    "se_shock": ols_train["se_shock"],
                    "t_stat": ols_train["t_stat"],
                    "p_val_cluster": ols_train["p_val"],
                    "p_val_wild": wild_train["p_val_wild"],
                    "ci_lower": ols_train["ci_lower"],
                    "ci_upper": ols_train["ci_upper"],
                    "r2_train": ols_train["r2"],
                    "mde_bp": mde_val,
                    "rmse_oos": rmse_oos,
                    "directional_accuracy_oos": dir_acc,
                    "r2_oos": r2_oos,
                    "holdout_episode_beta": ols_ep["coef_shock"],
                    "holdout_episode_se": ols_ep["se_shock"],
                    "holdout_episode_wild_p": wild_ep["p_val_wild"],
                    "specification": f"clr_5 ~ {' + '.join(feat_cols)}",
                })

                print(f"  [{c_label}{drop_str}] Holdout {ep_key}: "
                      f"Train beta={ols_train['coef_shock']:.4f} (wild_p={wild_train['p_val_wild']:.4f}), "
                      f"Holdout beta={ols_ep['coef_shock']:.4f} (wild_p={wild_ep['p_val_wild']:.4f}), "
                      f"R2_oos={r2_oos:.4f}, DirAcc={dir_acc:.2%}")

    return records


def run_design_3() -> list[dict]:
    """Design 3: Restatement of v1 Blind Test Results.
    Primary confirmatory: clr_W ~ shock_std + overlap_Wd
    Labelled deviation: clr_W ~ shock_std
    Horizons: clr_1, 3, 5, 20, 60.
    """
    print("\n=======================================================")
    print("RUNNING DESIGN 3: RESTATEMENT OF V1 BLIND TEST RESULTS")
    print("=======================================================")

    bt = load_v1_blind_test_sample()
    horizons = [("clr_1", 1), ("clr_3", 3), ("clr_5", 5), ("clr_20", 20), ("clr_60", 60)]
    records = []

    for h, w in horizons:
        ov_col = f"overlap_{w}d"

        # 1. Primary Confirmatory (Overlap Controlled)
        feat_conf = ["shock_std", ov_col]
        ols_conf = fit_ols_clustered(bt, h, feat_conf, cluster_col="event_id")
        wild_conf = wild_cluster_bootstrap(bt, h, feat_conf, cluster_col="event_id", n_boot=999, seed=42)
        df_deg = max(1, ols_conf["n_clusters"] - len(feat_conf) - 1)
        mde_conf = compute_mde(ols_conf["se_shock"], df_t=df_deg)

        # 2. Labelled Deviation (Bivariate)
        feat_dev = ["shock_std"]
        ols_dev = fit_ols_clustered(bt, h, feat_dev, cluster_col="event_id")
        wild_dev = wild_cluster_bootstrap(bt, h, feat_dev, cluster_col="event_id", n_boot=999, seed=42)
        mde_dev = compute_mde(ols_dev["se_shock"], df_t=df_deg)

        records.append({
            "design": "Design 3: v1 Blind Test Restatement",
            "model_id": f"D3_V1_CONFIRMATORY_{h.upper()}",
            "tier": "tier1",
            "horizon": h,
            "spec_type": "Confirmatory Primary (Pre-Registered)",
            "specification": f"{h} ~ shock_std + {ov_col}",
            "sample": "47-decision v1 sample (US, EA, JP)",
            "drop_cbr_2014": False,
            "n_events": ols_conf["n_events"],
            "n_obs": ols_conf["n_obs"],
            "coef_shock": ols_conf["coef_shock"],
            "se_shock": ols_conf["se_shock"],
            "t_stat": ols_conf["t_stat"],
            "p_val_cluster": ols_conf["p_val"],
            "p_val_wild": wild_conf["p_val_wild"],
            "ci_lower": ols_conf["ci_lower"],
            "ci_upper": ols_conf["ci_upper"],
            "r2": ols_conf["r2"],
            "mde_bp": mde_conf,
            "caveats": "Primary pre-registered confirmatory model with overlap control",
        })

        records.append({
            "design": "Design 3: v1 Blind Test Restatement",
            "model_id": f"D3_V1_DEVIATION_{h.upper()}",
            "tier": "tier1",
            "horizon": h,
            "spec_type": "Labelled Deviation (Executed Bivariate)",
            "specification": f"{h} ~ shock_std",
            "sample": "47-decision v1 sample (US, EA, JP)",
            "drop_cbr_2014": False,
            "n_events": ols_dev["n_events"],
            "n_obs": ols_dev["n_obs"],
            "coef_shock": ols_dev["coef_shock"],
            "se_shock": ols_dev["se_shock"],
            "t_stat": ols_dev["t_stat"],
            "p_val_cluster": ols_dev["p_val"],
            "p_val_wild": wild_dev["p_val_wild"],
            "ci_lower": ols_dev["ci_lower"],
            "ci_upper": ols_dev["ci_upper"],
            "r2": ols_dev["r2"],
            "mde_bp": mde_dev,
            "caveats": "Disclosed deviation: omitted overlap_Wd control; requires author approval",
        })

        print(f"  [{h}] Primary (Overlap): beta={ols_conf['coef_shock']:.4f}, wild_p={wild_conf['p_val_wild']:.4f}, MDE={mde_conf:.1f} bp | "
              f"Deviation (Biv): beta={ols_dev['coef_shock']:.4f}, wild_p={wild_dev['p_val_wild']:.4f}, MDE={mde_dev:.1f} bp")

    return records


def update_ledger_and_save_reports(rec_d1: list[dict], rec_d2: list[dict], rec_d3: list[dict]):
    """Update outputs/modeling/ledger.csv and save design-specific CSVs."""
    print("\n=======================================================")
    print("UPDATING LEDGER AND COMPUTING MULTIPLICITY ADJUSTMENTS")
    print("=======================================================")

    df_d1 = pd.DataFrame(rec_d1)
    df_d2 = pd.DataFrame(rec_d2)
    df_d3 = pd.DataFrame(rec_d3)

    df_d1.to_csv(OUTPUTS_DIR / "v22_design1_forward_chaining.csv", index=False)
    df_d2.to_csv(OUTPUTS_DIR / "v22_design2_loteo.csv", index=False)
    df_d3.to_csv(OUTPUTS_DIR / "v22_design3_v1_restatement.csv", index=False)
    print("Saved individual design CSV reports to outputs/modeling/")

    # Read existing ledger
    old_ledger = pd.read_csv(LEDGER_PATH)
    print(f"Existing ledger row count: {len(old_ledger)}")

    # Format new ledger rows
    now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_ledger_rows = []

    # From Design 1
    for r in rec_d1:
        new_ledger_rows.append({
            "model_id": r["model_id"],
            "timestamp_utc": now_ts,
            "model_name": f"d1_fc_{r['tier']}_{r['train_end_year']}",
            "tier": r["tier"],
            "sample": r["sample"],
            "fold": "forward_chain",
            "outcome_col": "clr_5",
            "shock_col": "shock_raw_bp_fold_std",
            "specification": r["specification"],
            "n_obs": r["n_train_obs"],
            "n_events": r["n_train_events"],
            "n_clusters": r["n_train_events"],
            "coef_shock": r["coef_shock"],
            "se_shock": r["se_shock"],
            "t_stat": r["t_stat"],
            "p_val": r["p_val_cluster"],
            "ci_lower": r["ci_lower"],
            "ci_upper": r["ci_upper"],
            "r2": r["r2_train"],
            "caveats": f"Design 1 Forward Chaining: Train <= {r['train_end_year']}, Score {r['eval_year']}; MDE={r['mde_bp']:.1f} bp",
            "p_val_holm": np.nan,
            "p_val_bh_fdr": np.nan,
            "p_val_wild": r["p_val_wild"],
            "p_val_holm_wild": np.nan,
            "p_val_bh_wild": np.nan,
        })

    # From Design 2
    for r in rec_d2:
        new_ledger_rows.append({
            "model_id": r["model_id"],
            "timestamp_utc": now_ts,
            "model_name": f"d2_loteo_{r['tier']}_{r['episode_key']}",
            "tier": r["tier"],
            "sample": r["sample"],
            "fold": "loteo",
            "outcome_col": "clr_5",
            "shock_col": "shock_raw_bp_fold_std",
            "specification": r["specification"],
            "n_obs": r["n_train_obs"],
            "n_events": r["n_train_events"],
            "n_clusters": r["n_train_events"],
            "coef_shock": r["coef_shock"],
            "se_shock": r["se_shock"],
            "t_stat": r["t_stat"],
            "p_val": r["p_val_cluster"],
            "ci_lower": r["ci_lower"],
            "ci_upper": r["ci_upper"],
            "r2": r["r2_train"],
            "caveats": f"Design 2 LOTEO: Holdout {r['episode_key']}; MDE={r['mde_bp']:.1f} bp",
            "p_val_holm": np.nan,
            "p_val_bh_fdr": np.nan,
            "p_val_wild": r["p_val_wild"],
            "p_val_holm_wild": np.nan,
            "p_val_bh_wild": np.nan,
        })

    # From Design 3
    for r in rec_d3:
        new_ledger_rows.append({
            "model_id": r["model_id"],
            "timestamp_utc": now_ts,
            "model_name": f"d3_v1_{r['horizon']}_{'conf' if 'Confirmatory' in r['spec_type'] else 'dev'}",
            "tier": r["tier"],
            "sample": r["sample"],
            "fold": "v1_blind_test",
            "outcome_col": r["horizon"],
            "shock_col": "shock_std",
            "specification": r["specification"],
            "n_obs": r["n_obs"],
            "n_events": r["n_events"],
            "n_clusters": r["n_events"],
            "coef_shock": r["coef_shock"],
            "se_shock": r["se_shock"],
            "t_stat": r["t_stat"],
            "p_val": r["p_val_cluster"],
            "ci_lower": r["ci_lower"],
            "ci_upper": r["ci_upper"],
            "r2": r["r2"],
            "caveats": r["caveats"],
            "p_val_holm": np.nan,
            "p_val_bh_fdr": np.nan,
            "p_val_wild": r["p_val_wild"],
            "p_val_holm_wild": np.nan,
            "p_val_bh_wild": np.nan,
        })

    # Filter out any existing entries with matching model_id to avoid duplication
    new_model_ids = {r["model_id"] for r in new_ledger_rows}
    kept_old = old_ledger[~old_ledger["model_id"].isin(new_model_ids)].copy()

    df_combined = pd.concat([kept_old, pd.DataFrame(new_ledger_rows)], ignore_index=True)

    # Recompute Holm and BH across the ENTIRE ledger over p_val_wild
    print(f"Total models in updated ledger: {len(df_combined)}")
    wild_p_series = df_combined["p_val_wild"].fillna(1.0)
    _, p_holm_wild, _, _ = multipletests(wild_p_series, method="holm")
    _, p_bh_wild, _, _ = multipletests(wild_p_series, method="fdr_bh")

    df_combined["p_val_holm_wild"] = p_holm_wild
    df_combined["p_val_bh_wild"] = p_bh_wild

    # Also over asymptotic p_val
    asymp_p_series = df_combined["p_val"].fillna(1.0)
    _, p_holm_asymp, _, _ = multipletests(asymp_p_series, method="holm")
    _, p_bh_asymp, _, _ = multipletests(asymp_p_series, method="fdr_bh")

    df_combined["p_val_holm"] = p_holm_asymp
    df_combined["p_val_bh_fdr"] = p_bh_asymp

    df_combined.to_csv(LEDGER_PATH, index=False)
    print(f"Successfully wrote updated ledger to {LEDGER_PATH} with {len(df_combined)} rows.")


def main():
    print("=================================================================")
    print("MOTRANS-15 V2.2 PRE-DECLARED ALTERNATIVE EVALUATION DESIGNS")
    print("=================================================================")

    # Load Train+Val data (Strictly guarded, 0 test split loaded)
    df_t1 = prepare_tier_sample("tier1", split="train_val", version="v2_2")
    df_t1["year"] = pd.to_datetime(df_t1["decision_date"]).dt.year

    df_pool = prepare_tier_sample("pooled", split="train_val", version="v2_2")
    df_pool["year"] = pd.to_datetime(df_pool["decision_date"]).dt.year

    rec_d1 = run_design_1(df_t1, df_pool)
    rec_d2 = run_design_2(df_t1, df_pool)
    rec_d3 = run_design_3()

    update_ledger_and_save_reports(rec_d1, rec_d2, rec_d3)
    print("\nAll pre-declared designs executed successfully!")


if __name__ == "__main__":
    main()
