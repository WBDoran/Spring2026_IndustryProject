# NVIDIA Developer Journey & Persona Intelligence Framework (Detailed + HMM Extension)

## Objective
The goal of this project is to move beyond simple activity counts and build a dynamic, behavior-driven framework that explains:

- who developers are (persona / lane)
- where they are in their journey (stage)
- how they are progressing over time (trajectory)
- what their most likely next state is

This directly supports NVIDIA’s business objective of understanding whether engagement translates into real technology adoption, not just higher interaction counts.


## 1. Problem Statement

A static activity snapshot is not enough to explain developer behavior.

For example, two developers may each have five Build-related activities, but one may have completed all of them last year and gone inactive, while the other may be actively building right now. In a static summary, they look similar. In reality, they are in very different lifecycle positions.

This project addresses three gaps:

1. **Identity gap**  
   We do not just want to know what activities happened. We want to know what kind of developer this is.

2. **Journey gap**  
   We do not just want counts. We want to know whether the developer is discovering, learning, evaluating, building, or advocating.

3. **Time gap**  
   We do not just want a snapshot. We want to know whether the developer is progressing, stalling, regressing, or re-engaging.


## 2. Solution Overview

We build a multi-layer developer intelligence system with four connected layers:

### Layer 1: Persona / Developer Lane
Defines the developer’s main technical interest area.

### Layer 2: Journey Stage
Defines where the developer sits in the adoption lifecycle.

### Layer 3: Time-Based Modeling
Defines how the developer moves across stages over 30, 90, and 180-day windows.

### Layer 4: HMM Extension
Uses Hidden Markov Models to infer hidden journey states from noisy activity patterns over time.

Together, these layers allow us to move from simple activity reporting to a dynamic behavioral model of the developer lifecycle.


## 3. Persona Modeling (Developer Identity)

### 3.1 Goal

The persona layer identifies what kind of developer a user most likely is based on their activity patterns.

### 3.2 Persona Categories

Each activity is mapped into one persona category:

- CUDA / Accelerated Computing
- GenAI / Inference & APIs
- Robotics / Edge AI
- Simulation / Omniverse
- Learning / Community

### 3.3 Activity-to-Persona Mapping

We use fields such as:

- `activity`
- `activity_name`
- `filepath`

to assign each activity to a persona.

Examples:

- `NGC Downloads` + filepath contains Isaac -> Robotics
- `DLI Training` + activity name contains LLM -> GenAI
- `Webinars` + activity name contains CUDA -> CUDA
- `Forum Contributions` -> Learning / Community

### 3.4 Developer-Level Scoring

After mapping each activity row to a persona, we aggregate to the developer level:

```sql
SELECT
    dev_contact,
    COUNT_IF(persona = 'CUDA') AS cuda_score,
    COUNT_IF(persona = 'GenAI') AS genai_score,
    COUNT_IF(persona = 'Robotics') AS robotics_score,
    COUNT_IF(persona = 'Simulation') AS simulation_score,
    COUNT_IF(persona = 'Learning') AS learning_score
FROM activity_persona_tagged
GROUP BY dev_contact;
```

### 3.5 Normalization

Because highly active users can dominate raw counts, we normalize persona scores:

```sql
normalized_persona_score = persona_count / total_persona_activities
```

This helps distinguish true interest from simple activity volume.

### 3.6 Persona Assignment

We assign:

- **Primary persona** = highest normalized score
- **Secondary persona** = second highest score
- **Confidence** = strength of top score relative to others

This makes the persona layer interpretable, scalable, and actionable.


## 4. Journey Stage Modeling (Lifecycle Position)

### 4.1 Goal

The journey stage layer identifies where the developer is in the adoption funnel.

### 4.2 Journey Stages

Each activity is mapped to one of the following stages:

- Discover
- Learn
- Evaluate
- Build
- Champion

### 4.3 Current Implementation

This is already supported by the activity ontology:

```sql
SELECT
    af.*,
    aje.journey_stage,
    aje.effort
FROM activity_final af
JOIN activity_journey_effort aje
    ON af.activity = aje.activity;
```

### 4.4 What This Enables

With journey tagging in place, we can already analyze:

- stage reach
- funnel shape
- stage co-occurrence
- temporal ordering
- entry points
- highest stage reached
- time to stage
- champion vs non-champion behavior

This provides the core lifecycle framework before introducing probabilistic modeling.

