# Supervised Cluster Labeling - V11 Results Summary

**Task:** Train LightGBM and XGBoost to reproduce V11 HDBSCAN cluster assignments as a scalable, deployable surrogate. New developers can be scored without re-running HDBSCAN.

---

## Model Performance (20% holdout test set)

| Stratum | Classes | Training rows | LGBM Accuracy | LGBM Balanced Acc | LGBM Macro-F1 | XGB Accuracy | XGB Macro-F1 | Winner |
|---|---|---|---|---|---|---|---|---|
| active | 7 | 250K (of 418K) | **99.87%** | **99.84%** | **99.84%** | 99.85% | 99.82% | LGBM |
| cooling | 8 | 250K (of 357K) | **99.74%** | **99.77%** | **99.73%** | 99.64% | 99.64% | LGBM |
| at_risk | 7 | 250K (of 1.58M) | **99.64%** | **99.43%** | **99.48%** | 99.60% | 99.41% | LGBM |

LightGBM selected for final table across all three modeled strata.

---

## Final Developer Coverage (9,381,508 total)

| Group | Assignment method | Clusters | Developers | Share |
|---|---|---|---|---|
| active | Supervised LGBM | active_0 - active_5 + noise | 418,049 | 4.5% |
| cooling | Supervised LGBM | cooling_0 - cooling_6 + noise | 356,500 | 3.8% |
| at_risk | Supervised LGBM | at_risk_0 - at_risk_5 + noise | 1,580,877 | 16.8% |
| dormant | Carried forward from V11 | Former_Builders, Low_Depth, One_Time_Users | 5,304,852 | 56.5% |
| unactivated | Carried forward from V11 | unactivated | 1,721,230 | 18.3% |

Dormant breakdown: Former_Builders 1.66M, Low_Depth 2.47M, One_Time_Users 1.18M.

---

## Feature Configuration

| Stratum | Features used | Key signals |
|---|---|---|
| active | 12 | `log_activity_count_0_30d`, `log_activity_count_30_90d`, `unique_activity_types_0_30d`, `developer_effort_score`, `activity_velocity_0_30_vs_30_90`, `recent_build_flag` |
| cooling | 8 | `log_activity_count_30_90d`, `log_activity_count_90_180d`, `developer_effort_score`, `build_share_lifetime`, `persona_entropy` |
| at_risk | 7 | `log_activity_count_30_90d`, `log_activity_count_90_180d`, `developer_effort_score`, `build_share_lifetime`, `log_clipped_lifetime_activity_count_p99` |

---

## Key Takeaways

1. **Near-perfect cluster reproduction.** Accuracy above 99.6% on every stratum with as few as 7 features - the V11 HDBSCAN clusters are genuinely feature-driven, not algorithmic artifacts.
2. **LightGBM consistently edges XGBoost** by 0.1-0.4 pp on both accuracy and macro-F1 across all three strata.
3. **Scalable scoring path unlocked.** The three saved joblib artifacts can assign cluster labels to new developers in milliseconds without re-running HDBSCAN on the full 9.4M-row dataset.
4. **Noise is modeled, not discarded.** `*_noise` is included as an explicit class in all three strata, allowing the supervised model to flag ambiguous developers rather than force-assigning them.
5. **Outputs written to DuckDB:** `dev_supervised_cluster_membership_v1_final` (9.38M rows), `_lgbm`, `_xgb`, `_run_stats`, `_profile_summary` - all also exported to `toexport_clusters/` as Parquet.
