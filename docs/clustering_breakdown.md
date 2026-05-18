# Clustering breakdown (Team 1)

**Pipeline:** [clustering_v2.ipynb](../clustering_v2.ipynb) — `dev_profile_final_v4` → median impute + `RobustScaler` → **SVD(50)** → **HDBSCAN**, run **separately** per dormancy stratum (`active`, `cooling`, `dormant`).

**Archive:** Exploratory work (UMAP-primary, method sweeps) is in [clustering_v1.ipynb](../clustering_v1.ipynb).

**Data:** `outputs/clustering/v2/cluster_summary_table_all.csv` (100k stratified sample per stratum).

---

## Run summary (clustering_v2)

| Stratum | Eligible population | Sample | Clusters (incl. noise row) | HDBSCAN noise % |
|---------|--------------------:|-------:|----------------------------:|----------------:|
| **active** | 418,049 | 99,999 | 58 | 25.4% |
| **cooling** | 356,500 | 100,000 | 38 | 30.23% |
| **dormant** | 5,304,852 | 100,000 | 42 | 41.49% |

**Method notes**

- Clustering uses **scaled behavioral features only**; persona, journey, and dormancy are for interpretation.

- **Cluster IDs are not comparable across strata** — use `(dormancy_segment, hdbscan_cluster)` or `behavioral_segment_name`.

- **Noise (-1)** = sparse feature-space region, not a behavioral segment.

---

## Team 1 checklist

| Deliverable | Status |
|-------------|--------|
| Clean numeric features | Done |
| Scale / transform skewed features | Done (`RobustScaler` + log/clipped in FE) |
| UMAP for visualization | Optional in v2 (`RUN_UMAP_VIZ`) |
| HDBSCAN on SVD of scaled features | Done (primary) |
| Cluster labels | `cluster_results_all.parquet`, DuckDB `developer_clusters_v2` |
| Cluster summary table | CSV + tables below |
| Short descriptions (Explorers, Learners, Builders, …) | Draft below — refine in Phase 2 |
---

## Segment overview by stratum

### Active

| Draft segment type | Clusters | Developers (sample) | Share of sample |
|--------------------|---------:|--------------------:|----------------:|
| Explorers | 48 | 64,386 | 64.4% |
| Builders | 5 | 5,421 | 5.4% |
| Learners | 5 | 4,791 | 4.8% |
| **Unclustered (noise)** | 1 | 25,401 | 25.4% |

### Cooling

| Draft segment type | Clusters | Developers (sample) | Share of sample |
|--------------------|---------:|--------------------:|----------------:|
| Cooling_Explorers | 28 | 55,202 | 55.2% |
| Cooling_Learners | 5 | 7,401 | 7.4% |
| Cooling_Builders | 5 | 7,164 | 7.2% |
| **Unclustered (noise)** | 1 | 30,233 | 30.2% |

### Dormant

| Draft segment type | Clusters | Developers (sample) | Share of sample |
|--------------------|---------:|--------------------:|----------------:|
| Explorers | 19 | 25,478 | 25.5% |
| Dormant_Former_Builders | 14 | 19,635 | 19.6% |
| Learners | 7 | 10,095 | 10.1% |
| Dormant_Former_Explorers | 2 | 3,302 | 3.3% |
| **Unclustered (noise)** | 1 | 41,490 | 41.5% |

---

## Cluster catalog (detail)

Material clusters (typically **n ≥ 500** in sample). Smaller clusters remain in the CSV for manual review.

## Active — Active (activated, Active dormancy, activity in last 30d)

Population **418,049** · Sample **99,999** · **58** clusters · **25.4%** noise

