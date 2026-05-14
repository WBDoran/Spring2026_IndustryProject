"""Generate FeatureEngineering_Sample.ipynb"""
import json, uuid

def uid():
    return uuid.uuid4().hex[:8]

def code(src):
    return {"cell_type": "code", "execution_count": None,
            "id": uid(), "metadata": {}, "outputs": [], "source": src}

def md(src):
    return {"cell_type": "markdown", "id": uid(), "metadata": {}, "source": src}

cells = []

# ── Title ──────────────────────────────────────────────────────────────────
cells.append(md(
"# Feature Engineering Sample\n\n"
"Self-contained sample version of `FeatureEngineering_v3.ipynb`.\n"
"Loads `activity_sample.csv`, `contact_sample.csv`, and `sdk_download_sample.csv` "
"directly into an in-memory DuckDB connection — no persistent `.duckdb` file required.\n\n"
"Run all cells top-to-bottom."
))

# ── Cell 1: imports + load sample CSVs ────────────────────────────────────
cells.append(code(
"""import duckdb
import pandas as pd
import numpy as np
from pathlib import Path

con = duckdb.connect(":memory:")
pd.set_option("display.max_columns", 250)
pd.set_option("display.max_rows", 100)

DATA_DIR = "Data"
EFFORT_MAPPING_PATH = Path(f"{DATA_DIR}/Activity_Score_Mapping_filled.xlsx")
EFFORT_MAPPING_SHEET = "Activity_Score_Mapping"
ACTIVITY_TABLE = "activity_final"
CONTACT_TABLE  = "contact_final"

# Load sample CSVs as final tables
con.execute(f\"\"\"CREATE OR REPLACE TABLE activity_final AS
    SELECT * FROM read_csv_auto('{DATA_DIR}/activity_sample.csv', header=True)\"\"\")
con.execute(f\"\"\"CREATE OR REPLACE TABLE contact_final AS
    SELECT * FROM read_csv_auto('{DATA_DIR}/contact_sample.csv', header=True)\"\"\")
con.execute(f\"\"\"CREATE OR REPLACE TABLE sdk_download_final AS
    SELECT * FROM read_csv_auto('{DATA_DIR}/sdk_download_sample.csv', header=True)\"\"\")

for t in ["activity_final", "contact_final", "sdk_download_final"]:
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n:,} rows")
"""
))

# ── Cell 2: validate source tables ────────────────────────────────────────
cells.append(md("## 1. Validate source tables"))
cells.append(code(
"""tables = con.execute("SHOW TABLES").fetchdf()
available = set(tables.iloc[:, 0].astype(str))
missing = {ACTIVITY_TABLE, CONTACT_TABLE} - available
if missing:
    raise ValueError(f"Missing required table(s): {missing}")

def get_columns(tbl):
    return set(con.execute(f"DESCRIBE {tbl}").fetchdf()["column_name"].astype(str))

activity_cols = get_columns(ACTIVITY_TABLE)
contact_cols  = get_columns(CONTACT_TABLE)

required_activity_cols = {"dev_contact", "activity_date", "activity"}
required_contact_cols  = {"developer_id"}
if required_activity_cols - activity_cols:
    raise ValueError(f"Missing activity columns: {required_activity_cols - activity_cols}")
if required_contact_cols - contact_cols:
    raise ValueError(f"Missing contact columns: {required_contact_cols - contact_cols}")

for tbl in [ACTIVITY_TABLE, CONTACT_TABLE]:
    print(f"\\n{tbl}")
    display(con.execute(f"SELECT COUNT(*) AS rows FROM {tbl}").fetchdf())
    display(con.execute(f"DESCRIBE {tbl}").fetchdf())
"""
))

# ── Cell 3: load effort mapping ───────────────────────────────────────────
cells.append(md("## 2. Load AI effort mapping"))
cells.append(code(
"""if not EFFORT_MAPPING_PATH.exists():
    raise FileNotFoundError(f"Missing {EFFORT_MAPPING_PATH}")

raw_effort_map = pd.read_excel(EFFORT_MAPPING_PATH, sheet_name=EFFORT_MAPPING_SHEET)

def clean_text(s):
    return (s.astype("string").fillna("").str.strip()
             .str.lower().str.replace(r"\\s+", " ", regex=True))

effort_level_rank = {"passive": 0, "low": 1, "moderate": 2, "high": 3, "very high": 4}
confidence_weight = {"high": 1.00, "medium": 0.75, "low": 0.50, "": 0.50}

effort_map = raw_effort_map.copy()
effort_map["mapping_object_norm"]          = clean_text(effort_map["object"])
effort_map["mapping_field_norm"]           = clean_text(effort_map["field"])
effort_map["mapping_value_norm"]           = clean_text(effort_map["value"])
effort_map["ai_effort_level"]              = clean_text(effort_map["Effort Level"])
effort_map["ai_confidence"]                = clean_text(effort_map["Confidence"])
effort_map["ai_activity_score_guideline"]  = pd.to_numeric(effort_map["score"], errors="coerce")
effort_map["ai_effort_rank"]               = effort_map["ai_effort_level"].map(effort_level_rank).fillna(np.nan)
effort_map["ai_confidence_weight"]         = effort_map["ai_confidence"].map(confidence_weight).fillna(0.50)
effort_map["ai_weighted_effort_rank"]      = effort_map["ai_effort_rank"] * effort_map["ai_confidence_weight"]

effort_map_for_duckdb = effort_map[[
    "mapping_object_norm", "mapping_field_norm", "mapping_value_norm",
    "ai_effort_level", "ai_effort_rank", "ai_weighted_effort_rank",
    "ai_confidence", "ai_confidence_weight", "ai_activity_score_guideline",
    "Notes", "Other Notes"
]].rename(columns={"Notes": "ai_effort_notes", "Other Notes": "ai_effort_other_notes"})

con.register("effort_map_for_duckdb", effort_map_for_duckdb)
con.execute("CREATE OR REPLACE TABLE activity_effort_mapping_ai_v2 AS SELECT * FROM effort_map_for_duckdb")
con.unregister("effort_map_for_duckdb")

print("AI effort mapping loaded:", len(effort_map_for_duckdb), "rows")
display(con.execute("""
    SELECT COUNT(*) AS rows,
           COUNT(DISTINCT mapping_object_norm) AS objects,
           SUM(CASE WHEN ai_effort_rank IS NULL THEN 1 ELSE 0 END) AS missing_rank
    FROM activity_effort_mapping_ai_v2
""").fetchdf())
"""
))

# ── Cell 4: activity_base_v2 ──────────────────────────────────────────────
cells.append(md("## 3. Activity base and contact lookup"))
cells.append(code(
"""def activity_col_expr(col, out=None, cast="VARCHAR", default="NULL"):
    out = out or col
    if col in activity_cols:
        return f"CAST(a.{col} AS {cast}) AS {out}"
    return f"CAST({default} AS {cast}) AS {out}"

activity_score_expr = (
    "LEAST(GREATEST(COALESCE(TRY_CAST(a.activity_score AS DOUBLE), 0.0), 0.0), 100.0) AS activity_score"
    if "activity_score" in activity_cols else
    "CAST(0.0 AS DOUBLE) AS activity_score"
)

con.execute(f\"\"\"
CREATE OR REPLACE TABLE activity_base_v2 AS
SELECT
    CAST(a.dev_contact AS VARCHAR)             AS developer_id,
    CAST(a.activity_date AS DATE)              AS activity_date,
    LOWER(TRIM(CAST(a.activity AS VARCHAR)))   AS activity,
    {activity_col_expr('activity_name')},
    {activity_col_expr('activity_type')},
    {activity_col_expr('activity_role')},
    {activity_col_expr('activity_attendance')},
    {activity_score_expr},
    {activity_col_expr('filepath')},
    {activity_col_expr('lead_source')},
    {activity_col_expr('lead_source_details')},
    {activity_col_expr('nvidia_campaign_id')}
FROM {ACTIVITY_TABLE} a
WHERE a.dev_contact IS NOT NULL
  AND TRIM(CAST(a.dev_contact AS VARCHAR)) <> ''
  AND a.activity_date IS NOT NULL
\"\"\")

display(con.execute(\"\"\"
    SELECT COUNT(*) AS rows, COUNT(DISTINCT developer_id) AS developers,
           MIN(activity_date) AS min_date, MAX(activity_date) AS max_date
    FROM activity_base_v2
\"\"\").fetchdf())
"""
))

# ── Cell 5: contact_one_row_v2 ────────────────────────────────────────────
cells.append(code(
"""def contact_select_expr(col, out=None, cast="VARCHAR", default="NULL"):
    out = out or col
    if col in contact_cols:
        return f"CAST({col} AS {cast}) AS {out}"
    return f"CAST({default} AS {cast}) AS {out}"

order_terms = []
if "last_modified_date" in contact_cols:
    order_terms.append("last_modified_date DESC NULLS LAST")
if "created_date" in contact_cols:
    order_terms.append("created_date DESC NULLS LAST")
order_by = ", ".join(order_terms) if order_terms else "developer_id"

contact_fields = [
    "developer_id", "created_date", "first_activity_date", "last_activity_date",
    "development_areas", "fields_of_interest", "account_id", "account_type",
    "country", "region", "industry_segment_vertical", "program_application_source",
    "organization_english_name", "normalized_account_name", "wwfo_category", "wwfo_target_list"
]

select_list = []
for col in contact_fields:
    if col == "developer_id":
        select_list.append("CAST(developer_id AS VARCHAR) AS developer_id")
    elif col in {"created_date", "first_activity_date", "last_activity_date"} and col in contact_cols:
        select_list.append(f"CAST({col} AS DATE) AS {col}")
    else:
        select_list.append(contact_select_expr(col))

con.execute(f\"\"\"
CREATE OR REPLACE TABLE contact_one_row_v2 AS
WITH ranked AS (
    SELECT {", ".join(select_list)},
           ROW_NUMBER() OVER (PARTITION BY CAST(developer_id AS VARCHAR) ORDER BY {order_by}) AS rn
    FROM {CONTACT_TABLE}
    WHERE developer_id IS NOT NULL
      AND TRIM(CAST(developer_id AS VARCHAR)) <> ''
)
SELECT * EXCLUDE (rn) FROM ranked WHERE rn = 1
\"\"\")

display(con.execute(\"\"\"
    SELECT COUNT(*) AS rows, COUNT(DISTINCT developer_id) AS developers
    FROM contact_one_row_v2
\"\"\").fetchdf())
"""
))

