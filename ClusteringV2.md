# Developer Clustering Methodology v2 — Two-Layer Segmentation

This document specifies a redesign of the developer clustering pipeline. It replaces the single-axis MiniBatchKMeans (k=4) baseline currently in `DeveloperClustering.ipynb` with a two-layer segmentation system aligned with the project's strategic guidance: a stable **lane** (what kind of builder they are) and a dynamic **journey state** (where they are right now).

The redesign keeps the existing DuckDB + pandas + scikit-learn stack and reuses `activity_final`, `contact_final`, and `sdk_download_final`. New artifacts are written as versioned tables (`*_v1`) rather than mutating existing ones, so the v1 tier output remains reproducible while v2 is built alongside it.

---

## 1. Why the current approach is structurally limited

The current pipeline produces four global tiers (Beginner / Experienced / Advanced / Enterprise) by clustering 31 features in a single Euclidean space after `log1p` + `StandardScaler`. Three problems compound:

**Single-axis engagement.** `activity_score` blends learning, implementation, community influence, and marketing visibility into one number. A developer scored 100 for a presenter role is treated as comparable in "depth" to one with 100 in cumulative API calls — but they have very different jobs-to-be-done and require very different next actions.

**Lane collapse.** A robotics developer working through Jetson + Isaac, a CUDA performance engineer, and a GenAI builder using NIM/Triton can land in the same "Advanced" tier despite having almost no overlap in what they need from the platform. The single-tier label hides this entirely.

**Static snapshot.** The model treats the 9.3M developers as a fixed cross-section. It cannot answer: *which developers just moved from Learn to Prototype?* or *who is stalling at Evaluate?* — questions that drive intervention timing.

**Tenure blindness.** A developer 30 days into their journey gets compared to one 18 months in using the same raw counts. The engagement features need to be tenure-normalized.

The redesign addresses each.

---

## 2. Target architecture

```
                 ┌──────────────────────────┐
                 │  activity_final          │
                 │  contact_final           │
                 │  sdk_download_final      │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │  Phase 1                 │
                 │  activity_ontology_v1    │  ← tag every event with
                 │  (lane, stage, modality, │     lane / stage / modality / effort
                 │   effort)                │
                 └────────────┬─────────────┘
                              │
                              ▼
            ┌─────────────────┴──────────────────┐
            │                                    │
            ▼                                    ▼
┌──────────────────────────┐      ┌──────────────────────────┐
│  Phase 2                 │      │  Phase 3                 │
│  developer_axis_scores   │      │  developer_lane_probs    │
│  learn / build / deploy  │      │  P(lane) from activity + │
│  community / breadth /   │      │  contact-derived prior   │
│  cadence / recency       │      │                          │
└────────────┬─────────────┘      └────────────┬─────────────┘
             │                                  │
             └──────────────┬───────────────────┘
                            ▼
              ┌──────────────────────────┐
              │  Phase 4                 │
              │  developer_segments_v1   │
              │  (lane, journey_state,   │
              │   confidence)            │
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  Phase 5 (optional)      │
              │  account_graph_v1        │
              │  champion / spillover    │
              │  signals                 │
              └──────────────────────────┘
```

Each developer ends with a structured label, not a single tier:

```
{
  developer_id: 12345,
  lane_top1: "GenAI",          lane_top1_prob: 0.71,
  lane_top2: "CUDA",           lane_top2_prob: 0.18,
  journey_state: "Prototype",  state_prob: 0.62,
  confidence: 0.74,
  is_champion: false,
  account_id: ...
}
```

---

## 3. Phase 1 — Activity ontology

Before any clustering, every row in `activity_final` is tagged with four orthogonal dimensions. This is the single highest-leverage change in the redesign — everything downstream becomes interpretable once events are typed.

### 3.1 The four dimensions

| Dimension | Values | Source columns |
|---|---|---|
| **Lane** | cuda, genai, robotics, simulation, community, unknown | `activity_name`, `filepath`, `activity`, `lead_source_details`, `nvidia_campaign_id` |
| **Stage** | discover, learn, evaluate, prototype, build, advocate | `activity_type`, `activity_role`, `activity_score`, `activity_attendance` |
| **Modality** | live, async, asset, forum, api, application, feedback | `activity_type`, `filepath` |
| **Effort** | passive, moderate, high | `activity_score` (and stage cross-check) |

