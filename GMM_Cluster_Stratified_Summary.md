# GMM Stratified Clustering — Plain-English Summary

## What this notebook does

Instead of running one big clustering model on every developer at once, this notebook groups developers by where they are in their lifecycle (are they active? cooling off? at risk of leaving? dormant?) and then runs a separate, smaller clustering model on each group.

The reason: lumping everyone together hides the interesting differences. A "low activity" active developer and a "low activity" dormant developer look similar on paper but mean very different things to the business.

## Who the developers are

We start with 9.38 million developers. They fall into five buckets based on their current lifecycle status:

- **Unactivated (6.7M)** — signed up but never really engaged. Set aside.
- **Dormant (1.7M)** — used to be active, now quiet. Get a simple rules-based grouping (a full model would be slow and tell us very little, since most are just inactive).
- **Active (463K)** — currently engaged. Get the full clustering treatment.
- **At risk (394K)** — slipping away. Get the full clustering treatment.
- **Unknown (110K)** — couldn't be classified. Set aside.

The "cooling" group was empty in this run, so nothing to do there.

## How the clustering works (in plain terms)

For each of the active and at-risk groups, the notebook:

1. Pulls a custom list of features that matter for that group. Active developers get 12 features focused on recent behavior. At-risk developers get 7 features focused on whether they're trending down.
2. Cleans the data — fills in missing values, trims extreme outliers, and puts everything on the same scale.
3. Figures out how many clusters to use by trying values from 2 to 12 and picking the one that fits best without being overkill.
4. Double-checks that choice with a second method that independently suggests how many clusters are really needed.
5. Fits the final model and assigns each developer to a cluster.

For dormant developers, it skips the model and just buckets them by how much effort they used to put in and whether they were builders.

## What we ended up with

**Active developers** split into 6 clusters. One cluster holds the majority (about 59%), and the rest are smaller specialized groups.

**At-risk developers** split into 4 clusters. The largest holds about 44%, with three smaller groups making up the rest.

**Dormant developers** split into 4 simple buckets:
- Low-effort lapsed (859K) — the biggest chunk, people who were never very engaged
- Mid-effort lapsed (687K) — moderate former users
- Former high-effort (90K) — people who used to put in real work
- Former power builders (82K) — the most engaged dormant group, worth trying to win back

The models are very confident in their assignments. Active developers land in their cluster with 99.9% certainty on average; at-risk with 98.3%. That means the groups are genuinely distinct, not fuzzy overlaps.

## What gets saved

Everything ends up in a single DuckDB table called `dev_gmm_stratified_clusters_v1`, with one row per developer showing which lifecycle group and which cluster they belong to. The trained models themselves are saved as files so you don't have to retrain them every time.

There's also a separate weekly-level model (`dev_gmm_weekly_clusters_v1`) that clusters developer-weeks instead of developers, which is useful for comparing against the HMM model later.

## Things worth knowing if you want to rerun this

- By default the notebook skips any group that already has a saved model. To force a refit, add the group name to `FORCE_RERUN_STRATA`.
- The cluster counts (6 for active, 4 for at-risk) are picked automatically but you can override them if the plots suggest something different.
- Cluster labels start out generic (`active_c0`, `active_c1`, etc.). After looking at the profile plots, you can fill in human-readable names in the `CLUSTER_LABELS` dictionary — something like `active_high_effort_builders` instead of `active_c0`.

## What's still missing

The cluster labels haven't been filled in yet. The next step is to look at the centroid tables and radar plots for each cluster and decide what to actually call them, so the output is useful for downstream work rather than a wall of `c0` / `c1` / `c2`.
