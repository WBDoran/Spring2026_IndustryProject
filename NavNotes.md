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

---

# Suggested feature architecture

I would split the engineered features into 5 layers.

## Layer 1: Base joined table

**Table:** `activity_enriched_v1`

This is where you join activity rows to contact metadata.

### Needed columns

From activities:

* dev_contact
* activity_date
* activity
* activity_name
* activity_type
* activity_role
* activity_attendance
* activity_score
* filepath
* lead_source
* lead_source_details
* nvidia_campaign_id

From contacts:

* developer_id
* created_date
* first_activity_date
* last_activity_date
* development_areas
* fields_of_interest
* account_id
* account_type
* country
* region
* industry_segment_vertical
* program_application_source

### DuckDB pseudo-code

```sql
create or replace table activity_enriched_v1 as
select
    a.dev_contact as developer_id,
    cast(a.activity_date as date) as activity_date,
    a.activity,
    a.activity_name,
    a.activity_type,
    a.activity_role,
    a.activity_attendance,
    coalesce(a.activity_score, 0) as activity_score,
    a.filepath,
    a.lead_source,
    a.lead_source_details,
    a.nvidia_campaign_id,
    c.created_date,
    c.first_activity_date,
    c.last_activity_date,
    c.development_areas,
    c.fields_of_interest,
    c.account_id,
    c.account_type,
    c.country,
    c.region,
    c.industry_segment_vertical,
    c.program_application_source
from activity_clean a
left join contact_clean c
    on a.dev_contact = c.developer_id;
```

---

## Layer 2: Activity ontology features

**Table:** `activity_ontology_v1`

This is the most important feature table. Each activity gets mapped into:

* journey signal
* effort level
* persona lane hint
* modality

This is directly supported by the activity categories in the kickoff materials, which include DLI training, webinars, events, downloads, forum contributions, hosted API, and Brev. 

## 2A. Journey-signal features

Map each raw activity into one of:

* Discover
* Learn
* Evaluate
* Build
* Champion

### Suggested mapping

* `On-Demand Views`, `Dev Program Membership`, `Event Registrations`, `Product Specific Comms` → Discover
* `DLI Training`, `Webinars`, `Conference`, `Conf Sessions Live`, `Other Events` → Learn
* `DevZone Downloads`, repeated docs/assets-type interactions → Evaluate
* `NGC Downloads`, `Hosted API`, `Hackathon`, `Brev`, `Program Applications` → Build
* `Forum Contributions`, `Bugs Filed`, speaker/instructor roles, contests → Champion

### DuckDB pseudo-code

```sql
create or replace table activity_ontology_v1 as
select
    *,
    case
        when activity in ('On-Demand Views', 'Dev Program Membership', 'Event Registrations', 'Product Specific Comms')
            then 'Discover'
        when activity in ('DLI Training', 'Webinars', 'Conference', 'Conf Sessions Live', 'Other Events')
            then 'Learn'
        when activity in ('DevZone Downloads')
            then 'Evaluate'
        when activity in ('NGC Downloads', 'Hosted API', 'Hackathon', 'Brev', 'Program Applications')
            then 'Build'
        when activity in ('Forum Contributions', 'Bugs Filed', 'Contests')
             or lower(coalesce(activity_role, '')) in ('speaker', 'instructor', 'presenter')
            then 'Champion'
        else 'Other'
    end as journey_signal
from activity_enriched_v1;
```

## 2B. Effort-level features

Use:

* passive
* moderate
* high_effort

### Example logic

```sql
case
    when activity in ('On-Demand Views', 'Product Specific Comms') then 'Passive'
    when activity in ('Webinars', 'Conference', 'Other Events', 'DLI Training', 'DevZone Downloads') then 'Moderate'
    when activity in ('Hosted API', 'Hackathon', 'Brev', 'NGC Downloads', 'Forum Contributions', 'Bugs Filed', 'Program Applications') then 'High'
    else 'Unknown'
end as effort_level
```

## 2C. Persona-lane hint features

Use keywords from:

* `activity_name`
* `filepath`
* `lead_source_details`
* maybe `development_areas` / `fields_of_interest`

Suggested lanes:

* CUDA / Accelerated
* GenAI / Inference
* Robotics / Edge
* Simulation / Omniverse
* Learning / Community

### DuckDB pseudo-code

