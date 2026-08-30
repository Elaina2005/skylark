"""
Skylark BI Agent - Streamlit Application.
Conversational Business Intelligence assistant powered by Claude tool use and live Monday.com data.
"""
import os
import time
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load local environment if present
load_dotenv()

from src.monday_client import (
    refresh_cache,
    get_cached_data,
    MondayAuthError,
    MondayUnavailableError
)
from src.agent import chat_with_agent
from src.insights import generate_leadership_update

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Set Page Config
st.set_page_config(
    page_title="Skylark BI Agent | Executive Intelligence",
    page_icon="??",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for executive look & feel
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .metric-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-live {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .badge-cached {
        background-color: #e2e3e5;
        color: #383d41;
        border: 1px solid #d6d8db;
    }
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 0.75rem;
    }
    .quick-query-btn {
        margin-right: 5px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "leadership_markdown" not in st.session_state:
    st.session_state.leadership_markdown = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# Sidebar
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=150&auto=format&fit=crop&q=60", width=60)
    st.title("Skylark BI Agent")
    st.caption("Founder-Level Business Intelligence for Monday.com")
    st.divider()

    # Connection Status
    st.subheader("?? Connection Status")
    try:
        cache_data = get_cached_data()
        is_live = cache_data.get("is_connected_live", False)
        status_msg = cache_data.get("status_message", "Connected")
        last_refreshed = cache_data.get("last_refreshed_at")
        time_str = last_refreshed.strftime("%H:%M:%S UTC") if last_refreshed else "Never"

        if is_live:
            st.success(f"?? **Live Monday.com API**\n\n{status_msg}")
        else:
            st.info(f"?? **Sandbox Reference Mode**\n\n{status_msg}")
        
        st.caption(f"?? **Last Refreshed:** `{time_str}`")

    except MondayAuthError as auth_err:
        st.error(f"?? **Authentication Error**\n\n{str(auth_err)}")
    except MondayUnavailableError as unav_err:
        st.warning(f"?? **API Unavailable**\n\n{str(unav_err)}")
    except Exception as ex:
        st.error(f"?? **Connection Error:** {ex}")

    # Refresh Button
    if st.button("?? Refresh Data Cache", use_container_width=True):
        with st.spinner("Fetching latest updates from Monday.com..."):
            try:
                refresh_cache(force=True)
                st.toast("Data cache successfully refreshed!", icon="?")
                st.rerun()
            except Exception as e:
                st.error(f"Refresh failed: {e}")

    st.divider()

    # Leadership Update Action
    st.subheader("?? Executive Briefings")
    if st.button("Generate Leadership Update", type="primary", use_container_width=True):
        with st.spinner("Synthesizing live pipeline & operations briefing..."):
            try:
                update_md = generate_leadership_update(period="last_30_days")
                st.session_state.leadership_markdown = update_md
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": update_md
                })
                st.rerun()
            except Exception as e:
                st.error(f"Could not generate briefing: {e}")

    if st.session_state.leadership_markdown:
        today_slug = datetime.now().strftime("%Y_%m_%d")
        st.download_button(
            label="?? Download Briefing (.md)",
            data=st.session_state.leadership_markdown,
            file_name=f"leadership_update_{today_slug}.md",
            mime="text/markdown",
            use_container_width=True
        )

    st.divider()
    with st.expander("?? Connection Settings & Keys", expanded=False):
        st.markdown(
            "**API Credentials**\n"
            "- Set `MONDAY_API_TOKEN` to query live boards.\n"
            "- Set `ANTHROPIC_API_KEY` for Claude tool use.\n\n"
            "*Credentials are loaded securely from `.env` or Streamlit Secrets.*"
        )
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.leadership_markdown = None
            st.rerun()

# Initial Data Load & Welcome Banner
if not st.session_state.initialized:
    try:
        cache_data = refresh_cache(force=False)
        wo_len = len(cache_data.get("work_orders_df", []))
        deals_len = len(cache_data.get("deals_df", []))
        
        welcome_text = (
            f"?? **Welcome to Skylark BI Agent!**\n\n"
            f"I am connected to your live Monday.com workspace:\n"
            f"- **Work Orders:** `{wo_len}` records\n"
            f"- **Deals Pipeline:** `{deals_len}` records\n\n"
            f"Ask me anything about pipeline value, win rates, sectoral performance, overdue projects, or cross-board insights."
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_text
        })
        st.session_state.initialized = True
    except MondayAuthError as e:
        st.error(f"### ?? Monday.com Authentication Required\n{str(e)}")
        st.info("?? **Quick Start:** You can add `MONDAY_API_TOKEN=your_token` and `ANTHROPIC_API_KEY=your_key` to a `.env` file.")
    except Exception as e:
        st.warning(f"Initialization notice: {e}")

# Header
st.header("?? Skylark Business Intelligence Agent")
st.caption("Ask questions across sales opportunities, deal conversions, active work orders, and operational delivery metrics.")

# Quick Sample Query Pills
st.markdown("**Suggested Founder Queries:**")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("?? What's our total deal pipeline value right now?", use_container_width=True):
        st.session_state.selected_query = "What's our total deal pipeline value right now?"
with col2:
    if st.button("? How's our pipeline looking for renewables/powerline?", use_container_width=True):
        st.session_state.selected_query = "How's our pipeline looking for the renewables and powerline sectors?"
with col3:
    if st.button("?? How many work orders are overdue?", use_container_width=True):
        st.session_state.selected_query = "How many work orders are overdue right now?"

col4, col5, col6 = st.columns(3)
with col4:
    if st.button("?? Won deals with no work orders yet?", use_container_width=True):
        st.session_state.selected_query = "Which won deals haven't started work orders yet?"
with col5:
    if st.button("?? Sectors with high work orders but low won deals?", use_container_width=True):
        st.session_state.selected_query = "Which sectors have the most work orders but the fewest won deals?"
with col6:
    if st.button("?? Show Data Quality Report", use_container_width=True):
        st.session_state.selected_query = "What is the data quality and completeness across our Work Orders and Deals boards?"

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Chat Input
user_input = st.chat_input("Ask a business intelligence question...")
if "selected_query" in st.session_state and st.session_state.selected_query:
    user_input = st.session_state.selected_query
    st.session_state.selected_query = None

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate assistant response
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        
        def tool_status_callback(tool_name, tool_input):
            labels = {
                "get_work_orders": f"Querying Work Orders (filters: {tool_input.get('filters', {})})...",
                "get_deals": f"Querying Deals Pipeline (filters: {tool_input.get('filters', {})})...",
                "compute_metric": f"Computing Metric '{tool_input.get('metric')}' on {tool_input.get('board')}...",
                "cross_reference_boards": f"Cross-referencing Work Orders and Deals on {tool_input.get('join_key')}...",
                "get_data_quality_report": f"Inspecting Data Quality Report for {tool_input.get('board')}...",
                "generate_leadership_update": "Generating Executive Leadership Briefing...",
                "refresh_data": "Refreshing data cache from Monday.com..."
            }
            label = labels.get(tool_name, f"Executing {tool_name}...")
            with status_placeholder.status(f"?? {label}", expanded=False):
                st.write(f"Tool Input: `{tool_input}`")

        with st.spinner("Analyzing business data..."):
            reply, tool_history = chat_with_agent(
                messages=st.session_state.messages,
                callback=tool_status_callback
            )
            status_placeholder.empty()
            st.markdown(reply)

        # Save to history
        st.session_state.messages.append({"role": "assistant", "content": reply})
