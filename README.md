# NVIDIA Developer Persona, Journey, and Dormancy Analysis

## Overview

This project builds a scalable DuckDB-based analytical pipeline to evaluate how NVIDIA developer engagement evolves into meaningful technical usage.

The framework moves beyond a single engagement score and produces an interpretable developer-level profile with four main components:

* **Persona**: what the developer appears to build or care about
* **Journey State**: where the developer currently sits in the lifecycle
* **Dormancy Status**: whether an activated developer is active, at risk, dormant, or unactivated
* **Trajectory Features**: how the developer changes across time windows and historical periods

The current final notebook is:

```text
FeatureEngineering.ipynb
```

The primary final output table is:

```text
dev_profile_final_v3
```



## Objectives

* Identify developer personas from technical activity patterns.
* Track journey progression over time from Discover to Champion.
* Separate genuine users from tourists using an activation gate.
* Classify activated developers as Active, At_Risk, or Dormant using a survival-based dormancy framework.
* Create validated 30/90/180-day cumulative feature tables for business interpretation.
* Create non-cumulative period and weekly features for sequence modeling.
* Provide a repeatable, scalable feature engineering foundation for segmentation, HMM, and future monitoring.



## Data Sources

The project uses three primary datasets:

* `dev_activity.csv`  
  Developer engagement events, including trainings, webinars, downloads, hosted API usage, events, forums, program memberships, and related interactions.

* `dev_contact.csv`  
  Developer profile and account-level attributes, including interests, development areas, geography, industry, account information, and profile dates.

* `sdk_download.csv`  
  Aggregate product/download signals from sources such as PyPI, NGC, DevZone, Hugging Face, DockerHub, GitHub, Conda, and VS Code.

Important limitation:

* SDK downloads are not currently joined into developer-level profiles because they do not provide a reliable user-level key.



## Database

All major tables are stored in:

```text
developer_project.duckdb
```

DuckDB is used because it supports:

* large local analytical workloads
* reproducible table creation
* SQL-based validation
* separation of raw, clean, ontology, feature, and final profile layers



## Pipeline Notebooks

Recommended run order:

```text
Creating_duckDB.ipynb
Cleaning.ipynb
FeatureEngineering.ipynb
```

Optional exploratory notebooks may include:

```text
EDA_DuckDB.ipynb
```



## Table Structure

### Raw Layer

* `activity_raw`
* `contact_raw`
* `sdk_download_raw`

### Clean Layer

* `activity_clean`
* `contact_clean`
* `sdk_download_clean`

### Enriched Layer

* `activity_enriched_v1`

This joins activity rows to contact metadata while preserving activity-level grain.

### Ontology Layer

* `activity_ontology_v1`

Each activity is tagged with:

* journey signal
* effort level
* persona hint
* modality

### Snapshot Feature Layer

* `dev_features_30d_v1`
* `dev_features_90d_v1`
* `dev_features_180d_v1`

These are cumulative windows relative to the latest observed activity date in the dataset.

### Lifetime Persona Layer

* `dev_features_lifetime_v1`
* `dev_persona_v1`

Persona is built from lifetime activity and contact context, not only recent activity.

### Historical Period Layer

* `dev_30day_period_features_v1`
* `dev_30day_period_transitions_v1`

These are non-cumulative 30-day periods across the full 2020-2025 observation window.

### Weekly Sequence Layer

* `dev_weekly_features_v1`

This table supports later HMM or sequence modeling.

### Dormancy Layer

* `dev_meaningful_week_v1`
* `dev_activation_v1`
* `dev_dormancy_v1`

These tables implement the activation gate and survival-based dormancy framework.

### Final Profile Layer

* `dev_profile_final_v3`

This is the main one-row-per-developer output table.



## Core Framework

### 1. Activity Ontology

The ontology translates raw events into behavioral meaning. Each activity receives four tags.

#### Journey Signal

* Discover
* Learn
* Evaluate
* Build
* Champion
* Other

#### Effort Level

* Passive
* Moderate
* High
* Unknown

#### Persona Hint

* CUDA
* GenAI
* Robotics
* Simulation
* Learning_Community
* Other

#### Modality

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



### 2. Persona Modeling

Persona identifies what kind of developer the user most likely is.

Personas include:

* CUDA / Accelerated Computing
* GenAI / Inference and APIs
* Robotics / Edge AI
* Simulation / Omniverse
* Learning / Community
* Other / Unknown when evidence is insufficient

Persona is built using weighted keyword matching from:

* `activity_name`
* `filepath`
* `lead_source_details`
* `development_areas`
* `fields_of_interest`
* `industry_segment_vertical`

Strong activity/filepath matches receive higher weight than self-selected profile fields.

Developer-level outputs include:

* normalized persona scores
* assigned persona
* persona confidence
* confidence tier
* mixed persona flag



### 3. Journey State Modeling

