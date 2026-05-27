# HDBSCAN Cluster Names And Key Differences

This is the shorter, more digestible version of the HDBSCAN cluster readout.

## Biggest Differences Between Active, Cooling, And At-Risk

### Active

- Most differentiated by **journey stage**.
- Splits mainly into two families:
  - `GenAI Evaluators` driven by `webinar`, `dli_training`, `devzone_download`, and some `forum_contribution`
  - `CUDA Builders` driven by `devzone_download` and `ngc_download`
- Compared with the other strata, `active` has the clearest evidence of **current intent**:
  - recent learning behavior
  - recent evaluation behavior
  - recent builder behavior
- The most important divide inside `active` is:
  - **builder-led CUDA behavior** vs
  - **learning / evaluation-led GenAI behavior**

### Cooling

- Much more dominated by **Learners** than `active`.
- Behavior is less about active evaluation and more about **education and content consumption**.
- Main asset pattern is:
  - `devzone_download`
  - `dli_training`
  - sometimes `webinar`
  - sometimes `forum_contribution`
- Compared with `active`, `cooling` clusters look like people who were engaged in learning workflows but are no longer showing strong current momentum.
- The biggest divide inside `cooling` is:
  - **GenAI learners**
  - **CUDA learners**
  - **mixed-persona learners**

### At Risk

- Also dominated by **Learners**, but the tone is different from `cooling`.
- `At-risk` clusters look further along the disengagement path:
  - more clearly dormant / decayed
  - less current variety
  - more “former interest” than “current exploration”
- The core asset pattern is still learning-oriented:
  - `devzone_download`
  - `dli_training`
  - `ngc_download`
  - sometimes `webinar`
- Compared with `cooling`, `at_risk` looks more like:
  - **historical technical learning**
  - **fading hands-on interest**
  - **weaker conversion into sustained builder behavior**

### Where The Strata Differ Most

- `Active` differs from the others because it still contains clear **current evaluators and current builders**.
- `Cooling` differs from `at_risk` because it still looks like a **live education audience**, just weakening.
- `At-risk` differs from `cooling` because it looks like a **former education audience** that is closer to dropping out.
- The strongest business distinction is:
  - `Active` = people doing something now
  - `Cooling` = people still connected, but fading
  - `At-risk` = people whose prior pattern is visible, but current continuation is weak

## Active

### `active_5`
- Descriptive name: **GenAI Learning Evaluators**
- Business name: **GenAI Evaluation Cohort**
- Why it matters:
  - strongest `GenAI` + `Evaluator` pattern
  - centered on `webinar`, `dli_training`, and `devzone_download`
  - one of the clearest “evaluation without building” segments

### `active_noise`
- Descriptive name: **Mixed Active Generalists**
- Business name: **Active Multi-Path Users**
- Why it matters:
  - most mixed active segment
  - broader persona and journey mix
  - strongest catch-all population for active users who do not fit a clean single behavior type

### `active_2`
- Descriptive name: **Low-Effort GenAI Evaluators**
- Business name: **Lightweight GenAI Evaluators**
- Why it matters:
  - mostly `GenAI`
  - mostly `Evaluator`
  - lighter-touch version of `active_5`

### `active_3`
- Descriptive name: **GenAI Community Learners**
- Business name: **GenAI Community Participants**
- Why it matters:
  - community-led rather than webinar-led
  - `forum_contribution` is the clearest differentiator

### `active_1`
- Descriptive name: **High-Effort GenAI Learning Evaluators**
- Business name: **High-Intent GenAI Evaluators**
- Why it matters:
  - training-led GenAI evaluator segment
  - more intense version of the evaluator / learning pattern

### `active_4`
- Descriptive name: **Webinar-Led GenAI Evaluators**
- Business name: **Event-Driven GenAI Evaluators**
- Why it matters:
  - strongest webinar-led active segment
  - useful for content / event journey targeting

### `active_0`
- Descriptive name: **CUDA Builder-Downloaders**
- Business name: **Core CUDA Builders**
- Why it matters:
  - strongest builder-shaped active cluster
  - clear CUDA + builder + download pattern

