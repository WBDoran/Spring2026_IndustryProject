# NVIDIA Developer Engagement Analytics Project

## Project Summary

This project builds a repeatable analytics framework for NVIDIA developer engagement data. The goal is to move from raw activity, contact, and SDK download records into business-ready insights about developer cohorts, lifecycle status, engagement depth, journey movement, asset impact, and future cluster assignment.

The project is organized around two production-style workflows:

1. **Pipeline A: Full Reclustering / Model Development**
   - Used for the full project build, major refreshes, HDBSCAN reclustering, GMM validation, HMM journey modeling, and supervised model training.

2. **Pipeline B: New Incoming Data / Fixed-Cluster Scoring**
   - Used when new raw data arrives in the same format and the team wants to assign developers into the existing HDBSCAN-derived cluster framework without reclustering.

The project uses **DuckDB** as the local analytics database and saves the main modeling outputs back into DuckDB tables and model artifact folders.

---

## Business Objective

NVIDIA's core question for this project is:

> How do we ensure developer engagement efforts translate into meaningful technology adoption rather than only higher interaction counts?

This project supports that question through four main deliverables:

- **Developer cohort profiles:** identify distinct developer engagement patterns.
- **Asset impact analysis:** connect trainings, webinars, downloads, and other assets to later behavior.
- **Data enrichment plan:** document data gaps and future sources that could improve the developer view.
- **Repeatable framework:** create a pipeline that can be rerun or used for future scoring.

---

## Recommended Repository Structure

Place this README at the project root.

```text
NVIDIA_Developer_Engagement_Project/
|
|-- README.md
|-- PIPELINE_README.md
|-- PIPELINE_AB_INTEGRITY_MANIFEST.md
|-- requirements_pipeline.txt
|
|-- run_pipeline_A_full_reclustering.sh
|-- run_pipeline_B_new_data_fixed_cluster_scoring.sh
|
|-- Data/                         # raw NVIDIA data files go here
|   |-- contacts.csv or .xlsx
|   |-- activities.csv or .xlsx
|   |-- sdk_downloads.csv or .xlsx
|   |-- data_dictionary.xlsx
|   `-- supporting lookup files
|
|-- Pipeline_A/
|   |-- 1A_Create_DuckDB.ipynb
|   |-- 2A_Clean_Data.ipynb
|   |-- 3A_Feature_Engineering.ipynb
|   |-- 4A_HDBSCAN_Clustering.ipynb
|   |-- 5A_GMM_Cluster_Validation.ipynb
|   |-- 6A_HMM_Journey_Modeling.ipynb
|   |-- 7A_Supervised_Labeling_LGBM_XGB.ipynb
|   `-- 8A_Train_Saved_LGBM_Labeler.ipynb
|
|-- Pipeline_B/
|   |-- 0B_OPTIONAL_Create_Sample_New_Incoming_Profile.ipynb
|   |-- 1B_Load_New_Raw_Data_To_DuckDB.ipynb
|   |-- 2B_Clean_New_Data.ipynb
|   |-- 3B_Feature_Engineering_New_Data.ipynb
|   `-- 4B_Score_New_Data_Fixed_Clusters.ipynb
|
|-- developer_project.duckdb       # created by the pipeline
|-- supervised_cluster_labeler_artifacts_v1/
|-- executed_notebooks_pipeline_A/
`-- executed_notebooks_pipeline_B/
```

### Data folder requirement

