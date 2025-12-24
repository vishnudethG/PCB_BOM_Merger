from src.core.file_loader import load_xy_file
import os

XY_PATH = r"P:\PCB_BOM_Merger\XYDATA.xlsx"  # <--- Update this

try:
    print(f"Testing Header Hunter on: {os.path.basename(XY_PATH)}")
    df = load_xy_file(XY_PATH)
    
    print("\n[SUCCESS] File Loaded.")
    print(f"Columns Detected: {list(df.columns)}")
    print("First Row Data:")
    print(df.iloc[0].to_dict())
    
except Exception as e:
    print(f"\n[FAIL] {e}")