| Cluster | n | % sample | Draft label | Top persona | Journey (30d) | Lifecycle | Short description |
|--------:|--:|---------:|-------------|-------------|----------------|-----------|-------------------|
| 52 | 4,311 | 4.31% | Explorers | GenAI (87%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (87%), lifecycle Tourist. |
| 15 | 3,952 | 3.95% | Explorers | GenAI (98%) | Evaluator | Active_Discover | Moderately active (~14 events/30d); GenAI (98%), journey Evaluator, lifecycle Active_Discover. |
| 19 | 3,880 | 3.88% | Explorers | Unknown (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; Unknown (100%), lifecycle Tourist. |
| 13 | 3,062 | 3.06% | Explorers | CUDA (94%) | Learner | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; CUDA (94%), lifecycle Tourist. |
| 11 | 3,048 | 3.05% | Explorers | GenAI (95%) | Evaluator | Active_Discover | Moderately active (~10 events/30d); GenAI (95%), journey Evaluator, lifecycle Active_Discover. |
| 24 | 2,562 | 2.56% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 51 | 2,281 | 2.28% | Explorers | GenAI (93%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (93%), lifecycle Tourist. |
| 25 | 2,226 | 2.23% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 21 | 2,175 | 2.18% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 26 | 1,896 | 1.90% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 7 | 1,824 | 1.82% | Explorers | GenAI (97%) | Evaluator | Active_Discover | Moderately active (~6 events/30d); GenAI (97%), journey Evaluator, lifecycle Active_Discover. |
| 18 | 1,651 | 1.65% | Explorers | GenAI (89%) | Learner | Active_Discover | Active Explorers; GenAI (89%), journey Learner. |
| 10 | 1,629 | 1.63% | Builders | CUDA (60%) | Builder | Tourist | Active CUDA-leaning builders with recent build activity (~2 events/30d); CUDA (60%), journey Builder, lifecycle Tourist. |
| 56 | 1,573 | 1.57% | Explorers | GenAI (100%) | Evaluator | Active_Discover | Active Explorers; GenAI (100%), journey Evaluator. |
| 55 | 1,570 | 1.57% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~2 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 0 | 1,485 | 1.49% | Learners | Learning_Community (51%) | Evaluator | Tourist | Active learners with learn-stage history and recent touchpoints; Learning_Community (51%), journey Evaluator. |
| 20 | 1,424 | 1.42% | Explorers | Robotics (44%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; Robotics (44%), lifecycle Tourist. |
| 27 | 1,316 | 1.32% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 38 | 1,230 | 1.23% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 37 | 1,211 | 1.21% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 6 | 1,179 | 1.18% | Builders | CUDA (48%) | Builder | Tourist | Active CUDA-leaning builders with recent build activity (~2 events/30d); CUDA (48%), journey Builder, lifecycle Tourist. |
| 49 | 1,121 | 1.12% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 48 | 1,060 | 1.06% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 47 | 1,042 | 1.04% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 12 | 1,012 | 1.01% | Builders | CUDA (66%) | Builder | Tourist | Active CUDA-leaning builders with recent build activity (~2 events/30d); CUDA (66%), journey Builder, lifecycle Tourist. |
| 57 | 941 | 0.94% | Explorers | GenAI (99%) | Evaluator | Active_Discover | Light-touch active explorers (~2 events/30d), discover/evaluate heavy; GenAI (99%), lifecycle Active_Discover. |
| 43 | 934 | 0.93% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 31 | 928 | 0.93% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| 5 | 914 | 0.91% | Builders | CUDA (47%) | Builder | Tourist | Active CUDA-leaning builders with recent build activity (~2 events/30d); CUDA (47%), journey Builder, lifecycle Tourist. |
| 36 | 908 | 0.91% | Explorers | GenAI (100%) | Evaluator | Tourist | Light-touch active explorers (~1 events/30d), discover/evaluate heavy; GenAI (100%), lifecycle Tourist. |
| **-1 (noise)** | 25,401 | 25.40% | Unclustered_Noise | — | — | — | Sparse-region profiles that do not fit a stable dense cluster in this stratum. Often mixed high-activity signals; treat as review bucket, not a single persona segment. |

## Cooling — Cooling (activity fading; little/none in last 30d)

Population **356,500** · Sample **100,000** · **38** clusters · **30.23%** noise

| Cluster | n | % sample | Draft label | Top persona | Journey (30d) | Lifecycle | Short description |
|--------:|--:|---------:|-------------|-------------|----------------|-----------|-------------------|
| 14 | 7,191 | 7.19% | Cooling_Explorers | CUDA (96%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; CUDA (96%), lifecycle Tourist. |
| 19 | 4,185 | 4.18% | Cooling_Explorers | Unknown (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; Unknown (100%), lifecycle Tourist. |
| 37 | 3,272 | 3.27% | Cooling_Explorers | GenAI (86%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (86%), lifecycle Tourist. |
| 10 | 3,137 | 3.14% | Cooling_Explorers | GenAI (44%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (44%), lifecycle Tourist. |
| 35 | 3,122 | 3.12% | Cooling_Learners | GenAI (82%) | Cooling_Historically_Active | Tourist | Cooling learners with fading 30d activity; GenAI (82%), journey Cooling_Historically_Active, lifecycle Tourist. |
| 3 | 2,690 | 2.69% | Cooling_Explorers | GenAI (70%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (70%), lifecycle Tourist. |
| 33 | 2,684 | 2.68% | Cooling_Explorers | GenAI (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (100%), lifecycle Tourist. |
| 2 | 2,646 | 2.65% | Cooling_Explorers | GenAI (92%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (92%), lifecycle Tourist. |
| 11 | 2,486 | 2.49% | Cooling_Explorers | GenAI (43%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (43%), lifecycle Tourist. |
| 9 | 2,427 | 2.43% | Cooling_Explorers | CUDA (49%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; CUDA (49%), lifecycle Tourist. |
| 1 | 2,371 | 2.37% | Cooling_Explorers | Robotics (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; Robotics (100%), lifecycle Tourist. |
| 8 | 2,347 | 2.35% | Cooling_Explorers | CUDA (45%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; CUDA (45%), lifecycle Tourist. |
| 5 | 2,025 | 2.02% | Cooling_Builders | CUDA (60%) | Cooling_Historically_Active | Tourist | Cooling former builders: activity in 30–90d window, little in last 30d; CUDA/build history; ~84 days since last activity; CUDA (60%). |
| 6 | 1,750 | 1.75% | Cooling_Builders | CUDA (64%) | Cooling_Historically_Active | Tourist | Cooling former builders: activity in 30–90d window, little in last 30d; CUDA/build history; ~77 days since last activity; CUDA (64%). |
| 7 | 1,726 | 1.73% | Cooling_Builders | CUDA (54%) | Cooling_Historically_Active | Tourist | Cooling former builders: activity in 30–90d window, little in last 30d; CUDA/build history; ~69 days since last activity; CUDA (54%). |
| 22 | 1,601 | 1.60% | Cooling_Explorers | GenAI (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (100%), lifecycle Tourist. |
| 26 | 1,562 | 1.56% | Cooling_Explorers | GenAI (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (100%), lifecycle Tourist. |
| 20 | 1,494 | 1.49% | Cooling_Explorers | GenAI (84%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (84%), lifecycle Tourist. |
| 29 | 1,484 | 1.48% | Cooling_Explorers | GenAI (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (100%), lifecycle Tourist. |
| 25 | 1,462 | 1.46% | Cooling_Explorers | GenAI (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (100%), lifecycle Tourist. |
| 13 | 1,431 | 1.43% | Cooling_Learners | GenAI (70%) | Cooling_Historically_Active | Tourist | Cooling learners with fading 30d activity; GenAI (70%), journey Cooling_Historically_Active, lifecycle Tourist. |
| 28 | 1,379 | 1.38% | Cooling_Explorers | GenAI (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (100%), lifecycle Tourist. |
| 18 | 1,335 | 1.33% | Cooling_Explorers | CUDA (51%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; CUDA (51%), lifecycle Tourist. |
| 21 | 1,239 | 1.24% | Cooling_Explorers | GenAI (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (100%), lifecycle Tourist. |
| 27 | 1,115 | 1.11% | Cooling_Explorers | GenAI (100%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (100%), lifecycle Tourist. |
| 17 | 1,098 | 1.10% | Cooling_Explorers | GenAI (85%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (85%), lifecycle Tourist. |
| 4 | 985 | 0.98% | Cooling_Explorers | GenAI (51%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; GenAI (51%), lifecycle Tourist. |
| 36 | 970 | 0.97% | Cooling_Explorers | Unknown (41%) | Cooling_Historically_Active | Tourist | Cooling discover/evaluate profiles with sparse recent activity; Unknown (41%), lifecycle Tourist. |
| 16 | 967 | 0.97% | Cooling_Learners | Learning_Community (100%) | Cooling_Historically_Active | Tourist | Cooling learners with fading 30d activity; Learning_Community (100%), journey Cooling_Historically_Active, lifecycle Tourist. |
| 15 | 963 | 0.96% | Cooling_Learners | Learning_Community (100%) | Cooling_Historically_Active | Tourist | Cooling learners with fading 30d activity; Learning_Community (100%), journey Cooling_Historically_Active, lifecycle Tourist. |
| **-1 (noise)** | 30,233 | 30.23% | Unclustered_Noise | — | — | — | Sparse-region profiles that do not fit a stable dense cluster in this stratum. Often mixed high-activity signals; treat as review bucket, not a single persona segment. |

## Dormant — Dormant (long idle; historically may have been active)

Population **5,304,852** · Sample **100,000** · **42** clusters · **41.49%** noise

| Cluster | n | % sample | Draft label | Top persona | Journey (30d) | Lifecycle | Short description |
|--------:|--:|---------:|-------------|-------------|----------------|-----------|-------------------|
| 38 | 3,359 | 3.36% | Dormant_Former_Builders | CUDA (100%) | Dormant_Historically_Active | Dormant_Build | Long-idle with past build signals (lifetime build ~2); ~1169 days since last activity; CUDA (100%). |
| 3 | 3,002 | 3.00% | Explorers | CUDA (99%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~532 days since last activity; CUDA (99%). |
| 10 | 2,978 | 2.98% | Explorers | GenAI (100%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~862 days since last activity; GenAI (100%). |
| 16 | 2,859 | 2.86% | Learners | GenAI (100%) | Dormant_Historically_Active | Tourist | Dormant with learn history, little recent activity; GenAI (100%). |
| 31 | 2,316 | 2.32% | Dormant_Former_Builders | CUDA (100%) | Dormant_Historically_Active | Tourist | Long-idle with past build signals (lifetime build ~1); ~822 days since last activity; CUDA (100%). |
| 35 | 2,266 | 2.27% | Dormant_Former_Explorers | CUDA (100%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~1869 days since last activity; CUDA (100%). |
| 32 | 2,223 | 2.22% | Dormant_Former_Builders | CUDA (100%) | Dormant_Historically_Active | Tourist | Long-idle with past build signals (lifetime build ~1); ~816 days since last activity; CUDA (100%). |
| 19 | 2,108 | 2.11% | Dormant_Former_Builders | Simulation (100%) | Dormant_Historically_Active | Tourist | Long-idle with past build signals (lifetime build ~1); ~1531 days since last activity; Simulation (100%). |
| 37 | 1,699 | 1.70% | Explorers | CUDA (97%) | Dormant_Historically_Active | Dormant_Evaluate | Dormant discover/evaluate-heavy; minimal recent windows; ~1792 days since last activity; CUDA (97%). |
| 0 | 1,683 | 1.68% | Learners | Learning_Community (71%) | Dormant_Historically_Active | Tourist | Dormant with learn history, little recent activity; Learning_Community (71%). |
| 1 | 1,614 | 1.61% | Explorers | Simulation (100%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~1198 days since last activity; Simulation (100%). |
| 26 | 1,575 | 1.57% | Explorers | CUDA (86%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~1600 days since last activity; CUDA (86%). |
| 15 | 1,539 | 1.54% | Explorers | Unknown (100%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~537 days since last activity; Unknown (100%). |
| 8 | 1,488 | 1.49% | Explorers | GenAI (98%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~968 days since last activity; GenAI (98%). |
| 29 | 1,446 | 1.45% | Dormant_Former_Builders | CUDA (100%) | Dormant_Historically_Active | Tourist | Long-idle with past build signals (lifetime build ~1); ~870 days since last activity; CUDA (100%). |
| 7 | 1,423 | 1.42% | Explorers | GenAI (88%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~923 days since last activity; GenAI (88%). |
| 33 | 1,379 | 1.38% | Dormant_Former_Builders | CUDA (100%) | Dormant_Historically_Active | Tourist | Long-idle with past build signals (lifetime build ~1); ~818 days since last activity; CUDA (100%). |
| 14 | 1,301 | 1.30% | Explorers | Unknown (100%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~1302 days since last activity; Unknown (100%). |
| 24 | 1,228 | 1.23% | Learners | CUDA (42%) | Dormant_Historically_Active | Tourist | Dormant with learn history, little recent activity; CUDA (42%). |
| 5 | 1,207 | 1.21% | Learners | GenAI (46%) | Dormant_Historically_Active | Tourist | Dormant with learn history, little recent activity; GenAI (46%). |
| 27 | 1,172 | 1.17% | Explorers | CUDA (88%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~1196 days since last activity; CUDA (88%). |
| 17 | 1,138 | 1.14% | Learners | Learning_Community (74%) | Dormant_Historically_Active | Tourist | Dormant with learn history, little recent activity; Learning_Community (74%). |
| 6 | 1,106 | 1.11% | Learners | GenAI (68%) | Dormant_Historically_Active | Tourist | Dormant with learn history, little recent activity; GenAI (68%). |
| 39 | 1,036 | 1.04% | Dormant_Former_Explorers | CUDA (97%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~962 days since last activity; CUDA (97%). |
| 30 | 1,018 | 1.02% | Dormant_Former_Builders | Unknown (100%) | Dormant_Historically_Active | Tourist | Long-idle with past build signals (lifetime build ~1); ~1109 days since last activity; Unknown (100%). |
| 40 | 996 | 1.00% | Dormant_Former_Builders | CUDA (100%) | Dormant_Historically_Active | Tourist | Long-idle with past build signals (lifetime build ~2); ~861 days since last activity; CUDA (100%). |
| 25 | 990 | 0.99% | Explorers | CUDA (82%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~1556 days since last activity; CUDA (82%). |
| 13 | 970 | 0.97% | Explorers | GenAI (85%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~819 days since last activity; GenAI (85%). |
| 4 | 947 | 0.95% | Explorers | CUDA (100%) | Dormant_Historically_Active | Tourist | Dormant discover/evaluate-heavy; minimal recent windows; ~1761 days since last activity; CUDA (100%). |
| 23 | 925 | 0.93% | Dormant_Former_Builders | GenAI (59%) | Dormant_Historically_Active | Tourist | Long-idle with past build signals (lifetime build ~1); ~1496 days since last activity; GenAI (59%). |
| **-1 (noise)** | 41,490 | 41.49% | Unclustered_Noise | — | — | — | Sparse-region profiles that do not fit a stable dense cluster in this stratum. Often mixed high-activity signals; treat as review bucket, not a single persona segment. |

---

## How to refine labels (Phase 2)

1. Open `outputs/clustering/v2/cluster_summary_table_all.csv`.

2. Add `stakeholder_segment_name` for final Team 1 names.

3. Merge near-duplicate clusters (many active **Explorers** share ~1 event/30d).

4. **At_Risk** (~1.6M) not in v2 — add a stratum or rule-based bucket if needed.

---

## Output files

| File | Description |
|------|-------------|
| `outputs/clustering/v2/cluster_summary_table_all.csv` | Full cluster profiles |
| `outputs/clustering/v2/cluster_results_all.parquet` | Per-developer labels |
| `outputs/clustering/v2/run_summary.csv` | Run metrics per stratum |
| `outputs/clustering/v2/{stratum}/cluster_summary_table.csv` | Per-stratum summary |
---

## Archived experiments (clustering_v1)

Broad mixed cohort (~40% noise), UMAP→HDBSCAN primary, §9 parameter sweep, GMM/Leiden benchmarks. Superseded for Team 1 by **clustering_v2**. Section-by-section notes were in `docs/clustering_v1_breakdown.md` (now redirects here).

### Quick reference — v1 broad sample

| Run | Clusters | Noise % |
|-----|----------|---------|
| §3 UMAP → HDBSCAN | 27 | 40.3 |
| §8 Feature HDBSCAN | 46 | 39.4 |
| §4 SVD → HDBSCAN (same 100k) | ~53 | ~33 |
