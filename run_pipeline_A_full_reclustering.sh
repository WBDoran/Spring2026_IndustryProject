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
# Pipeline A: Full Project / Reclustering / Model Training
# ============================================================
# Runs the current project pipeline from raw data through HDBSCAN,
# GMM validation, HMM journey modeling, supervised labeling, and
# saved LightGBM labeler training.
# ============================================================

OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_DIR}/executed_notebooks_pipeline_A}"
ensure_data_dir
mkdir -p "$OUTPUT_DIR"

NOTEBOOKS=(
  "Pipeline_A/1A_Create_DuckDB.ipynb"
  "Pipeline_A/2A_Clean_Data.ipynb"
  "Pipeline_A/3A_Feature_Engineering.ipynb"
  "Pipeline_A/4A_HDBSCAN_Clustering.ipynb"
  "Pipeline_A/5A_GMM_Cluster_Validation.ipynb"
  "Pipeline_A/6A_HMM_Journey_Modeling.ipynb"
  "Pipeline_A/7A_Supervised_Labeling_LGBM_XGB.ipynb"
  "Pipeline_A/8A_Train_Saved_LGBM_Labeler.ipynb"
)

for nb in "${NOTEBOOKS[@]}"; do
  run_notebook "$nb" "$OUTPUT_DIR"
done

echo "============================================================"
echo "Pipeline A completed successfully."
echo "Executed notebooks saved to: $OUTPUT_DIR"
echo "Saved scorer artifacts expected in: supervised_cluster_labeler_artifacts_v1/"
echo "============================================================"
