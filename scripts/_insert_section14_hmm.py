#!/usr/bin/env python3
"""Insert Section 14 cells into NVIDIA_HMM_Journey_Analysis_v2.ipynb."""
import json
from pathlib import Path

nb_path = Path(__file__).resolve().parents[1] / "NVIDIA_HMM_Journey_Analysis_v2.ipynb"
nb = json.loads(nb_path.read_text())

if any("## 14. Cluster" in "".join(c.get("source", [])) for c in nb["cells"]):
    raise SystemExit("Section 14 already present — aborting insert to avoid duplicates.")


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": [text]}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [text],
    }


CELL_14_0 = r'''# 14.0 Standalone bootstrap
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DB_PATH = "developer_project.duckdb"
OUTPUT_DIR = Path("hmm_analysis_outputs_v2")
OUTPUT_DIR.mkdir(exist_ok=True)
MIN_CLUSTER_N = 30
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
    "dev_hmm_developer_journey_v1",
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

con.execute("""
CREATE OR REPLACE TEMP VIEW v_hmm_sample_with_persona AS
SELECT
    j.developer_id,
    j.n_weeks,
    j.first_hmm_state,
    j.last_hmm_state,
    j.dominant_hmm_state,
    j.first_week,
    j.last_week,
    j.avg_state_probability,
    j.hmm_state_entropy,
    j.stratum,
    j.cluster_key,
    j.adoption_direction,
    n.persona_feature_name,
    n.persona_technical_name,
    n.demographic_audience,
    n.demographic_archetypes,
    n.is_ghost_cluster,
    n.cluster_label_slide,
    n.cluster_label_combined
FROM dev_hmm_developer_journey_v1 j
JOIN dev_v11_cluster_names n
  USING (developer_id, stratum, cluster_key)
""")

n_sample = con.execute("SELECT COUNT(*) FROM v_hmm_sample_with_persona").fetchone()[0]
n_clusters_sample = con.execute("SELECT COUNT(DISTINCT cluster_key) FROM v_hmm_sample_with_persona").fetchone()[0]
n_clusters_full = con.execute(
    "SELECT COUNT(DISTINCT cluster_key) FROM dev_lifecycle_cluster_membership_v11_final"
).fetchone()[0]

print(f"HMM sample developers: {n_sample:,}")
print(f"Clusters in HMM sample: {n_clusters_sample} / {n_clusters_full} total V11 clusters")
print(f"MIN_CLUSTER_N for visuals: {MIN_CLUSTER_N}")
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
    INNER JOIN v_hmm_sample_with_persona s
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
    COUNT(DISTINCT developer_id) AS n_developers
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

eligible_clusters = (
    state_dist.groupby(["stratum", "cluster_key", "cluster_label_slide"], as_index=False)["n_developers"]
    .max()
    .query("n_developers >= @MIN_CLUSTER_N")
)

plot_df = state_dist.merge(
    eligible_clusters[["stratum", "cluster_key"]],
    on=["stratum", "cluster_key"],
    how="inner",
)

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
ax.set_title("HMM Weekly State Share by V11 Cluster (clusters with n >= MIN_CLUSTER_N)")
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

CELL_14_2 = r'''# 14.2 — latest HMM state mix by cluster
latest_mix = con.execute("""
WITH latest AS (
    SELECT
        w.developer_id,
        w.hmm_hidden_state,
        ROW_NUMBER() OVER (PARTITION BY w.developer_id ORDER BY w.week_start DESC) AS rn
    FROM dev_hmm_weekly_states_v1 w
    INNER JOIN v_hmm_sample_with_persona s
        ON w.developer_id = s.developer_id
),
latest_labeled AS (
    SELECT
        s.stratum,
        s.cluster_key,
        s.persona_feature_name,
        s.cluster_label_slide,
        l.hmm_hidden_state,
        lbl.hmm_state_label,
        l.developer_id
    FROM latest l
    JOIN v_hmm_sample_with_persona s
        ON l.developer_id = s.developer_id
    JOIN hmm_state_labels_v2_view lbl
        ON l.hmm_hidden_state = lbl.hmm_hidden_state
    WHERE l.rn = 1
)
SELECT
    stratum,
    cluster_key,
    persona_feature_name,
    cluster_label_slide,
    hmm_hidden_state,
    hmm_state_label,
    COUNT(*) AS n_developers
FROM latest_labeled
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY stratum, cluster_key, n_developers DESC
""").fetchdf()

