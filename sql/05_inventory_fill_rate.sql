-- 05 | Fill rate and inventory utilisation by placement and month
--   fill_rate_pct             = delivered ad impressions / available ad-slot capacity
--   high_utilisation_days_pct = share of days on which a placement was >= 85% sold
-- Business question: "Where do we have unsold inventory, and where are we capacity-constrained?"
WITH filled AS (
    SELECT dp.date, c.placement, SUM(dp.impressions) AS filled_impressions
    FROM daily_performance dp
    JOIN campaigns c USING (campaign_id)
    GROUP BY dp.date, c.placement
),
daily AS (
    SELECT
        i.date,
        i.placement,
        i.capacity_impressions                                        AS capacity,
        COALESCE(f.filled_impressions, 0)                             AS filled,
        1.0 * COALESCE(f.filled_impressions, 0) / i.capacity_impressions AS fill
    FROM inventory i
    LEFT JOIN filled f ON f.date = i.date AND f.placement = i.placement
)
SELECT
    substr(date, 1, 7)                                                AS month,
    placement,
    SUM(capacity)                                                     AS capacity_impressions,
    SUM(filled)                                                       AS filled_impressions,
    ROUND(100.0 * SUM(filled) / SUM(capacity), 1)                     AS fill_rate_pct,
    ROUND(100.0 * AVG(CASE WHEN fill >= 0.85 THEN 1.0 ELSE 0.0 END), 1) AS high_utilisation_days_pct
FROM daily
GROUP BY 1, 2
ORDER BY 1, 2;
