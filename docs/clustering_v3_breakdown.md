# Clustering v3 breakdown

**Notebook:** [`clustering_v3.ipynb`](../clustering_v3.ipynb)

**Goal:** Test whether clustering improves when highly correlated behavioral features are removed, compare dormancy-only vs dormancy×persona cohorting, tune HDBSCAN toward **~5–8 clusters per stratum**, and validate the final runs for leakage, stability, and interpretability.

Compared with v2, the main v3 experiments remove the SVD step and run HDBSCAN directly on reduced, scaled feature sets.

**Production baseline (latest):** dormancy-only clustering with **16 correlation-group representatives**, per-stratum hyperparameters from coarse + cooling tuning, saved under `outputs/clustering/v3_final_selected/`.

---

## Notebook flow (high level)

| Section | Notebook topic | Purpose |
| --- | --- | --- |
| 1 | Correlation diagnostics | Pre-reduction correlation matrices |
| 2 | Greedy correlation filtering | First feature reduction (~36/28/21 features per stratum) |
| 3 | Correlation-group representatives | 16 global reps from 107 candidates |
| 4 | Dormancy-only + dormancy×persona HDBSCAN | Baseline grouped-feature runs |
| 5 | Similar-cluster / merge analysis | Cosine ≥0.9 profile similarity review |
| 6 | Meta-clusters | 20 business-level groupings over 108 technical clusters |
| 7 | **Coarse HDBSCAN tuning** | Grid toward ~6–8 clusters; reduce noise vs `v3_corr_groups` |
| 8 | **Cooling expanded tuning** | Feature swaps + broader grid for cooling noise |
| 9 | **Feature audit** | Why 16 requested → 16 / 12 / 11 used per stratum |
| 10 | **Final selected configs + validation** | Locked hyperparameters, leakage, stability, sanity |

---

## 1. Correlation diagnostics

The notebook builds correlation matrices for numeric clustering features from `dev_profile_final_v4` (pre-SVD space).

**Output:** `outputs/clustering/v3/correlation/`

---

## 2. Greedy correlation filtering

Greedy selection enforces pairwise `abs(correlation) < 0.50`. Usable feature count still varies by stratum (all-null / zero-variance drops).

**Output:** `outputs/clustering/v3/`

| Dormancy | Sample | Features used | Clusters | Noise % |
| --- | ---: | ---: | ---: | ---: |
| Active | 99,999 | 36 | 60 | 25.58 |
| Cooling | 100,000 | 28 | 27 | 25.12 |
| Dormant | 100,000 | 21 | 39 | 39.08 |
| **Total / weighted** | **299,999** | - | **126** | **29.93** |

---

## 3. Correlation-group representative features

Features are grouped into connected components at `abs(correlation) >= 0.50`; one representative is chosen per group. **107 candidates → 16 representatives.**

```text
log_activity_count_30_90d
mixed_persona_flag
cuda_share
activity_velocity_0_30_vs_30_90
build_velocity_0_30_vs_30_90
days_since_last_activity_0_30d
learning_community_share
lifetime_bug_count
lifetime_dli_training_count
lifetime_forum_count
lifetime_hackathon_count
lifetime_learn_count
lifetime_webinar_count
recent_champion_flag
robotics_share
simulation_share
```

The largest group (`corr_group_001`) contains **89** activity, effort, recency, and lifetime features; representative = `log_activity_count_30_90d`.

**Outputs:**

- `outputs/clustering/v3/feature_selection_grouped/v3_correlation_groups_abs_corr_ge_0_50.csv`
- `outputs/clustering/v3/feature_selection_grouped/v3_group_representative_features.txt`

---

## Main v3 results (baseline grouped features)

### Dormancy-only clustering

**Output:** `outputs/clustering/v3_corr_groups/`

| Dormancy | Sample | Features used | Clusters | Noise % |
| --- | ---: | ---: | ---: | ---: |
| Active | 99,999 | 16 | 47 | 8.36 |
| Cooling | 100,000 | 12 | 28 | 14.42 |
| Dormant | 100,000 | 11 | 33 | 28.26 |
| **Total / weighted** | **299,999** | - | **108** | **17.01** |

