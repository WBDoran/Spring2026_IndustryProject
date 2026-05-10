# NVIDIA Developer Journey, Persona, Lifecycle, and Behavioral Segmentation Framework

## Objective

The goal of this project is to move beyond simple activity counts and build a behavior-driven framework that explains:

* who developers are
* what they appear to care about
* where they are in the adoption journey
* whether they are currently active, at risk, dormant, or low-depth
* what assets are associated with deeper engagement
* what natural behavior segments exist
* what NVIDIA can do next for each segment

This directly supports NVIDIA's business objective of understanding whether engagement translates into real technology adoption rather than just higher interaction counts.

## Current Project Position

The project is no longer just in early EDA. It now has a working feature foundation.

Current primary feature notebook:

```text
FeatureEngineering_v2.ipynb
```

Current final profile table:

```text
dev_profile_final_v4
```

Current main EDA and validation notebook:

```text
Combined_EDA_Features.ipynb
```

The current pipeline creates a one-row-per-developer feature table that supports modeling, asset impact analysis, demographic profiling, recommendations, and visualization.

## Problem Statement

A static activity snapshot is not enough to explain developer behavior.

For example, two developers may each have five Build-related activities. One may have completed them last year and gone inactive. The other may be building right now. In a static summary, they look similar. In reality, they are in very different lifecycle positions.

This project addresses five gaps:

1. **Identity gap**
   We do not just want to know what activities happened. We want to know what kind of developer this is.

2. **Journey gap**
   We do not just want counts. We want to know whether the developer is discovering, learning, evaluating, building, or advocating.

3. **Lifecycle gap**
   We need to separate active users, at-risk users, dormant users, one-time tourists, and low-depth users.

4. **Time gap**
   We do not just want a snapshot. We want to know whether the developer is progressing, stalling, regressing, or re-engaging.

5. **Action gap**
   We need outputs that teams can turn into recommendations, dashboards, and client-facing decisions.

## Solution Overview

The project is built as a multi-layer developer intelligence system.

| Layer | Purpose | Current status |
|---|---|---|
| Data cleaning | Create trustworthy clean source tables | Built |
| Activity ontology | Convert raw activity into behavioral meaning | Built |
| Recency features | Compare current and prior behavior | Built with non-overlapping windows |
| Lifetime features | Capture full developer history | Built |
| Persona | Identify technical lane or interest | Built |
| Behavior journey | Identify current adoption behavior | Built |
| Lifecycle overlay | Separate active, at-risk, dormant, tourist, and low-depth users | Built |
| EDA validation | Check quality and business reasonableness | Built and ongoing |
| UMAP + HDBSCAN | Discover natural behavior segments | Next modeling step |
| Asset impact | Connect assets to downstream engagement | Next analysis step |
| HMM | Infer hidden journey states over sequences | Future extension |

## Core Design Principle

The project should keep one official feature foundation.

```text
FeatureEngineering_v2.ipynb -> dev_profile_final_v4
```

All teams should use this foundation rather than redefining persona, journey, lifecycle, or activity labels in separate notebooks.

## 1. Activity Ontology

### Goal

Translate raw events into stable business meaning.

### Current tags

Each activity row receives:

* `journey_signal`
* `effort_level`
* `persona_hint`
* `modality`

### Journey signals

* Discover
* Learn
* Evaluate
* Build
* Champion
* Other

### Effort levels

* Passive
* Moderate
* High
* Unknown

### Modalities

Examples:

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

### DevZone filepath override

A key recent improvement is that DevZone Downloads are no longer treated as one generic activity.

Instead:

* installers, toolkits, SDKs, `.exe`, `.deb`, `.rpm`, and package paths are stronger Build evidence
* PDFs, docs, and documentation paths are more likely Discover or Evaluate evidence
* ambiguous paths stay moderate/evaluation-style unless stronger evidence exists

This makes the feature logic more realistic because not all downloads imply the same level of adoption.

## 2. Persona Modeling

### Goal

Identify what kind of developer a user most likely is.

### Current personas

* CUDA
* GenAI
* Robotics
* Simulation
* Learning_Community
* Unknown or Other

### Evidence sources

Persona is inferred from:

* activity names
* filepaths
* lead source details
* development areas
* fields of interest
* industry context

Activity evidence is stronger than profile evidence because it shows actual behavior.

### Outputs

* primary persona
* normalized persona scores
* persona confidence
* confidence tier
* mixed persona flag

## 3. Behavior Journey Modeling

### Goal

Identify where the developer is in the adoption lifecycle based on behavior.

### Stages

* Discover
* Learn
* Evaluate
* Build
* Champion

### Interpretation

| Stage | Meaning |
|---|---|
| Discover | Awareness or early browsing |
| Learn | Training, webinars, and educational engagement |
| Evaluate | Comparing, downloading docs, applying, or assessing fit |
| Build | Hands-on usage, APIs, toolkits, workspaces, technical assets |
| Champion | Community contribution, feedback, bugs, speaking, advocacy |

