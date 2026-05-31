#!/usr/bin/env python3
"""Patch Section 14 to run on all HMM-scored developers (full weekly population)."""
import json
from pathlib import Path

nb_path = Path(__file__).resolve().parents[1] / "NVIDIA_HMM_Journey_Analysis_v2.ipynb"
nb = json.loads(nb_path.read_text())

CELL_14_MD = """## 14. Cluster × Journey Targeting Analysis

Combines **V11 HDBSCAN persona clusters** with **HMM weekly journey behavior** to identify cluster-specific journey patterns and targeting opportunities.

Run **14.0** first (standalone-safe if v1 HMM parquets are loaded in DuckDB). Outputs land in `hmm_analysis_outputs_v2/`.

**Population:** All **valid HMM-scored developers** in `dev_hmm_weekly_states_v1` (every developer with ≥3 weekly rows and a V11 cluster assignment). This is the full HMM inference cohort (~150K), not a journey-table subsample. Clusters with no HMM-scored developers are omitted."""

CELL_14_0 = r'''# 14.0 Standalone bootstrap
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DB_PATH = "developer_project.duckdb"
OUTPUT_DIR = Path("hmm_analysis_outputs_v2")
OUTPUT_DIR.mkdir(exist_ok=True)
MIN_CLUSTER_N = 1  # include all clusters with any HMM-scored developers
WRITE_TABLES = True

HMM_STATE_LABELS = {
    0: "Idle / Minimal Weekly Activity",
    1: "Low Recent Activity / Lapsing",
    2: "Light At-Risk Engagement",
    3: "Cooling / Declining Engagement",
    4: "Active Exploration Burst",
    5: "Build-Oriented Weekly Usage",
    6: "Prior Active / Starting Engagement",
    7: "Irregular / Noisy Weekly Activity",
}

NVIDIA_GREEN = "#76B900"
PALETTE = {
    "active": "#76B900",
    "cooling": "#F4B400",
    "at_risk": "#DB4437",
    "dormant": "#5F6368",
    "unactivated": "#B0BEC5",
}

state_label_order = [HMM_STATE_LABELS[i] for i in sorted(HMM_STATE_LABELS)]

plt.rcParams["figure.dpi"] = 120
pd.set_option("display.max_columns", 200)
pd.set_option("display.max_rows", 100)

try:
    con.execute("SELECT 1").fetchone()
except Exception:
    con = duckdb.connect(DB_PATH)

REQUIRED_TABLES = [
    "dev_hmm_weekly_states_v1",
    "dev_v11_cluster_names",
    "dev_lifecycle_cluster_membership_v11_final",
]

existing = set(con.execute("SHOW TABLES").fetchdf().iloc[:, 0].astype(str))
missing = [t for t in REQUIRED_TABLES if t not in existing]
if missing:
    raise RuntimeError(f"Missing required tables: {missing}. Load toexport_HMM/ parquets first.")

label_df = pd.DataFrame([
    {"hmm_hidden_state": state, "hmm_state_label": label}
    for state, label in HMM_STATE_LABELS.items()
])
con.register("_label_df", label_df)
con.execute("CREATE OR REPLACE TEMP TABLE hmm_state_labels_v2_view AS SELECT * FROM _label_df")
con.unregister("_label_df")

# All developers with HMM weekly rows + V11 persona names
con.execute("""
CREATE OR REPLACE TEMP VIEW v_hmm_valid_developers AS
SELECT DISTINCT
    n.developer_id,
    n.stratum,
    n.cluster_key,
    n.persona_feature_name,
    n.persona_technical_name,
    n.demographic_audience,
    n.demographic_archetypes,
    n.is_ghost_cluster,
    n.cluster_label_slide,
    n.cluster_label_combined
FROM dev_hmm_weekly_states_v1 w
JOIN dev_v11_cluster_names n
  ON w.developer_id = n.developer_id
""")

# Journey metrics derived from weekly states for every valid developer
con.execute("""
CREATE OR REPLACE TEMP VIEW v_hmm_dev_journey_from_weekly AS
SELECT
    d.developer_id,
    d.stratum,
    d.cluster_key,
    d.persona_feature_name,
    d.persona_technical_name,
    d.demographic_audience,
    d.demographic_archetypes,
    d.is_ghost_cluster,
    d.cluster_label_slide,
    d.cluster_label_combined,
    COUNT(*) AS n_weeks,
    arg_min(w.hmm_hidden_state, w.week_start) AS first_hmm_state,
    arg_max(w.hmm_hidden_state, w.week_start) AS last_hmm_state,
    mode(w.hmm_hidden_state) AS dominant_hmm_state,
    MIN(w.week_start) AS first_week,
    MAX(w.week_start) AS last_week,
    AVG(w.hmm_state_probability) AS avg_state_probability
FROM dev_hmm_weekly_states_v1 w
JOIN v_hmm_valid_developers d
  ON w.developer_id = d.developer_id
GROUP BY
    d.developer_id, d.stratum, d.cluster_key, d.persona_feature_name,
    d.persona_technical_name, d.demographic_audience, d.demographic_archetypes,
    d.is_ghost_cluster, d.cluster_label_slide, d.cluster_label_combined
""")

n_valid = con.execute("SELECT COUNT(*) FROM v_hmm_valid_developers").fetchone()[0]
n_weekly_rows = con.execute("SELECT COUNT(*) FROM dev_hmm_weekly_states_v1").fetchone()[0]
n_clusters_in_hmm = con.execute("SELECT COUNT(DISTINCT cluster_key) FROM v_hmm_valid_developers").fetchone()[0]
n_clusters_full = con.execute(
    "SELECT COUNT(DISTINCT cluster_key) FROM dev_lifecycle_cluster_membership_v11_final"
).fetchone()[0]

print(f"Valid HMM-scored developers: {n_valid:,}")
print(f"Weekly HMM rows: {n_weekly_rows:,}")
print(f"Clusters with HMM data: {n_clusters_in_hmm} / {n_clusters_full} total V11 clusters")
print(f"Output directory: {OUTPUT_DIR.resolve()}")
'''

