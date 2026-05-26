# sdk_download_final Analysis

Analysis date: 2026-05-26

Source table: `developer_project.duckdb`.`sdk_download_final`

## Executive Summary

`sdk_download_final` is a strong product adoption signal for the project, but it should be treated as an aggregate adoption dataset rather than a developer-level table. It has 93,038,213 rows and 15.34B total `download_count` from 2020-01-01 through 2026-03-12.

The table is clean on the most important validity checks: no null `download_date`, no null `download_count`, and no negative `download_count`. However, exact duplicate rows still exist. They add 278,056 duplicate rows beyond the first copy, inflating total downloads by 1,261,852, or only 0.0082% of total downloads. This is small enough that directional adoption findings are stable, but deduplication is still recommended before final metrics.

## Key Findings

### 1. Adoption Is Highly Concentrated

Downloads are heavily concentrated in the top products:

| Product rank group | Downloads | Share of total |
| --- | ---: | ---: |
| Top 5 products | 4.77B | 31.11% |
| Top 10 products | 7.87B | 51.30% |
| Top 20 products | 12.10B | 78.90% |

Top products by total downloads include:

| Product | Downloads |
| --- | ---: |
| torch | 1.51B |
| tensorflow | 1.23B |
| nvidia-nccl-cu12 | 708.91M |
| triton | 672.79M |
| nvidia-cublas-cu12 | 647.34M |

This suggests the project should separate "core ecosystem products" from long-tail products. Otherwise, aggregate adoption metrics will mostly describe PyTorch/TensorFlow/CUDA package behavior.

### 2. PyPI Dominates the Adoption Signal

`pypi` accounts for 94.53% of total downloads. Other sources are much smaller:

| Source | Download share |
| --- | ---: |
| pypi | 94.53% |
| github | 1.88% |
| cdn | 1.82% |
| ngc | 0.70% |
| dockerhub | 0.57% |
| conda | 0.30% |

For modeling, source should be treated as a major segmentation variable. A product can look successful overall simply because it is distributed through PyPI.

### 3. U.S. Downloads Dominate Geography

The U.S. accounts for 70.40% of all downloads. The next largest geographies are far smaller:

| Country | Region | Download share |
| --- | --- | ---: |
| US | nala | 70.40% |
| UNKNOWN | unknown | 2.93% |
| DE | emea | 2.81% |
| SG | apac | 2.70% |
| NL | emea | 2.68% |
| IE | emea | 2.57% |

Recommendation: report both global adoption and non-U.S. adoption. Otherwise geographic insights will mostly reflect U.S. package download behavior.

### 4. Downloads Accelerated Strongly In 2025

Monthly downloads rose from 178.40M in January 2024 to 894.37M in February 2026. March 2026 is partial because the latest date is 2026-03-12.

Notable month-over-month increases:

| Month | Downloads | MoM change |
| --- | ---: | ---: |
| 2025-02 | 421.63M | +20.74% |
| 2025-03 | 485.41M | +15.13% |
| 2025-08 | 761.74M | +20.89% |
| 2025-10 | 837.85M | +12.90% |

This supports using monthly adoption trend features such as trailing 30/90/180-day downloads, month-over-month growth, and product activation month.

### 5. Recent Growth Products Are Not Just The Historic Leaders

In the latest 90-day window compared with the prior 90 days, the largest absolute growth products were:

| Product | Recent 90d | Prior 90d | Absolute growth | Growth ratio |
| --- | ---: | ---: | ---: | ---: |
| cuda-bindings | 42.83M | 5.12M | +37.71M | 8.37x |
| nvidia-nvshmem-cu12 | 65.39M | 34.73M | +30.65M | 1.88x |
| sglang | 29.96M | 6.37M | +23.59M | 4.70x |
| onnxruntime | 87.04M | 74.81M | +12.23M | 1.16x |
| nvidia-cufile-cu12 | 81.80M | 71.84M | +9.96M | 1.14x |

This is useful for a deal-sourcing or prioritization angle: recent momentum surfaces emerging adoption pockets that would be hidden by lifetime totals.

### 6. Some Historic Leaders Recently Declined

Largest recent 90-day declines versus prior 90 days:

| Product | Recent 90d | Prior 90d | Absolute change | Growth ratio |
| --- | ---: | ---: | ---: | ---: |
| torch | 198.91M | 217.41M | -18.50M | 0.91x |
| tensorflow | 62.09M | 76.78M | -14.69M | 0.81x |
| nvidia-cudnn-cu12 | 115.56M | 122.18M | -6.62M | 0.95x |
| nvidia-cuda-cupti-cu12 | 114.16M | 120.18M | -6.02M | 0.95x |
| nvidia-cusolver-cu12 | 116.19M | 122.04M | -5.86M | 0.95x |

These are still huge products, so the decline should be interpreted as momentum cooling, not low adoption.

## Data Quality Notes

The final table has no SQL nulls or blanks in the core columns, but several columns use placeholder values:

| Column | Placeholder rows | Share of rows |
| --- | ---: | ---: |
| os_distribution | 88.31M | 94.92% |
| architecture | 88.14M | 94.74% |
| territory | 39.47M | 42.43% |
| operating_system | 18.04M | 19.39% |
| country / region / subregion / zone | 1.25M | 1.35% |
| file_type | 1.20M | 1.29% |

`os_distribution` and `architecture` should not be used as primary modeling features unless source-specific filtering improves coverage. `operating_system`, `file_type`, `country`, and `region` are more usable.

Exact duplicate rows remain:

| Metric | Value |
| --- | ---: |
| Duplicate groups | 277,810 |
| Rows in duplicate groups | 555,866 |
| Duplicate rows beyond first | 278,056 |
| Extra duplicate downloads | 1,261,852 |
| Duplicate inflation of total downloads | 0.0082% |

## Recommended Features For The Project

Useful adoption features from this table:

| Feature grain | Recommended features |
| --- | --- |
| product-month | monthly downloads, 3-month growth, 6-month growth, active countries, active sources, source diversity |
| product-country-month | downloads, share of product downloads, recent growth, first-seen date in country |
| source-product-month | downloads by source, source share, source growth |
| product lifecycle | first download date, latest download date, months active, peak month, latest 90-day downloads |
| product momentum | recent 90d vs prior 90d growth, recent country expansion, volatility/spike flags |

For final dashboards or models, use a deduplicated view:

```sql
CREATE OR REPLACE VIEW sdk_download_final_deduped AS
SELECT DISTINCT *
FROM sdk_download_final;
```

Then build monthly product adoption:

```sql
CREATE OR REPLACE TABLE sdk_product_month_adoption AS
SELECT
  DATE_TRUNC('month', download_date) AS month,
  product_name,
  sdk_name,
  source,
  SUM(download_count) AS downloads,
  COUNT(*) AS rows,
  COUNT(DISTINCT country) AS active_countries,
  COUNT(DISTINCT operating_system) AS operating_system_count,
  COUNT(DISTINCT file_type) AS file_type_count
FROM sdk_download_final_deduped
GROUP BY 1, 2, 3, 4;
```

## Bottom Line

The most helpful use of `sdk_download_final` is as a product adoption and product momentum layer. It should not be joined to developer-level activity as if it identifies individual developers. Instead, use it to build product, source, geography, and time-based adoption features that complement the developer engagement tables.
