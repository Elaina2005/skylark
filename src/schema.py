"""
Board schema definitions and constants for Monday.com Work Orders and Deals boards.
"""
import os

# Numeric Board IDs - can be set via env or defaults
WORK_ORDERS_BOARD_ID = os.getenv("MONDAY_WORK_ORDERS_BOARD_ID", "8010001001")
DEALS_BOARD_ID = os.getenv("MONDAY_DEALS_BOARD_ID", "8010001002")

BOARD_NAMES = {
    WORK_ORDERS_BOARD_ID: "Work Orders",
    DEALS_BOARD_ID: "Deals",
}

# Known Canonical Sectors for rapidfuzz matching
CANONICAL_SECTORS = [
    "Mining",
    "Powerline",
    "Renewables",
    "Railways",
    "Construction",
    "DSP",
    "Tender",
    "Security and Surveillance",
    "Aviation",
    "Manufacturing",
    "Others"
]

# Deals Board Column Schema
DEALS_COLUMNS_SPEC = {
    "Deal Name": {"type": "text", "description": "Name or identifier of the deal (masked)"},
    "Owner code": {"type": "text", "description": "Sales owner / rep code (e.g. OWNER_001)"},
    "Client Code": {"type": "text", "description": "Client account code (e.g. COMPANY089)"},
    "Deal Status": {"type": "status", "description": "Current status: Open, Won, Dead, On Hold"},
    "Close Date (A)": {"type": "date", "description": "Actual close date for won/closed deals"},
    "Closure Probability": {"type": "status", "description": "Probability rating: High, Medium, Low"},
    "Masked Deal value": {"type": "numeric", "description": "Monetary value of the deal in INR (masked)"},
    "Tentative Close Date": {"type": "date", "description": "Expected or estimated close date"},
    "Deal Stage": {"type": "status", "description": "Sales funnel stage (e.g. A. Lead Generated, B. Sales Qualified Leads, E. Proposal/Commercials Sent, F. Negotiations, G. Project Won, L. Project Lost, M. Projects On Hold, etc.)"},
    "Product deal": {"type": "text", "description": "Product or solution bundle (e.g. Service + Spectra, Pure Service, Spectra + DMO, Hardware)"},
    "Sector/service": {"type": "text", "description": "Industry sector (e.g. Mining, Powerline, Renewables, Railways, Construction, etc.)"},
    "Created Date": {"type": "date", "description": "Date the deal record was created"},
}

