# HDBSCAN Final Analysis

This file is the narrative analysis layer for the HDBSCAN workflow. It is meant to be read after running:

1. [Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb](/C:/Users/mason/Spring2026_IndustryProject/Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb)
2. [HDBSCAN_Extra_Analysis.ipynb](/C:/Users/mason/Spring2026_IndustryProject/HDBSCAN_Extra_Analysis.ipynb)

It combines:

- the richer cluster interpretation from [hdbscan_cluster_prelim_analysis.md](/C:/Users/mason/Spring2026_IndustryProject/hdbscan_cluster_prelim_analysis.md)
- the lifecycle-group and asset-audience tables produced by the HDBSCAN pipeline
- the visual cluster interpretation from the visualization section of [Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb](/C:/Users/mason/Spring2026_IndustryProject/Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb)

## How To Use This File

Use this file as the main written readout. The notebooks remain the place where tables are generated and inspected. This file is where the analysis is synthesized into:

- lifecycle-group interpretation
- cluster-level interpretation
- asset-centered interpretation
- recommendation-building directions for NVIDIA developer programs

Every section below points back to where the analysis came from.

## Source Map

### Lifecycle-group analysis

Built from:

- `cluster_group_rollup_summary_v2`
- `cluster_group_asset_profile_v2`
- `cluster_group_composition_summary_v2`

Use this when answering:

- what `active`, `cooling`, and `at_risk` look like overall
- which assets characterize each lifecycle group
- what kind of developers are concentrated in each lifecycle group

### Cluster-level analysis

Built from:

- `cluster_top_persona_summary_v2`
- `cluster_top_asset_summary_v2`
- `cluster_correlation_summary_v2`
- the visualization section of [Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb](/C:/Users/mason/Spring2026_IndustryProject/Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb)
- [hdbscan_cluster_prelim_analysis.md](/C:/Users/mason/Spring2026_IndustryProject/hdbscan_cluster_prelim_analysis.md)

Use this when answering:

- what each cluster is
- what makes one cluster different from another
- which clusters look builder-led, training-led, webinar-led, community-led, or mixed

### Asset-centered analysis

Built from:

- `asset_audience_summary_v2`

Use this when answering:

- what kind of audience each asset tends to attract
- whether an asset skews toward `active`, `cooling`, or `at_risk`
- whether an asset skews toward builders, learners, or high-effort users



## Run Context

This analysis assumes the HDBSCAN pipeline has already completed through the visualization section and written its summary tables to DuckDB.

Recommended run order:

1. Run [Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb](/C:/Users/mason/Spring2026_IndustryProject/Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb) through completion.
2. Run [HDBSCAN_Extra_Analysis.ipynb](/C:/Users/mason/Spring2026_IndustryProject/HDBSCAN_Extra_Analysis.ipynb) to inspect the summary tables.
3. Use this file as the written interpretation layer.

## Biggest Differences Between Active, Cooling, And At-Risk

Built from:

- `cluster_group_rollup_summary_v2`
- `cluster_group_asset_profile_v2`
- `cluster_group_composition_summary_v2`
- [hdbscan_cluster_prelim_analysis.md](/C:/Users/mason/Spring2026_IndustryProject/hdbscan_cluster_prelim_analysis.md)
- pipeline visualizations

### Active

`Active` is the clearest current-intent population. It is less uniformly asset-led than `cooling` or `at_risk`, which means it is not best understood as simply a heavier content or download audience. It splits mainly between:

- `GenAI` evaluator / learning behavior
- `CUDA` builder / downloader behavior

The biggest internal difference is whether a user looks like a:

- current evaluator
- current learner with community engagement
- current builder

### Cooling

`Cooling` is still mostly a live education audience, but one with weakening momentum. It is much more learner-dominated than `active`. The main variation is across:

- `GenAI` learners
- `CUDA` learners
- mixed learner groups with training, downloads, and some community behavior

### At-Risk

`At-risk` looks like a former education / technical learning audience that is closer to churn. It is still learner-heavy, but less live than `cooling`. The strongest differences are between:

- broad technical learners
- `GenAI` training-led learners
- `CUDA` learners
- event-led learners

### Where They Differ Most

The cleanest synthesis across the lifecycle-group tables and the prelim analysis is:

- `Active` still shows people doing something now: evaluating, learning, or building.
- `Cooling` still looks reachable because the education pattern is present, but fading.
- `At-risk` looks more decayed: prior interest is visible, but current continuation is weaker.

The lifecycle asset profile reinforces this by showing that `cooling` and `at_risk` are more consistently training-, webinar-, and download-associated than `active` overall. That does not mean `active` lacks those patterns. It means `active` as a full population is less dominated by them than the other two groups.

## Lifecycle-Group Interpretation

Built from:

- `cluster_group_asset_profile_v2`
- `cluster_group_composition_summary_v2`
- pipeline visualizations

### Active

Interpret `active` as the group where current behavior matters more than simple asset exposure. If `active` appears lower on some asset share columns than `cooling` or `at_risk`, that should not be read as “active does less of everything.” It should be read as:

