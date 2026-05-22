#!/usr/bin/env python3
"""One-off script to generate clustering_final.ipynb."""
import json
from pathlib import Path

def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": [s + "\n"]}

def code(s):
    return {
        "cell_type": "code",
        "metadata": {},
 "outputs": [],
        "execution_count": None,
        "source": [line + "\n" for line in s.splitlines()],
    }

cells = []

cells.append(md("""# Final dormancy clustering pipeline

Reproducible production clustering for **active**, **cooling**, and **dormant** using validated settings from `clustering_v3.ipynb`.

**Outputs:** `outputs/clustering/final/`

| Stratum | Features | Tuned HDBSCAN | Reference (100k sample) |
| --- | --- | --- | --- |
| Active | 16 correlation-group reps | frac=0.005, ε=0.75, min_samples=15 | ~6 clusters, ~5.8% noise |
| Cooling | Top-5 primary (permutation) | frac=0.04, ε=0.50, min_samples=10 | ~8 clusters, ~14% noise |
| Dormant | Top-5 primary (permutation) | frac=0.05, ε=0.50, min_samples=25 | ~5 clusters, ~2.4% noise |

**Pipeline:** (1) document feature selection & tuning → (2) fit preprocessor on **100k** reference sample (same as v3) → (3) fit HDBSCAN on that matrix → (4) assign **all** developers via batched `approximate_predict` with the **same** preprocessor → (5) save parquet + summary."""))

cells.append(md("""## 1. Feature selection

1. **Correlation diagnostics** on `dev_profile_final_v4` per stratum.
2. **Correlation groups** at `|corr| ≥ 0.50` → **16 representatives** (89-feature activity group → `log_activity_count_30_90d`).  
   File: `outputs/clustering/v3/feature_selection_grouped/v3_group_representative_features.txt`
3. **Per-stratum drops** after median impute + `RobustScaler` (zero variance): active keeps 16; cooling 12; dormant 11 if using all 16.
4. **Permutation test** (v3 validation): shuffle one feature, refit HDBSCAN, measure silhouette drop.  
   **Cooling top 5:** `learning_community_share`, `robotics_share`, `mixed_persona_flag`, `cuda_share`, `log_activity_count_30_90d`  
   **Dormant top 5:** `lifetime_learn_count`, `simulation_share`, `mixed_persona_flag`, `lifetime_bug_count`, `lifetime_dli_training_count`  
   **Active:** keep all 16 (drops spread across many features)."""))

cells.append(md("""## 2. Hyperparameter tuning (not re-run here)

Done in `clustering_v3.ipynb` on persona-stratified **100k** samples (`HASH_SALT=42`):

- Coarse grid → `outputs/clustering/v3_coarse_hdbscan/`
- Cooling feature comparison → `outputs/clustering/v3_top5_permutation_test/`
- Leakage / stability / sanity → `outputs/clustering/v3_final_validation/`

**Locked values below** are the best noise/cluster tradeoffs from those experiments."""))

