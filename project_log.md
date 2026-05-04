# Project Log

## Overview

This project analyzes NVIDIA developer engagement and progression using a scalable DuckDB pipeline. The goal is to move beyond raw activity counts and produce a repeatable behavioral framework that identifies:

* **Persona**: what a developer appears to build or care about
* **Journey state**: where the developer is in the lifecycle
* **Dormancy status**: whether an activated developer is still active, at risk, or dormant
* **Trajectory**: how behavior changes across time windows
* **Sequence-ready features**: non-cumulative weekly and 30-day period features for later HMM modeling

The current pipeline is implemented in `FeatureEngineering_FINAL_WITH_DORMANCY_PERSONA_FIXED.ipynb` and writes feature tables to `developer_project.duckdb`.



## Work Completed

### 1. Infrastructure and Database

* Established persistent DuckDB database:

  ```text
  developer_project.duckdb
  ```

* All major transformations are executed in DuckDB for scalability.
* Python is used where useful for validation summaries, plotting, and survival analysis logic.
* Pipeline supports large activity, contact, and SDK tables.



### 2. Data Ingestion

Datasets ingested:

* Activity data -> `activity_raw`, `activity_clean`
* Contact data -> `contact_raw`, `contact_clean`
* SDK downloads -> `sdk_download_raw`, `sdk_download_clean`

Approach:

* Load source columns as text first where needed.
* Use `TRY_CAST` for safer type conversion.
* Preserve reproducibility through persistent DuckDB tables.
* Keep SDK downloads separate because SDK data is product/download-level and does not have a reliable user-level join key.



### 3. Data Cleaning and Validation

Key cleaning steps:

* Removed duplicate rows from activity and SDK datasets.
* Filtered invalid values, including negative download counts.
* Capped extreme `activity_score` values to reduce distortion.
* Standardized categorical and text fields using `LOWER(TRIM())`.
* Validated row counts, date ranges, duplicate rates, and missingness after major cleaning steps.

Key principle:

> Remove rows only when structurally unusable, such as missing developer ID or invalid dates. Otherwise preserve data and flag limitations.



### 4. Data Profiling

#### Activity Data

* Very high volume, roughly tens of millions of rows.
* Highly skewed developer activity distribution.
* A small number of developers have extreme activity counts.
* `activity_name` and `filepath` are high-cardinality fields but are important for persona inference.

#### Contact Data

* `developer_id` is the stable developer-level key.
* Profile fields such as `development_areas`, `fields_of_interest`, and `industry_segment_vertical` help support persona priors.
* Some contact attributes have high null rates, so they are used as weak signals rather than hard labels.

#### SDK Data

* Useful as aggregate product/download signal.
* Not currently merged into developer-level profiles because there is no direct user-level link.



### 5. Data Integration

Created:

* `activity_enriched_v1`

This table joins activity rows to contact metadata using:

```sql
activity_clean.dev_contact = contact_clean.developer_id
```

Key validation checks:

* Confirmed the join does not inflate activity row counts.
* Checked matched contact coverage.
* Preserved activity-level grain: one row per activity event.



## Current Feature Engineering System

### 1. Activity Ontology

Created:

* `activity_ontology_v1`

Each activity is mapped into four behavioral tags:

1. **Journey signal**
   * Discover
   * Learn
   * Evaluate
   * Build
   * Champion
   * Other

2. **Effort level**
   * Passive
   * Moderate
   * High
   * Unknown

3. **Persona hint**
   * CUDA
   * GenAI
   * Robotics
   * Simulation
   * Learning_Community
   * Other

4. **Modality**
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

Persona logic now uses row-level keyword mapping from:

* `activity_name`
* `filepath`
* `lead_source_details`
* `development_areas`
* `fields_of_interest`
* `industry_segment_vertical`

Strong activity/filepath matches receive higher weight than profile-only matches.



### 2. Cumulative Snapshot Feature Tables

Created:

* `dev_features_30d_v1`
* `dev_features_90d_v1`
* `dev_features_180d_v1`

These use an explicit reference date based on the latest observed `activity_date` in the dataset, rather than the current calendar date. This is important because the source data covers 2020-2025.

Cumulative window interpretation:

* 30-day window = current behavior
* 90-day window = recent trajectory
* 180-day window = historical context

Feature groups include:

* volume features
* activity score features
* unique active days
* activity diversity
* journey-stage counts and scores
* effort-level counts and scores
* persona-score features
* recency features
* journey-state assignment

Validation checks:

* 90-day counts should be greater than or equal to 30-day counts.
* 180-day counts should be greater than or equal to 90-day counts.
* Developers with zero activity in a window should be classified as `Dormant` for that window.
* Stage scores and counts should be logically consistent.



### 3. Lifetime Persona Features

Created:

* `dev_features_lifetime_v1`
* `dev_persona_v1`

Persona is treated as more stable than journey state, so it is built from lifetime activity rather than only the latest 30/90/180-day windows.

The persona process is:

1. Build text fields from activity and contact metadata.
2. Apply keyword-based scores for CUDA, GenAI, Robotics, and Simulation.
3. Add Learning/Community evidence from training, webinar, conference, and forum behavior.
4. Aggregate weighted scores by developer.
5. Normalize scores by total persona evidence.
6. Assign dominant persona.
7. Add confidence score, confidence tier, and mixed persona flag.

