"""Build an executive-grade, interactive HTML dashboard (outputs/dashboard.html).

Crafted with a human-designed enterprise analytics UI (Stripe/Datadog inspired),
complete with interactive tabs, live scenario calculator, real-time segment search/sort,
advertiser risk inspector, and publication-quality chart embeds.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path

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


def run(verbose: bool = True) -> str:
    # 1. Load data tables
    kpis = pd.read_csv(config.TABLE_DIR / "01_overall_kpis.csv").iloc[0].to_dict()
    monthly = pd.read_csv(config.TABLE_DIR / "02_monthly_trend.csv").to_dict(orient="records")
    category = pd.read_csv(config.TABLE_DIR / "03_category_performance.csv").to_dict(orient="records")
    placement = pd.read_csv(config.TABLE_DIR / "04_placement_performance.csv").to_dict(orient="records")
    fill = pd.read_csv(config.TABLE_DIR / "05_inventory_fill_rate.csv").to_dict(orient="records")
    segments = pd.read_csv(config.TABLE_DIR / "06_advertiser_segments.csv").to_dict(orient="records")
    cohorts = pd.read_csv(config.TABLE_DIR / "07_retention_cohorts.csv").to_dict(orient="records")
    ranking = pd.read_csv(config.TABLE_DIR / "08_advertiser_ranking.csv").to_dict(orient="records")
    seg_actions = pd.read_csv(config.TABLE_DIR / "09_segments_to_grow_or_fix.csv").to_dict(orient="records")
    opp_inputs = pd.read_csv(config.TABLE_DIR / "10_opportunity_inputs.csv").to_dict(orient="records")
    ab_summary = pd.read_csv(config.TABLE_DIR / "ab_test_summary.csv").to_dict(orient="records")
    opp_sizing = pd.read_csv(config.TABLE_DIR / "opportunity_sizing.csv").to_dict(orient="records")
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
        "ranking": ranking[:100],  # top 100 for client-side inspector
        "seg_actions": seg_actions,
        "opp_inputs": opp_inputs,
        "ab_summary": ab_summary,
        "opp_sizing": opp_sizing,
        "ab_meta": ab_meta,
    }
    json_payload = json.dumps(app_data)

    # Derived headline figures
    rev_cr = kpis["ad_revenue_inr"] / 1e7
    gmv_cr = kpis["attributed_gmv_inr"] / 1e7
    impr_b = kpis["impressions"] / 1e9
    base_opp_lakhs = (pd.DataFrame(opp_sizing).query("scenario == 'Base'")["incremental_revenue_3m"].sum()) / 1e5
    base_opp_cr = base_opp_lakhs / 100

    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FoodAds Intelligence Console | Marketplace Economics & Experimentation</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

      /* Light Theme (default fallback) */
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
      width: 34px;
      height: 34px;
      border-radius: 8px;
      background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 800;
      font-size: 16px;
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

    /* Modal for charts */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.85);
      z-index: 999;
      justify-content: center;
      align-items: center;
      padding: 24px;
    }}

    .modal-overlay.open {{
      display: flex;
    }}

    .modal-content {{
      max-width: 95vw;
      max-height: 90vh;
      background: var(--bg-surface);
      border-radius: 12px;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
    }}

    .modal-content img {{
      max-width: 100%;
      max-height: 80vh;
      object-fit: contain;
    }}

    .modal-close {{
      position: absolute;
      top: 12px;
      right: 12px;
      background: rgba(0,0,0,0.6);
      color: #fff;
      border: none;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      font-size: 18px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    footer {{
      margin-top: 40px;
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
      <span class="pill-badge pill-success">● System Operational</span>
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
      <a href="../docs/INSIGHTS_MEMO.md" target="_blank" class="btn">Executive Memo</a>
      <a href="../README.md" target="_blank" class="btn btn-primary">Documentation</a>
    </div>
  </header>

  <!-- Shell Container -->
  <main class="app-shell">

    <!-- Strategic Context Banner -->
    <div class="context-banner">
      <div class="context-banner-text">
        <strong>Marketplace Note:</strong> This intelligence console analyzes a synthetic 3-sided food delivery ad platform.
        Ad revenue reached <strong>INR {rev_cr:.1f} Cr</strong> driven by a 5.6x expansion in advertisers and traffic, while merchant ROAS remained pegged at <strong>{kpis['roas']:.2f}x</strong>.
      </div>
      <div>
        <span class="pill-badge pill-neutral">Seed 42 · 300 Merchants</span>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <nav class="tab-nav">
      <button class="tab-btn active" data-tab="tab-overview">📊 Executive P&amp;L</button>
      <button class="tab-btn" data-tab="tab-inventory">🎯 Inventory &amp; Yield</button>
      <button class="tab-btn" data-tab="tab-segments">🍱 Category &amp; Segments</button>
      <button class="tab-btn" data-tab="tab-retention">🔄 Retention &amp; Churn</button>
      <button class="tab-btn" data-tab="tab-abtest">🧪 A/B Experiments</button>
      <button class="tab-btn" data-tab="tab-simulator">🧮 Opportunity Simulator</button>
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
              <span>🔍 Zoom</span>
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
            <h4>🚨 The Low-AOV Beverage/Dessert Trap</h4>
            <p>Beverages (1.09x ROAS) and Desserts (1.64x ROAS) consume <strong>23% of total ad spend</strong>. Because basket sizes are low (₹140-190), fixed click costs wipe out restaurant contribution margins.</p>
          </div>

          <div class="insight-card" style="border-left-color: #10b981;">
            <h4>💎 Cart Page: Premium Monetization Lever</h4>
            <p>Cart Page delivers the marketplace's highest return (<strong>5.80x ROAS</strong>) with a 22% conversion rate, yet remains <strong>24% unsold</strong>. A prime upsell target for high-AOV cuisine partners.</p>
          </div>

          <div class="insight-card" style="border-left-color: #3b82f6;">
            <h4>📈 Search Top Hits Capacity Ceiling</h4>
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
                <td><span class="badge-delta {'badge-pos' if str(m['ad_revenue_mom_pct']) != 'nan' and m['ad_revenue_mom_pct'] > 0 else ''}">{f"+{m['ad_revenue_mom_pct']:.1f}%" if str(m['ad_revenue_mom_pct']) != 'nan' else '—'}</span></td>
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
              <span>🔍 Zoom</span>
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
              <span>🔍 Zoom</span>
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
              <span>🔍 Zoom</span>
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
              <span>🔍 Zoom</span>
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
              <span>🔍 Zoom</span>
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
            <h4>⚠️ SMB Merchants Experience 10x Churn Risk</h4>
            <p><strong>31% of SMB advertisers churned</strong> during the period, compared to only <strong>14% of Mid-tier</strong> and <strong>3% of Enterprise Chains</strong>. SMB budgets are fragile to initial week performance volatility.</p>
          </div>

          <div class="insight-card" style="border-left-color: #f59e0b;">
            <h4>📉 The Month-3 Retention Cliff</h4>
            <p>Advertiser churn accelerates between Month 3 and Month 6. Onboarding support must proactively audit bids and creative before the Day-90 mark to prevent silent budget depletion.</p>
          </div>

          <div class="insight-card" style="border-left-color: #10b981;">
            <h4>🛡️ Strategic Recommendation: Automated Floor Shields</h4>
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
              <span>🔍 Zoom</span>
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

    <!-- Modal for chart zoom -->
    <div id="chartModal" class="modal-overlay" onclick="closeChartModal()">
      <div class="modal-content" onclick="event.stopPropagation()">
        <button class="modal-close" onclick="closeChartModal()">&times;</button>
        <img id="modalImg" src="" alt="Zoomed Chart">
        <div style="padding:14px;background:var(--bg-surface);font-weight:600;font-size:14px;" id="modalCaption"></div>
      </div>
    </div>

    <!-- Footer -->
    <footer>
      <div>FoodAds Analytics Engine · Production Release · Built for Marketplace Strategy &amp; Revenue Operations</div>
      <div>Methodology: 10 Relational SQL Pipelines · Two-Proportion Z-Test Engine · Scenario Monetization Model</div>
    </footer>

  </main>

  <!-- Embedded JSON Data for Client-Side Interactivity -->
  <script id="app-data" type="application/json">
    {json_payload}
  </script>

  <!-- Interactive Dashboard Controller -->
  <script>
    const APP_DATA = JSON.parse(document.getElementById('app-data').textContent);

    // 1. Tab Navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-tab');
        document.getElementById(targetId).style.display = 'block';
      }});
    }});

    // 2. Theme Toggle
    const themeBtn = document.getElementById('themeToggleBtn');
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

    // 3. Segments Table Filter & Render
    function renderSegmentsTable(data) {{
      const tbody = document.getElementById('segmentsBody');
      tbody.innerHTML = data.map(r => `
        <tr>
          <td><strong>${{r.category}}</strong></td>
          <td>${{r.city_tier}}</td>
          <td>${{r.advertisers}}</td>
          <td>₹${{(r.spend / 1e5).toFixed(1)}} L</td>
          <td><strong>${{r.roas.toFixed(2)}}x</strong></td>
          <td>${{r.roas_vs_overall.toFixed(2)}}x</td>
          <td><span class="action-badge action-${{r.action}}">${{r.action}}</span></td>
        </tr>
      `).join('');
    }}

    let currentSegments = [...APP_DATA.seg_actions];
    renderSegmentsTable(currentSegments);

    function filterSegments() {{
      const query = document.getElementById('segSearch').value.toLowerCase();
      const action = document.getElementById('segActionFilter').value;
      const tier = document.getElementById('segTierFilter').value;

      currentSegments = APP_DATA.seg_actions.filter(r => {{
        const matchesQuery = r.category.toLowerCase().includes(query) || r.city_tier.toLowerCase().includes(query);
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
        return sortAsc ? valA - valB : valB - valA;
      }});
      sortAsc = !sortAsc;
      renderSegmentsTable(currentSegments);
    }}

    // 4. Interactive Sizing Simulator
    function updateSim() {{
      const uplift = parseFloat(document.getElementById('fillSlider').value);
      const discount = parseFloat(document.getElementById('discSlider').value);

      document.getElementById('fillUpliftVal').textContent = `+${{uplift.toFixed(1)}} pp`;
      document.getElementById('discVal').textContent = `-${{discount.toFixed(1)}}%`;

      let totalExtraImpr = 0;
      let totalIncRev = 0;
      let baseRev = 0;
      let placementRevs = [];

      const rows = APP_DATA.opp_inputs.map(inp => {{
        const curFill = inp.fill_rate * 100;
        const newFill = Math.min(92.0, curFill + uplift);
        const extraImpr = Math.max(0, (newFill - curFill) / 100 * inp.capacity_3m);
        const marginalCpm = inp.cpm_inr * (1 - discount / 100);
        const incRev = (extraImpr * marginalCpm) / 1000;

        totalExtraImpr += extraImpr;
        totalIncRev += incRev;
        baseRev += inp.ad_revenue_3m_inr;

        placementRevs.push({{ name: inp.placement, rev: incRev }});

        return `
          <tr>
            <td><strong>${{inp.placement}}</strong></td>
            <td>${{(inp.capacity_3m / 1e6).toFixed(1)}} M</td>
            <td>${{curFill.toFixed(1)}}%</td>
            <td><strong>${{newFill.toFixed(1)}}%</strong></td>
            <td>₹${{inp.cpm_inr.toFixed(1)}}</td>
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
      document.getElementById('simRevUpliftPct').textContent = `+${{(totalIncRev / baseRev * 100).toFixed(1)}}% vs Baseline`;

      placementRevs.sort((a, b) => b.rev - a.rev);
      document.getElementById('simTopPlacement').textContent = placementRevs[0].name;
    }}

    function applyPreset(uplift, discount) {{
      document.getElementById('fillSlider').value = uplift;
      document.getElementById('discSlider').value = discount;
      updateSim();
    }}

    updateSim();

    // 5. Modal Chart Zoom
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
