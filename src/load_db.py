"""Load the generated CSVs into a local SQLite database (data/foodads.db)."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from src import config

SCHEMA = """
DROP TABLE IF EXISTS advertisers;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS daily_performance;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS ab_test_users;

CREATE TABLE advertisers (
    advertiser_id    TEXT PRIMARY KEY,
    advertiser_name  TEXT NOT NULL,
    category         TEXT NOT NULL,
    city_tier        TEXT NOT NULL,
    advertiser_size  TEXT NOT NULL,
    signup_date      TEXT NOT NULL,
    churn_date       TEXT NOT NULL DEFAULT ''
);
CREATE TABLE campaigns (
    campaign_id    TEXT PRIMARY KEY,
    advertiser_id  TEXT NOT NULL REFERENCES advertisers(advertiser_id),
    placement      TEXT NOT NULL,
    start_date     TEXT NOT NULL,
    end_date       TEXT NOT NULL
);
CREATE TABLE daily_performance (
    date                TEXT NOT NULL,
    campaign_id         TEXT NOT NULL REFERENCES campaigns(campaign_id),
    impressions         INTEGER NOT NULL,
    clicks              INTEGER NOT NULL,
    orders              INTEGER NOT NULL,
    spend               REAL NOT NULL,
    attributed_revenue  REAL NOT NULL,
    PRIMARY KEY (date, campaign_id)
);
CREATE TABLE inventory (
    date                  TEXT NOT NULL,
    placement             TEXT NOT NULL,
    capacity_impressions  INTEGER NOT NULL,
    PRIMARY KEY (date, placement)
);
CREATE TABLE ab_test_users (
    user_id      TEXT PRIMARY KEY,
    variant      TEXT NOT NULL,
    clicked      INTEGER NOT NULL,
    ordered      INTEGER NOT NULL,
    order_value  INTEGER NOT NULL
);
CREATE INDEX idx_perf_campaign ON daily_performance(campaign_id);
CREATE INDEX idx_perf_date     ON daily_performance(date);
CREATE INDEX idx_camp_adv      ON campaigns(advertiser_id);
"""

TABLES = ["advertisers", "campaigns", "daily_performance", "inventory", "ab_test_users"]


def load(data_dir: Path | None = None, db_path: Path | None = None, verbose: bool = True) -> Path:
    data_dir = Path(data_dir) if data_dir else config.DATA_DIR
    db_path = Path(db_path) if db_path else config.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as con:
        con.executescript(SCHEMA)
        for t in TABLES:
            csv = data_dir / f"{t}.csv"
            if not csv.exists():
                raise FileNotFoundError(f"{csv} not found - run `python -m src.generate_data` first")
            df = pd.read_csv(csv, keep_default_na=False)
            df.to_sql(t, con, if_exists="append", index=False)
            if verbose:
                print(f"  loaded {t:<20} {len(df):>9,} rows")
    return db_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Load CSVs into SQLite")
    ap.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    ap.add_argument("--db", type=Path, default=config.DB_PATH)
    a = ap.parse_args()
    print(f"Loading CSVs from {a.data_dir} into {a.db} ...")
    load(a.data_dir, a.db)


if __name__ == "__main__":
    main()
