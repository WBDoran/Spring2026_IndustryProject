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

