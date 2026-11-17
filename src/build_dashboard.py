"""Build an executive-grade, interactive HTML dashboard (outputs/dashboard.html).

Crafted with a human-designed enterprise analytics UI (Stripe/Datadog inspired),
complete with interactive tabs, live scenario calculator, real-time segment search/sort,
advertiser risk inspector, publication-quality chart embeds, in-dashboard Executive Memo
and Documentation modal dialog boxes, and powered by MongoDB.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src import config

CHARTS = [
    ("01_monthly_trend", "Monthly P&L: Ad Revenue & ROAS Trajectory", "Revenue scaled 5.6x while ROAS held steady at ~3.54x across 12 months."),
    ("02_category_roas", "Category ROAS Distribution & Benchmark", "Biryani (5.64x) and North Indian (5.01x) lead; Beverages (1.09x) destroys merchant ROI."),
    ("06_segment_heatmap", "ROAS Matrix: Category x City Tier", "Granular performance across 30 segments highlights low-AOV vulnerability in Tier-2."),
    ("03_placement_roas_fill", "Placement Efficiency: ROAS vs Inventory Fill", "Cart Page yields 5.80x ROAS with 24% unsold capacity; Home Banner underperforms at 1.30x."),
    ("04_fill_rate_trend", "Placement Fill Rate Pacing (12 Months)", "Search Top hits 90% capacity ceiling; Home Banner stagnates in the low 60s."),
    ("05_retention_heatmap", "Advertiser Cohort Retention (% Active)", "Steep retention cliff after Month 3 for SMB advertisers; Enterprise chains show 97% stability."),
    ("07_ab_test_ctr", "A/B Experiment Readout: Bestseller Badge", "Treatment unlocked +18.2% relative CTR lift (p=0.0001) without compromising downstream CVR."),
]


def _img_base64(name: str) -> str:
    path = config.CHART_DIR / f"{name}.png"
    if not path.exists():
        return ""
    data = path.read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode()


def _clean_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Clean DataFrame so all NaNs, Infs are replaced with None (valid JSON null)."""
    df_clean = df.replace({np.nan: None, np.inf: None, -np.inf: None})
    records = df_clean.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if pd.isna(v) or v is None:
                r[k] = None
    return records