CELL_14_1 = r'''# 14.1 — weekly state distribution by cluster
state_dist = con.execute("""
WITH weekly AS (
    SELECT
        s.stratum,
        s.cluster_key,
        s.persona_feature_name,
        s.cluster_label_slide,
        w.hmm_hidden_state,
        w.developer_id
    FROM dev_hmm_weekly_states_v1 w
    INNER JOIN v_hmm_valid_developers s
        ON w.developer_id = s.developer_id
)
SELECT
    w.stratum,
    w.cluster_key,
    w.persona_feature_name,
    w.cluster_label_slide,
    w.hmm_hidden_state,
    l.hmm_state_label,
    COUNT(*) AS n_weeks,
    COUNT(DISTINCT w.developer_id) AS n_developers
FROM weekly w
JOIN hmm_state_labels_v2_view l
    ON w.hmm_hidden_state = l.hmm_hidden_state
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY stratum, cluster_key, n_weeks DESC
""").fetchdf()

state_dist["share_within_cluster"] = (
    state_dist.groupby(["stratum", "cluster_key"])["n_weeks"].transform(lambda s: s / s.sum())
)

cluster_hmm_state_distribution_v2 = state_dist.copy()

plot_df = state_dist.copy()
cluster_order = (
    state_dist.groupby(["stratum", "cluster_key", "cluster_label_slide"], as_index=False)["n_developers"]
    .max()
    .sort_values(["stratum", "n_developers"], ascending=[True, False])
)
plot_df = plot_df.merge(cluster_order[["cluster_key", "cluster_label_slide"]], on=["cluster_key", "cluster_label_slide"])
plot_df["cluster_label_slide"] = pd.Categorical(
    plot_df["cluster_label_slide"],
    categories=cluster_order["cluster_label_slide"].tolist(),
    ordered=True,
)

pivot = plot_df.pivot_table(
    index="cluster_label_slide",
    columns="hmm_state_label",
    values="share_within_cluster",
    aggfunc="sum",
    fill_value=0,
)
pivot = pivot.reindex(columns=[c for c in state_label_order if c in pivot.columns])

fig, ax = plt.subplots(figsize=(14, max(6, 0.35 * len(pivot))))
im = ax.imshow(pivot.values, aspect="auto", cmap="YlGn")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=8)
ax.set_title("HMM Weekly State Share by V11 Cluster (all valid HMM-scored developers)")
fig.colorbar(im, ax=ax, label="Share of weeks")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "cluster_hmm_state_distribution_heatmap.png", bbox_inches="tight")
plt.show()

if WRITE_TABLES:
    con.register("_state_dist", cluster_hmm_state_distribution_v2)
    con.execute("CREATE OR REPLACE TABLE cluster_hmm_state_distribution_v2 AS SELECT * FROM _state_dist")
    con.unregister("_state_dist")

cluster_hmm_state_distribution_v2.to_csv(OUTPUT_DIR / "cluster_hmm_state_distribution_v2.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'cluster_hmm_state_distribution_v2.csv'}")
display(cluster_hmm_state_distribution_v2.head(12))
'''

