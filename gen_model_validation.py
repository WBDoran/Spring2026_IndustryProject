"""
Generates ModelValidation.ipynb from FeatureEngineering_v3.ipynb outputs.
Based on: NVIDIA Parallel Modeling Approaches and Validation Strategy (PDF)
"""
import json
import uuid

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

# ---------------------------------------------------------------------------
# Cells
# ---------------------------------------------------------------------------
cells = []

# ── Title ──────────────────────────────────────────────────────────────────
cells.append(md("""\
# NVIDIA Developer Journey — Model Validation Notebook

Implements the validation strategy from *Parallel Modeling Approaches and Validation Strategy*.

**Pipeline:**
1. Feature panel assembly from `dev_profile_final_v4`
2. Outcome label creation (cutoff-based, 90-day horizon)
3. Feature preprocessing & train / validation split
4. **Primary segmentation:** UMAP + HDBSCAN
5. **Parallel clustering:** PCA + K-Means · SVD + HDBSCAN · Bayesian GMM
6. **Segment agreement:** ARI / NMI cross-method matrix
7. **Journey-state modeling:** rule-based baseline · HMM
8. **Supervised validation (5-test sequence):** activity-score baseline → engineered features → + cluster labels → + HMM states → full framework
9. Validation summary"""))

# ── 0  Setup ────────────────────────────────────────────────────────────────
cells.append(md("## 0. Setup & connection"))
cells.append(code("""\
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 60)
pd.set_option("display.float_format", "{:.4f}".format)

# ── paths ──────────────────────────────────────────────────────────────────
DB_PATH = "developer_project.duckdb"
SAMPLE_PARQUET = "sample_dev_profile_final_v4.parquet"  # fallback for sample run

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
        "Neither " + DB_PATH + " nor " + SAMPLE_PARQUET + " found."
    )

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)"""))

# ── 1  Feature panel ────────────────────────────────────────────────────────
cells.append(md("""\
## 1. Feature panel assembly

Loads `dev_profile_final_v4` and organises features into the six groups from PDF §2.2:
*Intensity · Category/Stage · Persona/Lane · Recency/Cadence · Diversity · Trajectory*"""))

cells.append(code("""\
df_raw = con.execute("SELECT * FROM dev_profile_final_v4").df()
print(f"Loaded {len(df_raw):,} developers  |  {df_raw.shape[1]} columns")
display(df_raw.dtypes.value_counts().rename("dtype counts"))"""))

cells.append(code("""\
# ── Feature group definitions (PDF §2.2) ──────────────────────────────────
INTENSITY = [
    "activity_count_0_30d", "activity_count_30_90d", "activity_count_90_180d",
    "high_effort_count_0_30d", "high_effort_count_30_90d",
    "developer_effort_score",
    "log_clipped_lifetime_activity_count_p99",
    "log_clipped_lifetime_activity_score_sum_p99",
    "log_clipped_lifetime_total_confidence_weighted_effort_p99",
    "log_clipped_lifetime_effort_x_activity_score_sum_p99",
    "weighted_recent_activity",
    "weighted_recent_confidence_effort",
]

STAGE = [
    "lifetime_discover_count", "lifetime_learn_count", "lifetime_evaluate_count",
    "lifetime_build_count", "lifetime_champion_count",
    "build_count_0_30d", "build_count_30_90d",
    "build_share_0_30d", "high_effort_share_0_30d",
    "lifetime_dli_training_count", "lifetime_forum_count",
    "lifetime_api_count", "lifetime_hackathon_count",
]

PERSONA = [
    "cuda_share", "genai_share", "robotics_share",
    "simulation_share", "learning_community_share",
    "persona_entropy", "mixed_persona_flag",
]

RECENCY = [
    "days_since_last_activity", "days_since_last_meaningful_week",
    "lifetime_meaningful_weeks", "lifetime_active_weeks",
    "activity_velocity_0_30_vs_30_90",
    "avg_effort_rank_0_30d", "avg_effort_rank_30_90d",
]

DIVERSITY = [
    "unique_activity_types_0_30d", "unique_modalities_0_30d",
    "lifetime_unique_activity_types", "lifetime_unique_modalities",
    "unique_activity_days_0_30d",
]

TRAJECTORY = [
    "behavior_journey_rank_30d", "current_journey_rank_30d",
    "developer_effort_rank",
    "dormant_flag", "at_risk_flag", "cooling_flag", "is_activated",
]

ALL_FEATURES = (INTENSITY + STAGE + PERSONA + RECENCY + DIVERSITY + TRAJECTORY)

# Keep only columns that actually exist in the dataframe
available = [f for f in ALL_FEATURES if f in df_raw.columns]
missing_def = sorted(set(ALL_FEATURES) - set(df_raw.columns))
print(f"Feature panel: {len(available)} / {len(ALL_FEATURES)} defined features present")
if missing_def:
    print(f"Not found (will be skipped): {missing_def}")

df = df_raw[["developer_id"] + available].copy()"""))