def run(verbose: bool = True) -> str:
    # 1. Load data tables
    raw_kpis = pd.read_csv(config.TABLE_DIR / "01_overall_kpis.csv").iloc[0].to_dict()
    kpis = {k: (None if pd.isna(v) else v) for k, v in raw_kpis.items()}

    monthly = _clean_records(pd.read_csv(config.TABLE_DIR / "02_monthly_trend.csv"))
    category = _clean_records(pd.read_csv(config.TABLE_DIR / "03_category_performance.csv"))
    placement = _clean_records(pd.read_csv(config.TABLE_DIR / "04_placement_performance.csv"))
    fill = _clean_records(pd.read_csv(config.TABLE_DIR / "05_inventory_fill_rate.csv"))
    segments = _clean_records(pd.read_csv(config.TABLE_DIR / "06_advertiser_segments.csv"))
    cohorts = _clean_records(pd.read_csv(config.TABLE_DIR / "07_retention_cohorts.csv"))
    ranking = _clean_records(pd.read_csv(config.TABLE_DIR / "08_advertiser_ranking.csv"))[:100]
    seg_actions = _clean_records(pd.read_csv(config.TABLE_DIR / "09_segments_to_grow_or_fix.csv"))
    opp_inputs = _clean_records(pd.read_csv(config.TABLE_DIR / "10_opportunity_inputs.csv"))
    ab_summary = _clean_records(pd.read_csv(config.TABLE_DIR / "ab_test_summary.csv"))
    opp_sizing = _clean_records(pd.read_csv(config.TABLE_DIR / "opportunity_sizing.csv"))
    ab_meta = json.loads((config.REPORT_DIR / "ab_test_result.json").read_text())

    # Pre-render chart images map
    chart_imgs = {name: _img_base64(name) for name, _, _ in CHARTS}

    # Consolidated JSON payload for client-side interactivity
    app_data = {
        "kpis": kpis,
        "monthly": monthly,
        "category": category,
        "placement": placement,
        "fill": fill,
        "segments": segments,
        "cohorts": cohorts,
        "ranking": ranking,
        "seg_actions": seg_actions,
        "opp_inputs": opp_inputs,
        "ab_summary": ab_summary,
        "opp_sizing": opp_sizing,
        "ab_meta": ab_meta,
    }
    json_payload = json.dumps(app_data, default=str)

    # Derived headline figures
    rev_cr = kpis["ad_revenue_inr"] / 1e7
    gmv_cr = kpis["attributed_gmv_inr"] / 1e7
    impr_b = kpis["impressions"] / 1e9
    opp_df = pd.DataFrame(opp_sizing)
    base_opp_lakhs = (opp_df[opp_df["scenario"] == "Base"]["incremental_revenue_3m"].sum()) / 1e5
    base_opp_cr = base_opp_lakhs / 100

    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FoodAds Intelligence Console | Marketplace Economics & Experimentation (MongoDB)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

      /* Light Theme */
      --bg-canvas: #f8fafc;
      --bg-surface: #ffffff;
      --bg-surface-elevated: #ffffff;
      --bg-subtle: #f1f5f9;
      --bg-hover: #e2e8f0;
      --border-subtle: #e2e8f0;
      --border-strong: #cbd5e1;
      --text-primary: #0f172a;
      --text-secondary: #475569;
      --text-muted: #64748b;
      --brand-primary: #ea580c;
      --brand-glow: rgba(234, 88, 12, 0.12);
      --accent-blue: #2563eb;
      --status-success: #15803d;
      --status-success-bg: #f0fdf4;
      --status-success-border: #bbf7d0;
      --status-danger: #b91c1c;
      --status-danger-bg: #fef2f2;
      --status-danger-border: #fecaca;
      --status-warn: #b45309;
      --status-warn-bg: #fffbeb;
      --status-warn-border: #fef3c7;
      --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.05);
      --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.04);
    }}

    [data-theme="dark"] {{
      --bg-canvas: #090d16;
      --bg-surface: #111827;
      --bg-surface-elevated: #162032;
      --bg-subtle: #1c283d;
      --bg-hover: #24334f;
      --border-subtle: #1f2d44;
      --border-strong: #2e4366;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --brand-primary: #f97316;
      --brand-glow: rgba(249, 115, 22, 0.18);
      --accent-blue: #3b82f6;
      --status-success: #22c55e;
      --status-success-bg: rgba(34, 197, 94, 0.12);
      --status-success-border: rgba(34, 197, 94, 0.3);
      --status-danger: #ef4444;
      --status-danger-bg: rgba(239, 68, 68, 0.12);
      --status-danger-border: rgba(239, 68, 68, 0.3);
      --status-warn: #f59e0b;
      --status-warn-bg: rgba(245, 158, 11, 0.12);
      --status-warn-border: rgba(245, 158, 11, 0.3);
      --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.2);
      --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5), 0 4px 6px -4px rgb(0 0 0 / 0.3);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: var(--font-sans);
      background-color: var(--bg-canvas);
      color: var(--text-primary);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      transition: background-color 0.25s ease, color 0.25s ease;
    }}

    /* Top Utility Bar */
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border-subtle);
      backdrop-filter: blur(12px);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}

    .brand-block {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .brand-logo {{
      width: 36px;
      height: 36px;
      border-radius: 9px;
      background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 800;
      font-size: 17px;
      box-shadow: 0 2px 8px var(--brand-glow);
    }}

    .brand-titles {{
      display: flex;
      flex-direction: column;
    }}

    .brand-title {{
      font-size: 15px;
      font-weight: 700;
      letter-spacing: -0.01em;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .brand-subtitle {{
      font-size: 12px;
      color: var(--text-muted);
      font-weight: 500;
    }}

    .pill-badge {{
      font-size: 11px;
      padding: 2px 7px;
      border-radius: 9999px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .pill-neutral {{
      background: var(--bg-subtle);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
    }}

    .pill-success {{
      background: var(--status-success-bg);
      color: var(--status-success);
      border: 1px solid var(--status-success-border);
    }}

    .pill-mongo {{
      background: rgba(16, 185, 129, 0.15);
      color: #10b981;
      border: 1px solid rgba(16, 185, 129, 0.3);
      font-family: var(--font-mono);
    }}

    .top-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 600;
      padding: 7px 13px;
      border-radius: 7px;
      cursor: pointer;
      border: 1px solid var(--border-subtle);
      background: var(--bg-surface);
      color: var(--text-primary);
      transition: all 0.15s ease;
      text-decoration: none;
    }}

    .btn:hover {{
      background: var(--bg-subtle);
      border-color: var(--border-strong);
    }}

    .btn-primary {{
      background: var(--brand-primary);
      border-color: var(--brand-primary);
      color: #fff;
    }}

    .btn-primary:hover {{
      background: #c2410c;
      border-color: #c2410c;
    }}

    .theme-toggle {{
      background: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: 7px;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--text-secondary);
    }}

    .theme-toggle:hover {{
      color: var(--text-primary);
      border-color: var(--border-strong);
    }}

    /* Main Container */
    .app-shell {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 20px 24px 60px;
    }}

    /* Strategic Alert Banner */
    .context-banner {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-left: 4px solid var(--brand-primary);
      border-radius: 8px;
      padding: 12px 18px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}

    .context-banner-text {{
      font-size: 13px;
      color: var(--text-secondary);
    }}

    .context-banner-text strong {{
      color: var(--text-primary);
    }}

    /* Tabs Navigation */
    .tab-nav {{
      display: flex;
      gap: 4px;
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: 24px;
      overflow-x: auto;
      padding-bottom: 1px;
    }}

    .tab-btn {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 16px;
      font-family: var(--font-sans);
      font-size: 13.5px;
      font-weight: 600;
      color: var(--text-secondary);
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    }}

    .tab-btn:hover {{
      color: var(--text-primary);
      background: var(--bg-subtle);
      border-top-left-radius: 6px;
      border-top-right-radius: 6px;
    }}

    .tab-btn.active {{
      color: var(--brand-primary);
      border-bottom-color: var(--brand-primary);
      background: var(--bg-subtle);
      border-top-left-radius: 6px;
      border-top-right-radius: 6px;
    }}

    /* KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }}

    .kpi-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 16px 18px;
      box-shadow: var(--shadow-sm);
      position: relative;
      overflow: hidden;
      transition: transform 0.15s ease, border-color 0.15s ease;
    }}

    .kpi-card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-strong);
    }}

    .kpi-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }}

    .kpi-label {{
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .kpi-val {{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--text-primary);
      font-variant-numeric: tabular-nums;
      margin-bottom: 4px;
    }}

    .kpi-footer {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--text-muted);
    }}

    .badge-delta {{
      font-weight: 600;
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 4px;
    }}

    .badge-pos {{
      background: var(--status-success-bg);
      color: var(--status-success);
    }}

    .badge-neg {{
      background: var(--status-danger-bg);
      color: var(--status-danger);
    }}

    /* Cards & Layout */
    .grid-2col {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}

    .grid-halves {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}

    @media (max-width: 960px) {{
      .grid-2col, .grid-halves {{
        grid-template-columns: 1fr;
      }}
    }}

    .panel-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--shadow-sm);
      margin-bottom: 20px;
    }}

    .panel-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 10px;
    }}

    .panel-title {{
      font-size: 15px;
      font-weight: 700;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .panel-subtitle {{
      font-size: 12.5px;
      color: var(--text-muted);
      margin-top: 2px;
    }}

    .chart-container {{
      position: relative;
      width: 100%;
      border-radius: 8px;
      overflow: hidden;
      background: #0f172a;
      border: 1px solid var(--border-subtle);
      cursor: zoom-in;
    }}

    .chart-container img {{
      display: block;
      width: 100%;
      height: auto;
      object-fit: contain;
    }}

    .chart-caption {{
      padding: 10px 14px;
      font-size: 12px;
      color: var(--text-secondary);
      background: var(--bg-subtle);
      border-top: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    /* Tables */
    .table-wrapper {{
      overflow-x: auto;
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
    }}

    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;
    }}

    table.data-table th {{
      background: var(--bg-subtle);
      color: var(--text-secondary);
      font-weight: 600;
      padding: 10px 14px;
      border-bottom: 1px solid var(--border-subtle);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }}

    table.data-table th:hover {{
      color: var(--text-primary);
    }}

    table.data-table td {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-primary);
      font-variant-numeric: tabular-nums;
    }}

    table.data-table tr:last-child td {{
      border-bottom: none;
    }}

    table.data-table tr:hover td {{
      background: var(--bg-subtle);
    }}

    /* Action Badges */
    .action-badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 5px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.04em;
    }}

    .action-FIX {{
      background: var(--status-danger-bg);
      color: var(--status-danger);
      border: 1px solid var(--status-danger-border);
    }}

    .action-GROW {{
      background: var(--status-success-bg);
      color: var(--status-success);
      border: 1px solid var(--status-success-border);
    }}

    .action-MAINTAIN {{
      background: var(--status-warn-bg);
      color: var(--status-warn);
      border: 1px solid var(--status-warn-border);
    }}

    /* Interactive Simulator */
    .sim-box {{
      background: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 18px;
      margin-bottom: 20px;
    }}

    .sim-controls {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 18px;
      margin-bottom: 18px;
    }}

    .sim-group {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .sim-label {{
      font-size: 12.5px;
      font-weight: 600;
      color: var(--text-secondary);
      display: flex;
      justify-content: space-between;
    }}

    .sim-slider {{
      -webkit-appearance: none;
      width: 100%;
      height: 6px;
      border-radius: 3px;
      background: var(--border-strong);
      outline: none;
    }}

    .sim-slider::-webkit-slider-thumb {{
      -webkit-appearance: none;
      appearance: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: var(--brand-primary);
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }}

    .sim-results {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 16px;
    }}

    /* Filter Controls */
    .filter-bar {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }}

    .input-search {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 7px 12px;
      font-size: 13px;
      color: var(--text-primary);
      outline: none;
      min-width: 200px;
    }}

    .input-search:focus {{
      border-color: var(--brand-primary);
    }}

    .select-filter {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 7px 10px;
      font-size: 13px;
      color: var(--text-primary);
      outline: none;
      cursor: pointer;
    }}

    /* Insights Callout Box */
    .insight-card {{
      background: var(--bg-subtle);
      border-left: 3px solid var(--accent-blue);
      border-radius: 6px;
      padding: 14px 16px;
      margin-bottom: 16px;
      font-size: 13px;
    }}

    .insight-card h4 {{
      font-size: 13.5px;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 4px;
    }}

    .insight-card p {{
      color: var(--text-secondary);
      line-height: 1.5;
    }}

    /* Generic Modal Box */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.75);
      z-index: 1000;
      justify-content: center;
      align-items: center;
      padding: 20px;
      backdrop-filter: blur(4px);
    }}

    .modal-overlay.open {{
      display: flex;
    }}

    .modal-box {{
      width: 100%;
      max-width: 860px;
      max-height: 85vh;
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      border-radius: 12px;
      box-shadow: var(--shadow-lg);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      animation: modalFadeIn 0.2s ease-out;
    }}

    @keyframes modalFadeIn {{
      from {{ transform: scale(0.97); opacity: 0; }}
      to {{ transform: scale(1); opacity: 1; }}
    }}

    .modal-box-header {{
      padding: 16px 22px;
      border-bottom: 1px solid var(--border-subtle);
      background: var(--bg-surface-elevated);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .modal-box-title {{
      font-size: 16px;
      font-weight: 700;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .modal-box-close {{
      background: transparent;
      border: none;
      font-size: 22px;
      color: var(--text-muted);
      cursor: pointer;
      line-height: 1;
      padding: 4px 8px;
      border-radius: 6px;
    }}

    .modal-box-close:hover {{
      background: var(--bg-subtle);
      color: var(--text-primary);
    }}

    .modal-box-body {{
      padding: 24px;
      overflow-y: auto;
      font-size: 13.5px;
      line-height: 1.65;
      color: var(--text-primary);
    }}

    .modal-box-body h2 {{
      font-size: 17px;
      margin: 20px 0 10px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-primary);
    }}

    .modal-box-body h3 {{
      font-size: 15px;
      margin: 16px 0 8px;
      color: var(--text-primary);
    }}

    .modal-box-body p {{
      margin-bottom: 12px;
      color: var(--text-secondary);
    }}

    .modal-box-body ul, .modal-box-body ol {{
      margin-left: 20px;
      margin-bottom: 14px;
      color: var(--text-secondary);
    }}

    .modal-box-body li {{
      margin-bottom: 6px;
    }}

    .modal-box-body table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 13px;
    }}

    .modal-box-body th, .modal-box-body td {{
      padding: 8px 12px;
      border: 1px solid var(--border-subtle);
      text-align: left;
    }}

    .modal-box-body th {{
      background: var(--bg-subtle);
      font-weight: 600;
    }}

    .modal-box-body blockquote {{
      border-left: 4px solid var(--brand-primary);
      background: var(--bg-subtle);
      padding: 10px 16px;
      border-radius: 4px;
      margin: 14px 0;
      color: var(--text-primary);
    }}

    /* Image zoom modal */
    .image-modal-content {{
      max-width: 95vw;
      max-height: 90vh;
      background: var(--bg-surface);
      border-radius: 12px;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
    }}

    .image-modal-content img {{
      max-width: 100%;
      max-height: 80vh;
      object-fit: contain;
    }}

    /* Dedicated Documentation Section */
    .docs-section {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 24px;
      margin-top: 40px;
    }}

    .docs-section h2 {{
      font-size: 18px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    footer {{
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid var(--border-subtle);
      color: var(--text-muted);
      font-size: 12.5px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
  </style>
</head>
<body>

  <!-- Top App Bar -->
  <header class="topbar">
    <div class="brand-block">
      <div class="brand-logo">FA</div>
      <div class="brand-titles">
        <div class="brand-title">
          FoodAds Intelligence Console
          <span class="pill-badge pill-neutral">Production Analytics</span>
        </div>
        <div class="brand-subtitle">Simulated Food-Delivery Ads Marketplace · Jul 2025 - Jun 2026</div>
      </div>
    </div>

    <div class="top-actions">
      <span class="pill-badge pill-success">Active (foodads)</span>
      <button class="theme-toggle" id="themeToggleBtn" title="Toggle Light/Dark Theme">
        <svg id="themeIcon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5"></circle>
          <line x1="12" y1="1" x2="12" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="23"></line>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
          <line x1="1" y1="12" x2="3" y2="12"></line>
          <line x1="21" y1="12" x2="23" y2="12"></line>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
      </button>
      <button class="btn" onclick="openMemoModal()">Executive Memo</button>
      <button class="btn btn-primary" onclick="openDocsModal()">Documentation</button>
    </div>
  </header>

  <!-- Shell Container -->
  <main class="app-shell">

    <!-- Strategic Context Banner -->
    <div class="context-banner">
      <div class="context-banner-text">
        <strong>Marketplace Note:</strong> This intelligence console analyzes a synthetic 3-sided food delivery ad platform backed by <strong>MongoDB Aggregation Pipelines</strong>.
        Ad revenue reached <strong>INR {rev_cr:.1f} Cr</strong> driven by a 5.6x expansion in advertisers and traffic, while merchant ROAS remained pegged at <strong>{kpis['roas']:.2f}x</strong>.
      </div>
      <div>
        <span class="pill-badge pill-neutral">Seed 42 · 300 Merchants</span>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <nav class="tab-nav">
      <button class="tab-btn active" data-tab="tab-overview" onclick="switchTab('tab-overview', this)">Executive P&amp;L</button>
      <button class="tab-btn" data-tab="tab-inventory" onclick="switchTab('tab-inventory', this)">Inventory &amp; Yield</button>
      <button class="tab-btn" data-tab="tab-segments" onclick="switchTab('tab-segments', this)">Category &amp; Segments</button>
      <button class="tab-btn" data-tab="tab-retention" onclick="switchTab('tab-retention', this)">Retention &amp; Churn</button>
      <button class="tab-btn" data-tab="tab-abtest" onclick="switchTab('tab-abtest', this)">A/B Experiments</button>
      <button class="tab-btn" data-tab="tab-simulator" onclick="switchTab('tab-simulator', this)">Opportunity Simulator</button>
    </nav>

    <!-- TAB 1: EXECUTIVE OVERVIEW -->
    <section id="tab-overview" class="tab-pane">
      <!-- KPI Scorecards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Ad Revenue</span>
            <span class="badge-delta badge-pos">+472% YoY</span>
          </div>
          <div class="kpi-val">₹{rev_cr:.1f} Cr</div>
          <div class="kpi-footer">Total platform advertiser spend</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Attributed GMV</span>
            <span class="badge-delta badge-pos">3.54x Ratio</span>
          </div>
          <div class="kpi-val">₹{gmv_cr:.1f} Cr</div>
          <div class="kpi-footer">Order value generated for merchants</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Total Impressions</span>
            <span class="badge-delta badge-pos">1.02 Billion</span>
          </div>
          <div class="kpi-val">{impr_b:.2f} B</div>
          <div class="kpi-footer">Average CPM: ₹{kpis['cpm_inr']:.0f}</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Overall ROAS</span>
            <span class="badge-delta badge-pos">Flat</span>
          </div>
          <div class="kpi-val">{kpis['roas']:.2f}x</div>
          <div class="kpi-footer">Benchmark healthy: &gt; 3.0x</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Active Merchants</span>
            <span class="badge-delta badge-pos">300 Tracked</span>
          </div>
          <div class="kpi-val">{int(kpis['advertisers_with_spend'])}</div>
          <div class="kpi-footer">272 active in peak month (Jun)</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-header">
            <span class="kpi-label">Unsold Upside (Qtr)</span>
            <span class="badge-delta badge-pos">Base Case</span>
          </div>
          <div class="kpi-val">+₹{base_opp_lakhs:.1f} L</div>
          <div class="kpi-footer">+4.4% quarterly top-line boost</div>
        </div>
      </div>

      <!-- Overview Charts Grid -->
      <div class="grid-2col">
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Monthly Monetization Pacing &amp; ROAS Trend</div>
              <div class="panel-subtitle">Volume-driven scale: revenue grew from ₹1.1 Cr (Jul 2025) to ₹6.3 Cr (Jun 2026)</div>
            </div>
            <span class="pill-badge pill-neutral">Click chart to expand</span>
          </div>
          <div class="chart-container" onclick="openChartModal('01_monthly_trend', 'Monthly Ad Revenue &amp; ROAS')">
            <img src="{chart_imgs['01_monthly_trend']}" alt="Monthly Trend">
            <div class="chart-caption">
              <span><b>Finding:</b> Revenue scaled 5.6x due to merchant and traffic growth; ROAS remained constant (~3.54x).</span>
              <span>Zoom</span>
            </div>
          </div>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Strategic Insights &amp; Red Flags</div>
              <div class="panel-subtitle">Immediate leadership priorities</div>
            </div>
          </div>

          <div class="insight-card" style="border-left-color: #ef4444;">
            <h4>The Low-AOV Beverage/Dessert Trap</h4>
            <p>Beverages (1.09x ROAS) and Desserts (1.64x ROAS) consume <strong>23% of total ad spend</strong>. Because basket sizes are low (₹140-190), fixed click costs wipe out restaurant contribution margins.</p>
          </div>

          <div class="insight-card" style="border-left-color: #10b981;">
            <h4>Cart Page: Premium Monetization Lever</h4>
            <p>Cart Page delivers the marketplace's highest return (<strong>5.80x ROAS</strong>) with a 22% conversion rate, yet remains <strong>24% unsold</strong>. A prime upsell target for high-AOV cuisine partners.</p>
          </div>

          <div class="insight-card" style="border-left-color: #3b82f6;">
            <h4>Search Top Hits Capacity Ceiling</h4>
            <p>Search Top is <strong>90% filled</strong> across all days. Additional volume cannot be sold without degrading user search experience. The revenue growth lever here is <em>floor price optimization</em>, not volume.</p>
          </div>
        </div>
      </div>

      <!-- Monthly Trend Table -->
      <div class="panel-card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Monthly Ads P&amp;L Breakdown</div>
            <div class="panel-subtitle">Granular financial pacing across the 12-month operating window</div>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Impressions</th>
                <th>Clicks</th>
                <th>CTR %</th>
                <th>CPM (₹)</th>
                <th>Ad Revenue (₹ Cr)</th>
                <th>MoM Growth</th>
                <th>ROAS</th>
                <th>Active Merchants</th>
              </tr>
            </thead>
            <tbody>
              {"".join([f'''<tr>
                <td><strong>{m['month']}</strong></td>
                <td>{m['impressions']/1e6:,.1f} M</td>
                <td>{m['clicks']:,.0f}</td>
                <td>{m['ctr_pct']:.2f}%</td>
                <td>₹{m['cpm_inr']:.1f}</td>
                <td>₹{m['ad_revenue_inr']/1e7:.2f} Cr</td>
                <td><span class="badge-delta {'badge-pos' if m.get('ad_revenue_mom_pct') is not None and m['ad_revenue_mom_pct'] > 0 else ''}">{f"+{m['ad_revenue_mom_pct']:.1f}%" if m.get('ad_revenue_mom_pct') is not None else '—'}</span></td>
                <td><strong>{m['roas']:.2f}x</strong></td>
                <td>{m['active_advertisers']}</td>
              </tr>''' for m in monthly])}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 2: INVENTORY & YIELD -->
    <section id="tab-inventory" class="tab-pane" style="display:none;">
      <div class="grid-halves">
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Placement ROAS vs Fill Rate</div>
              <div class="panel-subtitle">Advertiser return plotted against current inventory sell-through</div>
            </div>
          </div>
          <div class="chart-container" onclick="openChartModal('03_placement_roas_fill', 'ROAS vs Fill Rate')">
            <img src="{chart_imgs['03_placement_roas_fill']}" alt="ROAS vs Fill">
            <div class="chart-caption">
              <span><b>Opportunity:</b> Cart Page delivers 5.8x ROAS with 24% capacity unmonetized.</span>
              <span>Zoom</span>
            </div>
          </div>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Placement Fill Rate Trend (12 Months)</div>
              <div class="panel-subtitle">Evolution of inventory fill across placements</div>
            </div>
          </div>
          <div class="chart-container" onclick="openChartModal('04_fill_rate_trend', 'Fill Rate Trend')">
            <img src="{chart_imgs['04_fill_rate_trend']}" alt="Fill Rate Trend">
            <div class="chart-caption">
              <span><b>Trend:</b> Steady ramp across H1 followed by plateauing fill in H2.</span>
              <span>Zoom</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Placement Economics Table -->
      <div class="panel-card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Placement Unit Economics &amp; Yield Matrix</div>
            <div class="panel-subtitle">Cross-placement comparison of cost, conversion, and return metrics</div>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Placement</th>
                <th>Impressions</th>
                <th>Ad Spend (₹ Cr)</th>
                <th>CTR %</th>
                <th>CPM (₹)</th>
                <th>Cost / Click (₹)</th>
                <th>Cost / Order (₹)</th>
                <th>Click-to-Order %</th>
                <th>ROAS</th>
                <th>Yield Assessment</th>
              </tr>
            </thead>
            <tbody>
              {"".join([f'''<tr>
                <td><strong>{p['placement']}</strong></td>
                <td>{p['impressions']/1e6:,.1f} M</td>
                <td>₹{p['ad_revenue_inr']/1e7:.2f} Cr</td>
                <td>{p['ctr_pct']:.2f}%</td>
                <td>₹{p['cpm_inr']:.1f}</td>
                <td>₹{p['cost_per_click_inr']:.2f}</td>
                <td>₹{p['cost_per_order_inr']:.1f}</td>
                <td>{p['click_to_order_pct']:.2f}%</td>
                <td><strong>{p['roas']:.2f}x</strong></td>
                <td><span class="action-badge {'action-GROW' if p['roas'] > 4 else ('action-FIX' if p['roas'] < 2 else 'action-MAINTAIN')}">{'High Yield' if p['roas'] > 4 else ('Underperforming' if p['roas'] < 2 else 'Balanced')}</span></td>
              </tr>''' for p in placement])}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 3: CATEGORY & SEGMENTS -->
    <section id="tab-segments" class="tab-pane" style="display:none;">
      <div class="grid-halves">
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Category ROAS vs Spend Share</div>
              <div class="panel-subtitle">Green: &gt;1.2x average ROAS | Red: &lt;0.7x average ROAS</div>
            </div>
          </div>
          <div class="chart-container" onclick="openChartModal('02_category_roas', 'Category ROAS')">
            <img src="{chart_imgs['02_category_roas']}" alt="Category ROAS">
            <div class="chart-caption">
              <span><b>Contrast:</b> Biryani (5.64x) vs Beverages (1.09x) highlights the AOV divide.</span>
              <span>Zoom</span>
            </div>
          </div>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Category x City Tier ROAS Heatmap</div>
              <div class="panel-subtitle">Cross-dimensional ROAS distribution</div>
            </div>
          </div>
          <div class="chart-container" onclick="openChartModal('06_segment_heatmap', 'Segment Heatmap')">
            <img src="{chart_imgs['06_segment_heatmap']}" alt="Segment Heatmap">
            <div class="chart-caption">
              <span><b>Geography:</b> Tier-2 cities exhibit severe ROAS degradation for low-order-value cuisines.</span>
              <span>Zoom</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Interactive Segments Explorer -->
      <div class="panel-card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Interactive Segment Action Matrix (Category x City Tier)</div>
            <div class="panel-subtitle">Actionable segmentation: FIX (&lt;0.7x overall), GROW (&gt;1.2x overall), MAINTAIN</div>
          </div>
        </div>

        <!-- Filter Controls -->
        <div class="filter-bar">
          <input type="text" id="segSearch" class="input-search" placeholder="Search category or tier..." onkeyup="filterSegments()">
          <select id="segActionFilter" class="select-filter" onchange="filterSegments()">
            <option value="ALL">All Actions (30 segments)</option>
            <option value="FIX">Action: FIX only</option>
            <option value="GROW">Action: GROW only</option>
            <option value="MAINTAIN">Action: MAINTAIN only</option>
          </select>
          <select id="segTierFilter" class="select-filter" onchange="filterSegments()">
            <option value="ALL">All City Tiers</option>
            <option value="Metro">Metro</option>
            <option value="Tier-1">Tier-1</option>
            <option value="Tier-2">Tier-2</option>
          </select>
        </div>

        <div class="table-wrapper">
          <table class="data-table" id="segmentsTable">
            <thead>
              <tr onclick="sortSegmentsTable(event)">
                <th data-col="category">Category ↕</th>
                <th data-col="city_tier">City Tier ↕</th>
                <th data-col="advertisers">Merchants ↕</th>
                <th data-col="spend">Ad Spend (₹ L) ↕</th>
                <th data-col="roas">ROAS ↕</th>
                <th data-col="roas_vs_overall">vs Marketplace ↕</th>
                <th data-col="action">Strategic Action ↕</th>
              </tr>
            </thead>
            <tbody id="segmentsBody">
              <!-- Dynamically populated by JS -->
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 4: RETENTION & CHURN -->
    <section id="tab-retention" class="tab-pane" style="display:none;">
      <div class="grid-2col">
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Advertiser Cohort Retention Heatmap</div>
              <div class="panel-subtitle">% of merchants continuing to invest in ad spend by tenure month</div>
            </div>
          </div>
          <div class="chart-container" onclick="openChartModal('05_retention_heatmap', 'Retention Heatmap')">
            <img src="{chart_imgs['05_retention_heatmap']}" alt="Retention Heatmap">
            <div class="chart-caption">
              <span><b>Finding:</b> Retention is ~95% at Month 3, dropping to ~86% by Month 6.</span>
              <span>Zoom</span>
            </div>
          </div>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Churn Vulnerability by Merchant Tier</div>
              <div class="panel-subtitle">SMB vs Enterprise Chain retention dynamics</div>
            </div>
          </div>

          <div class="insight-card" style="border-left-color: #ef4444;">
            <h4>SMB Merchants Experience 10x Churn Risk</h4>
            <p><strong>31% of SMB advertisers churned</strong> during the period, compared to only <strong>14% of Mid-tier</strong> and <strong>3% of Enterprise Chains</strong>. SMB budgets are fragile to initial week performance volatility.</p>
          </div>

          <div class="insight-card" style="border-left-color: #f59e0b;">
            <h4>The Month-3 Retention Cliff</h4>
            <p>Advertiser churn accelerates between Month 3 and Month 6. Onboarding support must proactively audit bids and creative before the Day-90 mark to prevent silent budget depletion.</p>
          </div>

          <div class="insight-card" style="border-left-color: #10b981;">
            <h4>Strategic Recommendation: Automated Floor Shields</h4>
            <p>Implement algorithmic bid adjustments for first-time SMB campaigns to guarantee minimum ROAS thresholds and prevent early flight abandonment.</p>
          </div>
        </div>
      </div>

      <!-- Segment Size Summary -->
      <div class="panel-card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Advertiser Segment Performance (Merchant Size x City Tier)</div>
            <div class="panel-subtitle">Volume and efficiency breakdown by merchant scale</div>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Merchant Size</th>
                <th>City Tier</th>
                <th>Merchants</th>
                <th>Ad Spend (₹ Cr)</th>
                <th>CTR %</th>
                <th>Click-to-Order %</th>
                <th>ROAS</th>
              </tr>
            </thead>
            <tbody>
              {"".join([f'''<tr>
                <td><strong>{s['advertiser_size']}</strong></td>
                <td>{s['city_tier']}</td>
                <td>{s['advertisers']}</td>
                <td>₹{s['ad_revenue_inr']/1e7:.2f} Cr</td>
                <td>{s['ctr_pct']:.2f}%</td>
                <td>{s['click_to_order_pct']:.2f}%</td>
                <td><strong>{s['roas']:.2f}x</strong></td>
              </tr>''' for s in segments])}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 5: A/B EXPERIMENTS -->
    <section id="tab-abtest" class="tab-pane" style="display:none;">
      <div class="grid-2col">
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">A/B Experiment Readout: "Bestseller Badge" Format</div>
              <div class="panel-subtitle">Testing visual trust badges on Sponsored Carousel ad units</div>
            </div>
            <span class="pill-badge pill-success">Verdict: {ab_meta['verdict']}</span>
          </div>

          <div class="insight-card" style="border-left-color: #10b981;">
            <h4>Decision Engine Verdict: SHIP TO 100% PRODUCTION</h4>
            <p>The Bestseller Badge demonstrated a statistically significant lift on the primary metric without triggering any guardrail regressions. Platform ad revenue remains protected while merchant click-volume expands.</p>
          </div>

          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Metric</th>
                  <th>Control</th>
                  <th>Treatment</th>
                  <th>Relative Lift</th>
                  <th>95% Conf. Interval</th>
                  <th>p-value</th>
                  <th>Stat Sig?</th>
                </tr>
              </thead>
              <tbody>
                {"".join([f'''<tr>
                  <td><span class="pill-badge {'pill-success' if r['role'] == 'primary' else 'pill-neutral'}">{r['role'].upper()}</span></td>
                  <td><strong>{r['metric']}</strong></td>
                  <td>{r['control'] * 100 if 'CTR' in r['metric'] or 'rate' in r['metric'] or 'user' in r['metric'] else r['control']:.2f}{'%' if 'rate' in r['metric'] or 'CTR' in r['metric'] else ''}</td>
                  <td>{r['treatment'] * 100 if 'CTR' in r['metric'] or 'rate' in r['metric'] or 'user' in r['metric'] else r['treatment']:.2f}{'%' if 'rate' in r['metric'] or 'CTR' in r['metric'] else ''}</td>
                  <td><strong style="color: {'var(--status-success)' if r['rel_lift'] > 0 else 'inherit'}">{r['rel_lift'] * 100:+.1f}%</strong></td>
                  <td>[{r['ci_low']*100:+.2f} pp, {r['ci_high']*100:+.2f} pp]</td>
                  <td><strong>{r['p_value']:.4f}</strong></td>
                  <td><span class="pill-badge {'pill-success' if r['significant'] else 'pill-neutral'}">{'YES' if r['significant'] else 'NO'}</span></td>
                </tr>''' for r in ab_summary])}
              </tbody>
            </table>
          </div>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">CTR Distribution Chart</div>
              <div class="panel-subtitle">Control (3.06%) vs Treatment (3.62%)</div>
            </div>
          </div>
          <div class="chart-container" onclick="openChartModal('07_ab_test_ctr', 'A/B Test CTR Lift')">
            <img src="{chart_imgs['07_ab_test_ctr']}" alt="A/B Test CTR">
            <div class="chart-caption">
              <span><b>Confidence:</b> Statistically significant lift (p = 0.0001, alpha = 0.05).</span>
              <span>Zoom</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 6: OPPORTUNITY SIMULATOR -->
    <section id="tab-simulator" class="tab-pane" style="display:none;">
      <div class="panel-card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Interactive Inventory Monetization Simulator</div>
            <div class="panel-subtitle">Simulate quarterly top-line revenue upside from selling unsold placement capacity</div>
          </div>
        </div>

        <div class="sim-box">
          <div class="sim-controls">
            <div class="sim-group">
              <div class="sim-label">
                <span>Target Fill Rate Uplift:</span>
                <span id="fillUpliftVal" style="color:var(--brand-primary);font-weight:700;">+6.0 pp</span>
              </div>
              <input type="range" id="fillSlider" class="sim-slider" min="1" max="15" step="0.5" value="6" oninput="updateSim()">
              <span style="font-size:11px;color:var(--text-muted);">Simulate selling an extra 1% to 15% of available ad slots</span>
            </div>

            <div class="sim-group">
              <div class="sim-label">
                <span>Marginal CPM Price Discount:</span>
                <span id="discVal" style="color:var(--brand-primary);font-weight:700;">-25.0%</span>
              </div>
              <input type="range" id="discSlider" class="sim-slider" min="0" max="60" step="5" value="25" oninput="updateSim()">
              <span style="font-size:11px;color:var(--text-muted);">Assumed discount required to clear incremental unsold impressions</span>
            </div>

            <div class="sim-group">
              <div class="sim-label">
                <span>Preset Scenarios:</span>
              </div>
              <div style="display:flex;gap:8px;">
                <button class="btn" onclick="applyPreset(3, 40)">Conservative</button>
                <button class="btn btn-primary" onclick="applyPreset(6, 25)">Base Case</button>
                <button class="btn" onclick="applyPreset(10, 10)">Optimistic</button>
              </div>
            </div>
          </div>

          <!-- Dynamic Simulator Result Scorecard -->
          <div class="sim-results">
            <div>
              <div class="kpi-label">Quarterly Incremental Revenue</div>
              <div class="kpi-val" id="simRevQtr" style="color:var(--brand-primary);">+₹81.6 L</div>
              <div class="kpi-footer" id="simRevUpliftPct">+4.4% vs Baseline</div>
            </div>
            <div>
              <div class="kpi-label">Annualized Run-Rate Upside</div>
              <div class="kpi-val" id="simRevAnn">₹3.26 Cr</div>
              <div class="kpi-footer">Compounded annual incremental</div>
            </div>
            <div>
              <div class="kpi-label">Extra Impressions Sold</div>
              <div class="kpi-val" id="simExtraImpr">23.9 M</div>
              <div class="kpi-footer">Across all 5 placements</div>
            </div>
            <div>
              <div class="kpi-label">Highest Yield Placement</div>
              <div class="kpi-val" id="simTopPlacement">Cart Page</div>
              <div class="kpi-footer">Contributes 25% of total upside</div>
            </div>
          </div>
        </div>

        <!-- Sizing Table Breakdown -->
        <div class="panel-header" style="margin-top:20px;">
          <div class="panel-title">Placement Opportunity Breakdown (Current Baseline: Last 3 Months)</div>
        </div>
        <div class="table-wrapper">
          <table class="data-table" id="simBreakdownTable">
            <thead>
              <tr>
                <th>Placement</th>
                <th>Capacity (3M)</th>
                <th>Current Fill %</th>
                <th>Target Fill %</th>
                <th>Current CPM (₹)</th>
                <th>Marginal CPM (₹)</th>
                <th>Extra Impressions</th>
                <th>Incremental Rev (₹ Lakhs)</th>
              </tr>
            </thead>
            <tbody id="simBreakdownBody">
              <!-- Dynamically populated by JS -->
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- DEDICATED DOCUMENTATION BOX AT BOTTOM -->
    <section id="documentation" class="docs-section">
      <h2>FoodAds Architecture &amp; Methodology Reference</h2>
      <p style="color:var(--text-secondary);margin-bottom:16px;">
        Complete platform documentation covering database architecture (MongoDB aggregation pipelines), unit economics, experimental design, and metrics.
      </p>

      <div class="grid-halves" style="margin-bottom:16px;">
        <div class="insight-card" style="border-left-color:var(--brand-primary);">
          <h4>MongoDB Analytics Pipeline Suite</h4>
          <p>The platform executes 10 production MongoDB aggregation pipelines stored in <code>mongo/*.json</code>. Raw CSVs are ingested into typed collections: <code>advertisers</code>, <code>campaigns</code>, <code>daily_performance</code>, <code>inventory</code>, and <code>ab_test_users</code>.</p>
        </div>
        <div class="insight-card" style="border-left-color:var(--status-success);">
          <h4>Hypothesis Testing Framework</h4>
          <p>Two-proportion pooled z-tests evaluate rate lifts (CTR, CVR) while Welch's t-test guards continuous spend. Enforces an automated decision rule: <strong>SHIP</strong>, <strong>RAMP CAUTIOUSLY</strong>, <strong>HOLD</strong>, or <strong>DO NOT SHIP</strong>.</p>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Pipeline</th>
              <th>Business Question</th>
              <th>MongoDB Aggregation Operator</th>
            </tr>
          </thead>
          <tbody>
            <tr><td><code>01_overall_kpis</code></td><td>Topline Ads P&amp;L</td><td><code>$lookup, $group, $project ($round, $divide, $multiply)</code></td></tr>
            <tr><td><code>02_monthly_trend</code></td><td>Month-over-month growth pacing</td><td><code>$project ($substr), $group, $sort, pandas pct_change</code></td></tr>
            <tr><td><code>03_category_performance</code></td><td>Category efficiency &amp; spend share</td><td><code>$lookup, $group, $project, spend share rank</code></td></tr>
            <tr><td><code>04_placement_performance</code></td><td>Ad slot yield &amp; conversion rates</td><td><code>$lookup campaigns, $group placement, CPC/CPO projection</code></td></tr>
            <tr><td><code>05_inventory_fill_rate</code></td><td>Capacity saturation &amp; utilization</td><td><code>$lookup inventory, daily capacity calculation, utilization threshold</code></td></tr>
            <tr><td><code>06_advertiser_segments</code></td><td>Merchant size vs. city tier returns</td><td><code>$lookup, $group by advertiser_size and city_tier</code></td></tr>
            <tr><td><code>07_retention_cohorts</code></td><td>Monthly advertiser churn decay</td><td><code>$lookup, min active month cohort grouping, tenure delta</code></td></tr>
            <tr><td><code>08_advertiser_ranking</code></td><td>Merchant spend &amp; risk quartiles</td><td><code>$group advertiser, spend rank, category ROAS quartile</code></td></tr>
            <tr><td><code>09_segments_to_grow_or_fix</code></td><td>Actionable segment matrix (FIX/GROW)</td><td><code>$group category x tier, benchmark comparison to overall ROAS</code></td></tr>
            <tr><td><code>10_opportunity_inputs</code></td><td>Trailing 90-day sizing inputs</td><td><code>$match date >= 90 days, $lookup inventory, CPM and fill rates</code></td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- MODAL 1: EXECUTIVE MEMO BOX -->
    <div id="memoModal" class="modal-overlay" onclick="closeMemoModal()">
      <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-box-header">
          <div class="modal-box-title">
            <span>Executive Insights Memo: Ads Marketplace Strategy</span>
          </div>
          <button class="modal-box-close" onclick="closeMemoModal()">&times;</button>
        </div>
        <div class="modal-box-body">
          <blockquote>
            <strong>To:</strong> Ads Leadership &amp; Commercial Operations | <strong>From:</strong> Marketplace Strategy &amp; Revenue Analytics<br>
            <strong>Period:</strong> Jul 2025 - Jun 2026 | <strong>Backend:</strong> MongoDB <code>foodads</code> Aggregations (Seed 42)
          </blockquote>

          <h2>1. Executive Summary: The P&amp;L Paradox</h2>
          <p>
            Over the 12-month period, top-line platform ad revenue grew from <strong>INR 1.12 Cr/month (Jul 2025)</strong> to <strong>INR 6.32 Cr/month (Jun 2026)</strong>—a <strong>5.6x expansion (+472% YoY)</strong>, totaling <strong>INR 50.68 Cr</strong> with <strong>INR 179.54 Cr in attributed GMV</strong>.
          </p>
          <p>
            However, our diagnostic shows that <strong>the growth is 100% volume-driven while ROAS remained completely flat at 3.54x</strong>. More critically, <strong>28.2% of ad revenue (₹14.3 Cr) sits in category-tier segments with ROAS &lt;70% of marketplace average (&lt;2.48x)</strong>. In low-AOV cuisines like Beverages (1.09x ROAS), merchants are losing money on every order once food costs (32%) and commissions (22%) are deducted.
          </p>

          <h2>2. Strategic Diagnostic Findings</h2>
          <h3>Finding 1: The "Low-AOV Trap" (Beverages &amp; Desserts)</h3>
          <p>
            Returns diverge by 5.1x across cuisines: Biryani leads at <strong>5.64x ROAS</strong> and North Indian at <strong>5.01x</strong>, while Beverages stagnates at <strong>1.09x</strong> and Desserts at <strong>1.64x</strong>. Clicks are not the problem (Beverages has high CTR of 3.83%), but because basket size is low (₹140 vs ₹380 for Biryani), fixed click costs (₹129 CPA) wipe out merchant gross margins.
          </p>

          <h3>Finding 2: Placement Yield Disparity (Cart Page vs. Home Banner)</h3>
          <p>
            <strong>Cart Page</strong> delivers our highest ROAS (<strong>5.80x</strong>), highest conversion (<strong>21.98%</strong>), and lowest CPA (<strong>₹53.90</strong>), yet remains <strong>24% unsold</strong>. Conversely, <strong>Home Banner</strong> underperforms at <strong>1.30x ROAS</strong> and ₹265 CPA (5x worse than Cart Page), while <strong>Search Top is at 90% capacity saturation</strong>.
          </p>

          <h3>Finding 3: The SMB Churn Cliff</h3>
          <p>
            Retention is stable through month 3 (~95%), but drops to 86% by month 6 and 72% by month 9. <strong>SMB merchants suffer 31.1% churn</strong>—10x worse than Enterprise Chains (3.0%).
          </p>

          <h3>Finding 4: Bestseller Badge Experiment</h3>
          <p>
            A/B test on 60,000 users confirmed a <strong>+18.2% relative lift in CTR (p = 0.0001)</strong> and <strong>+27.6% orders/user (p = 0.0235)</strong> with zero guardrail regression. Verdict: <strong>SHIP TO PRODUCTION</strong>.
          </p>

          <h2>3. Operational Playbook &amp; Recommendations</h2>
          <table>
            <thead>
              <tr><th>#</th><th>Initiative</th><th>Action</th><th>Financial Impact</th></tr>
            </thead>
            <tbody>
              <tr><td>1</td><td><strong>Cart Page Blitz</strong></td><td>Monetize unsold Cart Page inventory for cuisines with AOV &gt; ₹300.</td><td>+₹20.4 L / quarter</td></tr>
              <tr><td>2</td><td><strong>Low-AOV Shield</strong></td><td>Mandate minimum order size thresholds or meal combos for beverage ads.</td><td>Protects ₹14.3 Cr annual ad spend</td></tr>
              <tr><td>3</td><td><strong>Search Top Floor Pricing</strong></td><td>Raise reserve CPM floors by 12% during peak dinner hours in Metro cities.</td><td>+₹35.0 L / quarter</td></tr>
              <tr><td>4</td><td><strong>Home Banner Repositioning</strong></td><td>Discount reserve CPM by 25% and restrict to brand awareness launches.</td><td>+₹19.2 L / quarter</td></tr>
              <tr><td>5</td><td><strong>SMB Guardrail Alerts</strong></td><td>Deploy algorithmic bid throttles if SMB ROAS falls below 2.0x in first 14 days.</td><td>Cut SMB churn from 31% to &lt;20%</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- MODAL 2: DOCUMENTATION BOX -->
    <div id="docsModal" class="modal-overlay" onclick="closeDocsModal()">
      <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-box-header">
          <div class="modal-box-title">
            <span>FoodAds Technical Architecture &amp; Methodology</span>
          </div>
          <button class="modal-box-close" onclick="closeDocsModal()">&times;</button>
        </div>
        <div class="modal-box-body">
          <h2>1. Database Architecture (MongoDB Aggregation Framework)</h2>
          <p>
            The platform relies on a normalized MongoDB 8.0 schema running on <code>localhost:27017</code>. Collections are indexed on compound keys for optimal query execution:
          </p>
          <ul>
            <li><code>advertisers</code>: 300 documents (indexed by <code>advertiser_id</code>, <code>category</code>, <code>city_tier</code>).</li>
            <li><code>campaigns</code>: 448 documents (indexed by <code>campaign_id</code>, <code>advertiser_id</code>, <code>placement</code>).</li>
            <li><code>daily_performance</code>: 86,170 documents (indexed by <code>campaign_id + date</code>).</li>
            <li><code>inventory</code>: 1,825 documents (indexed by <code>date + placement</code>).</li>
            <li><code>ab_test_users</code>: 60,000 documents (indexed by <code>variant</code>).</li>
          </ul>

          <h2>2. Statistical Formulation for A/B Testing</h2>
          <p>
            Primary metrics (CTR, conversion rates) use a two-proportion pooled z-test:
          </p>
          <blockquote>
            z = (p_T - p_C) / sqrt( p_pool * (1 - p_pool) * (1/n_T + 1/n_C) )<br>
            95% CI = (p_T - p_C) ± 1.96 * sqrt( p_T*(1-p_T)/n_T + p_C*(1-p_C)/n_C )
          </blockquote>
          <p>
            Continuous spend guardrails evaluate user revenue via Welch's two-sample t-test without assuming equal variances.
          </p>

          <h2>3. Opportunity Sizing Methodology</h2>
          <p>
            Unsold inventory upside models capacity expansion over the trailing 90 days with price elasticity decay:
          </p>
          <blockquote>
            Incremental Revenue = Capacity_3M * ΔFillRate * CPM_current * (1 - DiscountRate) / 1000
          </blockquote>
          <ul>
            <li><strong>Conservative:</strong> +3 pp fill uplift, 40% marginal price discount (+₹37.6 L / quarter).</li>
            <li><strong>Base Case:</strong> +6 pp fill uplift, 25% marginal price discount (+₹81.6 L / quarter).</li>
            <li><strong>Optimistic:</strong> +10 pp fill uplift, 10% marginal price discount (+₹152.0 L / quarter).</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- MODAL 3: CHART ZOOM -->
    <div id="chartModal" class="modal-overlay" onclick="closeChartModal()">
      <div class="image-modal-content" onclick="event.stopPropagation()">
        <button class="modal-box-close" style="position:absolute;top:12px;right:12px;background:rgba(0,0,0,0.6);color:#fff;" onclick="closeChartModal()">&times;</button>
        <img id="modalImg" src="" alt="Zoomed Chart">
        <div style="padding:14px;background:var(--bg-surface);font-weight:600;font-size:14px;" id="modalCaption"></div>
      </div>
    </div>

    <!-- Footer -->
    <footer>
      <div>FoodAds Analytics Engine · Production Release · Powered by MongoDB Aggregations</div>
      <div>Methodology: 10 MongoDB Aggregation Pipelines · Two-Proportion Z-Test Engine · Scenario Monetization Model</div>
    </footer>

  </main>

  <!-- Embedded JSON Data for Client-Side Interactivity -->
  <script id="app-data" type="application/json">
    {json_payload}
  </script>

  <!-- Interactive Dashboard Controller -->
  <script>
    // 1. Tab Switching Function (Global & Inline Support)
    function switchTab(tabId, btn) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
      if (btn) {{
        btn.classList.add('active');
      }} else {{
        const matched = document.querySelector(`.tab-btn[data-tab="${{tabId}}"]`);
        if (matched) matched.classList.add('active');
      }}
      const target = document.getElementById(tabId);
      if (target) {{
        target.style.display = 'block';
      }}
    }}

    // Safe JSON Data Retrieval
    let APP_DATA = {{}};
    try {{
      APP_DATA = JSON.parse(document.getElementById('app-data').textContent);
    }} catch(e) {{
      console.error('Error parsing APP_DATA:', e);
    }}

    // 2. Theme Toggle
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {{
      themeBtn.addEventListener('click', () => {{
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('foodads-theme', next);
      }});
      const savedTheme = localStorage.getItem('foodads-theme');
      if (savedTheme) {{
        document.documentElement.setAttribute('data-theme', savedTheme);
      }}
    }}

    // 3. Modal Box Controls
    function openMemoModal() {{
      document.getElementById('memoModal').classList.add('open');
    }}
    function closeMemoModal() {{
      document.getElementById('memoModal').classList.remove('open');
    }}

    function openDocsModal() {{
      document.getElementById('docsModal').classList.add('open');
    }}
    function closeDocsModal() {{
      document.getElementById('docsModal').classList.remove('open');
    }}

    function openChartModal(chartKey, title) {{
      const chartMap = {{
        {"".join([f"'{name}': '{_img_base64(name)}',\n" for name, _, _ in CHARTS])}
      }};
      document.getElementById('modalImg').src = chartMap[chartKey] || '';
      document.getElementById('modalCaption').textContent = title;
      document.getElementById('chartModal').classList.add('open');
    }}
    function closeChartModal() {{
      document.getElementById('chartModal').classList.remove('open');
    }}

    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') {{
        closeMemoModal();
        closeDocsModal();
        closeChartModal();
      }}
    }});

    // 4. Segments Table Filter & Render
    function renderSegmentsTable(data) {{
      const tbody = document.getElementById('segmentsBody');
      if (!tbody) return;
      tbody.innerHTML = data.map(r => `
        <tr>
          <td><strong>${{r.category}}</strong></td>
          <td>${{r.city_tier}}</td>
          <td>${{r.advertisers}}</td>
          <td>₹${{((r.spend || 0) / 1e5).toFixed(1)}} L</td>
          <td><strong>${{(r.roas || 0).toFixed(2)}}x</strong></td>
          <td>${{(r.roas_vs_overall || 0).toFixed(2)}}x</td>
          <td><span class="action-badge action-${{r.action}}">${{r.action}}</span></td>
        </tr>
      `).join('');
    }}

    let currentSegments = (APP_DATA && APP_DATA.seg_actions) ? [...APP_DATA.seg_actions] : [];
    renderSegmentsTable(currentSegments);

    function filterSegments() {{
      const searchEl = document.getElementById('segSearch');
      const actionEl = document.getElementById('segActionFilter');
      const tierEl = document.getElementById('segTierFilter');
      if (!searchEl || !actionEl || !tierEl) return;

      const query = searchEl.value.toLowerCase();
      const action = actionEl.value;
      const tier = tierEl.value;

      currentSegments = (APP_DATA.seg_actions || []).filter(r => {{
        const matchesQuery = (r.category || '').toLowerCase().includes(query) || (r.city_tier || '').toLowerCase().includes(query);
        const matchesAction = action === 'ALL' || r.action === action;
        const matchesTier = tier === 'ALL' || r.city_tier === tier;
        return matchesQuery && matchesAction && matchesTier;
      }});
      renderSegmentsTable(currentSegments);
    }}

    let sortAsc = true;
    function sortSegmentsTable(e) {{
      const th = e.target.closest('th');
      if (!th) return;
      const col = th.getAttribute('data-col');
      if (!col) return;

      currentSegments.sort((a, b) => {{
        let valA = a[col];
        let valB = b[col];
        if (typeof valA === 'string') {{
          return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }}
        return sortAsc ? (valA || 0) - (valB || 0) : (valB || 0) - (valA || 0);
      }});
      sortAsc = !sortAsc;
      renderSegmentsTable(currentSegments);
    }}

    // 5. Interactive Sizing Simulator
    function updateSim() {{
      const fillEl = document.getElementById('fillSlider');
      const discEl = document.getElementById('discSlider');
      if (!fillEl || !discEl || !APP_DATA.opp_inputs) return;

      const uplift = parseFloat(fillEl.value);
      const discount = parseFloat(discEl.value);

      document.getElementById('fillUpliftVal').textContent = `+${{uplift.toFixed(1)}} pp`;
      document.getElementById('discVal').textContent = `-${{discount.toFixed(1)}}%`;

      let totalExtraImpr = 0;
      let totalIncRev = 0;
      let baseRev = 0;
      let placementRevs = [];

      const rows = APP_DATA.opp_inputs.map(inp => {{
        const curFill = (inp.fill_rate || 0) * 100;
        const newFill = Math.min(92.0, curFill + uplift);
        const extraImpr = Math.max(0, (newFill - curFill) / 100 * (inp.capacity_3m || 0));
        const marginalCpm = (inp.cpm_inr || 0) * (1 - discount / 100);
        const incRev = (extraImpr * marginalCpm) / 1000;

        totalExtraImpr += extraImpr;
        totalIncRev += incRev;
        baseRev += (inp.ad_revenue_3m_inr || 0);

        placementRevs.push({{ name: inp.placement, rev: incRev }});

        return `
          <tr>
            <td><strong>${{inp.placement}}</strong></td>
            <td>${{((inp.capacity_3m || 0) / 1e6).toFixed(1)}} M</td>
            <td>${{curFill.toFixed(1)}}%</td>
            <td><strong>${{newFill.toFixed(1)}}%</strong></td>
            <td>₹${{(inp.cpm_inr || 0).toFixed(1)}}</td>
            <td>₹${{marginalCpm.toFixed(1)}}</td>
            <td>+${{(extraImpr / 1e6).toFixed(2)}} M</td>
            <td><strong>+₹${{(incRev / 1e5).toFixed(2)}} L</strong></td>
          </tr>
        `;
      }});

      document.getElementById('simBreakdownBody').innerHTML = rows.join('');
      document.getElementById('simRevQtr').textContent = `+₹${{(totalIncRev / 1e5).toFixed(1)}} L`;
      document.getElementById('simRevAnn').textContent = `₹${{(totalIncRev * 4 / 1e7).toFixed(2)}} Cr`;
      document.getElementById('simExtraImpr').textContent = `${{(totalExtraImpr / 1e6).toFixed(1)}} M`;
      document.getElementById('simRevUpliftPct').textContent = `+${{(baseRev > 0 ? totalIncRev / baseRev * 100 : 0).toFixed(1)}}% vs Baseline`;

      if (placementRevs.length > 0) {{
        placementRevs.sort((a, b) => b.rev - a.rev);
        document.getElementById('simTopPlacement').textContent = placementRevs[0].name;
      }}
    }}

    function applyPreset(uplift, discount) {{
      document.getElementById('fillSlider').value = uplift;
      document.getElementById('discSlider').value = discount;
      updateSim();
    }}

    updateSim();
  </script>
</body>
</html>"""

    out_file = config.OUT_DIR / "dashboard.html"
    out_file.write_text(html_content, encoding="utf-8")
    if verbose:
        print(f"  dashboard: {out_file}")
    return str(out_file)


def main() -> None:
    argparse.ArgumentParser(description="Build Executive HTML Dashboard").parse_args()
    run()


if __name__ == "__main__":
    main()
