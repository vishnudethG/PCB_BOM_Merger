import pandas as pd
from src.core.normalizer import normalize_bom_data
import re

def perform_merge_v2(bom_df, xy_df, mapping):
    print("\n!!! EXECUTING V2.1 LOGIC ENGINE (SMART FOOTPRINT) !!!")
    
    # --- 1. KEY RETRIEVAL ---
    bom_ref_col = mapping.get("BOM Reference Col")
    xy_ref_col = mapping.get("XY Reference Col")
    
    if not bom_ref_col or not xy_ref_col:
         raise ValueError("Mapping Error: Reference Columns missing.")

    # Get Column Names
    ref_x_col = mapping.get("Ref X") or mapping.get("Mid X")
    ref_y_col = mapping.get("Ref Y") or mapping.get("Mid Y")
    rot_col = mapping.get("Rotation")
    
    # Detect if we can grab footprint from XY as a backup
    # (We assume the column name is 'Footprint' in XY if not explicitly mapped)
    xy_footprint_col = None
    for col in xy_df.columns:
        if "footprint" in col.lower():
            xy_footprint_col = col
            break

    # --- 2. CLEAN UNITS FROM XY DATA ---
    if ref_x_col and ref_x_col in xy_df.columns:
        xy_df[ref_x_col] = _clean_numeric_col(xy_df[ref_x_col])
    if ref_y_col and ref_y_col in xy_df.columns:
        xy_df[ref_y_col] = _clean_numeric_col(xy_df[ref_y_col])
    if rot_col and rot_col in xy_df.columns:
        xy_df[rot_col] = _clean_numeric_col(xy_df[rot_col])

    # --- 3. PRE-PROCESS XY (PANEL LOGIC) ---
    print("Resolving Panels...")
    xy_clean = _resolve_panels_v2(xy_df, xy_ref_col, ref_y_col)

    # --- 4. PRE-PROCESS BOM ---
    print(f"Normalizing BOM...")
    bom_exploded = normalize_bom_data(bom_df, bom_ref_col, delimiter=',') 

    # --- 5. MERGE ---
    bom_exploded['_JOIN_KEY'] = bom_exploded[bom_ref_col].astype(str).str.strip().str.upper()
    xy_clean['_JOIN_KEY'] = xy_clean[xy_ref_col].astype(str).str.strip().str.upper()

    merged_df = pd.merge(xy_clean, bom_exploded, on='_JOIN_KEY', how='outer', indicator=True, suffixes=('_XY', '_BOM'))

    # --- 6. BUILD OUTPUT ---
    final_rows = []
    
    for _, row in merged_df.iterrows():
        merge_status = row['_merge']
        status = "MATCHED" if merge_status == 'both' else ("XY_ONLY" if merge_status == 'left_only' else "BOM_ONLY")
        
        # --- SMART FOOTPRINT FETCH ---
        # 1. Try BOM Mapping
        footprint = row.get(mapping.get("Footprint"), "")
        
        # 2. If BOM is empty, try XY Mapping or Auto-Detected XY Column
        if pd.isna(footprint) or str(footprint).strip() == "":
            # Try to get it from the XY side of the merge
            if xy_footprint_col and xy_footprint_col in row:
                footprint = row[xy_footprint_col]
            # Or check if it was suffixed during merge
            elif xy_footprint_col and f"{xy_footprint_col}_XY" in row:
                 footprint = row[f"{xy_footprint_col}_XY"]

        new_row = {
            "Ref Des": row['_JOIN_KEY'],
            "Status": status,
            "Is Ignored": False,
            "Layer": row.get(mapping.get("Layer") or mapping.get("Layer / Side"), ""),
            "Ref X": row.get(ref_x_col, ""),
            "Ref Y": row.get(ref_y_col, ""),
            "Rotation": row.get(rot_col, ""),
            "Part number": row.get(mapping.get("Part number") or mapping.get("Part Number"), ""),
            "VALUE": row.get(mapping.get("VALUE") or mapping.get("Value"), ""),
            "Footprint": str(footprint).strip(), # Uses the smart fallback result
            "Quantity": row.get(mapping.get("Quantity") or mapping.get("Qty"), ""),
            "Remark": str(row.get(mapping.get("Remark"), "")).strip()
        }
        
        # Auto-Ignore
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