# ── 2  Outcome labels ───────────────────────────────────────────────────────
cells.append(md("""\
## 2. Outcome label creation (PDF §6.1)

Uses a 90-day cutoff window:
- **Features** = activity **before** `anchor_date − 90 days`
- **Labels** = activity **from** `anchor_date − 90 days` **to** `anchor_date`

| Label | Definition |
|-------|-----------|
| `retained_90d` | Any meaningful activity in the outcome window |
| `deepened_90d` | Build/Champion activity OR score increase ≥ 20 % vs prior 90d |
| `expanded_90d` | Touched a new persona lane not present in pre-cutoff period |
| `churned_90d` | Was active pre-cutoff; zero activity in outcome window |"""))

cells.append(code("""\
if DATA_SOURCE == "duckdb":
    outcome_sql = \"\"\"
    WITH max_dt AS (
        SELECT MAX(activity_date) AS anchor_date
        FROM activity_labeled_v2
    ),
    cutoff AS (
        SELECT
            anchor_date - INTERVAL 90 DAY AS cutoff_date,
            anchor_date
        FROM max_dt
    ),
    pre AS (
        SELECT
            a.developer_id,
            COUNT(*)                                              AS pre_count,
            SUM(a.activity_score)                                 AS pre_score,
            MAX(CASE WHEN a.journey_signal IN ('Build','Champion') THEN 1 ELSE 0 END)
                                                                  AS pre_had_build,
            COUNT(DISTINCT
                CASE WHEN a.cuda_persona_score   > 0 THEN 'cuda'
                     WHEN a.genai_persona_score  > 0 THEN 'genai'
                     WHEN a.robotics_persona_score > 0 THEN 'robotics'
                     WHEN a.simulation_persona_score > 0 THEN 'simulation'
                     WHEN a.learning_community_persona_score > 0 THEN 'learning'
                END
            )                                                     AS pre_lane_count
        FROM activity_labeled_v2 a, cutoff
        WHERE a.activity_date <= cutoff.cutoff_date
        GROUP BY a.developer_id
    ),
    post AS (
        SELECT
            a.developer_id,
            COUNT(*)                                              AS post_count,
            SUM(a.activity_score)                                 AS post_score,
            MAX(CASE WHEN a.journey_signal IN ('Build','Champion') THEN 1 ELSE 0 END)
                                                                  AS post_had_build,
            COUNT(DISTINCT
                CASE WHEN a.cuda_persona_score   > 0 THEN 'cuda'
                     WHEN a.genai_persona_score  > 0 THEN 'genai'
                     WHEN a.robotics_persona_score > 0 THEN 'robotics'
                     WHEN a.simulation_persona_score > 0 THEN 'simulation'
                     WHEN a.learning_community_persona_score > 0 THEN 'learning'
                END
            )                                                     AS post_lane_count
        FROM activity_labeled_v2 a, cutoff
        WHERE a.activity_date > cutoff.cutoff_date
        GROUP BY a.developer_id
    )
    SELECT
        u.developer_id,
        -- retained: any activity in outcome window
        CASE WHEN COALESCE(post.post_count, 0) > 0 THEN 1 ELSE 0 END
            AS retained_90d,
        -- deepened: new build/champion signal OR meaningful score growth
        CASE
            WHEN COALESCE(post.post_had_build, 0) = 1 THEN 1
            WHEN COALESCE(post.post_score, 0) > COALESCE(pre.pre_score, 0) * 1.20
                 AND COALESCE(post.post_count, 0) > 0 THEN 1
            ELSE 0
        END AS deepened_90d,
        -- expanded: touched more lanes post-cutoff than pre-cutoff
        CASE
            WHEN COALESCE(post.post_lane_count, 0) > COALESCE(pre.pre_lane_count, 0)
                 AND COALESCE(post.post_count, 0) > 0 THEN 1
            ELSE 0
        END AS expanded_90d,
        -- churned: was active before, zero activity after
        CASE
            WHEN COALESCE(pre.pre_count, 0) > 0
             AND COALESCE(post.post_count, 0) = 0 THEN 1
            ELSE 0
        END AS churned_90d
    FROM developer_universe_v2 u
    LEFT JOIN pre  USING (developer_id)
    LEFT JOIN post USING (developer_id)
    \"\"\"
    df_labels = con.execute(outcome_sql).df()
else:
    # Parquet / sample fallback: approximate using recency columns already in df_raw
    df_labels = pd.DataFrame({
        "developer_id": df_raw["developer_id"],
        "retained_90d":  (df_raw.get("activity_count_0_30d", 0) > 0).astype(int),
        "deepened_90d":  (df_raw.get("build_count_0_30d", 0) > 0).astype(int),
        "expanded_90d":  (df_raw.get("mixed_persona_flag", 0) == 1).astype(int),
        "churned_90d":   (
            (df_raw.get("activity_count_30_90d", 0) > 0) &
            (df_raw.get("activity_count_0_30d",  0) == 0)
        ).astype(int),
    })

print("Outcome label distribution:")
display(df_labels[["retained_90d","deepened_90d","expanded_90d","churned_90d"]].mean()
        .rename("positive rate").to_frame())"""))

