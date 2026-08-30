import pdfplumber
import pandas as pd
import numpy as np

def extract_work_orders():
    with pdfplumber.open("data/Work_Order_Tracker_Data.pdf") as pdf:
        # 14 strips of 5 pages each
        # pages 0..4, 5..9, 10..14, etc.
        strip_defs = [
            # Strip 0: pages 0..4
            (0, 5, [
                ("Deal name masked", 30, 160),
                ("Customer Name Code", 160, 270),
                ("Serial #", 270, 390),
                ("Nature of Work", 390, 580)
            ]),
            # Strip 1: pages 5..9
            (5, 10, [
                ("Last executed month of recurring project", 30, 200),
                ("Execution Status", 200, 390),
                ("Data Delivery Date", 390, 580)
            ]),
            # Strip 2: pages 10..14
            (10, 15, [
                ("Date of PO/LOI", 30, 150),
                ("Document Type", 150, 270),
                ("Probable Start Date", 270, 390),
                ("Probable End Date", 390, 580)
            ]),
            # Strip 3: pages 15..19
            (15, 20, [
                ("BD/KAM Personnel code", 30, 250),
                ("Sector", 250, 580)
            ]),
            # Strip 4: pages 20..24
            (20, 25, [
                ("Type of Work", 30, 380),
                ("Is any Skylark software platform part of the client deliverables in this deal?", 380, 580)
            ]),
            # Strip 5: pages 25..29
            (25, 30, [
                ("Last invoice date", 30, 150),
                ("latest invoice no.", 150, 320),
                ("Amount in Rupees (Excl of GST) (Masked)", 320, 580)
            ]),
            # Strip 6: pages 30..34
            (30, 35, [
                ("Amount in Rupees (Incl of GST) (Masked)", 30, 580)
            ]),
            # Strip 7: pages 35..39
            (35, 40, [
                ("Billed Value in Rupees (Excl of GST.) (Masked)", 30, 580)
            ]),
            # Strip 8: pages 40..44
            (40, 45, [
                ("Billed Value in Rupees (Incl of GST.) (Masked)", 30, 320),
                ("Collected Amount in Rupees (Incl of GST.) (Masked)", 320, 580)
            ]),
            # Strip 9: pages 45..49
            (45, 50, [
                ("Amount to be billed in Rs. (Exl. of GST) (Masked)", 30, 320),
                ("Amount to be billed in Rs. (Incl. of GST) (Masked)", 320, 580)
            ]),
            # Strip 10: pages 50..54
            (50, 55, [
                ("Amount Receivable (Masked)", 30, 190),
                ("AR Priority account", 190, 280),
                ("Quantity by Ops", 280, 400),
                ("Quantities as per PO", 400, 580)
            ]),
            # Strip 11: pages 55..59
            (55, 60, [
                ("Quantity billed (till date)", 30, 150),
                ("Balance in quantity", 150, 270),
                ("Invoice Status", 270, 410),
                ("Expected Billing Month", 410, 580)
            ]),
            # Strip 12: pages 60..64
            (60, 65, [
                ("Actual Billing Month", 30, 160),
                ("Actual Collection Month", 160, 280),
                ("WO Status (billed)", 280, 410),
                ("Collection status", 410, 580)
            ]),
            # Strip 13: pages 65..69
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
            
            strip_df = pd.DataFrame(all_rows)
            strip_dfs.append(strip_df)
            print(f"WO Strip {s_idx:2d} shape: {strip_df.shape}")
        
        combined_wo = pd.concat(strip_dfs, axis=1)
        # Deduplicate any duplicate column names if any
        print("Combined Work Orders DataFrame shape:", combined_wo.shape)
        print("\nFirst 5 rows of Work Orders:")
        print(combined_wo[["Deal name masked", "Customer Name Code", "Serial #", "Sector", "Execution Status"]].head(5))
        return combined_wo

wo = extract_work_orders()
