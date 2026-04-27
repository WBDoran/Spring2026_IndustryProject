---

# Data Pipeline Workflow

This section explains how to run the full data processing and analysis pipeline.

---

## Prerequisites

**Python environment:** Use the Anaconda environment (`anaconda3`). The following packages are required:

```
duckdb
pandas
numpy
scikit-learn
matplotlib
```

**Jupyter kernel:** Make sure your notebook kernel is set to the Anaconda Python, not the system Python. In VS Code, select the kernel from the top-right of the notebook.

---

## Required Data Files

Place the following files inside the `Data/` folder before running any notebooks. These are not tracked by Git.

```
Data/
├── activity.csv               (pipe-delimited |)
├── contact.csv
├── contact-addition.csv
├── sdk.csv
├── Activity_Score_Mapping.csv
```

---

## Notebook Execution Order

Run the notebooks in the following sequence. Each notebook depends on the outputs of the one before it.

### Step 1 — `Creating_duckDB.ipynb`
Loads the raw CSV files into `developer_project.duckdb` and applies basic type casting.

**Outputs:** `activity_raw`, `activity_clean`, `contact_raw`, `contact_clean`, `sdk_download_raw`, `sdk_download_clean`

---

### Step 2 — `EDA_DuckDB.ipynb`
Exploratory data analysis. Documents data quality issues (nulls, duplicates, outliers) across all three tables.

**Outputs:** Charts and summary statistics (no new tables written).

---

### Step 3 — `Cleaning_Final.ipynb`
Full cleaning pipeline. Merges `contact-addition.csv` into contacts, applies the activity score mapping, deduplicates all tables, and creates 100k random samples.

**Outputs:**
- `contact_final` — cleaned developer profiles (contact + supplement)
- `activity_final` — cleaned engagement events with mapped scores
- `sdk_download_final` — cleaned SDK download records
- `activity_sample`, `contact_sample`, `sdk_download_sample` — 100k samples in DuckDB
- `Data/activity_sample.csv`, `Data/contact_sample.csv`, `Data/sdk_download_sample.csv`

> **Note:** If re-running this notebook, close any other notebooks connected to `developer_project.duckdb` first to avoid a file lock error.

---

### Step 4 — `CleanDataSanity.ipynb`
Validates data integrity before joining tables. Checks null join keys, duplicate developer IDs, unmatched activity rows, and join cardinality.

**Run after:** `Cleaning_Final.ipynb`

---

### Step 5 — `DeveloperClustering.ipynb`
Builds a 31-feature matrix per developer, scales it, and runs MiniBatchKMeans (k=4) to segment developers into four tiers.

| Tier | Description |
|------|-------------|
| Beginner | Low activity, mostly basic downloads, inactive or new |
| Experienced | Moderate activity, API/container/self-paced DLI usage |
| Advanced | High-value activities — instructor-led DLI, hackathons, presenter roles |
| Enterprise | Organization-linked, enterprise account type, WWFO-targeted |

**Outputs:**
- `developer_clusters` table in DuckDB
- `Data/developer_clusters.csv`

> **Note:** If re-running after edits, use **Kernel → Restart & Clear Output → Run All** and reload the file from disk first (File → Revert File in VS Code).

---

## DeveloperClustering.ipynb — Cell-by-Cell Breakdown

### Setup
Imports libraries (duckdb, pandas, numpy, sklearn, matplotlib) and connects to `developer_project.duckdb`. Defines all global constants in one place: `FEATURE_COLS` (the 31 feature names), `LOG_COLS` (columns to log-transform), `TIER_ORDER`, and `TIER_COLORS`.

---

### Section 1 — Feature Engineering

**Cell 1 — Activity aggregation (`dev_activity_features`)**
Reads `activity_final` and groups by developer. Produces 24 features per developer covering:
- Volume: total activities, cumulative score, average score, max score
- Learning: DLI course count, split into self-paced vs instructor-led
- Advanced technical usage: API calls, container/model/helm chart downloads, NGC downloads
- Community engagement: hackathon entries, forum posts, bugs filed, presenter role appearances
- Recency: days since last activity, total span of activity in days