# ── 3  Preprocessing ─────────────────────────────────────────────────────────
cells.append(md("""\
## 3. Feature preprocessing & train / validation split

- Median imputation for missing numeric values
- Clip extreme outliers at 99th percentile
- Standard scaling (zero-mean, unit-variance)
- 80 / 20 stratified split on `retained_90d`"""))

cells.append(code("""\
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# Merge labels into feature frame
df_model = df.merge(df_labels, on="developer_id", how="left")

# Numeric feature matrix
X_raw = df_model[available].copy()

# Clip at 99th percentile (per column)
for col in X_raw.select_dtypes(include=np.number).columns:
    p99 = X_raw[col].quantile(0.99)
    X_raw[col] = X_raw[col].clip(upper=p99)

# Impute then scale
imputer = SimpleImputer(strategy="median")
scaler  = StandardScaler()

X_imp    = imputer.fit_transform(X_raw)
X_scaled = scaler.fit_transform(X_imp)
X_df     = pd.DataFrame(X_scaled, columns=available, index=df_model.index)

# Outcome targets
TARGETS = ["retained_90d", "deepened_90d", "expanded_90d", "churned_90d"]
y = df_model[TARGETS].fillna(0).astype(int)

# Stratified split on retained_90d
idx_train, idx_val = train_test_split(
    df_model.index,
    test_size=0.20,
    random_state=RANDOM_STATE,
    stratify=y["retained_90d"],
)

X_train, X_val = X_df.loc[idx_train], X_df.loc[idx_val]
y_train, y_val = y.loc[idx_train],    y.loc[idx_val]

print(f"Train: {len(X_train):,}  |  Val: {len(X_val):,}")
print(f"Val retained rate: {y_val['retained_90d'].mean():.2%}")"""))

# ── 4  UMAP + HDBSCAN ────────────────────────────────────────────────────────
cells.append(md("""\
## 4. Primary segmentation: UMAP + HDBSCAN (PDF §3)

UMAP creates a 2-D behavior space; HDBSCAN identifies dense clusters without requiring a preset *k*."""))

cells.append(code("""\
try:
    import umap
except ImportError:
    raise ImportError("Install with: pip install umap-learn")

try:
    import hdbscan as hdbscan_lib
except ImportError:
    raise ImportError("Install with: pip install hdbscan")

# Use full scaled matrix for clustering (train + val together — unsupervised)
X_cluster = X_df.values

reducer = umap.UMAP(
    n_neighbors=30,
    min_dist=0.0,
    n_components=2,
    metric="euclidean",
    random_state=RANDOM_STATE,
    n_jobs=1,
)
embedding = reducer.fit_transform(X_cluster)
df_model["umap_x"] = embedding[:, 0]
df_model["umap_y"] = embedding[:, 1]
print("UMAP embedding shape:", embedding.shape)"""))

cells.append(code("""\
clusterer = hdbscan_lib.HDBSCAN(
    min_cluster_size=50,
    min_samples=10,
    cluster_selection_method="eom",
    prediction_data=True,
)
clusterer.fit(embedding)

df_model["hdbscan_cluster"]     = clusterer.labels_
df_model["cluster_probability"] = clusterer.probabilities_
df_model["noise_flag"]          = (clusterer.labels_ == -1).astype(int)

n_clusters = len(set(clusterer.labels_)) - (1 if -1 in clusterer.labels_ else 0)
noise_pct   = df_model["noise_flag"].mean()
print(f"HDBSCAN: {n_clusters} clusters  |  noise: {noise_pct:.1%}")
display(
    pd.Series(clusterer.labels_).value_counts()
      .rename_axis("cluster").reset_index(name="count")
      .head(20)
)"""))

