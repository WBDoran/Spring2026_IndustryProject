cluster users based on their maturity level in the developer journey. Instead of only looking at how many activities they did, we look at how their behavior changes over 30, 60, 90, and longer-day periods. This helps identify whether a user is just exploring, actively learning, evaluating NVIDIA technologies, or showing signs of real adoption.

clustering developers by maturity in their journey using longitudinal activity and profile features across 30, 60, 90, 180, and 365-day windows, so we can distinguish exploration, learning, evaluation, and adoption behavior over time, while also identifying the current gap between engagement data and true user-level SDK adoption measurement.


Features I think we need

developer u and a time window W days

- A(u,W) = all activity rows for user u in the last W days
- D(u,W) = all SDK download rows for user u in the last W days
- today = reference date for feature generation
- n(X) = number of rows in set X
- sum(X.f) = sum of field f over set X
- count_distinct(X.f) = distinct count of field f
- I(condition) = indicator, 1 if true else 0

W ∈ {30, 60, 90, 180, 365, lifetime}

| Feature Name         | Formula / Pseudocode                   | Source   | Why it Matters              |
| -------------------- | -------------------------------------- | -------- | --------------------------- |
| activity_count_W     | `COUNT(A_W)`                           | activity | Total engagement volume     |
| activity_score_sum_W | `SUM(activity_score)`                  | activity | Weighted engagement quality |
| activity_score_avg_W | `SUM(score) / COUNT(*)`                | activity | Average engagement quality  |
| activity_score_max_W | `MAX(activity_score)`                  | activity | Peak engagement             |
| active_days_W        | `COUNT(DISTINCT DATE(activity_date))`  | activity | Engagement spread           |
| activities_per_day_W | `activity_count_W / active_days_W`     | activity | Intensity per session       |
| score_per_day_W      | `activity_score_sum_W / active_days_W` | activity | Depth per session           |

| Feature Name             | Formula / Pseudocode                  | Source   | Why it Matters          |
| ------------------------ | ------------------------------------- | -------- | ----------------------- |
| days_since_last_activity | `today - MAX(activity_date)`          | activity | Detects dormancy        |
| engagement_span_W        | `MAX(date) - MIN(date)`               | activity | Duration of engagement  |
| active_weeks_W           | `COUNT(DISTINCT WEEK(activity_date))` | activity | Weekly consistency      |
| pct_weeks_active_W       | `active_weeks_W / (W/7)`              | activity | Regularity of usage     |
| avg_gap_days_W           | `MEAN(diff(sorted(activity_dates)))`  | activity | Consistency             |
| std_gap_days_W           | `STD(diff(...))`                      | activity | Stability vs randomness |
| active_last_14d          | `1 if last_activity ≤ 14 days`        | activity | Recent engagement flag  |

| Feature Name               | Formula / Pseudocode                 | Source   | Why it Matters          |
| -------------------------- | ------------------------------------ | -------- | ----------------------- |
| learning_count_W           | `COUNT(activity IN learning_types)`  | activity | Early-stage behavior    |
| event_count_W              | `COUNT(activity IN event_types)`     | activity | Community engagement    |
| technical_count_W          | `COUNT(activity IN technical_types)` | activity | Deep engagement         |
| program_count_W            | `COUNT(activity IN program_types)`   | activity | Commitment level        |
| learning_share_W           | `learning_count / total_count`       | activity | Passive learning signal |
| technical_share_W          | `technical_count / total_count`      | activity | Adoption signal         |
| event_share_W              | `event_count / total_count`          | activity | Exploration/community   |
| passive_to_technical_ratio | `learning_count / technical_count`   | activity | Maturity indicator      |

