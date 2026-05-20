"""
Generates SupervisedModeling_LGBM_XGB.ipynb
Primary: LightGBM and XGBoost on full engineered features.
Validation/alternative: same models on PCA-reduced features.
"""
import json, uuid

def _id():
    return str(uuid.uuid4())[:8]

def md(text):
    lines = text.split("\n")
    src = [l + "\n" for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    return {"cell_type": "markdown", "id": _id(), "metadata": {}, "source": src}

def code(text):
    lines = text.split("\n")
    src = [l + "\n" for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": _id(),
        "metadata": {},
        "outputs": [],
        "source": src,
    }

cells = []

# ── Title ──────────────────────────────────────────────────────────────────
cells.append(md("""\
# NVIDIA Developer Journey — Supervised Modeling: LightGBM & XGBoost

**Goal:** Predict four 90-day developer outcomes using tree-based gradient boosting.
PCA-reduced features are run in parallel as a validation/alternative.

| Section | Contents |
|---------|----------|
| 0 | Setup & connection |
| 1 | Feature panel & outcome labels |
| 2 | Preprocessing & train / val / test split |
| 3 | PCA analysis (variance scree, component selection) |
| 4 | LightGBM — full features (4 outcome models) |
| 5 | XGBoost — full features (4 outcome models) |
| 6 | LightGBM & XGBoost — PCA features (validation) |
| 7 | Model comparison table (AUC, PR-AUC, Brier) |
| 8 | Feature importance (gain) |
| 9 | SHAP analysis |
| 10 | Calibration (reliability diagrams) |
| 11 | Score output (predicted probabilities per developer) |

**Outcome labels** (90-day horizon, cutoff-based):
- `retained_90d` — any activity after cutoff
- `deepened_90d` — Build/Champion signal or ≥ 20 % score growth
- `expanded_90d` — touched a new persona lane
- `churned_90d` — active pre-cutoff, zero post-cutoff"""))

# ── 0  Setup ────────────────────────────────────────────────────────────────
cells.append(md("## 0. Setup"))
cells.append(code("""\
import warnings
warnings.filterwarnings("ignore")

import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path

pd.set_option("display.max_columns", 60)
pd.set_option("display.float_format", "{:.4f}".format)

DB_PATH       = "developer_project.duckdb"
SAMPLE_PARQUET = "sample_dev_profile_final_v4.parquet"
RANDOM_STATE  = 42
np.random.seed(RANDOM_STATE)

if Path(DB_PATH).exists():
    con = duckdb.connect(DB_PATH, read_only=True)
    DATA_SOURCE = "duckdb"
    print(f"Connected to {DB_PATH}")
elif Path(SAMPLE_PARQUET).exists():
    con = duckdb.connect(":memory:")
    con.execute(
        "CREATE TABLE dev_profile_final_v4 AS SELECT * FROM read_parquet('"
        + SAMPLE_PARQUET + "')"
    )
    DATA_SOURCE = "parquet"
    print(f"Loaded sample parquet: {SAMPLE_PARQUET}")
else:
    raise FileNotFoundError(
        "Neither " + DB_PATH + " nor " + SAMPLE_PARQUET + " found. "
        "Run FeatureEngineering_v3.ipynb first."
    )"""))

# ── 1  Features & labels ─────────────────────────────────────────────────────
cells.append(md("## 1. Feature panel & outcome labels"))
cells.append(code("""\
df_raw = con.execute("SELECT * FROM dev_profile_final_v4").df()
print(f"dev_profile_final_v4: {len(df_raw):,} rows  |  {df_raw.shape[1]} columns")

# ── Numeric feature columns ────────────────────────────────────────────────
# Recency window features
RECENCY_FEATURES = [
    "activity_count_0_30d", "activity_count_30_90d", "activity_count_90_180d",
    "log_activity_count_0_30d", "log_activity_count_30_90d", "log_activity_count_90_180d",
    "has_activity_0_30d", "has_activity_30_90d", "has_activity_90_180d",
    "build_count_0_30d", "build_count_30_90d", "build_count_90_180d",
    "log_build_count_0_30d",
    "high_effort_count_0_30d", "high_effort_count_30_90d", "high_effort_count_90_180d",
    "unique_activity_days_0_30d", "unique_activity_types_0_30d", "unique_modalities_0_30d",
    "activity_per_active_day_0_30d", "build_share_0_30d", "high_effort_share_0_30d",
    "avg_effort_rank_0_30d", "avg_effort_rank_30_90d", "avg_effort_rank_90_180d",
    "total_confidence_weighted_effort_0_30d", "total_confidence_weighted_effort_30_90d",
    "confidence_weighted_effort_per_activity_0_30d",
    "avg_score_effort_gap_0_30d", "score_effort_misalignment_count_0_30d",
    "score_effort_misalignment_share_0_30d",
    "effort_x_activity_score_sum_0_30d",
    "activity_velocity_0_30_vs_30_90", "build_velocity_0_30_vs_30_90",
    "weighted_recent_activity", "weighted_recent_build", "weighted_recent_confidence_effort",
    "active_non_builder_0_30d", "newly_inactive_0_30d", "low_volume_builder_0_30d",
    "has_high_effort_0_30d", "recent_build_flag", "recent_champion_flag",
]

# Lifetime aggregate features (numeric only; user_type / max_stage handled below)
LIFETIME_FEATURES = [
    "lifetime_activity_count", "lifetime_activity_score_sum", "lifetime_activity_score_avg",
    "lifetime_unique_activity_days", "lifetime_unique_activity_types", "lifetime_unique_modalities",
    "lifetime_active_weeks",
    "lifetime_discover_count", "lifetime_learn_count", "lifetime_evaluate_count",
    "lifetime_build_count", "lifetime_champion_count",
    "lifetime_high_effort_count", "lifetime_avg_effort_rank", "lifetime_max_effort_rank",
    "lifetime_total_confidence_weighted_effort", "lifetime_avg_score_effort_gap",
    "lifetime_score_effort_misalignment_count", "lifetime_effort_x_activity_score_sum",
    "lifetime_dli_training_count", "lifetime_webinar_count", "lifetime_forum_count",
    "lifetime_bug_count", "lifetime_hackathon_count", "lifetime_api_count",
    "lifetime_devzone_download_count", "lifetime_ngc_download_count",
    "log_lifetime_activity_count", "log_lifetime_activity_score_sum",
    "log_lifetime_build_count", "log_lifetime_high_effort_count",
    "log_lifetime_total_confidence_weighted_effort", "log_lifetime_effort_x_activity_score_sum",
    "log_clipped_lifetime_activity_count_p99", "log_clipped_lifetime_activity_score_sum_p99",
    "log_clipped_lifetime_total_confidence_weighted_effort_p99",
    "log_clipped_lifetime_effort_x_activity_score_sum_p99",
    "effort_per_activity_lifetime", "score_effort_misalignment_share_lifetime",
    "activity_per_active_week_lifetime", "build_share_lifetime", "high_effort_share_lifetime",
    "has_lifetime_activity",
]

# Persona features
PERSONA_FEATURES = [
    "cuda_share", "genai_share", "robotics_share",
    "simulation_share", "learning_community_share",
    "persona_entropy", "mixed_persona_flag", "persona_confidence",
]

# Effort & journey state (numeric)
EFFORT_JOURNEY_FEATURES = [
    "developer_effort_score", "developer_effort_rank", "effort_recency_weight",
    "behavior_journey_rank_30d", "current_journey_rank_30d",
    "is_activated", "lifetime_meaningful_weeks", "days_since_last_meaningful_week",
    "days_since_last_activity",
    "dormant_flag", "at_risk_flag", "cooling_flag",
]

ALL_NUM_FEATURES = RECENCY_FEATURES + LIFETIME_FEATURES + PERSONA_FEATURES + EFFORT_JOURNEY_FEATURES

# Keep only columns that exist
NUM_FEATURES = [f for f in ALL_NUM_FEATURES if f in df_raw.columns]
print(f"Numeric features: {len(NUM_FEATURES)} / {len(ALL_NUM_FEATURES)} defined columns found")
missing = sorted(set(ALL_NUM_FEATURES) - set(df_raw.columns))
if missing:
    print(f"  Missing (skipped): {missing}")

# Ordinal-encode user_type and persona columns for tree models
CAT_COLS = ["user_type", "max_stage_reached", "developer_effort_level",
            "dormancy_status", "persona"]
USER_TYPE_MAP   = {"tourist": 0, "free_email_user": 1, "real_user": 2}
STAGE_MAP       = {"None": 0, "Discover": 1, "Learn": 2, "Evaluate": 3, "Build": 4, "Champion": 5}
EFFORT_MAP      = {"passive": 0, "low": 1, "moderate": 2, "high": 3, "very high": 4}
DORMANCY_MAP    = {"Unactivated": 0, "Dormant": 1, "At_Risk": 2, "Cooling": 3, "Active": 4}
PERSONA_ORD_MAP = {"Unknown": 0, "CUDA": 1, "GenAI": 2, "Robotics": 3,
                   "Simulation": 4, "Learning/Community": 5}

df = df_raw[["developer_id"] + NUM_FEATURES].copy()

for col, mapping in [
    ("user_type",              USER_TYPE_MAP),
    ("max_stage_reached",      STAGE_MAP),
    ("developer_effort_level", EFFORT_MAP),
    ("dormancy_status",        DORMANCY_MAP),
    ("persona",                PERSONA_ORD_MAP),
]:
    if col in df_raw.columns:
        df[col] = df_raw[col].map(mapping).fillna(0).astype(int)
        if col not in NUM_FEATURES:
            NUM_FEATURES.append(col)

print(f"Final feature count (including ordinal-encoded categoricals): {len(NUM_FEATURES)}")"""))

cells.append(code("""\
# ── Outcome labels ──────────────────────────────────────────────────────────
TARGETS = ["retained_90d", "deepened_90d", "expanded_90d", "churned_90d"]

if DATA_SOURCE == "duckdb":
    df_labels = con.execute(\"\"\"
    WITH max_dt AS (SELECT MAX(activity_date) AS anchor_date FROM activity_labeled_v2),
    cutoff AS (
        SELECT anchor_date - INTERVAL 90 DAY AS cutoff_date, anchor_date FROM max_dt
    ),
    pre AS (
        SELECT
            a.developer_id,
            COUNT(*)                                                                AS pre_count,
            SUM(a.activity_score)                                                   AS pre_score,
            MAX(CASE WHEN a.journey_signal IN ('Build','Champion') THEN 1 ELSE 0 END) AS pre_had_build,
            COUNT(DISTINCT
                CASE WHEN a.cuda_persona_score            > 0 THEN 'cuda'
                     WHEN a.genai_persona_score           > 0 THEN 'genai'
                     WHEN a.robotics_persona_score        > 0 THEN 'robotics'
                     WHEN a.simulation_persona_score      > 0 THEN 'simulation'
                     WHEN a.learning_community_persona_score > 0 THEN 'learning'
                END
            )                                                                       AS pre_lane_count
        FROM activity_labeled_v2 a, cutoff
        WHERE a.activity_date <= cutoff.cutoff_date
        GROUP BY a.developer_id
    ),
    post AS (
        SELECT
            a.developer_id,
            COUNT(*)                                                                AS post_count,
            SUM(a.activity_score)                                                   AS post_score,
            MAX(CASE WHEN a.journey_signal IN ('Build','Champion') THEN 1 ELSE 0 END) AS post_had_build,
            COUNT(DISTINCT
                CASE WHEN a.cuda_persona_score            > 0 THEN 'cuda'
                     WHEN a.genai_persona_score           > 0 THEN 'genai'
                     WHEN a.robotics_persona_score        > 0 THEN 'robotics'
                     WHEN a.simulation_persona_score      > 0 THEN 'simulation'
                     WHEN a.learning_community_persona_score > 0 THEN 'learning'
                END
            )                                                                       AS post_lane_count
        FROM activity_labeled_v2 a, cutoff
        WHERE a.activity_date > cutoff.cutoff_date
        GROUP BY a.developer_id
    )
    SELECT
        u.developer_id,
        CASE WHEN COALESCE(post.post_count, 0) > 0 THEN 1 ELSE 0 END              AS retained_90d,
        CASE
            WHEN COALESCE(post.post_had_build, 0) = 1 THEN 1
            WHEN COALESCE(post.post_score, 0) > COALESCE(pre.pre_score, 0) * 1.20
             AND COALESCE(post.post_count, 0) > 0                           THEN 1
            ELSE 0
        END                                                                         AS deepened_90d,
        CASE
            WHEN COALESCE(post.post_lane_count, 0) > COALESCE(pre.pre_lane_count, 0)
             AND COALESCE(post.post_count, 0) > 0                           THEN 1
            ELSE 0
        END                                                                         AS expanded_90d,
        CASE
            WHEN COALESCE(pre.pre_count,  0) > 0
             AND COALESCE(post.post_count, 0) = 0                           THEN 1
            ELSE 0
        END                                                                         AS churned_90d
    FROM developer_universe_v2 u
    LEFT JOIN pre  USING (developer_id)
    LEFT JOIN post USING (developer_id)
    \"\"\").df()
else:
    df_labels = pd.DataFrame({
        "developer_id": df_raw["developer_id"],
        "retained_90d": (df_raw.get("activity_count_0_30d", pd.Series(0, index=df_raw.index)) > 0).astype(int),
        "deepened_90d": (df_raw.get("build_count_0_30d",    pd.Series(0, index=df_raw.index)) > 0).astype(int),
        "expanded_90d": (df_raw.get("mixed_persona_flag",   pd.Series(0, index=df_raw.index)) == 1).astype(int),
        "churned_90d":  (
            (df_raw.get("activity_count_30_90d", pd.Series(0, index=df_raw.index)) > 0) &
            (df_raw.get("activity_count_0_30d",  pd.Series(0, index=df_raw.index)) == 0)
        ).astype(int),
    })

df = df.merge(df_labels, on="developer_id", how="left")
print("Label distribution:")
display(df[TARGETS].mean().rename("positive rate").to_frame().T)"""))

# ── 2  Preprocessing & split ─────────────────────────────────────────────────
cells.append(md("## 2. Preprocessing & train / val / test split"))
cells.append(code("""\
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

X_raw = df[NUM_FEATURES].copy()

# Replace inf values with NaN before imputing
X_raw.replace([np.inf, -np.inf], np.nan, inplace=True)

# Clip each column at its 99th percentile to suppress extreme outliers
for col in X_raw.columns:
    p99 = X_raw[col].quantile(0.99)
    if pd.notna(p99):
        X_raw[col] = X_raw[col].clip(upper=p99)

# Impute with column median
imputer = SimpleImputer(strategy="median")
X_imp   = imputer.fit_transform(X_raw)

# Scale (needed for PCA; tree models are scale-invariant but we keep one pipeline)
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X_imp)

X_full = pd.DataFrame(X_scaled, columns=NUM_FEATURES, index=df.index)
y      = df[TARGETS].fillna(0).astype(int)

# 70 / 15 / 15 split stratified on retained_90d
X_tr_val, X_test, y_tr_val, y_test = train_test_split(
    X_full, y, test_size=0.15, random_state=RANDOM_STATE, stratify=y["retained_90d"]
)
X_train, X_val, y_train, y_val = train_test_split(
    X_tr_val, y_tr_val, test_size=0.15 / 0.85,
    random_state=RANDOM_STATE, stratify=y_tr_val["retained_90d"]
)

print(f"Train: {len(X_train):,}  |  Val: {len(X_val):,}  |  Test: {len(X_test):,}")
print(f"Test positive rates:")
display(y_test.mean().rename("rate").to_frame().T)"""))

# ── 3  PCA ───────────────────────────────────────────────────────────────────
cells.append(md("""\
## 3. PCA analysis — variance scree & component selection

PCA is used as a validation alternative: if LightGBM / XGBoost on PCA features
performs nearly as well as on the full feature set, it suggests the signal is
concentrated in a lower-dimensional subspace and that the features carry
redundant information."""))

cells.append(code("""\
from sklearn.decomposition import PCA

# Fit PCA on training data only; transform all splits
pca_full = PCA(random_state=RANDOM_STATE)
pca_full.fit(X_train)

cumvar = np.cumsum(pca_full.explained_variance_ratio_)
n_90   = int(np.searchsorted(cumvar, 0.90)) + 1
n_95   = int(np.searchsorted(cumvar, 0.95)) + 1
n_99   = int(np.searchsorted(cumvar, 0.99)) + 1
print(f"Components to explain 90 % variance: {n_90}")
print(f"Components to explain 95 % variance: {n_95}")
print(f"Components to explain 99 % variance: {n_99}")

# Scree plot
fig, axes = plt.subplots(1, 2, figsize=(14, 4))

axes[0].plot(range(1, min(61, len(cumvar) + 1)),
             pca_full.explained_variance_ratio_[:60] * 100,
             marker="o", markersize=3, linewidth=1.2)
axes[0].set_title("Per-component explained variance (first 60)")
axes[0].set_xlabel("Component"); axes[0].set_ylabel("Variance explained (%)")

axes[1].plot(range(1, len(cumvar) + 1), cumvar * 100, linewidth=1.5)
for thresh, n_comp, col in [(90, n_90, "green"), (95, n_95, "orange"), (99, n_99, "red")]:
    axes[1].axhline(thresh, color=col, linestyle="--", alpha=0.7, label=f"{thresh}% @ {n_comp} PCs")
    axes[1].axvline(n_comp, color=col, linestyle=":", alpha=0.5)
axes[1].set_title("Cumulative explained variance")
axes[1].set_xlabel("Number of components"); axes[1].set_ylabel("Cumulative variance (%)")
axes[1].legend()

plt.tight_layout()
plt.show()

# Choose n_components = threshold that covers 95 % variance
N_PCA = n_95
print(f"Using {N_PCA} PCA components (95 % variance threshold)")"""))

cells.append(code("""\
# Fit final PCA with selected n_components
pca = PCA(n_components=N_PCA, random_state=RANDOM_STATE)
pca.fit(X_train)

X_train_pca = pca.transform(X_train)
X_val_pca   = pca.transform(X_val)
X_test_pca  = pca.transform(X_test)

pca_cols = [f"PC{i+1}" for i in range(N_PCA)]
print(f"PCA feature matrix: {X_train_pca.shape}  (train)")"""))

# ── 4  LightGBM — full features ───────────────────────────────────────────────
cells.append(md("""\
## 4. LightGBM — full features

One binary classifier per outcome label. `scale_pos_weight` handles class imbalance.
Evaluate on validation set; final metrics reported on held-out test set."""))

cells.append(code("""\
try:
    import lightgbm as lgb
except ImportError:
    raise ImportError("pip install lightgbm")

from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

def pos_weight(y_ser):
    n_neg = (y_ser == 0).sum()
    n_pos = (y_ser == 1).sum()
    return n_neg / max(n_pos, 1)

def eval_binary(model, X, y_true, label=""):
    prob = model.predict_proba(X)[:, 1]
    auc  = roc_auc_score(y_true, prob)
    ap   = average_precision_score(y_true, prob)
    brier = brier_score_loss(y_true, prob)
    if label:
        print(f"  {label:<14} AUC={auc:.4f}  PR-AUC={ap:.4f}  Brier={brier:.4f}")
    return {"auc": auc, "ap": ap, "brier": brier, "prob": prob}

LGB_PARAMS = dict(
    n_estimators    = 500,
    learning_rate   = 0.05,
    max_depth       = 6,
    num_leaves      = 63,
    min_child_samples = 50,
    subsample       = 0.8,
    colsample_bytree = 0.8,
    reg_alpha       = 0.1,
    reg_lambda      = 1.0,
    random_state    = RANDOM_STATE,
    n_jobs          = -1,
    verbosity       = -1,
)

lgb_models_full = {}
lgb_results_full = {}

print("LightGBM — full features")
print("-" * 55)
for tgt in TARGETS:
    spw = pos_weight(y_train[tgt])
    m = lgb.LGBMClassifier(scale_pos_weight=spw, **LGB_PARAMS)
    m.fit(
        X_train, y_train[tgt],
        eval_set=[(X_val, y_val[tgt])],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
    )
    lgb_models_full[tgt] = m
    lgb_results_full[tgt] = {
        "val":  eval_binary(m, X_val,  y_val[tgt],  f"{tgt} val"),
        "test": eval_binary(m, X_test, y_test[tgt], f"{tgt} test"),
    }

print("\\nBest iteration per target:")
for tgt, m in lgb_models_full.items():
    print(f"  {tgt}: {m.best_iteration_} trees")"""))

# ── 5  XGBoost — full features ────────────────────────────────────────────────
cells.append(md("## 5. XGBoost — full features"))
cells.append(code("""\
try:
    import xgboost as xgb
except ImportError:
    raise ImportError("pip install xgboost")

XGB_PARAMS = dict(
    n_estimators    = 500,
    learning_rate   = 0.05,
    max_depth       = 6,
    subsample       = 0.8,
    colsample_bytree = 0.8,
    reg_alpha       = 0.1,
    reg_lambda      = 1.0,
    eval_metric     = "auc",
    early_stopping_rounds = 50,
    use_label_encoder = False,
    random_state    = RANDOM_STATE,
    n_jobs          = -1,
    verbosity       = 0,
)

xgb_models_full = {}
xgb_results_full = {}

print("XGBoost — full features")
print("-" * 55)
for tgt in TARGETS:
    spw = pos_weight(y_train[tgt])
    m = xgb.XGBClassifier(scale_pos_weight=spw, **XGB_PARAMS)
    m.fit(
        X_train, y_train[tgt],
        eval_set=[(X_val, y_val[tgt])],
        verbose=False,
    )
    xgb_models_full[tgt] = m
    xgb_results_full[tgt] = {
        "val":  eval_binary(m, X_val,  y_val[tgt],  f"{tgt} val"),
        "test": eval_binary(m, X_test, y_test[tgt], f"{tgt} test"),
    }

print("\\nBest iteration per target:")
for tgt, m in xgb_models_full.items():
    print(f"  {tgt}: {m.best_iteration} trees")"""))

# ── 6  PCA validation ─────────────────────────────────────────────────────────
cells.append(md("""\
## 6. LightGBM & XGBoost — PCA features (validation/alternative)

Running the same models on `N_PCA` principal components.
If AUC is close (< 0.02 gap) to full-feature models, the engineered features
carry high redundancy and future pipelines may benefit from dimensionality reduction."""))

cells.append(code("""\
lgb_results_pca = {}
xgb_results_pca = {}

print(f"LightGBM — PCA ({N_PCA} components)")
print("-" * 55)
for tgt in TARGETS:
    spw = pos_weight(y_train[tgt])
    m = lgb.LGBMClassifier(scale_pos_weight=spw, **LGB_PARAMS)
    m.fit(
        X_train_pca, y_train[tgt],
        eval_set=[(X_val_pca, y_val[tgt])],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
    )
    lgb_results_pca[tgt] = {
        "val":  eval_binary(m, X_val_pca,  y_val[tgt],  f"{tgt} val"),
        "test": eval_binary(m, X_test_pca, y_test[tgt], f"{tgt} test"),
    }

print(f"\\nXGBoost — PCA ({N_PCA} components)")
print("-" * 55)
for tgt in TARGETS:
    spw = pos_weight(y_train[tgt])
    m = xgb.XGBClassifier(scale_pos_weight=spw, **XGB_PARAMS)
    m.fit(
        X_train_pca, y_train[tgt],
        eval_set=[(X_val_pca, y_val[tgt])],
        verbose=False,
    )
    xgb_results_pca[tgt] = {
        "val":  eval_binary(m, X_val_pca,  y_val[tgt],  f"{tgt} val"),
        "test": eval_binary(m, X_test_pca, y_test[tgt], f"{tgt} test"),
    }"""))

# ── 7  Comparison table ───────────────────────────────────────────────────────
cells.append(md("""\
## 7. Model comparison table (test-set metrics)

Rows = outcome labels. Columns = model × feature set.
`Δ AUC (full − PCA)` shows marginal value of using the full feature space."""))

cells.append(code("""\
rows = []
for tgt in TARGETS:
    lgb_f = lgb_results_full[tgt]["test"]
    xgb_f = xgb_results_full[tgt]["test"]
    lgb_p = lgb_results_pca[tgt]["test"]
    xgb_p = xgb_results_pca[tgt]["test"]
    rows.append({
        "target":           tgt,
        "LGB_full_AUC":     lgb_f["auc"],
        "XGB_full_AUC":     xgb_f["auc"],
        "LGB_PCA_AUC":      lgb_p["auc"],
        "XGB_PCA_AUC":      xgb_p["auc"],
        "LGB_full_PRAUC":   lgb_f["ap"],
        "XGB_full_PRAUC":   xgb_f["ap"],
        "LGB_full_Brier":   lgb_f["brier"],
        "XGB_full_Brier":   xgb_f["brier"],
        "Delta_AUC_LGB":    lgb_f["auc"] - lgb_p["auc"],
        "Delta_AUC_XGB":    xgb_f["auc"] - xgb_p["auc"],
    })

cmp_df = pd.DataFrame(rows).set_index("target")

def _style(v):
    if isinstance(v, float):
        if v > 0.02:
            return "color: green"
        if v < -0.01:
            return "color: red"
    return ""

display(
    cmp_df.style
    .format("{:.4f}")
    .applymap(_style, subset=["Delta_AUC_LGB", "Delta_AUC_XGB"])
    .set_caption("Test-set metrics: LightGBM & XGBoost — full features vs PCA")
)

print("\\nInterpretation:")
print("  Delta_AUC > 0.02 → full features add meaningful signal over PCA")
print("  Delta_AUC < 0.01 → PCA is a viable, lower-dimensional alternative")"""))

cells.append(code("""\
# Bar chart — AUC comparison across models and targets
fig, axes = plt.subplots(1, len(TARGETS), figsize=(16, 4), sharey=False)
model_labels = ["LGB\\nFull", "XGB\\nFull", "LGB\\nPCA", "XGB\\nPCA"]
colors       = ["#2196F3", "#1565C0", "#90CAF9", "#64B5F6"]

for ax, tgt in zip(axes, TARGETS):
    aucs = [
        lgb_results_full[tgt]["test"]["auc"],
        xgb_results_full[tgt]["test"]["auc"],
        lgb_results_pca [tgt]["test"]["auc"],
        xgb_results_pca [tgt]["test"]["auc"],
    ]
    bars = ax.bar(model_labels, aucs, color=colors, width=0.6, edgecolor="white")
    ax.set_ylim(max(0, min(aucs) - 0.05), 1.0)
    ax.set_title(tgt.replace("_", " "), fontsize=10)
    ax.set_ylabel("ROC-AUC" if ax == axes[0] else "")
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)
    for bar, auc in zip(bars, aucs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                f"{auc:.3f}", ha="center", va="bottom", fontsize=8)

plt.suptitle("ROC-AUC by model and feature set (test set)", y=1.02, fontsize=12)
plt.tight_layout()
plt.show()"""))

# ── 8  Feature importance ─────────────────────────────────────────────────────
cells.append(md("""\
## 8. Feature importance (gain)

LightGBM and XGBoost gain-based importance averaged across the four outcome models.
High-gain features are the most useful predictors across all four outcomes."""))

cells.append(code("""\
def get_lgb_importance(models, feat_names, top_n=25):
    imp_sum = np.zeros(len(feat_names))
    for m in models.values():
        imp_sum += m.feature_importances_
    imp_mean = imp_sum / len(models)
    s = pd.Series(imp_mean, index=feat_names).sort_values(ascending=False)
    return s.head(top_n)

def get_xgb_importance(models, feat_names, top_n=25):
    imp_sum = np.zeros(len(feat_names))
    for m in models.values():
        imp_sum += m.feature_importances_
    imp_mean = imp_sum / len(models)
    s = pd.Series(imp_mean, index=feat_names).sort_values(ascending=False)
    return s.head(top_n)

lgb_imp = get_lgb_importance(lgb_models_full, NUM_FEATURES)
xgb_imp = get_xgb_importance(xgb_models_full, NUM_FEATURES)

fig, axes = plt.subplots(1, 2, figsize=(16, 8))

for ax, imp, title in [
    (axes[0], lgb_imp, "LightGBM — Top 25 features (avg gain)"),
    (axes[1], xgb_imp, "XGBoost  — Top 25 features (avg gain)"),
]:
    ax.barh(imp.index[::-1], imp.values[::-1], color="#1565C0", edgecolor="white")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Mean importance (gain)")
    ax.tick_params(axis="y", labelsize=9)

plt.tight_layout()
plt.show()"""))

cells.append(code("""\
# Per-target top-10 feature importance (LightGBM)
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
for ax, tgt in zip(axes.flat, TARGETS):
    m   = lgb_models_full[tgt]
    imp = pd.Series(m.feature_importances_, index=NUM_FEATURES).sort_values(ascending=False).head(10)
    ax.barh(imp.index[::-1], imp.values[::-1], color="#42A5F5", edgecolor="white")
    ax.set_title(f"LightGBM importance: {tgt}", fontsize=10)
    ax.set_xlabel("Gain"); ax.tick_params(axis="y", labelsize=8)
plt.suptitle("Top-10 features per outcome (LightGBM gain)", y=1.01, fontsize=12)
plt.tight_layout()
plt.show()"""))

# ── 9  SHAP ──────────────────────────────────────────────────────────────────
cells.append(md("""\
## 9. SHAP analysis

SHAP values explain individual predictions and confirm which features actually
drive the model's decisions (as opposed to correlated-but-irrelevant features
that can have high split-based importance)."""))

cells.append(code("""\
try:
    import shap
    shap.initjs()
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("shap not installed — skipping SHAP section. Install with: pip install shap")

if HAS_SHAP:
    # Use a sample for speed (SHAP on 10 k rows is fast; full dataset can be slow)
    shap_sample_n = min(5000, len(X_test))
    rng = np.random.default_rng(RANDOM_STATE)
    shap_idx = rng.choice(len(X_test), shap_sample_n, replace=False)
    X_shap = X_test.iloc[shap_idx]

    print(f"Computing SHAP values on {shap_sample_n:,} test-set samples ...")

    for tgt in TARGETS:
        m        = lgb_models_full[tgt]
        explainer = shap.TreeExplainer(m)
        shap_vals = explainer.shap_values(X_shap)
        # LightGBM returns list [neg_class, pos_class]; take positive class
        sv = shap_vals[1] if isinstance(shap_vals, list) else shap_vals

        print(f"\\n--- SHAP summary: {tgt} ---")
        shap.summary_plot(sv, X_shap, feature_names=NUM_FEATURES,
                          max_display=20, show=True, plot_size=(10, 6))"""))

# ── 10  Calibration ──────────────────────────────────────────────────────────
cells.append(md("""\
## 10. Calibration — reliability diagrams

Well-calibrated models output probabilities that match observed frequencies.
Miscalibrated models (overconfident or underconfident) reduce actionability.
Use `CalibratedClassifierCV` with Platt scaling if calibration is poor."""))

cells.append(code("""\
from sklearn.calibration import calibration_curve, CalibratedClassifierCV

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for ax, tgt in zip(axes.flat, TARGETS):
    y_true = y_test[tgt].values

    for label, results in [
        ("LGB full",  lgb_results_full[tgt]["test"]),
        ("XGB full",  xgb_results_full[tgt]["test"]),
        ("LGB PCA",   lgb_results_pca [tgt]["test"]),
    ]:
        prob = results["prob"]
        if len(np.unique(y_true)) < 2:
            continue
        frac_pos, mean_pred = calibration_curve(y_true, prob, n_bins=10)
        ax.plot(mean_pred, frac_pos, marker="o", markersize=4, label=label)

    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect")
    ax.set_title(f"Reliability diagram: {tgt}", fontsize=10)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.legend(fontsize=8)

plt.suptitle("Calibration — reliability diagrams (test set)", y=1.01, fontsize=12)
plt.tight_layout()
plt.show()"""))

cells.append(code("""\
# Optional: apply Platt (sigmoid) calibration to the best-AUC model per target
# Uncomment to calibrate and re-evaluate

# calibrated_models = {}
# for tgt in TARGETS:
#     lgb_auc = lgb_results_full[tgt]["test"]["auc"]
#     xgb_auc = xgb_results_full[tgt]["test"]["auc"]
#     base_model = lgb_models_full[tgt] if lgb_auc >= xgb_auc else xgb_models_full[tgt]
#     cal = CalibratedClassifierCV(base_model, method="sigmoid", cv="prefit")
#     cal.fit(X_val, y_val[tgt])
#     calibrated_models[tgt] = cal
#     prob_cal = cal.predict_proba(X_test)[:, 1]
#     print(f"{tgt} — calibrated Brier: {brier_score_loss(y_test[tgt], prob_cal):.4f}")"""))

# ── 11  Score output ──────────────────────────────────────────────────────────
cells.append(md("""\
## 11. Score output — predicted probabilities per developer

Attaches the four predicted probabilities to `developer_id` for downstream targeting.
Uses the LightGBM full-feature models as primary; XGBoost as secondary column."""))

cells.append(code("""\
# Predict on the entire population (train + val + test)
X_all = X_full  # scaled, imputed

score_rows = {}
for tgt in TARGETS:
    lgb_prob = lgb_models_full[tgt].predict_proba(X_all)[:, 1]
    xgb_prob = xgb_models_full[tgt].predict_proba(X_all)[:, 1]
    score_rows[f"lgb_p_{tgt}"] = lgb_prob
    score_rows[f"xgb_p_{tgt}"] = xgb_prob

df_scores = pd.DataFrame(score_rows, index=df.index)
df_scores.insert(0, "developer_id", df["developer_id"].values)

# Highest-probability outcome per developer (primary LightGBM scores)
lgb_score_cols = [f"lgb_p_{t}" for t in TARGETS]
df_scores["top_outcome"] = (
    df_scores[lgb_score_cols]
    .idxmax(axis=1)
    .str.replace("lgb_p_", "", regex=False)
)

print(f"Score table shape: {df_scores.shape}")
display(df_scores.describe().T)

# Save to parquet for downstream use
out_path = "developer_scores.parquet"
df_scores.to_parquet(out_path, index=False)
print(f"\\nScores saved to {out_path}")"""))

cells.append(code("""\
# Score distribution plots
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
for ax, tgt in zip(axes.flat, TARGETS):
    col = f"lgb_p_{tgt}"
    positives = df_scores.loc[df[tgt] == 1, col] if tgt in df.columns else None
    negatives = df_scores.loc[df[tgt] == 0, col] if tgt in df.columns else None
    if positives is not None and len(positives) > 0:
        ax.hist(negatives, bins=50, alpha=0.5, color="#90CAF9", density=True, label="Negative")
        ax.hist(positives, bins=50, alpha=0.6, color="#1565C0", density=True, label="Positive")
        ax.legend(fontsize=9)
    else:
        ax.hist(df_scores[col], bins=50, color="#1565C0", alpha=0.7)
    ax.set_title(f"LightGBM score distribution: {tgt}", fontsize=10)
    ax.set_xlabel("Predicted probability"); ax.set_ylabel("Density")

plt.tight_layout()
plt.show()

con.close()
print("Done. Connection closed.")"""))

# ── Write notebook ────────────────────────────────────────────────────────────
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.10.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = "SupervisedModeling_LGBM_XGB.ipynb"
with open(out, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"Written: {out}  ({len(cells)} cells)")