latest_mix["share_within_cluster"] = (
    latest_mix.groupby(["stratum", "cluster_key"])["n_developers"].transform(lambda s: s / s.sum())
)

cluster_latest_hmm_state_mix_v2 = latest_mix.copy()

if WRITE_TABLES:
    con.register("_latest_mix", cluster_latest_hmm_state_mix_v2)
    con.execute("CREATE OR REPLACE TABLE cluster_latest_hmm_state_mix_v2 AS SELECT * FROM _latest_mix")
    con.unregister("_latest_mix")

cluster_sizes = (
    latest_mix.groupby(["stratum", "cluster_key", "cluster_label_slide"], as_index=False)["n_developers"]
    .sum()
)
top_clusters = (
    cluster_sizes.sort_values(["stratum", "n_developers"], ascending=[True, False])
    .groupby("stratum", as_index=False)
    .head(6)
)

plot_latest = latest_mix.merge(top_clusters[["stratum", "cluster_key"]], on=["stratum", "cluster_key"])
strata = sorted(plot_latest["stratum"].unique())
fig, axes = plt.subplots(1, len(strata), figsize=(5 * len(strata), 6), sharey=True)
if len(strata) == 1:
    axes = [axes]

for ax, stratum in zip(axes, strata):
    sub = plot_latest[plot_latest["stratum"] == stratum]
    pivot = sub.pivot_table(
        index="cluster_label_slide",
        columns="hmm_state_label",
        values="share_within_cluster",
        aggfunc="sum",
        fill_value=0,
    )
    bottom = np.zeros(len(pivot))
    for col in [c for c in state_label_order if c in pivot.columns]:
        ax.barh(pivot.index.astype(str), pivot[col].values, left=bottom, label=col)
        bottom += pivot[col].values
    ax.set_title(stratum)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of developers")

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=7, bbox_to_anchor=(0.5, -0.02))
fig.suptitle("Latest HMM State Mix — Top Clusters per Stratum", y=1.02)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "cluster_latest_hmm_state_mix.png", bbox_inches="tight")
plt.show()

latest_mix.to_csv(OUTPUT_DIR / "cluster_latest_hmm_state_mix_v2.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'cluster_latest_hmm_state_mix_v2.csv'}")
display(cluster_latest_hmm_state_mix_v2.head(12))
'''

CELL_14_3 = r'''# 14.3 — journey paths per cluster
journey_base = con.execute("""
SELECT
    s.*,
    lf.hmm_state_label AS first_hmm_state_label,
    ll.hmm_state_label AS last_hmm_state_label,
    ld.hmm_state_label AS dominant_hmm_state_label
FROM v_hmm_sample_with_persona s
JOIN hmm_state_labels_v2_view lf ON s.first_hmm_state = lf.hmm_hidden_state
JOIN hmm_state_labels_v2_view ll ON s.last_hmm_state = ll.hmm_hidden_state
JOIN hmm_state_labels_v2_view ld ON s.dominant_hmm_state = ld.hmm_hidden_state
""").fetchdf()

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

eligible = (
    journey_base.groupby(["cluster_key"], as_index=False)["developer_id"].count()
    .query("developer_id >= @MIN_CLUSTER_N")
)
global_paths = (
    journey_base.merge(eligible[["cluster_key"]], on="cluster_key")
    .groupby(["journey_label", "cluster_label_slide"], as_index=False)
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
ax.set_title("Top Journey Paths (eligible clusters, n >= MIN_CLUSTER_N)")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "cluster_top_journey_paths.png", bbox_inches="tight")
plt.show()

