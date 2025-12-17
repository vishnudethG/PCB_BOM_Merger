
import pandas as pd

def perform_merge_and_validation(bom_df, xy_df, mapping):
    """
    Merges BOM and XY based on the mapped Reference Designator columns.
    Returns: A unified DataFrame with a 'status' column (MATCHED, XY_ONLY, BOM_ONLY).
    """
    # 1. Identify Key Columns from Mapping
    bom_ref_col = mapping.get("Reference Designator") # e.g. "Part Ref"
    xy_ref_col = mapping.get("Reference Designator")  # e.g. "Designator" (Assuming user mapped same or we handle split)
    
    # Note: In our UI we had one "Reference Designator" mapping. 
    # We assume the user selected the BOM column name.
    # We need to find the equivalent in XY. Usually standardizing both works best.
    
    # Standardize Keys for Joining (Create temp columns)
    # We assume 'Ref Des' is the normalized column in BOM from previous step
    # We need to ensure we know the XY Ref column. 
    # For this implementation, we will try to auto-detect the XY ref col if not explicitly separated in UI.
    
    # --- HELPER: Find XY Ref Column ---
    # In Screen 2, if we mapped "Reference Designator" to a BOM column, 
    # we need to find the matching XY column. 
    # A robust app would have 2 dropdowns. 
    # For now, let's look for the mapped name, OR standard "Ref", "Designator".
    xy_key = None
    if bom_ref_col in xy_df.columns:
        xy_key = bom_ref_col
    else:
        # Fallback search
        for c in xy_df.columns:
            if "des" in c.lower() or "ref" in c.lower():
                xy_key = c
                break
    
    if not xy_key:
        raise ValueError("Could not find Reference Designator column in XY file.")

    # 2. Prepare Dataframes for Merge
    # Standardize keys to Uppercase/Trimmed for the join
    bom_df['_JOIN_KEY'] = bom_df[bom_ref_col].astype(str).str.strip().str.upper()
    xy_df['_JOIN_KEY'] = xy_df[xy_key].astype(str).str.strip().str.upper()

    # 3. Perform Outer Join
    # indicator=True creates a '_merge' column: 'left_only', 'right_only', 'both'
    # left = XY, right = BOM (We treat XY as the physical master)
    merged_df = pd.merge(xy_df, bom_df, on='_JOIN_KEY', how='outer', indicator=True, suffixes=('_XY', '_BOM'))

    # 4. Process Results & Rename Columns based on Mapping
    final_rows = []
    
    for _, row in merged_df.iterrows():
        # Determine Status
        merge_status = row['_merge']
        status = "UNKNOWN"
        if merge_status == 'both': status = "MATCHED"
        elif merge_status == 'left_only': status = "XY_ONLY"  # In XY, missing BOM
        elif merge_status == 'right_only': status = "BOM_ONLY" # In BOM, missing XY
        
        # Build Unified Row
        new_row = {
            "Ref Des": row['_JOIN_KEY'],
            "Status": status,
            "Is Ignored": False, # Default
            # XY Data (Handle if missing)
            "Layer": row.get(mapping.get("Layer / Side"), ""),
            "Mid X": row.get(mapping.get("Mid X"), ""),
            "Mid Y": row.get(mapping.get("Mid Y"), ""),
            "Rotation": row.get(mapping.get("Rotation"), ""),
            # BOM Data (Handle if missing)
            "Part Number": row.get(mapping.get("Part Number"), ""),
            "Value": row.get(mapping.get("Value"), ""),
            "Footprint": row.get(mapping.get("Footprint"), ""),
            "Description": row.get(mapping.get("Description"), "")
        }
        
        # Auto-Ignore logic for Fiducials (Optional, can be expanded)
        ref = new_row["Ref Des"]
        if ref.startswith("FID") or ref.startswith("TP") or ref.startswith("MH"):
            if status == "XY_ONLY":
                new_row["Is Ignored"] = True
                
        final_rows.append(new_row)

    return pd.DataFrame(final_rows)