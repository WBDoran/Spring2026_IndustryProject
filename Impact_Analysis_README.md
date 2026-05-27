# Impact Analysis README

This file explains how to run [Cluster_Asset_Impact_Analysis_Pipeline.ipynb](/C:/Users/mason/Spring2026_IndustryProject/Cluster_Asset_Impact_Analysis_Pipeline.ipynb) and the HDBSCAN-specific version [Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb](/C:/Users/mason/Spring2026_IndustryProject/Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb).

## Important Note

When running the HDBSCAN specific version of the pipeline there is an important step that changes the cluster numbers to be ranked by their size. For example if active_3 was the largest active cluster the pipeline converts this cluster into active_0, then the second largest active cluster would be active_1. This is done for the active, cooling, and at_risk clusters.

## Purpose

The pipeline notebook does two things in one run:

1. Standardizes a model-specific cluster output table into a reusable cluster-membership table.
2. Runs the downstream cluster asset impact analysis on that standardized membership table.

The goal is to let the same downstream impact analysis work across different clustering models, as long as the model output can be mapped to a developer id and cluster id.

## What You Need Before Running

- `developer_project.duckdb` must exist.
- `dev_profile_final_v4` must already exist in DuckDB.
- A model-specific cluster output table must already exist in DuckDB.

Examples of possible source cluster tables:

- `dev_gmm_clusters_v1`
- an HMM developer-level cluster rollup table
- a K-means developer cluster table

## Source Table Requirements

The source cluster table must have:

- one row per developer
- a developer id column
- a cluster id column

It may also have:

- a human-readable cluster label column

Minimum required source schema:

- `developer_id`
- `some_cluster_id_column`

Optional:

- `some_cluster_label_column`

## Notebook To Run

Open and run:

- [Cluster_Asset_Impact_Analysis_Pipeline.ipynb]

For the HDBSCAN v11 workflow, open and run:

- [Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb]

## Parameter Setup

In the parameter cell, set:

- `SOURCE_TABLE`: the model-specific cluster output table
- `OUTPUT_TABLE`: the standardized membership table this pipeline will create
- `ID_COL`: the developer id column in the source table
- `CLUSTER_ID_COL`: the cluster id column in the source table
- `CLUSTER_LABEL_COL`: the label column in the source table, or `None` if no label exists

Example for GMM:

```python
SOURCE_TABLE = 'dev_gmm_clusters_v1'
OUTPUT_TABLE = 'cluster_membership_gmm_v1'

ID_COL = 'developer_id'
CLUSTER_ID_COL = 'gmm_cluster_id'
CLUSTER_LABEL_COL = 'gmm_cluster_label'
```

If the source table has no label column:

```python
CLUSTER_LABEL_COL = None
```

In that case, the notebook creates labels as:

- `cluster_0`
- `cluster_1`
- `cluster_2`

and so on.

## HDBSCAN v11 Run Path

If you are running the HDBSCAN workflow from Nav's v11 final membership data:

1. Export or save the NAV HDBSCAN final membership snapshot in your data folder as `Data/dev_lifecycle_cluster_membership_v11_final.parquet`.
2. Open [Cluster_Asset_Impact_Analysis_Pipeline_hdbscan.ipynb]
3. The parameter cell is already wired to:
   - `SOURCE_TABLE = 'Data/dev_lifecycle_cluster_membership_v11_final.parquet'`
   - `CLUSTER_ID_COL = 'cluster_key'`
   - `CLUSTER_LABEL_COL = None`
   - `REMAP_HDBSCAN_BY_SIZE = True`
4. With `REMAP_HDBSCAN_BY_SIZE = True`, the notebook standardizes `active`, `cooling`, and `at_risk` cluster numbers by descending cluster size:
   - largest non-noise cluster becomes `_0`
   - second-largest becomes `_1`
   - and so on
   - `*_noise`, `Dormant_*`, and `unactivated` are left unchanged
5. In the normal case, just run the notebook top to bottom without changing those defaults.

## What The Pipeline Does

### Step 1: Validate Inputs

The notebook checks:

- the source table exists
- the profile table exists
- the required source columns exist

It also previews:

- source table columns
- source sample rows
- source cluster counts preview

### Step 2: Standardize Cluster Membership

The notebook creates a standardized output table with exactly:

- `developer_id`
- `cluster_id`
- `cluster_label`

This is the standardization layer that makes the downstream analysis reusable across models.

For the HDBSCAN parquet workflow, this step also standardizes the cluster numbering for `active`, `cooling`, and `at_risk` by descending cluster size so the labels are more stable and easier to interpret across reruns and exports.

### Step 3: Validate Standardized Output

The notebook then previews:

- row count
- null checks
- output sample rows
- output cluster counts

### Step 4: Run Asset Impact Analysis

After standardization, the notebook:

- joins standardized cluster membership back to `dev_profile_final_v4`
- builds the cluster profile base table
- creates the long asset table
- builds summary, exposure, outcomes, intensity, and ranking tables
- renders cluster-level and per-asset visualizations

## Main Output Tables

The standardized handoff table:

- `OUTPUT_TABLE`

Typical downstream analysis tables:

- `cluster_profile_asset_base_v2`
- `cluster_asset_catalog_v2`
- `cluster_asset_long_v2`
- `cluster_asset_summary_v2`
- `cluster_asset_exposure_by_cluster_v2`
- `cluster_asset_outcomes_exposed_v2`
- `cluster_asset_intensity_by_cluster_v2`
- `cluster_asset_exposed_profile_v2`
- `cluster_asset_priority_by_cluster_v2`
- `cluster_persona_profile_v2`
- `cluster_journey_profile_v2`
- `cluster_journey_state_profile_v2`
- `cluster_lifecycle_profile_v2`
- `cluster_dormancy_profile_v2`
- `cluster_effort_profile_v2`
- `cluster_recent_activity_debug_v2`

## Expected Runtime Notes

Some steps can take a while, especially:

- building the base cluster-profile table
- building the long asset table
- cluster size / summary aggregation steps

This is expected because the notebook is working across a large developer population and multiple derived tables.

The expensive parts are mostly:

- joining cluster membership to a wide developer profile table
- expanding one developer row into many asset/signal rows
- aggregating those long tables multiple times

## Common Failure Modes

### Missing source table

Cause:

- the clustering notebook has not been run yet
- `SOURCE_TABLE` is set to the wrong table name

### Missing source columns

Cause:

- `ID_COL` or `CLUSTER_ID_COL` is mapped incorrectly

### Missing label column

Cause:

- `CLUSTER_LABEL_COL` is set to a column that does not exist

Fix:

- set `CLUSTER_LABEL_COL = None` if the source table does not have labels

### Multiple rows per developer in the source table

Cause:

- the source table is not yet a developer-level cluster assignment table

Fix:

- create a developer-level rollup first
- then run the pipeline notebook

## When This Pipeline Will Work

This pipeline should work for any clustering model if the source table can be reduced to:

- one row per developer
- one chosen cluster id per developer
- optional cluster label per developer

It is not limited to GMM.

## Recommended Run Order

1. Run the clustering notebook.
2. Confirm the cluster output table exists in DuckDB.
3. Open the pipeline notebook.
4. Set the source-to-standardized mappings in the parameter cell.
5. Run the notebook from top to bottom.
6. Review the standardized output preview.
7. Review the downstream summary tables and visualizations.

## Quick Sanity Checks

After standardization, these should be true:

- `developer_id` is present
- `cluster_id` is present
- `cluster_label` is present
- row count looks reasonable
- cluster counts look reasonable

If those checks pass, the downstream impact analysis should be using the standardized table correctly.
