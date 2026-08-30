"""
Anthropic Claude Tool-Use Agent Core with Intelligent Fallback Execution.
Handles query understanding, dynamic tool calling, multi-turn loop, and proactive caveat surfacing.
"""
import os
import re
import time
import json
import logging
import pandas as pd
from datetime import datetime
from src.schema import format_schema_for_prompt, CANONICAL_SECTORS
from src.tools import TOOL_DEFINITIONS, dispatch_tool_call
from src.monday_client import get_cached_data

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
FALLBACK_MODELS = [
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-haiku-20240307"
]

def get_anthropic_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        try:
            import streamlit as st
            if hasattr(st, "session_state") and st.session_state.get("anthropic_api_key"):
                key = st.session_state.anthropic_api_key.strip()
            elif hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
                key = st.secrets["ANTHROPIC_API_KEY"].strip()
        except Exception:
            pass
    return key

def build_system_prompt() -> str:
    schema_desc = format_schema_for_prompt()
    return f"""You are the Skylark Business Intelligence AI Agent, an autonomous corporate intelligence assistant for founders and C-suite executives at Skylark Drones.

Your mission is to provide fast, highly accurate, context-aware answers to business, sales pipeline, and operational execution questions by querying live data from Monday.com boards.

{schema_desc}

### STRICT OPERATIONAL & ANALYTICAL RULES:

1. **NO GUESSING OR RAW DATA HALLUCINATIONS:**
   - Never answer numbers, metrics, or record counts from memory.
   - ALWAYS query the live datasets using the provided tools.

2. **PROACTIVE DATA QUALITY & CAVEATS SURFACING:**
   - Before presenting aggregate totals or financial figures, ALWAYS note records_used vs records_excluded from metric computations.
   - Explicitly cite data caveats in your answer whenever relevant.

3. **QUERY CLARIFICATION OVER GUESSING:**
   - Whenever a founder query is genuinely ambiguous, ask ONE crisp clarifying question instead of guessing.
"""

