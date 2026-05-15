# NVIDIA MSBA Project — Feature Engineering Handoff README

## Overview

This document defines:
- The final feature tables
- The modeling-ready dataset
- Rules for how each team should use the data

Goal:
Ensure all teams use a consistent, validated feature set to analyze **developer engagement depth and behavior**, not just activity volume.



## Source of Truth Tables

All teams should use the following tables in DuckDB:

### Primary tables

| Logical Name | Table |
|-|-|
| Final profile | dev_profile_final_v4 |
| Recency features | dev_recency_features_v2 |
| Journey state | dev_journey_state_v2 |
| Dormancy | dev_dormancy_status_v2 |
| Lifetime features | dev_features_lifetime_v2 |

These tables are:
- One row per developer
- Fully joined and validated
- Production-ready for analysis



## Critical Data Characteristics (READ FIRST)

From EDA:

- ~95% of users have zero recent activity
- ~99.5% have zero recent builds
- ~75%+ are Dormant or Unactivated

### Implication
Running models on all users will produce:
- One large inactive cluster
- Poor behavioral segmentation



## Required Data Filters

### For Modeling (Clustering)

Use ONLY active users:

```sql
WHERE activity_count_0_30d > 0
````

Optional broader filter:

```sql
WHERE activity_count_0_30d > 0
   OR activity_count_30_90d > 0
```



### For Business Analysis

* Use full dataset for population insights
* Use filtered dataset for behavior modeling



## Model-Ready Feature Set

Use ONLY these features for clustering.

### Engagement (normalized)

* activity_rate_0_30d
* activity_rate_30_90d

### Build / Usage

* build_count_0_30d
* recent_build_flag

### Effort

* avg_effort_rank_0_30d
* avg_score_effort_gap_0_30d

### Diversity

* unique_activity_types_0_30d
* unique_modalities_0_30d

### Momentum

* activity_velocity_0_30_vs_30_90
* weighted_recent_confidence_effort

### Behavioral Flags

* has_high_effort_0_30d
* active_non_builder_0_30d
* low_volume_builder_0_30d
* recent_champion_flag



## Do NOT Use These for Modeling (Do Test it)

These features introduce leakage or bias:

### Journey Labels (outputs)

* behavior_journey_stage_30d
* current_journey_state_30d
* current_journey_rank_30d

### Lifecycle Labels

* dormancy_status
* final_lifecycle_status

### Redundant Volume Features

* activity_count_*
* log_activity_count_*
* weighted_recent_activity

### Derived Score Mixes

* effort_x_activity_score_sum



## Known Data Limitations

### 1. Activity Label Instability

* Some activities map to multiple effort/journey labels
* Minor noise in effort features

### 2. High Sparsity

* Most users have little or no activity
* Use ratios and flags instead of raw counts

### 3. Event / Download Bias

* Downloads dominate activity (~68%)
* May inflate perceived engagement



## Team-Specific Instructions

### Modeling Team

**Input**

* Filtered dataset (active users only)
* Model-ready features listed above

**Steps**

1. Standardize features
2. Apply UMAP for dimensionality reduction
3. Run HDBSCAN clustering

**Output**

* Cluster labels
* Cluster-level summaries

**Do NOT**

* Add new features
* Use journey labels as inputs


### Validation Team

**Tasks**

* Compare models: HDBSCAN, KMeans, DBSCAN, etc
* Evaluate:

  * Cluster stability
  * Sensitivity to features

**Focus**

* Are clusters differentiated by:

  * Effort
  * Build behavior
  * Diversity



### Asset Impact Analysis Team

**Use**

* Full dataset + cluster labels

**Analyze**

* Pre vs post engagement behavior
* Which assets drive:

  * Deeper engagement
  * Movement across clusters

**Note**

* Adjust for overrepresentation of downloads/events



### Cohort Profiling Team

**Use**

* Cluster labels
* Persona and demographic features

**Goal**

* Define developer segments:

  * Industry
  * Geography
  * Organization type



### Recommendations Team

**Use**

* Cluster definitions
* Asset impact findings

**Goal**

* Recommend actions to:

  * Increase high-effort engagement
  * Move users to deeper engagement states



### Visualization Team

**Build**

* UMAP cluster plots
* Engagement journey visualizations
* Cohort breakdown dashboards



### QA / Integration Team

**Responsibilities**

* Ensure all teams:

  * Use the same filters
  * Use the same feature set
* Validate consistency across outputs



## Reproducibility Rules

* Do NOT export full dataset (too large)
* Always query directly from DuckDB
* Save:

  * SQL queries
  * Feature definitions
  * Model parameters



## Final Note

This project is NOT about:

* Who clicks the most

It IS about:

* Who is progressing toward building on NVIDIA’s platform

The feature system is designed to separate:

* Low-friction engagement
* High-intent, high-effort behavior



## Handoff Complete

If anything is unclear:

* Ask before modifying features
* Consistency across teams is more important than individual optimizations
