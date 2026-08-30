import pdfplumber
import pandas as pd
import numpy as np
import os

def parse_deal_funnel(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        print(f"Deal Funnel pages: {num_pages}")
        
        # 3 strips of 9 pages each
        # Strip 0: pages 0-8: Deal Name, Owner code, Client Code, Deal Status, Close Date (A), Closure Probability
        # Strip 1: pages 9-17: Masked Deal value, Tentative Close Date, Deal Stage, Product deal
        # Strip 2: pages 18-26: Sector/service, Created Date
        
        strip_cols = [
            [
                ("Deal Name", 30, 115),
                ("Owner code", 115, 190),
                ("Client Code", 190, 280),
                ("Deal Status", 280, 360),
                ("Close Date (A)", 360, 440),
                ("Closure Probability", 440, 560),
            ],
            [
                ("Masked Deal value", 30, 140),
                ("Tentative Close Date", 140, 240),
                ("Deal Stage", 240, 390),
                ("Product deal", 390, 580),
            ],
            [
                ("Sector/service", 30, 180),
                ("Created Date", 180, 300),
            ]
        ]
        
        strip_dfs = []
        for s_idx, col_defs in enumerate(strip_cols):
            start_p = s_idx * 9
            end_p = start_p + 9
            rows = []
            
            for p_num in range(start_p, end_p):
                page = pdf.pages[p_num]
                words = page.extract_words()
                if not words:
                    continue
                
                # find header line (top < 65)
                header_words = [w for w in words if w['top'] < 65]
                data_words = [w for w in words if w['top'] >= 65]
                
                # cluster data_words into rows by 'top' within 6 pt
                data_words.sort(key=lambda w: (w['top'], w['x0']))
                
                row_groups = []
                for w in data_words:
                    assigned = False
                    for rg in row_groups:
                        if abs(rg['avg_top'] - w['top']) < 7:
                            rg['words'].append(w)
                            rg['avg_top'] = sum(x['top'] for x in rg['words']) / len(rg['words'])
                            assigned = True
                            break
                    if not assigned:
                        row_groups.append({'avg_top': w['top'], 'words': [w]})
                
                # sort row groups by avg_top
                row_groups.sort(key=lambda rg: rg['avg_top'])
                
                for rg in row_groups:
                    r_dict = {}
                    for col_name, x_min, x_max in col_defs:
                        c_words = [w['text'] for w in rg['words'] if x_min <= (w['x0'] + w['x1'])/2 < x_max]
                        val = " ".join(c_words).strip() if c_words else np.nan
                        r_dict[col_name] = val
                    rows.append(r_dict)
            
            df_strip = pd.DataFrame(rows)
            strip_dfs.append(df_strip)
            print(f"Strip {s_idx} rows: {len(df_strip)}")
        
        # Combine strips horizontally
        min_len = min(len(df) for df in strip_dfs)
        combined_df = pd.concat([df.iloc[:min_len].reset_index(drop=True) for df in strip_dfs], axis=1)
        print(f"Combined Deal Funnel shape: {combined_df.shape}")
        return combined_df

def parse_work_order_tracker(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        print(f"\nWork Order Tracker pages: {num_pages}")
        
        # 7 strips of 10 pages each
        # Strip 0: pages 0-9: Deal name masked, Customer Name Code, Serial #, Nature of Work
        # Strip 1: pages 10-19: Date of PO/LOI, Document Type, Probable Start Date, Probable End Date
        # Strip 2: pages 20-29: Type of Work, Is any Skylark software platform part of the client deliverables in this deal?
        # Strip 3: pages 30-39: Amount in Rupees (Incl of GST) (Masked)
        # Strip 4: pages 40-49: Billed Value in Rupees (Incl of GST.) (Masked), Collected Amount in Rupees (Incl of GST.) (Masked)
        # Strip 5: pages 50-59: Amount Receivable (Masked), AR Priority account, Quantity by Ops, Quantities as per PO
        # Strip 6: pages 60-69: Actual Billing Month, Actual Collection Month, WO Status (billed), Collection status
        
        # Also notice pages 6, 16, 26, 36, 46, 56, 66 have specific extra column layouts or strips
        # Let's inspect headers on each 10-page strip carefully
        
        strip_page_ranges = [
            (0, 10, [
                ("Deal name masked", 30, 160),
                ("Customer Name Code", 160, 270),
                ("Serial #", 270, 390),
                ("Nature of Work", 390, 580)
            ]),
            (10, 20, [
                ("Date of PO/LOI", 30, 150),
                ("Document Type", 150, 270),
                ("Probable Start Date", 270, 390),
                ("Probable End Date", 390, 550)
            ]),
            (20, 30, [
                ("Type of Work", 30, 350),
                ("Is any Skylark software platform part of the client deliverables in this deal?", 350, 580)
            ]),
            (30, 40, [
                ("Amount in Rupees (Incl of GST) (Masked)", 30, 580)
            ]),
            (40, 50, [
                ("Billed Value in Rupees (Incl of GST.) (Masked)", 30, 320),
                ("Collected Amount in Rupees (Incl of GST.) (Masked)", 320, 580)
            ]),
            (50, 60, [
                ("Amount Receivable (Masked)", 30, 190),
                ("AR Priority account", 190, 290),
                ("Quantity by Ops", 290, 400),
                ("Quantities as per PO", 400, 580)
            ]),
            (60, 70, [
                ("Actual Billing Month", 30, 160),
                ("Actual Collection Month", 160, 280),
                ("WO Status (billed)", 280, 410),
                ("Collection status", 410, 580)
            ])
        ]
        
        strip_dfs = []
        for s_idx, (start_p, end_p, col_defs) in enumerate(strip_page_ranges):
            rows = []
            for p_num in range(start_p, end_p):
                page = pdf.pages[p_num]
                words = page.extract_words()
                if not words:
                    continue
                data_words = [w for w in words if w['top'] >= 65]
                data_words.sort(key=lambda w: (w['top'], w['x0']))
                
                row_groups = []
                for w in data_words:
                    assigned = False
                    for rg in row_groups:
                        if abs(rg['avg_top'] - w['top']) < 7:
                            rg['words'].append(w)
                            rg['avg_top'] = sum(x['top'] for x in rg['words']) / len(rg['words'])
                            assigned = True
                            break
                    if not assigned:
                        row_groups.append({'avg_top': w['top'], 'words': [w]})
                
                row_groups.sort(key=lambda rg: rg['avg_top'])
                
                for rg in row_groups:
                    r_dict = {}
                    for col_name, x_min, x_max in col_defs:
                        c_words = [w['text'] for w in rg['words'] if x_min <= (w['x0'] + w['x1'])/2 < x_max]
                        val = " ".join(c_words).strip() if c_words else np.nan
                        r_dict[col_name] = val
                    rows.append(r_dict)
            
            df_strip = pd.DataFrame(rows)
            strip_dfs.append(df_strip)
            print(f"WO Strip {s_idx} rows: {len(df_strip)}")
        
        min_len = min(len(df) for df in strip_dfs)
        combined_df = pd.concat([df.iloc[:min_len].reset_index(drop=True) for df in strip_dfs], axis=1)
        print(f"Combined Work Order shape: {combined_df.shape}")
        return combined_df

deals_df = parse_deal_funnel('data/Deal_funnel_Data.pdf')
wo_df = parse_work_order_tracker('data/Work_Order_Tracker_Data.pdf')

deals_df.to_excel('data/Deal Funnel Data.xlsx', index=False)
deals_df.to_csv('data/Deal Funnel Data.csv', index=False)

wo_df.to_excel('data/Work_Order_Tracker Data.xlsx', index=False)
wo_df.to_csv('data/Work_Order_Tracker Data.csv', index=False)

print("Saved files to data/ successfully!")
