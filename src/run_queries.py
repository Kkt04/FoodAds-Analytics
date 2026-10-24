"""Run every .sql file in /sql against the SQLite DB and export each result as a CSV.

The CSVs in outputs/tables/ can be uploaded directly to Google Sheets / Looker Studio.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from src import config


def run(db_path: Path | None = None, sql_dir: Path | None = None,
        out_dir: Path | None = None, verbose: bool = True) -> dict[str, pd.DataFrame]:
    db_path = Path(db_path) if db_path else config.DB_PATH
    sql_dir = Path(sql_dir) if sql_dir else config.SQL_DIR
    out_dir = Path(out_dir) if out_dir else config.TABLE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, pd.DataFrame] = {}
    with sqlite3.connect(db_path) as con:
        for sql_file in sorted(sql_dir.glob("*.sql")):
            df = pd.read_sql_query(sql_file.read_text(), con)
            df.to_csv(out_dir / f"{sql_file.stem}.csv", index=False)
            results[sql_file.stem] = df
            if verbose:
                print(f"  {sql_file.name:<34} -> {len(df):>4} rows")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Run all SQL analyses")
    ap.add_argument("--db", type=Path, default=config.DB_PATH)
    a = ap.parse_args()
    print("Running SQL analyses ...")
    run(a.db)


if __name__ == "__main__":
    main()
