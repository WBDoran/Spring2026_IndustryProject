# NVIDIA Developer Persona, Journey, and Lifecycle Analysis

## Overview

This project builds a scalable DuckDB-based analytical pipeline to evaluate how NVIDIA developer engagement evolves into meaningful technical usage.

The framework moves beyond one generic engagement score and produces an interpretable developer-level profile with five connected components:

* **Persona**: what the developer appears to build or care about.
* **Behavior journey stage**: what the developer is currently doing, such as Discover, Learn, Evaluate, Build, or Champion.
* **Lifecycle status**: whether the developer is Active, At Risk, Dormant, Tourist, or Free Email style low-depth user.
* **Trajectory and recency features**: how behavior changes across recent non-overlapping windows.
* **Modeling-ready features**: a clean feature table for clustering, validation, asset impact, cohort profiling, visualization, and recommendations.

The current primary feature notebook is:

```text
FeatureEngineering_v2.ipynb
```

The primary final output table is:

```text
dev_profile_final_v4
```

The main EDA and validation notebook is:

```text
Combined_EDA_Features.ipynb
```

## Business Objective

NVIDIA's project question is not simply whether developers interact more often. The core question is whether engagement turns into real adoption behavior.

This project answers that by separating:

* passive browsing from meaningful activity
* learning from evaluation
* evaluation from building
* building from advocacy or community contribution
* dormant activated users from users who never meaningfully activated
* business-ready descriptive labels from optional advanced modeling outputs

## Current Project Status

### Completed

* DuckDB database setup and raw table loading.
* Activity, contact, and SDK cleaning workflow.
* Clean activity and contact feature base tables.
* Deterministic activity dictionary.
* Activity ontology with journey signal, effort level, persona hint, and modality.
* DevZone filepath override logic so DevZone downloads can be treated differently based on file type or path.
* Developer universe table.
* Non-overlapping recency windows: `0_30d`, `30_90d`, and `90_180d`.
* Lifetime developer features.
* Persona scoring from activity and contact profile evidence.
* Behavior journey state assignment.
* Lifecycle overlay, including activation-style user type, max stage reached, and final lifecycle status.
* Final one-row-per-developer profile table: `dev_profile_final_v4`.
* Combined EDA and validation notebook for sanity checks, lifecycle distribution, persona diagnostics, and modeling readiness.

### In progress or next

* Validate journey and lifecycle thresholds against sampled developer histories.
* Refine persona keyword dictionaries based on Unknown and mixed persona distributions.
* Run UMAP + HDBSCAN clustering on the final feature table.
* Benchmark clustering against simpler alternatives like KMeans and DBSCAN.
* Perform asset impact analysis on trainings, webinars, downloads, and downstream behavior.
* Build stakeholder visuals and dashboards.
* Turn results into recommendations for moving developers toward deeper adoption.
* Prototype HMM only after the weekly or sequence-ready features are stable.

## Data Sources

The project uses three primary datasets:

* `dev_activity.csv`: developer engagement events such as trainings, webinars, downloads, hosted API usage, events, forums, program memberships, and related interactions.
* `dev_contact.csv`: developer profile and account context such as development areas, interests, geography, industry, account metadata, and profile dates.
* `sdk_download.csv`: aggregate product/download signals from sources such as PyPI, NGC, DevZone, Hugging Face, DockerHub, GitHub, Conda, and VS Code.

Important limitation:

* SDK downloads are currently treated as aggregate product/download evidence. They should not be merged into developer-level profiles unless a reliable user-level join key is available.

## Database

All major tables are stored in:

```text
developer_project.duckdb
```

DuckDB is used because it supports:

* large local analytical workloads
* SQL-based reproducible transformations
* validation after each major pipeline layer
* persistent table outputs for notebooks and downstream teams

## Recommended Run Order

```text
Creating_duckDB.ipynb
Cleaning.ipynb
FeatureEngineering_v2.ipynb
Combined_EDA_Features.ipynb
```

Optional notebooks:

```text
CleanDataSanity.ipynb
EDA_DuckDB.ipynb
Creating_RandomSample_100000.ipynb
DropTables.ipynb
```

## Current Table Structure

### Raw and clean layers

* `activity_raw`
* `contact_raw`
* `sdk_download_raw`
* `activity_final`
* `contact_final`
* `sdk_download_final`

### Feature engineering v2 layers

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

## Core Framework

### 1. Activity ontology

The ontology translates raw activity events into behavioral meaning.

Each row in `activity_labeled_v2` receives:

* `journey_signal`: Discover, Learn, Evaluate, Build, Champion, or Other.
* `effort_level`: Passive, Moderate, High, or Unknown.
* `persona_hint`: CUDA, GenAI, Robotics, Simulation, Learning_Community, or Other.
* `modality`: channel or interaction format, such as Download, Event, Training, Hosted API, Community, or Support Feedback.