```sql
case
    when regexp_matches(lower(coalesce(activity_name,'') || ' ' || coalesce(filepath,'') || ' ' || coalesce(lead_source_details,'')),
        'cuda|cudnn|rapids|nccl|cutlass|dali')
        then 'CUDA'
    when regexp_matches(lower(coalesce(activity_name,'') || ' ' || coalesce(filepath,'') || ' ' || coalesce(lead_source_details,'')),
        'triton|tensorrt|nemo|nim|ngc|huggingface|inference|llm')
        then 'GenAI'
    when regexp_matches(lower(coalesce(activity_name,'') || ' ' || coalesce(filepath,'') || ' ' || coalesce(lead_source_details,'')),
        'jetson|isaac|robotics|edge')
        then 'Robotics'
    when regexp_matches(lower(coalesce(activity_name,'') || ' ' || coalesce(filepath,'') || ' ' || coalesce(lead_source_details,'')),
        'omniverse|openusd|usd|simulation|digital twin')
        then 'Simulation'
    else 'Learning_Community'
end as persona_hint
```

---

## Layer 3: Windowed developer features

**Tables:**

* `dev_features_30d_v1`
* `dev_features_90d_v1`
* `dev_features_180d_v1`
* maybe `dev_weekly_features_v1` for HMM

These align directly with your original project plan to capture behavior over 30, 90, 180, and 360-day windows. 

These are the core features I would engineer.

# Feature groups to build

## A. Volume features

These measure how much activity happened.

### Features

* `activity_count_total`
* `activity_score_sum`
* `activity_score_avg`
* `unique_activity_days`
* `unique_activity_types`
* `high_effort_activity_count`

### DuckDB pseudo-code

```sql
select
    developer_id,
    count(*) as activity_count_total,
    sum(activity_score) as activity_score_sum,
    avg(activity_score) as activity_score_avg,
    count(distinct activity_date) as unique_activity_days,
    count(distinct activity) as unique_activity_types,
    sum(case when effort_level = 'High' then 1 else 0 end) as high_effort_activity_count
from activity_ontology_v1
where activity_date >= current_date - interval 90 day
group by developer_id;
```

---

## B. Recency features

These measure how recently the user acted.

### Features

* `days_since_last_activity`
* `days_since_last_build_signal`
* `days_since_last_learn_signal`
* `days_since_first_activity`
* `tenure_days`

### DuckDB pseudo-code

```sql
select
    developer_id,
    date_diff('day', max(activity_date), current_date) as days_since_last_activity,
    date_diff('day',
        max(case when journey_signal = 'Build' then activity_date end),
        current_date) as days_since_last_build_signal,
    date_diff('day',
        max(case when journey_signal = 'Learn' then activity_date end),
        current_date) as days_since_last_learn_signal,
    date_diff('day', min(activity_date), current_date) as days_since_first_activity,
    date_diff('day', cast(min(created_date) as date), current_date) as tenure_days
from activity_ontology_v1
group by developer_id;
```

---

## C. Diversity features

These measure breadth of engagement.

### Features

* `unique_journey_signals`
* `unique_persona_hints`
* `unique_modalities`
* `active_weeks`
* `channel_breadth`

### DuckDB pseudo-code

```sql
select
    developer_id,
    count(distinct journey_signal) as unique_journey_signals,
    count(distinct persona_hint) as unique_persona_hints,
    count(distinct activity) as channel_breadth,
    count(distinct date_trunc('week', activity_date)) as active_weeks
from activity_ontology_v1
group by developer_id;
```

---

## D. Journey-state count features

These are the simplest and most useful.

### Features

* `discover_count`
* `learn_count`
* `evaluate_count`
* `build_count`
* `champion_count`

### DuckDB pseudo-code

```sql
select
    developer_id,
    sum(case when journey_signal = 'Discover' then 1 else 0 end) as discover_count,
    sum(case when journey_signal = 'Learn' then 1 else 0 end) as learn_count,
    sum(case when journey_signal = 'Evaluate' then 1 else 0 end) as evaluate_count,
    sum(case when journey_signal = 'Build' then 1 else 0 end) as build_count,
    sum(case when journey_signal = 'Champion' then 1 else 0 end) as champion_count
from activity_ontology_v1
where activity_date >= current_date - interval 90 day
group by developer_id;
```

---

## E. Weighted behavioral scores

These are better than one raw engagement score.

### Features

* `learn_score`
* `evaluate_score`
* `build_score`
* `champion_score`
* `passive_score`
* `high_effort_score`

### DuckDB pseudo-code

```sql
select
    developer_id,
    sum(case when journey_signal = 'Learn' then activity_score else 0 end) as learn_score,
    sum(case when journey_signal = 'Evaluate' then activity_score else 0 end) as evaluate_score,
    sum(case when journey_signal = 'Build' then activity_score else 0 end) as build_score,
    sum(case when journey_signal = 'Champion' then activity_score else 0 end) as champion_score,
    sum(case when effort_level = 'Passive' then activity_score else 0 end) as passive_score,
    sum(case when effort_level = 'High' then activity_score else 0 end) as high_effort_score
from activity_ontology_v1
group by developer_id;
```

