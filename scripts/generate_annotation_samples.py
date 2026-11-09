import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(".")
SOURCE_SAMPLE = ROOT / "docs" / "hand_label_sample.csv"
OUT_DIR = ROOT / "data" / "annotation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

df_all = pd.read_csv(SOURCE_SAMPLE)

# 1. Select 100 statements deterministically
rng = np.random.default_rng(2026)
sampled_indices = rng.choice(len(df_all), size=100, replace=False)
df_100 = df_all.iloc[sampled_indices].copy()

# Columns to retain (strictly blinded to returns and decisions)
base_cols = ["event_id", "regime", "decision_date", "source_url", "word_count"]

# 2. Annotator 1 sample (shuffled with seed 101)
rng1 = np.random.default_rng(101)
order1 = rng1.permutation(100)
df_ann1 = df_100.iloc[order1][base_cols].copy().reset_index(drop=True)
df_ann1.insert(0, "sample_id", range(1, 101))
df_ann1["coder_id"] = "annotator_01"
df_ann1["hawkish_dovish"] = np.nan
df_ann1["inflation_concern"] = np.nan
df_ann1["growth_concern"] = np.nan
df_ann1["uncertainty"] = np.nan
df_ann1["forward_guidance_shift"] = np.nan
df_ann1["notes"] = np.nan

out_ann1 = OUT_DIR / "annotator_1_sample.csv"
df_ann1.to_csv(out_ann1, index=False)
print(f"Wrote {len(df_ann1)} rows to {out_ann1}")

# 3. Annotator 2 sample (shuffled independently with seed 202)
rng2 = np.random.default_rng(202)
order2 = rng2.permutation(100)
df_ann2 = df_100.iloc[order2][base_cols].copy().reset_index(drop=True)
df_ann2.insert(0, "sample_id", range(1, 101))
df_ann2["coder_id"] = "annotator_02"
df_ann2["hawkish_dovish"] = np.nan
df_ann2["inflation_concern"] = np.nan
df_ann2["growth_concern"] = np.nan
df_ann2["uncertainty"] = np.nan
df_ann2["forward_guidance_shift"] = np.nan
df_ann2["notes"] = np.nan

out_ann2 = OUT_DIR / "annotator_2_sample.csv"
df_ann2.to_csv(out_ann2, index=False)
print(f"Wrote {len(df_ann2)} rows to {out_ann2}")

# 4. Adjudication log template (empty, ready for double annotation)
adj_cols = [
    "adjudication_id",
    "event_id",
    "regime",
    "decision_date",
    "dimension",
    "score_annotator_1",
    "score_annotator_2",
    "discrepancy_magnitude",
    "adjudicated_score",
    "adjudicator_id",
    "adjudication_timestamp",
    "notes",
]
df_adj = pd.DataFrame(columns=adj_cols)
out_adj = OUT_DIR / "adjudication_log.csv"
df_adj.to_csv(out_adj, index=False)
print(f"Created empty adjudication log template at {out_adj}")
