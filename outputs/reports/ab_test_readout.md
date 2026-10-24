# A/B Test Readout: "Bestseller badge" ad format (Sponsored Carousel)

> Data is **simulated**. The method is real; the numbers are not from any real platform.

**Hypothesis:** adding a "Bestseller" badge to the Sponsored Carousel ad will increase click-through rate
without hurting downstream conversion.

**Design:** randomised split, 30,000 control users vs 30,000 treatment users, alpha = 0.05, two-sided tests.

| Metric | Control | Treatment | Relative lift | 95% CI of difference | p-value | Significant? |
|---|---|---|---|---|---|---|
| **CTR (primary)** | 3.06% | 3.62% | +18.2% | [+0.269 pp, +0.844 pp] | 0.0001 | Yes |
| Orders per exposed user | 0.51% | 0.65% | +27.6% | [+0.019 pp, +0.261 pp] | 0.0235 | Yes |
| Click-to-order rate (guardrail) | 16.54% | 17.86% | +8.0% | [-1.987 pp, +4.635 pp] | 0.4344 | No |
| Revenue per exposed user, INR (guardrail) | 1.637 | 2.077 | +26.9% | [+0.027, +0.853] | 0.0368 | Yes |

*CI units: percentage points (pp) for rates, INR for revenue per user.*

## Decision: **SHIP**

Primary metric improved significantly and no guardrail deteriorated.

## What this means
- The badge changes CTR by **+18.2%** relative (+0.56 pp), statistically significant (p = 0.0001).
- Click-to-order rate did not drop (+8.0%, p = 0.434), so the extra clicks are not obviously lower quality.
- Orders per exposed user changed significantly (+27.6%, p = 0.0235).
- Advertisers pay per impression (CPM), so platform ad revenue is unaffected by CTR; advertisers care about ROAS, which depends on orders.

## Recommendation
Roll the badge out, but keep monitoring orders per user and advertiser ROAS for the badge cohort after launch.

## Method notes
- Rates: two-proportion z-test (pooled standard error for the test, unpooled for the confidence interval).
- Revenue per user: Welch's t-test (does not assume equal variance).
- Decision rule: SHIP if primary wins and no guardrail worsens; RAMP CAUTIOUSLY if primary wins and guardrails are negative but not significant;
  HOLD if a guardrail is significantly worse; DO NOT SHIP otherwise.
- Limitation: several metrics are tested, so a stricter analysis would apply a multiple-comparison correction (e.g. Bonferroni).