---

## F. Frequency / cadence features

These capture return behavior.

### Features

* `avg_days_between_activities`
* `median_days_between_activities`
* `activity_weeks_last_12`
* `max_gap_days`
* `reactivation_flag`

### Best split

* compute base event sequence in DuckDB
* finish interval calculations in Python if needed

### Python pseudo-code

```python
df = activity_df.sort_values(["developer_id", "activity_date"])
df["prev_date"] = df.groupby("developer_id")["activity_date"].shift(1)
df["gap_days"] = (df["activity_date"] - df["prev_date"]).dt.days

cadence = (
    df.groupby("developer_id")
      .agg(
          avg_days_between_activities=("gap_days", "mean"),
          median_days_between_activities=("gap_days", "median"),
          max_gap_days=("gap_days", "max")
      )
      .reset_index()
)

cadence["reactivation_flag"] = (cadence["max_gap_days"] >= 60).astype(int)
```

DuckDB can do some of this with window functions too, but Python is sometimes easier for debugging interval features.

---

## G. Persona-score features

These determine dominant lane.

### Features

* `cuda_score`
* `genai_score`
* `robotics_score`
* `simulation_score`
* `learning_community_score`

### DuckDB pseudo-code

```sql
select
    developer_id,
    sum(case when persona_hint = 'CUDA' then activity_score else 0 end) as cuda_score,
    sum(case when persona_hint = 'GenAI' then activity_score else 0 end) as genai_score,
    sum(case when persona_hint = 'Robotics' then activity_score else 0 end) as robotics_score,
    sum(case when persona_hint = 'Simulation' then activity_score else 0 end) as simulation_score,
    sum(case when persona_hint = 'Learning_Community' then activity_score else 0 end) as learning_community_score
from activity_ontology_v1
group by developer_id;
```

### Persona assignment pseudo-code

```sql
case
    when genai_score >= greatest(cuda_score, robotics_score, simulation_score, learning_community_score) then 'GenAI'
    when cuda_score >= greatest(genai_score, robotics_score, simulation_score, learning_community_score) then 'CUDA'
    when robotics_score >= greatest(genai_score, cuda_score, simulation_score, learning_community_score) then 'Robotics'
    when simulation_score >= greatest(genai_score, cuda_score, robotics_score, learning_community_score) then 'Simulation'
    else 'Learning_Community'
end as persona
```

---

## H. Journey-state assignment features

These support your rule-based current-state label.

### Features

* `current_journey_state`
* `current_state_confidence`
* `highest_state_reached`
* `recent_build_flag`
* `recent_champion_flag`

### Simple rule logic

```sql
case
    when champion_count >= 2 then 'Champion'
    when build_count >= 2 or build_score >= 20 then 'Build'
    when evaluate_count >= 2 then 'Evaluate'
    when learn_count >= 2 then 'Learn'
    when discover_count >= 1 then 'Discover'
    else 'Dormant'
end as current_journey_state
```

You can tune thresholds later.

---

## I. Transition features

These compare window outputs.

### Features

* `state_30d`
* `state_90d`
* `state_180d`
* `progressed_30_to_90`
* `dropped_30_to_90`
* `state_change_count`

### DuckDB pseudo-code

```sql
create or replace table dev_transition_v1 as
select
    a.developer_id,
    a.current_journey_state as state_30d,
    b.current_journey_state as state_90d,
    c.current_journey_state as state_180d,
    case
        when a.state_rank < b.state_rank then 1 else 0
    end as progressed_30_to_90,
    case
        when a.state_rank > b.state_rank then 1 else 0
    end as dropped_30_to_90
from dev_features_30d_v1 a
left join dev_features_90d_v1 b using(developer_id)
left join dev_features_180d_v1 c using(developer_id);
```

---

## J. HMM-ready weekly features

If you include HMM, this is the table the modeling team should use.

**Table:** `dev_weekly_features_v1`

### Features per developer-week

* `week_start`
* `activity_count_total`
* `activity_score_sum`
* `learn_count`
* `evaluate_count`
* `build_count`
* `champion_count`
* `high_effort_activity_count`
* `unique_activity_types`
* `persona_lane_scores`
* `days_since_prev_activity`
* `active_flag`

### DuckDB pseudo-code