### 3.2 Lane tagging — keyword rules

Build a keyword dictionary and apply it via SQL `CASE` over the concatenated activity text fields. The tagging is intentionally rule-based, auditable, and revisable:

```sql
CREATE OR REPLACE TABLE activity_ontology_v1 AS
WITH tagged AS (
  SELECT
    *,
    LOWER(COALESCE(activity_name, '') || ' ' ||
          COALESCE(activity, '')      || ' ' ||
          COALESCE(filepath, '')      || ' ' ||
          COALESCE(lead_source_details, '')) AS text_blob
  FROM activity_final
)
SELECT
  *,

  /* ---------------- LANE ---------------- */
  CASE
    WHEN regexp_matches(text_blob, '(cuda|cudnn|nsight|nccl|tensorrt-llm|cutlass)') THEN 'cuda'
    WHEN regexp_matches(text_blob, '(nim|triton|tensorrt|nemo|llm|generative|inference|riva)') THEN 'genai'
    WHEN regexp_matches(text_blob, '(jetson|isaac|ros|edge ai|embedded)') THEN 'robotics'
    WHEN regexp_matches(text_blob, '(omniverse|openusd|physx|modulus|digital twin|simulation)') THEN 'simulation'
    WHEN regexp_matches(text_blob, '(forum|hackathon|webinar|community|dli|conference)') THEN 'community'
    ELSE 'unknown'
  END AS lane,

  /* ---------------- STAGE ---------------- */
  CASE
    WHEN regexp_matches(text_blob, '(presenter|speaker|panel|hackathon)')           THEN 'advocate'
    WHEN regexp_matches(text_blob, '(api|container|model download|ngc pull|helm)')  THEN 'build'
    WHEN regexp_matches(text_blob, '(sample|notebook|sdk download|repo clone)')     THEN 'prototype'
    WHEN regexp_matches(text_blob, '(docs|asset|technical brief|whitepaper)')       THEN 'evaluate'
    WHEN regexp_matches(text_blob, '(dli|training|self.paced|instructor.led)')      THEN 'learn'
    WHEN regexp_matches(text_blob, '(webinar|on.demand|on demand|view)')            THEN 'discover'
    ELSE 'discover'
  END AS stage,

  /* ---------------- MODALITY ---------------- */
  CASE
    WHEN regexp_matches(text_blob, '(instructor.led|live|conference|in.person)') THEN 'live'
    WHEN regexp_matches(text_blob, '(self.paced|on.demand|recording)')           THEN 'async'
    WHEN regexp_matches(text_blob, '(forum|post|reply|accepted answer)')         THEN 'forum'
    WHEN regexp_matches(text_blob, '(api|hosted|playground)')                    THEN 'api'
    WHEN regexp_matches(text_blob, '(membership|signup|application|register)')   THEN 'application'
    WHEN regexp_matches(text_blob, '(feedback|survey|nps)')                      THEN 'feedback'
    ELSE 'asset'
  END AS modality,

  /* ---------------- EFFORT ---------------- */
  CASE
    WHEN activity_score >= 40 THEN 'high'
    WHEN activity_score >= 10 THEN 'moderate'
    ELSE 'passive'
  END AS effort

FROM tagged;
```

**Tuning protocol.** After first run, sample 200 rows per lane and validate manually. Iterate on the regex dictionary until ≥90% of `unknown`-labeled rows are genuinely ambiguous (not just missing keywords). Treat the keyword dictionary as a project artifact — version it next to the SQL.

### 3.3 Optional: marketing-vs-self-driven flag

A meaningful axis the PDF flags: distinguish outreach response from self-directed exploration. Add a fifth tag using `lead_source` and `nvidia_campaign_id`:

```sql
CASE
  WHEN nvidia_campaign_id IS NOT NULL
    OR lead_source ILIKE '%campaign%'
    OR lead_source ILIKE '%email%'        THEN 'campaign_driven'
  WHEN lead_source ILIKE '%forum%'
    OR lead_source ILIKE '%community%'    THEN 'community_driven'
  ELSE 'self_directed'
END AS origin
```

