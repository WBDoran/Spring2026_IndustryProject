# Project Log

## Overview

This project analyzes developer engagement and progression within NVIDIA’s ecosystem using a structured, scalable pipeline.

The updated approach focuses on:

* Persona-based segmentation (what developers build)
* Journey-state modeling (where developers are)
* Feature-driven analysis of engagement → adoption
* Optional sequence modeling (HMM)



## Work Completed

### 1. Infrastructure and Database

* Established persistent DuckDB database:

  ```
  developer_project.duckdb
  ```
* Supports large-scale analytics (100M+ rows)
* All transformations executed in DuckDB



### 2. Data Ingestion

Datasets ingested:

* Activity data → `activity_raw`, `activity_clean`
* Contact data → `contact_raw`, `contact_clean`
* SDK downloads → `sdk_download_raw`, `sdk_download_clean`

Approach:

* Loaded as VARCHAR initially
* Type casting using `TRY_CAST`
* Persistent storage for reproducibility



### 3. Data Cleaning and Validation

Key steps:

* Removed duplicate rows (activity + SDK)
* Filtered invalid values (negative downloads)
* Capped extreme outliers (`activity_score`)
* Standardized text fields using:

  ```sql
  LOWER(TRIM())
  ```



### 4. Data Profiling

#### Activity Data

* High volume (~69M rows)
* High cardinality in activity_name
* Mixed engagement signals (low vs high intent)

#### Contact Data

* Stable primary key (developer_id)
* High null rates in some attributes

#### SDK Data

* Strong proxy for product engagement
* No direct link to users



### 5. Data Integration

* Joined `activity_clean` with `contact_clean`
* Validated join coverage
* Identified key limitation:

  → SDK downloads are not user-level



## Updated Direction (NEW)

### Shift from Single Score → Behavioral System

Old approach:

* Single engagement score
* Static clustering

New approach:

* Persona + Journey State framework
* Feature-driven segmentation
* Time-based progression modeling



## Feature Engineering Plan

### Activity Ontology (NEW)

Create:

* `activity_ontology_v1`

Adds:

* journey_signal
* persona_hint
* effort_level



### Rolling Feature Tables

* `dev_features_30d_v1`
* `dev_features_90d_v1`
* `dev_features_180d_v1`

Feature categories:

* volume (counts, scores)
* recency
* diversity
* journey signals
* persona scores
* effort signals



### Weekly Features (HMM Support)

* `dev_weekly_features_v1`

Used for:

* sequence modeling
* time-series analysis



## Segmentation Plan

Each developer assigned:

* **Persona**
* **Journey State**

Journey states:

* Discover
* Learn
* Evaluate
* Build
* Champion



## Transition Analysis

Create:

* `dev_transition_v1`

Tracks:

* state changes across time windows
* progression vs drop-off
* conversion patterns



## Advanced Modeling (NEW)

### Hidden Markov Model (HMM)

Purpose:

* model developer journey as a sequence
* infer hidden states from activity patterns

Scope:

* single HMM (not mixture)
* 5–6 states
* weekly features as input

Status:

* planned (not yet implemented)



## Current Status

Completed:

* data ingestion
* cleaning
* validation
* EDA
* joins

In Progress:

* activity ontology mapping
* feature engineering (30/90/180-day windows)

Next Steps:

1. build `activity_ontology_v1`
2. build rolling feature tables
3. assign persona + journey state
4. create transition analysis
5. prototype HMM model



## Key Risks

* Engagement signals are heterogeneous
* No direct user-level adoption labels
* Activity_score may bias results
* Over-segmentation risk
* HMM complexity vs value tradeoff



## Guiding Principle

> Build a simple, interpretable system first, then layer advanced modeling.


