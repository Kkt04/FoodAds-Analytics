-- 10 | Inputs for opportunity sizing: last 3 months, by placement
-- Feeds src/opportunity_sizing.py
WITH bounds AS (
    SELECT date((SELECT MAX(date) FROM daily_performance), 'start of month', '-2 months') AS from_date
),
filled AS (
    SELECT c.placement, SUM(dp.impressions) AS impressions, SUM(dp.spend) AS spend
    FROM daily_performance dp
    JOIN campaigns c USING (campaign_id)
    CROSS JOIN bounds b
    WHERE dp.date >= b.from_date
    GROUP BY c.placement
),
cap AS (
    SELECT i.placement, SUM(i.capacity_impressions) AS capacity
    FROM inventory i
    CROSS JOIN bounds b
    WHERE i.date >= b.from_date
    GROUP BY i.placement
)
SELECT
    f.placement,
    f.impressions                                  AS impressions_3m,
    cap.capacity                                   AS capacity_3m,
    ROUND(1.0 * f.impressions / cap.capacity, 4)   AS fill_rate,
    ROUND(1000.0 * f.spend / f.impressions, 2)     AS cpm_inr,
    ROUND(f.spend, 0)                              AS ad_revenue_3m_inr
FROM filled f
JOIN cap USING (placement)
ORDER BY f.placement;
