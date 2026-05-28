#!/usr/bin/env python3
"""Generate hmm_gaussian_v1_weekly_gapaware_reproducible.ipynb."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hmm_gaussian_v1_weekly_gapaware_reproducible.ipynb"


def md(s: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": [s + "\n"]}


def code(s: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [line + "\n" for line in s.splitlines()],
    }


cells = []

cells.append(md("""# HMM Gaussian V1 — Weekly Behavior Sequences

**Goal:** Train a Gaussian HMM on **continuous weekly behavior features** (not GMM cluster IDs).

- **Observations:** `dev_weekly_features_v2` (activity counts, effort, build/product signals per week)
- **Interpretation anchor:** `dev_lifecycle_cluster_membership_v11_final` (V11 stratum + cluster labels)

```text
Weekly behavior features = observed continuous signal each week
Gaussian HMM = hidden journey-state transition model
V11 cluster = static developer segment for business interpretation
```

Designed for local runs or Google Colab (Drive parquet + optional DuckDB).

**V2-style improvements:**
- auto-detect weekly features (DuckDB table first, parquet fallback)
- gap-aware weekly timelines with `has_activity_week`
- reproducible hash-based developer sampling"""))

cells.append(md("## 1) Colab setup (optional)"))

cells.append(code("""# If running in Colab, uncomment:
# from google.colab import drive
# drive.mount('/content/drive')

# Example Drive project folder (match other HMM notebooks):
# PROJECT_DIR = "/content/drive/MyDrive/NVIDIA Industry Project"

PROJECT_DIR = "."
print("PROJECT_DIR:", PROJECT_DIR)"""))

cells.append(md("## 2) Install packages (Colab)"))

cells.append(code("""# In Colab, uncomment one of:
# !pip install -r "/content/drive/MyDrive/NVIDIA Industry Project/requirements_hmm_gaussian_v1.txt"
# !pip install duckdb pandas numpy scikit-learn hmmlearn matplotlib pyarrow"""))

cells.append(md("## 3) Imports and parameters"))

cells.append(code("""from pathlib import Path
import warnings

import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from hmmlearn.hmm import GaussianHMM

warnings.filterwarnings("ignore")

pd.set_option("display.max_columns", 200)

SEED = 42
np.random.seed(SEED)

PROJECT_DIR = Path(PROJECT_DIR)
DB_PATH = PROJECT_DIR / "developer_project.duckdb"
PARQUET_DIR = PROJECT_DIR

WEEKLY_TABLE = "dev_weekly_features_v2"
V11_FINAL_TABLE = "dev_lifecycle_cluster_membership_v11_final"

VALID_STRATA = ["active", "cooling", "at_risk"]
MIN_WEEKS_PER_DEV = 6
MAX_WEEKS_LOOKBACK = 104
MAX_DEVELOPERS = 25000

N_HIDDEN_STATE_OPTIONS = [2, 3, 4, 5]
RESTART_SEEDS = [42, 52, 62]
HMM_N_ITER = 200

LOAD_FROM_PARQUET = False  # set True in Colab if loading parquet into DuckDB

OUTPUT_DIR = PROJECT_DIR / "outputs" / "hmm_gaussian_v1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("DB_PATH:", DB_PATH)
print("PARQUET_DIR:", PARQUET_DIR)
print("OUTPUT_DIR:", OUTPUT_DIR)"""))

cells.append(md("## 4) Connect to DuckDB"))

cells.append(code("""con = duckdb.connect(str(DB_PATH))
print("Connected:", DB_PATH)"""))

cells.append(md("""## 5) Load tables (auto-detect)

**Required for Gaussian HMM:**
- `dev_weekly_features_v2` (DuckDB table or `dev_weekly_features_v2.parquet`)
- `dev_lifecycle_cluster_membership_v11_final` (DuckDB table or parquet)

**Not required:** `dev_gmm_weekly_clusters_v1.parquet` (categorical HMM only)"""))

