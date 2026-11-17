# Executive Insights Memo: Ads Marketplace Performance & Strategic Playbook
**Period:** July 2025 – June 2026 (12-Month Operating Window)  
**Target Audience:** VP of Ads, Head of Marketplace Product, Chief Commercial Officer  
**Author:** Revenue Strategy & Marketplace Analytics  
**Dataset:** Seed 42 Simulation (300 Merchants, 448 Campaigns, 1.02B Impressions, ₹50.7 Cr Ad Spend)

---

## 1. Executive Summary: The P&L Paradox

Over the 12-month period, the FoodAds platform expanded top-line ad revenue from **INR 1.12 Cr/month (Jul 2025)** to **INR 6.32 Cr/month (Jun 2026)**—a **5.6x expansion (+472% YoY)**. Total annual ad spend collected from restaurant partners reached **INR 50.68 Cr**, generating **INR 179.54 Cr in attributed Gross Merchandise Value (GMV)**.

However, an analysis of underlying unit economics reveals a critical strategic risk:
> **The top-line boom is 100% volume-driven; marketplace efficiency has stagnated.**  
> Blended ROAS remained flat at **3.54x** throughout the year. More alarmingly, **28.2% of total ad revenue (₹14.3 Cr) is concentrated in category-city segments where merchant ROAS is below 70% of marketplace average (<2.48x)**. In low-AOV categories like Beverages (1.09x ROAS), merchants are losing money on every order once food and packaging costs are factored in.

Unless the platform addresses the unit economics of low-AOV merchants and reallocates inventory toward high-yield placements, the platform faces an impending SMB merchant churn cliff.

---

## 2. Key Findings & Diagnostic Analysis

### Finding 1: The "Low-AOV Trap" (Beverages & Desserts)
* **The Divide:** Returns diverge by over 5.1x across cuisine types:
  * **High-Yield Leaders:** Biryani (**5.64x ROAS**), North Indian (**5.01x ROAS**), Pizza (**4.84x ROAS**), and Burgers (**4.72x ROAS**).
  * **Low-Yield Laggards:** Desserts (**1.64x ROAS**) and Beverages (**1.09x ROAS**).
* **The Root Cause:** Beverages and Desserts generate strong user curiosity and high CTR (**3.83%** and **3.71%**, respectively). However, because their Average Order Value (AOV) is low (**₹140 for Beverages, ₹190 for Desserts**, compared to **₹380 for Biryani**), the fixed cost of acquisition per order (**₹129 per order for Beverages**) absorbs up to **92% of the order value**.
* **Merchant Margin Impact:** Assuming a standard restaurant food cost of 32% and platform commission of 22%, a merchant requires a minimum ROAS of **2.2x just to break even**. A 1.09x ROAS represents a severe net loss for the merchant partner on every promoted order.

### Finding 2: Placement Yield Divergence (Cart Page vs. Home Banner)
* **Cart Page is the Undervalued Star:**
  * Delivers the platform's highest ROAS (**5.80x**), highest click-to-order rate (**21.98%**), and lowest cost-per-order (**₹53.90**).
  * Yet Cart Page is **24% unsold (76% average fill rate)**, leaving **INR 20.4 Lakhs/quarter** in unmonetized high-intent inventory.
* **Home Banner is an Inefficient Drain:**
  * Delivers the lowest ROAS (**1.30x**), worst CTR (**1.30%**), and highest cost-per-order (**₹265.20**—5x higher than Cart Page).
  * Advertisers pay an effective **₹27.27 per click** for top-of-funnel browsing traffic that fails to convert downstream.
* **Search Top is Constrained by Capacity:**
  * Search Top generates **43.6% of platform ad revenue (₹22.1 Cr)** at healthy returns (**3.52x ROAS**).
  * However, it is operating at **90.0% fill rate**, with 90% of June days at or above 85% capacity. Volume cannot be increased without cluttering search results and degrading diner discovery.

### Finding 3: The SMB Churn Cliff
* **Tenure Curve:** Merchant retention is robust through the first 90 days (~95% retention at Month 3), but decays significantly to **86% by Month 6** and **72% by Month 9**.
* **Scale Disparity:**
  * **SMB Merchants:** Experience a **31.1% churn rate** (54 of 176 SMBs discontinued ad spend).
  * **Mid-Tier Merchants:** Experience **14.3% churn**.
  * **Enterprise Chains:** Experience only **3.0% churn** (1 of 33 chains churned).
* **Implication:** SMBs lack dedicated performance marketing teams. When an unguided campaign underperforms in its initial 30–60 days, they interpret ads as an expense rather than a growth engine and churn permanently.

