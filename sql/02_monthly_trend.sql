-- 02 | Monthly trend with month-over-month growth (window function LAG)
-- Business question: "Is the ads business growing, and is growth coming from volume or price?"
WITH monthly AS (
    SELECT
        substr(dp.date, 1, 7)               AS month,
        SUM(dp.impressions)                 AS impressions,
        SUM(dp.clicks)                      AS clicks,
        SUM(dp.orders)                      AS orders,
        SUM(dp.spend)                       AS spend,
        SUM(dp.attributed_revenue)          AS revenue,
        COUNT(DISTINCT c.advertiser_id)     AS active_advertisers
    FROM daily_performance dp
    JOIN campaigns c USING (campaign_id)
    GROUP BY 1
)
SELECT
    month,
    impressions,
    clicks,
    orders,
    ROUND(spend, 0)                                                         AS ad_revenue_inr,
    ROUND(100.0 * clicks / impressions, 3)                                  AS ctr_pct,
    ROUND(1000.0 * spend / impressions, 1)                                  AS cpm_inr,
    ROUND(revenue / spend, 2)                                               AS roas,
    active_advertisers,
    ROUND(100.0 * (spend - LAG(spend) OVER (ORDER BY month))
          / LAG(spend) OVER (ORDER BY month), 1)                            AS ad_revenue_mom_pct,
    ROUND(100.0 * (impressions - LAG(impressions) OVER (ORDER BY month))
          / LAG(impressions) OVER (ORDER BY month), 1)                      AS impressions_mom_pct
FROM monthly
ORDER BY month;
