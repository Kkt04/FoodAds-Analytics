"""
A/B test readout: 'Bestseller badge' ad format on the Sponsored Carousel.

  control   = current ad format
  treatment = new format with a 'Bestseller' badge

Metrics
  primary    : CTR (clicks / exposed users)
  secondary  : orders per exposed user
  guardrail  : revenue per exposed user, click->order rate

Method: two-proportion z-test (pooled SE for the test, unpooled SE for the CI),
Welch t-test for revenue per user. Also reports power / required sample size.

Outputs: outputs/reports/ab_test_readout.md  and  outputs/tables/ab_test_summary.csv
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src import config

ALPHA = 0.05
POWER = 0.80
Z_ALPHA = stats.norm.ppf(1 - ALPHA / 2)


# ----------------------------------------------------------------------------- statistics
def two_prop_ztest(x1: int, n1: int, x2: int, n2: int) -> dict:
    """Compare conversion rates of group 1 (control) vs group 2 (treatment)."""
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se_pooled
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    se_unpooled = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    diff = p2 - p1
    return {
        "p_control": p1, "p_treatment": p2,
        "abs_diff": diff, "rel_lift": diff / p1 if p1 else float("nan"),
        "ci_low": diff - Z_ALPHA * se_unpooled, "ci_high": diff + Z_ALPHA * se_unpooled,
        "z": z, "p_value": p_value,
        "power": float(stats.norm.cdf(abs(diff) / se_unpooled - Z_ALPHA)) if se_unpooled else float("nan"),
    }


def sample_size_per_arm(p_baseline: float, mde_rel: float,
                        alpha: float = ALPHA, power: float = POWER) -> int:
    """Users needed per arm to detect a relative lift `mde_rel` on a baseline rate."""
    p2 = p_baseline * (1 + mde_rel)
    z_a, z_b = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    pbar = (p_baseline + p2) / 2
    n = ((z_a * math.sqrt(2 * pbar * (1 - pbar))
          + z_b * math.sqrt(p_baseline * (1 - p_baseline) + p2 * (1 - p2))) ** 2) / (p2 - p_baseline) ** 2
    return int(math.ceil(n))


def welch_ttest(a: np.ndarray, b: np.ndarray) -> dict:
    t, p = stats.ttest_ind(b, a, equal_var=False)
    diff = b.mean() - a.mean()
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return {"mean_control": a.mean(), "mean_treatment": b.mean(), "abs_diff": diff,
            "rel_lift": diff / a.mean() if a.mean() else float("nan"),
            "ci_low": diff - Z_ALPHA * se, "ci_high": diff + Z_ALPHA * se, "t": t, "p_value": p}


# ----------------------------------------------------------------------------- decision rule
def decide(primary: dict, guardrails: list[dict]) -> tuple[str, str]:
    """Simple, explicit decision framework (documented in the README)."""
    primary_win = primary["p_value"] < ALPHA and primary["abs_diff"] > 0
    guard_harm = any(g["p_value"] < ALPHA and g["abs_diff"] < 0 for g in guardrails)
    guard_unclear = any(g["p_value"] >= ALPHA and g["abs_diff"] < 0 for g in guardrails)
    if primary_win and guard_harm:
        return "HOLD", "Primary metric improved but a guardrail got significantly worse."
    if primary_win and guard_unclear:
        return ("RAMP CAUTIOUSLY",
                "Primary metric improved significantly; guardrail moves are negative-but-not-significant. "
                "Ramp to a larger traffic share and keep monitoring downstream metrics.")
    if primary_win:
        return "SHIP", "Primary metric improved significantly and no guardrail deteriorated."
    return "DO NOT SHIP", "No statistically significant improvement in the primary metric."


# ----------------------------------------------------------------------------- run
def _pct(x: float, d: int = 2) -> str:
    return f"{100 * x:.{d}f}%"


def run(db_path: Path | None = None, verbose: bool = True) -> dict:
    db_path = Path(db_path) if db_path else config.DB_PATH
    with sqlite3.connect(db_path) as con:
        df = pd.read_sql_query("SELECT * FROM ab_test_users", con)

    ctl, trt = df[df.variant == "control"], df[df.variant == "treatment"]
    n1, n2 = len(ctl), len(trt)

    ctr = two_prop_ztest(ctl.clicked.sum(), n1, trt.clicked.sum(), n2)
    opu = two_prop_ztest(ctl.ordered.sum(), n1, trt.ordered.sum(), n2)           # orders per user
    c2o = two_prop_ztest(ctl.ordered.sum(), ctl.clicked.sum(), trt.ordered.sum(), trt.clicked.sum())
    rpu = welch_ttest(ctl.order_value.to_numpy(float), trt.order_value.to_numpy(float))

    verdict, reason = decide(ctr, [opu, c2o, rpu])

    # How many users would we need to confirm the *order* effect?
    need_orders = sample_size_per_arm(opu["p_control"], 0.10)
    need_ctr = sample_size_per_arm(ctr["p_control"], 0.10)

    summary = pd.DataFrame([
        {"metric": "CTR (primary)", "role": "primary", "control": ctr["p_control"], "treatment": ctr["p_treatment"],
         "abs_diff": ctr["abs_diff"], "rel_lift": ctr["rel_lift"], "ci_low": ctr["ci_low"], "ci_high": ctr["ci_high"],
         "p_value": ctr["p_value"], "significant": ctr["p_value"] < ALPHA},
        {"metric": "Orders per exposed user", "role": "secondary", "control": opu["p_control"], "treatment": opu["p_treatment"],
         "abs_diff": opu["abs_diff"], "rel_lift": opu["rel_lift"], "ci_low": opu["ci_low"], "ci_high": opu["ci_high"],
         "p_value": opu["p_value"], "significant": opu["p_value"] < ALPHA},
        {"metric": "Click-to-order rate", "role": "guardrail", "control": c2o["p_control"], "treatment": c2o["p_treatment"],
         "abs_diff": c2o["abs_diff"], "rel_lift": c2o["rel_lift"], "ci_low": c2o["ci_low"], "ci_high": c2o["ci_high"],
         "p_value": c2o["p_value"], "significant": c2o["p_value"] < ALPHA},
        {"metric": "Revenue per exposed user (INR)", "role": "guardrail", "control": rpu["mean_control"], "treatment": rpu["mean_treatment"],
         "abs_diff": rpu["abs_diff"], "rel_lift": rpu["rel_lift"], "ci_low": rpu["ci_low"], "ci_high": rpu["ci_high"],
         "p_value": rpu["p_value"], "significant": rpu["p_value"] < ALPHA},
    ])
    config.TABLE_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(config.TABLE_DIR / "ab_test_summary.csv", index=False)

    def row(label, r, money=False):
        fmt = (lambda v: f"{v:.3f}") if money else _pct
        return (f"| {label} | {fmt(r['p_control'] if 'p_control' in r else r['mean_control'])} "
                f"| {fmt(r['p_treatment'] if 'p_treatment' in r else r['mean_treatment'])} "
                f"| {r['rel_lift'] * 100:+.1f}% "
                f"| [{(r['ci_low'] * (1 if money else 100)):+.3f}{'' if money else ' pp'}, "
                f"{(r['ci_high'] * (1 if money else 100)):+.3f}{'' if money else ' pp'}] "
                f"| {r['p_value']:.4f} | {'Yes' if r['p_value'] < ALPHA else 'No'} |")

    # ---- narrative is generated from the numbers, never hard-coded ----
    def sig(r):
        return r["p_value"] < ALPHA

    bullets = [
        f"- The badge changes CTR by **{ctr['rel_lift'] * 100:+.1f}%** relative ({ctr['abs_diff'] * 100:+.2f} pp), "
        f"{'statistically significant' if sig(ctr) else 'NOT statistically significant'} (p = {ctr['p_value']:.4f})."
    ]
    if sig(c2o) and c2o["abs_diff"] < 0:
        bullets.append(f"- Click-to-order rate is **significantly lower** ({c2o['rel_lift'] * 100:+.1f}%, p = {c2o['p_value']:.3f}): the extra clicks are lower-intent.")
    elif c2o["abs_diff"] < 0:
        bullets.append(f"- Click-to-order rate is slightly lower ({c2o['rel_lift'] * 100:+.1f}%) but not significantly (p = {c2o['p_value']:.3f}); keep watching it.")
    else:
        bullets.append(f"- Click-to-order rate did not drop ({c2o['rel_lift'] * 100:+.1f}%, p = {c2o['p_value']:.3f}), so the extra clicks are not obviously lower quality.")
    if sig(opu):
        bullets.append(f"- Orders per exposed user changed significantly ({opu['rel_lift'] * 100:+.1f}%, p = {opu['p_value']:.4f}).")
    else:
        bullets.append(f"- Orders per exposed user moved {opu['rel_lift'] * 100:+.1f}% but not significantly (p = {opu['p_value']:.4f}), "
                       f"so the test cannot yet prove that extra clicks become extra sales. Confirming a +10% order lift would need about "
                       f"**{need_orders:,} users per arm** (we have {min(n1, n2):,}); detecting +10% on CTR needs only about {need_ctr:,}.")
    bullets.append("- Advertisers pay per impression (CPM), so platform ad revenue is unaffected by CTR; advertisers care about ROAS, which depends on orders.")
    bullets = "\n".join(bullets)

    recommendation = {
        "SHIP": "Roll the badge out, but keep monitoring orders per user and advertiser ROAS for the badge cohort after launch.",
        "RAMP CAUTIOUSLY": "Ramp to a larger traffic share (for example 25%) and extend the test until the order-level metrics are conclusive.",
        "HOLD": "Do not roll out. Investigate why the guardrail metric deteriorated before running a follow-up test.",
        "DO NOT SHIP": "Do not roll out on this evidence. Consider a bigger change in the creative or a longer test.",
    }[verdict]

    md = f"""# A/B Test Readout: "Bestseller badge" ad format (Sponsored Carousel)

