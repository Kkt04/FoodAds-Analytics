"""
Generate a SIMULATED food-delivery ads dataset.

!! All data produced here is synthetic. It is NOT real Swiggy / Zomato / advertiser data. !!

Business patterns deliberately "planted" so the analysis has something to find
(each one is documented in docs/DATA_DICTIONARY.md):

  * Low-AOV categories (Desserts, Beverages) earn a lower ROAS than high-AOV ones.
  * "Healthy" converts much worse in Tier-2 cities.
  * Home Banner: expensive (high CPM), low CTR, low fill rate  -> weak ROAS, spare inventory.
  * Cart Page / Search Top: high intent -> high CTR and CVR -> strong ROAS.
  * Weekends (Fri-Sun) and festive months (Oct-Nov) carry more impressions.
  * SMB advertisers churn more (strong signal); low-ROAS categories get a small extra churn risk (weak signal at 300 advertisers).
  * A/B test: the new 'Bestseller badge' ad format lifts CTR by ~20% (relative).

Run:  python -m src.generate_data --seed 42
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src import config

START = pd.Timestamp("2025-07-01")
END = pd.Timestamp("2026-06-30")
NEW_SIGNUP_END = pd.Timestamp("2026-04-30")

# category -> average order value (INR), click->order conversion, CTR multiplier
CATEGORIES = {
    "Biryani":      dict(aov=380, cvr=0.17, ctr_mult=1.05, weight=0.14),
    "Pizza":        dict(aov=420, cvr=0.15, ctr_mult=1.00, weight=0.11),
    "Burgers":      dict(aov=290, cvr=0.16, ctr_mult=1.00, weight=0.11),
    "Chinese":      dict(aov=340, cvr=0.14, ctr_mult=0.95, weight=0.10),
    "North Indian": dict(aov=400, cvr=0.16, ctr_mult=1.00, weight=0.14),
    "South Indian": dict(aov=210, cvr=0.19, ctr_mult=0.95, weight=0.08),
    "Desserts":     dict(aov=190, cvr=0.10, ctr_mult=1.10, weight=0.09),
    "Beverages":    dict(aov=140, cvr=0.09, ctr_mult=1.05, weight=0.07),
    "Healthy":      dict(aov=360, cvr=0.12, ctr_mult=0.90, weight=0.06),
    "Fast Food":    dict(aov=260, cvr=0.15, ctr_mult=1.00, weight=0.10),
}
LOW_ROAS_CATEGORIES = {"Desserts", "Beverages", "Healthy"}

# placement -> CPM (INR per 1000 impressions), base CTR, CVR multiplier,
# target fill rate in the latest quarter, share of campaigns
PLACEMENTS = {
    "Search Top":         dict(cpm=600, ctr=0.045, cvr_mult=1.15, fill=0.90, share=0.30),
    "Home Banner":        dict(cpm=320, ctr=0.012, cvr_mult=0.70, fill=0.62, share=0.20),
    "Cart Page":          dict(cpm=700, ctr=0.060, cvr_mult=1.35, fill=0.74, share=0.10),
    "Category Listing":   dict(cpm=350, ctr=0.028, cvr_mult=1.00, fill=0.80, share=0.25),
    "Sponsored Carousel": dict(cpm=300, ctr=0.020, cvr_mult=0.90, fill=0.70, share=0.15),
}

SIZES = {
    "SMB":   dict(share=0.60, base_imps=2500,  ctr_mult=0.92, churn=0.40),
    "Mid":   dict(share=0.28, base_imps=9000,  ctr_mult=1.00, churn=0.22),
    "Chain": dict(share=0.12, base_imps=28000, ctr_mult=1.10, churn=0.10),
}
TIERS = {
    "Metro":  dict(share=0.45, cvr_mult=1.05),
    "Tier-1": dict(share=0.35, cvr_mult=1.00),
    "Tier-2": dict(share=0.20, cvr_mult=0.88),
}

NAME_PREFIX = ["Royal", "Tasty", "Urban", "Spice", "Golden", "Fresh", "Desi", "Crispy", "Smoky", "Cloud"]
NAME_SUFFIX = ["Kitchen", "House", "Hub", "Corner", "Co.", "Express", "Studio", "Bites"]

MONTHLY_GROWTH = 1.025  # platform traffic growth per month


# --------------------------------------------------------------------------- advertisers
def _make_advertisers(rng: np.random.Generator, n: int) -> pd.DataFrame:
    cats = list(CATEGORIES)
    category = rng.choice(cats, n, p=[CATEGORIES[c]["weight"] for c in cats])
    size = rng.choice(list(SIZES), n, p=[SIZES[s]["share"] for s in SIZES])
    tier = rng.choice(list(TIERS), n, p=[TIERS[t]["share"] for t in TIERS])

    # ~35% of advertisers already existed before the data window opens
    existing = rng.random(n) < 0.35
    old_days = rng.integers(0, 181, n)                                    # Jan-Jun 2025
    new_days = rng.integers(0, (NEW_SIGNUP_END - START).days + 1, n)      # Jul 2025 - Apr 2026
    signup = np.where(
        existing,
        pd.Timestamp("2025-01-01") + pd.to_timedelta(old_days, "D"),
        START + pd.to_timedelta(new_days, "D"),
    )
    signup = pd.to_datetime(signup)

    churn_p = np.array([SIZES[s]["churn"] for s in size])
    churn_p = churn_p * np.where(np.isin(category, list(LOW_ROAS_CATEGORIES)), 1.35, 1.0)
    will_churn = rng.random(n) < churn_p
    effective_start = signup.where(signup >= START, START)
    tenure = rng.integers(45, 300, n)
    churn_date = effective_start + pd.to_timedelta(tenure, "D")
    churn_date = churn_date.where(will_churn & (churn_date < END), pd.NaT)

    names = [
        f"{rng.choice(NAME_PREFIX)} {c} {rng.choice(NAME_SUFFIX)}"
        for c in category
    ]
    return pd.DataFrame({
        "advertiser_id": [f"ADV{i:04d}" for i in range(1, n + 1)],
        "advertiser_name": names,
        "category": category,
        "city_tier": tier,
        "advertiser_size": size,
        "signup_date": signup.strftime("%Y-%m-%d"),
        "churn_date": pd.Series(churn_date).dt.strftime("%Y-%m-%d").fillna(""),
    })


# --------------------------------------------------------------------------- campaigns
def _make_campaigns(rng: np.random.Generator, adv: pd.DataFrame) -> pd.DataFrame:
    placements = list(PLACEMENTS)
    p_share = [PLACEMENTS[p]["share"] for p in placements]
    rows = []
    cid = 1
    for a in adv.itertuples():
        signup = max(pd.Timestamp(a.signup_date), START)
        adv_end = pd.Timestamp(a.churn_date) if a.churn_date else END
        n_camp = rng.choice([1, 2, 3], p=[0.55, 0.30, 0.15])
        for k in range(n_camp):
            if k == 0:
                start = signup + pd.Timedelta(days=int(rng.integers(0, 15)))
                end = adv_end
            else:
                start = signup + pd.Timedelta(days=int(rng.integers(10, 150)))
                end = adv_end
                if rng.random() < 0.30:
                    end = min(adv_end, start + pd.Timedelta(days=int(rng.integers(30, 150))))
            if start >= end:
                continue
            rows.append({
                "campaign_id": f"CMP{cid:05d}",
                "advertiser_id": a.advertiser_id,
                "placement": rng.choice(placements, p=p_share),
                "start_date": start,
                "end_date": end,
                # hidden "latent" attributes used only to simulate performance
                "_quality": rng.lognormal(0, 0.15),
                "_bid_mult": rng.uniform(0.88, 1.20),
                "_vol": rng.lognormal(0, 0.30),
            })
            cid += 1
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- daily performance
def _make_daily_performance(rng, adv: pd.DataFrame, camp: pd.DataFrame) -> pd.DataFrame:
    cx = camp.merge(adv[["advertiser_id", "category", "city_tier", "advertiser_size"]], on="advertiser_id")
    n_days = ((cx["end_date"] - cx["start_date"]).dt.days + 1).to_numpy()
    idx = np.repeat(np.arange(len(cx)), n_days)
    offsets = np.concatenate([np.arange(n) for n in n_days])

    rows = cx.iloc[idx].reset_index(drop=True)
    rows["date"] = rows["start_date"] + pd.to_timedelta(offsets, "D")

    keep = rng.random(len(rows)) > 0.03          # ~3% of campaign-days are paused
    rows = rows[keep].reset_index(drop=True)

    months = ((rows["date"].dt.year - 2025) * 12 + rows["date"].dt.month - 7).to_numpy()
    weekend = (rows["date"].dt.day_of_week >= 4).to_numpy()          # Fri, Sat, Sun
    festive = rows["date"].dt.month.isin([10, 11]).to_numpy()

    base_imps = rows["advertiser_size"].map({k: v["base_imps"] for k, v in SIZES.items()}).to_numpy()
    mean_imps = (base_imps * rows["_vol"].to_numpy()
                 * np.where(weekend, 1.15, 1.0)
                 * np.where(festive, 1.15, 1.0)
                 * MONTHLY_GROWTH ** months)
    impressions = rng.poisson(mean_imps)

    plc = rows["placement"]
    cat = rows["category"]
    ctr = (plc.map({k: v["ctr"] for k, v in PLACEMENTS.items()}).to_numpy()
           * cat.map({k: v["ctr_mult"] for k, v in CATEGORIES.items()}).to_numpy()
           * rows["advertiser_size"].map({k: v["ctr_mult"] for k, v in SIZES.items()}).to_numpy()
           * rows["_quality"].to_numpy()
           * np.where(weekend, 1.04, 1.0)
           * rng.lognormal(0, 0.05, len(rows)))
    ctr = np.clip(ctr, 0, 0.30)
    clicks = rng.binomial(impressions, ctr)

    cvr = (cat.map({k: v["cvr"] for k, v in CATEGORIES.items()}).to_numpy()
           * plc.map({k: v["cvr_mult"] for k, v in PLACEMENTS.items()}).to_numpy()
           * rows["city_tier"].map({k: v["cvr_mult"] for k, v in TIERS.items()}).to_numpy())
    healthy_t2 = (cat == "Healthy").to_numpy() & (rows["city_tier"] == "Tier-2").to_numpy()
    cvr = np.where(healthy_t2, cvr * 0.60, cvr)          # planted: Healthy underperforms in Tier-2
    cvr = np.clip(cvr, 0, 0.50)
    orders = rng.binomial(clicks, cvr)

    cpm = (plc.map({k: v["cpm"] for k, v in PLACEMENTS.items()}).to_numpy()
           * rows["_bid_mult"].to_numpy()
           * (1 + 0.006 * months)
           * rng.lognormal(0, 0.05, len(rows)))
    spend = impressions * cpm / 1000.0

    aov = cat.map({k: v["aov"] for k, v in CATEGORIES.items()}).to_numpy()
    revenue = orders * aov * rng.lognormal(0, 0.04, len(rows))

    return pd.DataFrame({
        "date": rows["date"].dt.strftime("%Y-%m-%d"),
        "campaign_id": rows["campaign_id"],
        "impressions": impressions.astype(int),
        "clicks": clicks.astype(int),
        "orders": orders.astype(int),
        "spend": np.round(spend, 2),
        "attributed_revenue": np.round(revenue, 2),
    })


# --------------------------------------------------------------------------- inventory
def _make_inventory(rng, perf: pd.DataFrame, camp: pd.DataFrame) -> pd.DataFrame:
    """Ad-slot capacity per placement per day, driven by platform traffic (NOT by advertiser demand).

    Level is calibrated so the last ~90 days land near each placement's target fill rate.
    """
    filled = (perf.merge(camp[["campaign_id", "placement"]], on="campaign_id")
                  .groupby(["date", "placement"], as_index=False)["impressions"].sum()
                  .rename(columns={"impressions": "filled"}))

    dates = pd.date_range(START, END)
    grid = pd.MultiIndex.from_product([dates, list(PLACEMENTS)], names=["date", "placement"]).to_frame(index=False)
    grid["date_s"] = grid["date"].dt.strftime("%Y-%m-%d")
    months = ((grid["date"].dt.year - 2025) * 12 + grid["date"].dt.month - 7).to_numpy()
    shape = (MONTHLY_GROWTH ** months
             * np.where(grid["date"].dt.day_of_week >= 4, 1.15, 1.0)
             * np.where(grid["date"].dt.month.isin([10, 11]), 1.15, 1.0)
             * rng.normal(1.0, 0.04, len(grid)))
    grid["shape"] = shape

    grid = grid.merge(filled, left_on=["date_s", "placement"], right_on=["date", "placement"],
                      how="left", suffixes=("", "_f"))
    grid["filled"] = grid["filled"].fillna(0)

    recent = grid["date"] > (END - pd.Timedelta(days=90))
    capacity = np.zeros(len(grid))
    for p, spec in PLACEMENTS.items():
        m = (grid["placement"] == p)
        r = m & recent
        scale = grid.loc[r, "filled"].mean() / (spec["fill"] * grid.loc[r, "shape"].mean())
        capacity[m.to_numpy()] = scale * grid.loc[m, "shape"].to_numpy()
    capacity = np.maximum(capacity, grid["filled"].to_numpy() / 0.99)   # fill rate can never exceed 100%

    return pd.DataFrame({
        "date": grid["date_s"],
        "placement": grid["placement"],
        "capacity_impressions": np.ceil(capacity).astype(int),
    })


# --------------------------------------------------------------------------- A/B test
def _make_ab_test(rng, n_per_arm: int) -> pd.DataFrame:
    """Experiment: 'Bestseller badge' ad format on the Sponsored Carousel (control vs treatment)."""
    n = 2 * n_per_arm
    variant = np.array(["control"] * n_per_arm + ["treatment"] * n_per_arm)
    ctr = np.where(variant == "control", 0.030, 0.036)          # planted: +20% relative CTR
    clicked = rng.random(n) < ctr
    c2o = np.full(n, 0.180)                                      # click->order rate identical in both arms
    ordered = clicked & (rng.random(n) < c2o)
    order_value = np.where(ordered, np.round(rng.lognormal(np.log(310), 0.35, n)), 0)

    df = pd.DataFrame({
        "user_id": [f"U{i:06d}" for i in range(1, n + 1)],
        "variant": variant,
        "clicked": clicked.astype(int),
        "ordered": ordered.astype(int),
        "order_value": order_value.astype(int),
    })
    return df.sample(frac=1, random_state=int(rng.integers(0, 1_000_000))).reset_index(drop=True)


# --------------------------------------------------------------------------- public API
def generate(out_dir: Path | None = None, seed: int = config.DEFAULT_SEED,
             n_advertisers: int = config.DEFAULT_ADVERTISERS, ab_users_per_arm: int = 30_000,
             verbose: bool = True) -> dict[str, pd.DataFrame]:
    out_dir = Path(out_dir) if out_dir else config.DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    adv = _make_advertisers(rng, n_advertisers)
    camp = _make_campaigns(rng, adv)
    perf = _make_daily_performance(rng, adv, camp)
    inv = _make_inventory(rng, perf, camp)
    ab = _make_ab_test(rng, ab_users_per_arm)

    camp_out = camp[["campaign_id", "advertiser_id", "placement", "start_date", "end_date"]].copy()
    camp_out["start_date"] = camp_out["start_date"].dt.strftime("%Y-%m-%d")
    camp_out["end_date"] = camp_out["end_date"].dt.strftime("%Y-%m-%d")

    tables = {
        "advertisers": adv, "campaigns": camp_out, "daily_performance": perf,
        "inventory": inv, "ab_test_users": ab,
    }
    for name, df in tables.items():
        df.to_csv(out_dir / f"{name}.csv", index=False)
        if verbose:
            print(f"  wrote {name + '.csv':<22} {len(df):>9,} rows")
    return tables


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the SIMULATED ads dataset")
    ap.add_argument("--seed", type=int, default=config.DEFAULT_SEED)
    ap.add_argument("--advertisers", type=int, default=config.DEFAULT_ADVERTISERS)
    ap.add_argument("--ab-users-per-arm", type=int, default=30_000)
    ap.add_argument("--out", type=Path, default=config.DATA_DIR)
    a = ap.parse_args()
    print(f"Generating SIMULATED data (seed={a.seed}, advertisers={a.advertisers}) ...")
    generate(a.out, a.seed, a.advertisers, a.ab_users_per_arm)


if __name__ == "__main__":
    main()
