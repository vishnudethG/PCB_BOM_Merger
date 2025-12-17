# tests/test_loader.py
import sys
import os
import pandas as pd
import xlsxwriter

# 1. SETUP PATHS so we can import 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

from src.core.file_loader import load_and_clean_file

# File to generate for testing
TEST_FILE = os.path.join(current_dir, "temp_messy_bom.xlsx")

def create_messy_dummy_file():
    """Generates an Excel file with noise and merged cells."""
    workbook = xlsxwriter.Workbook(TEST_FILE)
    worksheet = workbook.add_worksheet()

    # Noise Rows
    worksheet.write('A1', 'Customer: Stark Industries')
    worksheet.write('A2', 'Project: Jarvis V1')
    worksheet.write('A3', '') # Blank row

    # The Header Row (Row 4 in Excel, Index 3 in 0-based)
    headers = ['Ref Des', 'Manufacturer', 'Part Number', 'Qty']
    for col, h in enumerate(headers):
        worksheet.write(3, col, h)

    # Data Row 1
    worksheet.write(4, 0, 'R1')
    # Merge Manufacturer for R1 and R2
    worksheet.merge_range('B5:B6', 'Murata') 
    worksheet.write(4, 2, 'GRM155')
    worksheet.write(4, 3, '10')

    # Data Row 2 (Should get 'Murata' from merge)
    worksheet.write(5, 0, 'R2')
    # B6 is merged with B5
    worksheet.write(5, 2, 'GRM155')
    worksheet.write(5, 3, '10')

    workbook.close()
    print(f"--> Created dummy file: {TEST_FILE}")

def run_test():
    print("--- TEST: FILE LOADER ---")
    
    # 1. Make the file
    create_messy_dummy_file()

    # 2. Run the logic
    try:
        print("--> Running load_and_clean_file()...")
        df = load_and_clean_file(TEST_FILE)
        
        print("\nSUCCESS! Data Loaded.")
        print("-" * 30)
        print(df.head())
        print("-" * 30)

        # 3. VERIFICATION
        # Check if Header scan worked (Should not see 'Customer: Stark Industries')
        if 'Ref Des' not in df.columns:
            print("[FAIL] Header detection failed.")
        else:
            print("[PASS] Header detection successful.")

        # Check if Unmerge worked (Row 1 is index 1 because index 0 is R1)
        # We look at the second data row. Column 'Manufacturer' should be 'Murata'
        val_r2 = df.iloc[1]['Manufacturer']
        if val_r2 == 'Murata':
            print("[PASS] Merged cell unmerged successfully (R2 has Manufacturer).")
        else:
            print(f"[FAIL] Merged cell failed. Got '{val_r2}' instead of 'Murata'.")

    except Exception as e:
        print(f"[CRITICAL FAIL] Logic crashed: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    # if os.path.exists(TEST_FILE):
    #    os.remove(TEST_FILE)

if __name__ == "__main__":
    run_test()