# HMM Gaussian V1 Output Guide

> **Full comparison guide (categorical + Gaussian, all outputs, run findings):** [`README_HMM_GAUSSIAN_AND_CATEGORICAL.md`](README_HMM_GAUSSIAN_AND_CATEGORICAL.md)

Notebook: [`hmm_gaussian_v1_weekly_gapaware_reproducible.ipynb`](hmm_gaussian_v1_weekly_gapaware_reproducible.ipynb)

Output folder: `outputs/hmm_gaussian_v1/`

## What this model does

- **Observations:** continuous weekly behavior features from `dev_weekly_features_v2`
- **Hidden process:** Gaussian HMM (`GaussianHMM`) over scaled weekly feature vectors
- **Interpretation anchor:** `dev_lifecycle_cluster_membership_v11_final` (V11 stratum + cluster labels only; not used as HMM inputs)

```text
Weekly behavior features -> observed signal each week
Gaussian HMM -> hidden journey states + transitions
V11 cluster -> static segment for interpretation
```

## Data required (Colab / local)

### Required

| File / table | Purpose |
|---|---|
| `dev_lifecycle_cluster_membership_v11_final` (DuckDB or `.parquet`) | V11 anchor (`stratum`, `cluster_key`, etc.) |
| `dev_weekly_features_v2` (DuckDB or `.parquet`) | Continuous weekly observations |

### Recommended

| File | Purpose |
|---|---|
| `developer_project.duckdb` | Auto-load tables if present |

### Not required for Gaussian HMM

| File | Purpose |
|---|---|
| `dev_gmm_weekly_clusters_v1.parquet` | Used by categorical HMM notebooks only |

### Export weekly features (if needed)

```sql
COPY dev_weekly_features_v2
TO 'dev_weekly_features_v2.parquet' (FORMAT PARQUET);
```

Weekly feature columns used:
- `developer_id`, `week_start`
- `activity_count_total`, `activity_score_sum`, `unique_activity_types`
- `build_count`, `champion_count`, `high_effort_count`, `product_use_count`

Derived in notebook:
- `log_activity_count`, `log_activity_score_sum`
- `build_share`, `high_effort_share`, `product_use_share`
- `has_activity_week` (1 = observed activity week, 0 = gap-filled missing week)

## Colab setup

Match other HMM notebooks:

```python
# from google.colab import drive
# drive.mount('/content/drive')
PROJECT_DIR = "/content/drive/MyDrive/NVIDIA Industry Project"
LOAD_FROM_PARQUET = True  # if tables are not already inside DuckDB
```

Install:

```bash
pip install -r requirements_hmm_gaussian_v1.txt
```

## Output CSV files

### `hmm_gaussian_model_comparison.csv`

Model selection across hidden-state counts (`2/3/4/5`) and random seeds.

Key columns:
- `n_hidden_states`, `loglik`, `aic`, `bic`
- `converged`, `n_iter`
- `min_state_share` (interpretability guardrail)

**Lower BIC is better** (penalizes complexity while rewarding fit).

### `hmm_gaussian_emission_profiles_z.csv`

Mean **scaled** feature vector per hidden state (z-scored space used for fitting).

Use to compare relative feature emphasis between hidden states.

### `hmm_gaussian_emission_profiles_raw.csv`

Mean **unscaled** feature values per hidden state (easier business reading).

### `hmm_gaussian_state_profiles.csv`

Volume summary per hidden state:
- `n_weekly_rows`, `n_developers`
- `share_missing_weeks`
- `avg_activity_count`
- `share_of_rows`

### `hmm_gaussian_transition_matrix.csv`

Square transition matrix (`from` hidden state -> `to` hidden state).

### `hmm_gaussian_transition_matrix_long.csv`

Long format of transitions for plotting/ranking.

### `hmm_gaussian_state_by_stratum.csv`

Hidden-state mix within each lifecycle stratum (`active`, `cooling`, `at_risk`).

### `hmm_gaussian_state_by_v11_cluster.csv`

Hidden-state mix within each V11 `cluster_key` (interpretation vs static clustering).

## Recommended reading order

1. `hmm_gaussian_model_comparison.csv`
2. `hmm_gaussian_emission_profiles_raw.csv`
3. `hmm_gaussian_transition_matrix.csv`
4. `hmm_gaussian_state_by_stratum.csv`
5. `hmm_gaussian_state_by_v11_cluster.csv`

## Notes / caveats

- This is exploratory: outputs are CSV summaries only (no DuckDB assignment tables yet).
- Gap-filled weeks are imputed to zero features with `has_activity_week=0`.
- Sampling is reproducible via `hash(developer_id || SEED)`.
- Hidden-state names should be assigned after inspecting emission profiles (not hard-coded in v1).