# ── Cell 6: activity_dictionary_v2 + activity_labeled_v2 ──────────────────
cells.append(md("## 4. Activity dictionary and labeled events"))
cells.append(code(
r"""con.execute(r"""
CREATE OR REPLACE TABLE activity_dictionary_v2 AS
WITH activities AS (
    SELECT DISTINCT activity FROM activity_base_v2 WHERE activity IS NOT NULL
)
SELECT
    activity,
    CASE
        WHEN activity IN ('forum contributions') THEN 'Champion'
        WHEN activity IN ('user feedback', 'bugs filed') THEN 'Evaluate'
        WHEN activity IN ('hosted api', 'brev', 'ngc downloads', 'devzone downloads', 'sdk downloads') THEN 'Build'
        WHEN activity IN ('dli training') THEN 'Learn'
        WHEN activity IN ('webinars', 'on-demand views', 'conf. sessions live') THEN 'Learn'
        WHEN activity IN ('conference', 'other events', 'event registrations', 'program applications',
                          'dev program membership', 'product specific comms', 'contests') THEN 'Discover'
        ELSE 'Discover'
    END AS fallback_journey_signal,
    CASE
        WHEN activity IN ('forum contributions', 'hosted api', 'brev', 'ngc downloads', 'devzone downloads',
                          'sdk downloads', 'user feedback', 'bugs filed') THEN 'high'
        WHEN activity IN ('dli training', 'webinars', 'on-demand views', 'conf. sessions live',
                          'conference', 'other events', 'contests') THEN 'moderate'
        ELSE 'passive'
    END AS fallback_effort_level,
    CASE
        WHEN activity IN ('forum contributions', 'hosted api', 'brev', 'ngc downloads', 'devzone downloads',
                          'sdk downloads', 'user feedback', 'bugs filed') THEN 3.0
        WHEN activity IN ('dli training', 'webinars', 'on-demand views', 'conf. sessions live',
                          'conference', 'other events', 'contests') THEN 2.0
        ELSE 0.0
    END AS fallback_effort_rank,
    CASE
        WHEN activity IN ('ngc downloads', 'devzone downloads', 'sdk downloads') THEN 'Download'
        WHEN activity IN ('hosted api') THEN 'Hosted API'
        WHEN activity IN ('brev') THEN 'Cloud Workspace'
        WHEN activity IN ('forum contributions') THEN 'Community'
        WHEN activity IN ('dli training') THEN 'Training'
        WHEN activity IN ('webinars', 'conference', 'other events', 'event registrations', 'conf. sessions live') THEN 'Event'
        ELSE 'Content'
    END AS modality
FROM activities
""" + '""")')
))

cells.append(code(
r"""con.execute(r"""
CREATE OR REPLACE TABLE activity_labeled_v2 AS
WITH base AS (
    SELECT
        a.*,
        d.fallback_journey_signal,
        d.fallback_effort_level,
        d.fallback_effort_rank,
        d.modality,
        LOWER(TRIM(COALESCE(a.activity_type, ''))) AS activity_type_norm,
        LOWER(TRIM(COALESCE(a.activity_attendance, ''))) AS activity_attendance_norm,
        LOWER(TRIM(COALESCE(a.activity_role, ''))) AS activity_role_norm,
        LOWER(TRIM(COALESCE(a.activity_name, ''))) AS activity_name_norm,
        LOWER(TRIM(COALESCE(a.filepath, ''))) AS filepath_norm,
        LOWER(
            COALESCE(a.activity_name, '') || ' ' ||
            COALESCE(a.filepath, '') || ' ' ||
            COALESCE(a.lead_source_details, '') || ' ' ||
            COALESCE(a.activity_type, '') || ' ' ||
            COALESCE(a.activity_role, '') || ' ' ||
            COALESCE(a.lead_source, '')
        ) AS persona_activity_text
    FROM activity_base_v2 a
    LEFT JOIN activity_dictionary_v2 d USING (activity)
), candidates AS (
    SELECT
        b.developer_id, b.activity_date, b.activity, b.activity_name, b.activity_type, b.activity_role,
        b.activity_attendance, b.activity_score, b.filepath, b.lead_source, b.lead_source_details,
        b.nvidia_campaign_id, b.fallback_journey_signal, b.fallback_effort_level, b.fallback_effort_rank,
        b.modality, b.persona_activity_text,
        m.ai_effort_level, m.ai_effort_rank, m.ai_weighted_effort_rank, m.ai_confidence,
        m.ai_confidence_weight, m.ai_activity_score_guideline,
        'event_or_dli_or_file_type' AS ai_effort_match_source
    FROM base b
    JOIN activity_effort_mapping_ai_v2 m
      ON m.mapping_value_norm = b.activity_type_norm
     AND m.mapping_field_norm IN ('event type', 'course type', 'file type', 'form type', 'post type', 'status')
     AND (
            (b.activity IN ('conference', 'other events', 'conf. sessions live', 'webinars', 'on-demand views')
                AND m.mapping_object_norm IN ('dev event', 'dev event attendance'))
         OR (b.activity = 'dli training' AND m.mapping_object_norm = 'dev dli attendance')
         OR (b.activity IN ('devzone downloads', 'ngc downloads', 'sdk downloads') AND m.mapping_object_norm = 'dev file')
         OR (b.activity IN ('program applications', 'dev program membership') AND m.mapping_object_norm = 'dev program applications')
         OR (b.activity IN ('user feedback', 'event registrations') AND m.mapping_object_norm = 'dev form')
         OR (b.activity = 'forum contributions' AND m.mapping_object_norm = 'dev forum activities')
     )

    UNION ALL

    SELECT
        b.developer_id, b.activity_date, b.activity, b.activity_name, b.activity_type, b.activity_role,
        b.activity_attendance, b.activity_score, b.filepath, b.lead_source, b.lead_source_details,
        b.nvidia_campaign_id, b.fallback_journey_signal, b.fallback_effort_level, b.fallback_effort_rank,
        b.modality, b.persona_activity_text,
        m.ai_effort_level, m.ai_effort_rank, m.ai_weighted_effort_rank, m.ai_confidence,
        m.ai_confidence_weight, m.ai_activity_score_guideline,
        'attendance_status' AS ai_effort_match_source
    FROM base b
    JOIN activity_effort_mapping_ai_v2 m
      ON m.mapping_value_norm = b.activity_attendance_norm
     AND m.mapping_object_norm IN ('dev event attendance', 'dev dli attendance')
     AND m.mapping_field_norm IN ('status', 'course type')

    UNION ALL

    SELECT
        b.developer_id, b.activity_date, b.activity, b.activity_name, b.activity_type, b.activity_role,
        b.activity_attendance, b.activity_score, b.filepath, b.lead_source, b.lead_source_details,
        b.nvidia_campaign_id, b.fallback_journey_signal, b.fallback_effort_level, b.fallback_effort_rank,
        b.modality, b.persona_activity_text,
        m.ai_effort_level, m.ai_effort_rank, m.ai_weighted_effort_rank, m.ai_confidence,
        m.ai_confidence_weight, m.ai_activity_score_guideline,
        'role' AS ai_effort_match_source
    FROM base b
    JOIN activity_effort_mapping_ai_v2 m
      ON m.mapping_value_norm = b.activity_role_norm
     AND m.mapping_object_norm = 'dev event attendance'
     AND m.mapping_field_norm = 'role'
), best_candidate AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY developer_id, activity_date, activity, activity_name, activity_type,
                             activity_role, activity_attendance, filepath, lead_source,
                             lead_source_details, nvidia_campaign_id, activity_score
                ORDER BY ai_effort_rank DESC NULLS LAST,
                         ai_confidence_weight DESC NULLS LAST,
                         ai_activity_score_guideline DESC NULLS LAST
            ) AS rn
        FROM candidates
    ) x WHERE rn = 1
), enriched AS (
    SELECT
        b.*,
        bc.ai_effort_level, bc.ai_effort_rank, bc.ai_weighted_effort_rank,
        bc.ai_confidence, bc.ai_confidence_weight, bc.ai_activity_score_guideline, bc.ai_effort_match_source
    FROM base b
    LEFT JOIN best_candidate bc
      ON COALESCE(b.developer_id,'')        = COALESCE(bc.developer_id,'')
     AND COALESCE(CAST(b.activity_date AS VARCHAR),'') = COALESCE(CAST(bc.activity_date AS VARCHAR),'')
     AND COALESCE(b.activity,'')            = COALESCE(bc.activity,'')
     AND COALESCE(b.activity_name,'')       = COALESCE(bc.activity_name,'')
     AND COALESCE(b.activity_type,'')       = COALESCE(bc.activity_type,'')
     AND COALESCE(b.activity_role,'')       = COALESCE(bc.activity_role,'')
     AND COALESCE(b.activity_attendance,'') = COALESCE(bc.activity_attendance,'')
     AND COALESCE(b.filepath,'')            = COALESCE(bc.filepath,'')
     AND COALESCE(b.lead_source,'')         = COALESCE(bc.lead_source,'')
     AND COALESCE(b.lead_source_details,'') = COALESCE(bc.lead_source_details,'')
     AND COALESCE(b.nvidia_campaign_id,'')  = COALESCE(bc.nvidia_campaign_id,'')
     AND COALESCE(b.activity_score,-999999) = COALESCE(bc.activity_score,-999999)
), finalized AS (
    SELECT
        * EXCLUDE (fallback_journey_signal, fallback_effort_level, fallback_effort_rank,
                   activity_type_norm, activity_attendance_norm, activity_role_norm,
                   activity_name_norm, filepath_norm),
        CASE
            WHEN activity = 'devzone downloads' THEN
                CASE
                    WHEN filepath_norm LIKE '%.exe' OR filepath_norm LIKE '%installer%'
                      OR filepath_norm LIKE '%toolkit%' OR filepath_norm LIKE '%.deb'
                      OR filepath_norm LIKE '%.rpm' THEN 'Build'
                    WHEN filepath_norm LIKE '%.pdf' OR filepath_norm LIKE '%docs/%'
                      OR filepath_norm LIKE '%documentation%' THEN 'Discover'
                    ELSE 'Evaluate'
                END
            WHEN LOWER(COALESCE(ai_effort_level,'')) = 'very high' THEN 'Champion'
            ELSE fallback_journey_signal
        END AS journey_signal,
        COALESCE(ai_effort_level, fallback_effort_level) AS effort_level,
        COALESCE(ai_effort_rank, fallback_effort_rank, 0.0) AS effort_rank,
        COALESCE(ai_weighted_effort_rank, fallback_effort_rank, 0.0) AS confidence_weighted_effort_rank,
        CASE WHEN COALESCE(ai_confidence,'') IN ('low','medium') THEN 1 ELSE 0 END AS low_medium_confidence_effort_flag,
        CASE WHEN ABS(COALESCE(activity_score,0) - (COALESCE(ai_effort_rank, fallback_effort_rank, 0.0)*25.0)) >= 50 THEN 1 ELSE 0 END AS score_effort_misalignment_flag,
        COALESCE(activity_score,0) - (COALESCE(ai_effort_rank, fallback_effort_rank, 0.0)*25.0) AS score_effort_gap,
        COALESCE(activity_score,0) * COALESCE(ai_weighted_effort_rank, fallback_effort_rank, 0.0) AS effort_x_activity_score
    FROM enriched
), scored AS (
    SELECT *,
        CASE WHEN REGEXP_MATCHES(persona_activity_text, 'cuda|cudnn|rapids|nccl|cutlass|\bdali\b|gpu|accelerated|hpc') THEN COALESCE(NULLIF(activity_score,0),1) ELSE 0 END AS cuda_activity_score,
        CASE WHEN REGEXP_MATCHES(persona_activity_text, 'triton|tensorrt|nemo|\bnim\b|llm|large language|genai|generative|inference|model') THEN COALESCE(NULLIF(activity_score,0),1) ELSE 0 END AS genai_activity_score,
        CASE WHEN REGEXP_MATCHES(persona_activity_text, 'isaac|robot|ros|autonomous machine|jetson|edge ai|autonomous') THEN COALESCE(NULLIF(activity_score,0),1) ELSE 0 END AS robotics_activity_score,
        CASE WHEN REGEXP_MATCHES(persona_activity_text, 'omniverse|simulation|digital twin|modulus|render|rtx|graphics') THEN COALESCE(NULLIF(activity_score,0),1) ELSE 0 END AS simulation_activity_score,
        CASE WHEN REGEXP_MATCHES(persona_activity_text, 'dli|training|course|workshop|webinar|certification|learn|community') THEN COALESCE(NULLIF(activity_score,0),1) ELSE 0 END AS learning_community_activity_score
    FROM finalized
)
SELECT *,
    CASE
        WHEN GREATEST(cuda_activity_score, genai_activity_score, robotics_activity_score,
                      simulation_activity_score, learning_community_activity_score) = 0 THEN 'Other'
        WHEN cuda_activity_score >= GREATEST(genai_activity_score, robotics_activity_score,
                                             simulation_activity_score, learning_community_activity_score) THEN 'CUDA'
        WHEN genai_activity_score >= GREATEST(cuda_activity_score, robotics_activity_score,
                                              simulation_activity_score, learning_community_activity_score) THEN 'GenAI'
        WHEN robotics_activity_score >= GREATEST(cuda_activity_score, genai_activity_score,
                                                 simulation_activity_score, learning_community_activity_score) THEN 'Robotics'
        WHEN simulation_activity_score >= GREATEST(cuda_activity_score, genai_activity_score,
                                                   robotics_activity_score, learning_community_activity_score) THEN 'Simulation'
        ELSE 'Learning_Community'
    END AS persona_hint,
    cuda_activity_score        AS cuda_persona_score,
    genai_activity_score       AS genai_persona_score,
    robotics_activity_score    AS robotics_persona_score,
    simulation_activity_score  AS simulation_persona_score,
    learning_community_activity_score AS learning_community_persona_score
