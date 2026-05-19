# Asset Impact Analysis README

## Purpose

`AssetImpact_Analysis.ipynb` answers the business question: **which NVIDIA assets drive meaningful engagement?**

It evaluates trainings, webinars, downloads, SDK activity, forums, and APIs against developer engagement outcomes using the feature tables from `FeatureEngineering_v3.ipynb` and the GMM cluster assignments from `GMM_Cluster.ipynb`.

## Required Run Order

1. Run `FeatureEngineering_v3.ipynb`.
2. Run `GMM_Cluster.ipynb`.
3. Run `AssetImpact_Analysis.ipynb`.

The asset notebook expects these DuckDB tables:

- `activity_labeled_v2`
- `dev_profile_final_v4`
- `dev_gmm_clusters_v1`

Optional tables:

- `dev_gmm_weekly_clusters_v1` for weekly cohort movement.
- `sdk_download_final` or `sdk_download_clean` for global SDK product demand.

## Method

The notebook creates first-touch cohorts for six asset families:

- `training`
- `webinar`
- `sdk_download`
- `download`
- `forum`
- `api`

For each developer and asset family, it compares the 90 days before first asset touch with the 90 days after first asset touch. The asset day itself is excluded from pre/post windows so the triggering event is not counted as lift.

The main engagement outcomes are:

- Activity count delta.
- Activity score delta.
- Build and champion activity delta.
- High-effort activity delta.
- Meaningful engagement delta.
- Journey-stage progression rate.
- Post-touch build/champion rate.
- 31-90 day retention rate.
- Shallow no-lift rate.

## Output Tables

The notebook writes these DuckDB tables:

- `asset_first_touch_v1`: first observed asset touch by developer and asset type.
- `asset_pre_post_developer_v1`: developer-level pre/post metrics.
- `asset_pre_post_summary_v1`: asset-level summary report.
- `asset_cluster_profile_v1`: asset usage and lift by GMM cluster.
- `asset_weekly_cluster_movement_v1`: developer-level weekly GMM movement, if weekly clusters exist.
- `asset_weekly_cluster_movement_summary_v1`: asset-level weekly cluster transition summary, if weekly clusters exist.
- `sdk_download_product_summary_v1`: global SDK product demand summary, if SDK tables exist.
- `sdk_download_monthly_top_products_v1`: monthly trend for top SDK products, if SDK tables exist.

It also exports compact CSVs and a markdown report into:

```text
asset_impact_outputs/
```

## Interpretation Guidance

Assets with high `avg_meaningful_count_delta`, high `progressed_stage_rate`, and high `post_build_or_champion_rate` are the strongest candidates for meaningful engagement drivers.

Assets with high touch volume but high `shallow_no_lift_rate` are more likely awareness or low-intent engagement signals.

Cluster findings should be read as associations. If an asset is concentrated in a strong GMM cohort but has low pre/post lift, it may be used mostly by developers who were already engaged. If an asset shows lift in weaker or early-stage cohorts, it may be a stronger progression lever.

SDK product tables are global demand signals unless the SDK table contains a developer identifier. Developer-level SDK impact is measured through `activity_labeled_v2` as the `sdk_download` asset type.

## Caveat

This analysis is observational, not causal. It measures association around first asset touch. A causal read would require a controlled design, matching, or a stronger quasi-experimental setup.
