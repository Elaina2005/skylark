import pandas as pd
import openpyxl

def inspect_file(filepath, name):
    print("=" * 80)
    print(f"INSPECTING: {name} ({filepath})")
    print("=" * 80)
    
    wb = openpyxl.load_workbook(filepath, read_only=True)
    sheets = wb.sheetnames
    print(f"Sheet Names: {sheets}")
    
    df = pd.read_excel(filepath)
    print(f"\nShape: {df.shape[0]} rows, {df.shape[1]} columns")
    
    print("\n--- Column Headers & Inferred Data Types ---")
    for col in df.columns:
        null_cnt = df[col].isnull().sum()
        pct_missing = (null_cnt / len(df)) * 100
        sample_vals = df[col].dropna().unique()[:5]
        print(f"Column: '{col}' | Dtype: {df[col].dtype} | Missing: {null_cnt}/{len(df)} ({pct_missing:.1f}%) | Samples: {sample_vals}")
    
    print("\n--- First 10 Rows ---")
    print(df.head(10).to_string())
    
    print("\n--- Categorical Column Value Distributions ---")
    for col in df.columns:
        if df[col].dtype == "object":
            uniques = df[col].dropna().unique()
            if len(uniques) <= 25:
                print(f"\nCategorical Column '{col}' ({len(uniques)} unique values):")
                print(df[col].value_counts(dropna=False).to_string())
    print("\n" + "=" * 80 + "\n")

inspect_file("data/Deal Funnel Data.xlsx", "Deals Board Source Data")
inspect_file("data/Work_Order_Tracker Data.xlsx", "Work Orders Board Source Data")
