# Metric Definitions

One place for every KPI used in this project, so everybody computes it the same way.
(Owning the metric definitions is part of any analyst's job: if two dashboards disagree, this file wins.)

> Everything here is **simulated** data. "Ad revenue" is the platform's revenue from advertisers.

| Metric | Definition | Formula | Notes |
|---|---|---|---|
| **Impressions** | Times an ad was shown | `SUM(impressions)` | |
| **Clicks** | Times an ad was clicked | `SUM(clicks)` | |
| **CTR** (click-through rate) | Share of impressions that were clicked | `clicks / impressions` | Shown as % |
| **Orders** | Orders attributed to an ad click | `SUM(orders)` | Click-based attribution only |
| **Click-to-order rate** | Share of clicks that became an order | `orders / clicks` | Often called CVR |
| **CPM** | Price per 1,000 impressions | `1000 * spend / impressions` | INR |
| **Ad revenue** | What advertisers paid the platform | `SUM(spend)` | Platform's top line from ads |
| **Attributed revenue (GMV)** | Order value driven by the ads | `SUM(attributed_revenue)` | Advertiser's sales, not platform revenue |
| **ROAS** (return on ad spend) | Advertiser sales per INR of ad spend | `attributed_revenue / spend` | 3.5x = INR 3.50 of sales per INR 1 spent. It is **not** profit |
| **Cost per click** | Spend per click | `spend / clicks` | INR |
| **Cost per order** | Spend per attributed order | `spend / orders` | INR (CPA) |
| **Average order value** | Order size | `attributed_revenue / orders` | INR |
| **Capacity** | Ad slots available to sell | `SUM(capacity_impressions)` | Set by platform traffic, not by advertisers |
| **Fill rate** | Share of available ad slots that carried an ad | `filled impressions / capacity` | Low = unsold inventory |
| **Inventory utilisation (high-utilisation days)** | Share of days a placement was at least 85% sold | `% of days with fill >= 85%` | High = capacity constrained, so price is the lever, not volume |
| **Active advertiser** | Advertiser with spend > 0 in the period | `COUNT(DISTINCT advertiser)` | |
| **Retention** | Share of a cohort still spending N months after first spend | `active in month N / cohort size` | Cohort = first active month. The first cohort (2025-07) also contains advertisers who joined earlier |
| **Churned advertiser** | Advertiser with a `churn_date` | flag | Simulated field |

## Segment actions (query 09)
Let `overall_roas` = total attributed revenue / total spend.

| Action | Rule |
|---|---|
| FIX | segment ROAS < 70% of overall ROAS |
| GROW | segment ROAS > 120% of overall ROAS |
| MAINTAIN | everything in between |

Segments with fewer than 3 advertisers are dropped (too noisy). Thresholds live in `sql/09_segments_to_grow_or_fix.sql` and `src/config.py`.

## A/B test metrics
| Role | Metric | Test |
|---|---|---|
| Primary | CTR (clicks / exposed users) | two-proportion z-test |
| Secondary | Orders per exposed user | two-proportion z-test |
| Guardrail | Click-to-order rate | two-proportion z-test |
| Guardrail | Revenue per exposed user | Welch t-test |

Significance level: 5% (two-sided). Target power: 80%.