# Continue with replacements for 14.2-14.6 using v_hmm_valid_developers
# I'll read from insert script and patch

def set_cell(prefix, new_src):
    for c in nb["cells"]:
        src = "".join(c.get("source", []))
        if src.startswith(prefix):
            c["source"] = [new_src]
            return True
    raise SystemExit(f"Cell not found: {prefix}")

def replace_in_cells(old, new):
    for c in nb["cells"]:
        src = "".join(c.get("source", []))
        if old in src:
            c["source"] = [src.replace(old, new)]

# markdown header
for c in nb["cells"]:
    if "".join(c.get("source", [])).startswith("## 14. Cluster"):
        c["source"] = [CELL_14_MD]
        break

set_cell("# 14.0 Standalone bootstrap", CELL_14_0)
set_cell("# 14.1 — weekly state distribution", CELL_14_1)

replace_in_cells("v_hmm_sample_with_persona", "v_hmm_valid_developers")
replace_in_cells("clusters with n >= MIN_CLUSTER_N", "all valid HMM-scored developers")
replace_in_cells("(eligible clusters, n >= MIN_CLUSTER_N)", "(all valid developers)")
replace_in_cells("Top Journey Paths (eligible clusters, n >= MIN_CLUSTER_N)", "Top Journey Paths (all valid developers)")

