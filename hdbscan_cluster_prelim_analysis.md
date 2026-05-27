# HDBSCAN Cluster Prelim Analysis

This version of analysis reflects the size-ranked naming used in the HDBSCAN pipeline parquet remap:
- for `active`, `cooling`, and `at_risk`, the largest non-noise cluster is `_0`, the next is `_1`, and so on
- `*_noise`, `Dormant_*`, and `unactivated` stay unchanged
- this analysis is based on the NAV dev_lifecycle_cluster_membership_v11_final.parquet snapshot used in the HDBSCAN impact pipeline, so the numbering is standardized by descending cluster size rather than the raw HDBSCAN label ids

## Biggest Differences Between Active, Cooling, And At-Risk

### Active

- `Active` is the clearest **current-intent** population.
- It splits mainly between:
  - `GenAI` evaluator / learning behavior
  - `CUDA` builder / downloader behavior
- The biggest internal difference is whether someone looks like a:
  - current evaluator
  - current learner with community engagement
  - current builder

### Cooling

- `Cooling` is still mostly a **live education audience**, but one with weakening momentum.
- It is much more learner-dominated than `active`.
- The main variation is across:
  - `GenAI` learners
  - `CUDA` learners
  - mixed learner groups with training, downloads, and some community behavior

### At Risk

- `At-risk` looks like a **former education / technical learning audience** that is closer to churn.
- It is still learner-heavy, but less live than `cooling`.
- The strongest differences are between:
  - broad technical learners
  - GenAI training-led learners
  - CUDA learners
  - event-led learners

### Where They Differ Most

- `Active` still shows people doing something now: evaluating, learning, or building.
- `Cooling` still looks reachable because the education pattern is present, but fading.
- `At-risk` looks more decayed: prior interest is visible, but current continuation is weaker.

## Active

### `active_0` | 155,026 developers
- Descriptive name: **GenAI Learning Evaluators**
- Business name: **GenAI Evaluation Cohort**
- Why it matters:
  - strongest `GenAI` + `Evaluator` pattern
  - centered on `webinar`, `dli_training`, and `devzone_download`
  - clearest large-scale evaluation-without-building segment

### `active_noise` | 105,723 developers
- Descriptive name: **Mixed Active Generalists**
- Business name: **Active Multi-Path Users**
- Why it matters:
  - most mixed active segment
  - broader persona and journey mix
  - catch-all active population that does not fit one clean behavior type

### `active_1` | 66,683 developers
- Descriptive name: **Low-Effort GenAI Evaluators**
- Business name: **Lightweight GenAI Evaluators**
- Why it matters:
  - mostly `GenAI`
  - mostly `Evaluator`
  - lighter-touch version of `active_0`

### `active_2` | 29,395 developers
- Descriptive name: **GenAI Community Learners**
- Business name: **GenAI Community Participants**
- Why it matters:
  - community-led rather than webinar-led
  - `forum_contribution` is the clearest differentiator

### `active_3` | 24,653 developers
- Descriptive name: **High-Effort GenAI Learning Evaluators**
- Business name: **High-Intent GenAI Evaluators**
- Why it matters:
  - training-led GenAI evaluator segment
  - more intense version of the evaluator / learning pattern

### `active_4` | 18,554 developers
- Descriptive name: **Webinar-Led GenAI Evaluators**
- Business name: **Event-Driven GenAI Evaluators**
- Why it matters:
  - strongest webinar-led active segment
  - useful for content / event journey targeting

### `active_5` | 18,015 developers
- Descriptive name: **CUDA Builder-Downloaders**
- Business name: **Core CUDA Builders**
- Why it matters:
  - strongest builder-shaped active cluster
  - clearest CUDA + builder + download pattern

## Cooling

### `cooling_0` | 83,334 developers
- Descriptive name: **Cooling GenAI Learners**
- Business name: **Cooling GenAI Education Users**
- Why it matters:
  - very pure GenAI learner cluster
  - high-effort history but weak current visible asset breadth

