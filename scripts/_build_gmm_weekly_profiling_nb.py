#!/usr/bin/env python3
"""Generate gmm_weekly_cluster_profiling.ipynb."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "gmm_weekly_cluster_profiling.ipynb"


def md(s: str):
    return {"cell_type": "markdown", "metadata": {}, "source": [s + "\n"]}


def code(s: str):
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [line + "\n" for line in s.strip("\n").splitlines()],
    }


CELL_COLAB = """
# from google.colab import drive
# drive.mount('/content/drive')
# PROJECT_DIR = "/content/drive/MyDrive/NVIDIA Industry Project"
PROJECT_DIR = "."
print("PROJECT_DIR:", PROJECT_DIR)
"""

CELL_IMPORTS = """
from pathlib import Path
import warnings

import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 200)

PROJECT_DIR = Path(PROJECT_DIR)
DB_PATH = PROJECT_DIR / "developer_project.duckdb"
PARQUET_DIR = PROJECT_DIR
OUTPUT_DIR = PROJECT_DIR / "outputs" / "gmm_weekly_cluster_profiling"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GMM_TABLE = "dev_gmm_weekly_clusters_v1"
WEEKLY_TABLE = "dev_weekly_features_v2"
V11_TABLE = "dev_lifecycle_cluster_membership_v11_final"

print("OUTPUT_DIR:", OUTPUT_DIR.resolve())
"""

CELL_CONNECT = """
con = duckdb.connect(str(DB_PATH))


def table_exists(name: str) -> bool:
    return con.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema='main' AND table_name='" + name + "'"
    ).fetchone()[0] > 0


def load_parquet(table: str) -> None:
    path = PARQUET_DIR / f"{table}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    sql = (
        "CREATE OR REPLACE TABLE " + table + " AS "
        "SELECT * FROM read_parquet('" + path.as_posix() + "')"
    )
    con.execute(sql)
    print("Loaded", path.name)


for t in [GMM_TABLE, WEEKLY_TABLE]:
    if not table_exists(t):
        load_parquet(t)

if not table_exists(V11_TABLE):
    v11_path = PARQUET_DIR / f"{V11_TABLE}.parquet"
    if v11_path.exists():
        load_parquet(V11_TABLE)
    else:
        print("V11 final table not found; stratum breakdown will be skipped.")