| Feature Name              | Formula / Pseudocode            | Source   | Why it Matters        |
| ------------------------- | ------------------------------- | -------- | --------------------- |
| distinct_activity_types_W | `COUNT(DISTINCT activity)`      | activity | Breadth of engagement |
| distinct_activity_names_W | `COUNT(DISTINCT activity_name)` | activity | Asset exploration     |
| distinct_campaigns_W      | `COUNT(DISTINCT campaign_id)`   | activity | Exposure diversity    |
| activity_entropy_W        | `-Σ(p * log p)`                 | activity | Behavioral diversity  |
| top_activity_share_W      | `MAX(activity_share)`           | activity | Focus vs exploration  |

| Feature Name               | Formula / Pseudocode       | Source       | Why it Matters        |
| -------------------------- | -------------------------- | ------------ | --------------------- |
| sdk_download_count_W       | `COUNT(D_W)`               | sdk_download | Core adoption signal  |
| unique_sdk_W               | `COUNT(DISTINCT product)`  | sdk_download | Breadth of usage      |
| unique_sources_W           | `COUNT(DISTINCT source)`   | sdk_download | Platform spread       |
| repeat_download_rate       | `(total - unique) / total` | sdk_download | Depth of usage        |
| downloads_per_day          | `downloads / active_days`  | both         | Intensity of adoption |
| download_to_activity_ratio | `downloads / activities`   | both         | Conversion signal     |
| has_download_flag          | `1 if downloads > 0`       | sdk_download | Binary adoption       |
| repeat_download_flag       | `1 if total > unique`      | sdk_download | Strong usage signal   |

| Feature Name            | Formula / Pseudocode          | Source       | Why it Matters         |
| ----------------------- | ----------------------------- | ------------ | ---------------------- |
| activity_growth_30_60   | `activity_60 - activity_30`   | activity     | Growth trajectory      |
| activity_growth_60_90   | `activity_90 - activity_60`   | activity     | Continued engagement   |
| score_growth_30_60      | `score_60 - score_30`         | activity     | Increasing depth       |
| download_growth_30_60   | `downloads_60 - downloads_30` | sdk_download | Adoption progression   |
| technical_share_growth  | `tech_90 - tech_30`           | activity     | Shift to technical use |
| engagement_acceleration | `(90-60) - (60-30)`           | activity     | Momentum               |
| retention_slope         | `slope([30,60,90])`           | activity     | Trend of engagement    |

| Feature Name      | Formula / Pseudocode               | Source   | Why it Matters       |
| ----------------- | ---------------------------------- | -------- | -------------------- |
| attended_count_W  | `COUNT(attendance = attended)`     | activity | Real participation   |
| no_show_count_W   | `COUNT(attendance != attended)`    | activity | Weak engagement      |
| attendance_rate   | `attended / total_events`          | activity | Commitment           |
| contributor_count | `COUNT(role IN contributor_roles)` | activity | Advanced engagement  |
| serious_share_W   | `serious_actions / total`          | activity | Depth of interaction |

| Feature Name             | Formula / Pseudocode            | Source  | Why it Matters         |
| ------------------------ | ------------------------------- | ------- | ---------------------- |
| profile_age_days         | `today - created_date`          | contact | User maturity baseline |
| engagement_tenure_days   | `today - first_activity`        | contact | Experience level       |
| days_since_devzone_login | `today - last_login`            | contact | Platform engagement    |
| is_rdp_member            | `1 if in program`               | contact | Commitment             |
| rdp_tenure_days          | `today - program_start`         | contact | Depth of involvement   |
| days_to_first_activity   | `first_activity - created_date` | contact | Activation speed       |

| Feature Name             | Formula / Pseudocode               | Source | Why it Matters         |
| ------------------------ | ---------------------------------- | ------ | ---------------------- |
| days_to_first_download   | `first_download - first_activity`  | both   | Adoption speed         |
| activity_before_download | `COUNT(activity < first_download)` | both   | Effort before adoption |
| download_after_training  | `1 if training before download`    | both   | Learning impact        |
| learning_to_download_gap | `download_date - learning_date`    | both   | Conversion timing      |