FROM scored
""" + '""")')
))

cells.append(code(
"""print("Dictionary coverage")
display(con.execute(\"\"\"
    SELECT COUNT(*) AS dictionary_rows, COUNT(DISTINCT activity) AS distinct_activities
    FROM activity_dictionary_v2
\"\"\").fetchdf())

print("AI effort mapping coverage")
display(con.execute(\"\"\"
    SELECT COUNT(*) AS activity_rows,
           SUM(CASE WHEN ai_effort_level IS NOT NULL THEN 1 ELSE 0 END) AS rows_with_ai_effort,
           ROUND(100.0 * SUM(CASE WHEN ai_effort_level IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_ai_effort
    FROM activity_labeled_v2
\"\"\").fetchdf())

print("Label distribution")
display(con.execute(\"\"\"
    SELECT journey_signal, effort_level, persona_hint, modality, COUNT(*) AS rows
    FROM activity_labeled_v2
    GROUP BY 1,2,3,4
    ORDER BY rows DESC
    LIMIT 20
\"\"\").fetchdf())
"""
))

# ── Cell 7: developer_universe_v2 ──────────────────────────────────────────
cells.append(md("## 5. Developer universe and anchor date"))
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE developer_universe_v2 AS
SELECT DISTINCT developer_id FROM activity_base_v2 WHERE developer_id IS NOT NULL
UNION
SELECT DISTINCT developer_id FROM contact_one_row_v2 WHERE developer_id IS NOT NULL
\"\"\")