This becomes useful in Phase 4 — a developer whose Build-stage activity is mostly campaign-driven looks very different from one whose Build-stage activity is self-directed.

---

## 4. Phase 2 — Multi-axis scoring (replaces `activity_score` aggregations)

Instead of summing one `activity_score` per developer, produce six orthogonal axes. Each axis answers a different business question.

### 4.1 The six axes

| Axis | What it measures | Aggregation |
|---|---|---|
| `learn_score`     | Capacity-building (DLI, webinars, async training)              | Sum of `activity_score` where `stage IN ('learn','discover')` |
| `build_score`     | Hands-on implementation (API, containers, models, samples)     | Sum where `stage IN ('prototype','build')` |
| `deploy_score`    | Repeated technical depth, returns to high-effort actions       | Count of distinct weeks with `effort='high'` AND `stage IN ('build','prototype')` |
| `community_score` | Forum + advocacy + presenter activity                          | Sum where `stage='advocate'` OR `modality='forum'` |
| `breadth_score`   | Distinct lanes touched (1–5)                                   | `COUNT(DISTINCT lane)` excluding `unknown` |
| `cadence_score`   | Activity regularity                                            | `active_weeks / tenure_weeks` |
| `recency_score`   | Time-decayed recency                                           | `exp(-days_since_last_activity / 30)` |

### 4.2 Tenure normalization

Per the project guidance, every count needs to be tenure-normalized. Two versions of each score:

- **Raw** (`learn_score_raw`): used for absolute thresholds (e.g. "at least one DLI completion")
- **Per-month** (`learn_score_per_mo`): `raw / max(months_active, 1)`, used for clustering

Tenure base is `LEAST(first_activity_date, created_date)` to today.

### 4.3 SQL aggregation

```sql
CREATE OR REPLACE TABLE developer_axis_scores_v1 AS
WITH per_dev AS (
  SELECT
    a.developer_id,
    -- Raw axes
    SUM(CASE WHEN a.stage IN ('learn','discover') THEN a.activity_score ELSE 0 END) AS learn_score_raw,
    SUM(CASE WHEN a.stage IN ('prototype','build') THEN a.activity_score ELSE 0 END) AS build_score_raw,
    COUNT(DISTINCT CASE WHEN a.effort='high' AND a.stage IN ('build','prototype')
                        THEN date_trunc('week', a.activity_date) END)               AS deploy_score_raw,
    SUM(CASE WHEN a.stage='advocate' OR a.modality='forum' THEN a.activity_score ELSE 0 END) AS community_score_raw,
    COUNT(DISTINCT CASE WHEN a.lane <> 'unknown' THEN a.lane END)                   AS breadth_score,

    -- Cadence / recency
    COUNT(DISTINCT date_trunc('week', a.activity_date))                             AS active_weeks,
    DATE_DIFF('day', MAX(a.activity_date), CURRENT_DATE)                            AS days_since_last,
    DATE_DIFF('day', MIN(a.activity_date), CURRENT_DATE)                            AS span_days,

    -- Origin mix (from optional Phase 1 tag)
    AVG(CASE WHEN a.origin='campaign_driven' THEN 1.0 ELSE 0 END)                   AS campaign_share,
    AVG(CASE WHEN a.origin='self_directed'   THEN 1.0 ELSE 0 END)                   AS self_directed_share

  FROM activity_ontology_v1 a
  GROUP BY a.developer_id
)
SELECT
  p.*,
  /* tenure base */
  GREATEST(p.span_days / 30.0, 1.0) AS months_active,

  /* per-month axes */
  p.learn_score_raw     / GREATEST(p.span_days / 30.0, 1.0) AS learn_score_per_mo,
  p.build_score_raw     / GREATEST(p.span_days / 30.0, 1.0) AS build_score_per_mo,
  p.deploy_score_raw    / GREATEST(p.span_days / 30.0, 1.0) AS deploy_score_per_mo,
  p.community_score_raw / GREATEST(p.span_days / 30.0, 1.0) AS community_score_per_mo,

  /* cadence and recency */
  p.active_weeks::DOUBLE / GREATEST(p.span_days / 7.0, 1.0) AS cadence_score,
  EXP(-p.days_since_last / 30.0)                            AS recency_score
FROM per_dev p;
```

