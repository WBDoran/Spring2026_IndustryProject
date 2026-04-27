# Git Workflow for This Project

This guide explains how to use Git for this project from start to finish.

---

## 1. Clone the Repository

```bash
git clone <repo-url>
cd Spring2026_IndustryProject
```

---

## 2. Add Your Data

Create a `Data/` folder if it does not exist:

(If you want to use CLI

```bash
mkdir -p Data
```

Place your 3 CSV files inside:

(too lazy to copy paste the full name
```
Data/
├── activity.csv
├── contact.csv
├── sdk_download.csv
```

Note:

* These files are ignored by `.gitignore`
* They will NOT be uploaded to GitHub

---

## 3. Do Your Work

You can now:

* Run scripts
* Work on notebooks
* Perform EDA
* Build features and models

---

## 4. Create Your Branch *(First Time Only)*

Before making changes, create your own branch:

```bash
git checkout -b your_name
```

Example (This is mine s dont use the same name!!):

```bash
git checkout -b Nav
```

---

## 5. Add Your Changes

Check what changed:

```bash
git status
```

Add files:

```bash
git add .
```

---

## 6. Commit Your Work

```bash
git commit -m "Some Message -- will show on github"
```

---

## 7. Push Your Branch (First Time Only)

```bash
git push --set-upstream origin your_name
```

Example:

```bash
git push --set-upstream origin Nav
```

---

## 8. After First Push (Normal Workflow)

From now on, use:

```bash
git add .
git commit -m "your message"
git push
```

---

## 9. Daily Workflow

Then after making changes:

```bash
git add .
git commit -m "what you did"
git push
```

---

## 10. Important Rules

Do NOT push:

* CSV files
* DuckDB database files (`.duckdb`, `.tmp`, `.wal`)
* Raw data folders

Only push:

* `.py` files
* `.ipynb` notebooks
* `README.md`
* `project_log.md`
* `requirements.txt`

---

## 11. Quick Summary

### First time:

```bash
git clone <repo>
cd project
git checkout -b your_name
git add .
git commit -m "message"
git push --set-upstream origin your_name
```

### After that:

```bash
git branch # To check if you are in your branch
git add .
git commit -m "message"
git push
```


---

## 12. Cloning and Working on an Existing Branch

If you already created your branch earlier and are setting up the project on a new machine, follow these steps:

### Step 1: Clone the Repository

```bash
git clone <repo-url>
cd Spring2026_IndustryProject
```

### Step 2: Fetch All Branches

```bash
git fetch --all
```

### Step 3: Checkout Your Existing Branch

```bash
git checkout your_name
```

If you do not see your branch locally, run:

```bash
git checkout -b your_name origin/your_name
```

This links your local branch to the remote branch.

---

## 13. Good Commit Message Examples

Use clear and meaningful messages:

Good:

* "added data preprocessing script"
* "fixed bug in feature engineering"
* "updated EDA notebook with visualizations"

Bad:

* "stuff"
* "update"
* "idk"

---

## 14. Common Mistakes to Avoid

* Working directly on main branch
* Forgetting to pull latest changes
* Pushing large or ignored files
* Using unclear commit messages
* Overwriting someone else's work

---

## 15. Final Tips

* Commit often, but keep commits meaningful
* Pull before you start working
* Push after you finish working
* Keep your branch clean and organized
* Ask before merging into main

---

## 16. Full Workflow Recap

### New Machine Setup:

```bash
git clone <repo>
cd project
git fetch --all
git checkout your_name
```

### Daily Work:

```bash
git checkout main
git pull
git checkout your_name
git merge main

git add .
git commit -m "message"
git push
```

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
