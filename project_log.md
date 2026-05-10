# Project Log

## Overview

This project analyzes NVIDIA developer engagement and progression using a scalable DuckDB pipeline. The goal is to move beyond raw activity counts and produce a repeatable behavioral framework that identifies:

* **Persona**: what a developer appears to build or care about.
* **Behavior journey stage**: where the developer is in the adoption lifecycle based on recent activity.
* **Lifecycle status**: whether the developer is active, at risk, dormant, tourist-like, or low-depth.
* **Trajectory and recency**: how behavior changes across non-overlapping time windows.
* **Modeling-ready features**: final features that support clustering, validation, asset impact, cohort profiling, visualization, and recommendations.

The current pipeline is implemented in:

```text
FeatureEngineering_v2.ipynb
```

The main output table is:

```text
dev_profile_final_v4
```

The main EDA and quality review notebook is:

```text
Combined_EDA_Features.ipynb
```

## Work Completed

### 1. Infrastructure and database

* Established persistent DuckDB database:

  ```text
  developer_project.duckdb
  ```

* Major transformations run in DuckDB for scalability.
* Python is used for notebook control flow, display, validation summaries, and visual EDA.
* Pipeline supports activity, contact, and SDK tables.

### 2. Data ingestion

Datasets ingested:

* Activity data -> `activity_raw`
* Contact data -> `contact_raw`
* SDK downloads -> `sdk_download_raw`

Current clean/final versions:

* `activity_final`
* `contact_final`
* `sdk_download_final`

Approach:

* Load source columns safely.
* Use typed conversions only after raw data is preserved.
* Preserve reproducibility through persistent DuckDB tables.
* Keep SDK downloads separate unless a defensible developer-level join key exists.

### 3. Cleaning and validation

Key cleaning steps:

* Standardized text fields using lower/trim logic.
* Applied activity score fallback and standardized score mapping.
* Capped invalid or extreme activity score values.
* Removed or controlled structurally unusable records.
* Standardized SDK source labels and filtered invalid download counts.
* Created final clean tables for downstream analysis.
* Added validation checks after major stages.

Guiding principle:

> Remove rows only when structurally unusable. Otherwise preserve data and document limitations.

### 4. Source sanity and EDA

Completed notebooks include:

* `CleanDataSanity.ipynb`: pre-join checks for keys, cardinality, and coverage.
* `EDA_DuckDB.ipynb`: source profiling, join coverage, anomaly checks, segmentation roadmap, asset impact candidates, and enrichment ideas.
* `Combined_EDA_Features.ipynb`: final production EDA for the v2 feature system.

### 5. Current feature engineering system

The v2 feature notebook moved the project to a safer structure:

```text
Aggregate activity first
Join contact metadata last
```

This prevents duplicated contact rows from inflating developer activity metrics.

Created or refreshed:

* `activity_base_v2`
* `contact_one_row_v2`
* `activity_dictionary_v2`
* `activity_labeled_v2`
* `developer_universe_v2`
* `dev_features_0_30d_v2`
* `dev_features_30_90d_v2`
* `dev_features_90_180d_v2`
* `dev_recency_features_v2`
* `dev_features_lifetime_v2`
* `dev_contact_persona_v2`
* `dev_persona_v2`
* `dev_journey_state_v2`
* `dev_profile_final_v4`

### 6. Activity ontology

The current ontology maps each activity into:

1. `journey_signal`
   * Discover
   * Learn
   * Evaluate
   * Build
   * Champion
   * Other

2. `effort_level`
   * Passive
   * Moderate
   * High
   * Unknown

3. `persona_hint`
   * CUDA
   * GenAI
   * Robotics
   * Simulation
   * Learning_Community
   * Other

4. `modality`
   * On Demand
   * Membership
   * Event
   * Communication
   * Training
   * Download
   * Hosted API
   * Cloud Workspace
   * Application
   * Support Feedback
   * Community
   * Other

Recent update:

* DevZone Downloads now use filepath override logic.
* This means DevZone Downloads are allowed to map to different journey signals depending on filepath.
* Installer, toolkit, package, or SDK-style files can indicate Build.
* Docs, PDFs, and documentation paths can indicate Discover or Evaluate.
* Because of this, dictionary determinism checks should exclude the filepath-overridden DevZone rows or validate them separately.

### 7. Recency windows

The current v2 pipeline uses non-overlapping windows:

* `0_30d`: current activity.
* `30_90d`: recent prior activity.
* `90_180d`: older comparison window.

This is different from the older cumulative window design.

Why this matters:

* 30-day, 30-to-90-day, and 90-to-180-day features can be compared without double-counting.
* Trend and velocity features become cleaner.
* Modeling teams can use these windows as separate signals.

### 8. Lifetime features

Created:

* `dev_features_lifetime_v2`

This table summarizes the developer's full observed history.

