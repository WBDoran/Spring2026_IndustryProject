# Demographic Cluster Fingerprints — For GMM & LightGBM Verification Teams

## Purpose

Each HDBSCAN V11 cluster has a demographic signature. When the GMM verification team maps their GMM components to HDBSCAN clusters, use this table to check whether the demographic profile matches. If GMM Component X is mapped to `at_risk_2`, its developer population should look like: 41% India, 70% DLI, 64% deployment interest. If it doesn't, the mapping is wrong or the methods found different structure.

The LightGBM/XGBoost team can use this to annotate their feature importance outputs — if `lifetime_dli_training_count` is the top separator for a cluster that is 70% DLI-trained, the model and the demographics are telling the same story (verification passes).

---

## Fingerprint Table

| Cluster | Stratum | Size | Top Region (%) | Top Country (%) | Top Industry (%) | Top Entry (%) | Top Dev Areas |
|---|---|---|---|---|---|---|---|
| **active_0** | active | 18K | APAC 50%, EMEA 29% | China 28% | Academia 27%, Other 32% | devzone 98% | Agentic AI 49%, CV 21%, Simulation 16% |
| **active_1** | active | 67K | NALA 93% | US 92% | Other 93% | api_catalog 90% | Agentic AI 97% |
| **active_2** | active | 25K | APAC 47%, EMEA 32% | India 28% | Other 29%, Academia 24% | dli 71%, devzone 26% | Agentic AI 74%, Data Science 41%, CV 33% |
| **active_3** | active | 29K | NALA 96% | US 96% | Other 97% | api_catalog 95% | Agentic AI 97% |
| **active_4** | active | 19K | APAC 45%, NALA 36% | US 29% | Other 32%, Academia 11% | gtc 61%, devzone 21% | Agentic AI 82%, Robotics 33%, Dev Tools 31% |
| **active_5** | active | 155K | NALA 77% | US 76% | Other 83% | api_catalog 69%, gtc 17% | Agentic AI 84%, Data Center 8% |
| **active_noise** | active | 106K | NALA 43%, APAC 35% | US 39% | Other 53%, Academia 11% | devzone 35%, null 25% | Agentic AI 54%, CV 26%, Data Science 21% |
| **cooling_0** | cooling | 35K | NALA 50%, APAC 29% | US 47% | Other 57%, Academia 16% | devzone 39%, api_catalog 39% | Agentic AI 76%, CV 18% |
| **cooling_1** | cooling | 27K | APAC 56%, EMEA 26% | China 35% | Other 32%, Academia 29% | devzone 99% | Agentic AI 49%, CV 20% |
| **cooling_2** | cooling | 57K | APAC 38%, EMEA 29% | US 25% | Other 38%, Academia 20% | dli 58%, devzone 26% | Agentic AI 73%, Data Science 36%, CV 28% |
| **cooling_3** | cooling | 24K | APAC 47%, EMEA 27% | US 21% | Other 99% | null 97% | null 97% — GHOST CLUSTER |
| **cooling_4** | cooling | 23K | APAC 41%, NALA 30% | US 26% | Academia 27%, Other 22% | devzone 48%, gtc 26% | Agentic AI 85%, Simulation 47%, Robotics 46% |
| **cooling_5** | cooling | 83K | NALA 67% | US 65% | Other 79% | api_catalog 55%, gtc 14% | Agentic AI 72%, Data Center 8% |
| **cooling_6** | cooling | 25K | APAC 47%, EMEA 22% | US 21% | Other 46%, Academia 13% | devzone 40%, null 35% | Agentic AI 31%, CV 25%, Data Science 23% |
| **cooling_noise** | cooling | 81K | APAC 45%, NALA 28% | US 28% | Other 41%, Academia 15% | devzone 47%, null 18% | Agentic AI 46%, CV 33%, Data Science 24% |
| **at_risk_0** | at_risk | 436K | APAC 50%, NALA 26% | US 21% | Other 43%, Academia 20% | devzone 45%, dli 26% | Agentic AI 51%, CV 25%, Data Science 24% |
| **at_risk_1** | at_risk | 145K | APAC 60%, EMEA 24% | China 36% | Academia 32%, Other 27% | devzone 98% | Deployment 50%, Other 23%, CV 20% |
| **at_risk_2** | at_risk | 210K | APAC 60% | India 41% | Other 28%, Academia 20% | dli 70%, devzone 21% | Deployment 64%, Agentic AI 62%, Data Science 42% |
| **at_risk_3** | at_risk | 207K | APAC 42%, NALA 32% | US 32% | Other 42%, Academia 17% | devzone 34%, dli 31%, api_catalog 19% | Agentic AI 55%, Deployment 46%, Data Science 26% |
| **at_risk_4** | at_risk | 119K | APAC 52% | China 24% | Other 96% | null 96% — GHOST CLUSTER | null 89% |
| **at_risk_5** | at_risk | 366K | APAC 56% | China 25% | Other 35%, Academia 20% | devzone 54%, dli 14% | Deployment 36%, Agentic AI 33%, CV 31% |
| **at_risk_noise** | at_risk | 98K | APAC 40%, NALA 31% | US 31% | Other 41%, Academia 12% | devzone 27%, null 23% | Agentic AI 40%, CV 31%, Data Science 28% |
| **Dormant_Former_Builders** | dormant | 1.66M | APAC 54%, EMEA 26% | China 27% | Other 36%, Academia 17% | devzone 49%, null 40% | CV 34%, Data Science 30%, Conv. AI 23% |
| **Dormant_Low_Depth** | dormant | 2.47M | APAC 50%, EMEA 26% | China 19% | Other 37%, Academia 16% | null 49%, devzone 19% | Data Science 46%, CV 43%, Conv. AI 37% |
| **Dormant_One_Time_Users** | dormant | 1.18M | APAC 48%, EMEA 25% | India 18% | Other 41%, Academia 11% | null 40%, devzone 20%, gtc 20% | Data Science 28%, CV 23%, Conv. AI 21% |
| **unactivated** | unactivated | 1.72M | null dominant | null dominant | Other 69% | null 73%, devzone 23% | null 65%, Data Science 9% |

