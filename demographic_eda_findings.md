# Demographic EDA: Key Findings
**Dataset:** NVIDIA Developer Program — Contact Table (`contact_clean`)
**Analysis Date:** May 2026
**Tool:** DuckDB + Python (Jupyter)

---

## Dataset Overview

| Metric | Value |
|---|---|
| Total records | 9,381,490 |
| Unique developers | 9,381,490 (1:1 — one row per developer) |
| Countries represented | 250 |
| Regions | 4 (APAC, NALA, EMEA + ~9% unattributed) |
| Distinct industry segments | 21 |
| Distinct account types | 6 |
| Date range (created) | Apr 2013 – Mar 2026 |

---

## 1. Geographic Distribution

### Top Countries
The developer base is heavily concentrated in three countries, which together account for nearly half of all records:

| Country | Developers | Share |
|---|---|---|
| United States | 1,688,338 | 18.0% |
| China | 1,645,122 | 17.5% |
| India | 1,111,879 | 11.9% |
| Korea, Republic of | 305,752 | 3.3% |
| Japan | 292,502 | 3.1% |
| Germany | 238,016 | 2.5% |

> **Note:** 804,111 records (8.6%) have a null country — the 4th largest "group" by count. This is a meaningful data quality gap and should be flagged for upstream resolution.

### Regional Breakdown
APAC is the dominant region, accounting for nearly half the global developer base:

| Region | Developers | Share |
|---|---|---|
| APAC | 4,284,392 | 45.7% |
| NALA | 2,220,135 | 23.7% |
| EMEA | 2,070,011 | 22.1% |
| Null / Unknown | ~806,952 | ~8.6% |

### Sub-Region Detail
Within APAC, China and India together make up ~67% of the region. Within EMEA, continental Europe dominates at 1.6M vs. Africa (237K) and Middle East (129K).

| Region | Sub-Region | Developers |
|---|---|---|
| APAC | China | 1,778,896 |
| APAC | India | 1,111,879 |
| APAC | ROAP | 581,691 |
| APAC | South Korea | 305,752 |
| APAC | Japan | 292,502 |
| APAC | Taiwan | 213,672 |
| EMEA | Europe | 1,632,036 |
| EMEA | Africa | 236,577 |
| EMEA | Middle East | 129,206 |
| NALA | US & Canada | 1,847,441 |
| NALA | LatAm | 372,694 |

---

## 2. Industry & Vertical Segmentation

The `industry_segment_vertical` field is multi-select (semicolon-delimited) and was exploded for accurate counting. `industry_segment_vertical` has **0% missingness** — the best-populated demographic field in the dataset.

| Industry Segment | Developers | % of Total |
|---|---|---|
| **Other** | 4,342,653 | 46.3% |
| Academia / Education | 1,224,186 | 13.1% |
| AEC | 594,797 | 6.3% |
| Gaming | 488,951 | 5.2% |
| Cloud Services | 285,473 | 3.0% |
| Media & Entertainment | 256,978 | 2.7% |
| Automotive / Transportation | 217,860 | 2.3% |
| Financial Services | 217,183 | 2.3% |
| Hardware / Semiconductor | 212,841 | 2.3% |
| Healthcare & Life Sciences | 210,352 | 2.2% |

> **Key insight:** The large "Other" bucket (46%) suggests the taxonomy may need refinement or that self-reported vertical selections are skewed toward catch-all options. Academia/Education is the largest meaningful segment, driven heavily by China and India.

**Sub-industry segment** is nearly entirely null (91% missing), with only "Gaming" having meaningful coverage (~449K). This field is not currently viable for analysis.

---

## 3. Development Areas

Development areas are also multi-select. This field is well-populated (~99.9% non-null) and reflects developer self-reported technical focus areas.

| Development Area | Developers | % of Total |
|---|---|---|
| Data Science | 2,642,299 | 28.2% |
| Computer Vision / Video Analytics | 2,540,341 | 27.1% |
| Agentic AI / Generative AI | 2,244,773 | 23.9% |
| Conversational AI | 1,970,164 | 21.0% |
| Simulation / Modeling / Design | 1,557,268 | 16.6% |
| Content Creation / Rendering | 1,399,898 | 15.0% |
| AR / VR | 1,294,014 | 13.8% |
| Data Center / Cloud | 1,238,709 | 13.2% |
| Robotics | 1,121,830 | 12.0% |

> **Key insight:** AI-adjacent development areas dominate. The top 4 alone (Data Science, CV, Agentic AI, Conversational AI) each exceed 2M developers, suggesting the program skews strongly toward ML/AI practitioners. Note that some labels appear inconsistently normalized (e.g., `conversational_ai` in snake_case vs. others in title case) — a cleaning recommendation for future work.

**Fields of interest** is effectively unusable: 94.9% null, with only "Unknown" as the non-null value. This field should be excluded from downstream modeling or imputed from `development_areas`.

