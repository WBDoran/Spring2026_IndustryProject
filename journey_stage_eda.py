
# JOURNEY STAGE EDA — COMPREHENSIVE ANALYSIS
# Prerequisites:
#   - DuckDB connection as `con`
#   - activity_final table (cleaned activity data)
#   - activity_journey_effort table (19-row mapping)

import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# Update if your db path is different
DB_PATH = "developer_project.duckdb"
con = duckdb.connect(DB_PATH)

pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 100)



# STEP 1: TAG EVERY ACTIVITY ROW WITH JOURNEY STAGE

con.execute("""
CREATE OR REPLACE TABLE activity_tagged AS
SELECT
    af.*,
    aje.journey_stage,
    aje.effort
FROM activity_final af
INNER JOIN activity_journey_effort aje
    ON af.activity = aje.activity
""")

tagged_count = con.execute("SELECT COUNT(*) FROM activity_tagged").fetchone()[0]
untagged_count = con.execute("""
    SELECT COUNT(*) FROM activity_final af
    LEFT JOIN activity_journey_effort aje ON af.activity = aje.activity
    WHERE aje.journey_stage IS NULL
""").fetchone()[0]

print(f"Tagged rows:   {tagged_count:,}")
print(f"Untagged rows: {untagged_count:,}")


# ANALYSIS 1: DEVELOPER REACH PER STAGE
# How many unique developers have at least one activity
# in each stage? This is the raw funnel.

stage_reach = con.execute("""
SELECT
    journey_stage,
    COUNT(DISTINCT dev_contact) AS unique_developers
FROM activity_tagged
GROUP BY journey_stage
ORDER BY unique_developers DESC
""").fetchdf()

print(stage_reach)

# Plot
stage_order = ['Discover', 'Learn', 'Evaluate', 'Build', 'Champion']
stage_colors = {
    'Discover': '#4ECDC4', 'Learn': '#45B7D1',
    'Evaluate': '#F7DC6F', 'Build': '#E74C3C', 'Champion': '#8E44AD'
}

