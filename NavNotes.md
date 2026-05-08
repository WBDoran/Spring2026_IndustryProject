# Client-facing explanation: current activity assignments and feature logic

Use this section as the client explanation for how the current feature engineering pipeline works. The final notebook is `FeatureEngineering.ipynb`, and the main output table is `dev_profile_final_v3`.

Current run context from the notebook:

* Activity date range: `2020-01-01` to `2026-03-12`
* Anchor date for 30/90/180-day windows: `2026-03-12`
* Activity rows in `activity_ontology_v1`: `69,347,501`
* Developers in final profile: `9,381,508`

## One-page flow

```text
Raw activity data + contact data
        |
        v
Clean and standardize source tables
        |
        v
activity_enriched_v1
Join each activity row to developer/contact context
        |
        v
activity_ontology_v1
Assign each activity row four meaning tags:
journey_signal, effort_level, persona_hint, modality
        |
        v
Developer feature tables
Aggregate tagged activities into 30d, 90d, 180d, weekly, and lifetime views
        |
        v
Current activity assignments
Assign journey state, persona, transition, activation, and dormancy labels
        |
        v
dev_profile_final_v3
One row per developer for dashboards, segmentation, targeting, and client review
```

## Why the pipeline is built this way

The model does not treat every activity as equal. A passive view, a training, a download, an API call, and a forum contribution all mean different things. So the first step is to translate raw activity names into business meaning before any developer-level scoring happens.

The logic is intentionally rule-based and interpretable. That lets us explain every final assignment back to a client: which activity happened, what it meant, how strongly it counted, and how it changed the developer's profile.

## Current activity assignments

Each activity is assigned into three client-friendly behavioral dimensions:

* `journey_signal`: where the activity sits in the adoption path.
* `effort_level`: how much commitment the activity suggests.
* `modality`: the channel or format of the activity.

| Source activity | Journey signal | Effort level | Modality | Client explanation |
|---|---:|---:|---:|---|
| `on-demand views` | Discover | Passive | On Demand | Awareness or browsing behavior. Useful signal, but low commitment. |
| `dev program membership` | Discover | Passive | Membership | Developer has entered the ecosystem, but has not yet shown deeper usage. |
| `event registrations`, `eventy registrations` | Discover | Passive | Event | Registration shows interest before confirmed learning or building. |
| `product specific comms` | Discover | Passive | Communication | Product interest through communication engagement. |
| `dli training` | Learn | Moderate | Training | Structured learning, stronger than passive browsing. |
| `webinars`, `conference`, `conf sessions live`, `conf. sessions live`, `other events` | Learn | Moderate | Event | Educational or technical engagement. |
| `devzone downloads` | Evaluate | Moderate | Download | Developer is pulling docs, samples, or assets to assess usefulness. |
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

* Documentation, docs, whitepaper, guide, sample, or asset terms are treated as `Evaluate`.
* API catalog, installer, container, Docker, workspace, notebook, or SDK terms are treated as `Build`.
* Speaker, instructor, and presenter roles are treated as `Champion`.

## Journey-state assignment logic

The activity-level tags are rolled up into developer-level feature tables over 30, 90, and 180 days. Then each window gets a journey state.

The current-state label uses the 30-day window. The 90-day and 180-day labels provide recent and historical context.

```text
For each developer and time window:

If no activity in the window
    -> Dormant
Else if Champion signal exists
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
    -> Dormant
```

Current rule thresholds:

* `Champion`: `champion_count >= 1` or `champion_score >= 10`
* `Build`: `build_count >= 2`, `build_score >= 20`, `hosted_api_count >= 1`, or `cloud_workspace_count >= 1`
* `Evaluate`: `evaluate_count >= 2`, `evaluate_score >= 15`, or `download_count >= 2`
* `Learn`: `learn_count >= 2`, `learn_score >= 10`, or `training_count >= 1`
* `Discover`: `discover_count >= 1`
* `Dormant`: no qualifying activity in the window

The rules are ordered from highest-intent to lowest-intent. That means if a developer has both viewing and building behavior, the building behavior wins because it is stronger evidence of adoption.

`journey_state_confidence` is calculated as:

```text
largest journey-count bucket / total activity count in that window
```

So a developer with most of their recent activity in one state gets higher confidence than a developer with scattered signals.

## Persona assignment logic

Persona answers: "What does this developer appear to care about or build with?"

Current personas:

* `CUDA`
* `GenAI`
* `Robotics`
* `Simulation`
* `Learning_Community`
* `Unknown`

The system uses two evidence sources:

| Evidence source | Fields used | Weight | Why |
|---|---|---:|---|
| Activity evidence | `activity_name`, `filepath`, `lead_source_details` | 3.0 | Stronger because it reflects what the developer actually touched. |
| Profile evidence | `development_areas`, `fields_of_interest`, `industry_segment_vertical` | 1.0 | Useful, but weaker because it is self-selected or contextual. |
| Learning/community evidence | Training, webinars, events, forum-style activity | 0.75 | Indicates broad learning or community orientation. |