**Cell 2 — Contact profile features (`dev_contact_features`)**
Reads `contact_final` and extracts 7 profile signals per developer:
- Binary flags for enterprise, university, and startup account type (handles mixed values like `Enterprise;University`)
- Whether the developer has a linked organizational account
- Whether they appear on the WWFO high-value target list
- Program tenure in days (since first application date)
- Breadth of declared development interests (count of semicolon-separated areas)

**Cell 3 — Feature join (`developer_features`)**
Left-joins the activity and contact tables on `developer_id`. Developers with no recorded activity receive 0 for all activity columns rather than being dropped. This ensures all 9.3M developers in `contact_final` are included in clustering.

---

### Section 2 — Preprocessing

**Cell 4 — Load to pandas**
Pulls `developer_features` from DuckDB into a pandas DataFrame. Runs a validation check that raises an error immediately if any expected feature column is missing.

**Cell 5 — Scale**
Applies `log1p` (log(x+1)) to all skewed count columns to reduce outlier influence — without this, one developer with 2M activities would dominate the clustering. Then applies `StandardScaler` so no single feature dominates by magnitude.

---

### Section 3 — Clustering

**Cell 6 — Elbow plot**
Runs MiniBatchKMeans for k=2 through k=8 on a 50k subsample and plots inertia (within-cluster variance) for each k. The "elbow" in the curve is where adding more clusters stops meaningfully reducing variance, visually confirming k=4 is appropriate.

**Cell 7 — Fit model**
Fits the final MiniBatchKMeans (k=4) on all 9.3M developers. Uses `MiniBatchKMeans` instead of standard KMeans because it processes data in batches of 50,000 rows at a time, making it feasible to cluster millions of developers without running out of memory.

**Cell 8 — Silhouette score**
Measures cluster separation quality on a 10k subsample. Score ranges from -1 to 1 — above 0.3 is reasonable, above 0.5 is strong. More reliable than the elbow plot alone.

---

### Section 4 — Cluster Labeling

**Cell 9 — Assign tier labels**
K-Means produces raw cluster IDs (0–3) with no built-in meaning. This cell:
1. Inverse-transforms the cluster centroids back to original feature scale for human inspection
2. Scores each cluster on orthogonal signals for each tier (e.g. enterprise = average rank on `is_enterprise`, `has_account`, `is_wwfo_targeted`)
3. Uses a greedy algorithm to assign one tier label per cluster — the cluster with the highest enterprise score gets labeled `enterprise`, then the process repeats for `advanced`, `experienced`, and `beginner` with no cluster reused
4. Maps those labels across all 9.3M developers

---

### Section 5 — Visualization

**Cell 10 — PCA scatter plot**
Compresses 31 features to 2 dimensions using PCA and plots 20k developers colored by tier. Dots close together share similar feature profiles. The % variance explained printed above the chart tells you how representative the 2D view is of the true 31D separation.

**Cell 11 — Feature bar charts**
Bar charts of mean values for 8 key features broken down by tier. Used to visually confirm labels make sense — e.g. advanced should have the highest DLI count, enterprise the highest `is_enterprise`, beginner the highest `days_since_last_activity`.

**Cell 12 — Summary table**
Full breakdown table showing developer count, % of total, and mean values of 14 key features per tier. Primary reference for communicating what distinguishes each segment.

**Cell 13 — Cluster interpretation**
Written descriptions of what each tier means in business terms and which engagement signals define them.

---

### Section 6 — Save Results

**Cell 14 — Save**
Writes `developer_id`, `cluster_id`, and `tier` for all 9.3M developers to the `developer_clusters` table in DuckDB and exports `Data/developer_clusters.csv`.

**Cell 15 — Spot-check**
Samples 3 developers from each tier and joins back to their feature values to confirm the labels look correct before closing the database connection.

---

## Output Summary

| File / Table | Description |
|---|---|
| `developer_project.duckdb` | Central database — all raw, clean, and final tables |
| `Data/activity_sample.csv` | 100k activity rows |
| `Data/contact_sample.csv` | 100k contact rows |
| `Data/sdk_download_sample.csv` | 100k SDK download rows |
| `Data/developer_clusters.csv` | All developers with assigned tier label |

---
