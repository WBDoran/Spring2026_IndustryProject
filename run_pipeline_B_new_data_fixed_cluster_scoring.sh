#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
KERNEL_NAME="${KERNEL_NAME:-python3}"
cd "$PROJECT_DIR"

ensure_data_dir () {
  if [ ! -d "Data" ] && [ -d "data" ]; then
    echo "Found data/ but notebooks expect Data/. Creating Data -> data symlink."
    ln -s data Data
  fi
  if [ ! -d "Data" ]; then
    echo "ERROR: Missing Data/ folder. Put the raw NVIDIA data files in Data/."
    echo "       Lowercase data/ is also accepted; the script will create a Data symlink."
    exit 1
  fi
}

run_notebook () {
  local notebook="$1"
  local output_root="$2"
  local notebook_dir
  local notebook_base
  notebook_dir="$(dirname "$notebook")"
  notebook_base="$(basename "$notebook")"

  echo "============================================================"
  echo "Running: $notebook"
  echo "============================================================"

  if [ ! -f "$notebook" ]; then
    echo "ERROR: Notebook not found: $notebook"
    exit 1
  fi

  mkdir -p "$output_root/$notebook_dir"

  jupyter nbconvert \
    --to notebook \
    --execute "$notebook" \
    --output "$notebook_base" \
    --output-dir "$output_root/$notebook_dir" \
    --ExecutePreprocessor.kernel_name="$KERNEL_NAME" \
    --ExecutePreprocessor.timeout=-1
}

# ============================================================
# Pipeline B: New Incoming Data / Fixed-Cluster Scoring
# ============================================================
# Runs the same raw-data load, cleaning, and feature engineering logic
# for a new incoming batch, then scores developers into the existing
# HDBSCAN-derived cluster framework using saved LightGBM artifacts.
# This does NOT rerun HDBSCAN.
# ============================================================

OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_DIR}/executed_notebooks_pipeline_B}"
ensure_data_dir

if [ ! -d "supervised_cluster_labeler_artifacts_v1" ]; then
  echo "ERROR: Missing supervised_cluster_labeler_artifacts_v1/."
  echo "       Run Pipeline A through 8A first to save the LightGBM labeler artifacts."
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

NOTEBOOKS=(
  "Pipeline_B/1B_Load_New_Raw_Data_To_DuckDB.ipynb"
  "Pipeline_B/2B_Clean_New_Data.ipynb"
  "Pipeline_B/3B_Feature_Engineering_New_Data.ipynb"
  "Pipeline_B/4B_Score_New_Data_Fixed_Clusters.ipynb"
)

for nb in "${NOTEBOOKS[@]}"; do
  run_notebook "$nb" "$OUTPUT_DIR"
done

echo "============================================================"
echo "Pipeline B completed successfully."
echo "Executed notebooks saved to: $OUTPUT_DIR"
echo "Scored table expected in DuckDB: dev_new_developer_cluster_scores_v1"
echo "============================================================"