Persona keywords are grouped by lane:

* `CUDA`: CUDA, cuDNN, RAPIDS, NCCL, CUTLASS, DALI, Nsight, accelerated computing, GPU tooling, HPC terms.
* `GenAI`: Triton, TensorRT, NeMo, NIM, LLM, GenAI, inference, foundation models, Hugging Face, PyTorch, TensorFlow, model names, TAO, computer vision terms.
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
Create row-level raw persona evidence
activity matches count more than profile matches
        |
        v
Multiply evidence by activity_score
if activity_score is 0, use 1 so the event still counts
        |
        v
Sum scores over the developer lifetime
        |
        v
Normalize each lane score by total specific persona score
        |
        v
Top normalized lane becomes the assigned persona
```

Persona confidence is the top normalized lane score:

* `High`: `>= 0.70`
* `Medium`: `>= 0.45` and `< 0.70`
* `Low`: `< 0.45`
* `Unknown`: no specific persona evidence

`mixed_persona_flag = 1` when the top persona and second persona are within `0.15` of each other. This tells the client that the developer is multi-interest or ambiguous rather than purely one lane.

## How the features are created

The feature tables are built by aggregating the tagged activity rows.

```text
activity_ontology_v1
        |
        v
30/90/180-day cumulative windows
        |
        +--> Volume features
        |    activity_count_total, unique_activity_days, active_weeks
        |
        +--> Score features
        |    activity_score_sum, activity_score_avg
        |
        +--> Journey features
        |    discover_count, learn_count, evaluate_count, build_count, champion_count
        |    discover_score, learn_score, evaluate_score, build_score, champion_score
        |
        +--> Effort features
        |    passive_count, moderate_count, high_effort_count, high_effort_score
        |
        +--> Modality features
        |    download_count, hosted_api_count, cloud_workspace_count, training_count, event_count
        |
        +--> Persona features
        |    cuda_score, genai_score, robotics_score, simulation_score, learning_community_score
        |
        +--> Recency features
             days_since_last_activity, first_activity_date_window, last_activity_date_window
```

The windows are cumulative:

```text
30-day view  = current behavior
90-day view  = recent trajectory, includes the 30-day window
180-day view = broader historical context, includes the 90-day window
```

Every developer stays in the output even if they had no activity in a window. Missing window activity is converted to zero counts and a `Dormant` journey state. This keeps dashboard counts stable and prevents developers from disappearing simply because they were inactive.

## Transition logic

Transitions compare the 90-day state to the 30-day state.

```text
90-day state + 30-day state
        |
        v
If 90d Dormant and 30d active        -> Activated
If 90d active and 30d Dormant        -> Churned
If 30d rank is higher than 90d rank  -> Progressed
If 30d rank equals 90d rank          -> Stable
If 30d rank is lower than 90d rank   -> Regressed
```

The `trajectory_label` also uses the 180-day state to explain the pattern:

* `Consistent progression`: 180d rank < 90d rank < 30d rank
* `Recently accelerated`: current 30d rank is higher than 90d and not dormant
* `Re-engaged`: 180d was dormant, but 90d and 30d are active
* `Newly dormant`: 30d is dormant, but 90d was active
* `Fading`: 180d rank > 90d rank > 30d rank
* `Plateaued`: 180d, 90d, and 30d ranks are the same
* `Mixed / stable`: none of the above patterns clearly dominates

## Dormancy and activation logic

Dormancy is separate from journey state. This avoids calling a developer dormant if they were never meaningfully activated in the first place.

Meaningful active week:

```text
A developer-week is meaningful if:

Build or Champion activity happened
OR Moderate or High effort activity happened
OR passive Learn/Evaluate behavior happened on at least 2 distinct days in the week
```

Activation gate:

```text
Activated if:

At least 1 Build or Champion event ever
OR at least 2 meaningful active weeks in the first 90 days after first activity

Otherwise:
Unactivated
```

Dormancy status for activated developers:

* `Active`: last meaningful week was fewer than `56` days ago
* `At_Risk`: last meaningful week was `56` to `83` days ago
* `Dormant`: last meaningful week was `84+` days ago
* `Unactivated`: developer never passed the activation gate

The 56-day and 84-day cutoffs are validated with a Kaplan-Meier style return-rate check. In the notebook validation, the expected ordering holds: `Active` developers have the highest next-8-week return rate, followed by `At_Risk`, then `Dormant`.

## Final client talking track

```text
We first translate raw developer activity into behavioral meaning.
Then we aggregate those behaviors into interpretable features.
Then we assign each developer a current journey state, lifetime persona,
trajectory label, and activation-aware dormancy status.

The key point is that engagement is not treated as one generic score.
The pipeline separates passive interest, learning, evaluation, building,
community contribution, and true inactivity so clients can act on each group differently.
```