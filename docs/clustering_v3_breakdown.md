# Clustering v3 breakdown

**Notebook:** [`clustering_v3.ipynb`](../clustering_v3.ipynb)

**Goal:** Test whether clustering improves when highly correlated behavioral features are removed, and compare two cohorting strategies:

- **Dormancy-only:** cluster separately for `active`, `cooling`, and `dormant`.
- **Dormancy x persona:** cluster separately for each dormancy segment and persona group: `CUDA`, `GenAI`, `Robotics`, `Simulation`, `Learning_Community`, and `Unknown_or_Other`.

Compared with v2, the main v3 experiments remove the SVD step and run HDBSCAN directly on reduced, scaled feature sets.

---

## Notebook Flow

### 1. Correlation diagnostics

The notebook first builds correlation matrices for the numeric clustering features from `dev_profile_final_v4`.

This checks the **pre-SVD feature space** so we can see whether the original 100+ behavioral features contain duplicate or near-duplicate signals. Correlation matrices and top correlated pairs are written under:

`outputs/clustering/v3/correlation/`

### 2. Greedy correlation filtering

The first reduction approach greedily keeps features while enforcing pairwise `abs(correlation) < 0.50`.

This produced a global selected feature list, but the usable feature count varied by dormancy segment because some features are all-null or zero-variance within specific strata.

**Output:** `outputs/clustering/v3/`

| Dormancy | Sample | Features used | Clusters | Noise % |
| --- | ---: | ---: | ---: | ---: |
| Active | 99,999 | 36 | 60 | 25.58 |
| Cooling | 100,000 | 28 | 27 | 25.12 |
| Dormant | 100,000 | 21 | 39 | 39.08 |
| **Total / weighted** | **299,999** | - | **126** | **29.93** |

This run reduced feature redundancy, but noise remained high, especially for dormant users.

### 3. Correlation-group representative features

The second reduction approach grouped features into connected components where features were linked by `abs(correlation) >= 0.50`, then selected one representative from each group.

This is more interpretable than greedy filtering because whole correlated feature families are reviewed together. The grouped method reduced **107 candidate features to 16 representative features**. The selected representatives were:

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

The largest correlation group contained 89 activity, effort, recency, and lifetime engagement features. Its representative was `log_activity_count_30_90d`.

**Outputs:**

- `outputs/clustering/v3/feature_selection_grouped/v3_correlation_groups_abs_corr_ge_0_50.csv`
- `outputs/clustering/v3/feature_selection_grouped/v3_group_representative_features.txt`

---

## Main v3 Results

### Dormancy-only clustering

This run clusters separately by dormancy segment, using the 16 correlation-group representative features and no SVD.

**Output:** `outputs/clustering/v3_corr_groups/`

| Dormancy | Sample | Features used | Clusters | Noise % |
| --- | ---: | ---: | ---: | ---: |
| Active | 99,999 | 16 | 47 | 8.36 |
| Cooling | 100,000 | 12 | 28 | 14.42 |
| Dormant | 100,000 | 11 | 33 | 28.26 |
| **Total / weighted** | **299,999** | - | **108** | **17.01** |

This was the strongest result for **active users**, with noise dropping to **8.36%**. If the priority is clean segmentation of currently active developers, dormancy-only clustering looks especially strong.

### Dormancy x persona clustering

This run clusters each dormancy/persona cohort independently. It uses the same correlation-group representative features and no SVD.

**Output:** `outputs/clustering/v3_corr_groups_by_persona/`

| Dormancy | Cohorts | Sample | Clusters | Simple avg noise % | Weighted noise % |
| --- | ---: | ---: | ---: | ---: | ---: |
| Active | 6 | 226,016 | 252 | 20.93 | 16.12 |
| Cooling | 6 | 300,044 | 123 | 19.97 | 16.74 |
| Dormant | 6 | 600,000 | 121 | 15.37 | 15.37 |
| **Total** | **18** | **1,126,060** | **496** | **18.76** | **15.89** |

The dormancy x persona approach produces more clusters because each persona cohort is clustered independently. It also has a more consistent weighted noise rate across dormancy bands, roughly **15-17%**.

The tradeoff is that active-user noise is higher than the dormancy-only active run:

