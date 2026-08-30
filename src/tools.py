"""
Claude tool implementations and JSON schemas for Monday.com Business Intelligence querying.
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from src.monday_client import get_cached_data, refresh_cache
from src.normalizer import (
    handle_missing,
    data_quality_report,
    normalize_dates,
    normalize_currency,
    normalize_text_field
)
from src.schema import CANONICAL_SECTORS

logger = logging.getLogger(__name__)

# --- Tool JSON Schemas for Anthropic Claude ---

TOOL_DEFINITIONS = [
    {
        "name": "get_work_orders",
        "description": "Fetches, filters, and groups Work Orders data. Use to answer operational, milestone, execution, and project-specific questions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "Filter criteria: sector (string), status (string, e.g. 'Completed', 'Ongoing', 'Not Started'), date_from (YYYY-MM-DD), date_to (YYYY-MM-DD), client_name (string), is_overdue (boolean).",
                    "properties": {
                        "sector": {"type": "string"},
                        "status": {"type": "string"},
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                        "client_name": {"type": "string"},
                        "is_overdue": {"type": "boolean"}
                    }
                },
                "group_by": {
                    "type": ["string", "null"],
                    "description": "Optional column to group rows by, e.g. 'Sector', 'Execution Status', 'Nature of Work'."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rows to return in tabular view (default 50)."
                }
            }
        }
    },
    {
        "name": "get_deals",
        "description": "Fetches, filters, and groups Deals sales pipeline data. Use to answer sales opportunities, stages, deal size, rep ownership, and win/loss questions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "Filter criteria: sector (string), stage (string, e.g. 'G. Project Won', 'F. Negotiations', 'L. Project Lost'), status (string, e.g. 'Open', 'Won', 'Dead'), date_from (YYYY-MM-DD), date_to (YYYY-MM-DD), owner (string), min_value (number), max_value (number).",
                    "properties": {
                        "sector": {"type": "string"},
                        "stage": {"type": "string"},
                        "status": {"type": "string"},
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                        "owner": {"type": "string"},
                        "min_value": {"type": "number"},
                        "max_value": {"type": "number"}
                    }
                },
                "group_by": {
                    "type": ["string", "null"],
                    "description": "Optional column to group rows by, e.g. 'Sector/service', 'Deal Stage', 'Deal Status', 'Owner code'."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rows to return in tabular view (default 50)."
                }
            }
        }
    },
    {
        "name": "compute_metric",
        "description": "Computes high-level business intelligence aggregates and KPIs across Work Orders or Deals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": [
                        "total_value",
                        "count",
                        "average_value",
                        "win_rate",
                        "completion_rate",
                        "by_sector_breakdown"
                    ],
                    "description": "KPI metric to calculate: 'total_value' (sum of deal/order value), 'count' (record count), 'average_value' (mean value), 'win_rate' (percentage of Won deals vs total completed deals), 'completion_rate' (percentage of Completed work orders vs total), 'by_sector_breakdown' (sector breakdown of count and value)."
                },
                "board": {
                    "type": "string",
                    "enum": ["work_orders", "deals"],
                    "description": "Which board dataset to compute the metric from."
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filter criteria to narrow down the records prior to metric calculation."
                },
                "group_by": {
                    "type": ["string", "null"],
                    "description": "Optional dimension to group the metric aggregation by (e.g. 'Sector', 'Deal Stage', 'Owner code')."
                }
            },
            "required": ["metric", "board"]
        }
    },
    {
        "name": "cross_reference_boards",
        "description": "Performs cross-board analytics by joining Work Orders and Deals on company name, client code, or sector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "join_key": {
                    "type": "string",
                    "enum": ["company_name", "sector", "deal_name"],
                    "description": "Attribute to link the two datasets on."
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["won_deals_without_work_orders", "sector_comparison", "work_orders_without_deals", "full_cross_join"],
                    "description": "Cross-board analysis intent (e.g. 'won_deals_without_work_orders' finds deals marked Won that have no active work order; 'sector_comparison' compares deal revenue vs executed work order volume)."
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters to apply to both boards."
                }
            },
            "required": ["join_key"]
        }
    },
    {
        "name": "get_data_quality_report",
        "description": "Fetches data quality metrics, missing value percentages, and caveats for Work Orders and/or Deals. Proactively call this before presenting financial/pipeline aggregates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "board": {
                    "type": "string",
                    "enum": ["work_orders", "deals", "both"],
                    "description": "Which board to inspect for data completeness and quality."
                }
            },
            "required": ["board"]
        }
    },
    {
        "name": "refresh_data",
        "description": "Forces an immediate live refresh of the Monday.com cache.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "generate_leadership_update",
        "description": "Generates a structured executive leadership summary in Markdown covering pipeline health, operational throughput, data quality caveats, and watch items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Reporting timeframe: e.g. 'last_30_days', 'current_quarter', 'all_time'."
                }
            }
        }
    }
]

# --- Helper Utilities ---

def _get_dataframes():
    cache = get_cached_data()
    return cache.get("work_orders_df", pd.DataFrame()), cache.get("deals_df", pd.DataFrame())

def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        for cand in candidates:
            if cand.lower() in c.lower():
                return c
    return None

def _apply_date_filter(df: pd.DataFrame, date_col: str, d_from: str | None, d_to: str | None) -> pd.DataFrame:
    if date_col not in df.columns or (not d_from and not d_to):
        return df
    
    parsed_col = normalize_dates(df[date_col])
    mask = pd.Series(True, index=df.index)
    if d_from:
        try:
            from_dt = pd.to_datetime(d_from)
            mask &= (parsed_col >= from_dt)
        except Exception:
            pass
    if d_to:
        try:
            to_dt = pd.to_datetime(d_to)
            mask &= (parsed_col <= to_dt)
        except Exception:
            pass
    return df[mask]

# --- Tool Implementations ---

def execute_get_work_orders(filters: dict | None = None, group_by: str | None = None, limit: int = 50) -> dict:
    wo_df, _ = _get_dataframes()
    if wo_df is None or len(wo_df) == 0:
        return {"status": "empty", "total_records": 0, "records": [], "message": "No Work Orders data available."}

    df = wo_df.copy()
    filters = filters or {}
    total_original = len(df)

    # 1. Sector Filter
    if "sector" in filters and filters["sector"]:
        target_sector = normalize_text_field(pd.Series([filters["sector"]]), canonical_values=CANONICAL_SECTORS).iloc[0]
        sec_col = _find_column(df, ["Sector", "sector/service", "industry"])
        if sec_col:
            df = df[df[sec_col].astype(str).str.contains(str(target_sector), case=False, na=False)]

    # 2. Status Filter
    if "status" in filters and filters["status"]:
        stat_col = _find_column(df, ["Execution Status", "WO Status (billed)", "status"])
        if stat_col:
            df = df[df[stat_col].astype(str).str.contains(str(filters["status"]), case=False, na=False)]

    # 3. Client Filter
    if "client_name" in filters and filters["client_name"]:
        cli_col = _find_column(df, ["Customer Name Code", "Deal name masked", "client", "customer"])
        if cli_col:
            df = df[df[cli_col].astype(str).str.contains(str(filters["client_name"]), case=False, na=False)]

    # 4. Overdue Filter (End Date < today and Status != Completed)
    if filters.get("is_overdue"):
        end_col = _find_column(df, ["Probable End Date", "End Date", "Delivery Date"])
        stat_col = _find_column(df, ["Execution Status", "status"])
        if end_col and stat_col:
            parsed_end = normalize_dates(df[end_col])
            today = pd.to_datetime(datetime.now().date())
            is_overdue_mask = (parsed_end < today) & (~df[stat_col].astype(str).str.contains("Completed", case=False, na=False))
            df = df[is_overdue_mask]

    # 5. Date Range Filter
    date_col = _find_column(df, ["Probable Start Date", "Date of PO/LOI", "Created Date"])
    if date_col:
        df = _apply_date_filter(df, date_col, filters.get("date_from"), filters.get("date_to"))

    matched_count = len(df)
    if matched_count == 0:
        return {
            "status": "zero_matches",
            "total_records_searched": total_original,
            "matched_records": 0,
            "message": "No work orders matched the specified filter criteria.",
            "filters_applied": filters
        }

    # Grouping
    if group_by:
        group_col = _find_column(df, [group_by])
        if group_col:
            val_col = _find_column(df, ["Amount in Rupees (Excl of GST) (Masked)", "Amount in Rupees (Incl of GST) (Masked)", "Amount", "Value"])
            if val_col:
                numeric_series = normalize_currency(df[val_col])
                df["_val_temp"] = numeric_series
                grouped = df.groupby(group_col).agg(
                    count=("item_id" if "item_id" in df.columns else df.columns[0], "count"),
                    total_value=("_val_temp", "sum"),
                    avg_value=("_val_temp", "mean")
                ).reset_index()
                return {
                    "status": "success",
                    "group_by": group_col,
                    "grouped_summary": grouped.to_dict(orient="records"),
                    "total_matched": matched_count
                }

    # Sample rows for tabular inspection
    sample_cols = [c for c in [
        "Serial #", "Deal name masked", "Customer Name Code", "Sector",
        "Execution Status", "Probable Start Date", "Probable End Date",
        "Amount in Rupees (Excl of GST) (Masked)", "Type of Work"
    ] if c in df.columns]
    
    if not sample_cols:
        sample_cols = list(df.columns[:8])

    return {
        "status": "success",
        "total_records_searched": total_original,
        "matched_records": matched_count,
        "records": df[sample_cols].head(limit).to_dict(orient="records")
    }

def execute_get_deals(filters: dict | None = None, group_by: str | None = None, limit: int = 50) -> dict:
    _, deals_df = _get_dataframes()
    if deals_df is None or len(deals_df) == 0:
        return {"status": "empty", "total_records": 0, "records": [], "message": "No Deals data available."}

    df = deals_df.copy()
    filters = filters or {}
    total_original = len(df)

    # 1. Sector Filter
    if "sector" in filters and filters["sector"]:
        target_sector = normalize_text_field(pd.Series([filters["sector"]]), canonical_values=CANONICAL_SECTORS).iloc[0]
        sec_col = _find_column(df, ["Sector/service", "sector", "industry"])
        if sec_col:
            df = df[df[sec_col].astype(str).str.contains(str(target_sector), case=False, na=False)]

    # 2. Stage Filter
    if "stage" in filters and filters["stage"]:
        stage_col = _find_column(df, ["Deal Stage", "stage"])
        if stage_col:
            df = df[df[stage_col].astype(str).str.contains(str(filters["stage"]), case=False, na=False)]

    # 3. Status Filter (Open, Won, Dead)
    if "status" in filters and filters["status"]:
        stat_col = _find_column(df, ["Deal Status", "status"])
        if stat_col:
            df = df[df[stat_col].astype(str).str.contains(str(filters["status"]), case=False, na=False)]

    # 4. Owner Filter
    if "owner" in filters and filters["owner"]:
        owner_col = _find_column(df, ["Owner code", "owner", "sales rep"])
        if owner_col:
            df = df[df[owner_col].astype(str).str.contains(str(filters["owner"]), case=False, na=False)]

    # 5. Min / Max Value Filter
    val_col = _find_column(df, ["Masked Deal value", "Deal value", "value", "Amount"])
    if val_col:
        num_vals = normalize_currency(df[val_col])
        if "min_value" in filters and filters["min_value"] is not None:
            df = df[num_vals >= float(filters["min_value"])]
        if "max_value" in filters and filters["max_value"] is not None:
            df = df[num_vals <= float(filters["max_value"])]

    # 6. Date Range Filter
    date_col = _find_column(df, ["Tentative Close Date", "Close Date (A)", "Created Date"])
    if date_col:
        df = _apply_date_filter(df, date_col, filters.get("date_from"), filters.get("date_to"))

    matched_count = len(df)
    if matched_count == 0:
        return {
            "status": "zero_matches",
            "total_records_searched": total_original,
            "matched_records": 0,
            "message": "No deals matched the specified filter criteria.",
            "filters_applied": filters
        }

    # Grouping
    if group_by:
        group_col = _find_column(df, [group_by])
        if group_col:
            if val_col:
                df["_val_temp"] = normalize_currency(df[val_col])
                grouped = df.groupby(group_col).agg(
                    count=("item_id" if "item_id" in df.columns else df.columns[0], "count"),
                    total_value=("_val_temp", "sum"),
                    avg_value=("_val_temp", "mean")
                ).reset_index()
                return {
                    "status": "success",
                    "group_by": group_col,
                    "grouped_summary": grouped.to_dict(orient="records"),
                    "total_matched": matched_count
                }

    sample_cols = [c for c in [
        "Deal Name", "Owner code", "Client Code", "Deal Status",
        "Deal Stage", "Closure Probability", "Masked Deal value",
        "Tentative Close Date", "Sector/service"
    ] if c in df.columns]
    
    if not sample_cols:
        sample_cols = list(df.columns[:8])

    return {
        "status": "success",
        "total_records_searched": total_original,
        "matched_records": matched_count,
        "records": df[sample_cols].head(limit).to_dict(orient="records")
    }

def execute_compute_metric(metric: str, board: str, filters: dict | None = None, group_by: str | None = None) -> dict:
    wo_df, deals_df = _get_dataframes()
    filters = filters or {}
    
    target_df = wo_df if board == "work_orders" else deals_df
    board_label = "Work Orders" if board == "work_orders" else "Deals"
    
    if target_df is None or len(target_df) == 0:
        return {"error": f"Board '{board_label}' has no data available."}

    df = target_df.copy()
    total_raw_rows = len(df)

    # 1. Sector filtering if provided
    if "sector" in filters and filters["sector"]:
        target_sector = normalize_text_field(pd.Series([filters["sector"]]), canonical_values=CANONICAL_SECTORS).iloc[0]
        sec_col = _find_column(df, ["Sector", "Sector/service", "industry"])
        if sec_col:
            df = df[df[sec_col].astype(str).str.contains(str(target_sector), case=False, na=False)]

    # 2. Stage/Status filtering if provided
    if "stage" in filters and filters["stage"]:
        stage_col = _find_column(df, ["Deal Stage", "stage"])
        if stage_col:
            df = df[df[stage_col].astype(str).str.contains(str(filters["stage"]), case=False, na=False)]
    if "status" in filters and filters["status"]:
        stat_col = _find_column(df, ["Deal Status", "Execution Status", "status"])
        if stat_col:
            df = df[df[stat_col].astype(str).str.contains(str(filters["status"]), case=False, na=False)]

    # 3. Date filtering
    date_col = _find_column(df, ["Tentative Close Date", "Probable Start Date", "Close Date (A)", "Date of PO/LOI"])
    if date_col:
        df = _apply_date_filter(df, date_col, filters.get("date_from"), filters.get("date_to"))

    if len(df) == 0:
        return {
            "metric": metric,
            "board": board_label,
            "result": 0,
            "usable_records": 0,
            "total_records": total_raw_rows,
            "message": "0 records matched the filter criteria."
        }

    val_col = _find_column(df, ["Masked Deal value", "Amount in Rupees (Excl of GST) (Masked)", "Amount in Rupees (Incl of GST) (Masked)", "value", "amount"])

    # Metric: COUNT
    if metric == "count":
        return {
            "metric": "count",
            "board": board_label,
            "count": len(df),
            "total_board_records": total_raw_rows,
            "caveat": f"Computed from {len(df)} of {total_raw_rows} records."
        }

    # Metric: TOTAL_VALUE
    if metric == "total_value":
        if not val_col:
            return {"error": "Monetary value column not found in schema."}
        usable_df, excluded_cnt, reasons = handle_missing(df, [val_col])
        num_vals = normalize_currency(usable_df[val_col])
        total_val = float(num_vals.sum())
        return {
            "metric": "total_value",
            "board": board_label,
            "total_value_inr": total_val,
            "formatted_inr": f"?{total_val:,.2f}",
            "records_used": len(usable_df),
            "records_excluded": excluded_cnt,
            "caveat": f"Computed from {len(usable_df)} of {len(df)} records; {excluded_cnt} excluded due to missing value data."
        }

    # Metric: AVERAGE_VALUE
    if metric == "average_value":
        if not val_col:
            return {"error": "Monetary value column not found in schema."}
        usable_df, excluded_cnt, reasons = handle_missing(df, [val_col])
        num_vals = normalize_currency(usable_df[val_col])
        avg_val = float(num_vals.mean()) if len(num_vals) > 0 else 0.0
        return {
            "metric": "average_value",
            "board": board_label,
            "average_value_inr": avg_val,
            "formatted_inr": f"?{avg_val:,.2f}",
            "records_used": len(usable_df),
            "records_excluded": excluded_cnt,
            "caveat": f"Computed from {len(usable_df)} of {len(df)} records; {excluded_cnt} excluded due to missing value data."
        }

    # Metric: WIN_RATE (Deals only)
    if metric == "win_rate":
        status_col = _find_column(df, ["Deal Status", "Deal Stage", "status"])
        if not status_col:
            return {"error": "Deal Status column not found for win rate calculation."}
        
        # Consider closed deals: Won and Dead/Lost
        won_mask = df[status_col].astype(str).str.contains("Won|G. Project Won", case=False, na=False)
        dead_mask = df[status_col].astype(str).str.contains("Dead|Lost|L. Project Lost", case=False, na=False)
        closed_deals = df[won_mask | dead_mask]
        
        won_count = int(won_mask.sum())
        closed_count = len(closed_deals)
        win_rate = (won_count / closed_count * 100.0) if closed_count > 0 else 0.0

        return {
            "metric": "win_rate",
            "board": "Deals",
            "win_rate_percent": round(win_rate, 2),
            "won_deals_count": won_count,
            "closed_deals_count": closed_count,
            "open_deals_count": len(df) - closed_count,
            "caveat": f"Win rate is calculated as Won / (Won + Dead) across {closed_count} decided deals ({len(df) - closed_count} open deals excluded from denominator)."
        }

    # Metric: COMPLETION_RATE (Work Orders only)
    if metric == "completion_rate":
        exec_col = _find_column(df, ["Execution Status", "WO Status (billed)", "status"])
        if not exec_col:
            return {"error": "Execution status column not found."}
        
        completed_mask = df[exec_col].astype(str).str.contains("Completed", case=False, na=False)
        completed_count = int(completed_mask.sum())
        total_wo = len(df)
        rate = (completed_count / total_wo * 100.0) if total_wo > 0 else 0.0

        return {
            "metric": "completion_rate",
            "board": "Work Orders",
            "completion_rate_percent": round(rate, 2),
            "completed_count": completed_count,
            "total_work_orders": total_wo,
            "caveat": f"Based on {completed_count} completed orders out of {total_wo} total work orders."
        }

    # Metric: BY_SECTOR_BREAKDOWN
    if metric == "by_sector_breakdown":
        sec_col = _find_column(df, ["Sector", "Sector/service", "industry"])
        if not sec_col:
            return {"error": "Sector column not found in schema."}
        
        if val_col:
            df["_val_temp"] = normalize_currency(df[val_col])
        else:
            df["_val_temp"] = 0.0

        grouped = df.groupby(sec_col).agg(
            count=("item_id" if "item_id" in df.columns else df.columns[0], "count"),
            total_value=("_val_temp", "sum")
        ).reset_index().sort_values(by="total_value", ascending=False)

        null_sectors = int(df[sec_col].isna().sum())
        return {
            "metric": "by_sector_breakdown",
            "board": board_label,
            "sector_breakdown": grouped.to_dict(orient="records"),
            "records_with_missing_sector": null_sectors,
            "caveat": f"{null_sectors} records were missing sector classification and grouped into unassigned." if null_sectors > 0 else "All records mapped to sectors."
        }

    return {"error": f"Unsupported metric: '{metric}'"}

def execute_cross_reference_boards(join_key: str = "sector", analysis_type: str = "sector_comparison", filters: dict | None = None) -> dict:
    wo_df, deals_df = _get_dataframes()
    if wo_df is None or len(wo_df) == 0 or deals_df is None or len(deals_df) == 0:
        return {"error": "Both Work Orders and Deals boards must be populated for cross-referencing."}

    # Cross-reference 1: Won Deals Without Active Work Orders
    if analysis_type == "won_deals_without_work_orders":
        deal_status_col = _find_column(deals_df, ["Deal Status", "Deal Stage"])
        deal_name_col = _find_column(deals_df, ["Deal Name"])
        wo_deal_col = _find_column(wo_df, ["Deal name masked", "Serial #"])

        won_deals = deals_df[deals_df[deal_status_col].astype(str).str.contains("Won|G. Project Won", case=False, na=False)].copy()
        
        # Check matching deal names
        active_wo_deals = set(wo_df[wo_deal_col].dropna().astype(str).str.strip().str.lower())
        
        unmatched_won = []
        for _, row in won_deals.iterrows():
            d_name = str(row.get(deal_name_col, "")).strip()
            if d_name.lower() not in active_wo_deals:
                unmatched_won.append({
                    "deal_name": d_name,
                    "owner": row.get(_find_column(deals_df, ["Owner code"]), "N/A"),
                    "sector": row.get(_find_column(deals_df, ["Sector/service"]), "N/A"),
                    "value": row.get(_find_column(deals_df, ["Masked Deal value"]), "N/A")
                })

        return {
            "analysis_type": "won_deals_without_work_orders",
            "total_won_deals": len(won_deals),
            "won_deals_with_work_orders": len(won_deals) - len(unmatched_won),
            "won_deals_without_work_orders_count": len(unmatched_won),
            "unmatched_won_deals_sample": unmatched_won[:20],
            "caveat": f"Cross-referenced on deal identifiers; {len(unmatched_won)} won deals have no matching record in Work Orders."
        }

    # Cross-reference 2: Sector Comparison (Sectors with high WO but low won deals, or vice versa)
    sec_wo_col = _find_column(wo_df, ["Sector", "sector"])
    sec_deal_col = _find_column(deals_df, ["Sector/service", "sector"])
    deal_stat_col = _find_column(deals_df, ["Deal Status", "Deal Stage"])
    
    won_deals = deals_df[deals_df[deal_stat_col].astype(str).str.contains("Won|G. Project Won", case=False, na=False)]
    
    wo_by_sector = wo_df.groupby(sec_wo_col).size().rename("work_orders_count")
    deals_by_sector = won_deals.groupby(sec_deal_col).size().rename("won_deals_count")
    
    comparison = pd.concat([wo_by_sector, deals_by_sector], axis=1).fillna(0).astype(int)
    comparison["wo_to_deal_ratio"] = (comparison["work_orders_count"] / comparison["won_deals_count"].replace(0, 0.5)).round(2)
    comparison = comparison.sort_values(by="work_orders_count", ascending=False).reset_index()
    comparison.rename(columns={"index": "sector"}, inplace=True)

    return {
        "analysis_type": "sector_comparison",
        "comparison_table": comparison.to_dict(orient="records"),
        "top_work_orders_low_deals": comparison[comparison["work_orders_count"] > comparison["won_deals_count"]].head(5).to_dict(orient="records"),
        "caveat": "Sector matching is based on canonical mapped sectors; 0 won deals represented with 0.5 denominator for ratio ranking."
    }

def execute_get_data_quality_report(board: str = "both") -> dict:
    wo_df, deals_df = _get_dataframes()
    
    reports = {}
    if board in ("work_orders", "both") and wo_df is not None:
        reports["work_orders"] = data_quality_report(wo_df, "Work Orders")
    if board in ("deals", "both") and deals_df is not None:
        reports["deals"] = data_quality_report(deals_df, "Deals")
        
    return reports

def execute_refresh_data() -> dict:
    cache = refresh_cache(force=True)
    wo_cnt = len(cache.get("work_orders_df", []))
    deals_cnt = len(cache.get("deals_df", []))
    return {
        "status": "refreshed",
        "work_orders_records": wo_cnt,
        "deals_records": deals_cnt,
        "is_connected_live": cache.get("is_connected_live", False),
        "status_message": cache.get("status_message", "Refreshed successfully")
    }

def dispatch_tool_call(tool_name: str, tool_args: dict) -> dict:
    """Dispatches Claude tool calls to appropriate execution functions with error insulation."""
    try:
        if tool_name == "get_work_orders":
            return execute_get_work_orders(**tool_args)
        elif tool_name == "get_deals":
            return execute_get_deals(**tool_args)
        elif tool_name == "compute_metric":
            return execute_compute_metric(**tool_args)
        elif tool_name == "cross_reference_boards":
            return execute_cross_reference_boards(**tool_args)
        elif tool_name == "get_data_quality_report":
            return execute_get_data_quality_report(**tool_args)
        elif tool_name == "refresh_data":
            return execute_refresh_data()
        elif tool_name == "generate_leadership_update":
            from src.insights import generate_leadership_update
            period = tool_args.get("period", "last_30_days")
            md = generate_leadership_update(period)
            return {"status": "success", "leadership_update_markdown": md}
        else:
            return {"error": f"Unknown tool name: '{tool_name}'"}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}' with args {tool_args}: {e}", exc_info=True)
        return {"error": f"Tool execution failed: {str(e)}"}