cells.append(code("""
import json
import warnings
from pathlib import Path

import duckdb
import hdbscan
import joblib
import numpy as np
import pandas as pd
from IPython.display import display
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings("ignore", category=FutureWarning)

DB_PATH = "developer_project.duckdb"
PROFILE_TABLE = "dev_profile_final_v4"
OUTPUT_DIR = Path("outputs/clustering/final")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GROUPED_LIST = Path(
    "outputs/clustering/v3/feature_selection_grouped/v3_group_representative_features.txt"
)

SAMPLE_N = 100_000
HASH_SALT = 42
PREDICT_BATCH_SIZE = 50_000

if GROUPED_LIST.exists():
    FULL_16 = [
        line.strip() for line in GROUPED_LIST.read_text().splitlines() if line.strip()
    ]
else:
    FULL_16 = [
        "log_activity_count_30_90d", "mixed_persona_flag", "cuda_share",
        "activity_velocity_0_30_vs_30_90", "build_velocity_0_30_vs_30_90",
        "days_since_last_activity_0_30d", "learning_community_share",
        "lifetime_bug_count", "lifetime_dli_training_count", "lifetime_forum_count",
        "lifetime_hackathon_count", "lifetime_learn_count", "lifetime_webinar_count",
        "recent_champion_flag", "robotics_share", "simulation_share",
    ]

TOP5_COOLING = [
    "learning_community_share", "robotics_share", "mixed_persona_flag",
    "cuda_share", "log_activity_count_30_90d",
]
TOP5_DORMANT = [
    "lifetime_learn_count", "simulation_share", "mixed_persona_flag",
    "lifetime_bug_count", "lifetime_dli_training_count",
]

FINAL_MODELS = {
    "active": {
        "where_sql": (
            "is_activated = 1 AND COALESCE(dormancy_status, '') = 'Active' "
            "AND COALESCE(has_activity_0_30d, 0) = 1"
        ),
        "stratify_col": "persona",
        "features": FULL_16,
        "feature_set_type": "full_16",
        "min_cluster_frac": 0.005,
        "cluster_selection_epsilon": 0.75,
        "min_samples": 15,
        "reference_clusters": 6,
        "reference_noise_pct": 5.78,
    },
    "cooling": {
        "where_sql": "COALESCE(dormancy_status, '') = 'Cooling'",
        "stratify_col": "persona",
        "features": TOP5_COOLING,
        "feature_set_type": "top5_primary",
        "min_cluster_frac": 0.04,
        "cluster_selection_epsilon": 0.50,
        "min_samples": 10,
        "reference_clusters": 8,
        "reference_noise_pct": 14.05,
    },
    "dormant": {
        "where_sql": "COALESCE(dormancy_status, '') = 'Dormant'",
        "stratify_col": "persona",
        "features": TOP5_DORMANT,
        "feature_set_type": "top5_primary",
        "min_cluster_frac": 0.050,
        "cluster_selection_epsilon": 0.50,
        "min_samples": 25,
        "reference_clusters": 5,
        "reference_noise_pct": 2.41,
    },
}

EXCLUDE_EXACT = {
    "developer_id", "persona", "dormancy_status", "final_lifecycle_status",
    "behavior_journey_stage_30d", "current_journey_state_30d",
}
RAW_LIFETIME_SUPERSEDED = {
    "lifetime_activity_count", "lifetime_activity_score_sum", "lifetime_build_count",
    "lifetime_high_effort_count", "lifetime_total_confidence_weighted_effort",
    "lifetime_effort_x_activity_score_sum",
}

display(pd.DataFrame([
    {
        "stratum": k,
        "feature_set": v["feature_set_type"],
        "n_features": len(v["features"]),
        "min_cluster_frac": v["min_cluster_frac"],
        "epsilon": v["cluster_selection_epsilon"],
        "min_samples": v["min_samples"],
        "ref_clusters": v["reference_clusters"],
        "ref_noise_pct": v["reference_noise_pct"],
    }
    for k, v in FINAL_MODELS.items()
]))
"""))