fig, ax = plt.subplots(figsize=(10, 5))
plot_data = stage_reach.set_index('journey_stage').reindex(stage_order)
bars = ax.bar(
    plot_data.index, plot_data['unique_developers'],
    color=[stage_colors[s] for s in plot_data.index],
    edgecolor='white', linewidth=1.5
)
ax.set_title('Unique Developers with Activity in Each Stage', fontsize=14, fontweight='bold')
ax.set_ylabel('Developers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
for bar, val in zip(bars, plot_data['unique_developers']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f'{val:,.0f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.show()



# ANALYSIS 2: HOW MANY STAGES DOES EACH DEVELOPER TOUCH?

stages_per_dev = con.execute("""
SELECT
    stages_touched,
    COUNT(*) AS developers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM (
    SELECT dev_contact, COUNT(DISTINCT journey_stage) AS stages_touched
    FROM activity_tagged
    GROUP BY dev_contact
)
GROUP BY stages_touched
ORDER BY stages_touched
""").fetchdf()

print(stages_per_dev)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(stages_per_dev['stages_touched'], stages_per_dev['developers'],
       color='#45B7D1', edgecolor='white')
ax.set_xlabel('Number of Stages Touched')
ax.set_ylabel('Developers')
ax.set_title('How Many Stages Does Each Developer Touch?', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
ax.set_xticks(stages_per_dev['stages_touched'])
for i, row in stages_per_dev.iterrows():
    ax.text(row['stages_touched'], row['developers'],
            f"{row['pct']}%", ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.show()


# ANALYSIS 3: STAGE CO-OCCURRENCE MATRIX
# For each pair of stages: what % of developers in stage A
# also have activity in stage B?

dev_stage_flags = con.execute("""
SELECT
    dev_contact,
    MAX(CASE WHEN journey_stage = 'Discover'  THEN 1 ELSE 0 END) AS Discover,
    MAX(CASE WHEN journey_stage = 'Learn'     THEN 1 ELSE 0 END) AS Learn,
    MAX(CASE WHEN journey_stage = 'Evaluate'  THEN 1 ELSE 0 END) AS Evaluate,
    MAX(CASE WHEN journey_stage = 'Build'     THEN 1 ELSE 0 END) AS Build,
    MAX(CASE WHEN journey_stage = 'Champion'  THEN 1 ELSE 0 END) AS Champion
FROM activity_tagged
GROUP BY dev_contact
""").fetchdf()

# Build co-occurrence matrix
stages = ['Discover', 'Learn', 'Evaluate', 'Build', 'Champion']
cooccurrence = pd.DataFrame(index=stages, columns=stages, dtype=float)

for s1 in stages:
    for s2 in stages:
        mask_s1 = dev_stage_flags[s1] == 1
        if mask_s1.sum() > 0:
            cooccurrence.loc[s1, s2] = round(
                (dev_stage_flags.loc[mask_s1, s2].sum() / mask_s1.sum()) * 100, 1
            )
        else:
            cooccurrence.loc[s1, s2] = 0.0

print("Co-occurrence matrix (% of row stage that also has column stage):")
print(cooccurrence)

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(cooccurrence.astype(float), annot=True, fmt='.1f', cmap='YlOrRd',
            ax=ax, vmin=0, vmax=100, linewidths=0.5,
            cbar_kws={'label': '% of row developers also in column stage'})
ax.set_title('Stage Co-occurrence Matrix', fontsize=14, fontweight='bold')
ax.set_ylabel('If developer is in this stage...')
ax.set_xlabel('...what % also has activity in this stage?')
plt.tight_layout()
plt.show()


# ANALYSIS 4: TEMPORAL ORDERING — DO STAGES HAPPEN IN ORDER?

con.execute("""
CREATE OR REPLACE TABLE dev_first_stage_dates AS
SELECT
    dev_contact,
    MIN(CASE WHEN journey_stage = 'Discover'  THEN activity_date END) AS first_discover,
    MIN(CASE WHEN journey_stage = 'Learn'     THEN activity_date END) AS first_learn,
    MIN(CASE WHEN journey_stage = 'Evaluate'  THEN activity_date END) AS first_evaluate,
    MIN(CASE WHEN journey_stage = 'Build'     THEN activity_date END) AS first_build,
    MIN(CASE WHEN journey_stage = 'Champion'  THEN activity_date END) AS first_champion
FROM activity_tagged
GROUP BY dev_contact
""")

temporal_order = con.execute("""
SELECT
    'Discover → Learn' AS transition,
    COUNT(*) AS devs_with_both,
    SUM(CASE WHEN first_discover < first_learn THEN 1 ELSE 0 END) AS correct_order,
    ROUND(SUM(CASE WHEN first_discover < first_learn THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 1) AS pct_correct
FROM dev_first_stage_dates
WHERE first_discover IS NOT NULL AND first_learn IS NOT NULL

UNION ALL
SELECT 'Learn → Evaluate', COUNT(*),
    SUM(CASE WHEN first_learn < first_evaluate THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN first_learn < first_evaluate THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM dev_first_stage_dates
WHERE first_learn IS NOT NULL AND first_evaluate IS NOT NULL

UNION ALL
SELECT 'Evaluate → Build', COUNT(*),
    SUM(CASE WHEN first_evaluate < first_build THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN first_evaluate < first_build THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM dev_first_stage_dates
WHERE first_evaluate IS NOT NULL AND first_build IS NOT NULL

UNION ALL
SELECT 'Build → Champion', COUNT(*),
    SUM(CASE WHEN first_build < first_champion THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN first_build < first_champion THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM dev_first_stage_dates
WHERE first_build IS NOT NULL AND first_champion IS NOT NULL
""").fetchdf()

print(temporal_order)

fig, ax = plt.subplots(figsize=(8, 4))
colors = ['#2ecc71' if p >= 60 else '#e74c3c' for p in temporal_order['pct_correct']]
bars = ax.barh(temporal_order['transition'], temporal_order['pct_correct'], color=colors)
ax.axvline(x=50, color='gray', linestyle='--', alpha=0.5, label='50% (random)')
ax.set_xlabel('% of developers where earlier stage comes first')
ax.set_title('Does the Journey Follow the Expected Order?', fontsize=14, fontweight='bold')
ax.set_xlim(0, 100)
for bar, val in zip(bars, temporal_order['pct_correct']):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{val}%', va='center', fontsize=10)
ax.legend()
plt.tight_layout()
plt.show()


# ANALYSIS 5: PROFILE BUILD DEVELOPERS
# What else do Build developers do? Which activities?
# How active are they compared to non-Build developers?

build_profile = con.execute("""
SELECT
    at.activity,
    at.journey_stage,
    at.effort,
    COUNT(*) AS activity_rows,
    COUNT(DISTINCT at.dev_contact) AS unique_devs
FROM activity_tagged at
WHERE at.dev_contact IN (
    SELECT DISTINCT dev_contact
    FROM activity_tagged
    WHERE journey_stage = 'Build'
)
GROUP BY 1, 2, 3
ORDER BY activity_rows DESC
""").fetchdf()

print("=== FULL ACTIVITY PROFILE OF BUILD DEVELOPERS ===")
print(build_profile.to_string(index=False))


# ANALYSIS 6: PROFILE CHAMPION DEVELOPERS

champion_profile = con.execute("""
SELECT
    at.activity,
    at.journey_stage,
    at.effort,
    COUNT(*) AS activity_rows,
    COUNT(DISTINCT at.dev_contact) AS unique_devs
FROM activity_tagged at
WHERE at.dev_contact IN (
    SELECT DISTINCT dev_contact
    FROM activity_tagged
    WHERE journey_stage = 'Champion'
)
GROUP BY 1, 2, 3
ORDER BY activity_rows DESC
""").fetchdf()

print("=== FULL ACTIVITY PROFILE OF CHAMPION DEVELOPERS ===")
print(champion_profile.to_string(index=False))


# ANALYSIS 7: BUILD vs NON-BUILD DEVELOPER COMPARISON
# How different are Build developers from everyone else?

build_vs_rest = con.execute("""
WITH build_devs AS (
    SELECT DISTINCT dev_contact FROM activity_tagged WHERE journey_stage = 'Build'
)
SELECT
    CASE WHEN bd.dev_contact IS NOT NULL THEN 'Has Build Activity' ELSE 'No Build Activity' END AS group_label,
    COUNT(DISTINCT at.dev_contact) AS developers,
    ROUND(AVG(dev_stats.total_activities), 1) AS avg_total_activities,
    ROUND(AVG(dev_stats.distinct_stages), 1) AS avg_stages_touched,
    ROUND(AVG(dev_stats.distinct_activities), 1) AS avg_distinct_activity_types,
    ROUND(AVG(dev_stats.activity_span_days), 0) AS avg_active_span_days
FROM activity_tagged at
LEFT JOIN build_devs bd ON at.dev_contact = bd.dev_contact
JOIN (
    SELECT
        dev_contact,
        COUNT(*) AS total_activities,
        COUNT(DISTINCT journey_stage) AS distinct_stages,
        COUNT(DISTINCT activity) AS distinct_activities,
        DATE_DIFF('day', MIN(activity_date)::DATE, MAX(activity_date)::DATE) AS activity_span_days
    FROM activity_tagged
    GROUP BY dev_contact
) dev_stats ON at.dev_contact = dev_stats.dev_contact
GROUP BY 1
""").fetchdf()

print("=== BUILD vs NON-BUILD DEVELOPERS ===")
print(build_vs_rest.to_string(index=False))



# ANALYSIS 8: ACTIVITY COUNT DISTRIBUTION PER STAGE
# How many activities does each developer have in each stage?
# This reveals natural breaks for potential thresholds.

for stage in ['Build', 'Champion', 'Learn', 'Evaluate']:
    dist = con.execute(f"""
    SELECT activity_count, COUNT(*) AS developers
    FROM (
        SELECT dev_contact, COUNT(*) AS activity_count
        FROM activity_tagged
        WHERE journey_stage = '{stage}'
        GROUP BY dev_contact
    )
    GROUP BY activity_count
    ORDER BY activity_count
    LIMIT 25
    """).fetchdf()
    print(f"\n=== {stage.upper()} activity count distribution ===")
    print(dist.to_string(index=False))


# Plot the distributions side by side
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
for ax, stage in zip(axes.flatten(), ['Build', 'Champion', 'Learn', 'Evaluate']):
    dist = con.execute(f"""
    SELECT activity_count, COUNT(*) AS developers
    FROM (
        SELECT dev_contact, COUNT(*) AS activity_count
        FROM activity_tagged
        WHERE journey_stage = '{stage}'
        GROUP BY dev_contact
    )
    WHERE activity_count <= 20
    GROUP BY activity_count
    ORDER BY activity_count
    """).fetchdf()
    ax.bar(dist['activity_count'], dist['developers'],
           color=stage_colors.get(stage, '#45B7D1'), edgecolor='white')
    ax.set_title(f'{stage} — Activity Count Distribution', fontweight='bold')
    ax.set_xlabel('Number of activities')
    ax.set_ylabel('Developers')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e3:.0f}K' if x >= 1000 else f'{x:.0f}'))
plt.suptitle('Per-Developer Activity Counts Within Each Stage (capped at 20)',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# ANALYSIS 9: RECENCY — WHEN WAS LAST ACTIVITY PER STAGE?

recency = con.execute("""
SELECT
    journey_stage,
    COUNT(DISTINCT dev_contact) AS developers,
    ROUND(AVG(days_since_last), 0) AS avg_days_since_last,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_since_last), 0) AS median_days_since_last,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY days_since_last), 0) AS p25_days,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY days_since_last), 0) AS p75_days
FROM (
    SELECT
        dev_contact,
        journey_stage,
        DATE_DIFF('day', MAX(activity_date)::DATE, CURRENT_DATE) AS days_since_last
    FROM activity_tagged
    GROUP BY dev_contact, journey_stage
)
GROUP BY journey_stage
ORDER BY
    CASE journey_stage
        WHEN 'Discover'  THEN 1
        WHEN 'Learn'     THEN 2
        WHEN 'Evaluate'  THEN 3
        WHEN 'Build'     THEN 4
        WHEN 'Champion'  THEN 5
    END
""").fetchdf()

print("=== RECENCY BY STAGE ===")
print(recency.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 5))
x = range(len(recency))
ax.bar(x, recency['median_days_since_last'],
       color=[stage_colors.get(s, '#999') for s in recency['journey_stage']],
       edgecolor='white', linewidth=1.5)
ax.errorbar(x, recency['median_days_since_last'],
            yerr=[recency['median_days_since_last'] - recency['p25_days'],
                  recency['p75_days'] - recency['median_days_since_last']],
            fmt='none', color='black', capsize=5)
ax.set_xticks(x)
ax.set_xticklabels(recency['journey_stage'])
ax.set_ylabel('Days Since Last Activity (median, IQR)')
ax.set_title('How Recently Active Are Developers in Each Stage?', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()


# ANALYSIS 10: EFFORT LEVEL DISTRIBUTION WITHIN EACH STAGE

effort_by_stage = con.execute("""
SELECT
    journey_stage,
    effort,
    COUNT(*) AS rows,
    COUNT(DISTINCT dev_contact) AS developers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY journey_stage), 1) AS pct_of_stage
FROM activity_tagged
GROUP BY journey_stage, effort
ORDER BY
    CASE journey_stage
        WHEN 'Discover' THEN 1 WHEN 'Learn' THEN 2
        WHEN 'Evaluate' THEN 3 WHEN 'Build' THEN 4
        WHEN 'Champion' THEN 5
    END,
    CASE effort WHEN 'low' THEN 1 WHEN 'medium' THEN 2 WHEN 'high' THEN 3 END
""").fetchdf()

print("=== EFFORT DISTRIBUTION WITHIN EACH STAGE ===")
print(effort_by_stage.to_string(index=False))

# Stacked bar chart
effort_pivot = effort_by_stage.pivot_table(
    index='journey_stage', columns='effort', values='pct_of_stage', fill_value=0
)
effort_pivot = effort_pivot.reindex(stage_order)
effort_colors = {'low': '#82E0AA', 'medium': '#F4D03F', 'high': '#E74C3C'}

fig, ax = plt.subplots(figsize=(10, 5))
bottom = np.zeros(len(effort_pivot))
for effort_level in ['low', 'medium', 'high']:
    if effort_level in effort_pivot.columns:
        vals = effort_pivot[effort_level].values
        ax.bar(effort_pivot.index, vals, bottom=bottom,
               label=effort_level.capitalize(), color=effort_colors[effort_level],
               edgecolor='white', linewidth=0.5)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 5:
                ax.text(i, b + v/2, f'{v:.0f}%', ha='center', va='center', fontsize=9)
        bottom += vals
ax.set_ylabel('% of Stage Activity')
ax.set_title('Effort Level Distribution Within Each Stage', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.show()


# ANALYSIS 11: JOURNEY ENTRY POINT — WHERE DO DEVELOPERS START?
# What is the first journey stage each developer touches?
# Does everyone start at Discover, or do some jump straight
# to Evaluate or Build?

entry_points = con.execute("""
WITH first_activity AS (
    SELECT
        dev_contact,
        journey_stage,
        activity_date,
        ROW_NUMBER() OVER (PARTITION BY dev_contact ORDER BY activity_date ASC) AS rn
    FROM activity_tagged
)
SELECT
    journey_stage AS entry_stage,
    COUNT(*) AS developers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM first_activity
WHERE rn = 1
GROUP BY journey_stage
ORDER BY developers DESC
""").fetchdf()

print("=== WHERE DO DEVELOPERS FIRST ENTER THE ECOSYSTEM? ===")
print(entry_points.to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 5))
ep = entry_points.set_index('entry_stage').reindex(stage_order).dropna()
ax.bar(ep.index, ep['developers'],
       color=[stage_colors[s] for s in ep.index], edgecolor='white')
ax.set_title('First Activity Stage Per Developer (Entry Point)', fontsize=14, fontweight='bold')
ax.set_ylabel('Developers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
for i, (stage, row) in enumerate(ep.iterrows()):
    ax.text(i, row['developers'], f"{row['pct']}%", ha='center', va='bottom', fontsize=10)
plt.tight_layout()
plt.show()


# ANALYSIS 12: HIGHEST STAGE REACHED PER DEVELOPER
# Without any threshold — just based on whether they have
# ANY activity in a stage, what's the "highest" stage
# each developer has ever reached?

highest_stage = con.execute("""
SELECT
    highest_stage,
    COUNT(*) AS developers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM (
    SELECT
        dev_contact,
        CASE
            WHEN MAX(CASE WHEN journey_stage = 'Champion' THEN 1 ELSE 0 END) = 1 THEN 'Champion'
            WHEN MAX(CASE WHEN journey_stage = 'Build'    THEN 1 ELSE 0 END) = 1 THEN 'Build'
            WHEN MAX(CASE WHEN journey_stage = 'Evaluate' THEN 1 ELSE 0 END) = 1 THEN 'Evaluate'
            WHEN MAX(CASE WHEN journey_stage = 'Learn'    THEN 1 ELSE 0 END) = 1 THEN 'Learn'
            WHEN MAX(CASE WHEN journey_stage = 'Discover' THEN 1 ELSE 0 END) = 1 THEN 'Discover'
            ELSE 'None'
        END AS highest_stage
    FROM activity_tagged
    GROUP BY dev_contact
)
GROUP BY highest_stage
ORDER BY
    CASE highest_stage
        WHEN 'Discover' THEN 1 WHEN 'Learn' THEN 2
        WHEN 'Evaluate' THEN 3 WHEN 'Build' THEN 4
        WHEN 'Champion' THEN 5 ELSE 6
    END
""").fetchdf()

print("=== HIGHEST STAGE REACHED (no thresholds, any activity counts) ===")
print(highest_stage.to_string(index=False))


# ANALYSIS 13: TIME TO REACH EACH STAGE
# For developers who reach Build or Champion, how long
# does it take from their first activity?

time_to_stage = con.execute("""
SELECT
    journey_stage,
    COUNT(DISTINCT dev_contact) AS developers,
    ROUND(AVG(days_to_reach), 0) AS avg_days_from_first_activity,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_to_reach), 0) AS median_days
FROM (
    SELECT
        at.dev_contact,
        at.journey_stage,
        DATE_DIFF('day',
            MIN(at.activity_date) OVER (PARTITION BY at.dev_contact)::DATE,
            MIN(at.activity_date) OVER (PARTITION BY at.dev_contact, at.journey_stage)::DATE
        ) AS days_to_reach
    FROM activity_tagged at
)
WHERE days_to_reach > 0
GROUP BY journey_stage
ORDER BY
    CASE journey_stage
        WHEN 'Discover' THEN 1 WHEN 'Learn' THEN 2
        WHEN 'Evaluate' THEN 3 WHEN 'Build' THEN 4
        WHEN 'Champion' THEN 5
    END
""").fetchdf()

print("=== TIME TO REACH EACH STAGE (from first-ever activity) ===")
print(time_to_stage.to_string(index=False))


# ANALYSIS 14: STAGE TRANSITION PATTERNS
# What is the most common stage combination per developer?
# This reveals real journey archetypes.

stage_combos = con.execute("""
SELECT
    stage_combo,
    COUNT(*) AS developers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM (
    SELECT
        dev_contact,
        STRING_AGG(DISTINCT journey_stage, ' + ' ORDER BY
            CASE journey_stage
                WHEN 'Discover' THEN 1 WHEN 'Learn' THEN 2
                WHEN 'Evaluate' THEN 3 WHEN 'Build' THEN 4
                WHEN 'Champion' THEN 5
            END
        ) AS stage_combo
    FROM activity_tagged
    GROUP BY dev_contact
)
GROUP BY stage_combo
ORDER BY developers DESC
LIMIT 20
""").fetchdf()

print("=== TOP 20 STAGE COMBINATION PATTERNS ===")
print(stage_combos.to_string(index=False))


# ANALYSIS 15: ACTIVITY VOLUME — STAGE SHARE PER DEVELOPER
# For multi-stage developers, what % of their activity
# is in each stage? Is one stage dominant or spread evenly?

stage_share = con.execute("""
SELECT
    stage_bucket,
    COUNT(*) AS developers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM (
    SELECT
        dev_contact,
        CASE
            WHEN max_share >= 0.8 THEN 'Dominated by 1 stage (80%+)'
            WHEN max_share >= 0.5 THEN 'Majority in 1 stage (50-80%)'
            ELSE 'Spread across stages (<50%)'
        END AS stage_bucket
    FROM (
        SELECT
            dev_contact,
            MAX(stage_pct) AS max_share
        FROM (
            SELECT
                dev_contact,
                journey_stage,
                COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY dev_contact) AS stage_pct
            FROM activity_tagged
            GROUP BY dev_contact, journey_stage
        )
        GROUP BY dev_contact
    )
    WHERE (SELECT COUNT(DISTINCT journey_stage) FROM activity_tagged a2
           WHERE a2.dev_contact = dev_contact) > 1
)
GROUP BY stage_bucket
ORDER BY developers DESC
""").fetchdf()

print("=== STAGE CONCENTRATION FOR MULTI-STAGE DEVELOPERS ===")
print(stage_share.to_string(index=False))


# ANALYSIS 16: CHAMPION DEEP DIVE — WHAT MAKES THEM SPECIAL?
# Compare Champions to all other developers on key metrics.

champion_deep = con.execute("""
WITH champion_devs AS (
    SELECT DISTINCT dev_contact FROM activity_tagged WHERE journey_stage = 'Champion'
),
dev_metrics AS (
    SELECT
        at.dev_contact,
        CASE WHEN cd.dev_contact IS NOT NULL THEN 'Champion' ELSE 'Others' END AS dev_group,
        COUNT(*) AS total_activities,
        COUNT(DISTINCT at.activity) AS distinct_activity_types,
        COUNT(DISTINCT at.journey_stage) AS stages_touched,
        DATE_DIFF('day', MIN(at.activity_date)::DATE, MAX(at.activity_date)::DATE) AS active_span_days,
        COUNT(DISTINCT DATE_TRUNC('month', at.activity_date::DATE)) AS active_months
    FROM activity_tagged at
    LEFT JOIN champion_devs cd ON at.dev_contact = cd.dev_contact
    GROUP BY at.dev_contact, dev_group
)
SELECT
    dev_group,
    COUNT(*) AS developers,
    ROUND(AVG(total_activities), 1) AS avg_activities,
    ROUND(AVG(distinct_activity_types), 1) AS avg_activity_types,
    ROUND(AVG(stages_touched), 1) AS avg_stages,
    ROUND(AVG(active_span_days), 0) AS avg_span_days,
    ROUND(AVG(active_months), 1) AS avg_active_months
FROM dev_metrics
GROUP BY dev_group
""").fetchdf()

print("=== CHAMPION vs EVERYONE ELSE ===")
print(champion_deep.to_string(index=False))



# SUMMARY: PRINT KEY FINDINGS
print("""
Review the outputs above and note:

1. FUNNEL SHAPE: Does developer count decrease from
   Discover → Learn → Evaluate → Build → Champion?

2. CO-OCCURRENCE: Do Build/Champion developers almost
   always have Evaluate activity too? (validates ordering)

3. TEMPORAL ORDER: Is the % correct order > 60% for
   each transition? If not, the linear model may not hold.

4. ENTRY POINTS: Do most developers enter at Discover,
   or do many skip straight to Evaluate? (affects funnel)

5. STAGE COMBOS: What are the most common journey
   archetypes? (single-stage vs multi-stage patterns)

6. CHAMPION PROFILE: Are Champions fundamentally different
   from other developers? (more active, longer tenure, etc.)

7. COUNT DISTRIBUTIONS: Where are natural breaks in
   Build/Champion counts? (informs threshold decisions)
""")