cells.append(code("""\
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Cluster map
sc = axes[0].scatter(
    df_model["umap_x"], df_model["umap_y"],
    c=df_model["hdbscan_cluster"],
    cmap="tab20", s=2, alpha=0.4, linewidths=0,
)
axes[0].set_title("UMAP + HDBSCAN Clusters")
axes[0].set_xlabel("UMAP 1"); axes[0].set_ylabel("UMAP 2")
plt.colorbar(sc, ax=axes[0], label="Cluster")

# Effort level overlay
effort_map = {"low": 0, "passive": -1, "moderate": 1, "high": 2, "very high": 3}
if "developer_effort_level" in df_model.columns:
    hue_vals = df_model["developer_effort_level"].map(effort_map).fillna(0)
    sc2 = axes[1].scatter(
        df_model["umap_x"], df_model["umap_y"],
        c=hue_vals, cmap="RdYlGn", s=2, alpha=0.4, linewidths=0,
    )
    axes[1].set_title("Developer Effort Level")
    axes[1].set_xlabel("UMAP 1"); axes[1].set_ylabel("UMAP 2")
    plt.colorbar(sc2, ax=axes[1], label="Effort rank")

plt.tight_layout()
plt.show()"""))

# ── 5  Parallel clustering ───────────────────────────────────────────────────
cells.append(md("""\
## 5. Parallel clustering for validation (PDF §4)

Three alternatives to test whether UMAP + HDBSCAN segments are real:
- **PCA + K-Means** — classic baseline
- **SVD + HDBSCAN** — density clusters on a stable linear embedding
- **Bayesian GMM** — soft probabilistic clusters; handles mixed membership"""))

cells.append(code("""\
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.cluster import KMeans

# ── PCA + K-Means ─────────────────────────────────────────────────────────
N_CLUSTERS_KMEANS = max(n_clusters, 6)  # match HDBSCAN count where possible

pca = PCA(n_components=20, random_state=RANDOM_STATE)
X_pca = pca.fit_transform(X_cluster)
print(f"PCA 20-D explained variance: {pca.explained_variance_ratio_.sum():.1%}")

kmeans = KMeans(n_clusters=N_CLUSTERS_KMEANS, random_state=RANDOM_STATE, n_init=10)
df_model["kmeans_cluster"] = kmeans.fit_predict(X_pca)

print(f"K-Means: {N_CLUSTERS_KMEANS} clusters")
display(
    pd.Series(df_model["kmeans_cluster"]).value_counts()
      .rename_axis("cluster").reset_index(name="count")
)"""))

cells.append(code("""\
# ── SVD + HDBSCAN ────────────────────────────────────────────────────────
svd = TruncatedSVD(n_components=30, random_state=RANDOM_STATE)
X_svd = svd.fit_transform(X_cluster)
print(f"SVD 30-D explained variance: {svd.explained_variance_ratio_.sum():.1%}")

clusterer_svd = hdbscan_lib.HDBSCAN(
    min_cluster_size=50,
    min_samples=10,
    cluster_selection_method="eom",
)
df_model["svd_hdbscan_cluster"] = clusterer_svd.fit_predict(X_svd)

n_svd_clusters = len(set(clusterer_svd.labels_)) - (1 if -1 in clusterer_svd.labels_ else 0)
print(f"SVD + HDBSCAN: {n_svd_clusters} clusters  |  noise: {(clusterer_svd.labels_ == -1).mean():.1%}")"""))

cells.append(code("""\
# ── Bayesian GMM ────────────────────────────────────────────────────────
from sklearn.mixture import BayesianGaussianMixture

bgmm = BayesianGaussianMixture(
    n_components=N_CLUSTERS_KMEANS,
    covariance_type="full",
    random_state=RANDOM_STATE,
    max_iter=200,
)
bgmm.fit(X_pca)
df_model["bgmm_cluster"]     = bgmm.predict(X_pca)
df_model["bgmm_probability"] = bgmm.predict_proba(X_pca).max(axis=1)

active_components = (bgmm.predict_proba(X_pca).sum(axis=0) > 10).sum()
print(f"Bayesian GMM: {active_components} active components (of {N_CLUSTERS_KMEANS} max)")"""))

# ── 6  Segment agreement ────────────────────────────────────────────────────
cells.append(md("""\
## 6. Segment agreement matrix (PDF §4.1)

ARI and NMI measure how similarly each pair of clustering methods partitions developers.
High agreement (ARI > 0.3) across methods increases confidence that segments are real."""))

