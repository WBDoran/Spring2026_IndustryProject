# NVIDIA MSBA Project Constitution

## Source of Truth Document for Team Alignment

---

# Purpose

This document defines:

* Official project structure
* Approved datasets and tables
* Modeling rules
* Feature governance
* Team responsibilities
* Business assumptions
* Known limitations

Goal:
Ensure all teams work from the same assumptions, definitions, and datasets throughout the NVIDIA MSBA project.

---

# 1. Project Objective

The project is NOT focused on:

* maximizing clicks
* maximizing downloads
* maximizing raw engagement counts

The project IS focused on:

* identifying meaningful developer engagement
* understanding technology adoption behavior
* distinguishing casual users from high-intent builders
* identifying pathways toward deeper NVIDIA ecosystem adoption

---

# 2. Core Business Question

> How do we ensure engagement efforts translate into real technology adoption rather than superficial interaction?

---

# 3. Canonical Definitions

| Term                 | Definition                                                       |
| -------------------- | ---------------------------------------------------------------- |
| Activated Developer  | Developer with meaningful lifetime activity                      |
| Active Developer     | Developer with activity in the 0–30d window                      |
| Dormant Developer    | Developer with no meaningful activity beyond dormancy threshold  |
| At-Risk Developer    | Developer showing declining recency/activity patterns            |
| Builder              | Developer exhibiting build-oriented behavior                     |
| Champion             | High-effort, high-depth developer with strong engagement         |
| Tourist              | Low-depth engagement with minimal progression                    |
| Meaningful Activity  | Activities weighted above casual engagement                      |
| High-Effort Activity | API usage, builds, advanced workflows, production-oriented usage |
| Persona              | Dominant engagement identity inferred from behavioral activity   |

---

# 4. Official Project Pipeline

```text
01_create_database
        ↓
02_clean_raw_data
        ↓
03_feature_engineering
        ↓
04_feature_sanity_checks
        ↓
05_model_dataset_builder
        ↓
06_clustering_model
        ↓
07_cluster_profiling
        ↓
08_asset_impact_analysis
        ↓
09_final_dashboard_and_report
```

---

# 5. Source-of-Truth Tables

## Primary Final Tables

| Logical Name            | Table                    |
| ----------------------- | ------------------------ |
| Final developer profile | dev_profile_final_v4     |
| Recency features        | dev_recency_features_v2  |
| Lifetime features       | dev_features_lifetime_v2 |
| Journey state           | dev_journey_state_v2     |
| Dormancy                | dev_dormancy_status_v2   |
| Persona features        | dev_persona_v2           |

These tables are:

* one row per developer
* validated
* approved for downstream analysis

---

# 6. Approved Modeling Population

## Required Clustering Filter

```sql
WHERE activity_count_0_30d > 0
```

Optional broader filter:

```sql
WHERE activity_count_0_30d > 0
   OR activity_count_30_90d > 0
```

Reason:
The full dataset is highly sparse and dominated by inactive users.

---

# 7. Official Model-Ready Features

## Engagement

* activity_rate_0_30d
* activity_rate_30_90d

## Build / Usage

* build_count_0_30d
* recent_build_flag

## Effort

* avg_effort_rank_0_30d
* avg_score_effort_gap_0_30d
* developer_effort_score

## Diversity

* unique_activity_types_0_30d
* unique_modalities_0_30d

## Momentum

* activity_velocity_0_30_vs_30_90
* weighted_recent_confidence_effort

## Behavioral Flags

* has_high_effort_0_30d
* active_non_builder_0_30d
* low_volume_builder_0_30d
* recent_champion_flag

## Persona

* persona
* persona_entropy
* mixed_persona_flag

---

# 8. Features NOT Allowed for Clustering

## Leakage / Output Labels

* behavior_journey_stage_30d
* current_journey_state_30d
* current_journey_rank_30d
* dormancy_status
* final_lifecycle_status

## Highly Redundant Features

* activity_count_*
* log_activity_count_*
* weighted_recent_activity

## Derived Score Mixes

* effort_x_activity_score_sum

---

# 9. Feature Taxonomy

