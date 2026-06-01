# NVIDIA Developer Engagement A/B Pipeline README

## Purpose

This project is organized as two related pipelines.

**Pipeline A** is the full current-project pipeline. It rebuilds the database, cleans the data, creates developer features, discovers clusters with HDBSCAN, runs GMM/HMM analysis, and trains the saved LightGBM labeler.

**Pipeline B** is the production-style new-data scoring pipeline. It takes a new raw data batch in the same format, applies the same load/clean/feature logic, creates `dev_profile_new_incoming_v1`, and uses the saved LightGBM labeler to assign developers into the existing HDBSCAN-derived cluster framework.

Pipeline B does **not** rerun HDBSCAN and does **not** change the cluster definitions.

---

## Required Data Folder

The current notebooks read raw files from a folder named:

```text
Data/
```

The shell scripts also accept lowercase `data/`. If `data/` exists and `Data/` does not, the scripts create a `Data -> data` symlink so the original notebook paths still work.

Place the raw NVIDIA files in `Data/` using the names currently referenced by `1A_Create_DuckDB.ipynb` / `1B_Load_New_Raw_Data_To_DuckDB.ipynb`, for example:

```text
Data/DEVPM_8674_Cal_Poly_Export_dev_activity.csv
Data/DEVPM_8674_Cal_Poly_Export_dev_contact.csv
Data/DEVPM_8674_Cal_Poly_Export_sdk_download.csv
Data/DEVPM_8674_Cal_Poly_Export_dev_contact_supplement.csv
Data/Activity_Score_Mapping_filled.xlsx
```

Do not move the files elsewhere unless you also update the notebook file paths.

---

## Folder Structure

```text
project_root/
├── Data/
├── Pipeline_A/
│   ├── 1A_Create_DuckDB.ipynb
│   ├── 2A_Clean_Data.ipynb
│   ├── 3A_Feature_Engineering.ipynb
│   ├── 4A_HDBSCAN_Clustering.ipynb
│   ├── 5A_GMM_Cluster_Validation.ipynb
│   ├── 6A_HMM_Journey_Modeling.ipynb
│   ├── 7A_Supervised_Labeling_LGBM_XGB.ipynb
│   └── 8A_Train_Saved_LGBM_Labeler.ipynb
├── Pipeline_B/
│   ├── 1B_Load_New_Raw_Data_To_DuckDB.ipynb
│   ├── 2B_Clean_New_Data.ipynb
│   ├── 3B_Feature_Engineering_New_Data.ipynb
│   ├── 4B_Score_New_Data_Fixed_Clusters.ipynb
│   └── 0B_OPTIONAL_Create_Sample_New_Incoming_Profile.ipynb
├── run_pipeline_A_full_reclustering.sh
├── run_pipeline_B_new_data_fixed_cluster_scoring.sh
├── requirements_pipeline.txt
└── developer_project.duckdb
```

---

## Pipeline A: Full Current Project / Reclustering

Run Pipeline A when you need to rebuild or refresh the full project.

```bash
bash run_pipeline_A_full_reclustering.sh
```

Execution order:

| Step | Notebook | Purpose | Main output |
|---:|---|---|---|
| 1A | `Pipeline_A/1A_Create_DuckDB.ipynb` | Load raw NVIDIA files into DuckDB | Raw and initial clean tables |
| 2A | `Pipeline_A/2A_Clean_Data.ipynb` | Clean contacts, activities, SDK downloads | `contact_final`, `activity_final`, `sdk_download_final` |
| 3A | `Pipeline_A/3A_Feature_Engineering.ipynb` | Create developer-level features | `dev_profile_final_v4` |
| 4A | `Pipeline_A/4A_HDBSCAN_Clustering.ipynb` | Main lifecycle-aware clustering | `dev_lifecycle_cluster_membership_v11_final` |
| 5A | `Pipeline_A/5A_GMM_Cluster_Validation.ipynb` | GMM validation / benchmark | `dev_gmm_stratified_clusters_v1`, `dev_gmm_weekly_clusters_v1` |
| 6A | `Pipeline_A/6A_HMM_Journey_Modeling.ipynb` | Journey sequence modeling | HMM state / transition outputs |
| 7A | `Pipeline_A/7A_Supervised_Labeling_LGBM_XGB.ipynb` | Supervised reproduction of cluster labels | `dev_supervised_cluster_membership_v1_*` |
| 8A | `Pipeline_A/8A_Train_Saved_LGBM_Labeler.ipynb` | Save production LightGBM labelers | `supervised_cluster_labeler_artifacts_v1/` |

Use Pipeline A when:

- the full project needs to be rerun,
- you receive a major data refresh,
- the schema changes,
- feature definitions change,
- new sources or new behavior patterns appear,
- the business wants a new segmentation refresh.

---

## Pipeline B: New Incoming Data / Fixed-Cluster Scoring

