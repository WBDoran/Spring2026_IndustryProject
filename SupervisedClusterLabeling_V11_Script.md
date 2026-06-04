# Slide Script - Supervised Cluster Labeling V11

---

While HDBSCAN gives us high-quality behavioral cohorts, rerunning clustering across millions of developers every time new data arrives would be computationally expensive.

To solve this, we trained supervised models to learn the V11 HDBSCAN cluster assignments. We built separate models for the Active, Cooling, and At-Risk strata and evaluated them on a holdout dataset.

All three strata achieved over 99.6% accuracy - Active at 99.87%, Cooling at 99.74%, and At-Risk at 99.64%. LightGBM was selected as the final production model.

This result matters for two reasons. First, it allows NVIDIA to automatically classify incoming developers into the existing lifecycle cohorts without rerunning the full clustering pipeline. Second, the fact that these models achieve such high accuracy using only a small set of behavioral features suggests the clusters are being driven by meaningful, interpretable signals rather than artifacts of the clustering algorithm itself.

In short, this transforms the framework from a one-time analysis into a scalable prediction system capable of continuously assigning new developers to the appropriate lifecycle cohort.

---
