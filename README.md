# Developer Persona & Journey Analysis

## Overview

This project builds a scalable DuckDB-based analytical pipeline to evaluate how **developer engagement evolves into meaningful technical usage** within NVIDIA’s ecosystem.

Rather than relying on a single engagement score, we model developer behavior using two key dimensions:

* **Persona (What they build)** → stable
* **Journey State (Where they are)** → dynamic

This enables a clearer understanding of how developers progress from initial exploration to real usage and contribution.



## Objectives

* Identify **developer personas** based on technical activity patterns
* Track **journey progression** over time (Discover → Champion)
* Analyze **engagement → adoption relationships**
* Detect **drop-offs, transitions, and high-value behaviors**
* Build a **repeatable, scalable analytical framework**
* Prototype a **sequence model (HMM)** to improve journey modeling



## Data Sources

The project uses three primary datasets:

* `dev_activity.csv`
  → Developer engagement events (trainings, webinars, downloads, APIs, etc.)

* `dev_contact.csv`
  → Developer profile and account-level attributes

* `sdk_download.csv`
  → Aggregate product interaction signals (PyPI, NGC, DevZone, etc.)



## Database

All data is stored in:

```
developer_project.duckdb
```

This enables:

* fast querying on large datasets (100M+ rows)
* reproducibility
* separation of raw, clean, and feature layers



## Table Structure

### Raw Layer

* `activity_raw`
* `contact_raw`
* `sdk_download_raw`

### Clean Layer

* `activity_clean`
* `contact_clean`
* `sdk_download_clean`

### Feature Layer (New)

* `activity_ontology_v1`
* `dev_features_30d_v1`
* `dev_features_90d_v1`
* `dev_features_180d_v1`
* `dev_weekly_features_v1`
* `dev_profile_v1`
* `dev_transition_v1`



## Core Framework

### 1. Developer Persona (Stable)

Each developer is assigned a dominant technical lane:

* CUDA / Accelerated Computing
* GenAI / Inference & APIs
* Robotics / Edge AI
* Simulation / Omniverse
* Learning / Community



### 2. Journey State (Dynamic)

Each developer is assigned a current stage:

* Discover
* Learn
* Evaluate
* Build
* Champion

States are derived from activity behavior over recent time windows.



## Data Processing Pipeline

### 1. Data Cleaning

* Deduplicate activity and download tables
* Handle nulls and invalid values
* Standardize text fields
* Cast types using `TRY_CAST`



### 2. Activity Ontology (Key Step)

Each activity is mapped into:

* **Journey signal** (Discover → Champion)
* **Persona hint** (CUDA, GenAI, etc.)
* **Effort level** (Passive, Moderate, High)

This ensures different activity types are treated appropriately.



### 3. Feature Engineering

Features are built over rolling windows (30 / 90 / 180 days):

#### Core Feature Types

* Volume (activity count, score)
* Recency (days since last activity)
* Diversity (unique activities, breadth)
* Behavioral signals:

  * learn_count
  * evaluate_count
  * build_count
  * champion_count
* Persona scores (CUDA, GenAI, etc.)
* Effort-based features (high-effort actions)



### 4. Segmentation

Each developer receives:

* **Persona**
* **Current Journey State**

Final segmentation:

```
Persona × Journey State
```

Examples:

* GenAI → Evaluate
* CUDA → Build
* Robotics → Learn



### 5. Journey Analysis

We track:

* transitions across time windows
* progression rates (Learn → Build)
* drop-offs and inactivity
* time spent in each stage



## Advanced Modeling (HMM Extension)

We implement a **Hidden Markov Model (HMM)** as an extension.

### Purpose

* Model developer journey as a sequence of hidden states
* Smooth noisy activity signals
* identify likely progression paths

### Design (Scoped)

* 5–6 states (Discover → Champion + Dormant)
* weekly feature inputs
* Gaussian emissions on aggregated features
* sticky transitions

### Output

* current state probabilities
* most likely journey path
* transition probabilities



## Key Insight

Engagement does not equal adoption.

* Not all activities reflect real usage
* High interaction ≠ technical implementation

This project focuses on identifying **signals of progression toward building and deploying**.



## How to Run

### Setup

```bash
pip install -r requirements.txt
```

### Build Database

Run:

```
Creating_duckDB.ipynb
Cleaning.ipynb
```

### Connect

```python
import duckdb
con = duckdb.connect("developer_project.duckdb")
```



## Guiding Principle

Keep the system simple and scalable:

* Use **2 labels per user** (Persona + Journey State)
* Build features in DuckDB
* Use models (like HMM) as enhancements, not dependencies


