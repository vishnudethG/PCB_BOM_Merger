# tests/test_normalizer.py
import sys
import os
import pandas as pd

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

from src.core.normalizer import normalize_bom_data

def run_test():
    print("--- TEST: BOM NORMALIZER ---")

    # 1. Create Dummy Data
    data = {
        'Ref Des': ['R1-R3', 'C5, C6', 'U1', 'D1-D2, D4'],
        'Value':   ['10k',   '100nF',  'MCU', 'LED']
    }
    df = pd.DataFrame(data)
    
    print("Input Data:")
    print(df)
    print("-" * 30)

    # 2. Run Normalizer
    try:
        # We assume the user selected Comma as delimiter
        df_clean = normalize_bom_data(df, 'Ref Des', delimiter=',')
        
        print("Output Data (Exploded):")
        print(df_clean)
        print("-" * 30)

        # 3. VERIFICATION
        
        # Check Total Rows
        # R1-R3 = 3 rows
        # C5, C6 = 2 rows
        # U1 = 1 row
        # D1-D2, D4 = (D1, D2) + D4 = 3 rows
        # Total should be 3+2+1+3 = 9 rows
        if len(df_clean) == 9:
            print("[PASS] Row count is correct (9).")
        else:
            print(f"[FAIL] Expected 9 rows, got {len(df_clean)}.")

        # Check Range Expansion
        if 'R2' in df_clean['Ref Des'].values:
            print("[PASS] Range R1-R3 expanded to include R2.")
        else:
            print("[FAIL] R2 is missing.")

        # Check Complex Mix (D1-D2, D4)
        if 'D2' in df_clean['Ref Des'].values and 'D4' in df_clean['Ref Des'].values:
             print("[PASS] Mixed range (D1-D2, D4) handled correctly.")
        else:
             print("[FAIL] Mixed range failed.")

    except Exception as e:
        print(f"[CRITICAL FAIL] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()