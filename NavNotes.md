# Client-Facing Explanation: Current Activity Assignments and Feature Logic

Use this document as the client-facing explanation for how the current feature engineering pipeline works.

Current primary feature notebook:

```text
FeatureEngineering_v2.ipynb
```

Current final profile table:

```text
dev_profile_final_v4
```

Current EDA and validation notebook:

```text
Combined_EDA_Features.ipynb
```

## One-page flow

```text
Raw activity data + contact data + SDK aggregate data
        |
        v
Clean and standardize source tables
        |
        v
activity_base_v2
Create activity-only base table
        |
        v
activity_labeled_v2
Assign each activity row four behavior tags:
journey_signal, effort_level, persona_hint, modality
        |
        v
Non-overlapping recency feature tables
0_30d, 30_90d, 90_180d
        |
        v
Lifetime feature table
Summarize full developer history and max stage reached
        |
        v
Persona and lifecycle logic
Assign persona, behavior journey stage, user type, and lifecycle status
        |
        v
dev_profile_final_v4
One row per developer for EDA, modeling, dashboards, and recommendations
```

## Why the pipeline is built this way

The model does not treat every activity as equal. A passive view, a training, a download, an API call, and a forum contribution all mean different things. The first step is to translate raw activity names and activity details into business meaning before any developer-level scoring happens.

The logic is intentionally rule-based and interpretable. This lets us explain every final assignment back to a client: which activity happened, what it meant, how strongly it counted, and how it changed the developer's profile.

The current v2 pipeline also aggregates activity before joining contact metadata. This prevents contact duplication from inflating activity metrics.

## Current activity assignments

Each activity is assigned into four client-friendly behavioral dimensions:

* `journey_signal`: where the activity sits in the adoption path.
* `effort_level`: how much commitment the activity suggests.
* `persona_hint`: which technical lane the activity suggests.
* `modality`: the channel or format of the activity.

| Source activity or signal | Journey signal | Effort level | Modality | Client explanation |
|---|---:|---:|---:|---|
| `on-demand views` | Discover | Passive | On Demand | Awareness or browsing behavior. Useful signal, but low commitment. |
| `dev program membership` | Discover | Passive | Membership | Developer has entered the ecosystem, but has not yet shown deeper usage. |
| `event registrations`, `eventy registrations` | Discover | Passive | Event | Registration shows interest before confirmed learning or building. |
| `product specific comms` | Discover | Passive | Communication | Product interest through communication engagement. |
| `dli training` | Learn | Moderate | Training | Structured learning, stronger than passive browsing. |
| `webinars`, `conference`, `conf sessions live`, `conf. sessions live`, `other events` | Learn | Moderate | Event | Educational or technical engagement. |
| `devzone downloads` with documentation or PDF paths | Discover or Evaluate | Passive or Moderate | Download | Documentation and PDF downloads show research, learning, or evaluation intent. |
| `devzone downloads` with installer, toolkit, SDK, package, `.deb`, `.rpm`, or `.exe` paths | Build | High | Download | Technical package or installer downloads are stronger evidence of hands-on usage. |
| `program applications` | Evaluate | Moderate | Application | Intent signal, but not automatically proof of building yet. |
| `ngc downloads` | Build | High | Download | Pulling models, containers, or technical assets suggests hands-on use. |
| `hosted api`, `model api` | Build | High | Hosted API | API usage is treated as direct technical interaction. |
| `hackathon`, `hackathons` | Build | High | Application | Project-based activity indicates active experimentation or creation. |
| `brev` | Build | High | Cloud Workspace | Cloud workspace usage indicates a hands-on development environment. |
| `forum contributions` | Champion | High | Community | Developer contributes back to the community. |
| `bugs filed`, `user feedback` | Champion | High | Support Feedback | Developer is engaged enough to report problems or improve the product. |
| `contests` | Champion | High | Community | Public or community participation beyond ordinary consumption. |
| Speaker, instructor, or presenter roles | Champion | High | Based on source activity | Teaching or presenting is treated as advocacy or leadership. |

Additional keyword logic catches behavior hidden in text fields:

* Documentation, docs, whitepaper, guide, sample, or asset terms support Discover or Evaluate.
* API catalog, installer, container, Docker, workspace, notebook, SDK, or package terms support Build.
* Speaker, instructor, and presenter roles support Champion.

## Important validation note for DevZone Downloads

Earlier versions assumed that each raw `activity` value mapped to exactly one journey signal and one effort level. That was true when `devzone downloads` had a single fixed label.

The current project intentionally improves that logic. DevZone Downloads can now map differently based on `filepath`.

That means this validation rule is no longer correct for DevZone Downloads:

```text
one activity name = one label
```

The updated validation approach should be:

```text
standard activities: one activity name = one label
DevZone Downloads: validate filepath override distribution separately
```