cells.append(code("""
def should_exclude(col: str) -> bool:
    if col in EXCLUDE_EXACT or col in RAW_LIFETIME_SUPERSEDED:
        return True
    return col.startswith("first_activity_date") or col.startswith("last_activity_date")


def build_matrix_fit(df: pd.DataFrame, features: list[str]):
    cols = [c for c in features if c in df.columns and not should_exclude(c)]
    cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().any()]
    pre = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", RobustScaler()),
    ])
    X = pre.fit_transform(df[cols])
    var_keep = np.var(X, axis=0) > 1e-12
    names = [cols[i] for i, k in enumerate(var_keep) if k]
    return X[:, var_keep], names, pre, cols, var_keep


def transform_preprocessed(df: pd.DataFrame, fit_cols: list[str], preprocessor: Pipeline, var_keep: np.ndarray):
    return preprocessor.transform(df[fit_cols])[:, var_keep]


def cohort_count(con, where_sql: str) -> int:
    return int(con.execute(
        f"SELECT COUNT(*) FROM {PROFILE_TABLE} WHERE {where_sql}"
    ).fetchone()[0])


def load_cohort_batch(con, where_sql: str, feature_cols: list[str], offset: int, limit: int) -> pd.DataFrame:
    meta = ["developer_id", "persona", "dormancy_status"]
    select_sql = ", ".join(sorted(set(meta) | set(feature_cols)))
    return con.execute(
        f"SELECT {select_sql} FROM {PROFILE_TABLE} WHERE {where_sql} "
        f"ORDER BY developer_id LIMIT {limit} OFFSET {offset}"
    ).fetchdf()


def sample_stratum_100k(con, where_sql: str, stratify_col: str, feature_cols: list[str]):
    select_sql = ", ".join(sorted(set(["developer_id", stratify_col, "persona", "dormancy_status"]) | set(feature_cols)))
    cohort_n = cohort_count(con, where_sql)
    target = min(SAMPLE_N, cohort_n)
    if cohort_n <= target:
        return cohort_n, con.execute(
            f"SELECT {select_sql} FROM {PROFILE_TABLE} WHERE {where_sql}"
        ).fetchdf()
    sql = (
        f"WITH cohort AS (SELECT {select_sql} FROM {PROFILE_TABLE} WHERE {where_sql}), "
        f"targets AS ("
        f"  SELECT {stratify_col},"
        f"    GREATEST(1, CAST(ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () * {target}) AS BIGINT)) AS target_n"
        f"  FROM cohort GROUP BY {stratify_col}"
        f"), "
        f"ranked AS ("
        f"  SELECT c.*,"
        f"    ROW_NUMBER() OVER ("
        f"      PARTITION BY c.{stratify_col}"
        f"      ORDER BY hash(CAST(c.developer_id AS VARCHAR) || '{HASH_SALT}')"
        f"    ) AS rn, t.target_n"
        f"  FROM cohort c JOIN targets t USING ({stratify_col})"
        f") "
        f"SELECT * EXCLUDE (rn, target_n) FROM ranked WHERE rn <= target_n"
    )
    df = con.execute(sql).fetchdf()
    if len(df) > target:
        sql_trim = (
            "WITH sampled AS ("
            f"  WITH cohort AS (SELECT {select_sql} FROM {PROFILE_TABLE} WHERE {where_sql}), "
            f"  targets AS ("
            f"    SELECT {stratify_col},"
            f"      GREATEST(1, CAST(ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () * {target}) AS BIGINT)) AS target_n"
            f"    FROM cohort GROUP BY {stratify_col}"
            f"  ), "
            f"  ranked AS ("
            f"    SELECT c.*,"
            f"      ROW_NUMBER() OVER ("
            f"        PARTITION BY c.{stratify_col}"
            f"        ORDER BY hash(CAST(c.developer_id AS VARCHAR) || '{HASH_SALT}')"
            f"      ) AS rn, t.target_n"
            f"    FROM cohort c JOIN targets t USING ({stratify_col})"
            f"  ) "
            f"  SELECT * EXCLUDE (rn, target_n) FROM ranked WHERE rn <= target_n"
            ") "
            f"SELECT * EXCLUDE (rn) FROM ("
            f"  SELECT *, ROW_NUMBER() OVER ("
            f"    ORDER BY hash(CAST(developer_id AS VARCHAR) || '{HASH_SALT}')"
            f"  ) AS rn FROM sampled"
            f") WHERE rn <= {target}"
        )
        df = con.execute(sql_trim).fetchdf()
    return cohort_n, df


def fit_clusterer(X: np.ndarray, sample_n: int, cfg: dict):
    mcs = max(30, int(sample_n * cfg["min_cluster_frac"]))
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=mcs,
        min_samples=cfg["min_samples"],
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=cfg["cluster_selection_epsilon"],
        prediction_data=True,
        core_dist_n_jobs=1,
    )
    labels = clusterer.fit_predict(X)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_pct = round(100.0 * (labels == -1).sum() / len(labels), 2)
    return labels, n_clusters, noise_pct, mcs, clusterer

print("Helpers ready.")
"""))

