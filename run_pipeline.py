"""One command to run everything:  python run_pipeline.py

generate data -> load SQLite -> run SQL -> A/B test -> opportunity sizing -> charts -> HTML dashboard
"""
from __future__ import annotations

import argparse
import time

from src import ab_test, build_dashboard, config, generate_data, load_db, make_charts, opportunity_sizing, run_queries


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the full FoodAds analytics pipeline")
    ap.add_argument("--seed", type=int, default=config.DEFAULT_SEED, help="random seed (same seed = same data)")
    ap.add_argument("--advertisers", type=int, default=config.DEFAULT_ADVERTISERS, help="number of advertisers to simulate")
    ap.add_argument("--regenerate", action="store_true",
                    help="create a fresh dataset even if CSVs already exist in data/ (numbers may differ slightly by NumPy version)")
    a = ap.parse_args()

    t0 = time.time()
    config.ensure_dirs()

    have_data = all((config.DATA_DIR / f"{t}.csv").exists() for t in load_db.TABLES)
    if have_data and not a.regenerate:
        print("[1/7] Using existing CSVs in data/ (pass --regenerate to create new data)")
    else:
        print(f"[1/7] Generating SIMULATED data (seed={a.seed}, advertisers={a.advertisers})")
        generate_data.generate(seed=a.seed, n_advertisers=a.advertisers)
    print("[2/7] Loading data into SQLite")
    load_db.load()
    print("[3/7] Running SQL analyses")
    run_queries.run()
    print("[4/7] A/B test readout")
    ab_test.run()
    print("[5/7] Opportunity sizing")
    opportunity_sizing.run()
    print("[6/7] Building charts")
    make_charts.run()
    print("[7/7] Building dashboard")
    build_dashboard.run()

    print(f"\nDone in {time.time() - t0:.1f}s")
    print(f"  Dashboard : {config.OUT_DIR / 'dashboard.html'}")
    print(f"  Tables    : {config.TABLE_DIR}")
    print(f"  Reports   : {config.REPORT_DIR}")


if __name__ == "__main__":
    main()