Create a folder named **Data/** in the project root and place the raw NVIDIA source files inside it before running either pipeline.

Lowercase **data/** is also acceptable if the shell scripts are used, because the scripts create a `Data -> data` symlink when needed. The notebooks currently expect the capitalized `Data/` path.

Raw data should not be committed to a public repository.

---

## Environment Setup

Install Python dependencies before running the notebooks.

```bash
pip install -r requirements_pipeline.txt
```

If the requirements file is unavailable, install the main packages manually:

```bash
pip install duckdb pandas numpy scikit-learn matplotlib seaborn jupyter nbconvert hdbscan hmmlearn lightgbm xgboost joblib pyarrow openpyxl
```

Optional virtual environment setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_pipeline.txt
```

---

## Pipeline A: Full Reclustering / Model Development

Use Pipeline A when rebuilding the complete project from raw data or refreshing the segmentation framework.

### Run command

```bash
bash run_pipeline_A_full_reclustering.sh
```

### Notebook order

```text
Pipeline_A/1A_Create_DuckDB.ipynb
Pipeline_A/2A_Clean_Data.ipynb
Pipeline_A/3A_Feature_Engineering.ipynb
Pipeline_A/4A_HDBSCAN_Clustering.ipynb
Pipeline_A/5A_GMM_Cluster_Validation.ipynb
Pipeline_A/6A_HMM_Journey_Modeling.ipynb
Pipeline_A/7A_Supervised_Labeling_LGBM_XGB.ipynb
Pipeline_A/8A_Train_Saved_LGBM_Labeler.ipynb
```

### What Pipeline A does

1. Loads raw NVIDIA files into DuckDB.
2. Cleans contacts, activities, SDK downloads, and supporting tables.
3. Builds the main developer-level feature table.
4. Runs lifecycle-aware HDBSCAN clustering.
5. Keeps dormant or unactivated users as interpretable rule-based groups when appropriate.
6. Runs GMM as a benchmark or validation clustering layer.
7. Builds HMM journey states and transition outputs.
8. Trains and saves LightGBM/XGBoost-style supervised labelers so future developers can be assigned to the fixed cluster framework.

### Key Pipeline A outputs

```text
developer_project.duckdb
dev_profile_final_v4
dev_lifecycle_cluster_membership_v11_final
dev_gmm_stratified_clusters_v1
dev_gmm_weekly_clusters_v1
supervised_cluster_labeler_artifacts_v1/
executed_notebooks_pipeline_A/
```

---

## Pipeline B: New Incoming Data / Fixed-Cluster Scoring

Use Pipeline B when a new raw batch arrives in the same general format as the original raw data. Pipeline B should score new developers into the existing cluster framework without rerunning HDBSCAN.

### Required before running Pipeline B

Pipeline A must be run at least once through the saved model step so this folder exists:

```text
supervised_cluster_labeler_artifacts_v1/
```

That folder stores the trained LightGBM labeler artifacts used for fixed-cluster scoring.

### Run command

```bash
bash run_pipeline_B_new_data_fixed_cluster_scoring.sh
```

### Notebook order

```text
Pipeline_B/1B_Load_New_Raw_Data_To_DuckDB.ipynb
Pipeline_B/2B_Clean_New_Data.ipynb
Pipeline_B/3B_Feature_Engineering_New_Data.ipynb
Pipeline_B/4B_Score_New_Data_Fixed_Clusters.ipynb
```

Optional testing notebook:

```text
Pipeline_B/0B_OPTIONAL_Create_Sample_New_Incoming_Profile.ipynb
```

### What Pipeline B does

1. Loads a new raw data batch.
2. Applies the same cleaning concepts used in Pipeline A.
3. Applies the same feature engineering concepts used in Pipeline A.
4. Creates the new-data feature table.
5. Loads the saved LightGBM labeler artifacts.
6. Scores new developers into the existing HDBSCAN-derived cluster framework.

### Key Pipeline B outputs

```text
dev_profile_new_incoming_v1
dev_new_developer_cluster_scores_v1
executed_notebooks_pipeline_B/
```

---

## Modeling Logic

### HDBSCAN is the final discovery model

HDBSCAN is used to discover the primary developer clusters because developer engagement behavior is not expected to form clean spherical groups. HDBSCAN can find irregular clusters and leave ambiguous users as noise or rule-based cases.

### Rule-based lifecycle groups should remain interpretable

Dormant and unactivated developers should not always be forced into behavioral clusters. Their most important feature is often inactivity or lack of meaningful engagement, so clear business rules are easier to explain and maintain.

### GMM is a validation layer

GMM helps compare whether broad engagement patterns are visible under a different clustering assumption. It should not replace HDBSCAN as the final segmentation unless the team intentionally changes the modeling strategy.

### HMM is a journey layer

HMM is used to understand movement over time, not to replace developer clustering. It helps explain how developers transition between states such as discovery, learning, building, cooling, and dormant behavior.

### LightGBM is the production assignment layer

The trained LightGBM model should be saved after Pipeline A and reused in Pipeline B. HDBSCAN discovers clusters; LightGBM assigns future developers into those existing clusters.

For normal new incoming data:

```text
New raw data -> cleaning -> feature engineering -> saved LightGBM scorer -> fixed cluster assignment
```

Do not rerun HDBSCAN for every new batch unless there is a strong reason to refresh the segmentation.

---

## When to Use Each Pipeline

| Scenario | Recommended Pipeline |
|---|---|
| Initial project build | Pipeline A |
| Final class/project presentation refresh | Pipeline A |
| Major schema change | Pipeline A |
| New activity source added | Pipeline A |
| Major behavioral distribution shift | Pipeline A |
| Weekly or monthly new raw data batch | Pipeline B |
| Dashboard scoring refresh | Pipeline B |
| Assign new developers to existing clusters | Pipeline B |
| Test scoring on a sample from existing data | Pipeline B optional sample notebook |

---

## Retraining Policy

### Use saved LightGBM without reclustering when:

- new data has the same columns and meaning,
- business definitions are unchanged,
- cluster names and lifecycle rules are unchanged,
- model confidence is stable,
- dashboard users want continuity over time.

### Retrain LightGBM when:

- feature definitions change,
- cluster labels are renamed or consolidated,
- model accuracy drops,
- prediction confidence becomes consistently low,
- the new batch has a noticeably different distribution but the team still wants the same cluster framework.

### Rerun HDBSCAN and refresh the full segmentation when:

- new data sources are added,
- engagement behavior changes substantially,
- the business wants a new segmentation,
- old clusters no longer explain developer behavior,
- the feature engineering framework changes substantially.

---

## Main Tables and Artifacts

| Output | Description |
|---|---|
| `developer_project.duckdb` | Main local DuckDB database |
| `dev_profile_final_v4` | Main developer-level feature table for the current project |
| `dev_lifecycle_cluster_membership_v11_final` | Final lifecycle-aware HDBSCAN cluster membership output |
| `dev_gmm_stratified_clusters_v1` | GMM benchmark clustering output |
| `dev_gmm_weekly_clusters_v1` | Weekly GMM behavior cluster output |
| HMM state and transition outputs | Journey movement and transition analysis |
| `supervised_cluster_labeler_artifacts_v1/` | Saved LightGBM model artifacts for future scoring |
| `dev_profile_new_incoming_v1` | New-data developer feature table for Pipeline B |
| `dev_new_developer_cluster_scores_v1` | Scored new developers assigned to fixed clusters |

---

## Suggested Dashboard Outputs

A business-facing dashboard can be built from the final tables and should include:

- developer count by lifecycle segment,
- cluster size and cluster profile summaries,
- high-depth engagement clusters,
- dormant or cooling-risk developers,
- asset engagement before and after key activities,
- SDK download patterns by cluster,
- journey state transitions,
- predicted cluster assignments for new developers,
- prediction confidence or review flags.

---

## Data Stewardship Notes

This project uses developer engagement data and should be handled carefully.

Recommended practices:

- keep raw data in the local `Data/` folder only,
- do not commit raw data or personally identifiable data to public repos,
- share only aggregate results in presentations,
- avoid exposing individual developer records unless explicitly approved,
- document all transformations that affect lifecycle or cluster interpretation,
- preserve the trained model artifacts with versioned dates when handing off the project.

---

## Troubleshooting

### Missing Data folder

Create the folder and add raw data files:

```bash
mkdir Data
```

Then place the raw NVIDIA files inside it.

### Pipeline B fails because model artifacts are missing

Run Pipeline A first through the final saved scorer notebook:

```bash
bash run_pipeline_A_full_reclustering.sh
```

Then rerun Pipeline B.

### `stratum` column missing in new data

The scoring notebook is designed to derive `stratum` from available lifecycle fields such as `lifecycle_status`, `dormancy_status`, `final_lifecycle_status`, or lifecycle flags. If all lifecycle indicators are missing, rerun the feature engineering step or inspect the new-data feature table.

### DuckDB table missing

Open DuckDB and check available tables:

```bash
duckdb developer_project.duckdb
SHOW TABLES;
```

Common required tables include:

```text
contact_final
activity_final
sdk_download_final
dev_profile_final_v4
dev_lifecycle_cluster_membership_v11_final
dev_profile_new_incoming_v1
```

---

## One-Sentence Project Story

This project converts NVIDIA developer engagement records into a repeatable segmentation and scoring framework that identifies meaningful technology adoption patterns, explains developer journeys, and supports future scoring without reclustering every new data batch.