## 4.5 Dormant State (Critical Lifecycle Component)

### Why Dormant Matters

Dormant is not just "no activity." It represents:
- churn risk
- disengagement after evaluation or build
- gaps in the developer experience

In large developer ecosystems, Dormant is often:
- the largest segment
- the biggest source of lost potential
- the most actionable group for re-engagement



### Definition

A developer is labeled **Dormant** in a given time window if:

- No activity is observed in that window

Example:
- No activity in last 30 days → Dormant (current state)
- Activity in 90-day but none in 30-day → churned



### Why This is Important

Without Dormant:
- Old Build users appear "active"
- Funnel metrics are misleading
- Churn is invisible

With Dormant:
- lifecycle becomes realistic
- transitions become actionable
- re-engagement opportunities become measurable

### Transition Types (Updated)

- Progressed → moved to higher stage
- Stable → same stage
- Regressed → moved to lower stage
- Activated → Dormant → Active
- Churned → Active → Dormant

## 5. Time-Based Behavioral Modeling

### 5.1 Why Time Matters

Without time, the journey is only a bucket. With time, it becomes a path.

Time-based analysis allows us to answer:

- Is the developer progressing?
- Are they stable?
- Did they regress?
- Did they churn?
- Did they re-engage?

### 5.2 Cumulative Windows

We use cumulative windows:

- 30 days -> current behavior
- 90 days -> recent trajectory
- 180 days -> historical context

These windows are cumulative rather than non-overlapping, so the 90-day window includes everything in the 30-day window, and the 180-day window includes everything in the 90-day window.

This makes state assignment easier to interpret and operationalize.

### 5.3 Features Per Developer Per Window

For each developer and each window, we compute:

#### Stage Features
- `discover_count`
- `learn_count`
- `evaluate_count`
- `build_count`
- `champion_count`

#### Score Features
- `discover_score`
- `learn_score`
- `evaluate_score`
- `build_score`
- `champion_score`

#### Effort Features
- `low_effort_count`
- `medium_effort_count`
- `high_effort_count`

#### Volume and Breadth Features
- `total_activities`
- `unique_activity_types`
- `unique_active_days`

#### Recency
- `days_since_last_activity`


## 6. State Assignment Across Windows

### 6.1 Goal

We convert per-window behavior into operational lifecycle labels.

### 6.2 Output States

For each developer, assign:

- `state_30d`
- `state_90d`
- `state_180d`

If there is no activity in a window, the developer is labeled:

- `Dormant`

### 6.3 Example Threshold Logic

```sql
CASE
    WHEN champion_count >= 1 THEN 'Champion'
    WHEN build_count >= 2 THEN 'Build'
    WHEN evaluate_count >= 2 THEN 'Evaluate'
    WHEN learn_count >= 2 THEN 'Learn'
    WHEN discover_count >= 1 THEN 'Discover'
    ELSE 'Dormant'
END
```

The exact threshold logic may evolve, but the structure remains the same.


## 7. Transition and Trajectory Analysis

### 7.1 Transition Analysis

Compare `state_90d` to `state_30d` to identify:

- Progressed
- Stable
- Regressed
- Activated
- Churned

### 7.2 Rank Mapping

```text
Dormant = 0
Discover = 1
Learn = 2
Evaluate = 3
Build = 4
Champion = 5
```

### 7.3 Transition Logic

```sql
CASE
    WHEN state_30d_rank > state_90d_rank THEN 'Progressed'
    WHEN state_30d_rank = state_90d_rank THEN 'Stable'
    WHEN state_30d_rank < state_90d_rank THEN 'Regressed'
END
```

### 7.4 Trajectory Analysis

Using the full sequence `state_180d -> state_90d -> state_30d`, classify developers into patterns such as:

- Consistent progression
- Plateaued
- Recently accelerated
- Fading
- Churning
- Re-engaged
- Newly dormant

This gives a richer behavioral story than a single-stage label.


## 8. Where Hidden Markov Models Fit

## 8.1 Why HMMs Make Sense Here

Yes, we can absolutely continue this project using HMMs, and it follows the same logic as the rest of the framework.

HMMs are a natural extension because journey stage is not directly observed. What we observe are noisy activity signals:

- webinars
- training
- forum activity
- downloads
- hosted API usage
- events
- memberships
- feedback
- campaign touches

The hidden variable is the developer’s true journey state.

That is exactly the kind of problem HMMs are built for.

