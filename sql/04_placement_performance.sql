-- 04 | Placement (ad slot) performance
-- Business question: "Which placements deliver value for advertisers, and what do we charge for them?"
SELECT
    c.placement,
    SUM(dp.impressions)                                          AS impressions,
    ROUND(SUM(dp.spend), 0)                                      AS ad_revenue_inr,
    ROUND(100.0 * SUM(dp.clicks) / SUM(dp.impressions), 3)       AS ctr_pct,
    ROUND(1000.0 * SUM(dp.spend) / SUM(dp.impressions), 1)       AS cpm_inr,
    ROUND(SUM(dp.spend) / SUM(dp.clicks), 2)                     AS cost_per_click_inr,
    ROUND(SUM(dp.spend) / SUM(dp.orders), 1)                     AS cost_per_order_inr,
    ROUND(100.0 * SUM(dp.orders) / SUM(dp.clicks), 2)            AS click_to_order_pct,
    ROUND(SUM(dp.attributed_revenue) / SUM(dp.spend), 2)         AS roas
FROM daily_performance dp
JOIN campaigns c USING (campaign_id)
GROUP BY c.placement
ORDER BY roas DESC;
