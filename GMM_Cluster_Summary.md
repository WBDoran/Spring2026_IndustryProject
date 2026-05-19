# GMM Developer Clustering — Summary

## What This Notebook Does

Fits a **Gaussian Mixture Model (GMM)** on NVIDIA developer activity data to group ~9.4M developers into behaviorally distinct segments. GMM is used as a structural comparison against the primary HMM clustering — same Gaussian emission family, but without the sequential (transition) component. If GMM and HMM produce similar groupings, the temporal structure in HMM is adding little; if they diverge, it is real signal.

Two parallel models are produced:
- **Developer-level GMM** — one row per developer, 40 lifetime features. Primary deliverable.
- **Weekly-emission GMM** — one row per developer-week, 7 weekly activity features. Direct analog to HMM emissions.

---

## Data

- **Source:** `developer_project.duckdb` (produced by `FeatureEngineering_v3.ipynb`)
- **Active developers fit:** 7,660,278 (developers with zero lifetime activity are excluded from the model and reattached afterward as the `unactivated` segment)
- **Features (40 total):** lifetime volume/breadth, effort scores, modality counts (build, champion, evaluate, etc.), recency/velocity, persona shares, and behavior flags

---

## Methodology

1. **Preprocessing** — log-transform raw counts, winsorize ratio features, StandardScaler. Float32 storage to manage memory on the full 9M-row dataset.
2. **BIC/AIC sweep** — fit GMM for k = 2 through 12 on a stratified 100k-row subsample using diagonal covariance (fast) to locate the elbow.
3. **Bayesian GMM sanity check** — `BayesianGaussianMixture` with a Dirichlet-process prior run at k_max = 20. The prior shrinks unused components; the effective count validates the BIC elbow choice.
4. **Final fit** — full-covariance GMM at the chosen k, refit on all 7.66M active developers.
5. **Weekly fit** — separate GMM on the 14.9M developer-week rows, elbow at k = 8.

---

## Key Results

### Component count selection

| Method | Suggested k |
|---|---|
| BIC geometric elbow | **5** |
| Bayesian GMM effective components | (run to validate) |

### Developer-level cluster assignments

| Cluster ID | Label | Size | Core profile |
|---|---|---|---|
| 0 | `dormant_cuda_tourists` | 53.8% | 64.5% CUDA persona; 85.5% dormant; low-medium effort; very long days-since-last-activity |
| 1 | `high_effort_at_risk_builders` | 11.7% | 80% high/very-high effort; heavy build + devzone activity; 40% at-risk, sliding toward churn |
| 2 | `elite_power_users` | 4.0% | Extreme NGC download, build, champion, API, forum activity; 73% high/very-high effort; top ecosystem tier |
| 3 | `low_effort_genai_tourists` | 26.0% | 46.8% GenAI; 99.7% Tourist lifecycle; 68.5% low effort; near-zero engagement across all modalities |
| 4 | `active_genai_api_discoverers` | 4.5% | Highest recent velocity (+4.65 SD); heavy API + discovery activity; 37.2% Active_Discover lifecycle |
| -1 | `unactivated` | 18.3% | Zero lifetime activity; held out of the model entirely |

### Weekly-emission GMM

Elbow at **k = 8** weekly behavioral states. Each developer is summarized by their modal weekly cluster, mean soft-probability profile, and a sequence string of weekly cluster IDs for temporal coherence analysis against HMM.

---

## Outputs Written to DuckDB

| Table | Granularity | Contents |
|---|---|---|
| `dev_gmm_clusters_v1` | One row per developer | Hard cluster ID, human label, max posterior, posterior entropy, soft probabilities (c0–c4) |
| `dev_gmm_weekly_clusters_v1` | One row per developer-week | Weekly cluster ID, max posterior, soft probabilities (c0–c7) |

Soft posteriors are preserved — unlike k-means or HMM Viterbi labels, they enable downstream uncertainty filtering and soft membership analysis.

---

## Model Artifacts

Fitted models are saved to `gmm_artifacts/` so profiling and downstream cells can be re-run without refitting:
- `gmm_developer_v1.joblib` — developer-level GMM + scaler + feature names
- `gmm_weekly_v1.joblib` — weekly GMM + scaler + feature names