- Dormancy-only active noise: **8.36%**
- Dormancy x persona active weighted noise: **16.12%**

So the persona split may be more stable across lifecycle/persona cohorts, but it gives up some of the very clean active-user clustering from the dormancy-only approach.

---

## Persona Noise Pattern

The persona split showed a strong noise difference by persona group.

| Persona group | Cohorts | Sample | Clusters | Simple avg noise % | Weighted noise % |
| --- | ---: | ---: | ---: | ---: | ---: |
| Robotics | 3 | 158,875 | 72 | 41.32 | 32.84 |
| CUDA | 3 | 258,072 | 108 | 25.22 | 25.82 |
| Learning_Community | 3 | 136,438 | 122 | 21.03 | 18.49 |
| Simulation | 3 | 119,408 | 63 | 16.31 | 8.96 |
| GenAI | 3 | 300,000 | 87 | 7.66 | 7.66 |
| Unknown_or_Other | 3 | 153,267 | 44 | 0.98 | 0.75 |

Robotics stands out as the highest-noise persona group. The highest individual noise rates were:

- `cooling_robotics`: **55.92%**
- `active_robotics`: **46.36%**
- `dormant_robotics`: **21.68%**

This may indicate that the Robotics persona is behaviorally broader, noisier, smaller, or less cleanly separated by the current representative feature set. It is worth reviewing whether Robotics should be split differently, assigned with different confidence rules, or clustered with additional Robotics-specific features.

---

## Similar Cluster / Merge Analysis

The notebook also compares cluster profile similarity within each cohort. It uses mean cluster profiles from the `mean_*` columns, scales them, and computes cosine similarity.

`near_duplicate_flag = True` means two clusters within the same cohort have `profile_cosine_similarity >= 0.98`.

This does **not** change HDBSCAN labels. It identifies clusters that look similar enough to review for manual merging or shared labeling.

**Outputs:** `outputs/clustering/v3_analysis/`

Latest merge-analysis totals:

| Method | Cohorts | Original clusters | Merged clusters | Clusters combined |
| --- | ---: | ---: | ---: | ---: |
| Dormancy-only | 3 | 108 | 82 | 26 |
| Dormancy x persona | 18 | 496 | 416 | 80 |

The near-duplicate analysis suggests that both approaches create some clusters with very similar average behavioral profiles. This is expected with HDBSCAN because it finds dense regions, not final business segments. A later stakeholder-facing segmentation layer can merge near-duplicate technical clusters into fewer named segments.

---

## Interpretation

The biggest v3 improvement came from using **correlation-group representative features** rather than either the original SVD approach or the initial greedy correlation filter.

Key takeaways:

- Removing highly correlated feature families reduced noise substantially.
- Dormancy-only clustering gives the cleanest result for active users.
- Dormancy x persona clustering gives more granular persona-specific clusters and more consistent weighted noise across dormancy groups.
- Robotics appears to be the noisiest persona split and should be investigated.
- Similar-cluster analysis shows that some HDBSCAN clusters may be better treated as subclusters of the same business segment.

Recommended next step: use dormancy-only clustering for a clean lifecycle-level segmentation baseline, then use dormancy x persona clustering as a diagnostic or persona-specific refinement layer. Robotics should get a focused review before final segment naming.

---

## Primary Output Files

| File | Description |
| --- | --- |
| `outputs/clustering/v3/run_summary.csv` | Greedy correlation-filter run summary |
| `outputs/clustering/v3_corr_groups/run_summary.csv` | Dormancy-only grouped-feature run summary |
| `outputs/clustering/v3_corr_groups/cluster_summary_table_all.csv` | Dormancy-only cluster profiles |
| `outputs/clustering/v3_corr_groups_by_persona/run_summary.csv` | Dormancy x persona run summary |
| `outputs/clustering/v3_corr_groups_by_persona/cluster_summary_table_all.csv` | Dormancy x persona cluster profiles |
| `outputs/clustering/v3_analysis/top_similar_cluster_pairs.csv` | Similar cluster pairs within cohorts |
| `outputs/clustering/v3_analysis/merged_cluster_counts_by_method.csv` | Original vs merged cluster totals |

