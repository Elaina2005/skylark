import pdfplumber
import pandas as pd
import numpy as np

def extract_and_save():
    # 1. Deal Funnel
    with pdfplumber.open("data/Deal_funnel_Data.pdf") as pdf:
        strip_defs = [
            (0, 9, [
                ("Deal Name", 30, 115),
                ("Owner code", 115, 190),
                ("Client Code", 190, 280),
                ("Deal Status", 280, 360),
                ("Close Date (A)", 360, 440),
                ("Closure Probability", 440, 560),
            ]),
            (9, 18, [
                ("Masked Deal value", 30, 140),
                ("Tentative Close Date", 140, 240),
                ("Deal Stage", 240, 390),
                ("Product deal", 390, 580),
            ]),
            (18, 27, [
                ("Sector/service", 30, 180),
                ("Created Date", 180, 300),
            ])
        ]
        
        strip_dfs = []
        for s_idx, (start_p, end_p, col_defs) in enumerate(strip_defs):
            all_rows = []
            for p_idx in range(start_p, end_p):
                page = pdf.pages[p_idx]
                words = page.extract_words()
                page_in_strip = p_idx - start_p
                num_rows = 3 if page_in_strip == 8 else 42
                
                for r in range(num_rows):
                    expected_top = 72.9 + r * 15.744
                    row_words = [w for w in words if abs(w['top'] - expected_top) <= 8]
                    row_data = {}
                    for col_name, x_min, x_max in col_defs:
                        c_words = [w['text'] for w in row_words if x_min <= (w['x0'] + w['x1'])/2 < x_max]
                        val = " ".join(c_words).strip() if c_words else np.nan
                        row_data[col_name] = val
                    all_rows.append(row_data)
            strip_dfs.append(pd.DataFrame(all_rows))
        
        deals_df = pd.concat(strip_dfs, axis=1)
    
    # 2. Work Orders
    with pdfplumber.open("data/Work_Order_Tracker_Data.pdf") as pdf:
        strip_defs = [
            (0, 5, [
                ("Deal name masked", 30, 160),
                ("Customer Name Code", 160, 270),
                ("Serial #", 270, 390),
                ("Nature of Work", 390, 580)
            ]),
            (5, 10, [
                ("Last executed month of recurring project", 30, 200),
                ("Execution Status", 200, 390),
                ("Data Delivery Date", 390, 580)
            ]),
            (10, 15, [
                ("Date of PO/LOI", 30, 150),
                ("Document Type", 150, 270),
                ("Probable Start Date", 270, 390),
                ("Probable End Date", 390, 580)
            ]),
            (15, 20, [
                ("BD/KAM Personnel code", 30, 250),
                ("Sector", 250, 580)
            ]),
            (20, 25, [
                ("Type of Work", 30, 380),
                ("Is any Skylark software platform part of the client deliverables in this deal?", 380, 580)
            ]),
            (25, 30, [
                ("Last invoice date", 30, 150),
                ("latest invoice no.", 150, 320),
                ("Amount in Rupees (Excl of GST) (Masked)", 320, 580)
            ]),
            (30, 35, [
                ("Amount in Rupees (Incl of GST) (Masked)", 30, 580)
            ]),
            (35, 40, [
                ("Billed Value in Rupees (Excl of GST.) (Masked)", 30, 580)
            ]),
            (40, 45, [
                ("Billed Value in Rupees (Incl of GST.) (Masked)", 30, 320),
                ("Collected Amount in Rupees (Incl of GST.) (Masked)", 320, 580)
            ]),
            (45, 50, [
                ("Amount to be billed in Rs. (Exl. of GST) (Masked)", 30, 320),
                ("Amount to be billed in Rs. (Incl. of GST) (Masked)", 320, 580)
            ]),
            (50, 55, [
                ("Amount Receivable (Masked)", 30, 190),
                ("AR Priority account", 190, 280),
                ("Quantity by Ops", 280, 400),
                ("Quantities as per PO", 400, 580)
            ]),
            (55, 60, [
                ("Quantity billed (till date)", 30, 150),
                ("Balance in quantity", 150, 270),
                ("Invoice Status", 270, 410),
                ("Expected Billing Month", 410, 580)
            ]),
            (60, 65, [
                ("Actual Billing Month", 30, 160),
                ("Actual Collection Month", 160, 280),
                ("WO Status (billed)", 280, 410),
                ("Collection status", 410, 580)
            ]),
            (65, 70, [
                ("Collection Date", 30, 250),
                ("Billing Status", 250, 580)
            ])
        ]
        
        strip_dfs = []
        for s_idx, (start_p, end_p, col_defs) in enumerate(strip_defs):
            all_rows = []
            for p_idx in range(start_p, end_p):
                page = pdf.pages[p_idx]
                words = page.extract_words()
                page_in_strip = p_idx - start_p
                num_rows = 5 if page_in_strip == 4 else 42
                
                for r in range(num_rows):
                    expected_top = 72.9 + r * 15.744
                    row_words = [w for w in words if abs(w['top'] - expected_top) <= 8]
                    row_data = {}
                    for col_name, x_min, x_max in col_defs:
                        c_words = [w['text'] for w in row_words if x_min <= (w['x0'] + w['x1'])/2 < x_max]
                        val = " ".join(c_words).strip() if c_words else np.nan
                        row_data[col_name] = val
                    all_rows.append(row_data)
            strip_dfs.append(pd.DataFrame(all_rows))
        
        wo_df = pd.concat(strip_dfs, axis=1)
        # Drop row 0 which is the header line
        wo_df = wo_df.iloc[1:].reset_index(drop=True)
    
    deals_df.to_excel("data/Deal Funnel Data.xlsx", index=False)
    deals_df.to_csv("data/Deal Funnel Data.csv", index=False)
    
    wo_df.to_excel("data/Work_Order_Tracker Data.xlsx", index=False)
    wo_df.to_csv("data/Work_Order_Tracker Data.csv", index=False)
    
    print(f"Deals saved: {len(deals_df)} rows, {len(deals_df.columns)} columns")
    print(f"Work Orders saved: {len(wo_df)} rows, {len(wo_df.columns)} columns")

extract_and_save()
