import pandas as pd

deals = pd.read_excel("data/Deal Funnel Data.xlsx")
wo = pd.read_excel("data/Work_Order_Tracker Data.xlsx")

# Filter any accidental header rows in Deals
deals_clean = deals[~deals["Deal Name"].astype(str).str.contains("Deal Name|Deal Status", case=False, na=False)].copy()
deals_clean = deals_clean[~deals_clean["Tentative Close Date"].astype(str).str.contains("Tentative Close Date", case=False, na=False)].copy()
deals_clean = deals_clean.reset_index(drop=True)

# Filter any accidental header rows in WO
wo_clean = wo[~wo["Deal name masked"].astype(str).str.contains("Deal name masked", case=False, na=False)].copy()
wo_clean = wo_clean[~wo_clean["Serial #"].astype(str).str.contains("Serial #", case=False, na=False)].copy()
wo_clean = wo_clean.reset_index(drop=True)

deals_clean.to_excel("data/Deal Funnel Data.xlsx", index=False)
deals_clean.to_csv("data/Deal Funnel Data.csv", index=False)

wo_clean.to_excel("data/Work_Order_Tracker Data.xlsx", index=False)
wo_clean.to_csv("data/Work_Order_Tracker Data.csv", index=False)

print(f"Cleaned Deals rows: {len(deals_clean)}")
print(f"Cleaned Work Orders rows: {len(wo_clean)}")