- `active` is less uniformly concentrated in these specific assets
- parts of `active` are likely more builder- or evaluator-shaped than broad education-shaped
- the active population is more mixed in how it expresses engagement

### Cooling

Interpret `cooling` as the strongest “education audience with declining momentum” group. This is the most natural place to look for:

- training-led users who may still be reachable
- webinar-led users who have not fully disengaged
- mixed learner groups that still retain visible content or download association

### At-Risk

Interpret `at_risk` as a former education / technical learning audience whose prior interest is still visible in assets, but whose continuation is weaker. The key caution here is:

- more training or more webinar exposure alone should not automatically be assumed to solve the problem
- the stronger pattern is that these users already touched educational assets and still moved closer to churn

## Cluster Reference

Built from:

- [hdbscan_cluster_prelim_analysis.md](/C:/Users/mason/Spring2026_IndustryProject/hdbscan_cluster_prelim_analysis.md)
- `cluster_correlation_summary_v2`
- pipeline visualizations

The following reference should be used when you need richer, more stable cluster names and “why it matters” summaries.

### Active

`active_0` | **GenAI Evaluation Cohort**

- strongest `GenAI` + `Evaluator` pattern
- centered on `webinar`, `dli_training`, and `devzone_download`
- clearest large-scale evaluation-without-building segment

`active_noise` | **Active Multi-Path Users**

- most mixed active segment
- broader persona and journey mix
- catch-all active population that does not fit one clean behavior type

`active_1` | **Lightweight GenAI Evaluators**

- mostly `GenAI`
- mostly `Evaluator`
- lighter-touch version of `active_0`

`active_2` | **GenAI Community Participants**

- community-led rather than webinar-led
- `forum_contribution` is the clearest differentiator

`active_3` | **High-Intent GenAI Evaluators**

- training-led `GenAI` evaluator segment
- more intense version of the evaluator / learning pattern

`active_4` | **Event-Driven GenAI Evaluators**

- strongest webinar-led active segment
- useful for content / event journey targeting

`active_5` | **Core CUDA Builders**

- strongest builder-shaped active cluster
- clearest `CUDA` + builder + download pattern

### Cooling

`cooling_0` | **Cooling GenAI Education Users**

- very pure `GenAI` learner cluster
- high-effort history but weak current visible asset breadth

`cooling_noise` | **Cooling Multi-Path Users**

- broadest cooling catch-all
- strongest mixed-persona download-centered cooling group

`cooling_1` | **Cooling GenAI Training Users**

- training-heavy `GenAI` learners
- clearest education audience losing momentum segment

`cooling_2` | **Cooling Cross-Persona Learners**

- more mixed than the purer `GenAI` or `CUDA` learner groups
- still meaningfully training-led

`cooling_3` | **Cooling CUDA Education Users**

- simple `CUDA` learner segment
- low-activity but still identifiable

`cooling_4` | **Cooling General Learning Users**

- balanced learner group
- useful mid-spectrum cluster between the pure persona groups

`cooling_5` | **Cooling CUDA Community Users**

- `CUDA` learner segment with clearer community flavor

`cooling_6` | **Cooling High-Intent GenAI Users**

- very concentrated `GenAI` learner cluster
- strong sign of formerly serious engagement

### At-Risk

`at_risk_0` | **At-Risk Technical Learners**

- biggest at-risk segment
- technical learning behavior is still visible, but current continuation is weak

`at_risk_1` | **At-Risk Builder-Learners**

- most mixed and potentially recoverable at-risk cluster
- some builder residue still remains

`at_risk_2` | **At-Risk GenAI Training Users**

- clear `GenAI` training audience that did not sustain

`at_risk_3` | **At-Risk GenAI Hands-On Learners**

- more hands-on than `at_risk_2`
- stronger bug / workshop flavor

`at_risk_4` | **At-Risk CUDA Education Users**

- narrow `CUDA` technical learning segment

`at_risk_5` | **At-Risk Event-Led Learners**

- clearest event / webinar-led at-risk cohort

`at_risk_noise` | **At-Risk Multi-Path Users**

- mixed backlog segment
- less coherent than the named at-risk clusters

## How To Analyze Individual Clusters

Built from:

- `cluster_top_persona_summary_v2`
- `cluster_top_asset_summary_v2`
- `cluster_correlation_summary_v2`
- pipeline visualizations
- prelim cluster reference above

Use this workflow:

1. Start with `cluster_correlation_summary_v2`.
   Read the dominant persona, dominant journey, dominant effort, and top assets.
2. Compare that cluster to the richer cluster description in the prelim reference.
3. Check the pipeline visualization section when you need confidence that the cluster really looks:
   - builder-led
   - webinar-led
   - training-led
   - community-led
   - mixed / residual
4. Only then write the narrative interpretation.

Good cluster-level analysis should answer:

- who dominates this cluster
- what kind of behavior stage dominates this cluster
- what asset pattern shows up most clearly
- whether it looks actionable or too mixed to target cleanly

## How To Analyze Clusters As A Whole

Built from:

- `cluster_group_rollup_summary_v2`
- `cluster_group_asset_profile_v2`
- `cluster_group_composition_summary_v2`
- the full cluster inventory in the prelim reference

