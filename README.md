## Overview

This project builds a scalable DuckDB-based analytical pipeline to evaluate whether **developer engagement leads to meaningful technology adoption**, rather than just higher interaction counts.

The core objective is to:

* understand developer behavior across the engagement lifecycle
* identify which activities drive real adoption signals
* build a repeatable framework for cohort analysis and monitoring

The workflow includes:

1. Data ingestion from raw CSV exports
2. Data cleaning and standardization
3. Time-based feature engineering
4. Developer segmentation (behavioral maturity)
5. Engagement → adoption analysis



## Data Sources

The project uses three primary datasets:

* `DEVPM_8674_Cal_Poly_Export_dev_activity.csv`
  → Developer engagement events (trainings, webinars, downloads, etc.)

* `DEVPM_8674_Cal_Poly_Export_dev_contact.csv`
  → Developer profile and account-level attributes

* `DEVPM_8674_Cal_Poly_Export_sdk_download.csv`
  → Product interaction signals across platforms (PyPI, NGC, DevZone, etc.)



## Database

All data is stored in a persistent DuckDB database:

* `developer_project.duckdb`

This enables:

* fast querying on large datasets (100M+ rows)
* reproducibility across sessions
* separation of raw and cleaned layers



## Table Structure

### Raw Layer

Unmodified ingested data:

* `activity_raw`
* `contact_raw`
* `sdk_download_raw`

### Clean Layer

Typed and standardized datasets:

* `activity_clean`
* `contact_clean`
* `sdk_download_clean`



## Data Processing Approach

* All raw data initially loaded as `VARCHAR` to prevent type errors
* Clean tables created using `TRY_CAST` for safe type conversion
* Persistent storage avoids repeated ingestion of large files
* Transformations performed directly in DuckDB for scalability



## Key Data Issues Identified

### Activity Data

* Duplicate rows present
* Extreme outliers in `activity_score`
* High-null columns (e.g., attendance)
* Very high cardinality in `activity_name`
* Inconsistent text formatting

Important note:
Not all activities represent equal engagement intensity. This dataset mixes low- and high-intent signals.



### Contact Data

* Several columns with high missingness
* `rdp_exit_date` fully null
* Developer ID behaves as a reliable primary key

Important note:
This dataset is primarily used for enrichment, not core modeling.



### SDK Download Data

* Duplicate rows present
* Negative `download_count` values
* High-null technical fields (OS, architecture)

Important note:
This is the strongest proxy for **product-level engagement**, but it is not directly linked to individual developers.



## Cleaning Strategy

### Deduplication

* Remove full-row duplicates from activity and SDK datasets

### Data Validation

* Filter invalid values (e.g., negative downloads)
* Cap extreme outliers (e.g., activity_score)

### Standardization

* Normalize text fields:

```sql
LOWER(TRIM(activity_name))
```

### Column Selection

Drop or ignore low-quality fields:

* very high null rate (>80%)
* low analytical value

### Null Handling

* > 80% null → drop
* 30–80% → evaluate carefully
* <30% → retain



## Data Model

* `activity_clean` → developer engagement events
* `contact_clean` → developer profile attributes
* `sdk_download_clean` → product interaction signals

Primary join:

```sql
activity_clean.dev_contact = contact_clean.developer_id
```

Key limitation:

* No direct user-level link between SDK downloads and developers
* Adoption must be inferred using aggregate or indirect methods



## Analytical Framework

### 1. Developer Maturity Segmentation

Goal:
Segment developers based on **behavior over time**, not just total activity.

Examples:

* Explorers (low activity, broad interactions)
* Learners (consistent training and content engagement)
* Evaluators (targeted, repeated engagement)
* Adopters (signals of real product usage)



### 2. Engagement → Adoption Analysis

Core question:
Which engagement patterns lead to adoption?

Approach:

* Analyze sequences of events over time
* Identify activities that precede stronger signals (e.g., downloads)
* Compare high-value vs low-value engagement



### 3. Time-Based Feature Engineering

* Build rolling windows:

  * 30, 60, 90, 180, 365 days
* Capture:

  * recency
  * frequency
  * progression



### 4. Product Analysis

* Aggregate downloads by product
* Identify:

  * top-performing products
  * long-tail distribution
* Analyze trends across time



### 5. Geographic Analysis

* Segment activity and downloads by:

  * country
  * region
* Identify growth and adoption patterns



## Key Risks and Considerations

* Engagement does not equal adoption
* Activity signals are heterogeneous and require weighting
* Missing direct linkage between users and downloads
* Data quality issues (nulls, duplicates, inconsistencies)
* Open-source usage may not be fully captured



## How to Run

### Setup

Ensure your directory contains a `Data/` folder with all CSV files.

Install dependencies:

```bash
pip install -r requirements.txt
```



### Build Database

Open:

```
Creating_duckDB.ipynb
```

Run all cells to:

* ingest raw data
* create clean tables
* persist database



### Connect to Database

```python
import duckdb
con = duckdb.connect("developer_project.duckdb")
```