Journey state identifies where the developer is in the adoption lifecycle.

States:

* Discover
* Learn
* Evaluate
* Build
* Champion
* Dormant

Journey states are assigned over cumulative 30/90/180-day windows. These windows are used because they are easy to interpret for business stakeholders:

* 30 days = current behavior
* 90 days = recent trajectory
* 180 days = historical context



### 4. Time Window Strategy

The project uses both cumulative and non-cumulative windows.

#### Cumulative Windows

Used for current business outputs:

* `dev_features_30d_v1`
* `dev_features_90d_v1`
* `dev_features_180d_v1`

Example:

```text
90-day window includes the 30-day window.
180-day window includes the 90-day window.
```

Use cases:

* current journey state
* snapshot profile
* transition summaries
* targeting and reporting

#### Non-Cumulative Windows

Used for historical sequence analysis:

* `dev_30day_period_features_v1`
* `dev_weekly_features_v1`

Example:

```text
0-30 days, 31-60 days, 61-90 days, etc.
```

Use cases:

* period-to-period movement
* HMM input
* time-series behavior analysis
* historical trajectory review



## Survival-Based Dormancy Framework

The dormancy framework separates developers into meaningful lifecycle statuses instead of using raw inactivity alone.

### Step 1: Meaningful Active Week

A developer-week is meaningful if any of the following are true:

* any Build or Champion activity occurred
* any Moderate or High effort activity occurred
* at least two distinct days of low-effort Learn or Evaluate activity occurred in the same week

This filters out passive one-click noise.

### Step 2: Activation Gate

A developer is activated if either is true:

* they had at least one Build or Champion event ever
* they accumulated at least two meaningful active weeks within their first 90 days after first activity

Developers who do not pass this gate are classified as `Unactivated` rather than dormant.

### Step 3: Days Since Last Meaningful Active Week

For activated developers, the pipeline computes:

```text
days_since_last_meaningful_week
```

This uses the latest observed activity date in the dataset as the reference date.

### Step 4: Dormancy Status

Current thresholds:

* `Active`: fewer than 56 days since last meaningful active week
* `At_Risk`: 56 to 83 days
* `Dormant`: 84 or more days
* `Unactivated`: did not pass activation gate

The 56-day and 84-day cutoffs are based on the Kaplan-Meier survival framing used in the dormancy analysis.

### Step 5: Validation

The framework is validated by checking whether future return rates follow the expected order:

```text
Active return rate > At_Risk return rate > Dormant return rate
```



## Final Output: `dev_profile_final_v3`

The final output is one row per developer.

It combines:

* developer ID
* current journey state
* 30/90/180-day journey states
* lifetime persona
* persona confidence tier
* mixed persona flag
* transition label
* activation status
* dormancy status
* days since last meaningful active week
* activity volume and recency features
* journey, effort, and persona scores

This table is intended for:

* dashboarding
* segmentation
* stakeholder review
* targeting analysis
* input to clustering or HMM extensions



## Validation Strategy

Validation is built into the pipeline after major steps.

Key validation checks include:

* row count checks before and after joins
* duplicate checks
* join coverage checks
* ontology coverage checks
* persona distribution checks
* cumulative-window monotonicity checks
* null checks for final outputs
* transition distribution checks
* dormancy status distribution checks
* holdout-style return-rate validation



## Advanced Modeling Extensions

### UMAP + HDBSCAN

Planned use:

* identify natural behavioral segments
* detect outliers/noise
* visualize developer similarity
* complement persona and journey labels

### Hidden Markov Model

Planned use:

* infer hidden journey states from weekly behavior sequences
* smooth noisy activity patterns
* estimate transition probabilities
* estimate most likely next state

Current status:

* Weekly feature table exists.
* HMM model is not yet implemented.



## How to Run

### Setup

Install required packages:

```bash
pip install -r requirements.txt
```

### Build Database

Run:

```text
Creating_duckDB.ipynb
Cleaning.ipynb
```

### Run Feature Engineering

Run:

```text
FeatureEngineering.ipynb
```

### Connect to DuckDB

```python
import duckdb
con = duckdb.connect("developer_project.duckdb")
```

### Inspect Final Profile

```sql
SELECT *
FROM dev_profile_final_v3
LIMIT 10;
```

### Validate Final Row Grain

```sql
SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT developer_id) AS developers
FROM dev_profile_final_v3;
```

Rows should equal distinct developers.



## Key Insight

Engagement does not equal adoption.

This project distinguishes:

* passive activity from meaningful activity
* tourists from activated developers
* current state from lifetime persona
* dormant developers from users who never activated
* cumulative business snapshots from non-cumulative modeling sequences

The goal is to create a trustworthy, repeatable system for understanding and influencing developer journeys.



## Guiding Principle

> Keep the baseline interpretable and validated. Use advanced models as extensions, not as replacements for the behavioral logic.
