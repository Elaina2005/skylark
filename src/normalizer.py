"""
Data resilience and normalization functions for Monday.com datasets.
Pure functions designed with defensive error handling to prevent unhandled exceptions.
"""
import re
import json
import logging
import numpy as np
import pandas as pd
from dateutil import parser
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

def normalize_dates(series: pd.Series) -> pd.Series:
    """
    Parses inconsistent date strings/formats (e.g., '12/03/2024', '2024-03-12', 'March 12, 2024', 'TBD', 'N/A').
    Unparseable or blank values degrade gracefully to pd.NaT.
    """
    if series is None or len(series) == 0:
        return pd.Series(dtype="datetime64[ns]")
    
    def _parse_single_date(val):
        if pd.isna(val) or val is None:
            return pd.NaT
        if isinstance(val, (pd.Timestamp, np.datetime64)):
            return pd.to_datetime(val)
        val_str = str(val).strip()
        if not val_str or val_str.lower() in ("nan", "nat", "none", "null", "tbd", "n/a", "-", ""):
            return pd.NaT
        
        # Check if JSON string with date field
        if val_str.startswith("{") and "date" in val_str:
            try:
                parsed_json = json.loads(val_str)
                if isinstance(parsed_json, dict) and "date" in parsed_json:
                    val_str = str(parsed_json["date"]).strip()
            except Exception:
                pass

        try:
            # First try standard ISO format for speed
            return pd.to_datetime(val_str, errors="raise")
        except Exception:
            pass
        
        try:
            # Fallback to dateutil parser
            parsed = parser.parse(val_str, fuzzy=False)
            return pd.to_datetime(parsed)
        except Exception as e:
            logger.warning(f"Could not parse date value: '{val_str}'. Coerced to NaT. Error: {e}")
            return pd.NaT

    return series.apply(_parse_single_date)

def normalize_text_field(series: pd.Series, canonical_values: list[str] | None = None, threshold: int = 85) -> pd.Series:
    """
    Cleans free-text fields: trims whitespace, collapses multiple spaces, standardizes casing.
    If canonical_values is provided, uses rapidfuzz to map near-duplicate variations to standard labels.
    """
    if series is None or len(series) == 0:
        return pd.Series(dtype=object)

    def _clean_single_text(val):
        if pd.isna(val) or val is None:
            return np.nan
        text = str(val).strip()
        if not text or text.lower() in ("nan", "none", "null", "n/a", "-"):
            return np.nan
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)
        
        if canonical_values and len(canonical_values) > 0:
            try:
                # Find best fuzzy match
                match = process.extractOne(
                    text,
                    canonical_values,
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=threshold
                )
                if match:
                    return match[0]
            except Exception as e:
                logger.warning(f"Fuzzy matching error on text '{text}': {e}")
        
        return text

    return series.apply(_clean_single_text)

def normalize_currency(series: pd.Series) -> pd.Series:
    """
    Strips currency symbols, commas, Indian numbering notations, and whitespace.
    Coerces numeric-looking values to float. Blank/invalid strings become NaN.
    """
    if series is None or len(series) == 0:
        return pd.Series(dtype="float64")

    def _clean_single_currency(val):
        if pd.isna(val) or val is None:
            return np.nan
        if isinstance(val, (int, float, np.number)):
            return float(val)
        val_str = str(val).strip()
        if not val_str or val_str.lower() in ("nan", "none", "null", "n/a", "-", "#value!", "na"):
            return np.nan
        
        # Remove currency symbols ($, INR, Rs, ?), commas, and spaces
        cleaned = re.sub(r"[^\d.-]", "", val_str)
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse numeric currency value: '{val_str}'. Coerced to NaN.")
            return np.nan

    return series.apply(_clean_single_currency)