The current design is deterministic for standard activity names. DevZone Downloads are the exception because they use filepath-based logic. For example, an installer or toolkit filepath is stronger Build evidence than a PDF or documentation filepath.

### 2. Feature windows

The current v2 pipeline uses non-overlapping recency windows:

* `0_30d`: current behavior.
* `30_90d`: recent prior behavior.
* `90_180d`: older comparison window.

This avoids double-counting when comparing recent behavior against earlier behavior.

### 3. Lifetime features

Lifetime features summarize the developer's full observed history. These include:

* total activity count
* activity score sums and averages
* unique activity days
* journey-stage counts
* effort-level counts
* modality counts
* persona evidence
* lifetime DevZone download count
* max stage reached

### 4. Persona modeling

Persona identifies the developer's likely technical lane.

Current personas include:

* CUDA
* GenAI
* Robotics
* Simulation
* Learning_Community
* Unknown or Other

Persona evidence comes from:

* `activity_name`
* `filepath`
* `lead_source_details`
* `development_areas`
* `fields_of_interest`
* `industry_segment_vertical`

Activity and filepath evidence are treated as stronger than profile-only evidence because they represent behavior rather than self-selected interests.

### 5. Behavior journey and lifecycle overlay

The pipeline separates behavior from lifecycle.

Behavior journey answers:

```text
What is the developer doing?
```

Lifecycle answers:

```text
How should we interpret the developer's current engagement condition?
```

Current lifecycle-style fields include:

* `user_type`
* `max_stage_reached`
* `final_lifecycle_status`
* recent activity and dormancy indicators
* behavior journey stage fields

This separation prevents the project from calling a developer dormant just because they had low recent activity if they never meaningfully activated in the first place.

## Final Output: `dev_profile_final_v4`

The final profile is one row per developer.

It combines:

* developer ID
* contact metadata
* persona and persona confidence
* recent window features
* lifetime features
* current behavior journey stage
* lifecycle overlay fields
* activation or user-type logic
* max stage reached
* final lifecycle status

This table is intended for:

* stakeholder review
* cohort profiling
* asset impact analysis
* clustering
* validation and benchmarking
* dashboarding
* recommendations

## Team Division and How the Pieces Fit

The team structure makes sense if each team owns a different layer of the final story while using the same `dev_profile_final_v4` foundation.

| Team | Main question | Primary inputs | Expected output |
|---|---|---|---|
| Modeling Team | What natural behavior groups exist? | `dev_profile_final_v4`, selected scaled features | UMAP visualization, HDBSCAN clusters, cluster descriptions |
| Model Validation and Benchmarking Team | Are the clusters reliable and better than alternatives? | Model outputs, feature matrix | Stability checks, silhouette or density metrics, KMeans/DBSCAN comparison |
| Asset Impact Analysis Team | Which assets are associated with deeper engagement? | `activity_labeled_v2`, recency windows, final profile | Pre/post analysis, asset impact summary, downstream movement patterns |
| Demographic and Cohort Profiling Team | Who is in each cohort or cluster? | Contact fields, persona, lifecycle, clusters | Segment profiles by geography, industry, account type, persona |
| Recommendations Team | What should NVIDIA do with each segment? | Outputs from all analytical teams | Action plan by persona, stage, lifecycle, and cluster |
| Visualization Team | How do stakeholders understand the results quickly? | Final tables and team outputs | Dashboards, charts, final presentation visuals |
| Final Integration and QA Team | Does the whole story hold together? | All notebooks, outputs, documentation | Final QA, consistent terminology, cleaned narrative, reproducible docs |

The key rule is that teams should not create conflicting definitions. The feature file defines the official fields. EDA, modeling, asset impact, and dashboard work should consume those fields instead of redefining persona, lifecycle, or journey logic.

## Advanced Modeling Extensions

### UMAP + HDBSCAN

UMAP + HDBSCAN is the best near-term modeling extension because the current feature table is already developer-level and modeling-ready.

Use it to:

* identify natural behavioral segments
* separate high-intent and low-intent developers
* detect outliers or noise points
* visualize developer similarity
* support recommendations and storytelling

UMAP should be framed as structure discovery and visualization, not as formal statistical validation.

### Hidden Markov Model

HMM is a later extension.

Use it only after sequence features are finalized because HMM needs regular time-based observations. It can eventually support:

* hidden journey state inference
* transition probabilities
* next-state prediction
* churn and reactivation dynamics

HMM should extend the interpretable framework, not replace it.

## Key Principle

Build the interpretable and validated behavioral foundation first. Then use advanced models to deepen the analysis, not to hide the logic.