cells.append(md("""## 3. Reference fit (100k sample)

Reproduce tuning metrics: fit **preprocessor + HDBSCAN on the same 100k** persona-stratified sample used in `clustering_v3.ipynb` (`HASH_SALT=42`). Do **not** use full-cohort medians/IQR — that changes the scaled space and invalidates tuned ε / noise targets."""))

cells.append(code("""
con = duckdb.connect(DB_PATH)
con.execute("SET preserve_insertion_order=false")

REFERENCE = {}
ref_rows = []

for stratum_key, cfg in FINAL_MODELS.items():
    feats = cfg["features"]
    print(f"\\n{stratum_key}:")

    cohort_n = cohort_count(con, cfg["where_sql"])
    _, df100 = sample_stratum_100k(con, cfg["where_sql"], cfg["stratify_col"], feats)
    X100, names_kept, pre, fit_cols, var_keep = build_matrix_fit(df100, feats)

    labels, nc, noise, mcs, clusterer = fit_clusterer(X100, len(df100), cfg)

    REFERENCE[stratum_key] = {
        "preprocessor": pre,
        "fit_cols": fit_cols,
        "names_kept": names_kept,
        "var_keep": var_keep,
        "clusterer": clusterer,
        "cfg": cfg,
        "min_cluster_size": mcs,
        "X100": X100,
        "labels": labels,
        "meta_100k": df100[["developer_id", "persona", "dormancy_status"]].copy(),
    }
    ref_rows.append({
        "stratum": stratum_key,
        "cohort_n": cohort_n,
        "sample_n_100k": len(df100),
        "n_features_used": len(names_kept),
        "n_clusters": nc,
        "noise_pct": noise,
        "reference_clusters": cfg["reference_clusters"],
        "reference_noise_pct": cfg["reference_noise_pct"],
        "delta_clusters": nc - cfg["reference_clusters"],
        "delta_noise_pct": round(noise - cfg["reference_noise_pct"], 2),
        "min_cluster_size": mcs,
    })
    print(f"  cohort_n={cohort_n:,}; 100k preprocess+HDBSCAN: clusters={nc} noise={noise}%")

con.close()

ref_df = pd.DataFrame(ref_rows)
ref_df.to_csv(OUTPUT_DIR / "reference_100k_fit.csv", index=False)
display(ref_df)
"""))

cells.append(md("""## 4. Cluster full cohort (batched `approximate_predict`)

Assign every developer in each stratum using the model fit on the 100k reference sample. Batched rows use the **same 100k-fitted** imputer + `RobustScaler`, then `approximate_predict`."""))

