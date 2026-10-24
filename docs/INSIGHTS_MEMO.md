# Insights Memo: Ads Marketplace, Jul 2025 - Jun 2026

**To:** Ads leadership | **From:** Analytics | **Data:** simulated (see README). Numbers below are for `seed=42`; a different seed gives different numbers but the same structure.

## Bottom line
Ad revenue grew about 5.6x over the year (INR 1.1 cr in Jul 2025 to INR 6.3 cr in Jun 2026) on the back of more advertisers and more traffic, **not** better returns: ROAS stayed flat at about 3.5x. The growth is healthy, but **28% of ad revenue sits in category-city segments whose ROAS is below 70% of average**, and those are the segments most likely to stop spending. Fix those, and use the unsold inventory in high-return placements, before pushing volume further.

## What we found
1. **Returns vary a lot by category.** Biryani (5.6x), North Indian (5.0x), Pizza (4.8x) and Burgers (4.7x) are well above the 3.5x average. Beverages (1.1x) and Desserts (1.6x) are far below, driven by low order values (INR 140 and INR 190 vs INR 380 for Biryani). Beverages alone is 14% of ad revenue.
2. **High CTR does not mean high return.** Beverages and Desserts have an above-average CTR (about 3.8%) but cost INR 116-129 per order against INR 61-67 for Burgers and Biryani. Clicks are not the problem; basket size is.
3. **Home Banner is the weak slot.** Lowest CTR (1.3%), INR 27 per click (about double the other placements), INR 265 per order (5x Cart Page's INR 54) and only 1.3x ROAS. It is also the least sold (64% fill in Jun 2026).
4. **Cart Page is the best slot, and it is underfilled.** ROAS 5.8x and click-to-order 22%, yet only 76% filled. Search Top is nearly sold out (90% fill, 90% of June days at least 85% sold), so more volume is not available there; price is the lever.
5. **Small advertisers leave first.** About 31% of SMB advertisers churned vs 14% of Mid and 3% of Chain. In this data, churn does not track ROAS quartile, so we should not claim low returns cause churn; that needs a proper test.
6. **Retention is solid early, decays after month 3.** About 95% of advertisers are still spending after 3 months and about 86% after 6.
7. **The Bestseller-badge format works on CTR.** CTR +18% relative (3.06% to 3.62%, p = 0.0001). Orders per user also rose (+28%, p = 0.02) and click-to-order did not fall, so there is no sign of lower-quality clicks.

## Recommendations
| # | Action | Why | Owner |
|---|---|---|---|
| 1 | Run a **"fix" programme** for Beverages and Desserts (creative, bundles / higher-value items, bid guidance) | 14% + 9% of revenue at 1.1x and 1.6x ROAS | Sales + Ads Product |
| 2 | **Sell more Cart Page inventory** to high-ROAS categories (Biryani, Pizza, Burgers, North Indian) | Best ROAS, 24% unsold | Sales |
| 3 | **Re-price or re-position Home Banner** (lower floor price, better targeting or creative) | 1.3x ROAS, lowest fill | Ads Product |
| 4 | **Raise Search Top floor price** instead of adding volume | Near capacity | Pricing |
| 5 | **Ship the Bestseller badge** and monitor advertiser ROAS for the badge cohort | Significant CTR and order lift | Product |
| 6 | Build **early-warning for SMB advertisers** (spend drop in first 3 months) | SMB churn is 10x Chain | Account mgmt |

## Opportunity size (assumption-driven)
If fill rates rise 3 / 6 / 10 percentage points (capped at 92%) and the extra impressions sell 40% / 25% / 10% cheaper than today's average CPM, incremental ad revenue is about **INR 0.4 / 0.8 / 1.5 cr per quarter** (+2% / +4% / +8%). See `outputs/reports/opportunity_sizing.md`.

## Caveats
- Simulated data: these are demonstrations of method, not real market findings.
- ROAS is sales divided by ad spend. It is not profit; a 1.1x ROAS is likely loss-making once food margins are included (hypothesis).
- Attribution is click-based; view-through and halo effects are ignored.
- The A/B test tests four metrics at 5% each; a stricter analysis would correct for multiple comparisons.
- Category x tier cells with few advertisers (for example Healthy x Tier-2, 4 advertisers) are noisy.

## Suggested next steps
1. Validate the "Beverages / Desserts" finding with margin data (is 1.1x ROAS actually unprofitable?).
2. Run a price-elasticity test on Search Top.
3. Re-run the badge test with a larger sample on order-level metrics.