def handle_missing(df: pd.DataFrame, required_for_metric: list[str]) -> tuple[pd.DataFrame, int, list[str]]:
    """
    Filters rows that have valid, non-null values for the specified required columns.
    Returns (usable_rows_df, excluded_count, excluded_reasons).
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(), 0, ["Empty dataset"]

    valid_mask = pd.Series(True, index=df.index)
    excluded_reasons = []
    
    for col in required_for_metric:
        if col not in df.columns:
            excluded_reasons.append(f"Column '{col}' is missing from schema")
            valid_mask &= False
            continue
        
        missing_in_col = df[col].isna()
        missing_count = int(missing_in_col.sum())
        if missing_count > 0:
            excluded_reasons.append(f"{missing_count} rows missing '{col}'")
            valid_mask &= (~missing_in_col)

    usable_df = df[valid_mask].copy()
    excluded_count = len(df) - len(usable_df)
    return usable_df, excluded_count, excluded_reasons

def data_quality_report(df: pd.DataFrame, board_name: str) -> dict:
    """
    Returns per-column quality breakdown: %_missing, null_count, flagged counts,
    and a plain-English executive summary sentence citing key caveats.
    """
    if df is None or len(df) == 0:
        return {
            "board_name": board_name,
            "total_rows": 0,
            "columns": {},
            "summary": f"The '{board_name}' board currently contains 0 records."
        }

    total_rows = len(df)
    col_reports = {}
    caveats = []

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        pct_missing = round((null_count / total_rows) * 100, 1)
        
        col_reports[col] = {
            "null_count": null_count,
            "percent_missing": pct_missing,
            "valid_count": total_rows - null_count
        }
        
        if pct_missing >= 15.0:
            caveats.append(f"{pct_missing}% of records are missing '{col}'")

    summary_parts = [f"Board '{board_name}' has {total_rows} total records across {len(df.columns)} columns."]
    if caveats:
        summary_parts.append("Notable data quality caveats: " + "; ".join(caveats[:4]) + ".")
    else:
        summary_parts.append("Data quality is solid with minimal missing fields.")

    return {
        "board_name": board_name,
        "total_rows": total_rows,
        "columns": col_reports,
        "summary": " ".join(summary_parts),
        "caveats": caveats
    }

def raw_items_to_dataframe(items: list[dict], columns_meta: list[dict] | None = None) -> pd.DataFrame:
    """
    Converts Monday.com GraphQL item/column_values JSON into a clean, typed pandas DataFrame.
    """
    if not items:
        return pd.DataFrame()

    col_id_to_title = {}
    col_id_to_type = {}
    if columns_meta:
        for c in columns_meta:
            cid = c.get("id")
            title = c.get("title", cid)
            ctype = c.get("type", "text")
            col_id_to_title[cid] = title
            col_id_to_type[cid] = ctype

    rows = []
    for item in items:
        row = {
            "item_id": item.get("id"),
            "Name": item.get("name", "")
        }
        for cv in item.get("column_values", []):
            cid = cv.get("id")
            col_name = col_id_to_title.get(cid, cv.get("title", cid))
            col_type = col_id_to_type.get(cid, cv.get("type", "text"))
            raw_text = cv.get("text")
            raw_value = cv.get("value")

            # Parse value according to column type
            if col_type in ("date", "timeline"):
                # Value may be JSON {"date": "YYYY-MM-DD"} or raw text
                val = raw_text
                if raw_value and isinstance(raw_value, str) and "date" in raw_value:
                    try:
                        parsed_json = json.loads(raw_value)
                        if "date" in parsed_json:
                            val = parsed_json["date"]
                    except Exception:
                        pass
                row[col_name] = val
            elif col_type in ("numbers", "numeric", "formula"):
                row[col_name] = raw_text if raw_text is not None else raw_value
            else:
                row[col_name] = raw_text if raw_text is not None else ""

        rows.append(row)

    df = pd.DataFrame(rows)
    
    # Run automatic column normalization based on naming conventions
    for col in df.columns:
        col_lower = col.lower()
        if "date" in col_lower or "month" in col_lower and "actual" not in col_lower and "expected" not in col_lower:
            df[col] = normalize_dates(df[col])
        elif any(kw in col_lower for kw in ("amount", "value", "rupees", "revenue", "price", "probability", "quantity", "balance", "rate", "ops")):
            if col_lower != "closure probability": # Keep probability as categorical or handle separately
                df[col] = normalize_currency(df[col])
        elif "sector" in col_lower:
            df[col] = normalize_text_field(df[col], canonical_values=[
                "Mining", "Powerline", "Renewables", "Railways", "Construction",
                "DSP", "Tender", "Security and Surveillance", "Aviation", "Manufacturing", "Others"
            ])
        elif col in ("Deal Status", "Execution Status", "Deal Stage", "Nature of Work", "Invoice Status", "WO Status (billed)"):
            df[col] = normalize_text_field(df[col])

    return df