Strongest baseline for **active** users (8.36% noise). Cooling/dormant use fewer than 16 features after stratum-specific zero-variance / all-null drops.

### Dormancy × persona clustering

**Output:** `outputs/clustering/v3_corr_groups_by_persona/`

| Dormancy | Cohorts | Sample | Clusters | Simple avg noise % | Weighted noise % |
| --- | ---: | ---: | ---: | ---: | ---: |
| Active | 6 | 226,016 | 252 | 20.93 | 16.12 |
| Cooling | 6 | 300,044 | 123 | 19.97 | 16.74 |
| Dormant | 6 | 600,000 | 121 | 15.37 | 15.37 |
| **Total** | **18** | **1,126,060** | **496** | **18.76** | **15.89** |

Tradeoff: more granular persona-specific clusters, but active noise rises vs dormancy-only (16.12% vs 8.36% weighted).

---

## Coarse HDBSCAN tuning (~6–8 clusters)

**Notebook section:** Coarse HDBSCAN tuning  
**Output:** `outputs/clustering/v3_coarse_hdbscan/`

Grid over `min_cluster_frac` ∈ {0.005, 0.05, 0.10, 0.12, 0.15} and `cluster_selection_epsilon` ∈ {0.0, 0.25, 0.5, 0.75}, with the same 16 requested features and persona-stratified 100k samples.

**Best grid row per stratum (in-target cluster count 6–8):**

| Stratum | Sample | Features | Clusters | Noise % | min_cluster_frac | min_cluster_size | ε | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Active | 99,999 | 16 | 8 | 7.46 | 0.005 | 499 | 0.50 | In-target; user later preferred **5** clusters |
| Cooling | 100,000 | 12 | 6 | 21.42 | 0.050 | 5000 | 0.50 | Noise rose vs baseline 14.42% |
| Dormant | 100,000 | 11 | 6 | 10.01 | 0.050 | 5000 | 0.25 | Large noise drop vs baseline 28.26% |

**vs `v3_corr_groups` baseline (same features, default-style HDBSCAN):**

| Stratum | Δ clusters | Δ noise % |
| --- | ---: | ---: |
| Active | −39 | −0.90 |
| Cooling | −22 | +7.00 |
| Dormant | −27 | −18.25 |

Coarse tuning sharply reduced cluster count and dormant noise; **cooling noise increased** and motivated the dedicated cooling pass below.

**Key outputs:**

- `hdbscan_tuning_grid_all.csv`
- `hdbscan_tuning_best_per_stratum.csv`
- `run_summary.csv`
- Per-stratum `cluster_results.parquet`, `features_used.csv`, `preprocessor.joblib`

---

## Feature audit (16 reps → features actually used)

**Notebook section:** Feature audit  
**Output:** `outputs/clustering/v3_feature_audit/`

Same **16 representatives requested** for all strata; after median impute + `RobustScaler`, zero-variance features are dropped **per stratum**.

| Stratum | Requested | Used | Dropped | Drop reasons |
| --- | ---: | ---: | ---: | --- |
| Active | 16 | **16** | 0 | — |
| Cooling | 16 | **12** | 4 | `activity_velocity_0_30_vs_30_90`, `build_velocity_0_30_vs_30_90` (zero variance); `days_since_last_activity_0_30d` (all null); `recent_champion_flag` (zero variance) |
| Dormant | 16 | **11** | 5 | Above four + `log_activity_count_30_90d` (zero variance in dormant) |

Singleton correlation groups (velocity, `days_since_last_activity_0_30d`, `recent_champion_flag`) have **no alternate rep** in the grouped list; cooling swaps were tested separately in the cooling tuning cell (see below). Alternatives for recency/activity exist inside `corr_group_001` but were not auto-substituted in the baseline 16-rep pipeline.