cells.append(code("""def table_exists(table_name: str) -> bool:
    n = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema='main' AND table_name='" + table_name + "'"
    ).fetchone()[0]
    return n > 0


def load_table_from_parquet(table_name: str, parquet_name: str | None = None) -> bool:
  parquet_name = parquet_name or f"{table_name}.parquet"
  parquet_path = PARQUET_DIR / parquet_name
  if not parquet_path.exists():
      print(f"Missing parquet: {parquet_path}")
      return False
  print(f"Loading {parquet_path.name} -> {table_name}")
  sql = (
      "CREATE OR REPLACE TABLE " + table_name + " AS "
      "SELECT * FROM read_parquet('" + parquet_path.as_posix() + "')"
  )
  con.execute(sql)
  return True


# V11 final membership
if table_exists(V11_FINAL_TABLE):
    print(f"Found table: {V11_FINAL_TABLE}")
elif load_table_from_parquet(V11_FINAL_TABLE):
    print(f"Loaded table from parquet: {V11_FINAL_TABLE}")
else:
    raise RuntimeError(f"Required table missing: {V11_FINAL_TABLE}")

# Weekly features: DuckDB first, parquet fallback
if table_exists(WEEKLY_TABLE):
    print(f"Found table: {WEEKLY_TABLE}")
elif load_table_from_parquet(WEEKLY_TABLE):
    print(f"Loaded table from parquet: {WEEKLY_TABLE}")
else:
    raise RuntimeError(
        f"Required weekly features missing. Add {WEEKLY_TABLE} to DuckDB or upload "
        f"{WEEKLY_TABLE}.parquet to {PARQUET_DIR}"
    )

print("Required tables ready.")"""))

cells.append(md("## 6) Validate schemas and coverage"))

cells.append(code('''weekly_summary = con.execute(f"""
SELECT
    COUNT(*) AS n_rows,
    COUNT(DISTINCT developer_id) AS n_developers,
    MIN(week_start) AS min_week,
    MAX(week_start) AS max_week
FROM {WEEKLY_TABLE}
""").fetchdf()
display(weekly_summary)

v11_summary = con.execute(f"""
SELECT stratum, COUNT(*) AS n_developers
FROM {V11_FINAL_TABLE}
GROUP BY 1
ORDER BY n_developers DESC
""").fetchdf()
display(v11_summary)

weekly_cols = con.execute(
    f"SELECT column_name FROM information_schema.columns WHERE table_name='{WEEKLY_TABLE}'"
).fetchdf()["column_name"].tolist()
print("Weekly columns:", weekly_cols)'''))

cells.append(md("## 7) Build model-input view (join weekly + V11)"))

cells.append(code('''valid_strata_sql = ", ".join([f"'{s}'" for s in VALID_STRATA])

con.execute(f"""
CREATE OR REPLACE TEMP TABLE hmm_gaussian_input_temp AS
SELECT
    w.developer_id,
    CAST(w.week_start AS DATE) AS week_start,
    CAST(w.activity_count_total AS DOUBLE) AS activity_count_total,
    CAST(w.activity_score_sum AS DOUBLE) AS activity_score_sum,
    CAST(w.unique_activity_types AS DOUBLE) AS unique_activity_types,
    CAST(w.build_count AS DOUBLE) AS build_count,
    CAST(w.champion_count AS DOUBLE) AS champion_count,
    CAST(w.high_effort_count AS DOUBLE) AS high_effort_count,
    CAST(w.product_use_count AS DOUBLE) AS product_use_count,
    c.stratum,
    c.cluster_key,
    c.cluster_probability,
    c.outlier_score
FROM {WEEKLY_TABLE} w
INNER JOIN {V11_FINAL_TABLE} c
  ON CAST(w.developer_id AS VARCHAR) = CAST(c.developer_id AS VARCHAR)
WHERE lower(c.stratum) IN ({valid_strata_sql})
  AND w.week_start >= (CURRENT_DATE - INTERVAL '{MAX_WEEKS_LOOKBACK * 7} days')
""")

input_summary = con.execute("""
SELECT stratum, COUNT(*) AS n_rows, COUNT(DISTINCT developer_id) AS n_developers
FROM hmm_gaussian_input_temp
GROUP BY 1
ORDER BY n_developers DESC
""").fetchdf()
display(input_summary)'''))

