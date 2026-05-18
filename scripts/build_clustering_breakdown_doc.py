"""Build docs/clustering_breakdown.md from v2 cluster summary CSV."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "outputs/clustering/v2/cluster_summary_table_all.csv"
RUN_PATH = ROOT / "outputs/clustering/v2/run_summary.csv"
OUT_PATH = ROOT / "docs/clustering_breakdown.md"


def stakeholder_description(row) -> str:
    seg = row["dormancy_segment"]
    if row["noise_flag"]:
        return (
            "Sparse-region profiles that do not fit a stable dense cluster in this stratum. "
            "Often mixed high-activity signals; treat as review bucket, not a single persona segment."
        )

    name = str(row.get("behavioral_segment_name", "Segment"))
    persona = row.get("top_persona", "")
    pp = row.get("top_persona_pct", 0) or 0
    journey = row.get("top_journey_state_30d", "")
    life = row.get("top_lifecycle_status", "")
    act30 = row.get("mean_activity_count_0_30d", 0) or 0
    build30 = row.get("mean_build_count_0_30d", 0) or 0
    learn_lt = row.get("mean_lifetime_learn_count", 0) or 0
    build_lt = row.get("mean_lifetime_build_count", 0) or 0
    days = row.get("mean_days_since_last_activity", None)

    if seg == "active":
        if name == "Builders" and build30 >= 0.5:
            return (
                f"Active CUDA-leaning builders with recent build activity (~{act30:.0f} events/30d); "
                f"{persona} ({pp:.0f}%), journey {journey}, lifecycle {life}."
            )
        if name == "Learners" and learn_lt >= 0.5:
            return (
                f"Active learners with learn-stage history and recent touchpoints; "
                f"{persona} ({pp:.0f}%), journey {journey}."
            )
        if "Explorer" in name and act30 <= 2:
            return (
                f"Light-touch active explorers (~{act30:.0f} events/30d), discover/evaluate heavy; "
                f"{persona} ({pp:.0f}%), lifecycle {life}."
            )
        if act30 >= 5:
            return (
                f"Moderately active (~{act30:.0f} events/30d); {persona} ({pp:.0f}%), "
                f"journey {journey}, lifecycle {life}."
            )
        return f"Active {name.replace('_', ' ')}; {persona} ({pp:.0f}%), journey {journey}."

    if seg == "cooling":
        days_s = f"{days:.0f}" if pd.notna(days) else "—"
        if "Builder" in name:
            return (
                f"Cooling former builders: activity in 30–90d window, little in last 30d; "
                f"CUDA/build history; ~{days_s} days since last activity; {persona} ({pp:.0f}%)."
            )
        if "Learner" in name:
            return (
                f"Cooling learners with fading 30d activity; {persona} ({pp:.0f}%), "
                f"journey {journey}, lifecycle {life}."
            )
        if "Explorer" in name:
            return (
                f"Cooling discover/evaluate profiles with sparse recent activity; "
                f"{persona} ({pp:.0f}%), lifecycle {life}."
            )
        return f"Cooling {name.replace('Cooling_', '').replace('_', ' ')}; {persona} ({pp:.0f}%)."

    if seg == "dormant":
        days_s = f"{days:.0f}" if pd.notna(days) else "—"
        if "Former_Builder" in name or name == "Builders":
            return (
                f"Long-idle with past build signals (lifetime build ~{build_lt:.0f}); "
                f"~{days_s} days since last activity; {persona} ({pp:.0f}%)."
            )
        if "Former_Explorer" in name or name == "Explorers":
            return (
                f"Dormant discover/evaluate-heavy; minimal recent windows; "
                f"~{days_s} days since last activity; {persona} ({pp:.0f}%)."
            )
        if name == "Learners":
            return f"Dormant with learn history, little recent activity; {persona} ({pp:.0f}%)."
        return f"Dormant {name}; {persona} ({pp:.0f}%), journey {journey}."

    return str(row.get("segment_description", ""))


def cluster_table_md(sub_df: pd.DataFrame, min_n: int = 500, max_rows: int = 30) -> str:
    sub_df = sub_df.sort_values(["noise_flag", "n"], ascending=[True, False])
    lines = [
        "| Cluster | n | % sample | Draft label | Top persona | Journey (30d) | Lifecycle | Short description |",
        "|--------:|--:|---------:|-------------|-------------|----------------|-----------|-------------------|",
    ]
    shown = 0
    for _, r in sub_df.iterrows():
        if r["noise_flag"] == 0 and r["n"] < min_n and shown >= max_rows:
            continue
        if shown >= max_rows and r["noise_flag"] == 0:
            break
        desc = stakeholder_description(r).replace("|", "/")
        lines.append(
            f"| {int(r['hdbscan_cluster'])} | {int(r['n']):,} | {r['pct_of_sample']:.2f}% | "
            f"{r['behavioral_segment_name']} | {r.get('top_persona', '')} "
            f"({r.get('top_persona_pct', 0):.0f}%) | {r.get('top_journey_state_30d', '')} | "
            f"{r.get('top_lifecycle_status', '')} | {desc} |"
        )
        shown += 1

    noise = sub_df[sub_df["noise_flag"] == 1]
    if len(noise):
        r = noise.iloc[0]
        desc = stakeholder_description(r).replace("|", "/")
        lines.append(
            f"| **-1 (noise)** | {int(r['n']):,} | {r['pct_of_sample']:.2f}% | "
            f"Unclustered_Noise | — | — | — | {desc} |"
        )

    small = len(sub_df[(sub_df["noise_flag"] == 0) & (sub_df["n"] < min_n)])
    if small:
        lines.append(
            f"\n*Plus {small} smaller clusters (n < {min_n:,}) — see "
            f"`outputs/clustering/v2/cluster_summary_table_all.csv`.*"
        )
    return "\n".join(lines)


def main() -> None:
    df = pd.read_csv(CSV_PATH)
    run_df = pd.read_csv(RUN_PATH)

    parts: list[str] = [
        "# Clustering breakdown (Team 1)\n",
        "**Pipeline:** [clustering_v2.ipynb](../clustering_v2.ipynb) — "
        "`dev_profile_final_v4` → median impute + `RobustScaler` → **SVD(50)** → **HDBSCAN**, "
        "run **separately** per dormancy stratum (`active`, `cooling`, `dormant`).\n",
        "**Archive:** Exploratory work (UMAP-primary, method sweeps) is in "
        "[clustering_v1.ipynb](../clustering_v1.ipynb).\n",
        "**Data:** `outputs/clustering/v2/cluster_summary_table_all.csv` "
        "(100k stratified sample per stratum).\n",
        "---\n",
        "## Run summary (clustering_v2)\n",
        "| Stratum | Eligible population | Sample | Clusters (incl. noise row) | HDBSCAN noise % |",
        "|---------|--------------------:|-------:|----------------------------:|----------------:|",
    ]

    for _, r in run_df.iterrows():
        parts.append(
            f"| **{r['stratum_key']}** | {int(r['cohort_n']):,} | {int(r['sample_n']):,} | "
            f"{int(r['n_clusters'])} | {r['noise_pct']}% |"
        )

    parts.extend(
        [
            "\n**Method notes**\n",
            "- Clustering uses **scaled behavioral features only**; persona, journey, and dormancy are for interpretation.\n",
            "- **Cluster IDs are not comparable across strata** — use `(dormancy_segment, hdbscan_cluster)` or `behavioral_segment_name`.\n",
            "- **Noise (-1)** = sparse feature-space region, not a behavioral segment.\n",
            "---\n",
            "## Team 1 checklist\n",
            "| Deliverable | Status |",
            "|-------------|--------|",
            "| Clean numeric features | Done |",
            "| Scale / transform skewed features | Done (`RobustScaler` + log/clipped in FE) |",
            "| UMAP for visualization | Optional in v2 (`RUN_UMAP_VIZ`) |",
            "| HDBSCAN on SVD of scaled features | Done (primary) |",
            "| Cluster labels | `cluster_results_all.parquet`, DuckDB `developer_clusters_v2` |",
            "| Cluster summary table | CSV + tables below |",
            "| Short descriptions (Explorers, Learners, Builders, …) | Draft below — refine in Phase 2 |",
            "---\n",
            "## Segment overview by stratum\n",
        ]
    )

    for seg in ["active", "cooling", "dormant"]:
        sub = df[df["dormancy_segment"] == seg]
        sub_labeled = sub[sub["noise_flag"] == 0]
        parts.append(f"### {seg.capitalize()}\n")
        parts.append(
            "| Draft segment type | Clusters | Developers (sample) | Share of sample |"
        )
        parts.append("|--------------------|---------:|--------------------:|----------------:|")
        agg = (
            sub_labeled.groupby("behavioral_segment_name", observed=True)
            .agg(n_clusters=("hdbscan_cluster", "nunique"), n=("n", "sum"))
            .sort_values("n", ascending=False)
        )
        total = sub["n"].sum()
        for name, row in agg.iterrows():
            parts.append(
                f"| {name} | {int(row['n_clusters'])} | {int(row['n']):,} | "
                f"{100 * row['n'] / total:.1f}% |"
            )
        noise_n = sub.loc[sub["noise_flag"] == 1, "n"].sum()
        parts.append(
            f"| **Unclustered (noise)** | 1 | {int(noise_n):,} | {100 * noise_n / total:.1f}% |"
        )
        parts.append("")

    parts.extend(
        [
            "---\n",
            "## Cluster catalog (detail)\n",
            "Material clusters (typically **n ≥ 500** in sample). Smaller clusters remain in the CSV for manual review.\n",
        ]
    )

    titles = {
        "active": "Active (activated, Active dormancy, activity in last 30d)",
        "cooling": "Cooling (activity fading; little/none in last 30d)",
        "dormant": "Dormant (long idle; historically may have been active)",
    }
    for seg in ["active", "cooling", "dormant"]:
        r = run_df[run_df["stratum_key"] == seg].iloc[0]
        parts.append(f"## {seg.capitalize()} — {titles[seg]}\n")
        parts.append(
            f"Population **{int(r['cohort_n']):,}** · Sample **{int(r['sample_n']):,}** · "
            f"**{int(r['n_clusters'])}** clusters · **{r['noise_pct']}%** noise\n"
        )
        sub = df[df["dormancy_segment"] == seg]
        parts.append(cluster_table_md(sub, min_n=500, max_rows=30))
        parts.append("")

    parts.extend(
        [
            "---\n",
            "## How to refine labels (Phase 2)\n",
            "1. Open `outputs/clustering/v2/cluster_summary_table_all.csv`.\n",
            "2. Add `stakeholder_segment_name` for final Team 1 names.\n",
            "3. Merge near-duplicate clusters (many active **Explorers** share ~1 event/30d).\n",
            "4. **At_Risk** (~1.6M) not in v2 — add a stratum or rule-based bucket if needed.\n",
            "---\n",
            "## Output files\n",
            "| File | Description |",
            "|------|-------------|",
            "| `outputs/clustering/v2/cluster_summary_table_all.csv` | Full cluster profiles |",
            "| `outputs/clustering/v2/cluster_results_all.parquet` | Per-developer labels |",
            "| `outputs/clustering/v2/run_summary.csv` | Run metrics per stratum |",
            "| `outputs/clustering/v2/{stratum}/cluster_summary_table.csv` | Per-stratum summary |",
            "---\n",
            "## Archived experiments (clustering_v1)\n",
            "Broad mixed cohort (~40% noise), UMAP→HDBSCAN primary, §9 parameter sweep, GMM/Leiden benchmarks. "
            "Superseded for Team 1 by **clustering_v2**. Section-by-section notes were in "
            "`docs/clustering_v1_breakdown.md` (now redirects here).\n",
            "### Quick reference — v1 broad sample\n",
            "| Run | Clusters | Noise % |",
            "|-----|----------|---------|",
            "| §3 UMAP → HDBSCAN | 27 | 40.3 |",
            "| §8 Feature HDBSCAN | 46 | 39.4 |",
            "| §4 SVD → HDBSCAN (same 100k) | ~53 | ~33 |",
        ]
    )

    OUT_PATH.write_text("\n".join(parts) + "\n")
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