# Fix 14.3 to use journey from weekly + entropy
CELL_14_3 = r'''# 14.3 — journey paths per cluster (derived from all weekly rows)
journey_base = con.execute("""
SELECT
    s.*,
    lf.hmm_state_label AS first_hmm_state_label,
    ll.hmm_state_label AS last_hmm_state_label,
    ld.hmm_state_label AS dominant_hmm_state_label
FROM v_hmm_dev_journey_from_weekly s
JOIN hmm_state_labels_v2_view lf ON s.first_hmm_state = lf.hmm_hidden_state
JOIN hmm_state_labels_v2_view ll ON s.last_hmm_state = ll.hmm_hidden_state
JOIN hmm_state_labels_v2_view ld ON s.dominant_hmm_state = ld.hmm_hidden_state
""").fetchdf()

state_seq = con.execute("""
SELECT w.developer_id, w.hmm_hidden_state
FROM dev_hmm_weekly_states_v1 w
INNER JOIN v_hmm_valid_developers d ON w.developer_id = d.developer_id
""").fetchdf()


def _entropy(states: pd.Series) -> float:
    p = states.value_counts(normalize=True)
    return float(-(p * np.log2(p)).sum())


entropy_by_dev = (
    state_seq.groupby("developer_id")["hmm_hidden_state"]
    .apply(_entropy)
    .reset_index(name="hmm_state_entropy")
)
journey_base = journey_base.merge(entropy_by_dev, on="developer_id", how="left")

journey_base["journey_label"] = (
    journey_base["first_hmm_state_label"] + " -> " + journey_base["last_hmm_state_label"]
)

path_summary = (
    journey_base.groupby(
        [
            "stratum", "cluster_key", "persona_feature_name", "cluster_label_slide",
            "journey_label", "dominant_hmm_state_label",
        ],
        as_index=False,
    )
    .agg(
        n_developers=("developer_id", "count"),
        avg_state_probability=("avg_state_probability", "mean"),
        avg_hmm_state_entropy=("hmm_state_entropy", "mean"),
    )
)

path_summary["share_within_cluster"] = path_summary.groupby(["stratum", "cluster_key"])["n_developers"].transform(
    lambda s: s / s.sum()
)
path_summary["rank_within_cluster"] = path_summary.groupby(["stratum", "cluster_key"])["n_developers"].rank(
    ascending=False, method="first"
)

cluster_journey_paths_v2 = (
    path_summary[path_summary["rank_within_cluster"] <= 5]
    .sort_values(["stratum", "cluster_key", "n_developers"], ascending=[True, True, False])
    .reset_index(drop=True)
)

if WRITE_TABLES:
    con.register("_paths", cluster_journey_paths_v2)
    con.execute("CREATE OR REPLACE TABLE cluster_journey_paths_v2 AS SELECT * FROM _paths")
    con.unregister("_paths")

global_paths = (
    journey_base.groupby(["journey_label", "cluster_label_slide"], as_index=False)
    .size()
    .rename(columns={"size": "n_developers"})
    .sort_values("n_developers", ascending=False)
    .head(12)
)

fig, ax = plt.subplots(figsize=(12, 6))
plot_labels = []
for row in global_paths.itertuples():
    jl = row.journey_label if len(row.journey_label) <= 55 else row.journey_label[:52] + "..."
    plot_labels.append(f"{row.cluster_label_slide}\n{jl}")
ax.barh(plot_labels[::-1], global_paths["n_developers"].values[::-1], color=NVIDIA_GREEN)
ax.set_xlabel("Developers")
ax.set_title("Top Journey Paths (all valid HMM-scored developers)")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "cluster_top_journey_paths.png", bbox_inches="tight")
plt.show()

cluster_journey_paths_v2.to_csv(OUTPUT_DIR / "cluster_journey_paths_v2.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'cluster_journey_paths_v2.csv'}")
display(cluster_journey_paths_v2.head(15))
'''
set_cell("# 14.3 — journey paths per cluster", CELL_14_3)

# 14.5: use SPARSE threshold of 30 for annotation only, not exclusion
CELL_14_5_SPARSE = "SPARSE_CLUSTER_N = 30  # annotate only; analysis includes all valid developers\n\n"
for c in nb["cells"]:
    src = "".join(c.get("source", []))
    if src.startswith("# 14.5"):
        src = src.replace(
            "    if row[\"n_developers\"] < MIN_CLUSTER_N:\n        tags.append(\"sparse_cluster\")",
            "    if row[\"n_developers\"] < SPARSE_CLUSTER_N:\n        tags.append(\"sparse_cluster\")",
        )
        if "SPARSE_CLUSTER_N" not in src:
            src = src.replace("# 14.5 — cluster targeting profile\n", "# 14.5 — cluster targeting profile\n" + CELL_14_5_SPARSE)
        c["source"] = [src]
        break

# 14.6 coverage message
replace_in_cells(
    'sparse = cluster_targeting_profile_v2.query("n_developers < @MIN_CLUSTER_N")',
    'sparse = cluster_targeting_profile_v2.query("n_developers < @SPARSE_CLUSTER_N")',
)
replace_in_cells(
    'print(f"  Sparse clusters (n < {MIN_CLUSTER_N}): {len(sparse)}")',
    'print(f"  Sparse clusters (n < {SPARSE_CLUSTER_N}, annotated only): {len(sparse)}")',
)

nb_path.write_text(json.dumps(nb, indent=1))
print("Patched Section 14 for all valid HMM-scored developers")