### 8.2 Intuition

Observed behavior:
- attended webinar
- viewed docs
- took training
- returned to forum
- used hosted API
- then went inactive

Hidden state sequence:
- Discover
- Learn
- Evaluate
- Prototype
- Build
- Dormant

The HMM learns:

1. **Emission patterns**  
   What activity patterns are typical of each hidden state.

2. **Transition patterns**  
   How developers tend to move from one hidden state to another over time.

This allows us to say things like:

- 68% probability developer is currently in Evaluate
- 22% probability they are in Prototype
- most likely next state is Build

That is much more powerful than a rule-based stage label alone.


## 9. Recommended HMM Design

### 9.1 Key Modeling Principle

Do not use one single flat HMM to model everything at once unless the data is extremely large.

A better design is a **two-level structure**:

### Level 1: Developer Lane
A slower-moving latent variable that represents the technical lane:

- CUDA / accelerated computing
- GenAI / inference / API-first
- Robotics / edge
- Simulation / digital twin
- Community / learning-first
- Other / mixed

### Level 2: Journey Stage
A time-varying latent state within each lane:

- Dormant
- Discover
- Learn
- Evaluate
- Prototype
- Build
- Advocate / Champion

This gives a **mixture of HMMs**.

### 9.2 Formal Setup

For developer `i`:

- `L_i` = hidden lane
- `Z_i,t` = hidden journey state at time `t`
- `X_i,t` = observed activity features at time `t`

Formally:

```text
L_i ~ Categorical(pi)

Z_i,1 | L_i = k ~ Categorical(alpha_k)

Z_i,t | Z_i,t-1, L_i = k ~ Categorical(A_k)

X_i,t | Z_i,t = s, L_i = k ~ Emission(theta_k,s)
```

Interpretation:

- each developer belongs probabilistically to a lane
- each lane has its own transition behavior
- each hidden state emits a characteristic activity pattern

This is more realistic than assuming all developers follow the same journey dynamics.


## 10. Why We Need an Ontology Before the HMM

We should not feed raw activity logs directly into the HMM.

Raw logs are too sparse, too noisy, and too dependent on source-specific naming.

Before the HMM, we need an **activity ontology** that converts raw rows into stable semantic signals.

### 10.1 Semantic Buckets

#### Intent Bucket
- awareness
- learning
- evaluation
- implementation
- community
- advocacy

#### Effort Bucket
- passive
- moderate
- high-effort

#### Lane Bucket
- accelerated computing
- GenAI / inference
- robotics / edge
- simulation
- general platform / community

#### Interaction Mode
- live event
- async content
- docs / asset
- forum
- membership
- application
- API / hands-on
- feedback

This ontology becomes the feature foundation for the HMM.

Without this step, the HMM may learn campaign artifacts instead of genuine journey states.


## 11. Sequence Construction for the HMM

### 11.1 Time Unit

Use regular time windows, not raw timestamps.

Recommended:
- weekly windows
- or biweekly windows

Weekly is usually the better first pass.

### 11.2 Sequence Table

Create one row per developer per week:

- `developer_id`
- `week_start`
- engineered feature vector for that week

### 11.3 Example Weekly Features

```text
webinar_count
dli_selfpaced_count
dli_instructor_count
docs_asset_count
forum_contrib_count
program_membership_flag
hosted_api_flag
hackathon_count
high_effort_count
activity_score_sum
unique_activity_types
days_since_last_activity
campaign_touch_count
lane_cuda_score
lane_genai_score
lane_robotics_score
lane_simulation_score
```

### 11.4 Important Feature Engineering Rules

- use `log1p` transforms for skewed counts
- include zero-activity weeks
- normalize for tenure where needed
- keep missing values as explicit unknowns rather than dropping rows

This makes the model more stable and better aligned with the real lifecycle.


## 12. Using Contact Data as Lane Priors

The contact table should not just be used for descriptive analysis. It should help guide lane assignment.

Useful fields include:

- `development_areas`
- `fields_of_interest`
- `industry_segment_vertical`
- `program_application_source`
- `organization_english_name`
- `organization_website`
- `account_id`
- `created_date`
- `first_activity_date`
- `devzone_last_login_date`
- geography fields

### Example Prior Logic

- if `development_areas` contains robotics-related signals, increase robotics lane prior
- if profile interests and activity both suggest AI / ML, increase GenAI lane prior
- if organization context suggests simulation / industrial use, increase simulation lane prior