This is not a bug. It is a more precise feature engineering rule.

## Recency feature design

The current pipeline uses non-overlapping windows:

```text
0_30d     = current behavior
30_90d    = prior recent behavior
90_180d   = older comparison behavior
```

This is different from cumulative windows. Non-overlapping windows help teams compare current behavior against earlier behavior without double-counting the same activity.

Feature groups include:

* volume features
* score features
* unique active days
* journey counts
* effort counts
* modality counts
* persona scores
* recency and trend features

## Behavior journey-state assignment

Behavior journey stage answers:

```text
What is the developer doing based on recent behavior?
```

Example ordered logic:

```text
If Champion signal exists
    -> Champion
Else if strong Build signal exists
    -> Build
Else if repeated or scored Evaluate signal exists
    -> Evaluate
Else if repeated or scored Learn signal exists
    -> Learn
Else if Discover activity exists
    -> Discover
Else
    -> No recent behavior / Dormant-style lifecycle interpretation
```

The rules are ordered from highest-intent to lowest-intent. If a developer has both viewing and building behavior, the building behavior wins because it is stronger evidence of adoption.

## Persona assignment logic

Persona answers:

```text
What does this developer appear to care about or build with?
```

Current personas:

* `CUDA`
* `GenAI`
* `Robotics`
* `Simulation`
* `Learning_Community`
* `Unknown`

The system uses two evidence sources:

| Evidence source | Fields used | Why it matters |
|---|---|---|
| Activity evidence | `activity_name`, `filepath`, `lead_source_details` | Stronger because it reflects what the developer actually touched. |
| Profile evidence | `development_areas`, `fields_of_interest`, `industry_segment_vertical` | Useful, but weaker because it is self-selected or contextual. |

Persona keywords are grouped by technical lane:

* `CUDA`: CUDA, cuDNN, RAPIDS, NCCL, CUTLASS, DALI, Nsight, accelerated computing, GPU tooling, HPC terms.
* `GenAI`: Triton, TensorRT, NeMo, NIM, LLM, GenAI, inference, foundation models, Hugging Face, PyTorch, TensorFlow, TAO, computer vision terms.
* `Robotics`: Jetson, JetPack, DeepStream, Isaac, robotics, edge AI, autonomous machines, DRIVE, GXF runtime.
* `Simulation`: Omniverse, OpenUSD, USD, simulation, digital twin, SimReady, PhysX, rendering, graphics.
* `Learning_Community`: training, webinars, conferences, other events, and forum-style engagement.

Persona scoring flow:

```text
Each activity row
        |
        v
Check activity text and profile text for persona keywords
        |
        v
Create row-level persona evidence
        |
        v
Aggregate over developer lifetime
        |
        v
Normalize each lane score
        |
        v
Top normalized lane becomes the assigned persona
```

Persona confidence is the top normalized lane score. The mixed persona flag identifies developers whose top two lanes are close.

## Lifecycle overlay

Lifecycle status answers:

```text
How should we interpret the developer's current relationship with the platform?
```

The current lifecycle logic adds:

* `user_type`
* `max_stage_reached`
* `final_lifecycle_status`

Example interpretations:

| Field | Meaning |
|---|---|
| `user_type` | Separates tourist-like users, low-depth free-email style users, and real users. |
| `max_stage_reached` | Shows the deepest historical adoption stage reached. |
| `final_lifecycle_status` | Combines current recency and lifetime depth into a client-friendly status. |

This separation matters because a developer who previously reached Build but is now inactive is different from someone who only clicked once and disappeared.

## How the features support teams

| Team | How this file supports the team |
|---|---|
| Modeling Team | Uses clean feature columns from `dev_profile_final_v4` for UMAP + HDBSCAN. |
| Model Validation Team | Uses validation outputs and alternative clustering comparisons to test model reliability. |
| Asset Impact Team | Uses `activity_labeled_v2` and recency windows to connect asset usage to later behavior. |
| Demographic and Cohort Profiling Team | Uses contact metadata joined last, plus persona and lifecycle fields, to explain segments. |
| Recommendations Team | Converts segment, persona, journey, and lifecycle findings into action plans. |
| Visualization Team | Builds dashboards from stable final tables and agreed definitions. |
| Final Integration and QA Team | Ensures every notebook and deliverable uses the same definitions and table names. |

## Final client talking track

```text
We first translate raw developer activity into behavioral meaning.
Then we aggregate those behaviors into interpretable features.
Then we assign each developer a persona, current behavior stage,
lifecycle status, and modeling-ready profile.

The key point is that engagement is not treated as one generic score.
The pipeline separates passive interest, learning, evaluation, building,
community contribution, current inactivity, and never-activated users
so NVIDIA can act on each group differently.
```