cluster_journey_paths_v2.to_csv(OUTPUT_DIR / "cluster_journey_paths_v2.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'cluster_journey_paths_v2.csv'}")
display(cluster_journey_paths_v2.head(15))
'''

CELL_14_4 = r'''# 14.4 — per-cluster transition top pairs
trans_raw = con.execute("""
WITH weekly AS (
    SELECT
        s.stratum,
        s.cluster_key,
        s.persona_feature_name,
        s.cluster_label_slide,
        w.developer_id,
        w.week_start,
        w.hmm_hidden_state AS from_state,
        LEAD(w.hmm_hidden_state) OVER (
            PARTITION BY w.developer_id ORDER BY w.week_start
        ) AS to_state
    FROM dev_hmm_weekly_states_v1 w
    INNER JOIN v_hmm_sample_with_persona s
        ON w.developer_id = s.developer_id
),
pairs AS (
    SELECT
        stratum,
        cluster_key,
        persona_feature_name,
        cluster_label_slide,
        from_state,
        to_state,
        COUNT(*) AS n_transitions
    FROM weekly
    WHERE to_state IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT
    p.stratum,
    p.cluster_key,
    p.persona_feature_name,
    p.cluster_label_slide,
    p.from_state,
    lf.hmm_state_label AS from_state_label,
    p.to_state,
    lt.hmm_state_label AS to_state_label,
    p.n_transitions
FROM pairs p
JOIN hmm_state_labels_v2_view lf ON p.from_state = lf.hmm_hidden_state
JOIN hmm_state_labels_v2_view lt ON p.to_state = lt.hmm_hidden_state
ORDER BY stratum, cluster_key, n_transitions DESC
""").fetchdf()

trans_raw["share_from_state_within_cluster"] = trans_raw.groupby(
    ["stratum", "cluster_key", "from_state"]
)["n_transitions"].transform(lambda s: s / s.sum())

trans_raw["transition_label"] = trans_raw["from_state_label"] + " -> " + trans_raw["to_state_label"]
trans_raw["rank_within_cluster"] = trans_raw.groupby(["stratum", "cluster_key"])["n_transitions"].rank(
    ascending=False, method="first"
)

cluster_transition_top_pairs_v2 = (
    trans_raw[trans_raw["rank_within_cluster"] <= 3]
    .sort_values(["stratum", "cluster_key", "n_transitions"], ascending=[True, True, False])
    .reset_index(drop=True)
)

if WRITE_TABLES:
    con.register("_trans", cluster_transition_top_pairs_v2)
    con.execute("CREATE OR REPLACE TABLE cluster_transition_top_pairs_v2 AS SELECT * FROM _trans")
    con.unregister("_trans")

EXEMPLAR_KEYS = ["active_5", "cooling_1", "at_risk_5", "at_risk_2", "Dormant_Former_Builders", "active_noise"]
exemplar = cluster_transition_top_pairs_v2[
    cluster_transition_top_pairs_v2["cluster_key"].isin(EXEMPLAR_KEYS)
].copy()

display(exemplar)

cluster_transition_top_pairs_v2.to_csv(OUTPUT_DIR / "cluster_transition_top_pairs_v2.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'cluster_transition_top_pairs_v2.csv'}")
'''

CELL_14_5 = r'''# 14.5 — cluster targeting profile

def top_journey_for_cluster(cluster_key):
    sub = cluster_journey_paths_v2[cluster_journey_paths_v2["cluster_key"] == cluster_key]
    if sub.empty:
        return None, None, np.nan
    row = sub.iloc[0]
    return row["journey_label"], row["dominant_hmm_state_label"], row["share_within_cluster"]


def top_transition_for_cluster(cluster_key):
    sub = cluster_transition_top_pairs_v2[cluster_transition_top_pairs_v2["cluster_key"] == cluster_key]
    if sub.empty:
        return None, np.nan
    row = sub.iloc[0]
    return row["transition_label"], row["share_from_state_within_cluster"]


def state_shares(cluster_key, states):
    sub = state_dist[state_dist["cluster_key"] == cluster_key]
    if sub.empty:
        return 0.0
    return sub[sub["hmm_hidden_state"].isin(states)]["share_within_cluster"].sum()