---

## How to Use This for GMM Verification

1. For each GMM component, get its demographic distribution (region, country, industry, entry channel, dev areas)
2. Find the HDBSCAN cluster in this table whose fingerprint is the closest match
3. Record: agree / partial agree / disagree
4. Clusters that both methods agree on = verified behavioral segments
5. Clusters where methods disagree = investigate whether HDBSCAN's lifecycle stratification is doing unique work

**Highest-confidence matches to look for first** (most demographically distinct, easiest to verify):
- `active_1` and `active_3`: ~93–96% US, ~90–95% api_catalog, ~97% Agentic AI — very distinctive
- `at_risk_1`: ~98% devzone, ~36% China, 32% Academia, 50% deployment — very distinctive
- `at_risk_2`: ~70% DLI, ~41% India, 64% deployment — very distinctive
- `cooling_3` and `at_risk_4`: ghost clusters — GMM should show high posterior entropy for these

---

## How to Use This for LightGBM/XGBoost Feature Importance Validation

Cross-reference the top features from each per-stratum model against the demographic fingerprint:

| If top feature is... | Should align with these clusters... | Demographic check |
|---|---|---|
| `lifetime_dli_training_count` | at_risk_2 (70% DLI), cooling_2 (58% DLI), active_2 (71% DLI) | DLI entry share |
| `lifetime_api_count` | active_1, active_3, active_5 (90–95% api_catalog) | api_catalog entry share |
| `log_activity_count_0_30d` | active_1, active_3, active_5 vs. cooling_5 | Separates active from cooling |
| `build_share_lifetime` | Dormant_Former_Builders (high historical build) | CV/Data Science dev areas |
| `persona_entropy` | active_2, active_4, cooling_4 (broadest dev area mix) | Multi-interest clusters |

If a feature that should separate DLI clusters doesn't rank highly in the at_risk model, flag it — either the feature is weak or the cluster boundaries shifted.