cells.append(code("""
con = duckdb.connect(DB_PATH)
con.execute("SET preserve_insertion_order=false")

all_results = []
full_summary = []

for stratum_key, cfg in FINAL_MODELS.items():
    ref = REFERENCE[stratum_key]
    names = ref["names_kept"]
    clusterer = ref["clusterer"]
    where = cfg["where_sql"]
    feats = cfg["features"]

    cohort_n = cohort_count(con, where)
    print(f"\\n{'=' * 60}\\n{stratum_key}: assigning cohort_n={cohort_n:,}\\n{'=' * 60}")

    out_parts = []
    offset = 0
    total_noise = 0
    total_n = 0
    cluster_counts = {}

    while offset < cohort_n:
        batch = load_cohort_batch(con, where, feats, offset, PREDICT_BATCH_SIZE)
        if batch.empty:
            break
        refd = REFERENCE[stratum_key]
        Xb = transform_preprocessed(
            batch, refd["fit_cols"], refd["preprocessor"], refd["var_keep"]
        )
        labels, _ = hdbscan.approximate_predict(clusterer, Xb)

        batch_out = batch[["developer_id", "persona", "dormancy_status"]].copy()
        batch_out["dormancy_segment"] = stratum_key
        batch_out["hdbscan_cluster"] = labels
        batch_out["noise_flag"] = (labels == -1).astype(int)
        out_parts.append(batch_out)

        total_n += len(labels)
        total_noise += (labels == -1).sum()
        for cid in labels:
            cluster_counts[int(cid)] = cluster_counts.get(int(cid), 0) + 1

        offset += len(batch)
        if offset % 200_000 == 0 or offset >= cohort_n:
            print(f"  processed {min(offset, cohort_n):,} / {cohort_n:,}")

    stratum_results = pd.concat(out_parts, ignore_index=True)
    stratum_dir = OUTPUT_DIR / stratum_key
    stratum_dir.mkdir(parents=True, exist_ok=True)
    stratum_results.to_parquet(stratum_dir / "cluster_results_full.parquet", index=False)

    noise_pct = round(100.0 * total_noise / total_n, 2)
    n_clusters = len([c for c in cluster_counts if c >= 0])
    full_summary.append({
        "stratum": stratum_key,
        "feature_set_type": cfg["feature_set_type"],
        "n_features_used": len(names),
        "cohort_n": cohort_n,
        "assigned_n": total_n,
        "n_clusters": n_clusters,
        "noise_pct_full": noise_pct,
        "noise_pct_100k_ref": ref_df.loc[ref_df.stratum == stratum_key, "noise_pct"].iloc[0],
        "min_cluster_size": ref["min_cluster_size"],
        "cluster_selection_epsilon": cfg["cluster_selection_epsilon"],
        "min_samples": cfg["min_samples"],
    })

    joblib.dump(
        {
            "preprocessor": ref["preprocessor"],
            "fit_cols": ref["fit_cols"],
            "feature_names": names,
            "var_keep": ref["var_keep"],
            "clusterer": clusterer,
            "config": cfg,
            "reference_100k": ref_df.loc[ref_df.stratum == stratum_key].to_dict(),
        },
        stratum_dir / "model.joblib",
    )
    pd.Series(names, name="feature").to_csv(stratum_dir / "features_used.csv", index=False)

    all_results.append(stratum_results)

con.close()

combined = pd.concat(all_results, ignore_index=True)
combined.to_parquet(OUTPUT_DIR / "cluster_results_all_strata.parquet", index=False)

summary_df = pd.DataFrame(full_summary)
summary_df.to_csv(OUTPUT_DIR / "full_cohort_summary.csv", index=False)

print(f"\\nSaved: {OUTPUT_DIR.resolve()}")
display(summary_df)
display(combined.groupby(["dormancy_segment", "hdbscan_cluster"]).size().head(20))
"""))

cells.append(md("""## 5. Quick validation (full cohort labels)

Compare 100k reference metrics to full-cohort assignment noise and show largest cluster shares."""))

cells.append(code("""
val_rows = []
for stratum_key in FINAL_MODELS:
    path = OUTPUT_DIR / stratum_key / "cluster_results_full.parquet"
    df = pd.read_parquet(path)
    sizes = df["hdbscan_cluster"].value_counts()
    largest = sizes.max()
    val_rows.append({
        "stratum": stratum_key,
        "n": len(df),
        "n_clusters": df.loc[df["hdbscan_cluster"] >= 0, "hdbscan_cluster"].nunique(),
        "noise_pct": round(100 * (df["hdbscan_cluster"] == -1).mean(), 2),
        "largest_cluster_pct": round(100 * largest / len(df), 2),
        "largest_cluster_id": int(sizes.idxmax()),
    })

val_df = pd.DataFrame(val_rows)
val_df = val_df.merge(ref_df[["stratum", "noise_pct", "n_clusters"]], on="stratum", suffixes=("_full", "_100k"))
val_df.to_csv(OUTPUT_DIR / "validation_full_vs_100k.csv", index=False)
display(val_df)

for sk in FINAL_MODELS:
    df = pd.read_parquet(OUTPUT_DIR / sk / "cluster_results_full.parquet")
    print(f"\\n--- {sk}: persona vs cluster ---")
    display(pd.crosstab(df["persona"], df["hdbscan_cluster"], normalize="columns").round(2))
"""))

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "cells": cells,
}

out = Path(__file__).resolve().parents[1] / "clustering_final.ipynb"
out.write_text(json.dumps(nb, indent=2))
print("Wrote", out, "cells", len(cells))
