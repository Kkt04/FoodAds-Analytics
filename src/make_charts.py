"""Create the dashboard charts (PNG) from the CSVs in outputs/tables/."""
from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import config

COLORS = {"main": "#FC8019", "dark": "#2B2B2B", "good": "#2E9E6B", "bad": "#D64545", "grey": "#9AA0A6", "blue": "#3B6FD4"}
plt.rcParams.update({
    "figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 12, "axes.titleweight": "bold", "font.size": 9,
})
NOTE = "Simulated data"


def _save(fig, name: str) -> None:
    fig.text(0.995, 0.005, NOTE, ha="right", va="bottom", fontsize=7, color=COLORS["grey"])
    fig.tight_layout()
    fig.savefig(config.CHART_DIR / f"{name}.png")
    plt.close(fig)


def _t(name: str) -> pd.DataFrame:
    return pd.read_csv(config.TABLE_DIR / f"{name}.csv")


def monthly_trend() -> None:
    d = _t("02_monthly_trend")
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.bar(d["month"], d["ad_revenue_inr"] / 1e7, color=COLORS["main"], label="Ad revenue (INR crore)")
    ax.set_ylabel("Ad revenue (INR crore)")
    ax.tick_params(axis="x", rotation=45)
    ax2 = ax.twinx()
    ax2.plot(d["month"], d["roas"], color=COLORS["dark"], marker="o", label="ROAS")
    ax2.set_ylabel("ROAS (x)")
    ax2.set_ylim(0, max(5, d["roas"].max() * 1.3))
    ax2.spines["right"].set_visible(True)
    ax.set_title("Ad revenue grows, ROAS stays flat")
    _save(fig, "01_monthly_trend")


def category_roas() -> None:
    d = _t("03_category_performance").sort_values("roas")
    overall = _t("01_overall_kpis")["roas"].iloc[0]
    colors = [COLORS["bad"] if r < 0.7 * overall else COLORS["good"] if r > 1.2 * overall else COLORS["grey"] for r in d["roas"]]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(d["category"], d["roas"], color=colors)
    ax.axvline(overall, color=COLORS["dark"], ls="--", lw=1)
    ax.text(overall, len(d) - 0.35, f" overall {overall:.2f}x", fontsize=8, va="bottom")
    for y, (r, s) in enumerate(zip(d["roas"], d["spend_share_pct"])):
        ax.text(r + 0.05, y, f"{r:.2f}x  ({s:.0f}% of spend)", va="center", fontsize=8)
    ax.set_xlim(0, d["roas"].max() * 1.45)
    ax.set_ylim(-0.6, len(d) + 0.2)
    ax.set_xlabel("ROAS (attributed revenue / ad spend)")
    ax.set_title("ROAS by category (red = fix, green = grow)")
    _save(fig, "02_category_roas")


def placement_roas_vs_fill() -> None:
    p = _t("04_placement_performance")
    f = _t("05_inventory_fill_rate")
    last = f[f["month"] == f["month"].max()][["placement", "fill_rate_pct"]]
    d = p.merge(last, on="placement").sort_values("roas", ascending=False)
    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.bar(x - 0.2, d["roas"], 0.4, color=COLORS["main"], label="ROAS (x)")
    ax.set_ylabel("ROAS (x)")
    ax.set_xticks(x)
    ax.set_xticklabels(d["placement"], rotation=15)
    ax2 = ax.twinx()
    ax2.bar(x + 0.2, d["fill_rate_pct"], 0.4, color=COLORS["blue"], label=f"Fill rate % ({f['month'].max()})")
    ax2.set_ylabel("Fill rate (%)")
    ax2.set_ylim(0, 110)
    ax2.spines["right"].set_visible(True)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8, frameon=False)
    ax.set_title("Placements: advertiser return vs how much we sell")
    _save(fig, "03_placement_roas_fill")


def fill_rate_trend() -> None:
    f = _t("05_inventory_fill_rate")
    piv = f.pivot(index="month", columns="placement", values="fill_rate_pct")
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for c in piv.columns:
        ax.plot(piv.index, piv[c], marker="o", ms=3, label=c)
    ax.set_ylabel("Fill rate (%)")
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="lower right")
    ax.set_title("Fill rate by placement (ramp-up, then plateau)")
    _save(fig, "04_fill_rate_trend")


def retention_heatmap() -> None:
    r = _t("07_retention_cohorts")
    piv = r.pivot(index="cohort_month", columns="months_since_start", values="retention_pct")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    im = ax.imshow(piv.values, cmap="YlOrBr", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels(piv.columns)
    ax.set_yticks(range(piv.shape[0]))
    ax.set_yticklabels(piv.index)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                        color="white" if v > 65 else COLORS["dark"])
    ax.set_xlabel("Months since first spend")
    ax.set_ylabel("Cohort (first active month)")
    ax.set_title("Advertiser retention (% still spending)")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.spines[:].set_visible(False)
    _save(fig, "05_retention_heatmap")


def segment_heatmap() -> None:
    s = _t("09_segments_to_grow_or_fix")
    piv = s.pivot(index="category", columns="city_tier", values="roas")[["Metro", "Tier-1", "Tier-2"]]
    piv = piv.loc[piv.mean(axis=1).sort_values().index]
    fig, ax = plt.subplots(figsize=(6, 4.4))
    im = ax.imshow(piv.values, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(3))
    ax.set_xticklabels(piv.columns)
    ax.set_yticks(range(len(piv)))
    ax.set_yticklabels(piv.index)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.1f}x", ha="center", va="center", fontsize=8)
    ax.set_title("ROAS by category x city tier")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.spines[:].set_visible(False)
    _save(fig, "06_segment_heatmap")


def ab_test() -> None:
    d = _t("ab_test_summary")
    row = d[d["role"] == "primary"].iloc[0]
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    vals = [row["control"] * 100, row["treatment"] * 100]
    ax.bar(["Control", "Treatment\n(Bestseller badge)"], vals, color=[COLORS["grey"], COLORS["main"]], width=0.55)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.05, f"{v:.2f}%", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylabel("CTR (%)")
    ax.set_ylim(0, max(vals) * 1.35)
    sig = "significant" if row["significant"] else "not significant"
    ax.set_title(f"A/B test: CTR {row['rel_lift'] * 100:+.1f}% (p={row['p_value']:.4f}, {sig})")
    _save(fig, "07_ab_test_ctr")


def run(verbose: bool = True) -> None:
    config.CHART_DIR.mkdir(parents=True, exist_ok=True)
    for fn in (monthly_trend, category_roas, placement_roas_vs_fill, fill_rate_trend,
               retention_heatmap, segment_heatmap, ab_test):
        fn()
        if verbose:
            print(f"  chart: {fn.__name__}")


def main() -> None:
    argparse.ArgumentParser(description="Build charts from outputs/tables").parse_args()
    run()


if __name__ == "__main__":
    main()
