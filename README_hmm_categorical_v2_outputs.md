# HMM Categorical V2 Output Guide

> **Full comparison guide (categorical + Gaussian, all outputs, run findings):** [`README_HMM_GAUSSIAN_AND_CATEGORICAL.md`](README_HMM_GAUSSIAN_AND_CATEGORICAL.md)

This document explains outputs from:

- `hmm_categorical_v2_from_gmm_weekly_gapaware_reproducible.ipynb`
- output folder: `outputs/hmm_categorical_v2/`

## Model Setup (V2)

- **Observed sequence source:** weekly GMM assignments (`dev_gmm_weekly_clusters_v1`)
- **Hidden process model:** `CategoricalHMM` (3 hidden states selected in this run)
- **Interpretation anchor:** `dev_lifecycle_cluster_membership_v11_final`
- **Gap-aware behavior:** missing/no-activity weeks are explicitly represented as an observed category

## Observed Categories Used by HMM

In V2, weekly observations include 4 categories:

- missing/no-activity week
- GMM cluster 0
- GMM cluster 1
- GMM cluster 2

Because `CategoricalHMM` requires non-negative contiguous IDs, observations are remapped to integer IDs before fitting.

Important note: GMM weekly clusters (`0/1/2`) do **not** yet have finalized business names. Treat them as unlabeled behavior modes for now.

## Current Hidden-State Interpretation (Provisional)

Based on current emission probabilities:

- **HMM State 0 = low/mixed engagement**
  - missing/no-activity: 39.8%
  - GMM 0: 53.7%
  - GMM 1: 6.4%
  - GMM 2: 0.06%
  - Rationale: mostly emits GMM 0, but still a sizable missing/no-activity share.

- **HMM State 1 = active observed engagement**
  - missing/no-activity: 0.27%
  - GMM 0: 55.8%
  - GMM 1: 5.5%
  - GMM 2: 38.4%
  - Rationale: almost never emits missing/no-activity; mostly real observed behavior.

- **HMM State 2 = missing/no-activity**
  - missing/no-activity: 96.6%
  - GMM 0: 3.1%
  - GMM 1: 0.03%
  - GMM 2: 0.24%
  - Rationale: overwhelmingly emits missing/no-activity.

These names are practical working labels for analysis and slides, and can be revised after GMM cluster semantics are finalized.

## Output CSVs

### `hmm_categorical_model_comparison.csv`

Model-selection summary across candidate hidden-state counts (e.g., 2/3/4/5 states).

Use this to justify why the selected number of hidden states was chosen (BIC/AIC/log-likelihood tradeoff).

### `hmm_categorical_state_profiles.csv`

Per-hidden-state profile summary, including:

- row volume (`n_weekly_rows`)
- developer coverage (`n_developers`)
- average weekly GMM confidence (`avg_gmm_posterior`)
- most common emitted observed GMM cluster (`most_common_gmm_cluster`)
- dominant lifecycle stratum (`stratum_mode`)
- share of total weekly rows (`share_of_rows`)

Use this for state-level business interpretation.

### `hmm_categorical_emission_probabilities.csv`

Core interpretation artifact for categorical HMM.

- Rows: hidden HMM states
- Columns: observed categories (remapped IDs)
- Values: `P(observation | hidden_state)`

Use this to understand what each hidden state “looks like” in terms of weekly observed behavior.

### `hmm_categorical_transition_matrix.csv`

Square matrix:

- rows = `from` hidden state
- columns = `to` hidden state
- value = one-step transition probability

Use this to understand stability and likely movement between hidden states.

### `hmm_categorical_transition_matrix_long.csv`

Long-format version of transition probabilities:

- `from_state`
- `to_state`
- `transition_probability`

Use this for plotting and ranking top transitions.

### `hmm_categorical_state_by_stratum.csv`

Hidden-state composition within each lifecycle stratum:

- `stratum`
- `hmm_state`
- `n_rows`
- `share_within_stratum`

Use this to compare journey-state mix across `active`, `cooling`, and `at_risk`.

### `hmm_categorical_state_by_v11_cluster.csv`

Hidden-state composition within each V11 cluster:

- `stratum`
- `cluster_key`
- `hmm_state`
- `n_rows`
- `share_within_cluster`

Use this to identify which V11 clusters spend more time in low/missing vs active hidden states.

## Recommended Reading Order

For interpretation, review outputs in this sequence:

1. `hmm_categorical_model_comparison.csv`
2. `hmm_categorical_emission_probabilities.csv`
3. `hmm_categorical_state_profiles.csv`
4. `hmm_categorical_transition_matrix.csv`
5. `hmm_categorical_state_by_stratum.csv`
6. `hmm_categorical_state_by_v11_cluster.csv`

## Caveats

- GMM observed clusters are currently unlabeled behavior modes (no final business names yet).
- Hidden-state names in this README are provisional and should be revisited after GMM semantics are finalized.
- This is an exploratory local-output workflow (CSV artifacts), not a finalized production serving pipeline.
