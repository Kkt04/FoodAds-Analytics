"""
Opportunity sizing: "How much extra ad revenue could we earn by selling more of our unsold inventory?"

Approach (transparent, assumption-driven - the way it is done before building anything):
  extra impressions = capacity x (new fill rate - current fill rate)
  marginal CPM      = current CPM x (1 + marginal discount)   (the extra, harder-to-sell inventory is usually sold cheaper)
  extra revenue     = extra impressions x marginal CPM / 1000 (platform ad revenue = advertiser spend)

Three scenarios (conservative / base / optimistic) with different fill uplift and price dilution.
Fill rate is capped at MAX_FILL because 100% sell-through is unrealistic.

Output: outputs/tables/opportunity_sizing.csv and outputs/reports/opportunity_sizing.md
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from src import config

MAX_FILL = 0.92
SCENARIOS = {
    #  name           fill uplift (pp), discount on the extra (marginal) impressions
    "Conservative": dict(uplift=0.03, cpm_change=-0.40),
    "Base":         dict(uplift=0.06, cpm_change=-0.25),
    "Optimistic":   dict(uplift=0.10, cpm_change=-0.10),
}


def size(inputs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, sc in SCENARIOS.items():
        for r in inputs.itertuples():
            new_fill = max(r.fill_rate, min(r.fill_rate + sc["uplift"], MAX_FILL))
            new_impr = r.capacity_3m * new_fill
            extra_impr = new_impr - r.impressions_3m
            marginal_cpm = r.cpm_inr * (1 + sc["cpm_change"])
            base_rev = r.impressions_3m * r.cpm_inr / 1000.0
            new_rev = base_rev + extra_impr * marginal_cpm / 1000.0
            rows.append({
                "scenario": name, "placement": r.placement,
                "current_fill_pct": 100 * r.fill_rate, "new_fill_pct": 100 * new_fill,
                "extra_impressions_3m": extra_impr,
                "current_cpm": r.cpm_inr, "marginal_cpm": marginal_cpm,
                "baseline_revenue_3m": base_rev, "new_revenue_3m": new_rev,
                "incremental_revenue_3m": new_rev - base_rev,
            })
    df = pd.DataFrame(rows)
    df["incremental_revenue_annualised"] = df["incremental_revenue_3m"] * 4
    return df


def run(db_path: Path | None = None, verbose: bool = True) -> pd.DataFrame:
    db_path = Path(db_path) if db_path else config.DB_PATH
    sql = (config.SQL_DIR / "10_opportunity_inputs.sql").read_text()
    with sqlite3.connect(db_path) as con:
        inputs = pd.read_sql_query(sql, con)

    df = size(inputs)
    config.TABLE_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    df.round(2).to_csv(config.TABLE_DIR / "opportunity_sizing.csv", index=False)

    total = df.groupby("scenario", sort=False).agg(
        incremental_3m=("incremental_revenue_3m", "sum"),
        annualised=("incremental_revenue_annualised", "sum"),
        baseline_3m=("baseline_revenue_3m", "sum"))
    total["uplift_pct"] = 100 * total["incremental_3m"] / total["baseline_3m"]

    lines = ["# Opportunity Sizing: selling more unsold ad inventory", "",
             "> Based on **simulated** data. Figures in INR (1 crore = 10,000,000).", "",
             "**Question:** if we raise the fill rate of our ad placements, how much extra ad revenue can we expect?", "",
             "## Assumptions", ""]
    for n, sc in SCENARIOS.items():
        lines.append(f"- **{n}:** fill rate +{sc['uplift'] * 100:.0f} pp (capped at {MAX_FILL * 100:.0f}%), "
                     f"the extra impressions sell at a {abs(sc['cpm_change']) * 100:.0f}% lower CPM than today's average")
    lines += ["", "## Result (last 3 months as baseline)", "",
              "| Scenario | Incremental ad revenue, 3 months | Annualised | Uplift vs baseline |", "|---|---|---|---|"]
    for n, r in total.iterrows():
        lines.append(f"| {n} | INR {r.incremental_3m / 1e7:.2f} cr | INR {r.annualised / 1e7:.2f} cr | {r.uplift_pct:+.1f}% |")

    base = df[df.scenario == "Base"].sort_values("incremental_revenue_3m", ascending=False)
    lines += ["", "## Where the opportunity sits (Base scenario)", "",
              "| Placement | Fill now | Fill after | Incremental revenue, 3 months |", "|---|---|---|---|"]
    for r in base.itertuples():
        lines.append(f"| {r.placement} | {r.current_fill_pct:.1f}% | {r.new_fill_pct:.1f}% | INR {r.incremental_revenue_3m / 1e7:.2f} cr |")
    lines += ["", "## Caveats", "",
              "- Fill uplift and marginal-price discount are assumptions, not measurements. Validate them with a pricing / supply experiment.",
              "- More impressions only help if demand exists: advertisers must be willing to buy the extra volume at the new CPM.",
              "- Low-performing placements (low ROAS) may not sustain higher prices; check advertiser ROAS before pushing volume.",
              "- Sensitivity: change `SCENARIOS` at the top of `src/opportunity_sizing.py` and re-run."]
    (config.REPORT_DIR / "opportunity_sizing.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if verbose:
        for n, r in total.iterrows():
            print(f"  {n:<13} +INR {r.incremental_3m / 1e7:.2f} cr per quarter ({r.uplift_pct:+.1f}%)")
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description="Opportunity sizing")
    ap.add_argument("--db", type=Path, default=config.DB_PATH)
    a = ap.parse_args()
    print("Sizing the inventory opportunity ...")
    run(a.db)


if __name__ == "__main__":
    main()
