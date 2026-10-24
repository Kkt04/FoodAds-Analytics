-- 06 | Advertiser segments: size x city tier
-- Business question: "Do small vs large advertisers (and metro vs Tier-2) get different returns?"
SELECT
    a.advertiser_size,
    a.city_tier,
    COUNT(DISTINCT a.advertiser_id)                                AS advertisers,
    ROUND(SUM(dp.spend), 0)                                        AS ad_revenue_inr,
    ROUND(100.0 * SUM(dp.clicks) / SUM(dp.impressions), 3)         AS ctr_pct,
    ROUND(100.0 * SUM(dp.orders) / SUM(dp.clicks), 2)              AS click_to_order_pct,
    ROUND(SUM(dp.attributed_revenue) / SUM(dp.spend), 2)           AS roas
FROM daily_performance dp
JOIN campaigns   c USING (campaign_id)
JOIN advertisers a USING (advertiser_id)
GROUP BY a.advertiser_size, a.city_tier
ORDER BY a.advertiser_size, a.city_tier;