print("Tables ready.")
"""

CELL_JOIN = """
con.execute(\"\"\"
CREATE OR REPLACE TEMP TABLE gmm_weekly_profile_base AS
SELECT
    g.developer_id,
    CAST(g.week_start AS DATE) AS week_start,
    CAST(g.gmm_weekly_cluster_id AS INTEGER) AS gmm_weekly_cluster_id,
    CAST(g.gmm_weekly_max_posterior AS DOUBLE) AS gmm_weekly_max_posterior,
    CAST(g.gmm_weekly_prob_c0 AS DOUBLE) AS gmm_weekly_prob_c0,
    CAST(g.gmm_weekly_prob_c1 AS DOUBLE) AS gmm_weekly_prob_c1,
    CAST(g.gmm_weekly_prob_c2 AS DOUBLE) AS gmm_weekly_prob_c2,
    CAST(w.activity_count_total AS DOUBLE) AS activity_count_total,
    CAST(w.activity_score_sum AS DOUBLE) AS activity_score_sum,
    CAST(w.unique_activity_types AS DOUBLE) AS unique_activity_types,
    CAST(w.build_count AS DOUBLE) AS build_count,
    CAST(w.champion_count AS DOUBLE) AS champion_count,
    CAST(w.high_effort_count AS DOUBLE) AS high_effort_count,
    CAST(w.product_use_count AS DOUBLE) AS product_use_count
FROM dev_gmm_weekly_clusters_v1 g
INNER JOIN dev_weekly_features_v2 w
  ON CAST(g.developer_id AS VARCHAR) = CAST(w.developer_id AS VARCHAR)
 AND CAST(g.week_start AS DATE) = CAST(w.week_start AS DATE)
\"\"\")

overview = con.execute(\"\"\"
SELECT
    COUNT(*) AS joined_week_rows,
    COUNT(DISTINCT developer_id) AS developers,
    MIN(week_start) AS min_week,
    MAX(week_start) AS max_week,
    COUNT(DISTINCT gmm_weekly_cluster_id) AS n_gmm_clusters
FROM gmm_weekly_profile_base
\"\"\").fetchdf()
display(overview)

gmm_only = con.execute(\"\"\"
SELECT
    gmm_weekly_cluster_id,
    COUNT(*) AS n_weeks,
    COUNT(DISTINCT developer_id) AS n_developers,
    AVG(gmm_weekly_max_posterior) AS avg_posterior,
    MEDIAN(gmm_weekly_max_posterior) AS med_posterior
FROM gmm_weekly_profile_base
GROUP BY 1
ORDER BY 1
\"\"\").fetchdf()
display(gmm_only)
"""

CELL_PROFILE = """
profile_mean = con.execute(\"\"\"
SELECT
    gmm_weekly_cluster_id,
    COUNT(*) AS n_weeks,
    COUNT(DISTINCT developer_id) AS n_developers,
    AVG(gmm_weekly_max_posterior) AS avg_posterior,
    AVG(activity_count_total) AS avg_activity_count,
    MEDIAN(activity_count_total) AS med_activity_count,
    AVG(activity_score_sum) AS avg_activity_score,
    MEDIAN(activity_score_sum) AS med_activity_score,
    AVG(unique_activity_types) AS avg_unique_types,
    AVG(build_count) AS avg_build_count,
    AVG(champion_count) AS avg_champion_count,
    AVG(high_effort_count) AS avg_high_effort_count,
    AVG(product_use_count) AS avg_product_use_count,
    AVG(CASE WHEN activity_count_total = 0 THEN 1.0 ELSE 0.0 END) AS pct_zero_activity_weeks,
    AVG(build_count / NULLIF(activity_count_total, 0)) AS avg_build_share,
    AVG(high_effort_count / NULLIF(activity_count_total, 0)) AS avg_high_effort_share,
    AVG(product_use_count / NULLIF(activity_count_total, 0)) AS avg_product_use_share
FROM gmm_weekly_profile_base
GROUP BY 1
ORDER BY 1
\"\"\").fetchdf()

display(profile_mean)
profile_mean.to_csv(OUTPUT_DIR / "gmm_weekly_cluster_profile_mean.csv", index=False)
"""

CELL_HEATMAP = """
feature_cols = [
    "avg_activity_count",
    "avg_activity_score",
    "avg_unique_types",
    "avg_build_count",
    "avg_champion_count",
    "avg_high_effort_count",
    "avg_product_use_count",
    "avg_build_share",
    "avg_high_effort_share",
    "avg_product_use_share",
    "avg_posterior",
]

heat = profile_mean.set_index("gmm_weekly_cluster_id")[feature_cols].astype(float)
heat_z = (heat - heat.mean()) / heat.std(ddof=0).replace(0, np.nan)
heat_z = heat_z.fillna(0.0)

fig, ax = plt.subplots(figsize=(10, 3.5))
im = ax.imshow(heat_z.values, aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2)
ax.set_xticks(range(len(feature_cols)))
ax.set_xticklabels(feature_cols, rotation=45, ha="right")
ax.set_yticks(range(len(heat_z)))
ax.set_yticklabels([f"GMM {i}" for i in heat_z.index])
ax.set_title("Weekly GMM clusters — z-scored mean features")
plt.colorbar(im, ax=ax, label="z-score")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "gmm_weekly_cluster_feature_heatmap.png", dpi=150, bbox_inches="tight")
plt.show()

heat_z.to_csv(OUTPUT_DIR / "gmm_weekly_cluster_feature_heatmap_z.csv")
"""

CELL_STRATUM = """
if table_exists(V11_TABLE):
    mix = con.execute(f'''
    SELECT
        c.stratum,
        b.gmm_weekly_cluster_id,
        COUNT(*) AS n_weeks,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY c.stratum) AS share_within_stratum
    FROM gmm_weekly_profile_base b
    INNER JOIN {V11_TABLE} c
      ON CAST(b.developer_id AS VARCHAR) = CAST(c.developer_id AS VARCHAR)
    WHERE lower(c.stratum) IN ('active', 'cooling', 'at_risk')
    GROUP BY 1, 2
    ORDER BY 1, 2
    ''').fetchdf()
    display(mix.pivot(index="stratum", columns="gmm_weekly_cluster_id", values="share_within_stratum").round(3))
    mix.to_csv(OUTPUT_DIR / "gmm_weekly_cluster_by_stratum.csv", index=False)
else:
    print("Skipping stratum mix — V11 final table not available.")
"""

CELL_NAMES = """
rank_df = profile_mean.copy()
rank_df["intensity_score"] = (
    rank_df["avg_activity_count"].rank(pct=True)
    + rank_df["avg_activity_score"].rank(pct=True)
    + rank_df["avg_high_effort_count"].rank(pct=True)
    + rank_df["avg_build_count"].rank(pct=True)
)
rank_df = rank_df.sort_values("intensity_score")

name_map = {}
ordered = rank_df["gmm_weekly_cluster_id"].tolist()
if len(ordered) == 3:
    name_map[ordered[0]] = "light_active_week"
    name_map[ordered[1]] = "moderate_active_week"
    name_map[ordered[2]] = "high_intensity_week"
else:
    for i, cid in enumerate(ordered):
        name_map[cid] = f"gmm_cluster_{cid}"

suggestions = profile_mean.copy()
suggestions["provisional_name"] = suggestions["gmm_weekly_cluster_id"].map(name_map)
suggestions["intensity_rank"] = suggestions["gmm_weekly_cluster_id"].map(
    {cid: i + 1 for i, cid in enumerate(ordered)}
)

display(suggestions[[
    "gmm_weekly_cluster_id",
    "provisional_name",
    "intensity_rank",
    "n_weeks",
    "avg_activity_count",
    "avg_activity_score",
    "avg_build_count",
    "avg_high_effort_count",
    "pct_zero_activity_weeks",
    "avg_posterior",
]])

suggestions.to_csv(OUTPUT_DIR / "gmm_weekly_cluster_name_suggestions.csv", index=False)
print("Saved outputs to", OUTPUT_DIR.resolve())
"""

cells = [
    md(
        """# GMM Weekly Cluster Profiling

Profile `dev_gmm_weekly_clusters_v1` against `dev_weekly_features_v2` to assign business-friendly names to weekly GMM clusters **0, 1, 2**.

**Note:** This is separate from HMM hidden states and from explicit missing weeks (`-1` in categorical HMM gap-filling).

Runs locally or in Colab (Drive parquets + optional DuckDB)."""
    ),
    md("## 1) Colab setup (optional)"),
    code(CELL_COLAB),
    code("# !pip install duckdb pandas numpy matplotlib pyarrow"),
    code(CELL_IMPORTS),
    md("## 2) Connect and load tables"),
    code(CELL_CONNECT),
    md("## 3) Join GMM weekly assignments to weekly features (SQL aggregates)"),
    code(CELL_JOIN),
    md("## 4) Cluster behavioral profiles (mean + median)"),
    code(CELL_PROFILE),
    md("## 5) Heatmap (z-scored feature means)"),
    code(CELL_HEATMAP),
    md("## 6) GMM cluster mix by lifecycle stratum (optional)"),
    code(CELL_STRATUM),
    md("## 7) Suggested provisional names (edit after review)"),
    code(CELL_NAMES),
    md(
        """## 8) Notes for interpretation

- **GMM clusters** apply only to developer-weeks present in `dev_gmm_weekly_clusters_v1` (observed weekly rows).
- **Missing/no-activity weeks** in categorical HMM are a separate explicit category (`-1`), not GMM cluster 2 by default.
- Revisit `provisional_name` after reviewing heatmap and stratum mix; rename in HMM README/notebooks as needed."""
    ),
    code("# con.close()  # optional"),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT.write_text(json.dumps(nb, indent=1))
print("Wrote", OUT)