**Outputs:** `sixteen_feature_audit_by_stratum.csv`, `feature_count_summary_by_stratum.csv`, `feature_kept_heatmap_by_stratum.png`

---

## Cooling expanded tuning

**Notebook section:** Cooling stratum: expanded tuning + feature recovery  
**Output:** `outputs/clustering/v3_cooling_tuning/`

Motivation: coarse best cooling hit **21.42% noise**; four of sixteen reps are unusable in cooling.

**Feature sets compared (phase 1 screen):**

- `baseline_16_reps` — auto-drops to 12 (same as coarse)
- `cooling_swap_16` — replace dead reps with `activity_count_30_90d`, `build_count_30_90d`, `days_since_last_activity`, `lifetime_champion_count`
- `cooling_enriched_18` / `cooling_recency_18` — swap + extra axes
- `cooling_auto_resolve_16` — backup map from `corr_group_001`

**Finding:** On a full background grid, **baseline 12-feature reps** with retuned params beat swap/enriched sets for noise at ~6–8 clusters. Swap sets often **increased** noise (~27–31%). Production cooling config uses **baseline reps + tuning**, not swap-16.

**Recommended cooling hyperparameters (from tuning + final fit):**

| Parameter | Value |
| --- | ---: |
| `min_cluster_frac` | 0.04 |
| `min_cluster_size` | 4000 |
| `cluster_selection_epsilon` | 0.50 |
| `min_samples` | 10 |

---

## Final selected HDBSCAN configs (production)

**Notebook section:** Final selected HDBSCAN configs + validation  
**Output:** `outputs/clustering/v3_final_selected/`

Locked per-stratum settings used for reporting and validation:

| Stratum | Clusters (fit) | Noise % | Features used | min_cluster_frac | min_cluster_size | ε | min_samples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Active** | **5** | **5.72** | 16 | 0.005 | 499 | **0.75** | 15 |
| **Cooling** | **6** | **16.29** | 12 | 0.04 | 4000 | 0.50 | 10 |
| **Dormant** | **6** | **5.71** | 11 | 0.050 | 5000 | 0.50 | 25 |

**Notes:**

- Active uses **5 clusters** (user choice from grid row with 5 clusters / 6.15% noise at ε=0.75), not the coarse “best in-range” 8-cluster solution.
- Cooling/dormant **cluster counts** may differ by ±1 from a single tuning grid row on rerun; final fit produced **6** clusters each vs tuning notes of 7 (cooling) and 5 (dormant).
- **Cluster size imbalance** is strong (especially active: ~77% in one cluster). See validation outputs for persona mix per cluster.

**Per-stratum artifacts:** `{stratum}/cluster_results.parquet`, `features_used.csv`, `run_config.json`, `preprocessor.joblib`  
**Summary:** `final_run_summary.csv`

---

## Validation (final selected runs)

**Output:** `outputs/clustering/v3_final_validation/`

Run final-fit cell before validation cells (or load from `v3_final_selected/` parquet).

### 1. Leakage and cohort-definition audit

| Check | Result |
| --- | --- |
| Stratum flags in X (`cooling_flag`, `dormant_flag`, `has_activity_0_30d`, `dormancy_status`) | **Not** in the 16 reps; constant in cohort SQL only |
| Persona in distance matrix | **Excluded** (persona used for sampling only) |
| Persona vs cluster (Cramér’s V) | Active **0.20 (low)**; Cooling **0.55 (high)**; Dormant **0.52 (high)** |
| Single-feature dominance (high \|corr\| with cluster id) | Active: `mixed_persona_flag`, lifetime learn/DLI; Cooling: **`robotics_share`**; Dormant: **`simulation_share`** |

Cooling/dormant clusters align with **persona-flavored** axes (shares + lifetime channels), not a leak of `dormancy_status`.

### 2. Stability and overfitting

| Stratum | Bootstrap ARI (mean) | Interpretation |
| --- | ---: | --- |
| Active | 0.98 | Very stable |
| Cooling | 0.81 | Stable (more variable than active) |
| Dormant | 0.92 | Stable |