cells.append(code("""\
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

# Exclude noise (−1) rows from ARI / NMI to avoid distorting scores
mask_no_noise = df_model["hdbscan_cluster"] != -1

cluster_cols = {
    "UMAP+HDBSCAN":  "hdbscan_cluster",
    "SVD+HDBSCAN":   "svd_hdbscan_cluster",
    "PCA+KMeans":    "kmeans_cluster",
    "BayesianGMM":   "bgmm_cluster",
}

methods = list(cluster_cols.keys())
ari_mat = pd.DataFrame(np.eye(len(methods)), index=methods, columns=methods)
nmi_mat = pd.DataFrame(np.eye(len(methods)), index=methods, columns=methods)

for i, (m1, c1) in enumerate(cluster_cols.items()):
    for j, (m2, c2) in enumerate(cluster_cols.items()):
        if i >= j:
            continue
        a = df_model.loc[mask_no_noise, c1]
        b = df_model.loc[mask_no_noise, c2]
        ari = adjusted_rand_score(a, b)
        nmi = normalized_mutual_info_score(a, b)
        ari_mat.loc[m1, m2] = ari_mat.loc[m2, m1] = ari
        nmi_mat.loc[m1, m2] = nmi_mat.loc[m2, m1] = nmi

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.heatmap(ari_mat.astype(float), annot=True, fmt=".2f", cmap="YlGn",
            vmin=0, vmax=1, ax=axes[0], linewidths=0.5)
axes[0].set_title("Adjusted Rand Index (ARI)")

sns.heatmap(nmi_mat.astype(float), annot=True, fmt=".2f", cmap="YlGn",
            vmin=0, vmax=1, ax=axes[1], linewidths=0.5)
axes[1].set_title("Normalized Mutual Information (NMI)")

plt.suptitle("Segment Agreement Across Clustering Methods", fontsize=13, y=1.01)
plt.tight_layout()
plt.show()

print("Interpretation: ARI > 0.3 = meaningful agreement; ARI > 0.6 = strong agreement")"""))

# ── 7  Cluster profiles ──────────────────────────────────────────────────────
cells.append(md("""\
## 7. Behavioral cluster profiles (primary UMAP + HDBSCAN)

For each cluster: median effort score, effort level distribution, persona, and journey stage.
Used to assign human-readable `behavioral_segment_name` labels."""))

cells.append(code("""\
profile_cols = [
    "hdbscan_cluster",
    "developer_effort_score", "developer_effort_level",
    "persona", "behavior_journey_stage_30d",
    "dormancy_status", "mixed_persona_flag",
    "activity_count_0_30d", "build_count_0_30d",
]
profile_cols_exist = [c for c in profile_cols if c in df_model.columns]

cluster_profiles = (
    df_model[df_model["hdbscan_cluster"] != -1]
    [profile_cols_exist]
    .groupby("hdbscan_cluster")
    .agg(
        count=("developer_effort_score", "size"),
        median_effort_score=("developer_effort_score", "median"),
        top_effort_level=("developer_effort_level",
                          lambda x: x.value_counts().index[0] if len(x) else "N/A"),
        top_persona=("persona",
                     lambda x: x.value_counts().index[0] if len(x) else "N/A"),
        top_journey_stage=("behavior_journey_stage_30d",
                           lambda x: x.value_counts().index[0] if len(x) else "N/A"),
        pct_dormant=("dormancy_status",
                     lambda x: (x == "Dormant").mean()),
        pct_mixed_persona=("mixed_persona_flag", "mean"),
        median_activity_30d=("activity_count_0_30d", "median"),
    )
    .sort_values("count", ascending=False)
)
display(cluster_profiles)"""))

# ── 8  Weekly sequence & HMM ────────────────────────────────────────────────
cells.append(md("""\
## 8. Journey-state modeling (PDF §5)

### 8a. Load weekly sequence table

`dev_weekly_features_v2` (one row per developer per week) feeds both rule-based states and HMM."""))

cells.append(code("""\
if DATA_SOURCE == "duckdb":
    df_weekly = con.execute(\"\"\"
        SELECT
            developer_id,
            week_start,
            activity_count_total,
            activity_score_sum,
            unique_activity_types,
            build_count,
            champion_count,
            high_effort_count,
            product_use_count,
            meaningful_week_flag
        FROM dev_meaningful_week_v2
        ORDER BY developer_id, week_start
    \"\"\").df()
    print(f"Weekly sequences: {len(df_weekly):,} rows  |  "
          f"{df_weekly['developer_id'].nunique():,} developers")
else:
    df_weekly = pd.DataFrame(columns=[
        "developer_id","week_start","activity_count_total","activity_score_sum",
        "unique_activity_types","build_count","champion_count",
        "high_effort_count","product_use_count","meaningful_week_flag",
    ])
    print("Weekly data not available in parquet fallback — HMM section will be skipped.")

has_weekly = len(df_weekly) > 0"""))

cells.append(md("### 8b. Rule-based journey states (baseline, PDF §5)"))
cells.append(code("""\
# Rule-based states already computed in dev_journey_state_v2 → current_journey_state_30d.
# Map numeric rank to label for convenience.
JOURNEY_RANK_MAP = {
    0: "Unactivated", 1: "Discover", 2: "Learn",
    3: "Evaluate",    4: "Build",    5: "Champion",
}
if "current_journey_state_30d" in df_model.columns:
    state_dist = (
        df_model["current_journey_state_30d"].value_counts(normalize=True)
          .rename("share").reset_index()
    )
    state_dist.columns = ["state", "share"]
    display(state_dist)

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=state_dist, x="state", y="share", ax=ax,
                palette="Blues_d", linecolor="black")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_title("Rule-Based Journey State Distribution (30-day window)")
    ax.set_xlabel(""); ax.set_ylabel("Share of developers")
    plt.tight_layout()
    plt.show()
else:
    print("current_journey_state_30d not found in feature table.")"""))