Feature groups include:

* lifetime activity volume
* lifetime activity score summaries
* journey-stage counts
* effort-level counts
* modality counts
* DevZone download counts
* first and last activity dates
* max stage reached
* log-transformed and clipped features for modeling stability

### 9. Persona features

Created:

* `dev_contact_persona_v2`
* `dev_persona_v2`

Persona uses activity evidence and contact profile evidence.

Activity evidence is primary because it reflects what the developer actually touched. Contact evidence is secondary because it reflects self-selected or contextual metadata.

Outputs include:

* `persona`
* normalized persona scores
* `persona_confidence`
* `persona_confidence_tier`
* `mixed_persona_flag`

### 10. Behavior journey and lifecycle overlay

Created:

* `dev_journey_state_v2`

The current framework separates behavior from lifecycle.

Behavior fields answer:

```text
What is this developer doing recently?
```

Lifecycle fields answer:

```text
How should we interpret this developer's engagement condition?
```

Lifecycle-related additions include:

* `user_type`
* `max_stage_reached`
* `final_lifecycle_status`

This lets the project distinguish:

* one-time tourists
* low-depth free-email style users
* active developers
* at-risk developers
* dormant developers
* developers who reached Build or Champion historically but are not active now

### 11. Final developer profile

Created:

* `dev_profile_final_v4`

This is the main one-row-per-developer table.

It combines:

* developer ID
* contact metadata
* persona fields
* recency window features
* lifetime features
* behavior journey stage
* lifecycle status
* max stage reached
* user type
* modeling-ready numeric features

### 12. Combined EDA and validation

Current review notebook:

```text
Combined_EDA_Features.ipynb
```

This notebook validates and explains:

* table inventory and join coverage
* activity dictionary consistency
* final profile row grain
* missingness and duplicate checks
* activation and dormancy distributions
* activity distributions and zero inflation
* multi-window participation
* retention, churn, and reactivation patterns
* velocity and recency decay
* persona distribution and confidence
* behavior stage vs lifecycle separation
* modeling readiness
* outlier inspection
* marketing or source diagnostics
* executive summary outputs

## Team Division and Current Ownership Plan

The team division is logical as long as all teams use `dev_profile_final_v4` and do not redefine core labels independently.

| Team | Current role | Dependencies | Main deliverable |
|---|---|---|---|
| Modeling Team | Run UMAP + HDBSCAN and interpret clusters | Feature file, validation team | Cluster assignments and behavior segment descriptions |
| Model Validation and Benchmarking Team | Test whether clustering is stable and useful | Modeling outputs, feature matrix | Benchmark report and sensitivity checks |
| Asset Impact Analysis Team | Measure which assets are associated with movement or depth | `activity_labeled_v2`, recency features | Asset impact report by activity type or asset class |
| Demographic and Cohort Profiling Team | Explain who is inside each segment | Contact metadata, persona, lifecycle, clusters | Cohort profiles by geography, industry, account type, persona |
| Recommendations Team | Turn analysis into NVIDIA actions | All team outputs | Segment-specific engagement and reactivation recommendations |
| Visualization Team | Build visuals for client-facing storytelling | Final profile and all summary outputs | Dashboard, charts, and final presentation visuals |
| Final Integration and QA Team | Maintain consistency and reproducibility | All notebooks and docs | Final QA, cleaned docs, consistent language, run instructions |

## What should not happen

* Do not redefine persona separately in EDA, modeling, and dashboards.
* Do not create separate journey state logic in clustering notebooks.
* Do not join SDK downloads to developer profiles without a trustworthy key.
* Do not treat UMAP as formal validation.
* Do not treat HMM as required for the current deliverable.

## Current risks and limitations

* Activity signals are heterogeneous and not all engagement means adoption.
* `activity_score` may encode source-specific assumptions and should not be treated as ground truth.
* Persona keyword mapping can miss emerging product terms.
* DevZone filepath logic improves precision but requires a special validation check.
* SDK downloads are aggregate product/download evidence unless a user-level key becomes available.
* Clustering and HMM should extend the interpretable baseline, not replace it.

## Next steps

1. Patch validation checks to account for filepath-based DevZone Downloads.
2. Run final feature notebook from top to bottom.
3. Run combined EDA notebook from top to bottom.
4. Freeze the field definitions for `dev_profile_final_v4`.
5. Modeling team builds the feature matrix and first HDBSCAN results.
6. Validation team benchmarks cluster quality and stability.
7. Asset impact team analyzes pre/post behavior around key assets.
8. Cohort team profiles segments using contact metadata.
9. Recommendations and visualization teams convert results into client-facing outputs.
10. Integration and QA team checks consistency across notebooks, docs, tables, and final story.

## Guiding Principle

> Build one trusted feature foundation. Let each team answer a different business question from that same foundation.
