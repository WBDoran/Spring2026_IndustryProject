## Work Completed So Far

### 1. Persistent DuckDB Database Setup

* Established persistent database:

  ```python
  duckdb.connect("developer_project.duckdb")
  ```
* Enables scalable querying and reuse across sessions
* Supports large datasets (100M+ rows) efficiently



### 2. Activity Data Ingestion

Source:

* `DEVPM_8674_Cal_Poly_Export_dev_activity.csv`

Approach:

* Loaded using `read_csv_auto`
* All columns initially cast to `VARCHAR`
* Created structured table with selected fields and type casting

Tables:

* `activity_raw`
* `activity_clean`

Role in project:

* Represents **developer engagement behavior**
* Primary input for engagement and maturity modeling



### 3. Contact Data Ingestion

Source:

* `DEVPM_8674_Cal_Poly_Export_dev_contact.csv`

Approach:

* Loaded with comma delimiter
* Casted timestamps and key identifiers

Tables:

* `contact_raw`
* `contact_clean`

Role in project:

* Developer dimension table
* Used for joins and enrichment (industry, geography, lifecycle)



### 4. SDK Download Data Ingestion

Source:

* `DEVPM_8674_Cal_Poly_Export_sdk_download.csv`

Approach:

* Loaded using `read_csv_auto`
* Cleaned and casted numeric fields

Tables:

* `sdk_download_raw`
* `sdk_download_clean`

Role in project:

* Proxy for **technology adoption signals**
* Critical for linking engagement → adoption



## Validation Snapshots

### Row Counts

* `activity_clean`: 69.3M rows
* `contact_clean`: 8.9M rows
* `sdk_download_clean`: 93.0M rows

Observation:

* Data volume is large enough to support robust behavioral modeling
* Performance considerations will be important



## Data Profiling and Validation (2026-04-07)

### Activity Table

Key Findings:

* Duplicate rows: 163K
* Extreme outliers in `activity_score` (up to ~949K)
* Missing fields:

  * `activity_attendance`: ~81%
  * `activity_role`: ~13%
  * `activity_name`: ~7%
* High cardinality:

  * ~247K unique activity names
* Inconsistent text formatting

Interpretation:

* Contains diverse engagement signals with **uneven quality**
* Not all activities represent equal intent
* Requires **normalization and signal weighting**



### Contact Table

Key Findings:

* No duplicate developer IDs
* High null rates:

  * `account_type`: ~68%
  * `devzone_last_login_date`: ~49%
  * `rdp_exit_date`: 100%

Interpretation:

* Reliable as a **dimension table**
* Some attributes are not usable for modeling
* Should not be primary driver of segmentation



### SDK Download Table

Key Findings:

* Duplicate rows: 275K
* Negative `download_count` values
* High null rates:

  * `os_distribution`: ~94%
  * `architecture`: ~94%

Interpretation:

* Strongest available signal for **product-level engagement**
* Still requires cleaning and validation
* Does not directly map to individual developers



## Data Cleaning Strategy

### Deduplication

* Remove full-row duplicates from:

  * `activity_clean`
  * `sdk_download_clean`

### Data Corrections

* Remove negative `download_count`
* Cap `activity_score` (e.g., at 100)

### Standardization

* Normalize text fields:

  ```sql
  LOWER(TRIM(activity_name))
  ```

### Column Pruning

Drop low-value fields:

* `activity_attendance`
* `rdp_exit_date`
* `os_distribution`
* `architecture`

### Null Handling

* > 80% null → drop
* 30–80% null → evaluate case-by-case
* <30% null → retain



## Data Relationships

Primary join:

* `activity_clean.dev_contact` → `contact_clean.developer_id`

Key Risk:

* SDK downloads are **not directly tied to developer IDs**
* Adoption must be inferred using indirect signals

Next Step:

* Validate join coverage and identify unmatched records



## Analytical Direction

### 1. Developer Maturity Segmentation

Move beyond simple activity counts.

Goal:

* Segment developers based on **behavioral progression over time**

Examples:

* explorers
* learners
* evaluators
* adopters

Features will include:

* activity frequency
* activity diversity
* recency
* progression across time windows



### 2. Engagement vs Adoption Analysis

Core question:

* Which engagement behaviors precede adoption?

Approach:

* Analyze sequences:

  * activities → downloads
* Identify high-impact activities:

  * DLI training
  * webinars
  * conferences



### 3. Time-Based Behavior Modeling

* Build rolling windows:

  * 30, 60, 90, 180 days
* Track evolution of users over time
* Detect transitions between maturity stages



### 4. Product-Level Analysis

* Aggregate downloads by product
* Identify:

  * top products
  * long-tail distribution
* Link to engagement patterns where possible



## Key Risks and Considerations

### 1. Engagement ≠ Adoption

* High activity does not guarantee real usage

### 2. Missing User-Level Link to Downloads

* Limits direct attribution of adoption

### 3. Activity Signal Imbalance

* Not all activities have equal importance

### 4. Data Quality Issues

* Nulls, duplicates, inconsistent text

### 5. Open Ecosystem Blind Spots

* Some adoption may occur outside tracked platforms