cells.append(md("## 8) Reproducible developer sampling"))

cells.append(code('''eligible_devs = con.execute(f"""
WITH dev_counts AS (
    SELECT developer_id, COUNT(*) AS n_weeks
    FROM hmm_gaussian_input_temp
    GROUP BY 1
    HAVING COUNT(*) >= {MIN_WEEKS_PER_DEV}
)
SELECT developer_id, n_weeks
FROM dev_counts
ORDER BY hash(CAST(developer_id AS VARCHAR) || '{SEED}')
LIMIT {MAX_DEVELOPERS}
""").fetchdf()

print("Sampled developers:", len(eligible_devs))
con.register("eligible_devs_sample", eligible_devs)'''))

cells.append(md("## 9) Load sampled rows + gap-aware weekly expansion"))

cells.append(code('''base_df = con.execute("""
SELECT h.*
FROM hmm_gaussian_input_temp h
INNER JOIN eligible_devs_sample e USING (developer_id)
ORDER BY h.developer_id, h.week_start
""").fetchdf()

print("Observed weekly rows:", len(base_df))

# Derived continuous features on observed weeks
base_df["week_start"] = pd.to_datetime(base_df["week_start"])
for c in [
    "activity_count_total", "activity_score_sum", "unique_activity_types",
    "build_count", "champion_count", "high_effort_count", "product_use_count",
]:
    base_df[c] = pd.to_numeric(base_df[c], errors="coerce").fillna(0.0)

base_df["log_activity_count"] = np.log1p(base_df["activity_count_total"])
base_df["log_activity_score_sum"] = np.log1p(base_df["activity_score_sum"])
denom = base_df["activity_count_total"].replace(0, np.nan)
base_df["build_share"] = (base_df["build_count"] / denom).fillna(0.0)
base_df["high_effort_share"] = (base_df["high_effort_count"] / denom).fillna(0.0)
base_df["product_use_share"] = (base_df["product_use_count"] / denom).fillna(0.0)
base_df["has_activity_week"] = (base_df["activity_count_total"] > 0).astype(float)

feature_cols = [
    "log_activity_count",
    "log_activity_score_sum",
    "unique_activity_types",
    "build_share",
    "high_effort_share",
    "product_use_share",
    "has_activity_week",
]

static_cols = ["stratum", "cluster_key", "cluster_probability", "outlier_score"]

expanded_parts = []
for dev_id, g in base_df.groupby("developer_id", sort=False):
    g = g.sort_values("week_start")
    full_weeks = pd.date_range(g["week_start"].min(), g["week_start"].max(), freq="W-MON")
    frame = pd.DataFrame({"week_start": full_weeks})
    frame["developer_id"] = dev_id
    merged = frame.merge(g, on=["developer_id", "week_start"], how="left")

    for col in static_cols:
        if col in merged.columns:
            merged[col] = merged[col].ffill().bfill()

    merged["missing_week_flag"] = merged["activity_count_total"].isna().astype(int)
    for col in feature_cols:
        if col == "has_activity_week":
            merged[col] = merged[col].fillna(0.0)
        else:
            merged[col] = merged[col].fillna(0.0)

    expanded_parts.append(merged)

hmm_df = pd.concat(expanded_parts, ignore_index=True)
hmm_df = hmm_df.sort_values(["developer_id", "week_start"]).reset_index(drop=True)
print("Gap-filled weekly rows:", len(hmm_df))
print("Missing-week rows:", int(hmm_df["missing_week_flag"].sum()))
display(hmm_df.head())'''))

cells.append(md("## 10) Prepare sequences (`X`, `lengths`)"))

