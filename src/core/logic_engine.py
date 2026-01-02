import pandas as pd
from src.core.normalizer import normalize_bom_data
import re

def perform_merge_v2(bom_df, xy_df, mapping):
    print("\n!!! EXECUTING V3.1 LOGIC (PRESERVE BOM ORDER) !!!")
    
    # --- 1. KEY RETRIEVAL ---
    bom_ref_col = mapping.get("BOM Location Col")
    xy_ref_col = mapping.get("XY Location Col")
    
    if not bom_ref_col or not xy_ref_col:
         raise ValueError("Mapping Error: Location Columns missing.")

    ref_x_col = mapping.get("Center-X")
    ref_y_col = mapping.get("Center-Y")
    rot_col   = mapping.get("Rotation")

    # --- 2. CLEAN UNITS FROM XY DATA ---
    if ref_x_col and ref_x_col in xy_df.columns:
        xy_df[ref_x_col] = _clean_numeric_col(xy_df[ref_x_col])
    if ref_y_col and ref_y_col in xy_df.columns:
        xy_df[ref_y_col] = _clean_numeric_col(xy_df[ref_y_col])
    if rot_col and rot_col in xy_df.columns:
        xy_df[rot_col] = _clean_numeric_col(xy_df[rot_col])

    # --- 3. PRE-PROCESS XY ---
    print("Resolving Panels...")
    xy_clean = _resolve_panels_v2(xy_df, xy_ref_col, ref_y_col)

    # --- 4. PRE-PROCESS BOM (WITH ORDER TRACKING) ---
    print(f"Normalizing BOM...")
    bom_exploded = normalize_bom_data(bom_df, bom_ref_col, delimiter=',') 
    
    # [NEW] Capture the original order index
    # We assign a number (0, 1, 2...) to every row to remember its position
    bom_exploded['_BOM_ORDER'] = range(len(bom_exploded))

    # --- 5. MERGE ---
    bom_exploded['_JOIN_KEY'] = bom_exploded[bom_ref_col].astype(str).str.strip().str.upper()
    xy_clean['_JOIN_KEY'] = xy_clean[xy_ref_col].astype(str).str.strip().str.upper()

    merged_df = pd.merge(xy_clean, bom_exploded, on='_JOIN_KEY', how='outer', indicator=True, suffixes=('_XY', '_BOM'))

    # --- 6. BUILD OUTPUT ---
    final_rows = []
    
    for _, row in merged_df.iterrows():
        merge_status = row['_merge']
        status = "MATCHED" if merge_status == 'both' else ("XY_ONLY" if merge_status == 'left_only' else "BOM_ONLY")
        
        # [NEW] Get the Order Index (Default to 999999 for XY_ONLY items so they go to the end)
        bom_order = row.get("_BOM_ORDER")
        if pd.isna(bom_order): 
            bom_order = 999999
            
        new_row = {
            "Ref Des":     row['_JOIN_KEY'],
            "Status":      status,
            "Is Ignored":  False,
            "BOM_Order":   bom_order, # Pass this hidden value to the writer
            
            "Layer":       row.get(mapping.get("Layer"), ""),
            "Ref X":       row.get(ref_x_col, ""),
            "Ref Y":       row.get(ref_y_col, ""),
            "Rotation":    row.get(rot_col, ""),
            
            "Part Number": row.get(mapping.get("Part No."), ""),
            "Description": row.get(mapping.get("Description"), ""),
            "Quantity":    row.get(mapping.get("Quantity"), "")
        }
        
        ref = str(new_row["Ref Des"])
        if (ref.startswith("FID") or ref.startswith("TP") or ref.startswith("MH")) and status == "XY_ONLY":
            new_row["Is Ignored"] = True
                
        final_rows.append(new_row)

    return pd.DataFrame(final_rows)

def _clean_numeric_col(series):
    return series.astype(str).apply(
        lambda x: re.sub(r"[^\d\.\-]", "", x) if pd.notnull(x) else x
    )

def _resolve_panels_v2(xy_df, ref_col_name, y_col_name):
    if not y_col_name or y_col_name not in xy_df.columns:
        return xy_df
    temp_y = "__TEMP_Y"
    xy_df[temp_y] = pd.to_numeric(xy_df[y_col_name], errors='coerce')
    xy_sorted = xy_df.sort_values(by=temp_y, ascending=True)
    xy_deduped = xy_sorted.drop_duplicates(subset=ref_col_name, keep='first')
    return xy_deduped.drop(columns=[temp_y])