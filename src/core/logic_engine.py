import pandas as pd
from src.core.normalizer import normalize_bom_data # <--- NEW IMPORT

def perform_merge_and_validation(bom_df, xy_df, mapping):
    print("\n---------------------------------------------------")
    print(f"DEBUG MAPPING RECEIVED: {mapping}")
    print("---------------------------------------------------\n")

    # 1. Identify Key Columns
    bom_ref_col = mapping.get("BOM Reference Col")
    xy_ref_col = mapping.get("XY Reference Col")
    
    if not bom_ref_col: bom_ref_col = mapping.get("Reference Designator")
    if not xy_ref_col: xy_ref_col = mapping.get("Reference Designator") 

    if not bom_ref_col or bom_ref_col not in bom_df.columns:
         raise ValueError(f"Mapping Error: BOM Reference Column '{bom_ref_col}' not found.")
    if not xy_ref_col or xy_ref_col not in xy_df.columns:
         raise ValueError(f"Mapping Error: XY Reference Column '{xy_ref_col}' not found.")

    # 2. Normalize BOM
    print(f"Normalizing BOM using column: {bom_ref_col}")
    bom_df_exploded = normalize_bom_data(bom_df, bom_ref_col, delimiter=',') 

    # 3. Prepare Merge Keys
    bom_df_exploded['_JOIN_KEY'] = bom_df_exploded[bom_ref_col].astype(str).str.strip().str.upper()
    xy_df['_JOIN_KEY'] = xy_df[xy_ref_col].astype(str).str.strip().str.upper()

    # 4. Perform Outer Join
    merged_df = pd.merge(xy_df, bom_df_exploded, on='_JOIN_KEY', how='outer', indicator=True, suffixes=('_XY', '_BOM'))

    # 5. Process Results
    final_rows = []
    
    for _, row in merged_df.iterrows():
        merge_status = row['_merge']
        status = "UNKNOWN"
        if merge_status == 'both': status = "MATCHED"
        elif merge_status == 'left_only': status = "XY_ONLY"
        elif merge_status == 'right_only': status = "BOM_ONLY"
        
        new_row = {
            "Ref Des": row['_JOIN_KEY'],
            "Status": status,
            "Is Ignored": False,
            
            # --- XY DATA ---
            "Layer": row.get(mapping.get("Layer / Side"), ""),
            "Mid X": row.get(mapping.get("Mid X"), ""),
            "Mid Y": row.get(mapping.get("Mid Y"), ""),
            "Rotation": row.get(mapping.get("Rotation"), ""),
            
            # --- BOM DATA ---
            "Part Number": row.get(mapping.get("Part Number"), ""),
            "Description": row.get(mapping.get("Description"), ""),
            "Value": row.get(mapping.get("Value"), ""),
            "Footprint": row.get(mapping.get("Footprint"), ""),
            "Manufacturer": row.get(mapping.get("Manufacturer"), ""), # <--- NEW
            "Qty": row.get(mapping.get("Qty"), "")                    # <--- NEW
        }
        
        # Auto-Ignore Logic
        ref = str(new_row["Ref Des"])
        if ref.startswith("FID") or ref.startswith("TP") or ref.startswith("MH"):
            if status == "XY_ONLY":
                new_row["Is Ignored"] = True
                
        final_rows.append(new_row)

    return pd.DataFrame(final_rows)