def latest_state_shares(cluster_key, states):
    sub = latest_mix[latest_mix["cluster_key"] == cluster_key]
    if sub.empty:
        return 0.0
    return sub[sub["hmm_hidden_state"].isin(states)]["share_within_cluster"].sum()


INTERVENTIONS = {
    "training_to_inactive": "Post-DLI deployment pathway / ship-to-prod nudge",
    "event_spike_dropoff": "Post-event 30-day activation journey (GTC / webinar follow-up)",
    "recoverable": "Win-back with NIM / Agentic AI tooling",
    "cooling_decline": "Re-engagement drip: light-touch eval → build milestone",
    "stable_engaged": "Deepen API usage / expand to production workflows",
    "sparse_cluster": "Insufficient sample — validate before targeting",
}

cluster_meta = (
    journey_base.groupby(
        ["stratum", "cluster_key", "persona_feature_name", "cluster_label_slide"],
        as_index=False,
    )
    .agg(n_developers=("developer_id", "count"))
)
demo_cols = journey_base[
    ["cluster_key", "demographic_audience", "demographic_archetypes", "is_ghost_cluster"]
].drop_duplicates("cluster_key")
cluster_meta = cluster_meta.merge(demo_cols, on="cluster_key", how="left")

rows = []
for _, row in cluster_meta.iterrows():
    ck = row["cluster_key"]
    tags = []

    if row["n_developers"] < MIN_CLUSTER_N:
        tags.append("sparse_cluster")

    engaged_share = state_shares(ck, {4, 5, 6})
    lapse_share = state_shares(ck, {0, 1})
    cooling_share = state_shares(ck, {3, 1})
    latest_recover = latest_state_shares(ck, {5, 6})

    if engaged_share >= 0.25 and lapse_share <= 0.55:
        tags.append("stable_engaged")
    if cooling_share >= 0.45:
        tags.append("cooling_decline")

    top_journey, top_dominant, top_journey_share = top_journey_for_cluster(ck)
    top_trans, top_trans_share = top_transition_for_cluster(ck)

    persona = (row["persona_feature_name"] or "").lower()
    if "training" in persona and top_journey and top_journey.startswith("Prior Active"):
        tags.append("training_to_inactive")
    if "event" in persona and top_journey and "Active Exploration Burst" in top_journey:
        tags.append("event_spike_dropoff")
    if row["stratum"] in {"at_risk", "cooling", "dormant"} and latest_recover >= 0.08:
        tags.append("recoverable")

    tags = list(dict.fromkeys(tags))
    primary_tag = tags[0] if tags else "mixed_pattern"

    intervention = INTERVENTIONS.get(primary_tag, "Review cluster journey mix before campaign design")

    rows.append({
        "stratum": row["stratum"],
        "cluster_key": ck,
        "persona_feature_name": row["persona_feature_name"],
        "cluster_label_slide": row["cluster_label_slide"],
        "demographic_audience": row["demographic_audience"],
        "demographic_archetypes": row["demographic_archetypes"],
        "is_ghost_cluster": row["is_ghost_cluster"],
        "n_developers": row["n_developers"],
        "journey_archetype_tags": "; ".join(tags) if tags else "mixed_pattern",
        "primary_journey_archetype": primary_tag,
        "top_journey_label": top_journey,
        "top_journey_share": top_journey_share,
        "top_dominant_state_label": top_dominant,
        "top_transition_label": top_trans,
        "top_transition_share": top_trans_share,
        "engaged_state_week_share": engaged_share,
        "lapse_state_week_share": lapse_share,
        "latest_recoverable_state_share": latest_recover,
        "suggested_intervention": intervention,
    })

cluster_targeting_profile_v2 = pd.DataFrame(rows).sort_values(
    ["stratum", "n_developers"], ascending=[True, False]
)

if WRITE_TABLES:
    con.register("_profile", cluster_targeting_profile_v2)
    con.execute("CREATE OR REPLACE TABLE cluster_targeting_profile_v2 AS SELECT * FROM _profile")
    con.unregister("_profile")