cells.append(code("""lengths = hmm_df.groupby("developer_id").size().tolist()
X_raw = hmm_df[feature_cols].astype(float).values

print("X shape:", X_raw.shape)
print("Sequences:", len(lengths))
print("Avg sequence length:", np.mean(lengths))
assert sum(lengths) == X_raw.shape[0]"""))

cells.append(md("## 11) Scale features"))

cells.append(code("""scaler = StandardScaler()
X = scaler.fit_transform(X_raw)
print("Scaled X shape:", X.shape)"""))

cells.append(md("## 12) Fit Gaussian HMM candidates"))

cells.append(code("""def gaussian_hmm_param_count(n_states: int, n_features: int, covariance_type: str = "diag") -> int:
    start_p = n_states - 1
    trans_p = n_states * (n_states - 1)
    mean_p = n_states * n_features
    if covariance_type == "diag":
        cov_p = n_states * n_features
    else:
        cov_p = n_states * (n_features * (n_features + 1) // 2)
    return start_p + trans_p + mean_p + cov_p


fit_rows = []
models = {}

for n_states in N_HIDDEN_STATE_OPTIONS:
    best_local = None
    for seed in RESTART_SEEDS:
        model = GaussianHMM(
            n_components=n_states,
            covariance_type="diag",
            n_iter=HMM_N_ITER,
            random_state=seed,
            tol=1e-3,
            verbose=False,
        )
        try:
            model.fit(X, lengths)
            loglik = float(model.score(X, lengths))
            n_params = gaussian_hmm_param_count(n_states, X.shape[1])
            n_obs = X.shape[0]
            aic = 2 * n_params - 2 * loglik
            bic = np.log(max(n_obs, 2)) * n_params - 2 * loglik

            hidden = model.predict(X, lengths)
            state_counts = pd.Series(hidden).value_counts(normalize=True)
            min_state_share = float(state_counts.min()) if len(state_counts) else 0.0

            row = {
                "n_hidden_states": n_states,
                "seed": seed,
                "loglik": loglik,
                "aic": float(aic),
                "bic": float(bic),
                "converged": bool(getattr(model.monitor_, "converged", False)),
                "n_iter": int(getattr(model.monitor_, "iter", -1)),
                "min_state_share": min_state_share,
                "n_active_states": int((state_counts > 0).sum()),
            }
            fit_rows.append(row)
            if best_local is None or row["bic"] < best_local["bic"]:
                best_local = {**row, "model": model}
        except Exception as err:
            fit_rows.append({
                "n_hidden_states": n_states,
                "seed": seed,
                "loglik": np.nan,
                "aic": np.nan,
                "bic": np.nan,
                "converged": False,
                "n_iter": -1,
                "min_state_share": 0.0,
                "n_active_states": 0,
                "error": str(err),
            })

    if best_local is not None:
        models[n_states] = best_local

results_df = pd.DataFrame(fit_rows).sort_values(["n_hidden_states", "bic"], na_position="last")
display(results_df)"""))

cells.append(md("## 13) Select best model"))

cells.append(code("""candidate_df = results_df.dropna(subset=["bic"]).copy()
if candidate_df.empty:
    raise RuntimeError("No successful Gaussian HMM fits.")

candidate_df = candidate_df[candidate_df["min_state_share"] >= 0.01].copy()
if candidate_df.empty:
    candidate_df = results_df.dropna(subset=["bic"]).copy()

best_row = candidate_df.sort_values(["bic", "aic", "n_hidden_states"]).iloc[0]
BEST_N_STATES = int(best_row["n_hidden_states"])
best_model = models[BEST_N_STATES]["model"]
print(f"Selected n_states={BEST_N_STATES}, bic={best_row['bic']:.2f}")"""))

cells.append(md("## 14) Decode hidden states + emission profiles"))