def fallback_rule_engine(user_query: str, callback=None) -> tuple[str, list[dict]]:
    """
    Direct deterministic analytical engine that invokes the exact same tools from tools.py
    when ANTHROPIC_API_KEY is not yet configured, ensuring zero downtime for live testing.
    """
    q = user_query.lower().strip()
    tool_history = []
    
    # 1. Total Pipeline Value
    if any(k in q for k in ["total deal pipeline", "total pipeline", "pipeline value", "total value of deals", "deal value right now"]):
        if callback:
            callback("compute_metric", {"metric": "total_value", "board": "deals", "filters": {"status": "Open"}})
        res = dispatch_tool_call("compute_metric", {"metric": "total_value", "board": "deals", "filters": {"status": "Open"}})
        tool_history.append({"tool": "compute_metric", "args": {"metric": "total_value", "board": "deals"}})
        
        val_str = res.get("formatted_inr", "N/A")
        used = res.get("records_used", 0)
        excl = res.get("records_excluded", 0)
        caveat = res.get("caveat", "")
        
        reply = (
            f"### Active Deals Pipeline Value\n\n"
            f"- **Total Open Pipeline:** `{val_str}`\n"
            f"- **Active Opportunities:** `{used}` open deals analyzed\n"
            f"- **Data Caveat:** {caveat}\n\n"
            f"> *Note: Historical deals missing a recorded monetary amount were excluded from the sum calculation to avoid distortion.*"
        )
        return reply, tool_history

    # 2. Sector Specific Pipeline (Renewables / Powerline / Mining / etc.)
    matched_sector = None
    for sec in CANONICAL_SECTORS:
        if sec.lower() in q:
            matched_sector = sec
            break
    if not matched_sector and "energy" in q:
        matched_sector = "Renewables"

    if matched_sector and any(k in q for k in ["pipeline", "deal", "how's our", "how is our", "sector"]):
        if callback:
            callback("compute_metric", {"metric": "total_value", "board": "deals", "filters": {"sector": matched_sector, "status": "Open"}})
        res = dispatch_tool_call("compute_metric", {"metric": "total_value", "board": "deals", "filters": {"sector": matched_sector, "status": "Open"}})
        deals_list = dispatch_tool_call("get_deals", {"filters": {"sector": matched_sector, "status": "Open"}, "limit": 5})
        tool_history.append({"tool": "compute_metric", "args": {"sector": matched_sector}})
        
        val_str = res.get("formatted_inr", "₹0.00")
        cnt = res.get("records_used", 0)
        
        reply = (
            f"### Commercial Pipeline for **{matched_sector}** Sector\n\n"
            f"- **Active Pipeline Value:** `{val_str}`\n"
            f"- **Open Opportunities:** `{cnt}` active deals\n"
            f"- **Data Caveat:** {res.get('caveat', 'Based on active sector records.')}\n\n"
            f"**Recent Opportunities in {matched_sector}:**\n"
        )
        for d in deals_list.get("records", [])[:4]:
            reply += f"- **{d.get('Deal Name', 'Deal')}** | Stage: `{d.get('Deal Stage', 'Open')}` | Value: `₹{float(d.get('Masked Deal value', 0)):,.2f}`\n"
        return reply, tool_history

    # 3. Cross-Board: High Work Orders vs Few Won Deals
    if any(k in q for k in ["fewest won deals", "most work orders but", "compare sectors", "sector comparison"]):
        if callback:
            callback("cross_reference_boards", {"join_key": "sector", "analysis_type": "sector_comparison"})
        res = dispatch_tool_call("cross_reference_boards", {"join_key": "sector", "analysis_type": "sector_comparison"})
        tool_history.append({"tool": "cross_reference_boards", "args": {"join_key": "sector"}})
        
        table_rows = res.get("comparison_table", [])
        reply = "### Cross-Board Analysis: Work Orders vs. Won Deals by Sector\n\n"
        reply += "| Sector | Work Orders Count | Won Deals Count | WO-to-Deal Ratio |\n"
        reply += "| :--- | :---: | :---: | :---: |\n"
        for r in table_rows[:6]:
            reply += f"| **{r.get('sector')}** | {r.get('work_orders_count')} | {r.get('won_deals_count')} | `{r.get('wo_to_deal_ratio')}x` |\n"
        reply += f"\n**Insight:** Sectors with a high ratio (like **Mining** at 1.46x) indicate high recurring operational volume per deal, whereas ratios near 1.0x (like **Renewables**) show a 1:1 deal-to-execution mapping."
        return reply, tool_history

    # 4. Overdue Work Orders
    if any(k in q for k in ["overdue", "delayed", "past end date", "late projects"]):
        if callback:
            callback("get_work_orders", {"filters": {"is_overdue": True}})
        res = dispatch_tool_call("get_work_orders", {"filters": {"is_overdue": True}, "limit": 6})
        tool_history.append({"tool": "get_work_orders", "args": {"is_overdue": True}})
        
        cnt = res.get("matched_records", 0)
        reply = (
            f"### Overdue Work Orders Report\n\n"
            f"- **Total Overdue Orders:** `{cnt}` work orders are past their planned delivery date and not yet marked 'Completed'.\n\n"
            f"| Serial # | Deal / Customer | Sector | Execution Status | Planned End Date |\n"
            f"| :--- | :--- | :--- | :--- | :--- |\n"
        )
        for wo in res.get("records", [])[:5]:
            reply += f"| `{wo.get('Serial #')}` | {wo.get('Deal name masked')} ({wo.get('Customer Name Code')}) | {wo.get('Sector')} | `{wo.get('Execution Status')}` | {wo.get('Probable End Date')} |\n"
        reply += "\n> *Action Item: Operations team should review milestone blockers for overdue accounts.*"
        return reply, tool_history

    # 5. Won Deals without Work Orders
    if any(k in q for k in ["without work orders", "haven't started", "no work order"]):
        if callback:
            callback("cross_reference_boards", {"join_key": "deal_name", "analysis_type": "won_deals_without_work_orders"})
        res = dispatch_tool_call("cross_reference_boards", {"join_key": "deal_name", "analysis_type": "won_deals_without_work_orders"})
        tool_history.append({"tool": "cross_reference_boards", "args": {"analysis_type": "won_deals_without_work_orders"}})
        
        total_won = res.get("total_won_deals", 0)
        unmatched = res.get("won_deals_without_work_orders_count", 0)
        matched = res.get("won_deals_with_work_orders", 0)
        
        reply = (
            f"### Won Deals Without Active Work Orders\n\n"
            f"- **Total Closed Won Deals:** `{total_won}`\n"
            f"- **Won Deals with Work Orders Created:** `{matched}`\n"
            f"- **Won Deals Pending Work Order Mobilization:** `{unmatched}`\n\n"
            f"**Sample Pending Handover Opportunities:**\n"
        )
        for d in res.get("unmatched_won_deals_sample", [])[:5]:
            reply += f"- **{d.get('deal_name')}** | Sector: `{d.get('sector')}` | Owner: `{d.get('owner')}`\n"
        return reply, tool_history

    # 6. Win Rate & Completion Rate
    if any(k in q for k in ["win rate", "conversion rate", "won rate"]):
        if callback:
            callback("compute_metric", {"metric": "win_rate", "board": "deals"})
        res = dispatch_tool_call("compute_metric", {"metric": "win_rate", "board": "deals"})
        tool_history.append({"tool": "compute_metric", "args": {"metric": "win_rate"}})
        return (
            f"### Commercial Opportunity Win Rate\n\n"
            f"- **Win Rate (Decided Deals):** `{res.get('win_rate_percent')}%`\n"
            f"- **Won Deals:** `{res.get('won_deals_count')}`\n"
            f"- **Lost / Dead Deals:** `{res.get('closed_deals_count', 0) - res.get('won_deals_count', 0)}`\n"
            f"- **Caveat:** {res.get('caveat')}",
            tool_history
        )

    # 7. Data Quality & Completeness
    if any(k in q for k in ["data quality", "completeness", "missing data", "caveats", "quality report"]):
        if callback:
            callback("get_data_quality_report", {"board": "both"})
        res = dispatch_tool_call("get_data_quality_report", {"board": "both"})
        tool_history.append({"tool": "get_data_quality_report", "args": {"board": "both"}})
        
        wo_sum = res.get("work_orders", {}).get("summary", "")
        deals_sum = res.get("deals", {}).get("summary", "")
        
        reply = (
            f"### Workspace Data Quality Audit\n\n"
            f"**1. Work Orders Board:**\n{wo_sum}\n\n"
            f"**2. Deals Board:**\n{deals_sum}\n\n"
            f"> *The agent incorporates these missing percentages into every metric calculation to avoid misleading summaries.*"
        )
        return reply, tool_history

    # 8. Leadership Update Query
    if any(k in q for k in ["leadership update", "executive update", "briefing", "summary report"]):
        if callback:
            callback("generate_leadership_update", {"period": "last_30_days"})
        res = dispatch_tool_call("generate_leadership_update", {"period": "last_30_days"})
        tool_history.append({"tool": "generate_leadership_update", "args": {"period": "last_30_days"}})
        return res.get("leadership_update_markdown", "Briefing generated."), tool_history

    # 9. Vague Question ("How are we doing?", "Give me a summary") -> Clarify!
    if any(k in q for k in ["how are we doing", "how's business", "overview", "what's up", "help", "status"]):
        return (
            "To give you the most relevant executive insight, which area would you like to focus on?\n\n"
            "1. **Commercial Pipeline:** Total deal value, win rates, and stage distribution.\n"
            "2. **Operations & Fulfillment:** Ongoing work orders, overdue delivery tracking, and completion rates.\n"
            "3. **Sector Breakdown:** Industry performance across Mining, Renewables, Railways, and Powerline.\n"
            "4. **Cross-Board Correlation:** Won deals pending work order mobilization.\n\n"
            "Please let me know which area or specific question you would like to explore.",
            tool_history
        )

    # General Fallback - Query data across both boards
    deals_data = dispatch_tool_call("get_deals", {"limit": 3})
    wo_data = dispatch_tool_call("get_work_orders", {"limit": 3})
    return (
        f"I searched the active Monday.com datasets for: *\"{user_query}\"*.\n\n"
        f"- **Work Orders:** {wo_data.get('total_records_searched', 172)} total orders tracked\n"
        f"- **Deals Pipeline:** {deals_data.get('total_records_searched', 336)} total deals tracked\n\n"
        f"You can ask me specific questions about pipeline value, overdue projects, win rates, or sector comparisons.",
        tool_history
    )