The journey labels are behavior labels, not demographic labels.

## 4. Lifecycle Overlay

### Goal

Separate current engagement condition from behavior depth.

A developer can historically reach Build but currently be inactive. Another developer can be recently active but only browsing. These are different cases.

### Current lifecycle-style fields

* `user_type`
* `max_stage_reached`
* `final_lifecycle_status`

### Example user types

* `tourist`: very low activity, often one-off behavior
* `free_email_user`: low-depth activity with limited evidence of real adoption
* `real_user`: stronger evidence of meaningful engagement

### Example lifecycle statuses

* Active_Build
* AtRisk_Evaluate
* Dormant_Champion
* Tourist
* FreeEmail

This gives NVIDIA a more actionable view than raw activity counts.

## 5. Time-Based Feature Strategy

### Current v2 approach

The project currently uses non-overlapping recency windows:

```text
0_30d
30_90d
90_180d
```

This design is better for modeling and trend interpretation because each window captures a distinct period.

### Why this matters

With non-overlapping windows, the team can answer:

* Is recent activity stronger than prior activity?
* Did a developer stop building after earlier engagement?
* Are they reactivating after a quiet period?
* Is engagement velocity rising or falling?

## 6. Final Developer Profile

The final table is:

```text
dev_profile_final_v4
```

It contains one row per developer and combines:

* developer ID
* selected contact metadata
* recent behavior features
* lifetime behavior features
* persona
* behavior journey stage
* lifecycle status
* max stage reached
* user type
* modeling-ready numeric features

This table is the shared input for the team division.

## 7. Team Division and Project Logic

The proposed team division makes sense because each team owns a separate analytical question. The important condition is that every team uses the same feature foundation.

### Team 1: Modeling Team

**Question:** What natural behavior groups exist in the developer base?

**Recommended work:**

* Select clean numeric features from `dev_profile_final_v4`.
* Scale or transform skewed activity features.
* Use UMAP for low-dimensional structure discovery and visualization.
* Use HDBSCAN for density-based clustering.
* Label clusters using persona, journey stage, lifecycle status, and activity patterns.

**Output:**

* cluster labels
* UMAP plots
* cluster summary table
* short descriptions such as Explorers, Learners, Builders, Champions, Dormant Former Builders

### Team 2: Model Validation and Benchmarking Team

**Question:** Are the modeling results stable, defensible, and better than simpler alternatives?

**Recommended work:**

* Compare HDBSCAN with KMeans, DBSCAN, or Agglomerative clustering.
* Check sensitivity to feature subsets.
* Test cluster stability across samples.
* Evaluate whether clusters differ meaningfully by lifecycle, persona, and behavior depth.
* Avoid overclaiming UMAP as formal validation.

**Output:**

* model comparison table
* cluster stability notes
* chosen model justification
* risks and limitations

### Team 3: Asset Impact Analysis Team

**Question:** Which assets or engagement types are associated with deeper adoption?

**Recommended work:**

* Use `activity_labeled_v2` for asset-level behavior.
* Analyze trainings, webinars, downloads, DevZone assets, NGC downloads, hosted API usage, and events.
* Compare pre/post behavior after asset interaction.
* Measure movement from Learn or Evaluate into Build or Champion.
* Separate asset popularity from asset impact.

**Output:**

* asset engagement ranking
* pre/post movement analysis
* asset-to-stage impact summary
* recommendation on high-value assets

### Team 4: Demographic and Cohort Profiling Team

**Question:** Who are the developers in each persona, lifecycle group, and cluster?

**Recommended work:**

* Profile groups by geography, region, industry, account type, organization, and profile interests.
* Compare clusters against persona and lifecycle fields.
* Help label clusters in business-friendly language.
* Identify where high-value or dormant groups are concentrated.

**Output:**

* cohort profiles
* segment label recommendations
* demographic and account context for final story

### Team 5: Recommendations Team

**Question:** What should NVIDIA do with these insights?

**Recommended work:**

* Convert technical findings into action plans.
* Recommend interventions by lifecycle stage and persona.
* Identify reactivation opportunities for Dormant_Build or Dormant_Champion groups.
* Suggest ways to move Evaluate developers toward Build.
* Suggest content or support strategies by cluster.

**Output:**

* action matrix by segment
* prioritized recommendations
* client-facing next steps

### Team 6: Visualization Team

**Question:** How do we make the results understandable for stakeholders?

**Recommended work:**

* Build dashboards or charts around final profile outputs.
* Visualize persona distribution, lifecycle status, journey stage, clusters, and asset impact.
* Support final presentation visuals.
* Keep visuals tied to business questions.

**Output:**

* dashboard or visual pack
* UMAP cluster visuals
* lifecycle and cohort charts
* asset impact visuals