### Finding 4: A/B Experiment Readout — Bestseller Trust Badge
* **Experimental Setup:** 60,000 randomized users (30,000 Control vs. 30,000 Treatment) exposed to a "Bestseller" trust badge on the Sponsored Carousel ad unit.
* **Results:**
  * **Primary Metric (CTR):** Increased from **3.06% to 3.62%** (+18.2% relative lift, 95% CI `[+0.27 pp, +0.84 pp]`, $p = 0.0001$).
  * **Secondary Metric (Orders / User):** Increased from **0.51% to 0.65%** (+27.6% lift, $p = 0.0235$).
  * **Guardrail 1 (Click-to-Order CVR):** Rose from **16.54% to 17.86%** (+8.0% lift, $p = 0.4344$ — zero degradation).
  * **Guardrail 2 (Revenue / Exposed User):** Lifted from **₹1.64 to ₹2.08** (+26.9% lift, $p = 0.0368$).
* **Decision:** **SHIP TO 100% PRODUCTION**. The badge adds visual trust, driving higher intent clicks without lowering conversion efficiency.

---

## 3. Strategic Action Playbook

| Initiative | Objective | Operational Mechanism | Expected Financial Impact | Owner |
|---|---|---|---|---|
| **1. Cart Page Inventory Blitz** | Monetize 24% unsold high-ROAS inventory | Restrict Cart Page bidding to cuisines with AOV > ₹300 (Biryani, Pizza, North Indian). Run automated up-sell bundles. | +₹20.4 Lakhs incremental revenue per quarter | Sales & Ad Ops |
| **2. Low-AOV "Fix" Protocol** | Stop merchant margin destruction in Beverages/Desserts | Mandate minimum basket thresholds for ad boosts (e.g., minimum order ₹250 for beverage ads) or shift to combo meal ad formats. | Protects ₹14.3 Cr annual ad spend from churning | Product & Category Mgmt |
| **3. Home Banner Repositioning** | Fix low-fill, low-ROAS placement | Reposition Home Banner as a brand-awareness / national launch slot. Introduce dayparting (lunch/dinner rush only) and lower reserve CPM by 25%. | +₹19.2 Lakhs/qtr upside; lift placement ROAS from 1.3x to 2.2x | Pricing & Monetization |
| **4. Search Top Floor Pricing** | Capture pricing power on saturated inventory | Since Search Top is at 90% capacity, increase reserve CPM floors by 12% in Metro markets during peak hours (19:00–22:00). | +₹35.0 Lakhs incremental revenue without adding ad load | Revenue Operations |
| **5. SMB "Shield" Program** | Stem the 31% SMB merchant churn | Deploy automated bid guards: if an SMB campaign ROAS drops below 2.0x in its first 14 days, auto-throttle bids and trigger an automated audit. | Reduce SMB churn from 31% to <20% | Growth & Account Mgmt |
| **6. Roll Out Bestseller Badge** | Expand high-intent Carousel volume | Ship treatment to 100% of carousel ad inventory; expand badge logic to Category Listing cards. | +18% CTR lift; +₹10.8 Lakhs/qtr incremental carousel revenue | Engineering & Design |

---

## 4. Opportunity Sizing Summary

Selling unsold ad slots across placements at discounted marginal clearing prices unlocks substantial top-line expansion:

| Scenario | Assumptions (Uplift / Marginal Discount) | Incremental Ad Revenue (3 Months) | Annualized Run-Rate | % Uplift vs. Baseline |
|---|---|---|---|---|
| **Conservative** | +3.0 pp Fill Uplift (capped at 92%) / 40% CPM Discount | **+₹37.6 Lakhs** | **+₹1.51 Cr** | **+2.0%** |
| **Base Case** | +6.0 pp Fill Uplift (capped at 92%) / 25% CPM Discount | **+₹81.6 Lakhs** | **+₹3.26 Cr** | **+4.4%** |
| **Optimistic** | +10.0 pp Fill Uplift (capped at 92%) / 10% CPM Discount | **+₹152.0 Lakhs** | **+₹6.08 Cr** | **+8.3%** |

*Note: In the Base Case, Cart Page (+₹20.4L) and Home Banner (+₹19.2L) represent 48.5% of total revenue potential.*

---

## 5. Analytical Limitations & Next Steps

1. **Merchant Margin Modeling:** ROAS is gross order value over ad spend. To evaluate absolute merchant profitability, the analytics team must integrate merchant food cost matrices and platform commission tiers.
2. **Attribution Scope:** Current attribution relies on last-click attribution within session. View-through attribution and multi-touch halo effects across organic search should be modeled via geo-lift testing.
3. **Price Elasticity Testing:** Execute a controlled 5% CPM reserve price increase in a single isolated city tier to validate Search Top price elasticity before nationwide rollout.
