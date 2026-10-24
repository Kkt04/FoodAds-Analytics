-- 01 | Headline KPIs for the ads P&L (whole period)
-- Business question: "What does the ads business look like at a glance?"
SELECT
    SUM(dp.impressions)                                        AS impressions,
    SUM(dp.clicks)                                             AS clicks,
    SUM(dp.orders)                                             AS orders,
    ROUND(SUM(dp.spend), 0)                                    AS ad_revenue_inr,        -- advertiser spend = platform ad revenue
    ROUND(SUM(dp.attributed_revenue), 0)                       AS attributed_gmv_inr,    -- sales driven for advertisers
    ROUND(100.0 * SUM(dp.clicks) / SUM(dp.impressions), 3)     AS ctr_pct,
    ROUND(1000.0 * SUM(dp.spend) / SUM(dp.impressions), 1)     AS cpm_inr,
    ROUND(100.0 * SUM(dp.orders) / SUM(dp.clicks), 2)          AS click_to_order_pct,
    ROUND(SUM(dp.attributed_revenue) / SUM(dp.spend), 2)       AS roas,
    COUNT(DISTINCT c.advertiser_id)                            AS advertisers_with_spend
FROM daily_performance dp
JOIN campaigns c USING (campaign_id);