Outputs include:

* `persona`
* normalized persona scores
* `persona_confidence`
* `persona_confidence_tier`
* `mixed_persona_flag`



### 4. Non-Cumulative Full-History Period Features

Created:

* `dev_30day_period_features_v1`
* `dev_30day_period_transitions_v1`

These tables create repeated 30-day periods across the full 2020-2025 observation window.

Purpose:

* Measure true period-to-period behavior change without double-counting.
* Support historical trajectory analysis.
* Create sequence-style records that can be used for later HMM or other temporal models.

This is separate from cumulative snapshot features. Cumulative windows are used for current business outputs; non-cumulative windows are used for historical sequence analysis.



### 5. Weekly Features for HMM Support

Created:

* `dev_weekly_features_v1`

Weekly features provide the base time unit for possible Hidden Markov Model work. The table includes weekly activity counts, score sums, journey counts, effort signals, persona scores, active flags, and meaningful engagement flags.

Status:

* Feature table created.
* HMM model not yet implemented.



## Survival-Based Dormancy Framework

### Motivation

The project now separates simple inactivity from statistically defensible dormancy.

Instead of treating every inactive developer the same, the dormancy framework uses two layers:

1. **Activation gate**: separates tourists from developers who genuinely engaged.
2. **Dormancy classification**: applies active, at-risk, or dormant labels only to activated developers.



### Meaningful Active Week Definition

Created:

* `dev_meaningful_week_v1`

A developer-week is meaningful if at least one of the following is true:

* Any Build or Champion activity occurred.
* Any Moderate or High effort activity occurred.
* At least two distinct active days of low-effort Learn or Evaluate activity occurred in the same week.

This filters out one-off passive actions and single-click noise.



### Activation Gate

Created:

* `dev_activation_v1`

A developer is activated if either condition is true at any point in their lifetime:

* They had at least one Build or Champion event ever.
* They accumulated at least two meaningful active weeks within their first 90 days after first activity.

Developers who do not pass this gate are labeled as unactivated and are excluded from activated-developer dormancy interpretation.



### Dormancy Classification

Created:

* `dev_dormancy_v1`

For activated developers, the pipeline computes days since last meaningful active week using the dataset reference date.

Current thresholds:

* `Active`: fewer than 56 days since last meaningful active week
* `At_Risk`: 56 to 83 days
* `Dormant`: 84 or more days
* `Unactivated`: did not pass the activation gate

The 56-day and 84-day thresholds are tied to the Kaplan-Meier survival framing developed for the dormancy analysis. The 84-day threshold represents the point where return probability has flattened enough to justify dormant classification. The 56-day threshold is a warning zone where return probability has meaningfully declined but recovery is still plausible.



### Dormancy Validation

Validation checks added:

* Distribution of activation status.
* Distribution of dormancy status.
* Days-since-last-meaningful-week summary.
* Holdout-style return-rate checks for Active, At_Risk, and Dormant groups.
* Survival-curve output for interpreting return probability over inactivity duration.

Expected pattern:

* Active developers should have the highest short-term return rate.
* At-risk developers should have materially lower return rates.
* Dormant developers should have near-zero or very low return rates.



## Final Developer Profile Output

Created:

* `dev_profile_final_v3`

This is the main developer-level output table. It combines:

* developer ID
* current journey state
* 30/90/180-day journey states
* cumulative feature summaries
* lifetime persona
* persona confidence and mixed flag
* transition labels
* dormancy status
* activation status
* days since last meaningful active week
* lifetime activity context

The final profile is one row per developer.



## Current Status

Completed:

* Data ingestion
* Data cleaning
* Data validation
* Activity/contact integration
* 4-tag activity ontology
* Cumulative 30/90/180-day feature tables
* Lifetime persona scoring using activity name, filepath, source details, and profile fields
* Current journey-state assignment
* Transition analysis
* Non-cumulative 30-day period features across full data history
* Weekly HMM-ready features
* Survival-based dormancy layer
* Final developer profile table: `dev_profile_final_v3`

In progress or future work:

* Refine persona keyword dictionary after reviewing Unknown/Other distributions.
* Validate journey-state thresholds with sampled developer histories.
* Improve visualization of Kaplan-Meier survival curves and dormancy thresholds.
* Build UMAP + HDBSCAN behavioral segments.
* Prototype HMM using weekly features.
* Incorporate SDK downloads only if a defensible developer-level linkage becomes available.



## Key Risks and Limitations

* Activity signals are heterogeneous and not all engagement means adoption.
* `activity_score` may encode source-specific assumptions and should not be treated as ground truth.
* Persona keyword mapping can miss emerging product terms and should be iteratively refined.
* Dormancy thresholds should be validated on holdout periods and explained visually.
* SDK downloads are not currently user-level and should not be merged into developer profiles without a reliable key.
* HMM and clustering should be treated as extensions, not replacements for the interpretable baseline.



## Guiding Principle

> Build an interpretable, validated behavioral system first. Add advanced modeling only after the feature foundation is trustworthy.