### Team 7: Final Integration and QA Team

**Question:** Does the entire project tell one consistent, reproducible story?

**Recommended work:**

* Check that all teams use the same field definitions.
* Verify that notebooks run in the correct order.
* Ensure table names match documentation.
* Remove contradictions between README, project log, project idea, and notebook markdown.
* Compile final framework and client narrative.

**Output:**

* final documentation
* final run guide
* terminology checklist
* integrated final presentation logic

## 8. Recommended End-to-End Architecture

```text
Raw data
  |
  v
Creating_duckDB.ipynb
  |
  v
Cleaning.ipynb
  |
  v
FeatureEngineering_v2.ipynb
  |
  v
dev_profile_final_v4
  |
  +--> Combined_EDA_Features.ipynb
  +--> Modeling Team
  +--> Model Validation Team
  +--> Asset Impact Team
  +--> Cohort Profiling Team
  +--> Visualization Team
  +--> Recommendations Team
  |
  v
Final Integration and QA
```

## 9. UMAP + HDBSCAN Modeling Plan

### Why it makes sense now

UMAP + HDBSCAN is the right next modeling step because the project now has a stable developer-level feature table.

### What it answers

```text
Which developers behave similarly?
```

### Inputs

Use selected fields from `dev_profile_final_v4`, such as:

* activity counts across windows
* journey counts
* effort counts
* modality counts
* persona scores
* recency features
* lifetime activity features
* lifecycle encoded fields when appropriate

### Outputs

* cluster ID
* noise flag
* cluster size
* cluster profile
* cluster label
* UMAP coordinates for visualization

### Important framing

UMAP is best used for structure discovery and visualization. HDBSCAN provides clustering. Validation should come from stability, interpretability, and downstream usefulness, not from the UMAP chart alone.

## 10. HMM Extension

### Current status

HMM is a future extension, not the required next step.

### Why HMM could make sense later

HMMs are useful when the team has regular time-based sequences and wants to infer hidden journey states from noisy behavior.

Observed behavior could include:

* webinars
* training
* downloads
* API usage
* forum contributions
* periods of inactivity

Hidden states could include:

* Dormant
* Discover
* Learn
* Evaluate
* Build
* Champion

### Required before HMM

Before implementing HMM, the project needs:

* stable weekly or biweekly sequence features
* clear handling of zero-activity periods
* feature scaling and transformation choices
* validation plan for inferred states

### Recommendation

Use HMM after the core segmentation and asset impact deliverables are complete.

## 11. Asset Impact Analysis Plan

Asset impact should avoid saying an asset caused adoption unless a stronger causal design is implemented. The safer framing is:

```text
Which assets are associated with deeper downstream engagement?
```

Recommended comparisons:

* pre/post activity count
* pre/post Build or Champion probability
* movement from Learn or Evaluate to Build
* downstream high-effort activity after a training, webinar, or download
* differences by persona or cohort

Output should separate:

* popularity: many people used the asset
* impact: users had stronger behavior after using it

## 12. Recommendations Framework

Recommendations should be tied to lifecycle and persona.

Example:

| Segment | Likely need | Recommendation |
|---|---|---|
| Tourist | Low signal, little commitment | Do not over-target. Use lightweight nurture. |
| FreeEmail / low-depth | Needs clearer path to next step | Recommend guided onboarding or starter content. |
| Active_Learn | Education stage | Push role-specific technical pathway or next training. |
| Active_Evaluate | Considering technical fit | Surface docs, samples, comparison guides, and hands-on workshops. |
| Active_Build | Hands-on user | Offer advanced support, API resources, and product-specific enablement. |
| Dormant_Build | High potential reactivation | Target with product updates, migration guides, or direct technical support. |
| Champion | Advocate or contributor | Invite to community, feedback loops, beta programs, or speaking opportunities. |

## 13. Final Deliverable Story

The final presentation should tell this story:

```text
NVIDIA has many developer interactions, but not all interactions mean adoption.
We built a repeatable framework that turns raw engagement into interpretable developer profiles.
The framework identifies each developer's persona, behavior journey stage, lifecycle status, and behavior segment.
Then we use those outputs to understand asset impact, cohort differences, and recommended actions.
```

## 14. Success Criteria

The project is successful if it produces:

* a reliable final developer profile table
* consistent definitions across all teams
* defensible segment labels
* clear asset impact findings
* useful cohort profiles
* actionable recommendations
* visuals that make the framework easy to explain
* documentation that allows the analysis to be repeated

## 15. Key Pushback to Keep the Project Strong

Do not position advanced modeling as the whole project.

The project value is the combination of:

1. interpretable feature engineering
2. business-aligned lifecycle logic
3. validated EDA
4. segmentation and modeling
5. asset impact analysis
6. recommendations

Advanced models should strengthen the framework, not replace the reasoning.
