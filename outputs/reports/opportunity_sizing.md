# Opportunity Sizing: selling more unsold ad inventory

> Based on **simulated** data. Figures in INR (1 crore = 10,000,000).

**Question:** if we raise the fill rate of our ad placements, how much extra ad revenue can we expect?

## Assumptions

- **Conservative:** fill rate +3 pp (capped at 92%), the extra impressions sell at a 40% lower CPM than today's average
- **Base:** fill rate +6 pp (capped at 92%), the extra impressions sell at a 25% lower CPM than today's average
- **Optimistic:** fill rate +10 pp (capped at 92%), the extra impressions sell at a 10% lower CPM than today's average

## Result (last 3 months as baseline)

| Scenario | Incremental ad revenue, 3 months | Annualised | Uplift vs baseline |
|---|---|---|---|
| Conservative | INR 0.38 cr | INR 1.51 cr | +2.0% |
| Base | INR 0.81 cr | INR 3.25 cr | +4.4% |
| Optimistic | INR 1.52 cr | INR 6.08 cr | +8.3% |

## Where the opportunity sits (Base scenario)

| Placement | Fill now | Fill after | Incremental revenue, 3 months |
|---|---|---|---|
| Cart Page | 74.0% | 80.0% | INR 0.20 cr |
| Home Banner | 61.9% | 67.9% | INR 0.19 cr |
| Category Listing | 79.8% | 85.8% | INR 0.18 cr |
| Search Top | 90.0% | 92.0% | INR 0.13 cr |
| Sponsored Carousel | 70.0% | 76.0% | INR 0.11 cr |

## Caveats

- Fill uplift and marginal-price discount are assumptions, not measurements. Validate them with a pricing / supply experiment.
- More impressions only help if demand exists: advertisers must be willing to buy the extra volume at the new CPM.
- Low-performing placements (low ROAS) may not sustain higher prices; check advertiser ROAS before pushing volume.
- Sensitivity: change `SCENARIOS` at the top of `src/opportunity_sizing.py` and re-run.
