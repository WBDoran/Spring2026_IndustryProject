# NVIDIA Developer Engagement Analytics Project

## Project Overview

This project builds a repeatable analytics framework for NVIDIA developer engagement data. The objective is to transform raw developer interactions into actionable insights that help NVIDIA understand how engagement translates into meaningful technology adoption.

The framework combines lifecycle segmentation, behavioral clustering, journey modeling, asset impact analysis, demographic profiling, and future developer scoring into a unified analytical system.

The project is designed to answer the core business question:

> How do we ensure developer engagement efforts translate into meaningful technology adoption rather than simply increasing interaction counts?

The final deliverables support both immediate business insights and long-term operationalization through reusable pipelines and documented methodology.

---

# Business Objectives

The project focuses on four primary deliverables:

### 1. Developer Cohort Profiles

Identify distinct groups of developers based on engagement patterns, behavior, lifecycle stage, and adoption characteristics.

### 2. Asset Impact Analysis

Measure how trainings, webinars, events, downloads, and other NVIDIA assets influence subsequent developer behavior and technology adoption.

### 3. Data Enrichment Strategy

Identify gaps in internal visibility and recommend external data sources that improve measurement of developer adoption maturity.

### 4. Repeatable Analytics Framework

Create a documented process that NVIDIA can reuse for future analysis, monitoring, and developer scoring.

---

# Project Architecture

The project is organized into three major layers:

```text
Raw Data
    ↓
Pipeline A
(Core Modeling Pipeline)
    ↓
Final Developer Profiles
Final Cluster Membership
Journey Modeling Outputs
    ↓
Analysis Layer
(Demographics + Asset Impact)
    ↓
Business Insights
    ↓
Pipeline B
(Future Developer Scoring)
```

---

# Repository Structure

```text
NVIDIA_Developer_Engagement_Project/
│
├── README.md
├── PIPELINE_README.md
├── PIPELINE_AB_INTEGRITY_MANIFEST.md
├── requirements_pipeline.txt
│
├── run_pipeline_A_full_reclustering.sh
├── run_pipeline_B_new_data_fixed_cluster_scoring.sh
│
├── Data/
│   ├── contacts.csv / xlsx
│   ├── activities.csv / xlsx
│   ├── sdk_downloads.csv / xlsx
│   ├── data_dictionary.xlsx
│   └── supporting lookup files
│
├── Pipeline_A/
│   ├── 1A_Create_DuckDB.ipynb
│   ├── 2A_Clean_Data.ipynb
│   ├── 3A_Feature_Engineering.ipynb
│   ├── 4A_HDBSCAN_Clustering.ipynb
│   ├── 5A_GMM_Cluster_Validation.ipynb
│   ├── 6A_HMM_Journey_Modeling.ipynb
│   ├── 7A_Supervised_Labeling_LGBM_XGB.ipynb
│   └── 8A_Train_Saved_LGBM_Labeler.ipynb
│
├── Pipeline_B/
│   ├── 0B_OPTIONAL_Create_Sample_New_Incoming_Profile.ipynb
│   ├── 1B_Load_New_Raw_Data_To_DuckDB.ipynb
│   ├── 2B_Clean_New_Data.ipynb
│   ├── 3B_Feature_Engineering_New_Data.ipynb
│   └── 4B_Score_New_Data_Fixed_Clusters.ipynb
│
├── Analysis/
│   │
│   ├── Demographics/
│   │   └── demographic_analysis_by_cluster_duckdb_v11_final.ipynb
│   │
│   ├── Asset_Impact/
│   │   ├── Cluster_Asset_Impact_Analysis_Pipeline_hdbscan_duckdb.ipynb
│   │   └── HDBSCAN_Extra_Analysis_DuckDB_Final.ipynb
│   │
│   └── outputs/
│
├── developer_project.duckdb
│
├── supervised_cluster_labeler_artifacts_v1/
│
├── executed_notebooks_pipeline_A/
│
└── executed_notebooks_pipeline_B/
```

---

# Data Sources

The project uses three primary NVIDIA datasets.

## Contacts

Contains developer profile information including:

* Geography
* Organization
* Industry
* Interests
* Program membership
* Account metadata

Key Table:

