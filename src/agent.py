"""
Anthropic Claude Tool-Use Agent Core.
Handles query understanding, dynamic tool calling, multi-turn loop, and proactive caveat surfacing.
"""
import os
import time
import json
import logging
from typing import Generator, Any
import anthropic
from src.schema import format_schema_for_prompt
from src.tools import TOOL_DEFINITIONS, dispatch_tool_call
from src.monday_client import get_cached_data

logger = logging.getLogger(__name__)

# Default to Sonnet 3.7 or 3.5
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
FALLBACK_MODELS = [
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-haiku-20240307"
]

def get_anthropic_api_key() -> str:
    """Retrieves Anthropic API key from env or Streamlit secrets."""
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
                key = st.secrets["ANTHROPIC_API_KEY"].strip()
        except Exception:
            pass
    return key

def build_system_prompt() -> str:
    """
    Constructs the dynamic system prompt with current live schema and strict analytical rules.
    """
    schema_desc = format_schema_for_prompt()
    
    return f"""You are the Skylark Business Intelligence AI Agent, an autonomous corporate intelligence assistant for founders and C-suite executives at Skylark Drones.

Your mission is to provide fast, highly accurate, context-aware answers to business, sales pipeline, and operational execution questions by querying live data from Monday.com boards.

{schema_desc}

### STRICT OPERATIONAL & ANALYTICAL RULES:

1. **NO GUESSING OR RAW DATA HALLUCINATIONS:**
   - Never answer numbers, metrics, or record counts from memory.
   - ALWAYS query the live datasets using the provided tools (`get_work_orders`, `get_deals`, `compute_metric`, `cross_reference_boards`, `get_data_quality_report`, `generate_leadership_update`).

2. **PROACTIVE DATA QUALITY & CAVEATS SURFACING:**
   - Before presenting aggregate totals or financial figures for the first time or when computing metrics, ALWAYS call `get_data_quality_report` or note the `records_used` vs `records_excluded` from metric computations.
   - Explicitly cite data caveats in your answer whenever relevant (e.g., "Computed from 42 of 51 records; 9 records were excluded due to missing sector information" or "Note: 18% of Work Orders have unpopulated End Dates").

3. **QUERY CLARIFICATION OVER GUESSING:**
   - Whenever a founder query is genuinely ambiguous, ask ONE crisp clarifying question instead of guessing blindly:
     a. **Vague / Open-ended Questions** (e.g. "How are we doing?"): Ask the user which dimension they wish to focus on (e.g., "Would you like a snapshot of our active sales pipeline, operational delivery status, or sectoral performance?").
     b. **Relative Time Anchors Without Specific Dates** (e.g. "this quarter", "recently"): Confirm the specific calendar dates or quarter anchor (e.g. Q1 Jan-Mar vs Q3 Jul-Sep).
     c. **Ambiguous Metric Terms** (e.g. "pipeline value"): Clarify whether they mean total unweighted opportunity value or probability-weighted pipeline value.
     d. **Unrecognized Sector / Client Names**: Ask to confirm if they meant a specific canonical industry sector.

4. **CROSS-BOARD SYNTHESIS:**
   - For questions spanning commercial pipeline and operational fulfillment (e.g. "Which won deals haven't started work orders yet?" or "Which sectors have high work order volume but low won deals?"), use `cross_reference_boards` to bridge both datasets.

5. **EXECUTIVE COMMUNICATION STYLE:**
   - Deliver clear, crisp, executive-grade answers using markdown tables, bullet points, and bold metric callouts.
   - State the primary metric first, followed by breakdown context and caveats.
"""

def chat_with_agent(
    messages: list[dict],
    callback=None
) -> tuple[str, list[dict]]:
    """
    Executes the multi-step Claude tool use loop with error resilience and max 6 turns per round.
    Returns (final_response_text, list_of_tool_calls_executed).
    """
    api_key = get_anthropic_api_key()
    if not api_key:
        return (
            "⚠️ **Anthropic API Key Not Found**\n\n"
            "Please configure `ANTHROPIC_API_KEY` in your `.env` file or Streamlit Cloud Secrets (`.streamlit/secrets.toml`).",
            []
        )

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = build_system_prompt()
    
    # Clean messages for Anthropic API
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
        logger.info(f"Starting agent tool-use round {round_num + 1}/{max_rounds}...")
        
        # Call Anthropic API with retry
        response = None
        for attempt in range(2):
            try:
                response = client.messages.create(
                    model=model_to_use,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=formatted_messages,
                    tools=TOOL_DEFINITIONS,
                )
                break
            except anthropic.APIStatusError as status_err:
                logger.warning(f"Anthropic API status error on attempt {attempt+1}: {status_err}")
                if attempt == 0 and len(FALLBACK_MODELS) > 1:
                    model_to_use = FALLBACK_MODELS[1]
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"Anthropic client error: {e}")
                if attempt == 1:
                    return (
                        f"⚠️ **AI Service Error:** Failed to communicate with Claude API ({str(e)}). Please check your API key and connection.",
                        tool_calls_history
                    )
                time.sleep(1.0)

        if not response:
            return ("⚠️ Temporary error reaching AI service. Please try your question again.", tool_calls_history)

        # Check stop reason
        if response.stop_reason == "end_turn":
            text_blocks = [block.text for block in response.content if hasattr(block, "text")]
            final_text = "\n".join(text_blocks)
            return final_text, tool_calls_history

        elif response.stop_reason == "tool_use":
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            
            formatted_messages.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results_content = []
            for tool_block in tool_use_blocks:
                t_name = tool_block.name
                t_id = tool_block.id
                t_input = tool_block.input or {}
                
                tool_calls_history.append({"tool": t_name, "args": t_input})
                
                if callback:
                    callback(t_name, t_input)

                logger.info(f"Executing tool '{t_name}' with arguments: {t_input}")
                tool_output = dispatch_tool_call(t_name, t_input)
                
                tool_results_content.append({
                    "type": "tool_result",
                    "tool_use_id": t_id,
                    "content": json.dumps(tool_output, default=str)
                })

            formatted_messages.append({
                "role": "user",
                "content": tool_results_content
            })

        else:
            text_blocks = [block.text for block in response.content if hasattr(block, "text")]
            return "\n".join(text_blocks) if text_blocks else "Here is what I found based on the latest records.", tool_calls_history

    return (
        "*(Query completed maximum analysis steps)*\n\nBased on the data retrieved above, let me know if you would like me to drill into any specific area further.",
        tool_calls_history
    )
