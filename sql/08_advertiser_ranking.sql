-- 08 | Advertiser-level scorecard (RANK within category, NTILE quartiles, churn flag)
-- Business question: "Which large advertisers are getting poor returns and may churn?"
WITH adv AS (
    SELECT
        a.advertiser_id,
        a.advertiser_name,
        a.category,
        a.city_tier,
        a.advertiser_size,
        CASE WHEN a.churn_date <> '' THEN 1 ELSE 0 END               AS churned,
        SUM(dp.spend)                                                AS spend,
        SUM(dp.attributed_revenue)                                   AS revenue,
        SUM(dp.attributed_revenue) / SUM(dp.spend)                   AS roas
    FROM daily_performance dp
    JOIN campaigns   c USING (campaign_id)
    JOIN advertisers a USING (advertiser_id)
    GROUP BY a.advertiser_id, a.advertiser_name, a.category, a.city_tier, a.advertiser_size, a.churn_date
)
SELECT
    advertiser_id,
    advertiser_name,
    category,
    city_tier,
    advertiser_size,
    churned,
    ROUND(spend, 0)                                                  AS ad_revenue_inr,
    ROUND(roas, 2)                                                   AS roas,
    RANK()  OVER (PARTITION BY category ORDER BY roas DESC)          AS roas_rank_in_category,
    NTILE(4) OVER (ORDER BY roas DESC)                               AS roas_quartile,   -- 1 = best, 4 = worst
    RANK()  OVER (ORDER BY spend DESC)                               AS spend_rank
FROM adv
ORDER BY spend DESC;
