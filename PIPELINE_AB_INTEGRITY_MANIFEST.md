# A/B Pipeline Integrity Manifest

| Pipeline | New notebook | Source notebook | Code status | Source hash | New hash |
|---|---|---|---|---|---|
| A | `Pipeline_A/1A_Create_DuckDB.ipynb` | `01_Creating_duckDB.ipynb` | renamed copy; code cells unchanged | `6ad555a9e650e1db` | `6ad555a9e650e1db` |
| A | `Pipeline_A/2A_Clean_Data.ipynb` | `02_Cleaning.ipynb` | renamed copy; code cells unchanged | `b7eadb3f296ad21d` | `b7eadb3f296ad21d` |
| A | `Pipeline_A/3A_Feature_Engineering.ipynb` | `03_FeatureEngineering_v3.ipynb` | renamed copy; code cells unchanged | `13bd6cf04c6be560` | `13bd6cf04c6be560` |
| A | `Pipeline_A/4A_HDBSCAN_Clustering.ipynb` | `04_clustering_hdbscan.ipynb` | renamed copy; code cells unchanged | `ec1e9b2e343119a0` | `ec1e9b2e343119a0` |
| A | `Pipeline_A/5A_GMM_Cluster_Validation.ipynb` | `05_GMM_Cluster_Stratified.ipynb` | renamed copy; code cells unchanged | `19aa5f0775b0c803` | `19aa5f0775b0c803` |
| A | `Pipeline_A/6A_HMM_Journey_Modeling.ipynb` | `06_hmm_categorical.ipynb` | renamed copy; code cells unchanged | `090bbbd5270626bf` | `090bbbd5270626bf` |
| A | `Pipeline_A/7A_Supervised_Labeling_LGBM_XGB.ipynb` | `07_SupervisedClusterLabeling_LGBM_XGB.ipynb` | renamed copy; code cells unchanged | `43c6a64f03e35716` | `43c6a64f03e35716` |
| A | `Pipeline_A/8A_Train_Saved_LGBM_Labeler.ipynb` | `08_Score_New_Developers_LGBM_From_Fixed_HDBSCAN.ipynb` | same saved-labeler logic; syntax fixed; TRAIN_MODE=True; SCORE_MODE=False | `patched from source` | `c558468488f61b28` |
| B | `Pipeline_B/1B_Load_New_Raw_Data_To_DuckDB.ipynb` | `01_Creating_duckDB.ipynb` | renamed copy; code cells unchanged | `6ad555a9e650e1db` | `6ad555a9e650e1db` |
| B | `Pipeline_B/2B_Clean_New_Data.ipynb` | `02_Cleaning.ipynb` | renamed copy; code cells unchanged | `b7eadb3f296ad21d` | `b7eadb3f296ad21d` |
| B | `Pipeline_B/3B_Feature_Engineering_New_Data.ipynb` | `03_FeatureEngineering_v3.ipynb` | original feature logic unchanged; adapter cell added before close to create dev_profile_new_incoming_v1 | `13bd6cf04c6be560` | `233ee16c3978bc6a` |
| B | `Pipeline_B/4B_Score_New_Data_Fixed_Clusters.ipynb` | `08_Score_New_Developers_LGBM_From_Fixed_HDBSCAN.ipynb` | same saved-labeler scoring logic; syntax fixed; TRAIN_MODE=False; SCORE_MODE=True; robust stratum fallback added | `patched from source` | `86551d0589b7b067` |
