# Project Log

## Project goal

Build a reproducible DuckDB-based foundation for analyzing whether developer engagement translates into real technology adoption, not just higher interaction counts.

---

## Work completed so far

### 1. Persistent DuckDB database setup

* Created a persistent DuckDB connection using:

  * `duckdb.connect("developer_project.duckdb")`
* Enables reuse of tables across sessions.

---

### 2. Activity file ingestion completed

Source file:

* `DEVPM_8674_Cal_Poly_Export_dev_activity.csv`

Approach:

* Loaded raw data using `read_csv_auto`
* Used pipe delimiter `|`
* Forced all columns to `VARCHAR`
* Built cleaned table with selected columns and typed casts

Tables created:

* `activity_raw`
* `activity_clean`

---

### 3. Contact file ingestion completed

Source file:

* `DEVPM_8674_Cal_Poly_Export_dev_contact.csv`

Approach:

* Loaded raw data using comma delimiter `,`
* Forced all columns to `VARCHAR`
* Built cleaned table with selected columns and timestamp casting

Tables created:

* `contact_raw`
* `contact_clean`

---

### 4. SDK download file ingestion completed

Source file:

* `DEVPM_8674_Cal_Poly_Export_sdk_download.csv`

Approach:

* Loaded raw data using comma delimiter `,`
* Built cleaned table with proper column mapping and casting

Tables created:

* `sdk_download_raw`
* `sdk_download_clean`

---

## Validation snapshots

### Row counts

* `activity_clean`: 69,347,526 rows
* `contact_clean`: 8,903,197 rows
* `sdk_download_clean`: 93,038,213 rows

---

## Data profiling and validation (2026-04-07)

### Activity table findings

* Duplicate rows: 163,806
* Extreme outliers in `activity_score` (values up to ~949K)
* Missing data:

  * `activity_attendance`: ~81%
  * `activity_role`: ~13%
  * `activity_name`: ~7%
* High cardinality in `activity_name` (~247K unique values)
* Inconsistent casing in activity names

Interpretation:

* Represents developer engagement events
* Requires normalization and outlier handling

---

### Contact table findings

* No duplicate rows detected
* High null columns:

  * `account_type`: ~68%
  * `devzone_last_login_date`: ~49%
  * `rdp_exit_date`: 100%
* `developer_id` behaves as a primary key

Interpretation:

* Dimension table for developer attributes
* Some fields are unreliable and should be excluded

---

### SDK download table findings

* Duplicate rows: 275,400
* Negative values in `download_count`
* High null columns:

  * `os_distribution`: ~94%
  * `architecture`: ~94%
  * `territory`: ~42%
* Large variance in download counts

Interpretation:

* Core dataset for product adoption
* Requires strict cleaning before aggregation

---

## Data cleaning strategy

### Deduplication

* Remove full-row duplicates from:

  * `activity_clean`
  * `sdk_download_clean`

### Data corrections

* Remove negative `download_count`
* Cap `activity_score` at 100

### Standardization

* Normalize text fields:

  * `LOWER(TRIM(activity_name))`

### Column pruning

Drop or ignore:

* `activity_attendance`
* `rdp_exit_date`
* `os_distribution`
* `architecture`

### Null handling

* > 80% null: drop
* 30–80% null: use cautiously
* <30% null: retain

---

## Data relationships

Primary join:

* `activity_clean.dev_contact` → `contact_clean.developer_id`

Next step:

* Validate join coverage and unmatched records

---

## Segmentation framework

### Developer segmentation

Features:

* total activities
* average activity score
* last activity date

Segments:

* power users
* casual users
* dormant users

---

### Product segmentation

* total downloads per product
* identify top and long-tail products

---

### Geographic segmentation

* downloads by country and region
* identify growth markets

---

### Time-based analysis

* monthly download trends
* identify growth and seasonality

---

## Risks and considerations

* No direct link between SDK downloads and users
* Adoption may need to be inferred
* High-cardinality fields may impact performance

---

## Current status

* Data ingestion: complete
* Data profiling: complete
* Data cleaning: in progress
* Feature engineering: next step
