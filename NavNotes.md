# README

## NVIDIA Developer Lifecycle & Topic Modeling Pipeline

### Project Overview

This repository contains the final clustering and topic modeling workflows developed for the NVIDIA x Cal Poly MSBA industry project.

The project goal is to understand:

* developer engagement behavior
* lifecycle progression
* technology adoption patterns
* engagement-to-adoption conversion

across NVIDIA’s developer ecosystem.

The workflows are designed to:

* scale to ~9M developers
* remain interpretable for business stakeholders
* support reproducible analytics
* generate reusable outputs for downstream teams



# Main Notebooks



## 1. `clustering_v11_hdbscan_main_rule_dormant_skip_existing.ipynb`

### Purpose

Primary production lifecycle clustering pipeline.

This notebook performs:

* lifecycle-first segmentation
* HDBSCAN clustering on high-value active strata
* lightweight dormant segmentation
* DuckDB persistence
* resumable/restart-safe execution



### Final Methodology

| Stratum     | Method                  |
| -- | -- |
| active      | HDBSCAN                 |
| cooling     | HDBSCAN                 |
| at_risk     | HDBSCAN                 |
| dormant     | Rule-based segmentation |
| unactivated | Pseudo-group            |

The final pipeline intentionally avoids expensive dormant HDBSCAN because dormant users are:

* extremely large in volume
* behaviorally sparse
* low-value for dense clustering

This dramatically improves runtime and interpretability. 



### Key Features

* Full-population clustering (~9.3M developers)
* DuckDB persistence
* resumable clustering
* skip-existing logic
* cluster profile summaries
* business-ready outputs
* visualization support tables
* noise/outlier tracking



### Main Outputs

| Output                                                 | Description                               |
|  | -- |
| `dev_lifecycle_cluster_membership_v11_final`           | Final developer-level cluster assignments |
| `dev_lifecycle_cluster_membership_v11_profile_summary` | Cluster-level feature summaries           |
| `dev_lifecycle_cluster_run_stats_v11`                  | Run statistics and clustering diagnostics |



### Final Cluster Counts

| Stratum     | Clusters            |
| -- | - |
| active      | 6 + noise           |
| cooling     | 7 + noise           |
| at_risk     | 6 + noise           |
| dormant     | 3 rule-based groups |
| unactivated | pseudo-group        |



### Important Notes

* HDBSCAN noise is intentional and meaningful.
* PCA/UMAP visualizations are diagnostics only.
* Final business interpretation should occur at the profile-summary layer.
* Tiny or near-duplicate clusters may still be merged manually later. 



## 2. `clustering_final.ipynb`

### Purpose

Original clustering workflow / experimental reference notebook.

This notebook contains:

* earlier clustering experiments
* tuning history
* exploratory validation logic
* baseline clustering methodology

Useful for:

* historical comparison
* debugging
* understanding model evolution

Not intended as the final production pipeline.



## 3. `cluster_visualization_pca_umap.ipynb`

### Purpose

Visualization and interpretation notebook for the V11 clustering outputs.

This notebook:

* reads saved cluster membership tables
* joins cluster outputs back to developer profiles
* creates PCA + UMAP projections
* generates cluster diagnostics
* exports visualization samples

It does NOT rerun clustering. 



### Visualization Design

Main visualizations focus on:

* active
* cooling
* at_risk

because these are the actual modeled HDBSCAN strata.

Dormant and unactivated are excluded by default because they are:

* rule-based
* pseudo-groups
* not behaviorally clustered



### Main Outputs

| Output                                    | Description                   |
| -- | -- |
| `cluster_pca_coordinates_v11.csv`         | PCA embeddings                |
| `cluster_umap_coordinates_v11.csv`        | UMAP embeddings               |
| `cluster_visualization_sample_v11.csv`    | Sampled visualization dataset |
| `cluster_visualization_centroids_v11.csv` | Cluster centroid coordinates  |



### Visualization Features

The notebook visualizes behavioral features such as:

* activity velocity
* effort scores
* build behavior
* persona entropy
* modality diversity
* lifetime activity depth





## 4. `NVIDIA_topic_modeling_NMF.ipynb`

### Purpose

Latent developer ecosystem modeling using topic modeling.

This notebook treats:

* developers as documents
* activities/assets as tokens
* ecosystems as latent topics

using:

* TF-IDF
* NMF (Non-Negative Matrix Factorization)

instead of traditional clustering. 



### Why Topic Modeling?

Traditional clustering forces:

> one developer → one cluster

Topic modeling allows:

> one developer → multiple ecosystem memberships

Example:

* 40% GenAI
* 35% Robotics
* 25% CUDA

This better reflects real NVIDIA developer behavior.



### Current Modeling Scope

Included:

* activity tokens
* activity types
* asset/course tokens
* SDK integration scaffolding
* lightweight semantic token cleaning

Not included:

* large engineered feature matrices
* deep learning embeddings
* transformer models



### Topic Modeling Pipeline

```text
Developer Activity Logs
        ↓
Token Generation
        ↓
TF-IDF
        ↓
NMF Topic Modeling
        ↓
Developer Topic Mixtures
        ↓
Ecosystem Interpretation
```



### Main Outputs

| Output                       | Description                |
| - | -- |
| `developer_topic_scores.csv` | Developer topic mixtures   |
| `topic_terms.csv`            | Top terms per topic        |
| `topic_summary_template.csv` | Topic labeling template    |
| `model_comparison.csv`       | Topic-count tuning results |



### Example Ecosystems Identified

* GenAI / RAG workflows
* CUDA optimization
* Robotics / Jetson
* Deep learning foundations
* Inference deployment
* Omniverse / simulation
* Data science acceleration



### Important Current Limitation

`sdk_download_final` currently lacks developer-level IDs, so SDK tokens cannot yet fully join back to developers. The SDK token pipeline is scaffolded and ready once developer-level linkage becomes available. 



# Recommended Execution Order

## Lifecycle Clustering

1. Run `clustering_v11_hdbscan_main_rule_dormant_skip_existing.ipynb`
2. Verify final DuckDB tables exist
3. Run `cluster_visualization_pca_umap.ipynb`
4. Perform cluster interpretation/business labeling



## Topic Modeling

1. Run `NVIDIA_topic_modeling_NMF.ipynb`
2. Inspect topic terms
3. Assign topic labels
4. Join topic profiles back to developer profiles if needed



# Core Tables

| Table                                                  | Purpose                                  |
|  | - |
| `dev_profile_final_v4`                                 | Final engineered developer profile table |
| `activity_base_v2`                                     | Core activity dataset                    |
| `sdk_download_final`                                   | SDK download metadata                    |
| `dev_lifecycle_cluster_membership_v11_final`           | Final lifecycle cluster assignments      |
| `dev_lifecycle_cluster_membership_v11_profile_summary` | Cluster summaries                        |



# Key Modeling Philosophy

This project intentionally prioritizes:

* interpretability
* scalability
* business usability
* lifecycle understanding

over:

* excessive model complexity
* deep feature engineering
* black-box architectures

The final outputs are intended to support:

* developer cohort analysis
* adoption maturity analysis
* asset impact analysis
* retention/churn analysis
* ecosystem engagement mapping
* downstream business interpretation
