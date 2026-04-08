# Developer Adoption Project: DuckDB Setup and Analysis Guide

## Overview

This project builds a DuckDB-based analytical foundation to evaluate whether developer engagement translates into real technology adoption.

The workflow includes:

1. Data ingestion from raw CSV exports
2. Cleaning and standardization
3. Feature engineering
4. Segmentation and adoption analysis

---

## Data sources

* DEVPM_8674_Cal_Poly_Export_dev_activity.csv
* DEVPM_8674_Cal_Poly_Export_dev_contact.csv
* DEVPM_8674_Cal_Poly_Export_sdk_download.csv

---

## Database

Output:

* `developer_project.duckdb`

---

## Tables

### Raw layer

* activity_raw
* contact_raw
* sdk_download_raw

### Clean layer

* activity_clean
* contact_clean
* sdk_download_clean

---

## Data processing approach

* All raw data loaded as VARCHAR
* Clean tables created with typed fields using TRY_CAST
* Persistent database used to avoid reprocessing large files

---

## Key data issues identified

### Activity data

* Duplicate rows present
* Outliers in activity_score
* High null columns
* Inconsistent text formatting

### Contact data

* Some columns with high missingness
* One fully null column (rdp_exit_date)

### SDK download data

* Duplicate rows present
* Negative download counts
* Several high-null columns

---

## Cleaning strategy

* Remove duplicate rows
* Filter invalid values (e.g., negative downloads)
* Cap extreme outliers
* Normalize text fields
* Drop or ignore low-quality columns

---

## Data model

* activity_clean: developer engagement events
* contact_clean: developer profile attributes
* sdk_download_clean: product usage and adoption

Primary join:

* activity_clean.dev_contact = contact_clean.developer_id

---

## Analytical goals

### Developer segmentation

* classify users by engagement level

### Product analysis

* identify top products and adoption patterns

### Geographic analysis

* identify high-growth regions

### Time-series analysis

* track adoption trends over time

---

## Next steps

1. Finalize cleaned tables
2. Validate joins between datasets
3. Build developer-level feature table
4. Define adoption metrics
5. Create segmentation logic
6. Perform cohort and trend analysis

---

## How to run
In your folder make sure to have Data folder with the csv file data

```bash
pip install -r requirements.txt
```

Creating_duckDB.ipynb

`Run All`

Then connect:

```python
import duckdb
con = duckdb.connect("developer_project.duckdb")
```

---

## Status

* Data ingestion complete
* Data profiling complete
* Data cleaning in progress
* Feature engineering next