Use this workflow:

1. Start with lifecycle-group rollups for `active`, `cooling`, and `at_risk`.
2. Use cluster-level summaries to see which concrete clusters explain each group’s overall pattern.
3. Use the prelim reference to decide whether the story is mainly:
   - builder-led
   - evaluator-led
   - learner-led
   - community-led
   - download-heavy / mixed

This prevents the common mistake of treating a lifecycle group as if it were a single coherent audience when it is actually a weighted mix of clusters.

## Asset-Centered Analysis

Built from:

- `asset_audience_summary_v2`

This is the cleanest place to answer:

- what audience does `webinar` map to
- what audience does `dli_training` map to
- what audience do downloads map to
- which assets skew toward builders, learners, or high-effort users

This section is especially useful because it reverses the direction of the question:

- not “what assets are in `active`?”
- but “what kind of audience tends to touch this asset?”

Use this to avoid over-reading broad assets that everyone touches. If an asset has a large audience but still maps mostly to `cooling` or `at_risk`, that should shape how NVIDIA interprets that program motion.


## Recommendation-Building Directions For NVIDIA Developer Programs

Built from:

- `cluster_group_asset_profile_v2`
- `cluster_group_composition_summary_v2`
- `asset_audience_summary_v2`
- `cluster_correlation_summary_v2`
- pipeline visualizations
- prelim cluster reference

These recommendations should be framed as segment-fit guidance, not causal claims.

### 1. Lifecycle-group recommendations

Use:

- `cluster_group_asset_profile_v2`
- `cluster_group_composition_summary_v2`

Questions:

- which lifecycle group is most asset-led
- which lifecycle group is most learner-heavy
- which lifecycle group is most builder-heavy
- which lifecycle group looks reachable versus already decayed

Interpretation path:

- `Active`: likely needs depth, builder support, and higher-value hands-on motions rather than broad education blasts
- `Cooling`: likely best target for structured re-engagement through the asset types it already associates with
- `At-risk`: likely needs narrower recovery plays and more selective treatment

### 2. Cluster-level recommendations

Use:

- `cluster_correlation_summary_v2`
- prelim cluster reference
- pipeline visuals

Questions:

- which clusters are clean enough to target
- which clusters are too mixed
- which clusters are training-led versus builder-led versus event-led

Interpretation path:

- `Active` builder clusters: advanced technical content, project pathways, product adoption motions
- `Active` evaluator clusters: convert education and evaluation into hands-on next steps
- `Cooling` learner clusters: use guided re-engagement journeys
- `At-risk` training or webinar clusters: do not assume more of the same top-of-funnel asset is enough

### 3. Asset recommendations

Use:

- `asset_audience_summary_v2`

Questions:

- what kind of audience does each asset tend to attract
- whether an asset is mostly learner-heavy, active-heavy, or at-risk-heavy
- whether an asset skews toward high-effort users

Interpretation path:

- if an asset mostly maps to learners in `cooling` or `at_risk`, NVIDIA should treat it as a top- or mid-funnel program motion rather than proof of durable developer depth
- if an asset maps more strongly to builders or high-effort active users, it may be a better candidate for deepening engagement

### 4. Visual confirmation before recommendation

Use:

- the visualization section of [Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb](/C:/Users/mason/Spring2026_IndustryProject/Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb)

Before writing a recommendation like:

- “this is a webinar-led audience”
- “this is a training-heavy cluster”
- “this is a builder cluster”

check the visual panel for that cluster first. The visuals are the fastest way to confirm whether the numeric story is actually the dominant visual story.

## Practical Next Steps For NVIDIA

These are not final recommendations. They are the next analytical directions that fit the current evidence.

### Strengthen current-intent users

Focus on:

- `active` builder and evaluator clusters

Likely motions:

- advanced technical programming
- project-based hands-on content
- builder challenges
- deeper product / ecosystem adoption support

### Re-engage fading education users

Focus on:

- `cooling` learner clusters

Likely motions:

- structured post-training journeys
- webinar follow-up paths
- community nudges for the clusters with community residue

### Selectively recover at-risk users

Focus on:

- the clearest `at_risk` subsegments, especially those with some remaining coherence

Likely motions:

- narrow recovery plays tied to prior interest area
- more concrete next-step actions rather than broad repeated education

### Avoid over-reading broad assets

Downloads and other broad assets can dominate raw volume. Use the asset-audience and lifecycle-group composition views before concluding that a broad asset should drive strategy.

## Final Summary

The cleanest narrative across the pipeline outputs, the extra-analysis notebook, and the prelim cluster writeup is:

- `Active` = current builders and evaluators with less uniform dependence on broad education assets
- `Cooling` = learners losing momentum but still reachable through structured education-linked journeys
- `At-risk` = former learners and light builders whose prior interest is still visible, but whose continuation is weaker

The best way to build decisions from here is:

1. start with lifecycle-group rollups
2. drill into the cluster summaries and prelim cluster reference
3. use asset-audience views to avoid over-reading top-volume assets
4. confirm strong claims against the cluster visuals
5. write recommendations as segment-fit guidance, not as causal proof
