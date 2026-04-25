# Developer Persona & Journey Analysis (Final Project Plan with HMM Extension)

## Overview

This project analyzes how developers engage with NVIDIA’s ecosystem and how that engagement evolves into meaningful technical usage.

We build a **two-layer system**:

* **Persona (What they build)** → stable
* **Journey State (Where they are)** → dynamic

We implement:

1. A **simple, interpretable framework** (core deliverable)
2. A **Hidden Markov Model (HMM)** to model developer journeys over time (advanced extension)



## Objectives

* Segment developers by **technical persona**
* Track **journey progression** over time
* Identify **conversion paths and drop-offs**
* Understand how engagement relates to **real usage signals**
* Build a **repeatable, scalable analytics framework**
* Evaluate whether **sequence models (HMMs)** improve journey modeling



## Core Framework

### 1. Persona (Stable)

Each developer is assigned one dominant lane:

* CUDA / Accelerated Computing
* GenAI / Inference & APIs
* Robotics / Edge AI
* Simulation / Omniverse
* Learning / Community



### 2. Journey State (Dynamic)

Each developer is assigned one current state:

* Discover
* Learn
* Evaluate
* Build
* Champion

This is first implemented using **rule-based logic**.



## Data Sources

* **Contacts** → developer profile, account, industry
* **Activities** → engagement events
* **SDK Downloads** → aggregate market context (not user-level)



## Pipeline Architecture

### Layer 1: Clean Data

* `contact_clean`
* `activity_clean`



### Layer 2: Activity Ontology (Critical Step)

Create:

## `activity_ontology_v1`

Each activity is mapped to:

* persona lane
* journey signal (Discover → Champion)
* effort level (optional)



### Layer 3: Developer Feature Tables

Create:

## `dev_weekly_features_v1`

* One row per developer per time window (weekly or 30-day)
* Includes:

  * activity counts (by type)
  * learning vs build signals
  * recency
  * diversity
  * activity_score (as one feature, not the definition)



### Layer 4: Core Segmentation (Baseline System)

Create:

## `dev_profile_v1`

* dominant persona
* current journey state (rule-based)

Also create:

* transition tables (30 → 90 → 180 days)



### Layer 5: Enrichment

Join with `contact_clean` to analyze:

* industry
* geography
* account behavior



## Advanced Layer: Hidden Markov Model (HMM)

### Purpose

Model developer journey as a **sequence of hidden states** instead of static labels.



### HMM Design (Scoped)

We implement a **single HMM (not mixture)**:

* **States (5–6 max):**

  * Discover
  * Learn
  * Evaluate
  * Build
  * Champion
  * Dormant (optional)

* **Inputs:**

  * weekly feature vectors from `dev_weekly_features_v1`

* **Emissions:**

  * transformed activity features (log counts, flags)

* **Transitions:**

  * “sticky” (developers tend to stay in same state)
  * mostly forward progression
  * allow drop-off to dormant



### Outputs

Create:

## `dev_journey_hmm_v1`

For each developer:

* current state (most likely)
* state probabilities
* most likely journey path (Viterbi)
* transition probabilities
* time spent in each state



## Comparison: Baseline vs HMM

We evaluate:

* Does HMM produce **more stable states**?
* Does it better predict:

  * future engagement?
  * movement to Build?
* Does it reveal **hidden journey patterns**?



## Key Analyses

### 1. Journey Progression

* Discover → Learn → Evaluate → Build
* conversion rates between stages



### 2. Drop-off Analysis

* where users stall
* time spent in each stage



### 3. Persona Differences

* which personas reach Build fastest
* which produce Champions



### 4. Activity Impact

* which activities correlate with progression
* learning vs building signals



### 5. HMM Insights (Advanced)

* hidden journey paths
* re-engagement patterns
* state probabilities vs hard labels



## Team Structure

### Track 1: Data Engineering

* cleaning
* ontology mapping
* feature tables
* validation



### Track 2: Core Segmentation 

* persona assignment
* journey state rules
* transition analysis



### Track 3: HMM Modeling

* sequence construction
* model training
* evaluation vs baseline



### Track 4: Insights & Reporting 

* visualization
* storytelling
* final deliverables



## Key Design Principles

* Keep segmentation **simple and interpretable**
* Use HMM as an **enhancement, not replacement**
* Avoid over-granularity
* Separate:

  * labeling (persona + state)
  * modeling (features, HMM)
  * decision-making (insights)



## Expected Outcomes

* Clear developer personas across NVIDIA ecosystem
* Interpretable journey stages
* Measured progression and drop-offs
* Identification of high-value behaviors
* Prototype sequence model (HMM) for deeper insights
* Scalable framework for future analytics



## Guiding Principle

Start simple, then layer complexity:

> Build a system that works → then test if HMM makes it better


