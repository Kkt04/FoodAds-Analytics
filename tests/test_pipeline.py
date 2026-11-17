"""Tests: data integrity, KPI formulas, and the A/B statistics.  Run:  pytest -q"""
from pathlib import Path
import sqlite3

import pandas as pd
import pytest

from src import ab_test, build_dashboard, generate_data, load_db


@pytest.fixture(scope="module")
def small_db(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    generate_data.generate(out_dir=d, seed=7, n_advertisers=40, ab_users_per_arm=2000, verbose=False)
    db = d / "test.db"
    load_db.load(data_dir=d, db_path=db, verbose=False)
    return db


def q(db, sql):
    with sqlite3.connect(db) as con:
        return pd.read_sql_query(sql, con)


# ---------------------------------------------------------------- data integrity
def test_tables_not_empty(small_db):
    for t in ["advertisers", "campaigns", "daily_performance", "inventory", "ab_test_users"]:
        assert q(small_db, f"SELECT COUNT(*) n FROM {t}").n[0] > 0


def test_no_orphan_campaigns(small_db):
    n = q(small_db, """SELECT COUNT(*) n FROM daily_performance dp
                       LEFT JOIN campaigns c USING (campaign_id) WHERE c.campaign_id IS NULL""").n[0]
    assert n == 0


def test_funnel_is_monotonic(small_db):
    bad = q(small_db, "SELECT COUNT(*) n FROM daily_performance WHERE clicks > impressions OR orders > clicks").n[0]
    assert bad == 0


def test_no_negative_values(small_db):
    bad = q(small_db, """SELECT COUNT(*) n FROM daily_performance
                         WHERE impressions < 0 OR clicks < 0 OR orders < 0 OR spend < 0 OR attributed_revenue < 0""").n[0]
    assert bad == 0


def test_fill_rate_never_exceeds_100_percent(small_db):
    sql = open("sql/05_inventory_fill_rate.sql").read()
    assert q(small_db, sql).fill_rate_pct.max() <= 100.0


def test_data_is_reproducible(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    ta = generate_data.generate(a, seed=3, n_advertisers=20, ab_users_per_arm=500, verbose=False)
    tb = generate_data.generate(b, seed=3, n_advertisers=20, ab_users_per_arm=500, verbose=False)
    pd.testing.assert_frame_equal(ta["daily_performance"], tb["daily_performance"])


# ---------------------------------------------------------------- KPI formulas
def test_sql_kpis_match_pandas(small_db):
    sql = open("sql/01_overall_kpis.sql").read()
    k = q(small_db, sql).iloc[0]
    p = q(small_db, "SELECT * FROM daily_performance")
    assert k.ctr_pct == pytest.approx(round(100 * p.clicks.sum() / p.impressions.sum(), 3))
    assert k.cpm_inr == pytest.approx(round(1000 * p.spend.sum() / p.impressions.sum(), 1))
    assert k.roas == pytest.approx(round(p.attributed_revenue.sum() / p.spend.sum(), 2))


def test_category_spend_shares_sum_to_100(small_db):
    sql = open("sql/03_category_performance.sql").read()
    assert q(small_db, sql).spend_share_pct.sum() == pytest.approx(100, abs=0.6)


def test_retention_starts_at_100_percent(small_db):
    sql = open("sql/07_retention_cohorts.sql").read()
    r = q(small_db, sql)
    assert (r[r.months_since_start == 0].retention_pct == 100.0).all()


# ---------------------------------------------------------------- statistics
def test_two_prop_ztest_known_values():
    r = ab_test.two_prop_ztest(100, 1000, 130, 1000)
    assert r["z"] == pytest.approx(2.103, abs=0.01)
    assert r["p_value"] < 0.05
    assert r["ci_low"] < r["abs_diff"] < r["ci_high"]


def test_no_difference_is_not_significant():
    r = ab_test.two_prop_ztest(100, 1000, 100, 1000)
    assert r["z"] == 0 and r["p_value"] == pytest.approx(1.0)


def test_sample_size_grows_when_effect_shrinks():
    assert ab_test.sample_size_per_arm(0.03, 0.05) > ab_test.sample_size_per_arm(0.03, 0.20)


def test_decision_rule():
    win = {"p_value": 0.01, "abs_diff": 0.01}
    flat = {"p_value": 0.5, "abs_diff": 0.0}
    bad = {"p_value": 0.01, "abs_diff": -0.01}
    assert ab_test.decide(win, [flat])[0] == "SHIP"
    assert ab_test.decide(win, [bad])[0] == "HOLD"
    assert ab_test.decide(flat, [flat])[0] == "DO NOT SHIP"


def test_dashboard_builds():
    out = build_dashboard.run(verbose=False)
    p = Path(out)
    assert p.exists()
    assert p.stat().st_size > 50000
    content = p.read_text(encoding="utf-8")
    assert "FoodAds Intelligence Console" in content
    assert "app-data" in content