```sql
create or replace table dev_weekly_features_v1 as
select
    developer_id,
    date_trunc('week', activity_date) as week_start,
    count(*) as activity_count_total,
    sum(activity_score) as activity_score_sum,
    sum(case when journey_signal = 'Learn' then 1 else 0 end) as learn_count,
    sum(case when journey_signal = 'Evaluate' then 1 else 0 end) as evaluate_count,
    sum(case when journey_signal = 'Build' then 1 else 0 end) as build_count,
    sum(case when journey_signal = 'Champion' then 1 else 0 end) as champion_count,
    sum(case when effort_level = 'High' then 1 else 0 end) as high_effort_activity_count,
    count(distinct activity) as unique_activity_types,
    sum(case when persona_hint = 'CUDA' then activity_score else 0 end) as cuda_score,
    sum(case when persona_hint = 'GenAI' then activity_score else 0 end) as genai_score,
    sum(case when persona_hint = 'Robotics' then activity_score else 0 end) as robotics_score,
    sum(case when persona_hint = 'Simulation' then activity_score else 0 end) as simulation_score
from activity_ontology_v1
group by 1, 2;
```

Then Python handles:

* filling missing inactive weeks
* `log1p`
* scaling
* sequence packing for the HMM

### Python pseudo-code

```python
weekly = weekly.sort_values(["developer_id", "week_start"])

feature_cols = [
    "activity_count_total",
    "activity_score_sum",
    "learn_count",
    "evaluate_count",
    "build_count",
    "champion_count",
    "high_effort_activity_count",
    "unique_activity_types",
    "cuda_score",
    "genai_score",
    "robotics_score",
    "simulation_score"
]

weekly[feature_cols] = np.log1p(weekly[feature_cols])

X_list = []
lengths = []

for dev_id, g in weekly.groupby("developer_id"):
    X = g[feature_cols].to_numpy()
    X_list.append(X)
    lengths.append(len(X))

X_all = np.vstack(X_list)
```



RAW DATA
(activity + contact tables)
        │
        ▼
activity_enriched_v1
(join + clean + standardize)
        │
        ▼
────────────────────────────────────
ACTIVITY-LEVEL ENGINEERING
────────────────────────────────────
        │
        ▼
activity_ontology_v1
(each row gets 4 tags)

    ├── Journey Signal
    │       Discover → Champion (1–5)
    │
    ├── Effort Level
    │       Passive / Moderate / High (1–3)
    │
    ├── Persona Signals
    │       keyword matching:
    │       activity_name + filepath + profile
    │
    └── Modality
            Event / Download / API / etc.

        │
        ▼
Persona Raw Scores (row-level)
    ├── CUDA (0–3)
    ├── GenAI (0–3)
    ├── Robotics (0–3)
    ├── Simulation (0–3)
        │
        ▼
Weighted Persona Scores
    persona_score = activity_score × persona_raw
        │
        ▼
────────────────────────────────────
DEVELOPER-LEVEL AGGREGATION
────────────────────────────────────
        │
        ▼
dev_features_lifetime_v1

    ├── lifetime_activity_count
    ├── lifetime_build_count
    ├── persona scores (summed)
        │
        ▼
Persona Normalization

    persona_norm = persona_score / total_score

        │
        ▼
dev_persona_v1

    ├── persona (top score)
    ├── persona_confidence
    ├── confidence_tier
    ├── mixed_flag

────────────────────────────────────
TIME WINDOW FEATURES
────────────────────────────────────
        │
        ▼
dev_features_30d / 90d / 180d

    ├── activity counts
    ├── journey counts
    ├── effort counts
    ├── modality counts
    ├── recency features

        │
        ▼
Journey State Assignment

    Champion > Build > Evaluate > Learn > Discover > Dormant

        │
        ▼
dev_profile_30d / 90d / 180d

────────────────────────────────────
TRANSITIONS
────────────────────────────────────
        │
        ▼
dev_transition_v1

    ├── Progressed
    ├── Stable
    ├── Regressed
    ├── Activated
    ├── Churned

────────────────────────────────────
DORMANCY MODEL (SURVIVAL-BASED)
────────────────────────────────────
        │
        ▼
Weekly Aggregation
(dev_meaningful_week_v1)

        │
        ▼
Meaningful Week Flag
    (Build OR Moderate/High OR repeated passive)

        │
        ▼
Activation Gate
    ├── Activated
    └── Unactivated

        │
        ▼
Days Since Last Meaningful Week

        │
        ▼
Kaplan-Meier Curve
(return probability over time)

        │
        ▼
Dormancy Classification

    Active   (<56 days)
    At_Risk  (56–83)
    Dormant  (84+)
    Unactivated

────────────────────────────────────
FINAL OUTPUT
────────────────────────────────────
        │
        ▼
dev_profile_final_v3

    ├── Persona
    ├── Journey State (30d/90d/180d)
    ├── Transition + Trajectory
    ├── Dormancy Status
    ├── Activity + Engagement Features
