"""
Monday.com GraphQL API Integration Layer.
Handles authentication, cursor-based pagination, rate-limits, retries, and in-memory caching.
"""
import os
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from src.normalizer import raw_items_to_dataframe, normalize_dates, normalize_currency, normalize_text_field
from src.schema import WORK_ORDERS_BOARD_ID, DEALS_BOARD_ID

logger = logging.getLogger(__name__)

MONDAY_API_URL = "https://api.monday.com/v2"

class MondayAuthError(Exception):
    """Raised when authentication with Monday.com fails (401, 403, or missing token)."""
    pass

class MondayUnavailableError(Exception):
    """Raised when Monday.com API is unreachable or returns persistent 5xx/network errors."""
    pass

# Module-level in-memory cache
_CACHE = {
    "work_orders_df": None,
    "deals_df": None,
    "work_orders_columns": None,
    "deals_columns": None,
    "last_refreshed_at": None,
    "is_connected_live": False,
    "status_message": "Not initialized"
}

def get_api_token() -> str:
    """Retrieves the Monday.com API token from environment variable or Streamlit secrets."""
    token = os.getenv("MONDAY_API_TOKEN", "").strip()
    if not token:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "MONDAY_API_TOKEN" in st.secrets:
                token = st.secrets["MONDAY_API_TOKEN"].strip()
        except Exception:
            pass
    return token

def execute_graphql_query(query: str, variables: dict | None = None, max_retries: int = 3) -> dict:
    """
    Executes a GraphQL query against Monday.com API v2 with exponential backoff and rate-limit handling.
    """
    token = get_api_token()
    if not token:
        raise MondayAuthError(
            "Monday.com API Token is missing. Please set the 'MONDAY_API_TOKEN' environment variable "
            "or configure it in your Streamlit secrets (.streamlit/secrets.toml)."
        )

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "API-Version": "2024-01"
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    backoff = 1.0
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                MONDAY_API_URL,
                json=payload,
                headers=headers,
                timeout=25
            )

            # Check for Rate Limit (HTTP 429)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", int(backoff * 2)))
                logger.warning(f"Rate limited by Monday.com (429). Retrying in {retry_after}s...")
                time.sleep(retry_after)
                backoff *= 2
                continue

            # Check for Auth Errors
            if response.status_code in (401, 403):
                error_body = response.text
                logger.error(f"Monday.com Authentication failed ({response.status_code}): {error_body}")
                raise MondayAuthError(
                    f"Invalid or unauthorized MONDAY_API_TOKEN (HTTP {response.status_code}). "
                    "Please verify that your personal API token is active in Monday.com Admin/Developer settings."
                )

            # Check for Server / Gateway Errors
            if response.status_code in (500, 502, 503, 504):
                logger.warning(f"Server error from Monday.com (HTTP {response.status_code}) on attempt {attempt}/{max_retries}.")
                time.sleep(backoff)
                backoff *= 2
                continue

            response.raise_for_status()
            data = response.json()

            if "errors" in data and data["errors"]:
                error_msgs = [e.get("message", "Unknown GraphQL error") for e in data["errors"]]
                # If error is auth related inside GraphQL response
                if any("auth" in m.lower() or "token" in m.lower() or "permission" in m.lower() for m in error_msgs):
                    raise MondayAuthError(f"Monday.com GraphQL Permission Error: {'; '.join(error_msgs)}")
                raise MondayUnavailableError(f"Monday.com GraphQL error: {'; '.join(error_msgs)}")

            return data.get("data", {})

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as net_err:
            logger.warning(f"Network error connecting to Monday.com on attempt {attempt}/{max_retries}: {net_err}")
            last_exception = net_err
            time.sleep(backoff)
            backoff *= 2
        except MondayAuthError:
            raise
        except Exception as ex:
            last_exception = ex
            logger.warning(f"Unexpected error querying Monday.com on attempt {attempt}/{max_retries}: {ex}")
            time.sleep(backoff)
            backoff *= 2

    raise MondayUnavailableError(
        f"Monday.com API is temporarily unavailable after {max_retries} retry attempts. "
        f"Underlying error: {last_exception}"
    )

def get_board_columns(board_id: str) -> list[dict]:
    """
    Fetches column metadata for a given board.
    """
    query = """
    query ($board_ids: [ID!]) {
        boards(ids: $board_ids) {
            id
            name
            columns {
                id
                title
                type
                settings_str
            }
        }
    }
    """
    try:
        data = execute_graphql_query(query, variables={"board_ids": [str(board_id)]})
        boards = data.get("boards", [])
        if boards:
            return boards[0].get("columns", [])
        return []
    except Exception as e:
        logger.warning(f"Failed to fetch live board columns for {board_id}: {e}")
        return []

