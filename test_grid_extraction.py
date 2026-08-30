import pdfplumber
import pandas as pd
import numpy as np

def extract_deal_funnel():
    # Deal Funnel has 3 strips of 9 pages each (total 9 pages per strip)
    # Page rows per page: pages 0-7 have 42 rows, page 8 has 3 rows (total 339 rows)
    # Row tops on a full page: ~72.9 + i * 15.74 for i in range(42)
    with pdfplumber.open("data/Deal_funnel_Data.pdf") as pdf:
        strip_defs = [
            # Strip 0: pages 0..8
            (0, 9, [
                ("Deal Name", 30, 115),
                ("Owner code", 115, 190),
                ("Client Code", 190, 280),
                ("Deal Status", 280, 360),
                ("Close Date (A)", 360, 440),
                ("Closure Probability", 440, 560),
            ]),
            # Strip 1: pages 9..17
            (9, 18, [
                ("Masked Deal value", 30, 140),
                ("Tentative Close Date", 140, 240),
                ("Deal Stage", 240, 390),
                ("Product deal", 390, 580),
            ]),
            # Strip 2: pages 18..26
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
                # On page 0, top header is ~57.1. On pages 1..8, header might be repeated or first row starts at 72.9
                # Let's find row slots for this page index within strip (0..8)
                page_in_strip = p_idx - start_p
                num_rows = 3 if page_in_strip == 8 else 42
                
                # The expected top for row r (0..num_rows-1)
                for r in range(num_rows):
                    expected_top = 72.9 + r * 15.744
                    # find all words with top within 8 pt of expected_top
                    row_words = [w for w in words if abs(w['top'] - expected_top) <= 8]
                    row_data = {}
                    for col_name, x_min, x_max in col_defs:
                        c_words = [w['text'] for w in row_words if x_min <= (w['x0'] + w['x1'])/2 < x_max]
                        val = " ".join(c_words).strip() if c_words else np.nan
                        row_data[col_name] = val
                    all_rows.append(row_data)
            
            strip_df = pd.DataFrame(all_rows)
            strip_dfs.append(strip_df)
            print(f"Deal Funnel Strip {s_idx} shape: {strip_df.shape}")
        
        combined_deals = pd.concat(strip_dfs, axis=1)
        print("Combined Deals DataFrame shape:", combined_deals.shape)
        print("\nFirst 5 rows of Deals:")
        print(combined_deals.head(5))
        return combined_deals

deals = extract_deal_funnel()
