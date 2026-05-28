# Demographics Team — Slide Content
## 3 Slides

---

## SLIDE 1: The Activation Gap

**Headline:** Nvidia has attracted 9.4M developers. Fewer than 5% are actively building.

### The Funnel

| Lifecycle Stage | Developers | Share |
|---|---|---|
| Dormant (gone) | 5.3M | 57% |
| Never Activated | 1.72M | 18% |
| At Risk | 1.58M | 17% |
| Cooling | 357K | 4% |
| **Active** | **418K** | **4.5%** |

> The acquisition engine works. The activation engine doesn't.

---

### What the Active 4.5% Looks Like — Two Separate Populations

| | US API Builders | APAC Learners |
|---|---|---|
| Clusters | active_1, active_3, active_5 | active_0, active_2, active_4 |
| Size | 251K (60% of active base) | 61K (15% of active base) |
| Geography | 92–96% United States | 45–50% APAC |
| Entry channel | 90–95% API Catalog | DLI, devzone, GTC conference |
| Primary interest | Agentic AI (83–97%) | Agentic AI + broad stack |
| Industry | ~90%+ "Other" (startup/independent) | 20–27% Academia/Education |

**Key insight:** These two groups arrived differently, built differently, and stayed for different reasons. Every downstream recommendation needs to treat them as separate audiences.

---

## SLIDE 2: Three Demographic Failure Archetypes

**Headline:** The 75% who left weren't random — they match three specific failure patterns.

---

### Archetype 1: The DLI Dropout
- **Who:** `at_risk_2` — 210K developers
- **Where:** 41% India, 20% APAC total — 60% APAC overall
- **How they arrived:** 70% through DLI (Nvidia's own training product)
- **What they wanted:** Deployment (64%), Agentic AI (62%), Data Science (42%)
- **What happened:** Completed Nvidia training. Hit the wall between "certified" and "shipped." No structured pathway exists from DLI graduation to production deployment.
- **Industry:** 20% Academia/Education — learners, not yet builders

---

### Archetype 2: The Deployment Wall
- **Who:** `at_risk_1`, `at_risk_2`, `at_risk_3` combined — **562K developers**
- **Defining signal:** `deployment` is a top-3 development area in all three clusters (46–64%), which almost never appears in active clusters
- **Geography:** APAC-heavy (42–60%), but includes 32% US in at_risk_3
- **Entry:** Mix of devzone, DLI, API Catalog — these developers came in through multiple channels
- **What happened:** Developers with clear commercial intent — trying to deploy real products on Nvidia infrastructure — went quiet. This is friction, not lack of interest.
- **This is the highest-cost failure:** commercial-intent developers stopping before they ship

---

### Archetype 3: The Conference Bounce
- **Who:** `Dormant_One_Time_Users` — **1.18M developers**
- **Where:** 48% APAC, 25% EMEA, 23% NALA
- **How they arrived:** 20% via GTC (Nvidia's own conference) — the highest GTC share of any segment
- **What happened:** Attended GTC, enrolled in the developer program, completed minimal activity, disappeared. No "day after GTC" journey existed.
- **Industry:** Academia (11%), AEC (7%), Gaming (6%) — curious explorers, not committed builders

---

## SLIDE 3: The Recovery Opportunity

**Headline:** The single highest-ROI move is not acquiring new developers — it's reactivating Former Builders.

---

### Dormant Former Builders: 1.66M Technically Sophisticated Developers

| Attribute | Value |
|---|---|
| Size | 1.66M developers |
| Geography | 54% APAC, 26% EMEA, 19% NALA |
| Top interests | Computer Vision (34%), Data Science (30%), Conversational AI (23%) |
| Entry channel | 49% devzone — intentional community members |
| Industry | 17% Academia, 10% Gaming, 7% AEC |

These were real builders. They built things on Nvidia hardware and stopped. The GenAI landscape has been completely rebuilt since most of them disengaged. A win-back campaign anchored in modern tooling (NIM, Agentic AI frameworks) reaches developers who already know the platform.

---

### The Math

Moving **10% of the at-risk population** back to active = **158K additional engaged developers.**

Moving **5% of Dormant Former Builders** back to active = **83K additional engaged developers.**

Combined: **241K developers** reactivated without acquiring a single new one.

---

### One Data Quality Flag for Recommendations

**Ghost clusters** (`at_risk_4` + `cooling_3`): **143K developers** with 89–97% null development areas and 96–97% null program source. These are behaviorally at-risk but completely unprofileable. Recommendations team cannot personalize for them without a cold-start profiling step first.