---

## 4. Account Profile

### Account Type
Account type is the most sparsely populated field (68.3% Unknown/missing), but among records with data, University accounts make up the majority:

| Account Type | Developers | Share |
|---|---|---|
| Unknown | 6,404,129 | 68.3% |
| University | 1,980,017 | 21.1% |
| Enterprise | 740,459 | 7.9% |
| Startup | 215,987 | 2.3% |

> University's dominance aligns with the Academia/Education industry segment and strong APAC presence (particularly China and India), where academic developer communities are large.

### Account Source
Account source has 485 distinct values due to multi-value concatenation (e.g., `University: China;WWFO`). The top clean sources are:

| Account Source | Developers |
|---|---|
| Null | 3,132,203 |
| Manual | 2,495,695 |
| WWFO | 411,861 |
| University: India | 266,222 |
| University: China;WWFO | 249,381 |

> The 485 distinct values indicate this field was not normalized before ingestion. Recommend parsing and exploding the semicolon-delimited values for cleaner reporting.

**Account industry segment** is 94.9% null — effectively not usable in its current state.

---

## 5. Program Enrollment Over Time

### Application Source
DevZone is the dominant known acquisition channel, followed by DLI (Deep Learning Institute):

| Source | Developers | Share |
|---|---|---|
| Null | 4,006,295 | 42.7% |
| devzone | 2,806,574 | 29.9% |
| dli | 1,004,037 | 10.7% |
| gtc | 448,297 | 4.8% |
| api_catalog | 391,786 | 4.2% |

### Enrollment Trends
Enrollment has accelerated sharply in recent quarters, coinciding with the broader AI boom:

| Quarter | New Developers |
|---|---|
| Q1 2024 | 336,014 |
| Q4 2024 | 338,558 |
| Q1 2025 | 501,546 ⬆ peak |
| Q2 2025 | 362,269 |
| Q3 2025 | 354,084 |
| Q4 2025 | 306,332 |
| Q1 2026 | 532,026 ⬆ new peak |

> Q1 2025 and Q1 2026 are both record quarters, suggesting seasonal or event-driven spikes (likely GTC-related). The overall trajectory is strongly upward — the program crossed ~9.4M total developers by early 2026.

---

## 6. WWFO Segmentation

WWFO category is 82% null, but among records with values, Higher Ed/Research is the largest segment by far:

| WWFO Category | Developers | Share |
|---|---|---|
| Null | 7,707,466 | 82.2% |
| Higher Ed/Research | 1,059,005 | 11.3% |
| Unknown | 397,162 | 4.2% |
| Strategic Hyperscale | 42,925 | 0.5% |
| Manufacturing | 38,125 | 0.4% |
| Automotive | 34,371 | 0.4% |

---

## 7. Data Quality Summary

| Field | Missing % | Status |
|---|---|---|
| `account_type` | 68.3% | ⚠️ High — limit use in segmentation |
| `first_program_application_date` | 27.6% | ⚠️ Moderate — affects time-series analyses |
| `fields_of_interest` | 5.1% | ⚠️ Field is essentially empty (all remaining = "Unknown") |
| `account_industry_segment` | 5.1% | ⚠️ Same — not usable |
| `program_application_source` | 4.8% | ✅ Acceptable |
| `wwfo_category` | 4.2% | ✅ Acceptable for WWFO-filtered analysis |
| `sub_industry_segment_vertical` | 3.9% | ⚠️ Near-empty beyond "Gaming" |
| `territory` | 3.4% | ✅ Acceptable |
| `development_areas` | 0.06% | ✅ Excellent |
| `country` / `region` / `sub_region` / `zone` | 0.03% | ✅ Excellent |
| `industry_segment_vertical` | 0.0% | ✅ Complete |

---

## Key Takeaways

1. **APAC dominance:** Nearly half the program is APAC, with China, India, and South Korea as the top three contributors to the region.
2. **AI/ML is the core use case:** Data Science, Computer Vision, and Generative AI are the top development areas, each cited by 24–28% of developers.
3. **Academic skew:** Academia/Education is the largest industry segment with meaningful data, and University is the most common known account type — the developer base leans academic, particularly in Asia.
4. **Explosive recent growth:** Q1 2025 and Q1 2026 are record enrollment quarters. The program has grown dramatically since 2023, likely fueled by generative AI interest.
5. **DevZone is the primary acquisition channel:** Among known sources, devzone (29.9%) and DLI (10.7%) account for the majority of attributable enrollments.
6. **Significant missingness in account-level fields:** `account_type` (68%), `wwfo_category` (82%), and `account_industry_segment` (95%) are too sparse for reliable segmentation without imputation or upstream data improvement.

---

*Analysis conducted using DuckDB on `contact_clean` table. See `DemographicEDA_Contact.ipynb` for full code.*
