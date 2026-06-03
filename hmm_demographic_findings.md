# HMM Emission State Analysis — Findings
**NVIDIA Developer Lifecycle Project**

---

## Overview

This analysis examines how weekly GMM emission states (the observation sequences used as HMM inputs)
are distributed across developer lifecycle strata and adoption directions. Three emission states were
identified from the weekly GMM model:

| State | Label | Description |
|---|---|---|
| c0 | Moderate | Regular engagement weeks |
| c1 | Burst | High-intensity engagement weeks — rarest, highest confidence |
| c2 | Inactive | Low / no activity weeks |

---

## 1. State Characterization

| State | Observations | Unique Developers | Avg Confidence |
|---|---|---|---|
| Moderate (c0) | 8.99M | 4.3M | 1.0000 |
| Burst (c1) | 382K | 177K | 0.9963 |
| Inactive (c2) | 5.53M | 5.0M | 0.9997 |

- Burst is the rarest state at ~2.5% of all weekly observations, but has the most developers overlap
  with Inactive — many developers reach burst only occasionally.
- All three states are highly separable with average assignment confidence exceeding 0.996.

---

## 2. State Distribution by Lifecycle Stratum

| Stratum | % Moderate | % Burst | % Inactive |
|---|---|---|---|
| Active | 78.6% | 5.4% | 16.0% |
| Cooling | 71.9% | 4.0% | 24.0% |
| At-Risk | 64.9% | 2.7% | 32.4% |
| Dormant | 54.6% | 1.9% | 43.5% |

The gradient across strata is clean and monotonic — as developers move toward disengagement,
Moderate weeks decrease and Inactive weeks increase. This confirms the weekly GMM emission states
carry meaningful lifecycle signal, supporting their suitability as inputs to HMM modeling.

---

## 3. State Distribution by Adoption Direction

Adoption direction maps 1:1 to lifecycle strata in this dataset, so the pattern mirrors Section 2.
`accelerating_or_active` developers spend 78.6% of weeks in Moderate state; `steady_inactive`
(dormant) developers spend 43.5% in Inactive state. The weekly HMM states are consistent with the
adoption direction labels across the full developer population.

---

## 4. Transition Matrices by Stratum

Key patterns observed across all strata:

- **Self-loops dominate**: Developers tend to stay in the same state week-over-week, indicating
  strong behavioral inertia. This is expected and supports HMM's assumption of Markov structure.
- **Active developers**: Highest probability of staying Moderate and escalating to Burst.
  Lowest probability of dropping to Inactive.
- **Dormant developers**: Highest probability of staying Inactive. When reactivation occurs
  (c2 → c0), they tend to return to Inactive quickly — short-lived re-engagement.
- **At-risk developers**: Most volatile transitions — relatively balanced probabilities between
  Moderate and Inactive, confirming an unstable behavioral state that HMM should be able to
  detect early as a churn signal.

---

## 5. Developer-Level State Metrics

| Stratum | Avg Weeks Observed | Avg % Moderate | Avg % Burst | Avg % Inactive | Avg Entropy |
|---|---|---|---|---|---|
| Active | 3.3 | 73.0% | 1.7% | 25.3% | 0.1545 |
| Cooling | 2.6 | 60.8% | 1.9% | 37.3% | 0.1471 |
| At-Risk | 2.2 | 50.6% | 1.4% | 47.9% | 0.1515 |
| Dormant | 1.7 | 43.3% | 1.0% | 55.6% | 0.1379 |

- **Active developers have the highest state entropy (0.1545)** — their weekly behavior is the most
  varied, mixing Moderate and Burst weeks. This reflects genuine engagement diversity.
- **Dormant developers have the lowest entropy (0.1379)** — sequences are predominantly locked
  into Inactive, making them the most predictable group.
- Median observed weeks is 1 across all strata. Most developers have sparse sequences — an
  important consideration for HMM training and sequence length requirements.

---

## 6. Temporal Trends (2022–2026)

State composition is broadly stable over time within each stratum, which is a positive signal for
HMM — the emission probabilities are not drifting dramatically quarter over quarter. Dormant
developers show a slight increase in Inactive weeks in more recent quarters, consistent with
cooling and at-risk populations feeding into dormancy over time.

---

## 7. Burst-State Developer Profile

Of the 177K developers who ever reached a Burst week:

| Stratum | Adoption Direction | Burst Developers |
|---|---|---|
| Dormant | steady_inactive | 100,577 |
| At-Risk | at_risk | 45,919 |
| Active | accelerating_or_active | 16,537 |
| Cooling | declining | 14,342 |

- The majority of burst-capable developers are now **dormant** — these are historically
  high-engagement developers whose burst weeks occurred in the past. This maps directly to the
  `Dormant_Former_Builders` segment.
- Burst history in dormant and at-risk developers is a strong **re-engagement signal** for HMM
  to detect: a developer who has previously shown burst capacity is a higher-value reactivation
  target than one who never has.

---

## Key Takeaways for HMM Modeling

1. The three emission states (Moderate, Burst, Inactive) cleanly separate lifecycle strata —
   confirming they carry meaningful lifecycle signal as inputs to HMM. Note: this does not
   fully validate the HMM itself, which requires training and evaluating the model's transition
   probabilities and predictions.
2. Transition self-loops are strong across all strata, supporting a Markov structure assumption.
3. At-risk developers show the most volatile transitions — HMM should be most informative here
   for early churn detection.
4. Sparse observation sequences (median = 1 week per developer) will require careful handling
   during HMM training, either through smoothing, minimum sequence length filters, or imputation.
5. Burst history is a high-value feature for dormant re-engagement targeting.