# Work Orders Board Column Schema
WORK_ORDERS_COLUMNS_SPEC = {
    "Deal name masked": {"type": "text", "description": "Associated deal name (masked)"},
    "Customer Name Code": {"type": "text", "description": "Customer company code (e.g. WOCOMPANY_002)"},
    "Serial #": {"type": "text", "description": "Work order tracking ID (e.g. SDPLDEAL-075)"},
    "Nature of Work": {"type": "text", "description": "Contract type: One time Project, Proof of Concept, Monthly Contract, Annual Rate Contract"},
    "Last executed month of recurring project": {"type": "text", "description": "Month of last recurring execution (e.g. June, Dec)"},
    "Execution Status": {"type": "status", "description": "Operational status: Completed, Not Started, Executed until current month, Ongoing, Pause / struck, Partial Completed"},
    "Data Delivery Date": {"type": "date", "description": "Date deliverables were handed over to client"},
    "Date of PO/LOI": {"type": "date", "description": "Date Purchase Order or Letter of Intent was signed"},
    "Document Type": {"type": "text", "description": "Authorization document: Purchase Order, LOA/LOI, Email Confirmation"},
    "Probable Start Date": {"type": "date", "description": "Planned / probable start date"},
    "Probable End Date": {"type": "date", "description": "Planned / probable end date (used to check overdue status)"},
    "BD/KAM Personnel code": {"type": "text", "description": "Business Development / Key Account Manager code"},
    "Sector": {"type": "text", "description": "Industry sector (Mining, Powerline, Renewables, Railways, Construction, Others)"},
    "Type of Work": {"type": "text", "description": "Operational deliverable type (e.g. Topography Survey: RGB, LiDAR Survey, Powerline Inspection, Volumetric survey)"},
    "Is any Skylark software platform part of the client deliverables in this deal?": {"type": "text", "description": "Software platform included: NONE, SPECTRA, DMO, SPECTRA + DMO"},
    "Last invoice date": {"type": "date", "description": "Date of latest invoice issued"},
    "latest invoice no.": {"type": "text", "description": "Latest invoice reference number"},
    "Amount in Rupees (Excl of GST) (Masked)": {"type": "numeric", "description": "Total order value excluding GST (INR masked)"},
    "Amount in Rupees (Incl of GST) (Masked)": {"type": "numeric", "description": "Total order value including GST (INR masked)"},
    "Billed Value in Rupees (Excl of GST.) (Masked)": {"type": "numeric", "description": "Cumulative amount billed to date (Excl GST)"},
    "Billed Value in Rupees (Incl of GST.) (Masked)": {"type": "numeric", "description": "Cumulative amount billed to date (Incl GST)"},
    "Collected Amount in Rupees (Incl of GST.) (Masked)": {"type": "numeric", "description": "Cumulative cash collected from client (Incl GST)"},
    "Amount to be billed in Rs. (Exl. of GST) (Masked)": {"type": "numeric", "description": "Remaining unbilled balance (Excl GST)"},
    "Amount to be billed in Rs. (Incl. of GST) (Masked)": {"type": "numeric", "description": "Remaining unbilled balance (Incl GST)"},
    "Amount Receivable (Masked)": {"type": "numeric", "description": "Outstanding unpaid invoice balance / receivables"},
    "AR Priority account": {"type": "text", "description": "Flag for accounts requiring urgent collection ('Priority')"},
    "Quantity by Ops": {"type": "numeric", "description": "Survey units executed by operations team"},
    "Quantities as per PO": {"type": "text", "description": "Contracted scope/quantities (e.g. 5360 HA, 350 KM)"},
    "Quantity billed (till date)": {"type": "numeric", "description": "Total units invoiced to date"},
    "Balance in quantity": {"type": "numeric", "description": "Remaining units yet to be delivered/billed"},
    "Invoice Status": {"type": "status", "description": "Billing lifecycle: Fully Billed, Partially Billed, Not billed yet, Stuck"},
    "Expected Billing Month": {"type": "text", "description": "Forecasted billing month"},
    "Actual Billing Month": {"type": "text", "description": "Month billing actually occurred"},
    "Actual Collection Month": {"type": "text", "description": "Month payment received"},
    "WO Status (billed)": {"type": "status", "description": "Work order financial state: Open, Closed"},
    "Collection status": {"type": "status", "description": "Payment collection state: Closed, Open"},
    "Collection Date": {"type": "date", "description": "Date payment was settled"},
    "Billing Status": {"type": "status", "description": "Operations billing state: Billed, Partially Billed, Update Required, Not Billable, Stuck"}
}

def format_schema_for_prompt(work_orders_cols=None, deals_cols=None) -> str:
    """
    Generates a clear markdown schema description dynamically fed to Claude.
    """
    lines = ["## Live Board Schema Definitions\n"]
    
    # Work Orders Board
    lines.append("### 1. Board: `Work Orders` (Operational & Execution Data)")
    lines.append("Contains project execution timelines, contract values, milestone delivery, and revenue metrics.")
    lines.append("| Column Name | Type | Description |")
    lines.append("| :--- | :--- | :--- |")
    wo_spec = work_orders_cols or WORK_ORDERS_COLUMNS_SPEC
    for col, meta in wo_spec.items():
        desc = meta.get("description", "") if isinstance(meta, dict) else str(meta)
        ctype = meta.get("type", "text") if isinstance(meta, dict) else "text"
        lines.append(f"| `{col}` | {ctype} | {desc} |")
    
    lines.append("\n### 2. Board: `Deals` (Sales Pipeline Data)")
    lines.append("Contains prospective and closed sales opportunities, deal sizes, probability, and stages.")
    lines.append("| Column Name | Type | Description |")
    lines.append("| :--- | :--- | :--- |")
    deals_spec = deals_cols or DEALS_COLUMNS_SPEC
    for col, meta in deals_spec.items():
        desc = meta.get("description", "") if isinstance(meta, dict) else str(meta)
        ctype = meta.get("type", "text") if isinstance(meta, dict) else "text"
        lines.append(f"| `{col}` | {ctype} | {desc} |")
    
    return "\n".join(lines)