display(cluster_targeting_profile_v2)
cluster_targeting_profile_v2.to_csv(OUTPUT_DIR / "cluster_targeting_profile_v2.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'cluster_targeting_profile_v2.csv'}")
'''

CELL_14_6 = r'''# 14.6 — export all Section 14 artifacts
section14_tables = {
    "cluster_hmm_state_distribution_v2": cluster_hmm_state_distribution_v2,
    "cluster_latest_hmm_state_mix_v2": cluster_latest_hmm_state_mix_v2,
    "cluster_journey_paths_v2": cluster_journey_paths_v2,
    "cluster_transition_top_pairs_v2": cluster_transition_top_pairs_v2,
    "cluster_targeting_profile_v2": cluster_targeting_profile_v2,
}

manifest = []
for name, df in section14_tables.items():
    csv_path = OUTPUT_DIR / f"{name}.csv"
    pq_path = OUTPUT_DIR / f"{name}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(pq_path, index=False)
    manifest.append({"table_name": name, "rows": len(df), "csv": csv_path.as_posix(), "parquet": pq_path.as_posix()})
    print(f"Exported {name}: {len(df):,} rows")

manifest_df = pd.DataFrame(manifest)
manifest_df.to_csv(OUTPUT_DIR / "cluster_journey_analysis_manifest.csv", index=False)
display(manifest_df)

sparse = cluster_targeting_profile_v2.query("n_developers < @MIN_CLUSTER_N")
print("\nCoverage summary")
print(f"  Clusters profiled: {len(cluster_targeting_profile_v2)}")
print(f"  Sparse clusters (n < {MIN_CLUSTER_N}): {len(sparse)}")
if len(sparse):
    print("  Sparse cluster keys:", ", ".join(sparse["cluster_key"].tolist()))
'''

section14 = [
    md(
        "## 14. Cluster × Journey Targeting Analysis\n\n"
        "Combines **V11 HDBSCAN persona clusters** with **HMM weekly journey behavior** to identify "
        "cluster-specific journey patterns and targeting opportunities.\n\n"
        "Run **14.0** first (standalone-safe if v1 HMM parquets are loaded in DuckDB). "
        "Outputs land in `hmm_analysis_outputs_v2/`.\n\n"
        "**Note:** HMM data covers the **150K developer sample** only (~18 cluster keys appear in-sample). "
        "Clusters with fewer than `MIN_CLUSTER_N` developers are flagged as sparse."
    ),
    code(CELL_14_0),
    md(
        "### 14.1 Cluster HMM state distribution (time spent)\n\n"
        "Share of **weekly rows** in each HMM state, by V11 cluster (full observed timeline per developer)."
    ),
    code(CELL_14_1),
    md(
        "### 14.2 Latest HMM state by cluster (snapshot)\n\n"
        "Most recent weekly HMM state per developer — useful for **current** targeting signals."
    ),
    code(CELL_14_2),
    md(
        "### 14.3 Common journey paths per cluster\n\n"
        "Top **first → last** HMM state paths and dominant states within each cluster."
    ),
    code(CELL_14_3),
    md(
        "### 14.4 Per-cluster transition patterns\n\n"
        "Top outgoing HMM transitions computed from weekly sequences (not the global transition matrix)."
    ),
    code(CELL_14_4),
    md(
        "### 14.5 Journey archetype tags + targeting profile\n\n"
        "Rule-based journey archetypes and suggested intervention templates per cluster."
    ),
    code(CELL_14_5),
    md("### 14.6 Export cluster × journey outputs"),
    code(CELL_14_6),
]

insert_at = 27
for i, cell in enumerate(section14):
    nb["cells"].insert(insert_at + i, cell)

# Renumber close (now at insert_at + len(section14))
close_idx = insert_at + len(section14)
nb["cells"][close_idx]["source"] = ["## 15. Close connection\n"]

nb_path.write_text(json.dumps(nb, indent=1))
print(f"Inserted {len(section14)} cells at index {insert_at}. Total cells: {len(nb['cells'])}")