**Holdout test (70/30 + `approximate_predict`):** holdout noise **100%** for all strata — indicates the split/predict setup is **not informative**, not that the full model assigns everyone to noise. **Trust bootstrap ARI** for stability conclusions.

**Permutation silhouette (largest drops when shuffling one feature):**

| Stratum | Top driving features |
| --- | --- |
| Active | Small drops across features (~0.01–0.02) — structure spread across many axes |
| Cooling | `learning_community_share`, `robotics_share`, `mixed_persona_flag` |
| Dormant | `lifetime_learn_count`, `simulation_share`, `mixed_persona_flag` |

### 3. Sanity checks

| Stratum | cluster_count pass | noise_pct pass | min_cluster_size rule | Silhouette (non-noise) |
| --- | --- | --- | --- | ---: |
| Active | ✓ (5) | ✓ | ✓ | 0.18 |
| Cooling | ✗ (6 vs 7 expected) | ✓ | ✓ | 0.35 |
| Dormant | ✗ (6 vs 5 expected) | ✓ | ✓ | 0.34 |

**Outputs:** `leakage_feature_audit.csv`, `persona_cluster_association.csv`, `stability_summary.csv`, `permutation_silhouette_drops.csv`, `sanity_checks.csv`, `cluster_size_distribution.csv`

---

## Persona noise pattern (dormancy × persona baseline)

| Persona group | Cohorts | Sample | Clusters | Weighted noise % |
| --- | ---: | ---: | ---: | ---: |
| Robotics | 3 | 158,875 | 72 | 32.84 |
| CUDA | 3 | 258,072 | 108 | 25.82 |
| Learning_Community | 3 | 136,438 | 122 | 18.49 |
| Simulation | 3 | 119,408 | 63 | 8.96 |
| GenAI | 3 | 300,000 | 87 | 7.66 |
| Unknown_or_Other | 3 | 153,267 | 44 | 0.75 |

Robotics remains the noisiest persona split (`cooling_robotics` up to **55.92%** in baseline persona runs).

---

## Similar cluster / merge analysis

Cosine similarity on cluster `mean_*` profiles; `profile_cosine_similarity >= 0.90` flags near-duplicate **review** pairs (does not relabel HDBSCAN).

**Output:** `outputs/clustering/v3_analysis/`

| Method | Original clusters | Merged (review) clusters |
| --- | ---: | ---: |
| Dormancy-only | 108 | 54 |
| Dormancy × persona | 496 | 302 |

---

## Dormancy-only meta-clusters

Agglomerative clustering on **108** non-noise HDBSCAN cluster profiles → **20 meta-clusters** for business-facing labels.

**Output:** `outputs/clustering/v3_meta_clusters/`

| Input technical clusters | Meta-clusters |
| ---: | ---: |
| 108 | 20 |

Does not overwrite HDBSCAN labels; adds `meta_cluster_id` / `meta_cluster_label` on developer results.

---

## Interpretation (updated)

1. **Feature reduction:** Correlation-group reps are the main v3 win vs greedy filter or SVD-heavy v2.
2. **Coarse tuning:** Cuts cluster explosion and dormant noise; active can be tuned to **fewer, cleaner** clusters (5 at ε=0.75).
3. **Cooling:** Still the hardest stratum — **~16% noise**, persona-linked clusters, **`robotics_share` / `learning_community_share`** dominate separation. Swap-in of extra `corr_group_001` features did not beat 12 baseline reps in grids.
4. **Final production layer:** Use `v3_final_selected` for **5 / 6 / 6** clusters (active / cooling / dormant) with documented hyperparameters.
5. **Validation:** No stratum-label leakage in X; bootstrap stability good; holdout predict test not reliable as implemented; describe cooling/dormant as **persona-tinged** segments.
6. **Imbalance:** Expect one **dominant cluster per stratum** (e.g. active cluster 2 ≈ 77% GenAI-heavy) plus smaller niches and ~6–16% noise.
7. **Meta-clusters:** Still useful to roll 108 baseline technical clusters into **20** business themes; can be recomputed on top of final selected HDBSCAN labels when those replace the original `v3_corr_groups` assignment in downstream work.

