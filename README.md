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