cells.append(md("""\
### 8c. HMM journey states (PDF §5.1)

Uses `hmmlearn.hmm.GaussianHMM` on per-developer weekly observation sequences.
Hidden states map to: **Dormant · Discover · Learn · Evaluate · Build · Champion**"""))

cells.append(code("""\
if not has_weekly:
    print("Skipping HMM — no weekly data available.")
else:
    try:
        from hmmlearn import hmm as hmmlearn_hmm
    except ImportError:
        raise ImportError("Install with: pip install hmmlearn")

    # ── Feature matrix for HMM observations ────────────────────────────────
    OBS_COLS = [
        "activity_count_total", "activity_score_sum",
        "build_count", "champion_count",
        "high_effort_count", "product_use_count",
    ]
    # Log-transform + impute
    df_obs = df_weekly[["developer_id","week_start"] + OBS_COLS].copy()
    for c in OBS_COLS:
        df_obs[c] = np.log1p(df_obs[c].fillna(0))

    # Build sequences list and lengths array
    seqs, lengths = [], []
    dev_order = []
    for dev_id, grp in df_obs.groupby("developer_id", sort=True):
        obs = grp[OBS_COLS].values.astype(np.float32)
        seqs.append(obs)
        lengths.append(len(obs))
        dev_order.append(dev_id)

    X_hmm = np.vstack(seqs)
    lengths_arr = np.array(lengths)

    # ── Fit GaussianHMM ────────────────────────────────────────────────────
    N_STATES = 6  # Dormant · Discover · Learn · Evaluate · Build · Champion
    model_hmm = hmmlearn_hmm.GaussianHMM(
        n_components=N_STATES,
        covariance_type="diag",
        n_iter=100,
        random_state=RANDOM_STATE,
        verbose=False,
    )
    model_hmm.fit(X_hmm, lengths_arr)
    print(f"HMM log-likelihood: {model_hmm.score(X_hmm, lengths_arr):.2f}")

    # ── Decode most-likely state per developer (last week) ─────────────────
    state_seqs = model_hmm.predict(X_hmm, lengths_arr)
    # Reconstruct per-developer last state
    cumlen = np.concatenate([[0], np.cumsum(lengths_arr)])
    hmm_last_states = [state_seqs[cumlen[i+1] - 1] for i in range(len(dev_order))]

    df_hmm_states = pd.DataFrame({
        "developer_id": dev_order,
        "hmm_state": hmm_last_states,
    })
    print("HMM state distribution (raw labels):")
    display(df_hmm_states["hmm_state"].value_counts().sort_index())

    # Merge into model frame
    df_model = df_model.merge(df_hmm_states, on="developer_id", how="left")
    df_model["hmm_state"] = df_model["hmm_state"].fillna(-1).astype(int)
    print("HMM states merged into df_model.")"""))

cells.append(code("""\
if has_weekly and "hmm_state" in df_model.columns and df_model["hmm_state"].gt(-1).any():
    # Transition matrix heatmap
    fig, ax = plt.subplots(figsize=(7, 5))
    trans_df = pd.DataFrame(
        model_hmm.transmat_,
        index=[f"S{i}" for i in range(N_STATES)],
        columns=[f"S{i}" for i in range(N_STATES)],
    )
    sns.heatmap(trans_df, annot=True, fmt=".2f", cmap="Blues",
                linewidths=0.5, ax=ax)
    ax.set_title("HMM Transition Matrix")
    ax.set_xlabel("To state"); ax.set_ylabel("From state")
    plt.tight_layout()
    plt.show()

    # Overlay HMM states on UMAP
    if "umap_x" in df_model.columns:
        fig, ax = plt.subplots(figsize=(8, 6))
        sc = ax.scatter(
            df_model["umap_x"], df_model["umap_y"],
            c=df_model["hmm_state"], cmap="tab10",
            s=2, alpha=0.4, linewidths=0,
        )
        ax.set_title("HMM States on UMAP Embedding")
        ax.set_xlabel("UMAP 1"); ax.set_ylabel("UMAP 2")
        plt.colorbar(sc, ax=ax, label="HMM state")
        plt.tight_layout()
        plt.show()"""))

