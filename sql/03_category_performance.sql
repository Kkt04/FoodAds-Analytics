-- 03 | Category performance: spend share, efficiency and ROAS rank
-- Business question: "Which food categories are worth growing / fixing?"
SELECT
    a.category,
    COUNT(DISTINCT a.advertiser_id)                                         AS advertisers,
    ROUND(SUM(dp.spend), 0)                                                 AS ad_revenue_inr,
    ROUND(100.0 * SUM(dp.spend) / SUM(SUM(dp.spend)) OVER (), 1)            AS spend_share_pct,
    ROUND(100.0 * SUM(dp.clicks) / SUM(dp.impressions), 3)                  AS ctr_pct,
    ROUND(1000.0 * SUM(dp.spend) / SUM(dp.impressions), 1)                  AS cpm_inr,
    ROUND(SUM(dp.spend) / SUM(dp.orders), 1)                                AS cost_per_order_inr,
    ROUND(SUM(dp.attributed_revenue) / SUM(dp.orders), 1)                   AS avg_order_value_inr,
    ROUND(SUM(dp.attributed_revenue) / SUM(dp.spend), 2)                    AS roas,
    RANK() OVER (ORDER BY SUM(dp.attributed_revenue) / SUM(dp.spend) DESC)  AS roas_rank
FROM daily_performance dp
JOIN campaigns   c USING (campaign_id)
JOIN advertisers a USING (advertiser_id)
GROUP BY a.category
ORDER BY roas DESC;
