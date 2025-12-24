import pandas as pd
import sys
import os

# Import your actual logic
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.core.file_loader import load_and_clean_file
from src.core.normalizer import normalize_bom_data

# --- FILES TO TEST ---
# REPLACE THESE PATHS WITH YOUR ACTUAL FILE PATHS
BOM_PATH = r"P:\PCB_BOM_Merger\BOM-input.xlsx"  # <--- UPDATE THIS
XY_PATH = r"P:\PCB_BOM_Merger\XY-input.csv"    # <--- UPDATE THIS

def inspect_data():
    print("=== STEP 1: LOADING FILES ===")
    try:
        bom_df = load_and_clean_file(BOM_PATH)
        print(f"[OK] BOM Loaded. Columns found: {list(bom_df.columns)}")
        
        xy_df = load_and_clean_file(XY_PATH)
        print(f"[OK] XY Loaded. Columns found: {list(xy_df.columns)}")
    except Exception as e:
        print(f"[FAIL] Loading Error: {e}")
        return

    print("\n=== STEP 2: CHECKING XY KEYS ===")
    # Try to auto-find the Ref Des column in XY
    xy_ref_col = None
    for col in xy_df.columns:
        if "des" in col.lower() and "description" not in col.lower():
            xy_ref_col = col
            break
    
    if xy_ref_col:
        print(f"-> Detected XY Ref Col: '{xy_ref_col}'")
        print(f"-> First 5 XY Refs (Raw): {xy_df[xy_ref_col].head(5).tolist()}")
    else:
        print("[FAIL] Could not find 'Designator' column in XY. Check spelling!")

    print("\n=== STEP 3: CHECKING BOM NORMALIZATION ===")
    # Try to find BOM Ref Des
    bom_ref_col = "Reference Designator" # From your screenshot
    if bom_ref_col not in bom_df.columns:
        print(f"[FAIL] Could not find '{bom_ref_col}' in BOM. Found: {list(bom_df.columns)}")
        return

    print(f"-> BOM Ref Col: '{bom_ref_col}'")
    print(f"-> Sample Row 1 (Before Split): {bom_df[bom_ref_col].iloc[0]}")

    # Run Normalization
    try:
        clean_bom = normalize_bom_data(bom_df, bom_ref_col, delimiter=',')
        print(f"-> Normalization Complete. Row count grew from {len(bom_df)} to {len(clean_bom)}")
        print(f"-> First 5 BOM Refs (After Split): {clean_bom[bom_ref_col].head(5).tolist()}")
    except Exception as e:
        print(f"[FAIL] Normalizer Crashed: {e}")

    print("\n=== STEP 4: SIMULATING MATCH ===")
    if xy_ref_col:
        # Create sets to see overlap
        bom_refs = set(clean_bom[bom_ref_col].astype(str).str.strip().str.upper())
        xy_refs = set(xy_df[xy_ref_col].astype(str).str.strip().str.upper())
        
        common = bom_refs.intersection(xy_refs)
        print(f"-> Total Unique BOM Refs: {len(bom_refs)}")
        print(f"-> Total Unique XY Refs: {len(xy_refs)}")
        print(f"-> MATCHED COUNT: {len(common)}")
        
        if len(common) == 0:
            print("\n[DIAGNOSIS] ZERO MATCHES.")
            print("Comparison Sample:")
            print(f"BOM: {list(bom_refs)[:3]}")
            print(f"XY:  {list(xy_refs)[:3]}")

if __name__ == "__main__":
    inspect_data()