> Data is **simulated**. The method is real; the numbers are not from any real platform.

**Hypothesis:** adding a "Bestseller" badge to the Sponsored Carousel ad will increase click-through rate
without hurting downstream conversion.

**Design:** randomised split, {n1:,} control users vs {n2:,} treatment users, alpha = {ALPHA}, two-sided tests.

| Metric | Control | Treatment | Relative lift | 95% CI of difference | p-value | Significant? |
|---|---|---|---|---|---|---|
{row('**CTR (primary)**', ctr)}
{row('Orders per exposed user', opu)}
{row('Click-to-order rate (guardrail)', c2o)}
{row('Revenue per exposed user, INR (guardrail)', rpu, money=True)}

*CI units: percentage points (pp) for rates, INR for revenue per user.*

## Decision: **{verdict}**

{reason}

## What this means
{bullets}

## Recommendation
{recommendation}

## Method notes
- Rates: two-proportion z-test (pooled standard error for the test, unpooled for the confidence interval).
- Revenue per user: Welch's t-test (does not assume equal variance).
- Decision rule: SHIP if primary wins and no guardrail worsens; RAMP CAUTIOUSLY if primary wins and guardrails are negative but not significant;
  HOLD if a guardrail is significantly worse; DO NOT SHIP otherwise.
- Limitation: several metrics are tested, so a stricter analysis would apply a multiple-comparison correction (e.g. Bonferroni).
"""
    (config.REPORT_DIR / "ab_test_readout.md").write_text(md, encoding="utf-8")
    (config.REPORT_DIR / "ab_test_result.json").write_text(
        json.dumps({"verdict": verdict, "ctr_rel_lift": ctr["rel_lift"], "ctr_p_value": ctr["p_value"],
                    "n_control": n1, "n_treatment": n2}, indent=2), encoding="utf-8")
    if verbose:
        print(f"  verdict: {verdict}  (CTR lift {ctr['rel_lift'] * 100:+.1f}%, p={ctr['p_value']:.4f})")
    return {"verdict": verdict, "summary": summary}


def main() -> None:
    ap = argparse.ArgumentParser(description="A/B test readout")
    ap.add_argument("--db", type=Path, default=config.DB_PATH)
    a = ap.parse_args()
    print("Analysing A/B test ...")
    run(a.db)


if __name__ == "__main__":
    main()
