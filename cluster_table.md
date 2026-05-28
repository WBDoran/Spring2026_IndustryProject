# GMM Stratified Cluster Summary

Total developers (lifecycle strata): 9,379,190

---

## Active Developers — 462,627 total

| Cluster ID | Cluster Label | Developers | % of Stratum | % of All |
|-----------|--------------|-----------|-------------|---------|
| c1 | active_c1 | 271,032 | 58.6% | 2.9% |
| c5 | active_c5 | 64,322 | 13.9% | 0.7% |
| c0 | active_c0 | 50,483 | 10.9% | 0.5% |
| c3 | active_c3 | 40,141 | 8.7% | 0.4% |
| c2 | active_c2 | 26,120 | 5.6% | 0.3% |
| c4 | active_c4 | 10,529 | 2.3% | 0.1% |

---

## At-Risk Developers — 393,892 total

| Cluster ID | Cluster Label | Developers | % of Stratum | % of All |
|-----------|--------------|-----------|-------------|---------|
| c1 | at_risk_c1 | 174,169 | 44.2% | 1.9% |
| c2 | at_risk_c2 | 92,560 | 23.5% | 1.0% |
| c0 | at_risk_c0 | 64,063 | 16.3% | 0.7% |
| c3 | at_risk_c3 | 63,100 | 16.0% | 0.7% |

---

## Dormant Developers — 1,717,692 total (rule-based segmentation)

| Segment | Developers | % of Stratum | % of All |
|---------|-----------|-------------|---------|
| low_effort_lapsed | 858,704 | 50.0% | 9.2% |
| mid_effort_lapsed | 687,155 | 40.0% | 7.3% |
| former_high_effort | 89,564 | 5.2% | 1.0% |
| former_power_builder | 82,269 | 4.8% | 0.9% |

---

## Weekly Activity Clusters — 9,751,800 unique developers across 14,908,480 developer-weeks

Weekly GMM (k=6) fitted on `dev_weekly_features_v2`. Each developer can appear in multiple weeks.

| Cluster ID | Developer-Weeks | % of Weeks | Unique Developers | % of Devs |
|-----------|----------------|-----------|------------------|---------|
| c1 | 8,573,107 | 57.5% | 4,275,288 | 43.8% |
| c5 | 2,590,322 | 17.4% | 2,563,181 | 26.3% |
| c0 | 2,076,084 | 13.9% | 1,912,254 | 19.6% |
| c2 | 1,368,065 | 9.2% | 893,501 | 9.2% |
| c3 | 270,592 | 1.8% | 92,635 | 0.9% |
| c4 | 30,310 | 0.2% | 14,941 | 0.2% |
| **TOTAL** | **14,908,480** | | **9,751,800** | |

---

## Slide Notes

In the slides I would like to add these tables in whatever way you think fits best. My main conclusion I want to draw out of this is that they line up with Peter's HDBSCAN methods and the clusters themselves are very similar. Feel free to include any tables you think fit or alter things around as necessary. The weekly tables are a side note that should only be included if we are able to run HMM.
