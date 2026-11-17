"""Execute all 10 marketplace analytics pipelines using MongoDB aggregation framework.

Results are exported to outputs/tables/*.csv to drive downstream charts,
A/B testing, opportunity sizing models, and executive dashboards.
Pipeline JSON definitions are exported to mongo/*.json.
"""
from __future__ import annotations

import argparse
import json
from typing import Optional

import numpy as np
import pandas as pd
from pymongo import MongoClient

from src import config


def get_db(uri: Optional[str] = None, db_name: Optional[str] = None):
    client = MongoClient(uri or config.MONGO_URI, serverSelectionTimeoutMS=3000)
    return client[db_name or config.MONGO_DB_NAME]


def _save(df: pd.DataFrame, name: str, verbose: bool = True) -> Path:
    out = config.TABLE_DIR / f"{name}.csv"
    df.to_csv(out, index=False)
    if verbose:
        print(f"  mongo {name:<30} -> {len(df):>4} rows")
    return out


def _save_mongo_json(pipeline: list, name: str) -> None:
    config.MONGO_DIR.mkdir(parents=True, exist_ok=True)
    out = config.MONGO_DIR / f"{name}.json"
    out.write_text(json.dumps(pipeline, indent=2, default=str), encoding="utf-8")


def run(verbose: bool = True) -> None:
    config.ensure_dirs()
    db = get_db()

    # -------------------------------------------------------------
    # 01 | Overall Headline KPIs
    # -------------------------------------------------------------
    p01 = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$group": {
            "_id": None,
            "impressions": {"$sum": "$impressions"},
            "clicks": {"$sum": "$clicks"},
            "orders": {"$sum": "$orders"},
            "spend": {"$sum": "$spend"},
            "attributed_revenue": {"$sum": "$attributed_revenue"},
            "advertisers": {"$addToSet": "$c.advertiser_id"}
        }},
        {"$project": {
            "_id": 0,
            "impressions": "$impressions",
            "clicks": "$clicks",
            "orders": "$orders",
            "ad_revenue_inr": {"$round": ["$spend", 0]},
            "attributed_gmv_inr": {"$round": ["$attributed_revenue", 0]},
            "ctr_pct": {"$round": [{"$multiply": [{"$divide": ["$clicks", "$impressions"]}, 100]}, 3]},
            "cpm_inr": {"$round": [{"$multiply": [{"$divide": ["$spend", "$impressions"]}, 1000]}, 1]},
            "click_to_order_pct": {"$round": [{"$multiply": [{"$divide": ["$orders", "$clicks"]}, 100]}, 2]},
            "roas": {"$round": [{"$divide": ["$attributed_revenue", "$spend"]}, 2]},
            "advertisers_with_spend": {"$size": "$advertisers"}
        }}
    ]
    _save_mongo_json(p01, "01_overall_kpis")
    df01 = pd.DataFrame(list(db.daily_performance.aggregate(p01)))
    _save(df01, "01_overall_kpis", verbose)

    # -------------------------------------------------------------
    # 02 | Monthly Trend & Pacing
    # -------------------------------------------------------------
    p02 = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$project": {
            "month": {"$substr": ["$date", 0, 7]},
            "impressions": 1,
            "clicks": 1,
            "orders": 1,
            "spend": 1,
            "attributed_revenue": 1,
            "advertiser_id": "$c.advertiser_id"
        }},
        {"$group": {
            "_id": "$month",
            "impressions": {"$sum": "$impressions"},
            "clicks": {"$sum": "$clicks"},
            "orders": {"$sum": "$orders"},
            "spend": {"$sum": "$spend"},
            "revenue": {"$sum": "$attributed_revenue"},
            "advertisers": {"$addToSet": "$advertiser_id"}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "_id": 0,
            "month": "$_id",
            "impressions": 1,
            "clicks": 1,
            "orders": 1,
            "ad_revenue_inr": {"$round": ["$spend", 0]},
            "ctr_pct": {"$round": [{"$multiply": [{"$divide": ["$clicks", "$impressions"]}, 100]}, 3]},
            "cpm_inr": {"$round": [{"$multiply": [{"$divide": ["$spend", "$impressions"]}, 1000]}, 1]},
            "roas": {"$round": [{"$divide": ["$revenue", "$spend"]}, 2]},
            "active_advertisers": {"$size": "$advertisers"},
            "_spend": "$spend",
            "_impr": "$impressions"
        }}
    ]
    _save_mongo_json(p02, "02_monthly_trend")
    df02 = pd.DataFrame(list(db.daily_performance.aggregate(p02)))
    df02["ad_revenue_mom_pct"] = (df02["_spend"].pct_change() * 100).round(1)
    df02["impressions_mom_pct"] = (df02["_impr"].pct_change() * 100).round(1)
    df02 = df02.drop(columns=["_spend", "_impr"])
    _save(df02, "02_monthly_trend", verbose)

    # -------------------------------------------------------------
    # 03 | Category Performance
    # -------------------------------------------------------------
    p03 = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$lookup": {"from": "advertisers", "localField": "c.advertiser_id", "foreignField": "advertiser_id", "as": "a"}},
        {"$unwind": "$a"},
        {"$group": {
            "_id": "$a.category",
            "advertisers": {"$addToSet": "$a.advertiser_id"},
            "spend": {"$sum": "$spend"},
            "impressions": {"$sum": "$impressions"},
            "clicks": {"$sum": "$clicks"},
            "orders": {"$sum": "$orders"},
            "attributed_revenue": {"$sum": "$attributed_revenue"}
        }},
        {"$project": {
            "_id": 0,
            "category": "$_id",
            "advertisers": {"$size": "$advertisers"},
            "ad_revenue_inr": {"$round": ["$spend", 0]},
            "spend_raw": "$spend",
            "ctr_pct": {"$round": [{"$multiply": [{"$divide": ["$clicks", "$impressions"]}, 100]}, 3]},
            "cpm_inr": {"$round": [{"$multiply": [{"$divide": ["$spend", "$impressions"]}, 1000]}, 1]},
            "cost_per_order_inr": {"$round": [{"$divide": ["$spend", "$orders"]}, 1]},
            "avg_order_value_inr": {"$round": [{"$divide": ["$attributed_revenue", "$orders"]}, 1]},
            "roas": {"$round": [{"$divide": ["$attributed_revenue", "$spend"]}, 2]}
        }},
        {"$sort": {"roas": -1}}
    ]
    _save_mongo_json(p03, "03_category_performance")
    df03 = pd.DataFrame(list(db.daily_performance.aggregate(p03)))
    total_spend = df03["spend_raw"].sum()
    df03["spend_share_pct"] = (100.0 * df03["spend_raw"] / total_spend).round(1)
    df03["roas_rank"] = df03["roas"].rank(ascending=False, method="min").astype(int)
    df03 = df03.drop(columns=["spend_raw"])[["category", "advertisers", "ad_revenue_inr", "spend_share_pct",
                                             "ctr_pct", "cpm_inr", "cost_per_order_inr", "avg_order_value_inr",
                                             "roas", "roas_rank"]]
    _save(df03, "03_category_performance", verbose)

    # -------------------------------------------------------------
    # 04 | Placement Performance
    # -------------------------------------------------------------
    p04 = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$group": {
            "_id": "$c.placement",
            "impressions": {"$sum": "$impressions"},
            "clicks": {"$sum": "$clicks"},
            "orders": {"$sum": "$orders"},
            "spend": {"$sum": "$spend"},
            "revenue": {"$sum": "$attributed_revenue"}
        }},
        {"$project": {
            "_id": 0,
            "placement": "$_id",
            "impressions": 1,
            "ad_revenue_inr": {"$round": ["$spend", 0]},
            "ctr_pct": {"$round": [{"$multiply": [{"$divide": ["$clicks", "$impressions"]}, 100]}, 3]},
            "cpm_inr": {"$round": [{"$multiply": [{"$divide": ["$spend", "$impressions"]}, 1000]}, 1]},
            "cost_per_click_inr": {"$round": [{"$divide": ["$spend", "$clicks"]}, 2]},
            "cost_per_order_inr": {"$round": [{"$divide": ["$spend", "$orders"]}, 1]},
            "click_to_order_pct": {"$round": [{"$multiply": [{"$divide": ["$orders", "$clicks"]}, 100]}, 2]},
            "roas": {"$round": [{"$divide": ["$revenue", "$spend"]}, 2]}
        }},
        {"$sort": {"roas": -1}}
    ]
    _save_mongo_json(p04, "04_placement_performance")
    df04 = pd.DataFrame(list(db.daily_performance.aggregate(p04)))
    _save(df04, "04_placement_performance", verbose)

    # -------------------------------------------------------------
    # 05 | Inventory Fill Rate & Capacity
    # -------------------------------------------------------------
    # Compute daily fill rates to calculate high_util_days (fill >= 85%)
    p05_daily = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$group": {
            "_id": {"date": "$date", "placement": "$c.placement"},
            "filled": {"$sum": "$impressions"}
        }},
        {"$lookup": {
            "from": "inventory",
            "let": {"d": "$_id.date", "p": "$_id.placement"},
            "pipeline": [
                {"$match": {"$expr": {"$and": [{"$eq": ["$date", "$$d"]}, {"$eq": ["$placement", "$$p"]}]}}}
            ],
            "as": "inv"
        }},
        {"$unwind": "$inv"},
        {"$project": {
            "_id": 0,
            "date": "$_id.date",
            "month": {"$substr": ["$_id.date", 0, 7]},
            "placement": "$_id.placement",
            "filled": 1,
            "capacity": "$inv.capacity_impressions",
            "is_high_util": {"$cond": [{"$gte": [{"$divide": ["$filled", "$inv.capacity_impressions"]}, 0.85]}, 1, 0]}
        }}
    ]
    daily_fill = pd.DataFrame(list(db.daily_performance.aggregate(p05_daily)))
    df05 = daily_fill.groupby(["month", "placement"]).agg(
        filled_impressions=("filled", "sum"),
        capacity_impressions=("capacity", "sum"),
        high_util_days=("is_high_util", "sum"),
        days_in_month=("date", "count")
    ).reset_index()
    df05["fill_rate_pct"] = (100.0 * df05["filled_impressions"] / df05["capacity_impressions"]).round(2)
    df05["high_util_day_pct"] = (100.0 * df05["high_util_days"] / df05["days_in_month"]).round(1)
    df05 = df05.sort_values(["month", "placement"])
    _save_mongo_json(p05_daily, "05_inventory_fill_rate")
    _save(df05, "05_inventory_fill_rate", verbose)

    # -------------------------------------------------------------
    # 06 | Advertiser Segments (Size x Tier)
    # -------------------------------------------------------------
    p06 = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$lookup": {"from": "advertisers", "localField": "c.advertiser_id", "foreignField": "advertiser_id", "as": "a"}},
        {"$unwind": "$a"},
        {"$group": {
            "_id": {"advertiser_size": "$a.advertiser_size", "city_tier": "$a.city_tier"},
            "advertisers": {"$addToSet": "$a.advertiser_id"},
            "spend": {"$sum": "$spend"},
            "impressions": {"$sum": "$impressions"},
            "clicks": {"$sum": "$clicks"},
            "orders": {"$sum": "$orders"},
            "revenue": {"$sum": "$attributed_revenue"}
        }},
        {"$project": {
            "_id": 0,
            "advertiser_size": "$_id.advertiser_size",
            "city_tier": "$_id.city_tier",
            "advertisers": {"$size": "$advertisers"},
            "ad_revenue_inr": {"$round": ["$spend", 0]},
            "ctr_pct": {"$round": [{"$multiply": [{"$divide": ["$clicks", "$impressions"]}, 100]}, 3]},
            "click_to_order_pct": {"$round": [{"$multiply": [{"$divide": ["$orders", "$clicks"]}, 100]}, 2]},
            "roas": {"$round": [{"$divide": ["$revenue", "$spend"]}, 2]}
        }},
        {"$sort": {"advertiser_size": 1, "city_tier": 1}}
    ]
    _save_mongo_json(p06, "06_advertiser_segments")
    df06 = pd.DataFrame(list(db.daily_performance.aggregate(p06)))
    _save(df06, "06_advertiser_segments", verbose)

    # -------------------------------------------------------------
    # 07 | Retention Cohorts
    # -------------------------------------------------------------
    p07 = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$project": {
            "advertiser_id": "$c.advertiser_id",
            "active_month": {"$substr": ["$date", 0, 7]}
        }},
        {"$group": {
            "_id": {"advertiser_id": "$advertiser_id", "active_month": "$active_month"}
        }}
    ]
    adv_months = pd.DataFrame(list(db.daily_performance.aggregate(p07)))
    adv_months["advertiser_id"] = adv_months["_id"].apply(lambda x: x["advertiser_id"])
    adv_months["active_month"] = adv_months["_id"].apply(lambda x: x["active_month"])

    first_month = adv_months.groupby("advertiser_id")["active_month"].min().reset_index()
    first_month.rename(columns={"active_month": "cohort_month"}, inplace=True)
    merged = adv_months.merge(first_month, on="advertiser_id")

    # Calculate month difference
    def diff_months(row):
        y1, m1 = int(row["cohort_month"][:4]), int(row["cohort_month"][5:7])
        y2, m2 = int(row["active_month"][:4]), int(row["active_month"][5:7])
        return (y2 - y1) * 12 + (m2 - m1)

    merged["months_since_start"] = merged.apply(diff_months, axis=1)

    cohort_sizes = first_month.groupby("cohort_month")["advertiser_id"].count().to_dict()
    df07 = merged.groupby(["cohort_month", "months_since_start"])["advertiser_id"].nunique().reset_index()
    df07.rename(columns={"advertiser_id": "active_advertisers"}, inplace=True)
    df07["cohort_size"] = df07["cohort_month"].map(cohort_sizes)
    df07["retention_pct"] = (100.0 * df07["active_advertisers"] / df07["cohort_size"]).round(1)
    df07 = df07.sort_values(["cohort_month", "months_since_start"])
    _save_mongo_json(p07, "07_retention_cohorts")
    _save(df07, "07_retention_cohorts", verbose)

    # -------------------------------------------------------------
    # 08 | Advertiser Ranking & Churn
    # -------------------------------------------------------------
    p08 = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$lookup": {"from": "advertisers", "localField": "c.advertiser_id", "foreignField": "advertiser_id", "as": "a"}},
        {"$unwind": "$a"},
        {"$group": {
            "_id": {
                "advertiser_id": "$a.advertiser_id",
                "advertiser_name": "$a.advertiser_name",
                "category": "$a.category",
                "city_tier": "$a.city_tier",
                "advertiser_size": "$a.advertiser_size",
                "churn_date": "$a.churn_date"
            },
            "spend": {"$sum": "$spend"},
            "revenue": {"$sum": "$attributed_revenue"}
        }},
        {"$project": {
            "_id": 0,
            "advertiser_id": "$_id.advertiser_id",
            "advertiser_name": "$_id.advertiser_name",
            "category": "$_id.category",
            "city_tier": "$_id.city_tier",
            "advertiser_size": "$_id.advertiser_size",
            "churned": {"$cond": [{"$ne": ["$_id.churn_date", None]}, 1, 0]},
            "ad_revenue_inr": {"$round": ["$spend", 0]},
            "roas": {"$round": [{"$divide": ["$revenue", "$spend"]}, 2]}
        }}
    ]
    df08 = pd.DataFrame(list(db.daily_performance.aggregate(p08)))
    df08["spend_rank"] = df08["ad_revenue_inr"].rank(ascending=False, method="min").astype(int)
    df08["roas_rank_in_category"] = df08.groupby("category")["roas"].rank(ascending=False, method="min").astype(int)
    df08["roas_quartile"] = pd.qcut(df08["roas"], q=4, labels=[4, 3, 2, 1]).astype(int)  # 1 is best
    df08 = df08.sort_values("spend_rank")
    _save_mongo_json(p08, "08_advertiser_ranking")
    _save(df08, "08_advertiser_ranking", verbose)

    # -------------------------------------------------------------
    # 09 | Segments to Grow or Fix
    # -------------------------------------------------------------
    p09 = [
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$lookup": {"from": "advertisers", "localField": "c.advertiser_id", "foreignField": "advertiser_id", "as": "a"}},
        {"$unwind": "$a"},
        {"$group": {
            "_id": {"category": "$a.category", "city_tier": "$a.city_tier"},
            "advertisers": {"$addToSet": "$a.advertiser_id"},
            "spend": {"$sum": "$spend"},
            "revenue": {"$sum": "$attributed_revenue"}
        }},
        {"$project": {
            "_id": 0,
            "category": "$_id.category",
            "city_tier": "$_id.city_tier",
            "advertisers": {"$size": "$advertisers"},
            "spend": {"$round": ["$spend", 0]},
            "attributed_revenue": {"$round": ["$revenue", 0]},
            "roas": {"$round": [{"$divide": ["$revenue", "$spend"]}, 2]}
        }}
    ]
    df09 = pd.DataFrame(list(db.daily_performance.aggregate(p09)))
    overall_roas = df01["roas"].iloc[0]
    df09["overall_roas"] = overall_roas
    df09["roas_vs_overall"] = (df09["roas"] / overall_roas).round(2)
    df09["action"] = np.where(
        df09["roas_vs_overall"] < config.FIX_THRESHOLD, "FIX",
        np.where(df09["roas_vs_overall"] > config.GROW_THRESHOLD, "GROW", "MAINTAIN")
    )
    df09 = df09[df09["advertisers"] >= 3].sort_values("roas")
    _save_mongo_json(p09, "09_segments_to_grow_or_fix")
    _save(df09, "09_segments_to_grow_or_fix", verbose)

    # -------------------------------------------------------------
    # 10 | Opportunity Sizing Inputs (Last 3 Months)
    # -------------------------------------------------------------
    # Find the maximum date in the dataset
    max_date = db.daily_performance.find_one(sort=[("date", -1)])["date"]
    min_date = (pd.to_datetime(max_date) - pd.DateOffset(days=90)).strftime("%Y-%m-%d")

    p10 = [
        {"$match": {"date": {"$gte": min_date}}},
        {"$lookup": {"from": "campaigns", "localField": "campaign_id", "foreignField": "campaign_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$group": {
            "_id": "$c.placement",
            "impressions": {"$sum": "$impressions"},
            "spend": {"$sum": "$spend"}
        }}
    ]
    perf_90 = pd.DataFrame(list(db.daily_performance.aggregate(p10)))
    perf_90.rename(columns={"_id": "placement"}, inplace=True)

    p10_inv = [
        {"$match": {"date": {"$gte": min_date}}},
        {"$group": {
            "_id": "$placement",
            "capacity": {"$sum": "$capacity_impressions"}
        }}
    ]
    inv_90 = pd.DataFrame(list(db.inventory.aggregate(p10_inv)))
    inv_90.rename(columns={"_id": "placement"}, inplace=True)

    df10 = perf_90.merge(inv_90, on="placement")
    df10.rename(columns={
        "impressions": "impressions_3m",
        "capacity": "capacity_3m"
    }, inplace=True)
    df10["fill_rate"] = (df10["impressions_3m"] / df10["capacity_3m"]).round(4)
    df10["cpm_inr"] = (1000.0 * df10["spend"] / df10["impressions_3m"]).round(2)
    df10["ad_revenue_3m_inr"] = df10["spend"].round(0)
    df10 = df10[["placement", "impressions_3m", "capacity_3m", "fill_rate", "cpm_inr", "ad_revenue_3m_inr"]].sort_values("placement")
    _save_mongo_json(p10, "10_opportunity_inputs")
    _save(df10, "10_opportunity_inputs", verbose)


def main() -> None:
    argparse.ArgumentParser(description="Run MongoDB analytical aggregation queries").parse_args()
    run()


if __name__ == "__main__":
    main()