# ── 9  Supervised validation ─────────────────────────────────────────────────
cells.append(md("""\
## 9. Supervised validation — 5-test sequence (PDF §6.2)

Each test adds one layer to the feature set.
Primary metric: **ROC-AUC** for each of the four outcome labels.
Models: Logistic Regression (baseline), Random Forest, LightGBM."""))

cells.append(code("""\
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    print("lightgbm not installed — skipping LightGBM tests. Install with: pip install lightgbm")

def eval_model(model, X_tr, y_tr, X_v, y_v, label):
    model.fit(X_tr, y_tr)
    prob = model.predict_proba(X_v)[:, 1]
    return roc_auc_score(y_v, prob)

def run_test(test_name, feature_cols, targets=TARGETS):
    fc = [c for c in feature_cols if c in df_model.columns]
    X_tr = df_model.loc[idx_train, fc].fillna(0)
    X_v  = df_model.loc[idx_val,   fc].fillna(0)

    results = {}
    for tgt in targets:
        y_tr_ = y_train[tgt]
        y_v_  = y_val[tgt]
        if y_v_.sum() == 0:
            results[tgt] = {"LR": np.nan, "RF": np.nan, "LGB": np.nan}
            continue
        lr  = LogisticRegression(max_iter=500, random_state=RANDOM_STATE)
        rf  = RandomForestClassifier(n_estimators=100, max_depth=8,
                                      random_state=RANDOM_STATE, n_jobs=-1)
        lr_auc  = eval_model(lr,  X_tr, y_tr_, X_v, y_v_, tgt)
        rf_auc  = eval_model(rf,  X_tr, y_tr_, X_v, y_v_, tgt)
        if HAS_LGB:
            lgb_model = lgb.LGBMClassifier(
                n_estimators=200, max_depth=6,
                learning_rate=0.05, random_state=RANDOM_STATE,
                verbosity=-1, n_jobs=-1,
            )
            lgb_auc = eval_model(lgb_model, X_tr, y_tr_, X_v, y_v_, tgt)
        else:
            lgb_auc = np.nan
        results[tgt] = {"LR": lr_auc, "RF": rf_auc, "LGB": lgb_auc}

    flat = []
    for tgt, aucs in results.items():
        for model_name, auc in aucs.items():
            flat.append({"test": test_name, "target": tgt,
                         "model": model_name, "auc": auc})
    return flat

all_results = []"""))

cells.append(code("""\
# Test 1 — Activity score baseline (PDF §6.2 Test 1)
TEST1_FEATURES = [
    "log_clipped_lifetime_activity_score_sum_p99",
    "activity_count_0_30d", "activity_count_30_90d",
    "days_since_last_activity",
    "developer_effort_score",
]
print("Running Test 1: activity score baseline ...")
all_results += run_test("1_score_baseline", TEST1_FEATURES)
print("  done")"""))

cells.append(code("""\
# Test 2 — Engineered features only (PDF §6.2 Test 2)
TEST2_FEATURES = available  # full engineered feature panel
print("Running Test 2: engineered features only ...")
all_results += run_test("2_engineered_features", TEST2_FEATURES)
print("  done")"""))

cells.append(code("""\
# Test 3 — Add cluster labels (PDF §6.2 Test 3)
CLUSTER_COLS = [c for c in ["hdbscan_cluster","cluster_probability","noise_flag"] if c in df_model.columns]
TEST3_FEATURES = TEST2_FEATURES + CLUSTER_COLS
print("Running Test 3: + cluster labels ...")
all_results += run_test("3_plus_clusters", TEST3_FEATURES)
print("  done")"""))

cells.append(code("""\
# Test 4 — Add HMM states (PDF §6.2 Test 4)
HMM_COLS = [c for c in ["hmm_state","current_journey_rank_30d","behavior_journey_rank_30d"]
             if c in df_model.columns]
TEST4_FEATURES = TEST3_FEATURES + HMM_COLS
print("Running Test 4: + HMM / journey states ...")
all_results += run_test("4_plus_hmm", TEST4_FEATURES)
print("  done")"""))

cells.append(code("""\
# Test 5 — Full framework: + persona + account context (PDF §6.2 Test 5)
ACCOUNT_COLS = [c for c in [
    "account_type","country","region","industry_segment_vertical",
    "wwfo_category","wwfo_target_list",
] if c in df_model.columns]
# One-hot encode string account columns
df_account_ohe = pd.get_dummies(
    df_model[ACCOUNT_COLS].fillna("Unknown"), drop_first=False
)
for col in df_account_ohe.columns:
    df_model[col] = df_account_ohe[col].values

TEST5_FEATURES = TEST4_FEATURES + list(df_account_ohe.columns)
print("Running Test 5: full framework ...")
all_results += run_test("5_full_framework", TEST5_FEATURES)
print("  done")"""))

