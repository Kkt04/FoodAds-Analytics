-- 07 | Advertiser retention cohorts
--   An advertiser is "active" in a month if it had spend > 0 in that month.
--   Cohort = the advertiser's first active month in the data window.
--   NOTE: the first cohort (2025-07) also contains advertisers that joined before the window opened.
-- Business question: "How quickly do advertisers drop off after they start spending?"
WITH monthly AS (
    SELECT c.advertiser_id, substr(dp.date, 1, 7) AS month
    FROM daily_performance dp
    JOIN campaigns c USING (campaign_id)
    GROUP BY 1, 2
    HAVING SUM(dp.spend) > 0
),
first_month AS (
    SELECT advertiser_id, MIN(month) AS cohort_month
    FROM monthly
    GROUP BY 1
),
activity AS (
    SELECT
        m.advertiser_id,
        f.cohort_month,
        (CAST(substr(m.month, 1, 4) AS INTEGER) - CAST(substr(f.cohort_month, 1, 4) AS INTEGER)) * 12
        + CAST(substr(m.month, 6, 2) AS INTEGER) - CAST(substr(f.cohort_month, 6, 2) AS INTEGER) AS months_since_start
    FROM monthly m
    JOIN first_month f USING (advertiser_id)
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_advertisers
    FROM first_month
    GROUP BY 1
)
SELECT
    a.cohort_month,
    a.months_since_start,
    s.cohort_advertisers,
    COUNT(DISTINCT a.advertiser_id)                                              AS active_advertisers,
    ROUND(100.0 * COUNT(DISTINCT a.advertiser_id) / s.cohort_advertisers, 1)     AS retention_pct
FROM activity a
JOIN cohort_size s USING (cohort_month)
GROUP BY a.cohort_month, a.months_since_start
ORDER BY a.cohort_month, a.months_since_start;