This replaces 24 of the 31 features in the current `dev_activity_features` cell with 7 interpretable, tenure-normalized axes plus their raw counterparts.

---

## 5. Phase 3 — Lane assignment (probabilistic)

The lane is the stable persona dimension. It changes slowly and should combine evidence from both activity history and contact profile.

### 5.1 Activity-derived lane evidence

For each developer × lane combination, sum activity volume and apply softmax:

```sql
CREATE OR REPLACE TABLE dev_lane_activity_v1 AS
WITH lane_volume AS (
  SELECT
    developer_id,
    lane,
    SUM(activity_score) AS lane_volume
  FROM activity_ontology_v1
  WHERE lane <> 'unknown'
  GROUP BY 1, 2
),
totals AS (
  SELECT developer_id, SUM(lane_volume) AS total FROM lane_volume GROUP BY 1
)
SELECT
  l.developer_id,
  l.lane,
  l.lane_volume,
  l.lane_volume::DOUBLE / NULLIF(t.total, 0) AS lane_share_activity
FROM lane_volume l
JOIN totals t USING (developer_id);
```

### 5.2 Contact-derived lane prior

Parse `development_areas`, `fields_of_interest`, and `industry_segment_vertical` for lane keywords. These are typically semicolon-separated free-text fields, so use the same regex dictionary as Phase 1:

```python
def lane_prior_from_contact(row):
    """Returns dict: lane -> prior weight (sums to 1)."""
    text = " ".join([
        str(row.get("development_areas", "")),
        str(row.get("fields_of_interest", "")),
        str(row.get("industry_segment_vertical", "")),
    ]).lower()

    weights = {l: 0.0 for l in ["cuda", "genai", "robotics", "simulation", "community"]}
    if re.search(r"cuda|hpc|accelerated computing", text):              weights["cuda"]       += 1
    if re.search(r"llm|generative|nlp|inference|nim|nemo", text):       weights["genai"]      += 1
    if re.search(r"robot|jetson|isaac|edge|embedded", text):            weights["robotics"]   += 1
    if re.search(r"omniverse|simulation|usd|digital twin|cae", text):   weights["simulation"] += 1
    if re.search(r"education|training|community|advocacy", text):       weights["community"]  += 1

    total = sum(weights.values())
    if total == 0:  # uninformative — return uniform
        return {k: 0.2 for k in weights}
    return {k: v / total for k, v in weights.items()}
```

### 5.3 Combining: posterior with shrinkage

Low-activity developers should lean on the prior; high-activity developers should lean on observed behavior. A simple shrinkage formula does this cleanly:

```
P(lane | dev) = α · activity_share + (1 − α) · contact_prior

where  α = total_activity / (total_activity + κ)    (κ ≈ 50)
```

When `total_activity = 0`, the developer's lane probabilities equal the contact prior. When `total_activity ≫ κ`, they equal the activity share. κ=50 places the crossover at ~50 cumulative activity score points — tunable.

```python
def lane_posterior(activity_shares, contact_prior, total_activity, kappa=50):
    alpha = total_activity / (total_activity + kappa)
    return {
        lane: alpha * activity_shares.get(lane, 0.0) + (1 - alpha) * contact_prior.get(lane, 0.2)
        for lane in ["cuda", "genai", "robotics", "simulation", "community"]
    }
```

Output: `developer_lane_probs_v1` with one row per developer holding `(lane_top1, lane_top1_prob, lane_top2, lane_top2_prob, lane_entropy)`. High entropy = ambiguous lane = candidate for "Mixed/Generalist" segment.

---

## 6. Phase 4 — Journey state (within-lane clustering)

The journey state is dynamic. Two implementations follow, chosen by data and time budget:

- **6.A — Static baseline (build first):** within-lane clustering on stage-mix features. Works on the existing snapshot. Implementable in a day.
- **6.B — Sequence model (upgrade path):** mixture of HMMs over weekly sequences. Captures actual progression. ~2-3 week effort.

### 6.A — Static within-lane clustering