cells.append(code("""hmm_df["hmm_state"] = best_model.predict(X, lengths)

# Emission profile = mean scaled feature vector per hidden state
emission_profiles = (
    pd.DataFrame(X, columns=[f"z_{c}" for c in feature_cols])
    .assign(hmm_state=hmm_df["hmm_state"].values)
    .groupby("hmm_state", as_index=False)
    .mean()
)

# Unscaled means for business readability
emission_profiles_raw = (
    hmm_df.groupby("hmm_state", as_index=False)[feature_cols]
    .mean()
)

display(emission_profiles)
display(emission_profiles_raw)

state_profiles = (
    hmm_df.groupby("hmm_state", as_index=False)
    .agg(
        n_weekly_rows=("developer_id", "size"),
        n_developers=("developer_id", "nunique"),
        share_missing_weeks=("missing_week_flag", "mean"),
        avg_activity_count=("activity_count_total", "mean"),
        stratum_mode=("stratum", lambda s: s.value_counts().index[0]),
    )
)
state_profiles["share_of_rows"] = state_profiles["n_weekly_rows"] / state_profiles["n_weekly_rows"].sum()
display(state_profiles)"""))

cells.append(md("## 15) Transition matrix"))

cells.append(code("""transition_matrix = pd.DataFrame(
    best_model.transmat_,
    index=[f"from_hmm_state_{i}" for i in range(BEST_N_STATES)],
    columns=[f"to_hmm_state_{i}" for i in range(BEST_N_STATES)],
)
display(transition_matrix)

transition_long = (
    transition_matrix.reset_index()
    .melt(id_vars="index", var_name="to_state", value_name="transition_probability")
    .rename(columns={"index": "from_state"})
)
display(transition_long.sort_values("transition_probability", ascending=False).head(20))"""))

cells.append(md("## 16) Compare hidden states vs V11"))

cells.append(code("""state_by_stratum = (
    hmm_df.groupby(["stratum", "hmm_state"]).size().reset_index(name="n_rows")
)
state_by_stratum["share_within_stratum"] = (
    state_by_stratum["n_rows"] / state_by_stratum.groupby("stratum")["n_rows"].transform("sum")
)
display(state_by_stratum.sort_values(["stratum", "hmm_state"]))

state_by_v11_cluster = (
    hmm_df.groupby(["stratum", "cluster_key", "hmm_state"]).size().reset_index(name="n_rows")
)
state_by_v11_cluster["share_within_cluster"] = (
    state_by_v11_cluster["n_rows"]
    / state_by_v11_cluster.groupby(["stratum", "cluster_key"])["n_rows"].transform("sum")
)
display(
    state_by_v11_cluster.sort_values(
        ["stratum", "cluster_key", "share_within_cluster"], ascending=[True, True, False]
    ).head(100)
)"""))

cells.append(md("## 17) Export CSV summaries (no DuckDB model tables yet)"))

cells.append(code("""results_df.to_csv(OUTPUT_DIR / "hmm_gaussian_model_comparison.csv", index=False)
emission_profiles.to_csv(OUTPUT_DIR / "hmm_gaussian_emission_profiles_z.csv", index=False)
emission_profiles_raw.to_csv(OUTPUT_DIR / "hmm_gaussian_emission_profiles_raw.csv", index=False)
state_profiles.to_csv(OUTPUT_DIR / "hmm_gaussian_state_profiles.csv", index=False)
transition_matrix.to_csv(OUTPUT_DIR / "hmm_gaussian_transition_matrix.csv")
transition_long.to_csv(OUTPUT_DIR / "hmm_gaussian_transition_matrix_long.csv", index=False)
state_by_stratum.to_csv(OUTPUT_DIR / "hmm_gaussian_state_by_stratum.csv", index=False)
state_by_v11_cluster.to_csv(OUTPUT_DIR / "hmm_gaussian_state_by_v11_cluster.csv", index=False)

print("Saved outputs to:", OUTPUT_DIR.resolve())

# con.close()  # optional"""))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT.write_text(json.dumps(nb, indent=1))
print("Wrote", OUT)