| Category         | Example Features                |
| ---------------- | ------------------------------- |
| Recency          | activity_count_0_30d            |
| Intensity        | developer_effort_score          |
| Breadth          | unique_activity_types_0_30d     |
| Momentum         | activity_velocity_0_30_vs_30_90 |
| Persona          | persona_entropy                 |
| Lifecycle        | dormancy_status                 |
| Behavioral Flags | recent_build_flag               |

---

# 10. Cluster Interpretation Framework

Each cluster should include:

| Field              | Description                    |
| ------------------ | ------------------------------ |
| cluster_id         | Numerical cluster identifier   |
| cluster_name       | Human-readable label           |
| primary_behaviors  | Dominant engagement traits     |
| persona_mix        | Major persona composition      |
| lifecycle_mix      | Dormancy/lifecycle composition |
| business_value     | Strategic importance           |
| recommended_action | Suggested intervention         |

---

# 11. Feature Usage Matrix

| Feature                | Clustering | Profiling | Dashboard | Recommendations |
| ---------------------- | ---------- | --------- | --------- | --------------- |
| developer_effort_score | YES        | YES       | YES       | YES             |
| persona                | YES        | YES       | YES       | YES             |
| dormancy_status        | NO         | YES       | YES       | YES             |
| final_lifecycle_status | NO         | YES       | YES       | YES             |
| activity_count_*       | LIMITED    | YES       | YES       | LIMITED         |

---

# 12. Known Data Limitations

## High Sparsity

* Most users have minimal recent activity
* Most recent build features are sparse

## Download Dominance

* Downloads dominate engagement volume
* Downloads may overestimate adoption depth

## Metadata Quality

* Large number of null/unknown organization/account fields
* Some organization normalization issues

## Persona Uncertainty

* Mixed-persona developers exist
* Unknown persona group behaves differently from named personas

## Outliers

* Extremely large activity counts exist
* Use clipped/log features when appropriate

---

# 13. Modeling Rules

## Required Steps

1. Standardize numerical features
2. Handle missing values consistently
3. Remove highly correlated features
4. Use dimensionality reduction where appropriate
5. Save model parameters and dataset versions

## Recommended Algorithms

* HDBSCAN
* UMAP + HDBSCAN
* KMeans (benchmark only)
* DBSCAN (benchmark only)

---

# 14. Business Assumptions

The project assumes:

* Deeper engagement matters more than raw clicks
* Build-oriented activity reflects higher intent
* Repeat multi-channel engagement indicates ecosystem stickiness
* Effort and diversity are stronger signals than volume alone
* Dormancy reflects reduced platform engagement

---

# 15. Visualization Standards

## Standard Colors

| Concept     | Color  |
| ----------- | ------ |
| Active      | Green  |
| At-Risk     | Orange |
| Dormant     | Red    |
| Unactivated | Gray   |
| Builder     | Blue   |
| Champion    | Purple |

## Naming Standards

* Use consistent cluster names across notebooks
* Use consistent persona labels
* Use standardized lifecycle terminology

---

# 16. Deliverables Ownership Matrix

| Deliverable     | Team                 | Inputs                       | Outputs            |
| --------------- | -------------------- | ---------------------------- | ------------------ |
| Clustering      | Modeling Team        | model_active_developers      | developer_clusters |
| Profiling       | Cohort Team          | developer_clusters + profile | cluster_profiles   |
| Asset Impact    | Asset Team           | activities + clusters        | impact_analysis    |
| Recommendations | Recommendations Team | cluster outputs              | strategic_actions  |
| Dashboard       | Visualization Team   | all outputs                  | final_dashboard    |

---

# 17. Reproducibility Rules

* Do NOT export full datasets
* Query directly from DuckDB
* Save:

  * SQL queries
  * notebook versions
  * feature definitions
  * model parameters

---

# 18. Official Approved Dataset

## Current Approved Dataset

```text
official_model_dataset_v1
```

### Properties

* Active developers only
* Approved feature set only
* Standardized preprocessing
* One row per developer

---

# 20. Final Principle

Consistency across teams is more important than individual optimization.

If assumptions, features, or definitions change:

* document the change
* communicate the change
* update this constitution document
