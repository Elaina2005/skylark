"""
Executive Leadership Update Generator.
Synthesizes live Monday.com pipeline, operations, risk flags, and data quality into an executive Markdown briefing.
"""
import logging
import pandas as pd
from datetime import datetime, timezone
from src.tools import (
    execute_compute_metric,
    execute_get_deals,
    execute_get_work_orders,
    execute_get_data_quality_report,
    _get_dataframes,
    _find_column
)
from src.normalizer import normalize_dates, normalize_currency

logger = logging.getLogger(__name__)

def generate_leadership_update(period: str = "last_30_days") -> str:
    """
    Generates a comprehensive executive Markdown briefing from live Monday.com data.
    """
    now = datetime.now()
    today_str = now.strftime("%B %d, %Y")
    
    # 1. Pipeline Metrics
    total_pipeline_res = execute_compute_metric(metric="total_value", board="deals", filters={"status": "Open"})
    total_pipeline_inr = total_pipeline_res.get("formatted_inr", "?0.00")
    
    win_rate_res = execute_compute_metric(metric="win_rate", board="deals")
    win_rate_val = win_rate_res.get("win_rate_percent", 0.0)
    won_cnt = win_rate_res.get("won_deals_count", 0)
    closed_cnt = win_rate_res.get("closed_deals_count", 0)
    
    deals_by_sector = execute_compute_metric(metric="by_sector_breakdown", board="deals")
    top_sectors_pipeline = deals_by_sector.get("sector_breakdown", [])[:3]
    
    # Deals by stage
    deals_grouped_stage = execute_get_deals(group_by="Deal Stage")
    stage_breakdown = deals_grouped_stage.get("grouped_summary", [])
    
    # 2. Operations Metrics
    comp_rate_res = execute_compute_metric(metric="completion_rate", board="work_orders")
    comp_rate_val = comp_rate_res.get("completion_rate_percent", 0.0)
    comp_cnt = comp_rate_res.get("completed_count", 0)
    total_wo_cnt = comp_rate_res.get("total_work_orders", 0)
    
    overdue_res = execute_get_work_orders(filters={"is_overdue": True})
    overdue_cnt = overdue_res.get("matched_records", 0)
    
    wo_by_sector = execute_compute_metric(metric="by_sector_breakdown", board="work_orders")
    top_sectors_ops = wo_by_sector.get("sector_breakdown", [])[:3]
    
    # 3. Watch Items & Risk Detection
    wo_df, deals_df = _get_dataframes()
    watch_items = []
    
    if deals_df is not None and len(deals_df) > 0:
        # Check deals with close date in the past still marked Open
        close_date_col = _find_column(deals_df, ["Tentative Close Date", "Close Date"])
        status_col = _find_column(deals_df, ["Deal Status", "status"])
        deal_name_col = _find_column(deals_df, ["Deal Name", "Name"])
        val_col = _find_column(deals_df, ["Masked Deal value", "value"])
        
        if close_date_col and status_col:
            parsed_close = normalize_dates(deals_df[close_date_col])
            open_mask = deals_df[status_col].astype(str).str.contains("Open", case=False, na=False)
            past_close_mask = (parsed_close < pd.to_datetime(now.date())) & open_mask
            stale_deals = deals_df[past_close_mask]
            
            if len(stale_deals) > 0:
                watch_items.append(
                    f"?? **Stale Open Deals ({len(stale_deals)} deals):** Opportunities with tentative close date in the past still marked 'Open'."
                )
                for _, r in stale_deals.head(3).iterrows():
                    d_name = r.get(deal_name_col, "Unknown")
                    d_val = r.get(val_col, "N/A")
                    watch_items.append(f"  - `{d_name}` (Value: ?{float(d_val):,.2f} if valid, Est Date: {r.get(close_date_col)})")
    
    if wo_df is not None and len(wo_df) > 0:
        # Check work orders overdue by >14 days
        end_date_col = _find_column(wo_df, ["Probable End Date", "End Date"])
        wo_status_col = _find_column(wo_df, ["Execution Status", "status"])
        serial_col = _find_column(wo_df, ["Serial #", "Deal name masked"])
        
        if end_date_col and wo_status_col:
            parsed_end = normalize_dates(wo_df[end_date_col])
            not_completed_mask = ~wo_df[wo_status_col].astype(str).str.contains("Completed", case=False, na=False)
            days_overdue = (pd.to_datetime(now.date()) - parsed_end).dt.days
            critical_overdue = wo_df[not_completed_mask & (days_overdue > 14)]
            
            if len(critical_overdue) > 0:
                watch_items.append(
                    f"?? **Critically Overdue Work Orders ({len(critical_overdue)} orders):** Incomplete projects past target delivery by >14 days."
                )
                for _, r in critical_overdue.head(3).iterrows():
                    s_no = r.get(serial_col, "N/A")
                    watch_items.append(f"  - `{s_no}` (Status: {r.get(wo_status_col)}, Planned End: {r.get(end_date_col)})")

    if not watch_items:
        watch_items.append("? **No critical delivery or pipeline anomalies detected.**")

    # 4. Data Quality Caveats
    dq_report = execute_get_data_quality_report(board="both")
    wo_caveats = dq_report.get("work_orders", {}).get("caveats", [])
    deals_caveats = dq_report.get("deals", {}).get("caveats", [])
    all_caveats = wo_caveats + deals_caveats

    # Assemble Structured Markdown
    md_lines = [
        f"# ?? Executive Leadership Business Intelligence Update",
        f"**Date:** {today_str} | **Reporting Period:** `{period}` | **Data Source:** Live Monday.com Boards",
        "",
        "---",
        "",
        "## ?? 1. Sales & Commercial Pipeline Snapshot",
        f"- **Active Pipeline Value:** `{total_pipeline_inr}` ({total_pipeline_res.get('records_used', 0)} open opportunities)",
        f"- **Win Rate (Closed Deals):** `{win_rate_val}%` ({won_cnt} won out of {closed_cnt} decided deals)",
        f"- **Top Sectors by Pipeline Volume:**",
    ]

    for sec in top_sectors_pipeline:
        s_name = sec.get("Sector/service") or sec.get("Sector") or "Unassigned"
        s_val = sec.get("total_value", 0.0)
        s_cnt = sec.get("count", 0)
        md_lines.append(f"  - **{s_name}:** ?{s_val:,.2f} across {s_cnt} opportunities")

    md_lines.extend([
        "",
        "## ??? 2. Operations & Execution Snapshot",
        f"- **Total Work Orders Tracked:** `{total_wo_cnt}`",
        f"- **Overall Completion Rate:** `{comp_rate_val}%` ({comp_cnt} completed)",
        f"- **Overdue Orders (Past Delivery Date):** `{overdue_cnt}`",
        f"- **Top Sectors by Active Execution Value:**",
    ])

    for sec in top_sectors_ops:
        s_name = sec.get("Sector") or sec.get("Sector/service") or "Unassigned"
        s_val = sec.get("total_value", 0.0)
        s_cnt = sec.get("count", 0)
        md_lines.append(f"  - **{s_name}:** ?{s_val:,.2f} ({s_cnt} work orders)")

    md_lines.extend([
        "",
        "## ?? 3. Executive Watch Items & Operational Risks",
    ])
    for item in watch_items:
        md_lines.append(item)

    md_lines.extend([
        "",
        "## ?? 4. Data Quality & Reporting Caveats",
    ])
    if all_caveats:
        for c in all_caveats[:5]:
            md_lines.append(f"- *Caveat:* {c}")
    else:
        md_lines.append("- *Data Quality:* Clean records across all primary tracking fields.")

    md_lines.extend([
        "",
        "---",
        f"*Generated automatically by Skylark BI Agent on {today_str} UTC.*"
    ])

    return "\n".join(md_lines)