### `cooling_noise` | 81,368 developers
- Descriptive name: **Mixed Cooling Download Generalists**
- Business name: **Cooling Multi-Path Users**
- Why it matters:
  - broadest cooling catch-all
  - strongest mixed-persona download-centered cooling group

### `cooling_1` | 56,824 developers
- Descriptive name: **Cooling GenAI Training Learners**
- Business name: **Cooling GenAI Training Users**
- Why it matters:
  - training-heavy GenAI learners
  - clearest education audience losing momentum segment

### `cooling_2` | 35,432 developers
- Descriptive name: **Cooling Mixed-Persona Training Users**
- Business name: **Cooling Cross-Persona Learners**
- Why it matters:
  - more mixed than the purer GenAI or CUDA learner groups
  - still meaningfully training-led

### `cooling_3` | 26,704 developers
- Descriptive name: **Cooling CUDA Learners**
- Business name: **Cooling CUDA Education Users**
- Why it matters:
  - simple CUDA learner segment
  - low-activity but still identifiable

### `cooling_4` | 25,430 developers
- Descriptive name: **Cooling Mixed Learners**
- Business name: **Cooling General Learning Users**
- Why it matters:
  - balanced learner group
  - useful mid-spectrum cluster between the pure persona groups

### `cooling_5` | 24,216 developers
- Descriptive name: **Cooling CUDA Community Learners**
- Business name: **Cooling CUDA Community Users**
- Why it matters:
  - CUDA learner segment with clearer community flavor

### `cooling_6` | 23,192 developers
- Descriptive name: **Cooling High-Effort GenAI Learners**
- Business name: **Cooling High-Intent GenAI Users**
- Why it matters:
  - very concentrated GenAI learner cluster
  - strong sign of formerly serious engagement

## At Risk

### `at_risk_0` | 436,295 developers
- Descriptive name: **At-Risk CUDA/GenAI Learners**
- Business name: **At-Risk Technical Learners**
- Why it matters:
  - biggest at-risk segment
  - technical learning behavior is still visible, but current continuation is weak

### `at_risk_1` | 365,945 developers
- Descriptive name: **Broad At-Risk Learning Builders**
- Business name: **At-Risk Builder-Learners**
- Why it matters:
  - most mixed and potentially recoverable at-risk cluster
  - some builder residue still remains

### `at_risk_2` | 210,377 developers
- Descriptive name: **At-Risk GenAI Training Learners**
- Business name: **At-Risk GenAI Training Users**
- Why it matters:
  - clear GenAI training audience that did not sustain

### `at_risk_3` | 206,907 developers
- Descriptive name: **At-Risk GenAI Workshop Learners**
- Business name: **At-Risk GenAI Hands-On Learners**
- Why it matters:
  - more hands-on than `at_risk_2`
  - stronger bug / workshop flavor

### `at_risk_4` | 145,077 developers
- Descriptive name: **At-Risk CUDA Learners**
- Business name: **At-Risk CUDA Education Users**
- Why it matters:
  - narrow CUDA technical learning segment

### `at_risk_5` | 118,776 developers
- Descriptive name: **At-Risk Webinar Learners**
- Business name: **At-Risk Event-Led Learners**
- Why it matters:
  - clearest event / webinar-led at-risk cohort

### `at_risk_noise` | 97,500 developers
- Descriptive name: **Mixed At-Risk Download Generalists**
- Business name: **At-Risk Multi-Path Users**
- Why it matters:
  - mixed backlog segment
  - less coherent than the named at-risk clusters

## Short Takeaways

- `Active` is split between current `GenAI` evaluators and a much smaller but distinct `CUDA` builder segment.
- `Cooling` is mostly an education audience in decline, with the biggest split between `GenAI`, `CUDA`, and mixed learner pathways.
- `At-risk` is mostly a former technical learning audience with weaker continuation and a few more specialized subgroups.
- The cleanest high-level narrative is:
  - `Active` = current builders and evaluators
  - `Cooling` = learners losing momentum
  - `At Risk` = former learners and light builders close to churn