So the lane assignment becomes:

```text
P(lane | contact features, activity sequence)
```

This is stronger than activity-only assignment.


## 13. Emission Model Choice

### 13.1 Recommended First Pass

Start with a **Gaussian HMM** on transformed weekly features.

Why:
- easier to fit
- works well on summarized weekly features
- interpretable for a first implementation

### 13.2 What the Model Learns

For each hidden state, it learns:

- a mean feature profile
- covariance across features

Examples:

- a **Learning** state may show high training and async content, low technical depth
- an **Evaluate** state may show repeated docs, events, and product exploration
- a **Build** state may show hosted API usage, repeated technical assets, and strong return cadence
- an **Advocate** state may show forum participation, event speaking, and community engagement

Later, the project could evolve into count-based or custom emission models if needed.


## 14. Transition Constraints

A plain HMM may flip states too quickly and unrealistically.

To make the model reflect a real developer journey, we should use a **sticky** structure:

- high self-transition probabilities
- mostly forward movement
- some allowed backward movement
- dormancy possible from many states
- reactivation allowed from Dormant to Learn or Evaluate

Example structure:

```text
Dormant -> Discover -> Learn -> Evaluate -> Prototype -> Build -> Advocate
   ^           ^         ^         ^           ^          |
   |--|||--|-|
```

This prevents noisy week-to-week label changes that do not reflect real behavior shifts.


## 15. Lane Assignment Options

### Option A: Mixture of HMMs (Recommended)

Each lane has its own HMM.

Output for one developer:

- `P(GenAI lane) = 0.74`
- `P(Robotics lane) = 0.18`
- `P(CUDA lane) = 0.08`

Then within the top lane:

- `P(Current State = Evaluate) = 0.61`
- `P(Current State = Prototype) = 0.27`

This is the cleanest interpretation.

### Option B: One Large Combined HMM

State space becomes:

- `CUDA_Learn`
- `CUDA_Evaluate`
- `CUDA_Build`
- `Robotics_Learn`
- `GenAI_Build`
- etc.

This is possible, but usually harder to interpret and easier to overfit.

So for this project, the mixture-of-HMMs design is the better extension.


## 16. HMM Outputs

For each developer, the HMM can produce:

- top lane
- lane probability distribution
- current hidden journey state
- current state probability
- state probabilities over time
- Viterbi path for most likely journey sequence
- next-state probability distribution
- time spent in state
- confidence score

### Example Final Output Table

```text
developer_id
lane_top1
lane_top1_prob
lane_top2
current_stage
current_stage_prob
stage_probs_json
most_likely_path_last_12_weeks
next_state_probs
time_in_state
confidence_score
```

This turns the HMM into an operational output, not just a modeling exercise.


## 17. How the HMM Extends the Existing Project

The HMM does not replace the current project. It extends it.

### Current Framework
- rule-based persona assignment
- rule-based stage tagging
- time-window state assignment
- transition analysis
- trajectory analysis

### HMM Extension
- probabilistic lane inference
- probabilistic journey state inference
- hidden-state smoothing across time
- next-state prediction
- richer identification of churn, reactivation, and stage ambiguity

So the project becomes stronger in two ways:

1. **Interpretability** from the rule-based framework
2. **Probabilistic depth** from the HMM framework

That combination is actually ideal for a project like this.


## 18. Recommended Project Architecture

### Base Tables
- `activity_final`
- `contact_final`

### New Derived Tables
- `activity_ontology_v1`
- `activity_persona_tagged_v1`
- `dev_features_30d_v1`
- `dev_features_90d_v1`
- `dev_features_180d_v1`
- `dev_weekly_sequence_v1`
- `lane_prior_v1`

### HMM Output Tables
- `developer_lane_probs_v1`
- `developer_current_stage_v1`
- `dev_journey_hmm_v1`

This fits the project’s versioned, reproducible table-building style.


## 19. Validation Strategy

A good HMM should not just produce nice labels. It should improve prediction and business usefulness.

### 19.1 Predictive Validity
Does the inferred current state predict:
- future technical activity
- retention
- deeper adoption
- transition to Build or Champion

### 19.2 Interpretability
Do the learned states make sense when compared with real developer activity histories?

### 19.3 Stability
Does the same developer stay in a similar state unless their behavior truly changes?

### 19.4 Business Value
Can NVIDIA use the inferred state to trigger better interventions, messaging, or support?
