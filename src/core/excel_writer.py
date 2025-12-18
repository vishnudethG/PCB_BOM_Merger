import pandas as pd
import xlsxwriter

def generate_production_files(df, output_path):
    """
    Generates a multi-sheet Excel file with 6 specific reports:
    1. Internal BOM (All BOM parts)
    2. XY Data Sheet (All XY locations)
    3. XY Data Top (Merged data for Top)
    4. XY Data Bottom (Merged data for Bottom)
    5. Top BOM (BOM parts on Top)
    6. Bottom BOM (BOM parts on Bottom)
    """
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
    workbook = writer.book
    
    # Formats
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    
    # --- PREPARE DATA SUBSETS ---
    
    # Normalize Layer Column for filtering
    df['Layer_Norm'] = df['Layer'].astype(str).str.lower().str.strip()
    
    # Filter: Bottom Parts
    mask_bot = (df['Layer_Norm'].str.contains('bot')) | \
               (df['Layer_Norm'].str.contains('back')) | \
               (df['Layer_Norm'].str.contains('solder'))
    
    # Filter: Top Parts (Everything NOT Bottom that has XY data)
    df_bot = df[mask_bot].copy()
    df_top = df[~mask_bot & (df['Status'] != 'BOM_ONLY')].copy()
    
    # Filter: All BOM Items (Everything except XY_ONLY)
    df_all_bom = df[df['Status'] != 'XY_ONLY'].copy()
    
    # Filter: All XY Items (Everything except BOM_ONLY)
    df_all_xy = df[df['Status'] != 'BOM_ONLY'].copy()

    # --- GENERATE SHEETS ---

    # SHEET 1: Internal BOM
    # Cols: Part No, Description, Value, Manufacturer, Location, Qty
    cols_internal = ["Part Number", "Description", "Value", "Manufacturer", "Ref Des", "Qty"]
    _write_sheet(writer, df_all_bom, "Internal BOM", cols_internal, header_fmt)

    # SHEET 2: XY Data Sheet
    # Cols: Location, Layer, Center-Y, Center-X, Rotation
    cols_xy_raw = ["Ref Des", "Layer", "Mid Y", "Mid X", "Rotation"]
    _write_sheet(writer, df_all_xy, "XY Data Sheet", cols_xy_raw, header_fmt)

    # SHEET 3: XY Data Top
    # Cols: Part No, Location, X, Y, Rotation, Description, Side
    cols_xy_merged = ["Part Number", "Ref Des", "Mid X", "Mid Y", "Rotation", "Description", "Layer"]
    _write_sheet(writer, df_top, "XY Data Top", cols_xy_merged, header_fmt)

    # SHEET 4: XY Data Bottom
    _write_sheet(writer, df_bot, "XY Data Bottom", cols_xy_merged, header_fmt)

    # SHEET 5: Top BOM
    # Cols: Part No, Description, Location, Qty
    cols_bom_layer = ["Part Number", "Description", "Ref Des", "Qty"]
    _write_sheet(writer, df_top, "Top BOM", cols_bom_layer, header_fmt)

    # SHEET 6: Bottom BOM
    _write_sheet(writer, df_bot, "Bottom BOM", cols_bom_layer, header_fmt)

    writer.close()
    return output_path

def _write_sheet(writer, df, sheet_name, cols, header_fmt):
    """Helper to write a clean sheet with mapped columns."""
    if df.empty:
        pd.DataFrame(columns=cols).to_excel(writer, sheet_name=sheet_name, index=False)
        return

    # Select only the required columns
    final_df = pd.DataFrame()
    for col in cols:
        if col in df.columns:
            final_df[col] = df[col]
        else:
            final_df[col] = "" # Fill empty if missing

    # Sort by Ref Des
    if "Ref Des" in final_df.columns:
        final_df = final_df.sort_values(by="Ref Des")

    # Write Data
    final_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)

    # Write Header & Format
    worksheet = writer.sheets[sheet_name]
    for col_num, value in enumerate(cols):
        worksheet.write(0, col_num, value, header_fmt)
        
        # Auto-width
        max_len = len(value)
        if not final_df.empty:
             data_len = final_df[value].astype(str).map(len).max()
             if pd.notna(data_len):
                 max_len = max(max_len, data_len)
        
        worksheet.set_column(col_num, col_num, max_len + 2)