Run Pipeline B when a new raw data batch arrives in the same format and you want to assign developers into the existing cluster framework.

```bash
bash run_pipeline_B_new_data_fixed_cluster_scoring.sh
```

Execution order:

| Step | Notebook | Purpose | Main output |
|---:|---|---|---|
| 1B | `Pipeline_B/1B_Load_New_Raw_Data_To_DuckDB.ipynb` | Load the new raw batch | Raw and initial clean tables for the batch |
| 2B | `Pipeline_B/2B_Clean_New_Data.ipynb` | Apply the same cleaning logic | `contact_final`, `activity_final`, `sdk_download_final` |
| 3B | `Pipeline_B/3B_Feature_Engineering_New_Data.ipynb` | Apply the same feature engineering logic | `dev_profile_final_v4`, `dev_profile_new_incoming_v1` |
| 4B | `Pipeline_B/4B_Score_New_Data_Fixed_Clusters.ipynb` | Score new developers with saved LightGBM labelers | `dev_new_developer_cluster_scores_v1` |

Pipeline B uses the same current feature engineering logic. The only B-specific addition is an adapter at the end of `3B_Feature_Engineering_New_Data.ipynb` that copies the feature output to:

```text
dev_profile_new_incoming_v1
```

and adds a normalized `stratum` column for the saved labeler.

---

## Why Save the LightGBM Model?

Yes, save the trained model before scoring new developers.

HDBSCAN is the discovery model. It defines the original cluster structure.

LightGBM is the assignment model. It learns the mapping from developer features to the fixed HDBSCAN cluster labels and can be reused on future batches.

Saved artifacts are written by `8A_Train_Saved_LGBM_Labeler.ipynb` to:

```text
supervised_cluster_labeler_artifacts_v1/
├── cluster_labeler_lgbm_active.joblib
├── cluster_labeler_lgbm_cooling.joblib
├── cluster_labeler_lgbm_at_risk.joblib
└── cluster_labeler_metadata.json
```

Pipeline B requires this folder to exist.

---

## What Stayed the Same

The original concepts and modeling logic are preserved:

- cleaning stays in Step 2,
- developer-level feature creation stays in Step 3,
- HDBSCAN remains the main final segmentation model,
- dormant and unactivated users remain rule/rule-carry-forward groups,
- GMM remains validation/benchmarking,
- HMM remains journey analysis,
- LightGBM is used for future fixed-cluster assignment.

The A notebooks from 1A through 7A are renamed copies of the original notebooks. Pipeline B reuses the same 1/2/3 logic and then adds only the minimum scoring adapter needed to create the expected new-data table.

---

## Main Tables and Artifacts

| Output | Created by | Meaning |
|---|---|---|
| `developer_project.duckdb` | 1A / 1B | Main DuckDB database |
| `contact_final` | 2A / 2B | Cleaned contacts |
| `activity_final` | 2A / 2B | Cleaned activities |
| `sdk_download_final` | 2A / 2B | Cleaned SDK downloads |
| `dev_profile_final_v4` | 3A / 3B | Main developer-level feature table |
| `dev_lifecycle_cluster_membership_v11_final` | 4A | Final HDBSCAN cluster membership |
| `dev_gmm_stratified_clusters_v1` | 5A | GMM validation clusters |
| HMM state / transition outputs | 6A | Developer journey movement |
| `supervised_cluster_labeler_artifacts_v1/` | 8A | Saved LightGBM scoring artifacts |
| `dev_profile_new_incoming_v1` | 3B | New incoming batch feature table for scoring |
| `dev_new_developer_cluster_scores_v1` | 4B | New developer fixed-cluster predictions |

---

## When to Retrain vs. Only Score

Use Pipeline B for normal weekly/monthly scoring when the incoming raw data has the same schema and behavior is still similar.

Use Pipeline A when there is a major refresh or structural change.

Retrain the saved LightGBM labeler when:

- feature definitions change,
- cluster labels change,
- model accuracy drops,
- prediction confidence is consistently low,
- the incoming population distribution shifts noticeably.

Rerun HDBSCAN when:

- new data sources are added,
- the engagement ecosystem changes substantially,
- new meaningful cluster types appear,
- stakeholders want a new segmentation framework.

---

## Optional Sample Test for Pipeline B

If there is no real future batch yet, you can test the scorer using:

```text
Pipeline_B/0B_OPTIONAL_Create_Sample_New_Incoming_Profile.ipynb
```

This samples from `dev_profile_final_v4` and creates `dev_profile_new_incoming_v1`. It is only for testing and is not part of the default production B script.

---

## Install Requirements

```bash
pip install duckdb pandas numpy scikit-learn matplotlib seaborn jupyter nbconvert hdbscan hmmlearn lightgbm xgboost joblib pyarrow openpyxl
```