For each lane, cluster developers separately on stage-mix features. This avoids the lane-collapse problem the global k=4 produced.

**Within-lane feature vector (8 features):**

```
- learn_share        = learn_score_raw     / total_score
- evaluate_share     = (sum where stage='evaluate') / total_score
- prototype_share    = (sum where stage='prototype') / total_score
- build_share        = (sum where stage='build') / total_score
- advocate_share     = (sum where stage='advocate') / total_score
- recency_score      (from Phase 2)
- cadence_score      (from Phase 2)
- self_directed_share (from Phase 2)
```

These are all in [0, 1] — no log-transform needed, no `StandardScaler` required (though it doesn't hurt). This is deliberately a small, interpretable feature space.

**Clustering choice.** Per the strategic guidance, prefer **HDBSCAN** over KMeans here:

```python
import hdbscan

def cluster_within_lane(df_lane, min_cluster_size=200):
    X = df_lane[FEATURES].values
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(X)
    return labels  # -1 = noise (genuine long-tail edge cases)
```

HDBSCAN's advantages here, per project guidance:
- Finds clusters of varying density (Build-stage GenAI is dense; Advocate is sparse — KMeans forces them to similar sizes)
- Explicitly assigns `-1` to outliers instead of forcing every developer into a bucket
- No need to pre-specify cluster count per lane — different lanes naturally have different numbers of meaningful states

**Fallback.** If HDBSCAN produces too many tiny clusters or runs slow on a lane with millions of developers, fall back to **MiniBatchKMeans with k chosen per lane via silhouette** (CUDA may genuinely have 3 states; GenAI may have 5).

**Labeling.** Don't pre-name the journey states. Let the algorithm produce raw cluster IDs, then label by inspecting the centroid stage-mix:

```python
def label_journey_state(centroid):
    """Map a centroid's stage-share vector to a journey-state label."""
    dominant = centroid.idxmax()  # which stage_share is largest
    if   dominant == "build_share"     and centroid["recency_score"] > 0.5: return "Active Implementer"
    elif dominant == "build_share":                                         return "Build (lapsed)"
    elif dominant == "prototype_share":                                     return "Prototype Builder"
    elif dominant == "evaluate_share":                                      return "Evaluator"
    elif dominant == "learn_share":                                         return "Learner"
    elif dominant == "advocate_share":                                      return "Community Advocate"
    else:                                                                    return "Explorer"
```

Apply per lane, then validate the labels against a sample of 10 developers per (lane, state) cell.

### 6.B — Mixture of HMMs (upgrade path)

When you're ready to model progression rather than snapshot, the natural extension:

1. Build `dev_weekly_sequence_v1` — one row per (developer, week) with the 8-feature vector above.
2. Fit one `hmmlearn.GaussianHMM` per lane, with 5–7 hidden states.
3. Constrain transition matrices to be sticky and mostly forward (high diagonal, soft monotone progression, plus dormant ↔ any-state edges).
4. For each developer: run forward-backward to get `P(state_t | sequence)`, take Viterbi path for the most-likely-journey trajectory.

Specific sticky transition prior — initialize the transition matrix as:

```
        Discov  Learn  Eval  Proto  Build  Advoc  Dorm
Discov  [0.65   0.20   0.05  0.02   0.01   0.02   0.05]
Learn   [0.05   0.65   0.15  0.05   0.02   0.03   0.05]
Eval    [0.02   0.10   0.55  0.20   0.05   0.03   0.05]
Proto   [0.01   0.05   0.10  0.55   0.20   0.04   0.05]
Build   [0.01   0.02   0.05  0.10   0.65   0.10   0.07]
Advoc   [0.02   0.05   0.05  0.05   0.15   0.60   0.08]
Dorm    [0.20   0.20   0.15  0.10   0.05   0.05   0.25]
```

Rather than fit it freely, use `hmmlearn.GaussianHMM(init_params="mc")` and seed `transmat_` with the matrix above so the EM doesn't drift into nonsensical "build → discover" jumps. The model will refine the values but stay near the journey shape.

Output for each developer adds to the v1 segment table:

```
- current_state, state_prob
- viterbi_path_last_12_weeks
- next_state_probs           (one-step-ahead from posterior)
- time_in_current_state
```

The HMM upgrade is described separately in the project guidance — it deserves its own notebook (`DeveloperJourney_HMM.ipynb`) rather than being crammed into the segmentation notebook.

---

## 7. Phase 5 — Final segment output

`developer_segments_v1` consolidates everything:

| Column | Type | Source |
|---|---|---|
| `developer_id` | bigint | join key |
| `account_id` | bigint | from `contact_final` |
| `lane_top1` | varchar | Phase 3 |
| `lane_top1_prob` | double | Phase 3 |
| `lane_top2` | varchar | Phase 3 |
| `lane_top2_prob` | double | Phase 3 |
| `lane_entropy` | double | Phase 3 — high entropy = generalist |
| `journey_state` | varchar | Phase 4 |
| `state_prob` | double | Phase 4 |
| `confidence` | double | `lane_top1_prob × state_prob` |
| `is_outlier` | boolean | HDBSCAN label = −1 |
| `tier_v1` | varchar | legacy label, kept for back-compat |

A **business-facing segment label** is then `{lane}_{journey_state}` — e.g. `genai_prototype_builder`, `cuda_active_implementer`, `robotics_learner`. That's the unit DevRel and product can target directly.

---

## 8. Phase 6 (optional) — Account-level signals

`account_id` and `normalized_account_name` mean adoption can be traced inside an organization. One materialized table goes a long way:

```sql
CREATE OR REPLACE TABLE account_graph_v1 AS
SELECT
  c.account_id,
  c.normalized_account_name,
  COUNT(DISTINCT c.developer_id)                                               AS dev_count,
  COUNT(DISTINCT s.lane_top1)                                                  AS lanes_active,
  SUM(CASE WHEN s.journey_state IN ('Build (lapsed)','Active Implementer')
           THEN 1 ELSE 0 END)                                                  AS active_implementers,
  SUM(CASE WHEN s.journey_state = 'Community Advocate' THEN 1 ELSE 0 END)      AS advocates,
  MIN(c.created_date)                                                          AS account_first_seen,
  MAX(s.confidence)                                                            AS top_dev_confidence
FROM contact_final c
LEFT JOIN developer_segments_v1 s USING (developer_id)
GROUP BY 1, 2;
```

Derivable from this: **champion detection** (any developer in `Community Advocate` state inside an account with ≥3 `Active Implementer` peers), **account readiness score**, and **spillover candidates** (accounts where one developer just moved into Build with no peers yet active).

The full bipartite developer–asset graph + node2vec embedding the strategic guidance recommends is the production version of this. The SQL above is the v0.1 — useful immediately, easy to extend.

---

## 9. SDK download data — context, not user truth

Per the strategic guidance and the source data caveat, `sdk_download_final` is aggregate (KPI=1, NV_FLAG used to filter internal NVIDIA traffic). It cannot be joined to individual developers. Use it as **market context**:

```sql
CREATE OR REPLACE TABLE download_heat_v1 AS
SELECT
  product_release,
  geography,
  date_trunc('week', download_date) AS week,
  SUM(downloads) AS weekly_downloads,
  AVG(SUM(downloads)) OVER (
      PARTITION BY product_release, geography
      ORDER BY date_trunc('week', download_date)
      ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
  ) AS trailing_4wk_avg
FROM sdk_download_final
WHERE kpi = 1 AND nv_flag = 0
GROUP BY 1, 2, 3;
```

A `heat_index = weekly_downloads / trailing_4wk_avg` per (product, geo, week) becomes a contextual feature. Attach it to developer activity by joining on `(activity_lane, geography, activity_week)` to ask: *does a robotics developer in APAC behave differently when Jetson interest is surging versus quiet?* This stays explicitly contextual — don't claim individual attribution.

---

## 10. Validation plan

The v1 tier model was validated by inspection of cluster centroids. v2 deserves stricter validation since it claims to model journeys:

| Check | Method | Pass criterion |
|---|---|---|
| **Lane stability** | Re-run lane assignment on activity from first 80% of tenure vs. full tenure. Compute % unchanged. | ≥ 85% lane stability |
| **State separability** | Silhouette score on within-lane clusters | ≥ 0.30 per lane |
| **Predictive validity** | Hold out the most recent 90 days. Does `journey_state` at day −90 predict `build_score_per_mo` over the held-out period? | F-statistic significant; effect size meaningful |
| **Face validity** | Sample 5 developers per (lane, state) cell. Eyeball their activity timelines against the assigned label. | ≥ 80% subjectively reasonable |
| **Outlier rate** | % of developers HDBSCAN labels as `-1` | 5–15% range — too low means noise being absorbed; too high means clusters too tight |
| **Tier-v1 cross-tab** | Confusion matrix between v1 tiers and v2 (lane, state) | Should not be diagonal — if v2 just reproduces v1, redesign added no info |

Implement each as a cell in a new `Segments_v1_Validation.ipynb` notebook, sequenced after `DeveloperClustering_v2.ipynb`.

---

## 11. Migration plan from current pipeline

The redesign is additive — no existing artifact is overwritten. Both the v1 tier and v2 segment can be live during transition.

| Step | New notebook | Reads | Writes |
|---|---|---|---|
| 1 | `Activity_Ontology.ipynb` | `activity_final` | `activity_ontology_v1` |
| 2 | `Developer_AxisScores.ipynb` | `activity_ontology_v1` | `developer_axis_scores_v1` |
| 3 | `Developer_Lane.ipynb` | `activity_ontology_v1`, `contact_final` | `developer_lane_probs_v1` |
| 4 | `DeveloperClustering_v2.ipynb` | axis scores + lane probs | `developer_segments_v1`, `Data/developer_segments_v1.csv` |
| 5 | `Segments_v1_Validation.ipynb` | all of the above | validation report |
| 6 (optional) | `Account_Graph.ipynb` | segments + contact | `account_graph_v1` |
| 7 (later) | `DeveloperJourney_HMM.ipynb` | activity_ontology + axis scores | `developer_journey_hmm_v1` |

The existing `DeveloperClustering.ipynb` and `developer_clusters` table stay untouched. The README's "Notebook Execution Order" section gets a new section appended for the v2 chain.

---

## 12. What this buys you, concretely

Concretely, the v2 output lets the project answer questions the v1 tier could not:

1. **"Show me robotics developers stalled in Evaluate."**
   `SELECT developer_id FROM developer_segments_v1 WHERE lane_top1='robotics' AND journey_state='Evaluator' AND recency_score < 0.3`

2. **"Which accounts have a champion plus three implementers but no Inception linkage?"**
   Joinable from `account_graph_v1` + `contact_final.inception_id`.

3. **"Who just moved from Learn to Prototype this month?"**
   Requires the HMM upgrade (or running v2 segmentation weekly and diffing).

4. **"What's the lane mix of campaign-driven activity?"**
   `campaign_share` from Phase 2 split by `lane_top1` shows whether marketing reaches the right audience.

5. **"For the GenAI Build segment, what's the breakdown by industry vertical?"**
   Standard joinable cross-tab.

The single tier label `Beginner|Experienced|Advanced|Enterprise` cannot answer any of these. The structured `(lane, journey_state, confidence, account_signals)` output answers them as routine SQL.

---

## 13. Open questions to validate before building

A few decisions deserve a quick sanity-check before committing to implementation:

1. **Lane keyword coverage.** Sample 1,000 rows from `activity_final` and check what % have at least one lane keyword match. If <60%, the keyword dictionary needs expansion (or a small classifier on `activity_name`).
2. **Tenure proxy.** Is `created_date` reliably populated? Is `first_activity_date` ever later than `created_date`? Choose tenure base accordingly.
3. **HDBSCAN feasibility on 9.3M rows.** It may need to run on a per-lane subsample (e.g. 500K per lane) and then assign remaining points by nearest-cluster-membership probability. KMeans is the safe fallback.
4. **Contact field cleanliness.** `development_areas` and `fields_of_interest` are often free-text and inconsistently populated. The lane prior degrades gracefully (uniform prior when empty), but it's worth checking the populated rate and most common values upfront.
5. **Held-out window for validation.** Currently the data range for activity is unspecified; the 90-day holdout assumes ≥6 months of history. If history is shorter, validation needs adjustment.

---

*End of methodology v2.*