date_summary = con.execute(\"\"\"
    SELECT MIN(activity_date) AS min_date, MAX(activity_date) AS max_date
    FROM activity_labeled_v2
\"\"\").fetchdf()
ANCHOR_DATE = date_summary.loc[0, "max_date"]
print("ANCHOR_DATE:", ANCHOR_DATE)

display(con.execute(\"\"\"
    SELECT COUNT(*) AS universe_developers,
           SUM(CASE WHEN a.developer_id IS NOT NULL THEN 1 ELSE 0 END) AS developers_with_activity,
           SUM(CASE WHEN c.developer_id IS NOT NULL THEN 1 ELSE 0 END) AS developers_with_contact
    FROM developer_universe_v2 u
    LEFT JOIN (SELECT DISTINCT developer_id FROM activity_base_v2) a USING (developer_id)
    LEFT JOIN contact_one_row_v2 c USING (developer_id)
\"\"\").fetchdf())
"""
))

# ── Cell 8: windowed features ─────────────────────────────────────────────
cells.append(md("## 6. Windowed features (0–30 d, 30–90 d, 90–180 d)"))
cells.append(code(
"""WINDOWS = [("0_30d", 0, 30), ("30_90d", 30, 90), ("90_180d", 90, 180)]

def build_window_features(label, start_days_ago, end_days_ago):
    table_name = f"dev_features_{label}_v2"
    con.execute(f\"\"\"
    CREATE OR REPLACE TABLE {table_name} AS
    WITH max_dt AS (SELECT MAX(activity_date) AS anchor_date FROM activity_labeled_v2),
    agg AS (
        SELECT
            developer_id,
            COUNT(*) AS activity_count,
            SUM(activity_score) AS activity_score_sum,
            AVG(activity_score) AS activity_score_avg,
            COUNT(DISTINCT activity_date) AS unique_activity_days,
            COUNT(DISTINCT activity) AS unique_activity_types,
            COUNT(DISTINCT modality) AS unique_modalities,
            COUNT(DISTINCT DATE_TRUNC('week', activity_date)) AS active_weeks,
            MIN(activity_date) AS first_activity_date_window,
            MAX(activity_date) AS last_activity_date_window,
            SUM(CASE WHEN journey_signal = 'Discover'  THEN 1 ELSE 0 END) AS discover_count,
            SUM(CASE WHEN journey_signal = 'Learn'     THEN 1 ELSE 0 END) AS learn_count,
            SUM(CASE WHEN journey_signal = 'Evaluate'  THEN 1 ELSE 0 END) AS evaluate_count,
            SUM(CASE WHEN journey_signal = 'Build'     THEN 1 ELSE 0 END) AS build_count,
            SUM(CASE WHEN journey_signal = 'Champion'  THEN 1 ELSE 0 END) AS champion_count,
            SUM(CASE WHEN effort_rank >= 3             THEN 1 ELSE 0 END) AS high_effort_count,
            AVG(effort_rank) AS avg_effort_rank,
            MAX(effort_rank) AS max_effort_rank,
            SUM(confidence_weighted_effort_rank) AS total_confidence_weighted_effort,
            AVG(score_effort_gap) AS avg_score_effort_gap,
            SUM(score_effort_misalignment_flag) AS score_effort_misalignment_count,
            SUM(low_medium_confidence_effort_flag) AS low_medium_confidence_effort_count,
            SUM(effort_x_activity_score) AS effort_x_activity_score_sum,
            SUM(CASE WHEN modality = 'Download'        THEN 1 ELSE 0 END) AS download_count,
            SUM(CASE WHEN modality = 'Hosted API'      THEN 1 ELSE 0 END) AS hosted_api_count,
            SUM(CASE WHEN modality = 'Cloud Workspace' THEN 1 ELSE 0 END) AS cloud_workspace_count,
            SUM(CASE WHEN modality = 'Community'       THEN 1 ELSE 0 END) AS community_count,
            SUM(CASE WHEN modality = 'Training'        THEN 1 ELSE 0 END) AS training_count,
            SUM(CASE WHEN modality = 'Event'           THEN 1 ELSE 0 END) AS event_count,
            SUM(cuda_persona_score)              AS cuda_score,
            SUM(genai_persona_score)             AS genai_score,
            SUM(robotics_persona_score)          AS robotics_score,
            SUM(simulation_persona_score)        AS simulation_score,
            SUM(learning_community_persona_score) AS learning_community_score
        FROM activity_labeled_v2, max_dt
        WHERE activity_date >  anchor_date - INTERVAL {end_days_ago} DAY
          AND activity_date <= anchor_date - INTERVAL {start_days_ago} DAY
        GROUP BY developer_id
    )
    SELECT
        u.developer_id,
        COALESCE(a.activity_count, 0) AS activity_count,
        COALESCE(a.activity_score_sum, 0) AS activity_score_sum,
        COALESCE(a.activity_score_avg, 0) AS activity_score_avg,
        COALESCE(a.unique_activity_days, 0) AS unique_activity_days,
        COALESCE(a.unique_activity_types, 0) AS unique_activity_types,
        COALESCE(a.unique_modalities, 0) AS unique_modalities,
        COALESCE(a.active_weeks, 0) AS active_weeks,
        a.first_activity_date_window,
        a.last_activity_date_window,
        CASE WHEN a.last_activity_date_window IS NULL THEN 1 ELSE 0 END AS is_missing_last_activity_window,
        DATE_DIFF('day', a.last_activity_date_window, (SELECT anchor_date FROM max_dt)) AS days_since_last_activity_window,
        COALESCE(a.discover_count, 0) AS discover_count,
        COALESCE(a.learn_count, 0) AS learn_count,
        COALESCE(a.evaluate_count, 0) AS evaluate_count,
        COALESCE(a.build_count, 0) AS build_count,
        COALESCE(a.champion_count, 0) AS champion_count,
        COALESCE(a.high_effort_count, 0) AS high_effort_count,
        COALESCE(a.avg_effort_rank, 0) AS avg_effort_rank,
        COALESCE(a.max_effort_rank, 0) AS max_effort_rank,
        COALESCE(a.total_confidence_weighted_effort, 0) AS total_confidence_weighted_effort,
        COALESCE(a.avg_score_effort_gap, 0) AS avg_score_effort_gap,
        COALESCE(a.score_effort_misalignment_count, 0) AS score_effort_misalignment_count,
        COALESCE(a.low_medium_confidence_effort_count, 0) AS low_medium_confidence_effort_count,
        COALESCE(a.effort_x_activity_score_sum, 0) AS effort_x_activity_score_sum,
        COALESCE(a.download_count, 0) AS download_count,
        COALESCE(a.hosted_api_count, 0) AS hosted_api_count,
        COALESCE(a.cloud_workspace_count, 0) AS cloud_workspace_count,
        COALESCE(a.community_count, 0) AS community_count,
        COALESCE(a.training_count, 0) AS training_count,
        COALESCE(a.event_count, 0) AS event_count,
        COALESCE(a.cuda_score, 0) AS cuda_score,
        COALESCE(a.genai_score, 0) AS genai_score,
        COALESCE(a.robotics_score, 0) AS robotics_score,
        COALESCE(a.simulation_score, 0) AS simulation_score,
        COALESCE(a.learning_community_score, 0) AS learning_community_score,
        CASE WHEN COALESCE(a.activity_count, 0) > 0 THEN 1 ELSE 0 END AS has_activity,
        LN(1 + COALESCE(a.activity_count, 0)) AS log_activity_count,
        LN(1 + COALESCE(a.activity_score_sum, 0)) AS log_activity_score_sum,
        LN(1 + COALESCE(a.build_count, 0)) AS log_build_count,
        LN(1 + COALESCE(a.high_effort_count, 0)) AS log_high_effort_count,
        COALESCE(a.activity_count, 0) * 1.0 / NULLIF(COALESCE(a.unique_activity_days, 0), 0) AS activity_per_active_day,
        COALESCE(a.build_count, 0) * 1.0 / NULLIF(COALESCE(a.activity_count, 0), 0) AS build_share,
        COALESCE(a.high_effort_count, 0) * 1.0 / NULLIF(COALESCE(a.activity_count, 0), 0) AS high_effort_share
    FROM developer_universe_v2 u
    LEFT JOIN agg a USING (developer_id)
    \"\"\")

for label, start, end in WINDOWS:
    build_window_features(label, start, end)
    print(f"Built dev_features_{label}_v2")
    display(con.execute(f\"\"\"
        SELECT COUNT(*) AS rows, AVG(has_activity) AS pct_with_activity, MAX(activity_count) AS max_count
        FROM dev_features_{label}_v2
    \"\"\").fetchdf())
"""
))

# ── Cell 9: dev_recency_features_v2 ──────────────────────────────────────
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_recency_features_v2 AS
SELECT
    u.developer_id,
    f0.activity_count  AS activity_count_0_30d,
    f1.activity_count  AS activity_count_30_90d,
    f2.activity_count  AS activity_count_90_180d,
    f0.has_activity    AS has_activity_0_30d,
    f1.has_activity    AS has_activity_30_90d,
    f2.has_activity    AS has_activity_90_180d,
    f0.log_activity_count AS log_activity_count_0_30d,
    f1.log_activity_count AS log_activity_count_30_90d,
    f2.log_activity_count AS log_activity_count_90_180d,
    f0.build_count     AS build_count_0_30d,
    f1.build_count     AS build_count_30_90d,
    f2.build_count     AS build_count_90_180d,
    f0.log_build_count AS log_build_count_0_30d,
    f1.log_build_count AS log_build_count_30_90d,
    f2.log_build_count AS log_build_count_90_180d,
    f0.high_effort_count AS high_effort_count_0_30d,
    f1.high_effort_count AS high_effort_count_30_90d,
    f2.high_effort_count AS high_effort_count_90_180d,
    f0.unique_activity_days  AS unique_activity_days_0_30d,
    f0.unique_activity_types AS unique_activity_types_0_30d,
    f0.unique_modalities     AS unique_modalities_0_30d,
    f0.activity_per_active_day AS activity_per_active_day_0_30d,
    f0.build_share             AS build_share_0_30d,
    f0.high_effort_share       AS high_effort_share_0_30d,
    f0.avg_effort_rank AS avg_effort_rank_0_30d,
    f1.avg_effort_rank AS avg_effort_rank_30_90d,
    f2.avg_effort_rank AS avg_effort_rank_90_180d,
    f0.total_confidence_weighted_effort AS total_confidence_weighted_effort_0_30d,
    f1.total_confidence_weighted_effort AS total_confidence_weighted_effort_30_90d,
    f2.total_confidence_weighted_effort AS total_confidence_weighted_effort_90_180d,
    (f0.total_confidence_weighted_effort * 1.0 / NULLIF(f0.activity_count, 0))
        AS confidence_weighted_effort_per_activity_0_30d,
    f0.avg_score_effort_gap AS avg_score_effort_gap_0_30d,
    f0.score_effort_misalignment_count AS score_effort_misalignment_count_0_30d,
    (f0.score_effort_misalignment_count * 1.0 / NULLIF(f0.activity_count, 0))
        AS score_effort_misalignment_share_0_30d,
    f0.low_medium_confidence_effort_count AS low_medium_confidence_effort_count_0_30d,
    f0.effort_x_activity_score_sum AS effort_x_activity_score_sum_0_30d,
    f0.days_since_last_activity_window AS days_since_last_activity_0_30d,
    f0.is_missing_last_activity_window AS is_missing_last_activity_0_30d,
    f0.activity_count * 1.0 / NULLIF(f1.activity_count, 0) AS activity_velocity_0_30_vs_30_90,
    f0.build_count    * 1.0 / NULLIF(f1.build_count, 0)    AS build_velocity_0_30_vs_30_90,
    (0.60 * f0.activity_count + 0.30 * f1.activity_count + 0.10 * f2.activity_count)
        AS weighted_recent_activity,
    (0.60 * f0.build_count    + 0.30 * f1.build_count    + 0.10 * f2.build_count)
        AS weighted_recent_build,
    (0.60 * f0.total_confidence_weighted_effort + 0.30 * f1.total_confidence_weighted_effort
           + 0.10 * f2.total_confidence_weighted_effort)
        AS weighted_recent_confidence_effort,
    CASE WHEN f0.activity_count > 0 AND f0.build_count = 0 THEN 1 ELSE 0 END AS active_non_builder_0_30d,
    CASE WHEN f0.activity_count = 0 AND f1.activity_count > 0 THEN 1 ELSE 0 END AS newly_inactive_0_30d,
    CASE WHEN f0.build_count > 0 AND f0.activity_count <= 2  THEN 1 ELSE 0 END AS low_volume_builder_0_30d,
    CASE WHEN f0.high_effort_count > 0                        THEN 1 ELSE 0 END AS has_high_effort_0_30d,
    CASE WHEN f0.build_count > 0 OR f0.hosted_api_count > 0 OR f0.cloud_workspace_count > 0
         THEN 1 ELSE 0 END AS recent_build_flag,
    CASE WHEN f0.champion_count > 0 THEN 1 ELSE 0 END AS recent_champion_flag
FROM developer_universe_v2 u
LEFT JOIN dev_features_0_30d_v2   f0 USING (developer_id)
LEFT JOIN dev_features_30_90d_v2  f1 USING (developer_id)
LEFT JOIN dev_features_90_180d_v2 f2 USING (developer_id)
\"\"\")

display(con.execute(\"\"\"
    SELECT COUNT(*) AS rows,
           AVG(has_activity_0_30d) AS pct_active_0_30d,
           AVG(newly_inactive_0_30d) AS pct_newly_inactive
    FROM dev_recency_features_v2
\"\"\").fetchdf())
"""
))

# ── Cell 10: dev_features_lifetime_v2 ────────────────────────────────────
cells.append(md("## 7. Lifetime features"))
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_features_lifetime_v2 AS
WITH agg AS (
    SELECT
        developer_id,
        COUNT(*) AS lifetime_activity_count,
        SUM(activity_score) AS lifetime_activity_score_sum,
        AVG(activity_score) AS lifetime_activity_score_avg,
        COUNT(DISTINCT activity_date) AS lifetime_unique_activity_days,
        COUNT(DISTINCT activity) AS lifetime_unique_activity_types,
        COUNT(DISTINCT modality) AS lifetime_unique_modalities,
        COUNT(DISTINCT DATE_TRUNC('week', activity_date)) AS lifetime_active_weeks,
        MIN(activity_date) AS lifetime_first_activity_date,
        MAX(activity_date) AS lifetime_last_activity_date,
        SUM(CASE WHEN journey_signal = 'Discover'  THEN 1 ELSE 0 END) AS lifetime_discover_count,
        SUM(CASE WHEN journey_signal = 'Learn'     THEN 1 ELSE 0 END) AS lifetime_learn_count,
        SUM(CASE WHEN journey_signal = 'Evaluate'  THEN 1 ELSE 0 END) AS lifetime_evaluate_count,
        SUM(CASE WHEN journey_signal = 'Build'     THEN 1 ELSE 0 END) AS lifetime_build_count,
        SUM(CASE WHEN journey_signal = 'Champion'  THEN 1 ELSE 0 END) AS lifetime_champion_count,
        SUM(CASE WHEN effort_rank >= 3             THEN 1 ELSE 0 END) AS lifetime_high_effort_count,
        AVG(effort_rank) AS lifetime_avg_effort_rank,
        MAX(effort_rank) AS lifetime_max_effort_rank,
        SUM(confidence_weighted_effort_rank) AS lifetime_total_confidence_weighted_effort,
        AVG(score_effort_gap) AS lifetime_avg_score_effort_gap,
        SUM(score_effort_misalignment_flag) AS lifetime_score_effort_misalignment_count,
        SUM(low_medium_confidence_effort_flag) AS lifetime_low_medium_confidence_effort_count,
        SUM(effort_x_activity_score) AS lifetime_effort_x_activity_score_sum,
        SUM(CASE WHEN activity = 'dli training'   THEN 1 ELSE 0 END) AS lifetime_dli_training_count,
        SUM(CASE WHEN activity = 'webinars'        THEN 1 ELSE 0 END) AS lifetime_webinar_count,
        SUM(CASE WHEN activity = 'forum contributions' THEN 1 ELSE 0 END) AS lifetime_forum_count,
        SUM(CASE WHEN activity = 'bugs filed'      THEN 1 ELSE 0 END) AS lifetime_bug_count,
        SUM(CASE WHEN activity = 'hackathons'      THEN 1 ELSE 0 END) AS lifetime_hackathon_count,
        SUM(CASE WHEN activity IN ('model api','hosted api') THEN 1 ELSE 0 END) AS lifetime_api_count,
        SUM(CASE WHEN activity = 'devzone downloads' THEN 1 ELSE 0 END) AS lifetime_devzone_download_count,
        SUM(CASE WHEN activity = 'ngc downloads'   THEN 1 ELSE 0 END) AS lifetime_ngc_download_count,
        SUM(cuda_persona_score)              AS cuda_score,
        SUM(genai_persona_score)             AS genai_score,
        SUM(robotics_persona_score)          AS robotics_score,
        SUM(simulation_persona_score)        AS simulation_score,
        SUM(learning_community_persona_score) AS learning_community_score,
        SUM(CASE WHEN persona_hint = 'Other' THEN COALESCE(NULLIF(activity_score,0),1) ELSE 0 END) AS other_persona_score
    FROM activity_labeled_v2
    GROUP BY developer_id
),
filled AS (
    SELECT
        u.developer_id,
        COALESCE(a.lifetime_activity_count, 0) AS lifetime_activity_count,
        COALESCE(a.lifetime_activity_score_sum, 0) AS lifetime_activity_score_sum,
        COALESCE(a.lifetime_activity_score_avg, 0) AS lifetime_activity_score_avg,
        COALESCE(a.lifetime_unique_activity_days, 0) AS lifetime_unique_activity_days,
        COALESCE(a.lifetime_unique_activity_types, 0) AS lifetime_unique_activity_types,
        COALESCE(a.lifetime_unique_modalities, 0) AS lifetime_unique_modalities,
        COALESCE(a.lifetime_active_weeks, 0) AS lifetime_active_weeks,
        a.lifetime_first_activity_date,
        a.lifetime_last_activity_date,
        COALESCE(a.lifetime_discover_count, 0) AS lifetime_discover_count,
        COALESCE(a.lifetime_learn_count, 0) AS lifetime_learn_count,
        COALESCE(a.lifetime_evaluate_count, 0) AS lifetime_evaluate_count,
        COALESCE(a.lifetime_build_count, 0) AS lifetime_build_count,
        COALESCE(a.lifetime_champion_count, 0) AS lifetime_champion_count,
        COALESCE(a.lifetime_high_effort_count, 0) AS lifetime_high_effort_count,
        COALESCE(a.lifetime_avg_effort_rank, 0) AS lifetime_avg_effort_rank,
        COALESCE(a.lifetime_max_effort_rank, 0) AS lifetime_max_effort_rank,
        COALESCE(a.lifetime_total_confidence_weighted_effort, 0) AS lifetime_total_confidence_weighted_effort,
        COALESCE(a.lifetime_avg_score_effort_gap, 0) AS lifetime_avg_score_effort_gap,
        COALESCE(a.lifetime_score_effort_misalignment_count, 0) AS lifetime_score_effort_misalignment_count,
        COALESCE(a.lifetime_low_medium_confidence_effort_count, 0) AS lifetime_low_medium_confidence_effort_count,
        COALESCE(a.lifetime_effort_x_activity_score_sum, 0) AS lifetime_effort_x_activity_score_sum,
        COALESCE(a.lifetime_dli_training_count, 0) AS lifetime_dli_training_count,
        COALESCE(a.lifetime_webinar_count, 0) AS lifetime_webinar_count,
        COALESCE(a.lifetime_forum_count, 0) AS lifetime_forum_count,
        COALESCE(a.lifetime_bug_count, 0) AS lifetime_bug_count,
        COALESCE(a.lifetime_hackathon_count, 0) AS lifetime_hackathon_count,
        COALESCE(a.lifetime_api_count, 0) AS lifetime_api_count,
        COALESCE(a.lifetime_devzone_download_count, 0) AS lifetime_devzone_download_count,
        COALESCE(a.lifetime_ngc_download_count, 0) AS lifetime_ngc_download_count,
        COALESCE(a.cuda_score, 0) AS cuda_score,
        COALESCE(a.genai_score, 0) AS genai_score,
        COALESCE(a.robotics_score, 0) AS robotics_score,
        COALESCE(a.simulation_score, 0) AS simulation_score,
        COALESCE(a.learning_community_score, 0) AS learning_community_score,
        COALESCE(a.other_persona_score, 0) AS other_persona_score
    FROM developer_universe_v2 u
    LEFT JOIN agg a USING (developer_id)
),
p99 AS (
    SELECT
        APPROX_QUANTILE(lifetime_activity_count, 0.99) AS p99_activity_count,
        APPROX_QUANTILE(lifetime_build_count, 0.99) AS p99_build_count,
        APPROX_QUANTILE(lifetime_high_effort_count, 0.99) AS p99_high_effort_count,
        APPROX_QUANTILE(lifetime_total_confidence_weighted_effort, 0.99) AS p99_total_confidence_weighted_effort,
        APPROX_QUANTILE(lifetime_effort_x_activity_score_sum, 0.99) AS p99_effort_x_activity_score_sum,
        APPROX_QUANTILE(lifetime_activity_score_sum, 0.99) AS p99_activity_score_sum
    FROM filled
)
SELECT
    f.*,
    CASE
        WHEN f.lifetime_unique_activity_days = 1 THEN 'tourist'
        WHEN f.lifetime_build_count + f.lifetime_champion_count <= 2
          AND f.lifetime_high_effort_count = 0
          AND f.lifetime_devzone_download_count >= 1 THEN 'free_email_user'
        ELSE 'real_user'
    END AS user_type,
    CASE
        WHEN f.lifetime_champion_count >= 1 THEN 'Champion'
        WHEN f.lifetime_build_count    >= 1 THEN 'Build'
        WHEN f.lifetime_evaluate_count >= 1 THEN 'Evaluate'
        WHEN f.lifetime_learn_count    >= 1 THEN 'Learn'
        WHEN f.lifetime_discover_count >= 1 THEN 'Discover'
        ELSE 'None'
    END AS max_stage_reached,
    CASE WHEN lifetime_activity_count > 0 THEN 1 ELSE 0 END AS has_lifetime_activity,
    LN(1 + lifetime_activity_count) AS log_lifetime_activity_count,
    LN(1 + lifetime_activity_score_sum) AS log_lifetime_activity_score_sum,
    LN(1 + lifetime_build_count) AS log_lifetime_build_count,
    LN(1 + lifetime_high_effort_count) AS log_lifetime_high_effort_count,
    lifetime_total_confidence_weighted_effort * 1.0 / NULLIF(lifetime_activity_count, 0) AS effort_per_activity_lifetime,
    lifetime_score_effort_misalignment_count  * 1.0 / NULLIF(lifetime_activity_count, 0) AS score_effort_misalignment_share_lifetime,
    LN(1 + lifetime_total_confidence_weighted_effort) AS log_lifetime_total_confidence_weighted_effort,
    LN(1 + lifetime_effort_x_activity_score_sum) AS log_lifetime_effort_x_activity_score_sum,
    LEAST(lifetime_activity_count, p99.p99_activity_count) AS clipped_lifetime_activity_count_p99,
    LEAST(lifetime_build_count,    p99.p99_build_count)    AS clipped_lifetime_build_count_p99,
    LEAST(lifetime_activity_score_sum, p99.p99_activity_score_sum) AS clipped_lifetime_activity_score_sum_p99,
    LEAST(lifetime_total_confidence_weighted_effort, p99.p99_total_confidence_weighted_effort)
        AS clipped_lifetime_total_confidence_weighted_effort_p99,
    LEAST(lifetime_effort_x_activity_score_sum, p99.p99_effort_x_activity_score_sum)
        AS clipped_lifetime_effort_x_activity_score_sum_p99,
    LN(1 + LEAST(lifetime_activity_count, p99.p99_activity_count)) AS log_clipped_lifetime_activity_count_p99,
    LN(1 + LEAST(lifetime_activity_score_sum, p99.p99_activity_score_sum)) AS log_clipped_lifetime_activity_score_sum_p99,
    LN(1 + LEAST(lifetime_total_confidence_weighted_effort, p99.p99_total_confidence_weighted_effort))
        AS log_clipped_lifetime_total_confidence_weighted_effort_p99,
    LN(1 + LEAST(lifetime_effort_x_activity_score_sum, p99.p99_effort_x_activity_score_sum))
        AS log_clipped_lifetime_effort_x_activity_score_sum_p99,
    lifetime_activity_count * 1.0 / NULLIF(lifetime_active_weeks, 0) AS activity_per_active_week_lifetime,
    lifetime_build_count    * 1.0 / NULLIF(lifetime_activity_count, 0) AS build_share_lifetime,
    lifetime_high_effort_count * 1.0 / NULLIF(lifetime_activity_count, 0) AS high_effort_share_lifetime
FROM filled f
CROSS JOIN p99
\"\"\")

display(con.execute(\"\"\"
    SELECT COUNT(*) AS rows, MAX(lifetime_activity_count) AS max_activity_count,
           SUM(CASE WHEN user_type='tourist' THEN 1 ELSE 0 END) AS tourists
    FROM dev_features_lifetime_v2
\"\"\").fetchdf())
"""
))

# ── Cell 11: dev_weekly_features_v2 ──────────────────────────────────────
cells.append(md("## 8. Weekly features and activation gating\n\n"
                "Adapted from `FeatureENgineering.ipynb` v1 — source changed to `activity_labeled_v2`."))
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_weekly_features_v2 AS
WITH weekly AS (
    SELECT
        developer_id,
        DATE_TRUNC('week', activity_date) AS week_start,
        COUNT(*) AS activity_count_total,
        SUM(activity_score) AS activity_score_sum,
        COUNT(DISTINCT activity) AS unique_activity_types,
        COUNT(DISTINCT modality) AS unique_modalities,
        SUM(CASE WHEN journey_signal = 'Discover'  THEN 1 ELSE 0 END) AS discover_count,
        SUM(CASE WHEN journey_signal = 'Learn'     THEN 1 ELSE 0 END) AS learn_count,
        SUM(CASE WHEN journey_signal = 'Evaluate'  THEN 1 ELSE 0 END) AS evaluate_count,
        SUM(CASE WHEN journey_signal = 'Build'     THEN 1 ELSE 0 END) AS build_count,
        SUM(CASE WHEN journey_signal = 'Champion'  THEN 1 ELSE 0 END) AS champion_count,
        SUM(CASE WHEN effort_rank >= 3             THEN 1 ELSE 0 END) AS high_effort_count,
        SUM(CASE WHEN modality = 'Download'        THEN 1 ELSE 0 END) AS download_count,
        SUM(CASE WHEN modality = 'Hosted API'      THEN 1 ELSE 0 END) AS hosted_api_count,
        SUM(CASE WHEN modality = 'Cloud Workspace' THEN 1 ELSE 0 END) AS cloud_workspace_count,
        SUM(CASE WHEN persona_hint = 'CUDA'        THEN activity_score ELSE 0 END) AS cuda_score,
        SUM(CASE WHEN persona_hint = 'GenAI'       THEN activity_score ELSE 0 END) AS genai_score,
        SUM(CASE WHEN persona_hint = 'Robotics'    THEN activity_score ELSE 0 END) AS robotics_score,
        SUM(CASE WHEN persona_hint = 'Simulation'  THEN activity_score ELSE 0 END) AS simulation_score
    FROM activity_labeled_v2
    GROUP BY 1, 2
)
SELECT *,
    LN(1 + activity_count_total) AS activity_count_log,
    LN(1 + activity_score_sum)   AS activity_score_log,
    LN(1 + build_count)          AS build_count_log,
    LN(1 + high_effort_count)    AS high_effort_count_log
FROM weekly
\"\"\")

display(con.execute(\"\"\"
    SELECT COUNT(*) AS developer_weeks,
           COUNT(DISTINCT developer_id) AS developers,
           MIN(week_start) AS min_week,
           MAX(week_start) AS max_week
    FROM dev_weekly_features_v2
\"\"\").fetchdf())
"""
))

# ── Cell 12: dev_meaningful_week_v2 ──────────────────────────────────────
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_meaningful_week_v2 AS
WITH weekly AS (
    SELECT
        developer_id,
        DATE_TRUNC('week', activity_date) AS week_start,
        COUNT(*) AS activity_count_total,
        COUNT(DISTINCT activity_date) AS active_days,
        SUM(CASE WHEN journey_signal = 'Build'    THEN 1 ELSE 0 END) AS build_count,
        SUM(CASE WHEN journey_signal = 'Champion' THEN 1 ELSE 0 END) AS champion_count,
        SUM(CASE WHEN effort_rank = 2             THEN 1 ELSE 0 END) AS moderate_effort_count,
        SUM(CASE WHEN effort_rank >= 3            THEN 1 ELSE 0 END) AS high_effort_count,
        COUNT(DISTINCT CASE
            WHEN journey_signal IN ('Learn', 'Evaluate') AND effort_rank <= 1
            THEN activity_date
        END) AS passive_learn_eval_days
    FROM activity_labeled_v2
    GROUP BY 1, 2
)
SELECT *,
    CASE
        WHEN build_count > 0 OR champion_count > 0 THEN 1
        WHEN moderate_effort_count > 0 OR high_effort_count > 0 THEN 1
        WHEN passive_learn_eval_days >= 2 THEN 1
        ELSE 0
    END AS meaningful_week_flag
FROM weekly
\"\"\")

display(con.execute(\"\"\"
    SELECT COUNT(*) AS developer_weeks,
           SUM(meaningful_week_flag) AS meaningful_weeks,
           ROUND(AVG(meaningful_week_flag), 3) AS meaningful_week_rate
    FROM dev_meaningful_week_v2
\"\"\").fetchdf())
"""
))

# ── Cell 13: dev_activation_v2 ────────────────────────────────────────────
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_activation_v2 AS
WITH first_dates AS (
    SELECT developer_id, MIN(activity_date) AS first_activity_date
    FROM activity_labeled_v2
    GROUP BY developer_id
),
lifetime_signals AS (
    SELECT developer_id,
        SUM(CASE WHEN journey_signal IN ('Build','Champion') THEN 1 ELSE 0 END) AS lifetime_build_champion_events,
        COUNT(*) AS lifetime_activity_count_for_activation,
        MAX(activity_date) AS lifetime_last_activity_date
    FROM activity_labeled_v2
    GROUP BY developer_id
),
first_90_meaningful AS (
    SELECT f.developer_id,
        SUM(CASE WHEN mw.meaningful_week_flag = 1 THEN 1 ELSE 0 END) AS meaningful_weeks_first_90d
    FROM first_dates f
    LEFT JOIN dev_meaningful_week_v2 mw
        ON f.developer_id = mw.developer_id
       AND mw.week_start >= DATE_TRUNC('week', f.first_activity_date)
       AND mw.week_start <  f.first_activity_date + INTERVAL 90 DAY
    GROUP BY f.developer_id
),
last_meaningful AS (
    SELECT developer_id,
        MAX(CASE WHEN meaningful_week_flag = 1 THEN week_start END) AS last_meaningful_week_start,
        SUM(CASE WHEN meaningful_week_flag = 1 THEN 1 ELSE 0 END) AS lifetime_meaningful_weeks
    FROM dev_meaningful_week_v2
    GROUP BY developer_id
)
SELECT
    u.developer_id,
    f.first_activity_date,
    COALESCE(l.lifetime_build_champion_events, 0) AS lifetime_build_champion_events,
    COALESCE(m.meaningful_weeks_first_90d, 0) AS meaningful_weeks_first_90d,
    COALESCE(l.lifetime_activity_count_for_activation, 0) AS lifetime_activity_count_for_activation,
    l.lifetime_last_activity_date,
    COALESCE(lm.lifetime_meaningful_weeks, 0) AS lifetime_meaningful_weeks,
    lm.last_meaningful_week_start,
    CASE
        WHEN COALESCE(l.lifetime_build_champion_events, 0) >= 1 THEN 1
        WHEN COALESCE(m.meaningful_weeks_first_90d, 0) >= 2 THEN 1
        ELSE 0
    END AS is_activated,
    CASE
        WHEN COALESCE(l.lifetime_build_champion_events, 0) >= 1 THEN 'Build_or_Champion_Ever'
        WHEN COALESCE(m.meaningful_weeks_first_90d, 0) >= 2 THEN 'Two_Meaningful_Weeks_First_90d'
        ELSE 'Unactivated'
    END AS activation_reason
FROM developer_universe_v2 u
LEFT JOIN first_dates f      USING (developer_id)
LEFT JOIN lifetime_signals l USING (developer_id)
LEFT JOIN first_90_meaningful m USING (developer_id)
LEFT JOIN last_meaningful lm USING (developer_id)
\"\"\")

display(con.execute(\"\"\"
    SELECT activation_reason, is_activated, COUNT(*) AS developers
    FROM dev_activation_v2
    GROUP BY 1, 2
    ORDER BY developers DESC
\"\"\").fetchdf())
"""
))

# ── Cell 14: dev_dormancy_status_v2 ──────────────────────────────────────
cells.append(md("## 9. Dormancy status"))
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_dormancy_status_v2 AS
WITH max_dt AS (
    SELECT MAX(activity_date) AS anchor_date FROM activity_labeled_v2
),
base AS (
    SELECT
        a.*,
        DATE_DIFF('day', lifetime_last_activity_date,
                  (SELECT anchor_date FROM max_dt)) AS days_since_last_activity
    FROM dev_activation_v2 a
)
SELECT *,
CASE
    WHEN lifetime_activity_count_for_activation = 0 THEN 'Unactivated'
    WHEN days_since_last_activity < 30  THEN 'Active'
    WHEN days_since_last_activity < 90  THEN 'Cooling'
    WHEN days_since_last_activity < 365 THEN 'At_Risk'
    ELSE 'Dormant'
END AS dormancy_status
FROM base
\"\"\")

display(con.execute(\"\"\"
    SELECT dormancy_status, COUNT(*) AS developers,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
    FROM dev_dormancy_status_v2
    GROUP BY 1
    ORDER BY developers DESC
\"\"\").fetchdf())
"""
))

# ── Cell 15: dev_effort_level_v2 ─────────────────────────────────────────
cells.append(md("## 10. Developer effort level"))
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_effort_level_v2 AS
WITH base AS (
    SELECT
        lf.developer_id,
        lf.lifetime_activity_count,
        lf.lifetime_activity_score_sum,
        lf.lifetime_unique_activity_types,
        lf.lifetime_unique_modalities,
        lf.lifetime_high_effort_count,
        lf.lifetime_avg_effort_rank,
        lf.lifetime_max_effort_rank,
        lf.lifetime_total_confidence_weighted_effort,
        lf.lifetime_avg_score_effort_gap,
        lf.lifetime_score_effort_misalignment_count,
        lf.lifetime_low_medium_confidence_effort_count,
        lf.lifetime_effort_x_activity_score_sum,
        lf.lifetime_build_count,
        lf.lifetime_champion_count,
        lf.lifetime_dli_training_count,
        lf.lifetime_webinar_count,
        lf.lifetime_forum_count,
        lf.lifetime_bug_count,
        lf.lifetime_hackathon_count,
        lf.lifetime_api_count,
        lf.lifetime_devzone_download_count,
        lf.lifetime_ngc_download_count,
        lf.log_clipped_lifetime_activity_count_p99,
        lf.log_clipped_lifetime_activity_score_sum_p99,
        lf.log_clipped_lifetime_total_confidence_weighted_effort_p99,
        lf.log_clipped_lifetime_effort_x_activity_score_sum_p99,
        COALESCE(r.activity_count_0_30d, 0) AS activity_count_0_30d,
        COALESCE(r.activity_count_30_90d, 0) AS activity_count_30_90d,
        COALESCE(r.activity_count_90_180d, 0) AS activity_count_90_180d,
        COALESCE(r.unique_activity_types_0_30d, 0) AS unique_activity_types_0_30d,
        COALESCE(r.weighted_recent_confidence_effort, 0) AS weighted_recent_confidence_effort,
        COALESCE(r.avg_effort_rank_0_30d, 0) AS avg_effort_rank_0_30d,
        COALESCE(r.recent_build_flag, 0) AS recent_build_flag,
        CASE
            WHEN COALESCE(r.activity_count_0_30d, 0)  > 0 THEN 1.00
            WHEN COALESCE(r.activity_count_30_90d, 0) > 0 THEN 0.75
            WHEN COALESCE(r.activity_count_90_180d,0) > 0 THEN 0.50
            ELSE 0.25
        END AS recency_weight
    FROM dev_features_lifetime_v2 lf
    LEFT JOIN dev_recency_features_v2 r USING (developer_id)
), scored AS (
    SELECT *,
        (  0.30 * COALESCE(log_clipped_lifetime_total_confidence_weighted_effort_p99, 0)
         + 0.20 * COALESCE(log_clipped_lifetime_effort_x_activity_score_sum_p99, 0)
         + 0.15 * COALESCE(log_clipped_lifetime_activity_count_p99, 0)
         + 0.10 * LN(1 + COALESCE(lifetime_unique_activity_types, 0))
         + 0.10 * LN(1 + COALESCE(lifetime_unique_modalities, 0))
         + 0.10 * LN(1 + COALESCE(weighted_recent_confidence_effort, 0))
         + 0.05 * COALESCE(lifetime_avg_effort_rank, 0)
        ) * recency_weight AS developer_effort_score
    FROM base
), cutoffs AS (
    SELECT
        QUANTILE_CONT(developer_effort_score, 0.50) AS p50_effort,
        QUANTILE_CONT(developer_effort_score, 0.75) AS p75_effort,
        QUANTILE_CONT(developer_effort_score, 0.90) AS p90_effort
    FROM scored WHERE lifetime_activity_count > 0
)
SELECT
    s.*,
    CASE
        WHEN s.lifetime_activity_count = 0          THEN 'no activity'
        WHEN s.developer_effort_score >= c.p90_effort THEN 'very high effort'
        WHEN s.developer_effort_score >= c.p75_effort THEN 'high effort'
        WHEN s.developer_effort_score >= c.p50_effort THEN 'medium effort'
        ELSE 'low effort'
    END AS developer_effort_level,
    CASE
        WHEN s.lifetime_activity_count = 0          THEN 0
        WHEN s.developer_effort_score >= c.p90_effort THEN 4
        WHEN s.developer_effort_score >= c.p75_effort THEN 3
        WHEN s.developer_effort_score >= c.p50_effort THEN 2
        ELSE 1
    END AS developer_effort_rank
FROM scored s
CROSS JOIN cutoffs c
\"\"\")

display(con.execute(\"\"\"
    SELECT developer_effort_level, developer_effort_rank,
           COUNT(*) AS developers, ROUND(AVG(developer_effort_score), 3) AS avg_score
    FROM dev_effort_level_v2
    GROUP BY 1, 2 ORDER BY developer_effort_rank DESC
\"\"\").fetchdf())
"""
))

# ── Cell 16: dev_contact_persona_v2 + dev_persona_v2 ─────────────────────
cells.append(md("## 11. Persona"))
cells.append(code(
r"""con.execute(r"""
CREATE OR REPLACE TABLE dev_contact_persona_v2 AS
WITH base AS (
    SELECT
        developer_id,
        LOWER(
            COALESCE(development_areas, '') || ' ' ||
            COALESCE(fields_of_interest, '') || ' ' ||
            COALESCE(industry_segment_vertical, '')
        ) AS profile_text
    FROM contact_one_row_v2
)
SELECT
    developer_id,
    CASE WHEN REGEXP_MATCHES(profile_text, 'cuda|gpu|accelerated|hpc|rapids|cudnn') THEN 1.0 ELSE 0.0 END AS cuda_profile_score,
    CASE WHEN REGEXP_MATCHES(profile_text, 'genai|generative|llm|ai|machine learning|deep learning|inference') THEN 1.0 ELSE 0.0 END AS genai_profile_score,
    CASE WHEN REGEXP_MATCHES(profile_text, 'robot|isaac|ros|jetson|autonomous|edge') THEN 1.0 ELSE 0.0 END AS robotics_profile_score,
    CASE WHEN REGEXP_MATCHES(profile_text, 'simulation|omniverse|digital twin|graphics|render|rtx') THEN 1.0 ELSE 0.0 END AS simulation_profile_score,
    CASE WHEN REGEXP_MATCHES(profile_text, 'training|education|student|academic|community|developer program') THEN 1.0 ELSE 0.0 END AS learning_community_profile_score
FROM base
""" + '""")')
))

cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_persona_v2 AS
WITH base AS (
    SELECT
        lf.developer_id,
        lf.cuda_score              + COALESCE(cp.cuda_profile_score, 0)              AS cuda_score,
        lf.genai_score             + COALESCE(cp.genai_profile_score, 0)             AS genai_score,
        lf.robotics_score          + COALESCE(cp.robotics_profile_score, 0)          AS robotics_score,
        lf.simulation_score        + COALESCE(cp.simulation_profile_score, 0)        AS simulation_score,
        lf.learning_community_score + COALESCE(cp.learning_community_profile_score, 0) AS learning_community_score,
        lf.other_persona_score
    FROM dev_features_lifetime_v2 lf
    LEFT JOIN dev_contact_persona_v2 cp USING (developer_id)
),
norm AS (
    SELECT *,
        cuda_score + genai_score + robotics_score + simulation_score + learning_community_score
            AS specific_persona_score,
        cuda_score + genai_score + robotics_score + simulation_score + learning_community_score
            + other_persona_score AS total_persona_score
    FROM base
),
shares AS (
    SELECT *,
        COALESCE(cuda_score              / NULLIF(specific_persona_score, 0), 0) AS cuda_share,
        COALESCE(genai_score             / NULLIF(specific_persona_score, 0), 0) AS genai_share,
        COALESCE(robotics_score          / NULLIF(specific_persona_score, 0), 0) AS robotics_share,
        COALESCE(simulation_score        / NULLIF(specific_persona_score, 0), 0) AS simulation_share,
        COALESCE(learning_community_score / NULLIF(specific_persona_score, 0), 0) AS learning_community_share,
        COALESCE(other_persona_score     / NULLIF(total_persona_score, 0), 0) AS other_share
    FROM norm
),
entropy AS (
    SELECT *,
        -1 * (
            CASE WHEN cuda_share > 0              THEN cuda_share              * LN(cuda_share)              ELSE 0 END +
            CASE WHEN genai_share > 0             THEN genai_share             * LN(genai_share)             ELSE 0 END +
            CASE WHEN robotics_share > 0          THEN robotics_share          * LN(robotics_share)          ELSE 0 END +
            CASE WHEN simulation_share > 0        THEN simulation_share        * LN(simulation_share)        ELSE 0 END +
            CASE WHEN learning_community_share > 0 THEN learning_community_share * LN(learning_community_share) ELSE 0 END
        ) / LN(5) AS persona_entropy
    FROM shares
),
long_scores AS (
    SELECT developer_id, 'CUDA'               AS persona, cuda_share               AS score FROM entropy
    UNION ALL
    SELECT developer_id, 'GenAI',              genai_share              FROM entropy
    UNION ALL
    SELECT developer_id, 'Robotics',           robotics_share           FROM entropy
    UNION ALL
    SELECT developer_id, 'Simulation',         simulation_share         FROM entropy
    UNION ALL
    SELECT developer_id, 'Learning_Community', learning_community_share FROM entropy
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY developer_id ORDER BY score DESC, persona) AS rn,
        LEAD(score) OVER (PARTITION BY developer_id ORDER BY score DESC, persona) AS second_score
    FROM long_scores
)
SELECT
    e.*,
    CASE WHEN e.specific_persona_score = 0 THEN 'Unknown' ELSE r.persona END AS persona,
    CASE WHEN e.specific_persona_score = 0 THEN 0          ELSE r.score  END AS persona_confidence,
    CASE
        WHEN e.specific_persona_score = 0 THEN 'Unknown'
        WHEN r.score >= 0.70              THEN 'High'
        WHEN r.score >= 0.45              THEN 'Medium'
        ELSE 'Low'
    END AS persona_confidence_tier,
    CASE
        WHEN e.specific_persona_score = 0 THEN 0
        WHEN e.persona_entropy >= 0.60 OR r.score - COALESCE(r.second_score, 0) <= 0.15 THEN 1
        ELSE 0
    END AS mixed_persona_flag
FROM entropy e
LEFT JOIN ranked r ON e.developer_id = r.developer_id AND r.rn = 1
\"\"\")

display(con.execute(\"\"\"
    SELECT persona, persona_confidence_tier, COUNT(*) AS developers
    FROM dev_persona_v2
    GROUP BY 1, 2
    ORDER BY developers DESC
\"\"\").fetchdf())
"""
))

# ── Cell 17: dev_journey_state_v2 ─────────────────────────────────────────
cells.append(md("## 12. Journey state"))
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_journey_state_v2 AS
WITH base AS (
    SELECT
        r.developer_id,
        COALESCE(r.activity_count_0_30d,  0) AS activity_count_0_30d,
        COALESCE(r.activity_count_30_90d, 0) AS activity_count_30_90d,
        COALESCE(r.activity_count_90_180d,0) AS activity_count_90_180d,
        COALESCE(r.build_count_0_30d,     0) AS build_count_0_30d,
        COALESCE(r.build_count_30_90d,    0) AS build_count_30_90d,
        COALESCE(r.high_effort_count_0_30d,  0) AS high_effort_count_0_30d,
        COALESCE(r.high_effort_count_30_90d, 0) AS high_effort_count_30_90d,
        COALESCE(r.unique_activity_types_0_30d, 0) AS unique_activity_types_0_30d,
        COALESCE(r.unique_modalities_0_30d,     0) AS unique_modalities_0_30d,
        COALESCE(r.recent_build_flag,     0) AS recent_build_flag,
        COALESCE(r.recent_champion_flag,  0) AS recent_champion_flag,
        COALESCE(d.is_activated, 0) AS is_activated,
        COALESCE(d.lifetime_activity_count_for_activation, 0) AS lifetime_activity_count_for_activation,
        COALESCE(d.dormancy_status, 'Unactivated') AS dormancy_status,
        CASE WHEN d.dormancy_status = 'Dormant'  THEN 1 ELSE 0 END AS dormant_flag,
        CASE WHEN d.dormancy_status = 'At_Risk'  THEN 1 ELSE 0 END AS at_risk_flag,
        CASE WHEN d.dormancy_status = 'Cooling'  THEN 1 ELSE 0 END AS cooling_flag,
        d.days_since_last_activity,
        COALESCE(l.lifetime_activity_count,        0) AS lifetime_activity_count,
        COALESCE(l.lifetime_build_count,           0) AS lifetime_build_count,
        COALESCE(l.lifetime_champion_count,        0) AS lifetime_champion_count,
        COALESCE(l.lifetime_high_effort_count,     0) AS lifetime_high_effort_count,
        COALESCE(l.lifetime_unique_activity_types, 0) AS lifetime_unique_activity_types,
        COALESCE(l.lifetime_unique_modalities,     0) AS lifetime_unique_modalities,
        CASE
            WHEN COALESCE(r.activity_count_0_30d,0)=0 AND COALESCE(r.activity_count_30_90d,0)=0 THEN NULL
            WHEN COALESCE(r.activity_count_30_90d,0)=0 AND COALESCE(r.activity_count_0_30d,0)>0 THEN 2.0
            ELSE CAST(r.activity_count_0_30d AS DOUBLE) / NULLIF(CAST(r.activity_count_30_90d AS DOUBLE), 0)
        END AS recent_activity_trend_ratio
    FROM dev_recency_features_v2 r
    LEFT JOIN dev_dormancy_status_v2 d USING (developer_id)
    LEFT JOIN dev_features_lifetime_v2 l USING (developer_id)
),
scored AS (
    SELECT *,
        CASE
            WHEN activity_count_0_30d >= 5 THEN 'High'
            WHEN activity_count_0_30d >= 2 THEN 'Medium'
            WHEN activity_count_0_30d  = 1 THEN 'Low'
            ELSE 'None'
        END AS activity_volume_band,
        CASE
            WHEN build_count_0_30d > 0 OR recent_build_flag = 1 OR lifetime_build_count >= 5 THEN 'Build_Intent'
            WHEN high_effort_count_0_30d > 0 OR lifetime_high_effort_count >= 5 THEN 'Evaluation_Intent'
            WHEN activity_count_0_30d > 0 THEN 'Learning_Intent'
            ELSE 'No_Recent_Intent'
        END AS intent_signal,
        CASE
            WHEN recent_activity_trend_ratio IS NULL THEN NULL
            WHEN recent_activity_trend_ratio >= 1.5  THEN 'Accelerating'
            WHEN recent_activity_trend_ratio >= 0.7  THEN 'Stable'
            WHEN recent_activity_trend_ratio > 0     THEN 'Declining'
            ELSE NULL
        END AS trend_signal
    FROM base
),
behavior AS (
    SELECT *,
        CASE
            WHEN lifetime_activity_count = 0 THEN 'Unactivated'
            WHEN build_count_0_30d > 0 OR recent_build_flag = 1 OR lifetime_build_count >= 10 THEN 'Builder'
            WHEN high_effort_count_0_30d > 0 OR lifetime_high_effort_count >= 10 THEN 'Evaluator'
            WHEN activity_count_0_30d > 0 AND unique_activity_types_0_30d >= 2 THEN 'Explorer'
            WHEN activity_count_0_30d > 0 THEN 'Learner'
            WHEN lifetime_activity_count > 0 THEN 'Historically_Active'
            ELSE 'Unactivated'
        END AS behavior_journey_stage_30d
    FROM scored
)
SELECT
    developer_id,
    behavior_journey_stage_30d,
    CASE
        WHEN behavior_journey_stage_30d = 'Unactivated' THEN 'Unactivated'
        WHEN dormancy_status IN ('Dormant','At_Risk','Cooling')
        THEN dormancy_status || '_' || behavior_journey_stage_30d
        ELSE behavior_journey_stage_30d
    END AS current_journey_state_30d,
    CASE
        WHEN behavior_journey_stage_30d = 'Unactivated'        THEN 0
        WHEN behavior_journey_stage_30d = 'Historically_Active' THEN 1
        WHEN behavior_journey_stage_30d = 'Learner'             THEN 2
        WHEN behavior_journey_stage_30d = 'Explorer'            THEN 3
        WHEN behavior_journey_stage_30d = 'Evaluator'           THEN 4
        WHEN behavior_journey_stage_30d = 'Builder'             THEN 5
        ELSE 1
    END AS behavior_journey_rank_30d,
    CASE
        WHEN behavior_journey_stage_30d = 'Unactivated'        THEN 0
        WHEN behavior_journey_stage_30d = 'Historically_Active' THEN 1
        WHEN behavior_journey_stage_30d = 'Learner'             THEN 2
        WHEN behavior_journey_stage_30d = 'Explorer'            THEN 3
        WHEN behavior_journey_stage_30d = 'Evaluator'           THEN 4
        WHEN behavior_journey_stage_30d = 'Builder'             THEN 5
        ELSE 1
    END AS current_journey_rank_30d,
    activity_volume_band,
    intent_signal,
    trend_signal,
    recent_activity_trend_ratio
FROM behavior
\"\"\")

display(con.execute(\"\"\"
    SELECT behavior_journey_stage_30d, COUNT(*) AS developers,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
    FROM dev_journey_state_v2
    GROUP BY 1 ORDER BY developers DESC
\"\"\").fetchdf())
"""
))

# ── Cell 18: dev_profile_final_v4 ─────────────────────────────────────────
cells.append(md("## 13. Final developer profile"))
cells.append(code(
"""con.execute(\"\"\"
CREATE OR REPLACE TABLE dev_profile_final_v4 AS
SELECT
    u.developer_id,

    p.persona,
    p.persona_confidence,
    p.persona_confidence_tier,
    p.persona_entropy,
    p.mixed_persona_flag,
    p.cuda_share,
    p.genai_share,
    p.robotics_share,
    p.simulation_share,
    p.learning_community_share,

    e.developer_effort_score,
    e.developer_effort_level,
    e.developer_effort_rank,
    e.recency_weight AS effort_recency_weight,

    js.behavior_journey_stage_30d,
    js.behavior_journey_rank_30d,
    js.current_journey_state_30d,
    js.current_journey_rank_30d,

    COALESCE(d.is_activated, 0) AS is_activated,
    d.lifetime_meaningful_weeks,
    d.last_meaningful_week_start,
    DATE_DIFF('day', d.last_meaningful_week_start, CURRENT_DATE) AS days_since_last_meaningful_week,
    d.days_since_last_activity,
    COALESCE(d.dormancy_status, 'Unactivated') AS dormancy_status,
    CASE WHEN d.dormancy_status = 'Dormant'  THEN 1 ELSE 0 END AS dormant_flag,
    CASE WHEN d.dormancy_status = 'At_Risk'  THEN 1 ELSE 0 END AS at_risk_flag,
    CASE WHEN d.dormancy_status = 'Cooling'  THEN 1 ELSE 0 END AS cooling_flag,

    CASE
        WHEN COALESCE(lf.lifetime_activity_count, 0) = 0 THEN 'Unactivated'
        WHEN lf.user_type = 'tourist'         THEN 'Tourist'
        WHEN lf.user_type = 'free_email_user' THEN 'FreeEmail'
        WHEN COALESCE(d.days_since_last_activity,
                      DATE_DIFF('day', d.last_meaningful_week_start, CURRENT_DATE)) >= 365
             THEN 'Dormant_' || lf.max_stage_reached
        WHEN COALESCE(d.days_since_last_activity,
                      DATE_DIFF('day', d.last_meaningful_week_start, CURRENT_DATE)) >= 180
             THEN 'AtRisk_'  || lf.max_stage_reached
        ELSE 'Active_' || lf.max_stage_reached
    END AS final_lifecycle_status,

    r.* EXCLUDE (developer_id),

    lf.* EXCLUDE (
        developer_id,
        cuda_score, genai_score, robotics_score,
        simulation_score, learning_community_score, other_persona_score
    ),

    c.created_date             AS contact_created_date,
    c.first_activity_date      AS contact_first_activity_date,
    c.last_activity_date       AS contact_last_activity_date,
    c.account_id,
    c.account_type,
    c.country,
    c.region,
    c.industry_segment_vertical,
    c.program_application_source,
    c.organization_english_name,
    c.normalized_account_name,
    c.wwfo_category,
    c.wwfo_target_list,
    CASE WHEN c.developer_id IS NULL THEN 1 ELSE 0 END AS missing_contact_metadata_flag

FROM developer_universe_v2 u
LEFT JOIN dev_persona_v2            p  USING (developer_id)
LEFT JOIN dev_effort_level_v2       e  USING (developer_id)
LEFT JOIN dev_journey_state_v2      js USING (developer_id)
LEFT JOIN dev_dormancy_status_v2    d  USING (developer_id)
LEFT JOIN dev_recency_features_v2   r  USING (developer_id)
LEFT JOIN dev_features_lifetime_v2  lf USING (developer_id)
LEFT JOIN contact_one_row_v2        c  USING (developer_id)
\"\"\")

display(con.execute(\"\"\"
    SELECT COUNT(*) AS rows, COUNT(DISTINCT developer_id) AS developers,
           ROUND(AVG(developer_effort_score), 3) AS avg_effort_score,
           SUM(missing_contact_metadata_flag) AS missing_contact
    FROM dev_profile_final_v4
\"\"\").fetchdf())

display(con.execute(\"\"\"
    SELECT persona, current_journey_state_30d, dormancy_status, final_lifecycle_status,
           COUNT(*) AS developers
    FROM dev_profile_final_v4
    GROUP BY 1, 2, 3, 4
    ORDER BY developers DESC
    LIMIT 30
\"\"\").fetchdf())
"""
))

# ── Cell 19: final inventory ──────────────────────────────────────────────
cells.append(md("## Final table inventory"))
cells.append(code(
"""final_tables = [
    "activity_effort_mapping_ai_v2",
    "activity_base_v2",
    "contact_one_row_v2",
    "activity_dictionary_v2",
    "activity_labeled_v2",
    "developer_universe_v2",
    "dev_features_0_30d_v2",
    "dev_features_30_90d_v2",
    "dev_features_90_180d_v2",
    "dev_recency_features_v2",
    "dev_features_lifetime_v2",
    "dev_weekly_features_v2",
    "dev_meaningful_week_v2",
    "dev_activation_v2",
    "dev_dormancy_status_v2",
    "dev_effort_level_v2",
    "dev_contact_persona_v2",
    "dev_persona_v2",
    "dev_journey_state_v2",
    "dev_profile_final_v4",
]

rows = []
for t in final_tables:
    exists = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [t]
    ).fetchone()[0] > 0
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] if exists else None
    rows.append({"table": t, "rows": n, "exists": exists})

display(pd.DataFrame(rows))
"""
))

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"}
    },
    "cells": cells
}

out = "c:/Users/Owner/OneDrive/Documents/NVIDIA/Spring2026_IndustryProject/FeatureEngineering_Sample.ipynb"
with open(out, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Written {len(cells)} cells to {out}")