**Recommended use:**

- **Lifecycle reporting:** `v3_final_selected` dormancy-only runs.
- **Persona diagnostics:** `v3_corr_groups_by_persona` and persona validation tables.
- **Business naming:** meta-cluster layer + cluster profile CSVs + persona crosstabs from validation.

---

## Primary output files

| File | Description |
| --- | --- |
| `outputs/clustering/v3/run_summary.csv` | Greedy correlation-filter run summary |
| `outputs/clustering/v3_corr_groups/run_summary.csv` | Dormancy-only grouped-feature baseline |
| `outputs/clustering/v3_corr_groups/cluster_summary_table_all.csv` | Baseline dormancy-only cluster profiles |
| `outputs/clustering/v3_corr_groups_by_persona/run_summary.csv` | Dormancy × persona run summary |
| `outputs/clustering/v3_coarse_hdbscan/hdbscan_tuning_grid_all.csv` | Coarse hyperparameter grid |
| `outputs/clustering/v3_coarse_hdbscan/hdbscan_tuning_best_per_stratum.csv` | Best coarse config per stratum |
| `outputs/clustering/v3_feature_audit/sixteen_feature_audit_by_stratum.csv` | Per-feature kept/dropped by stratum |
| `outputs/clustering/v3_cooling_tuning/phase1_feature_set_screen.csv` | Cooling feature-set comparison |
| `outputs/clustering/v3_cooling_tuning/phase2_expanded_param_grid.csv` | Cooling expanded parameter grid |
| `outputs/clustering/v3_final_selected/final_run_summary.csv` | **Final** cluster/noise summary |
| `outputs/clustering/v3_final_selected/{stratum}/cluster_results.parquet` | **Final** developer-level labels |
| `outputs/clustering/v3_final_selected/{stratum}/run_config.json` | **Final** hyperparameters + features used |
| `outputs/clustering/v3_final_validation/leakage_feature_audit.csv` | Leakage / dominance flags |
| `outputs/clustering/v3_final_validation/stability_summary.csv` | Bootstrap ARI + holdout notes |
| `outputs/clustering/v3_final_validation/sanity_checks.csv` | Cluster count, noise, silhouette |
| `outputs/clustering/v3_final_validation/cluster_size_distribution.csv` | Cluster sizes and % of sample |
| `outputs/clustering/v3_analysis/top_similar_cluster_pairs.csv` | Similar cluster pairs |
| `outputs/clustering/v3_meta_clusters/dormancy_only_meta_cluster_map.csv` | HDBSCAN → meta-cluster map |
| `outputs/clustering/v3_meta_clusters/dormancy_only_cluster_results_with_meta.parquet` | Developer labels with meta-cluster |

---

## Final production pipeline notebook

**Notebook:** [`clustering_final.ipynb`](../clustering_final.ipynb)

End-to-end reproducible pipeline: documents feature selection and tuning, fits models on a **100k reference sample**, assigns **full cohort** labels via batched `approximate_predict`, writes `outputs/clustering/final/`.

| Stratum | Features | Reference noise (100k) |
| --- | --- | ---: |
| Active | 16 reps | ~5.8% |
| Cooling | Top-5 primary | ~14% |
| Dormant | Top-5 primary | ~2.4% |

---

## Notebook section index (quick reference)

| Cells (approx.) | Section |
| --- | --- |
| Early | Correlation diagnostics, greedy filter, 16 group reps |
| Mid | `v3_corr_groups`, `v3_corr_groups_by_persona`, comparisons |
| Meta | 20 meta-clusters on 108 baseline clusters |
| Coarse tuning | Grid → `v3_coarse_hdbscan` |
| Cooling tuning | Feature recovery + grid → `v3_cooling_tuning` |
| Final + validation | Fit `v3_final_selected` → leakage, stability, sanity |