# ── 10  Results table ────────────────────────────────────────────────────────
cells.append(md("""\
## 10. Supervised results — AUC comparison table (PDF §9)

Each row is one test × target × model combination.
Higher AUC in later tests shows incremental value of each modeling layer."""))

cells.append(code("""\
results_df = pd.DataFrame(all_results)

# Pivot: tests as rows, (target × model) as columns
pivot = results_df.pivot_table(
    index="test", columns=["target","model"], values="auc"
).round(3)
display(pivot)

# Simplified mean AUC per test (across targets, LR model)
lr_summary = (
    results_df[results_df["model"] == "LR"]
    .groupby("test")["auc"]
    .mean()
    .rename("mean_AUC_LR")
    .reset_index()
)
print("\\nMean AUC (LR) per test:")
display(lr_summary)

fig, ax = plt.subplots(figsize=(9, 4))
for model_name, grp in results_df[results_df["target"] == "retained_90d"].groupby("model"):
    ax.plot(grp["test"], grp["auc"], marker="o", label=model_name)
ax.set_title("ROC-AUC on retained_90d across 5 tests")
ax.set_ylabel("AUC"); ax.set_xlabel("")
ax.legend()
ax.tick_params(axis="x", rotation=20)
plt.tight_layout()
plt.show()"""))

# ── 11  Segment stability ────────────────────────────────────────────────────
cells.append(md("""\
## 11. Segment stability check (PDF §9)

Re-runs HDBSCAN with a different random seed on a 70 % subsample.
High ARI (> 0.4) with the original clustering confirms segments are not artefacts of sampling."""))

cells.append(code("""\
rng = np.random.default_rng(seed=99)
subsample_mask = rng.random(len(embedding)) < 0.70
sub_emb = embedding[subsample_mask]

clusterer_sub = hdbscan_lib.HDBSCAN(
    min_cluster_size=50, min_samples=10, cluster_selection_method="eom"
)
sub_labels = clusterer_sub.fit_predict(sub_emb)

full_labels_sub = df_model["hdbscan_cluster"].values[subsample_mask]
# Exclude noise
mask_both = (sub_labels != -1) & (full_labels_sub != -1)
stability_ari = adjusted_rand_score(full_labels_sub[mask_both], sub_labels[mask_both])
print(f"Stability ARI (70 % subsample vs. full): {stability_ari:.3f}")
print("Interpretation: ARI > 0.4 = stable; ARI < 0.2 = fragile segments")"""))

# ── 12  Final validation summary ─────────────────────────────────────────────
cells.append(md("""\
## 12. Validation summary (PDF §9)

Aggregates evidence across all four validation layers."""))

cells.append(code("""\
best_lr_auc = (
    results_df[results_df["model"] == "LR"]
    .groupby("test")["auc"].mean()
)

print("=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)

print(f"\\n1. Segment agreement (ARI, UMAP+HDBSCAN vs PCA+KMeans):")
ari_val = ari_mat.loc["UMAP+HDBSCAN", "PCA+KMeans"]
print(f"   ARI = {ari_val:.3f}  ->  {'good' if ari_val > 0.30 else 'weak'} agreement")

print(f"\\n2. Segment stability (subsample ARI):")
print(f"   ARI = {stability_ari:.3f}  ->  {'stable' if stability_ari > 0.40 else 'fragile'}")

print(f"\\n3. Supervised lift (mean LR AUC, retained_90d):")
for test, auc in best_lr_auc.items():
    print(f"   {test}: {auc:.3f}")

score_auc = best_lr_auc.get("1_score_baseline", np.nan)
full_auc  = best_lr_auc.get("5_full_framework", np.nan)
lift = full_auc - score_auc if not (np.isnan(full_auc) or np.isnan(score_auc)) else np.nan
print(f"   Lift (full framework vs. score baseline): {lift:+.3f}")

print(f"\\n4. Journey-state coverage (HMM vs rule-based):")
if "hmm_state" in df_model.columns and df_model["hmm_state"].gt(-1).any():
    rb_cov  = df_model["current_journey_state_30d"].notna().mean()
    hmm_cov = (df_model["hmm_state"] >= 0).mean()
    print(f"   Rule-based coverage: {rb_cov:.1%}")
    print(f"   HMM coverage:        {hmm_cov:.1%}")
else:
    print("   HMM not run — see section 8c.")

print("\\nDecision rule: choose the method most interpretable, stable,")
print("predictive of future outcomes, and actionable for NVIDIA.")"""))

# ── Close ────────────────────────────────────────────────────────────────────
cells.append(code("con.close()\nprint('Connection closed.')"))

# ---------------------------------------------------------------------------
# Write notebook
# ---------------------------------------------------------------------------
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out_path = "ModelValidation.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"Written: {out_path}  ({len(cells)} cells)")
