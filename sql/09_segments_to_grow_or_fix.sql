-- 09 | Category x city-tier segments to GROW or FIX
--   FIX  : segment ROAS < 70% of overall ROAS  (and enough spend to matter)
--   GROW : segment ROAS > 120% of overall ROAS
-- Thresholds are documented in docs/METRIC_DEFINITIONS.md and src/config.py
-- Business question: "Which segments should the sales / product team grow or fix first?"
WITH overall AS (
    SELECT SUM(attributed_revenue) / SUM(spend) AS overall_roas FROM daily_performance
),
seg AS (
    SELECT
        a.category,
        a.city_tier,
        COUNT(DISTINCT a.advertiser_id)                         AS advertisers,
        SUM(dp.spend)                                           AS spend,
        SUM(dp.attributed_revenue) / SUM(dp.spend)              AS roas,
        100.0 * SUM(dp.clicks) / SUM(dp.impressions)            AS ctr_pct,
        100.0 * SUM(dp.orders) / SUM(dp.clicks)                 AS click_to_order_pct
    FROM daily_performance dp
    JOIN campaigns   c USING (campaign_id)
    JOIN advertisers a USING (advertiser_id)
    GROUP BY a.category, a.city_tier
    HAVING COUNT(DISTINCT a.advertiser_id) >= 3
)
SELECT
    s.category,
    s.city_tier,
    s.advertisers,
    ROUND(s.spend, 0)                                           AS ad_revenue_inr,
    ROUND(s.roas, 2)                                            AS roas,
    ROUND(o.overall_roas, 2)                                    AS overall_roas,
    ROUND(s.roas / o.overall_roas, 2)                           AS roas_vs_overall,
    ROUND(s.ctr_pct, 3)                                         AS ctr_pct,
    ROUND(s.click_to_order_pct, 2)                              AS click_to_order_pct,
    CASE
        WHEN s.roas < 0.70 * o.overall_roas THEN 'FIX'
        WHEN s.roas > 1.20 * o.overall_roas THEN 'GROW'
        ELSE 'MAINTAIN'
    END                                                         AS action
FROM seg s
CROSS JOIN overall o
ORDER BY s.roas / o.overall_roas;