def get_all_items(board_id: str) -> list[dict]:
    """
    Fetches all items from a board with complete cursor-based pagination (limit 100 per page).
    """
    all_items = []
    cursor = None
    
    # Query for the first page
    first_page_query = """
    query ($board_ids: [ID!]) {
        boards(ids: $board_ids) {
            items_page(limit: 100) {
                cursor
                items {
                    id
                    name
                    column_values {
                        id
                        text
                        value
                        type
                    }
                }
            }
        }
    }
    """
    
    # Query for subsequent pages using cursor
    next_page_query = """
    query ($cursor: String!) {
        next_items_page(cursor: $cursor, limit: 100) {
            cursor
            items {
                id
                name
                column_values {
                    id
                    text
                    value
                    type
                }
            }
        }
    }
    """

    # First page fetch
    data = execute_graphql_query(first_page_query, variables={"board_ids": [str(board_id)]})
    boards = data.get("boards", [])
    if not boards:
        return []

    items_page = boards[0].get("items_page", {})
    items = items_page.get("items", [])
    all_items.extend(items)
    cursor = items_page.get("cursor")

    # Paginate until cursor is null
    page_count = 1
    while cursor:
        page_count += 1
        logger.info(f"Paginating items for board {board_id}: page {page_count}...")
        next_data = execute_graphql_query(next_page_query, variables={"cursor": cursor})
        next_page = next_data.get("next_items_page", {})
        next_items = next_page.get("items", [])
        if not next_items:
            break
        all_items.extend(next_items)
        cursor = next_page.get("cursor")

    logger.info(f"Retrieved total {len(all_items)} items across {page_count} pages from board {board_id}.")
    return all_items

def load_source_fallback_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads local reference datasets from data/ for graceful degradation if token is absent in local dev/demo.
    """
    base_dir = Path(__file__).resolve().parent.parent / "data"
    
    wo_file = base_dir / "Work_Order_Tracker Data.xlsx"
    deals_file = base_dir / "Deal Funnel Data.xlsx"
    
    wo_df = pd.read_excel(wo_file) if wo_file.exists() else pd.DataFrame()
    deals_df = pd.read_excel(deals_file) if deals_file.exists() else pd.DataFrame()
    
    return wo_df, deals_df

def refresh_cache(force: bool = False) -> dict:
    """
    Orchestrates data retrieval from Monday.com with in-memory caching and 10-minute TTL.
    """
    global _CACHE
    now = datetime.now(timezone.utc)

    # Check if cached data is fresh (< 10 minutes)
    if not force and _CACHE["work_orders_df"] is not None and _CACHE["last_refreshed_at"] is not None:
        elapsed = (now - _CACHE["last_refreshed_at"]).total_seconds()
        if elapsed < 600: # 10 minutes
            logger.info(f"Serving board data from in-memory cache ({int(elapsed)}s old).")
            return _CACHE

    logger.info("Refreshing board data from Monday.com...")
    token = get_api_token()

    if token:
        try:
            # 1. Fetch Columns Metadata
            wo_cols = get_board_columns(WORK_ORDERS_BOARD_ID)
            deals_cols = get_board_columns(DEALS_BOARD_ID)

            # 2. Fetch All Items Live with Cursor Pagination
            raw_wo_items = get_all_items(WORK_ORDERS_BOARD_ID)
            raw_deals_items = get_all_items(DEALS_BOARD_ID)

            # 3. Convert to DataFrames via Normalizer
            wo_df = raw_items_to_dataframe(raw_wo_items, wo_cols)
            deals_df = raw_items_to_dataframe(raw_deals_items, deals_cols)

            if len(wo_df) > 0 and len(deals_df) > 0:
                _CACHE["work_orders_df"] = wo_df
                _CACHE["deals_df"] = deals_df
                _CACHE["work_orders_columns"] = wo_cols
                _CACHE["deals_columns"] = deals_cols
                _CACHE["last_refreshed_at"] = now
                _CACHE["is_connected_live"] = True
                _CACHE["status_message"] = f"Live Monday.com (WO: {len(wo_df)}, Deals: {len(deals_df)})"
                return _CACHE
        except MondayAuthError:
            raise
        except Exception as err:
            logger.error(f"Live Monday.com fetch encountered error: {err}")
            raise MondayUnavailableError(f"Could not connect to Monday.com: {err}")
    else:
        # Check if local reference files exist to allow offline operation / demonstration
        wo_df, deals_df = load_source_fallback_data()
        if len(wo_df) > 0 and len(deals_df) > 0:
            logger.info("Loaded reference datasets from data/ for sandbox demonstration.")
            _CACHE["work_orders_df"] = wo_df
            _CACHE["deals_df"] = deals_df
            _CACHE["last_refreshed_at"] = now
            _CACHE["is_connected_live"] = False
            _CACHE["status_message"] = f"Local Sandbox Reference Data (WO: {len(wo_df)}, Deals: {len(deals_df)})"
            return _CACHE
        else:
            raise MondayAuthError(
                "MONDAY_API_TOKEN is not configured. Please set the environment variable "
                "or Streamlit secret MONDAY_API_TOKEN to connect live to Monday.com boards."
            )

    return _CACHE

def get_cached_data() -> dict:
    """Returns the current cache, refreshing if empty."""
    if _CACHE["work_orders_df"] is None:
        return refresh_cache(force=False)
    return _CACHE