```text
contact_final
```

---

## Activities

Contains developer engagement activity including:

* DLI Trainings
* Webinars
* Conferences
* Events
* Hackathons
* Downloads
* Forum activity
* Hosted APIs
* Feedback submissions

Key Table:

```text
activity_final
```

---

## SDK Downloads

Contains technology adoption signals from:

* PyPI
* NGC
* DevZone
* GitHub
* HuggingFace
* DockerHub
* Conda
* VSCode

Key Table:

```text
sdk_download_final
```

---

# Technology Stack

## Database

DuckDB

Purpose:

* Centralized local analytics database
* Shared schema across all notebooks
* Reproducible outputs
* Efficient large-scale aggregation

Primary Database:

```text
developer_project.duckdb
```

---

## Modeling Libraries

* HDBSCAN
* HMM (Hidden Markov Models)
* Gaussian Mixture Models
* LightGBM
* XGBoost
* Scikit-Learn

---

## Visualization and Analytics

* Pandas
* NumPy
* Matplotlib
* Jupyter Notebook

---

# Pipeline A: Full Reclustering and Model Development

Pipeline A is used when rebuilding the entire analytical framework from raw data.

Typical scenarios:

* Initial project build
* Major refreshes
* Feature redesign
* New data sources
* Updated segmentation strategy

---

## Pipeline A Notebook Order

```text
1A_Create_DuckDB.ipynb
2A_Clean_Data.ipynb
3A_Feature_Engineering.ipynb
4A_HDBSCAN_Clustering.ipynb
5A_GMM_Cluster_Validation.ipynb
6A_HMM_Journey_Modeling.ipynb
7A_Supervised_Labeling_LGBM_XGB.ipynb
8A_Train_Saved_LGBM_Labeler.ipynb
```

---

## Pipeline A Process

### Step 1: Database Creation

Loads raw NVIDIA datasets into DuckDB.

Outputs:

```text
contact_final
activity_final
sdk_download_final
```

---

### Step 2: Data Cleaning

Standardizes:

* Null values
* Duplicate records
* Invalid timestamps
* Inconsistent fields

Creates modeling-ready tables.

---

### Step 3: Feature Engineering

Builds developer-level features including:

* Activity intensity
* Engagement depth
* Recency
* Frequency
* Build behavior
* Asset interaction patterns
* Persona indicators

Primary output:

```text
dev_profile_final_v4
```

---

### Step 4: Lifecycle Segmentation

Developers are assigned to:

```text
active
cooling
at_risk
dormant
unactivated
```

These strata are used throughout the project.

---

### Step 5: HDBSCAN Clustering

Primary developer segmentation model.

Purpose:

* Discover natural engagement groups
* Handle irregular cluster shapes
* Preserve noise points
* Create interpretable segments

Output:

```text
dev_lifecycle_cluster_membership_v11_final
```

---

### Step 6: GMM Validation

Gaussian Mixture Models are used as an alternative clustering benchmark.

Outputs:

```text
dev_gmm_stratified_clusters_v1
dev_gmm_weekly_clusters_v1
```

Purpose:

* Validate segmentation stability
* Compare behavioral structure
* Support HMM emissions

---

### Step 7: HMM Journey Modeling

Hidden Markov Models are used to understand developer progression over time.

Purpose:

* State transitions
* Developer journeys
* Lifecycle movement
* Engagement evolution

Outputs:

```text
dev_hmm_weekly_states_v1
dev_hmm_transition_matrix_v1
dev_hmm_developer_journey_v1
```

---

### Step 8: Supervised Cluster Assignment

LightGBM and XGBoost learn the discovered cluster structure.

Purpose:

* Fast future scoring
* Real-time assignment
* Production deployment

Outputs:

```text
dev_supervised_cluster_membership_v1_final
supervised_cluster_labeler_artifacts_v1/
```

---

# Analysis Layer

The Analysis layer consumes the outputs of Pipeline A and generates stakeholder-facing insights.

These notebooks are not part of the modeling pipeline itself.

---

# Demographic Analysis

Notebook:

```text
Analysis/Demographics/
demographic_analysis_by_cluster_duckdb_v11_final.ipynb
```

Purpose:

* Geography analysis
* Industry analysis
* Organization analysis
* Interest analysis
* Cluster demographic profiling

Inputs:

```text
dev_lifecycle_cluster_membership_v11_final
contact_final
```

---

# Asset Impact Analysis

Notebook:

```text
Analysis/Asset_Impact/
Cluster_Asset_Impact_Analysis_Pipeline_hdbscan_duckdb.ipynb
```

Purpose:

* Identify highly engaged assets
* Measure asset influence
* Compare asset consumption across clusters

Creates:

```text
cluster_profile_asset_base_v2
cluster_asset_long_v2
cluster_asset_summary_v2
cluster_asset_priority_by_cluster_v2
cluster_persona_profile_v2
cluster_journey_profile_v2
cluster_effort_profile_v2
```

---

# Extended Asset Analysis

Notebook:

```text
Analysis/Asset_Impact/
HDBSCAN_Extra_Analysis_DuckDB_Final.ipynb
```

Creates:

```text
cluster_top_persona_summary_v2
cluster_top_asset_summary_v2
cluster_correlation_summary_v2
cluster_group_rollup_summary_v2
cluster_group_asset_profile_v2
cluster_group_composition_summary_v2
asset_audience_summary_v2
```

Purpose:

* Cluster summaries
* Persona analysis
* Asset audience analysis
* Lifecycle rollups
* Reporting tables

---

# Pipeline B: Future Developer Scoring

Pipeline B is used when new data arrives.

Pipeline B does not rerun clustering.

Instead, it assigns developers into the existing cluster framework.

---

## Pipeline B Notebook Order

```text
0B_OPTIONAL_Create_Sample_New_Incoming_Profile.ipynb

1B_Load_New_Raw_Data_To_DuckDB.ipynb
2B_Clean_New_Data.ipynb
3B_Feature_Engineering_New_Data.ipynb
4B_Score_New_Data_Fixed_Clusters.ipynb
```

---

## Pipeline B Process

1. Load new raw data.
2. Apply cleaning methodology.
3. Generate feature table.
4. Load saved LightGBM artifacts.
5. Score developers into existing clusters.

Outputs:

```text
dev_profile_new_incoming_v1
dev_new_developer_cluster_scores_v1
```

---

# Main Tables

## Core Modeling Tables

```text
contact_final
activity_final
sdk_download_final

dev_profile_final_v4

dev_lifecycle_cluster_membership_v11_final

dev_gmm_stratified_clusters_v1
dev_gmm_weekly_clusters_v1

dev_hmm_weekly_states_v1
dev_hmm_transition_matrix_v1

dev_supervised_cluster_membership_v1_final
```

---

## Asset Impact Tables

```text
cluster_profile_asset_base_v2
cluster_asset_long_v2
cluster_asset_summary_v2
cluster_asset_priority_by_cluster_v2

cluster_persona_profile_v2
cluster_journey_profile_v2
cluster_effort_profile_v2
```

---

## Extended Analysis Tables

```text
cluster_top_persona_summary_v2
cluster_top_asset_summary_v2
cluster_correlation_summary_v2

cluster_group_rollup_summary_v2
cluster_group_asset_profile_v2
cluster_group_composition_summary_v2

asset_audience_summary_v2
```

---

# When to Use Each Pipeline

| Scenario                  | Pipeline   |
| ------------------------- | ---------- |
| Initial project build     | Pipeline A |
| Major methodology changes | Pipeline A |
| New data sources          | Pipeline A |
| Feature redesign          | Pipeline A |
| New monthly data          | Pipeline B |
| New quarterly data        | Pipeline B |
| Dashboard refresh         | Pipeline B |
| Future developer scoring  | Pipeline B |

---

# Data Governance

Recommended practices:

* Keep raw data inside the Data folder only.
* Never commit raw developer data to public repositories.
* Share aggregated outputs only.
* Preserve DuckDB schemas.
* Preserve model artifacts with version control.
* Document any modifications to lifecycle rules or clustering logic.

---

# Project Story

This project transforms NVIDIA developer engagement data into a scalable developer intelligence framework that identifies behavioral cohorts, measures technology adoption signals, explains developer journeys, quantifies asset impact, and enables future developer scoring without requiring full reclustering.
