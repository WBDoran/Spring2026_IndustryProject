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

## Output Summary

| File / Table | Description |
|---|---|
| `developer_project.duckdb` | Central database — all raw, clean, and final tables |
| `Data/activity_sample.csv` | 100k activity rows |
| `Data/contact_sample.csv` | 100k contact rows |
| `Data/sdk_download_sample.csv` | 100k SDK download rows |
| `Data/developer_clusters.csv` | All developers with assigned tier label |

---
