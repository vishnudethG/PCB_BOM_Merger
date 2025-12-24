import pandas as pd
import os
import sys

# Ensure we can import from src
sys.path.append(os.getcwd())

try:
    from src.core.excel_writer import generate_production_files
    print("[SUCCESS] Found Excel Writer module.")
except ImportError:
    print("[ERROR] Could not find src.core.excel_writer. Make sure you run this from the project root folder.")
    sys.exit(1)

def create_dummy_data():
    print("Generating Dummy Data...")
    
    # 1. Create a DataFrame that mimics exactly what the Logic Engine SHOULD output
    data = {
        # --- KEYS ---
        "Ref Des":      ["R1", "R2", "C1", "C2", "U1", "D1", "TP1", "J1"],
        "Status":       ["MATCHED", "MATCHED", "MATCHED", "MATCHED", "XY_ONLY", "BOM_ONLY", "XY_ONLY", "MATCHED"],
        "Is Ignored":   [False, False, False, False, False, False, True, False],
        
        # --- XY DATA ---
        "Layer":        ["Top", "Bottom", "Top", "Bottom", "Top", "", "Top", "Top"],
        "Ref X":        [10.5, 10.5, 20.0, 20.0, 50.5, 0.0, 5.0, 100.0],
        "Ref Y":        [50.0, 50.0, 15.0, 15.0, 30.0, 0.0, 10.0, 100.0],
        "Rotation":     [0, 90, 180, 270, 0, 0, 0, 90],
        
        # --- BOM DATA ---
        # Note: We use "Part number" (lowercase n) to test the auto-fixer logic
        "Part number":  ["RES-10K", "RES-10K", "CAP-100N", "CAP-100N", "", "LED-RED", "", "CONN-04"],
        "VALUE":        ["10k", "10k", "100nF", "100nF", "", "Red", "", ""],
        "Footprint":    ["0402", "0402", "0603", "0603", "SOIC-8", "LED-0805", "TP-1MM", "CONN-TH"],
        "Quantity":     ["2", "2", "2", "2", "", "1", "", "1"],
        "Remark":       ["", "", "Decoupling", "Decoupling", "DNP Item", "Missing XY", "Test Point", "Connector"]
    }

    df = pd.DataFrame(data)
    
    print(f"Created DataFrame with {len(df)} rows.")
    return df

def run_test():
    # 1. Get Data
    df = create_dummy_data()
    
    # 2. Define Output Path
    output_path = os.path.abspath("Dummy_Template_Output.xlsx")
    
    # 3. Run the Writer
    print(f"Attempting to write to: {output_path}")
    try:
        generate_production_files(df, output_path)
        print("\n---------------------------------------------------")
        print("SUCCESS! File generated.")
        print("Open 'Dummy_Template_Output.xlsx' to see the template.")
        print("---------------------------------------------------")
        os.startfile(os.path.dirname(output_path))
    except Exception as e:
        print("\n!!! FAILURE !!!")
        print(f"Excel Writer crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()