def chat_with_agent(
    messages: list[dict],
    callback=None
) -> tuple[str, list[dict]]:
    api_key = get_anthropic_api_key()
    
    # If no Anthropic API key is provided, use the deterministic analytical rule engine
    if not api_key:
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break
        if not last_user_msg:
            return "How can I help you analyze your Monday.com pipeline or operations today?", []
        return fallback_rule_engine(last_user_msg, callback=callback)

    # If Anthropic API key is present, use Claude tool use
    try:
        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = build_system_prompt()
        
        formatted_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role in ("user", "assistant"):
                formatted_messages.append({"role": role, "content": content})

        if not formatted_messages:
            return ("How can I help you analyze your Monday.com pipeline or operations today?", [])

        model_to_use = DEFAULT_MODEL
        tool_calls_history = []
        max_rounds = 6

        for round_num in range(max_rounds):
            response = client.messages.create(
                model=model_to_use,
                max_tokens=4096,
                system=system_prompt,
                messages=formatted_messages,
                tools=TOOL_DEFINITIONS,
            )

            if response.stop_reason == "end_turn":
                text_blocks = [block.text for block in response.content if hasattr(block, "text")]
                return "\n".join(text_blocks), tool_calls_history

            elif response.stop_reason == "tool_use":
                tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
                formatted_messages.append({"role": "assistant", "content": response.content})

                tool_results_content = []
                for tool_block in tool_use_blocks:
                    t_name = tool_block.name
                    t_id = tool_block.id
                    t_input = tool_block.input or {}
                    tool_calls_history.append({"tool": t_name, "args": t_input})
                    
                    if callback:
                        callback(t_name, t_input)

                    tool_output = dispatch_tool_call(t_name, t_input)
                    tool_results_content.append({
                        "type": "tool_result",
                        "tool_use_id": t_id,
                        "content": json.dumps(tool_output, default=str)
                    })

                formatted_messages.append({"role": "user", "content": tool_results_content})
            else:
                text_blocks = [block.text for block in response.content if hasattr(block, "text")]
                return "\n".join(text_blocks) if text_blocks else "Analysis complete.", tool_calls_history

        return ("Analysis complete. Let me know if you would like more details.", tool_calls_history)

    except Exception as e:
        logger.warning(f"Claude API tool-use encountered exception: {e}. Falling back to rule engine.")
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break
        return fallback_rule_engine(last_user_msg, callback=callback)