## Cooling

### `cooling_1`
- Descriptive name: **Cooling GenAI Learners**
- Business name: **Cooling GenAI Education Users**
- Why it matters:
  - very pure GenAI learner cluster
  - high-effort history but weak current visible asset breadth

### `cooling_noise`
- Descriptive name: **Mixed Cooling Download Generalists**
- Business name: **Cooling Multi-Path Users**
- Why it matters:
  - broadest cooling catch-all
  - strongest mixed-persona download-centered cooling group

### `cooling_6`
- Descriptive name: **Cooling GenAI Training Learners**
- Business name: **Cooling GenAI Training Users**
- Why it matters:
  - training-heavy GenAI learners
  - one of the clearest “education audience losing momentum” clusters

### `cooling_4`
- Descriptive name: **Cooling Mixed-Persona Training Users**
- Business name: **Cooling Cross-Persona Learners**
- Why it matters:
  - more mixed than the purer GenAI or CUDA learner groups
  - still meaningfully training-led

### `cooling_5`
- Descriptive name: **Cooling CUDA Learners**
- Business name: **Cooling CUDA Education Users**
- Why it matters:
  - simple CUDA learner segment
  - low-activity but still identifiable

### `cooling_2`
- Descriptive name: **Cooling Mixed Learners**
- Business name: **Cooling General Learning Users**
- Why it matters:
  - balanced learner group
  - useful mid-spectrum cluster between the pure persona groups

### `cooling_0`
- Descriptive name: **Cooling CUDA Community Learners**
- Business name: **Cooling CUDA Community Users**
- Why it matters:
  - CUDA learner segment with clearer community flavor

### `cooling_3`
- Descriptive name: **Cooling High-Effort GenAI Learners**
- Business name: **Cooling High-Intent GenAI Users**
- Why it matters:
  - very concentrated GenAI learner cluster
  - strong sign of formerly serious engagement

## At Risk

### `at_risk_0`
- Descriptive name: **At-Risk CUDA/GenAI Learners**
- Business name: **At-Risk Technical Learners**
- Why it matters:
  - biggest at-risk segment
  - technical learning behavior is still visible, but current continuation is weak

### `at_risk_5`
- Descriptive name: **Broad At-Risk Learning Builders**
- Business name: **At-Risk Builder-Learners**
- Why it matters:
  - most mixed and potentially recoverable at-risk cluster
  - some builder residue still remains

### `at_risk_2`
- Descriptive name: **At-Risk GenAI Training Learners**
- Business name: **At-Risk GenAI Training Users**
- Why it matters:
  - clear GenAI training audience that did not sustain

### `at_risk_3`
- Descriptive name: **At-Risk GenAI Workshop Learners**
- Business name: **At-Risk GenAI Hands-On Learners**
- Why it matters:
  - more hands-on than `at_risk_2`
  - stronger bug / workshop flavor

### `at_risk_1`
- Descriptive name: **At-Risk CUDA Learners**
- Business name: **At-Risk CUDA Education Users**
- Why it matters:
  - narrow CUDA technical learning segment

### `at_risk_4`
- Descriptive name: **At-Risk Webinar Learners**
- Business name: **At-Risk Event-Led Learners**
- Why it matters:
  - clearest event / webinar-led at-risk cohort

### `at_risk_noise`
- Descriptive name: **Mixed At-Risk Download Generalists**
- Business name: **At-Risk Multi-Path Users**
- Why it matters:
  - mixed backlog segment
  - less coherent than the named at-risk clusters

## Short Takeaways

- The `active` population is not one thing. It splits sharply between:
  - **CUDA builders**
  - **GenAI evaluators / learners**
- The `cooling` population is mostly an **education audience in decline**.
- The `at-risk` population is mostly a **former education audience with weak current continuation**.
- If you want the cleanest high-level narrative:
  - `Active` = current builders and evaluators
  - `Cooling` = learners losing momentum
  - `At Risk` = former learners and light builders close to churn
