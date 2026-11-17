"""Load raw CSV data from data/ into MongoDB collections with schema typing and indexes."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd
import pymongo
from pymongo import MongoClient

from src import config

COLLECTIONS = ["advertisers", "campaigns", "daily_performance", "inventory", "ab_test_users"]


def get_client(uri: Optional[str] = None) -> MongoClient:
    return MongoClient(uri or config.MONGO_URI, serverSelectionTimeoutMS=3000)


def load(
    data_dir: Optional[Path] = None,
    uri: Optional[str] = None,
    db_name: Optional[str] = None,
    verbose: bool = True
) -> MongoClient:
    d = data_dir or config.DATA_DIR
    target_db_name = db_name or config.MONGO_DB_NAME
    client = get_client(uri)
    db = client[target_db_name]

    if verbose:
        print(f"Connecting to MongoDB at {uri or config.MONGO_URI} (db: {target_db_name})")

    for col in COLLECTIONS:
        csv_path = d / f"{col}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing CSV: {csv_path}")

        df = pd.read_csv(csv_path)

        # Cast column types cleanly
        if col == "daily_performance":
            df["impressions"] = df["impressions"].astype(int)
            df["clicks"] = df["clicks"].astype(int)
            df["orders"] = df["orders"].astype(int)
            df["spend"] = df["spend"].astype(float)
            df["attributed_revenue"] = df["attributed_revenue"].astype(float)
        elif col == "inventory":
            df["capacity_impressions"] = df["capacity_impressions"].astype(int)
        elif col == "ab_test_users":
            df["clicked"] = df["clicked"].astype(int)
            df["ordered"] = df["ordered"].astype(int)
            df["order_value"] = df["order_value"].astype(float)
        elif col == "advertisers":
            df = df.where(pd.notnull(df), None)

        collection = db[col]
        collection.drop()

        records = df.to_dict(orient="records")
        if records:
            # Insert in chunks of 25,000 to maintain high throughput
            chunk_size = 25000
            for i in range(0, len(records), chunk_size):
                collection.insert_many(records[i:i + chunk_size])

        if verbose:
            print(f"  loaded mongo {col:<20} {len(records):>7,} documents")

    # Create Indexes
    db.advertisers.create_index("advertiser_id", unique=True)
    db.advertisers.create_index([("category", 1), ("city_tier", 1)])
    db.campaigns.create_index("campaign_id", unique=True)
    db.campaigns.create_index("advertiser_id")
    db.campaigns.create_index("placement")
    db.daily_performance.create_index([("campaign_id", 1), ("date", 1)])
    db.daily_performance.create_index("date")
    db.inventory.create_index([("date", 1), ("placement", 1)])
    db.ab_test_users.create_index("variant")

    if verbose:
        print("  created MongoDB compound indexes")

    return client


def main() -> None:
    argparse.ArgumentParser(description="Load CSVs into MongoDB").parse_args()
    load()


if __name__ == "__main__":
    main()
