import pandas as pd
import xlsxwriter

def generate_production_files(df, output_path):
    """
    Generates the specific reports requested:
    1. Internal BOM (Grouped by Part Number, Comma-separated Locations)
    2. XY Data Sheet (All XY locations with numeric format)
    3. XY Data Top (Top side specific format with DNP and fixed Layer name)
    4. XY Data Bottom (Bottom side specific format with DNP and fixed Layer name)
    """
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
    workbook = writer.book
    
    # Formats
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    
    # --- 1. DATA PRE-PROCESSING ---
    
    # Convert Coordinates and Rotation to Numeric (Float)
    cols_to_numeric = ['Mid X', 'Mid Y', 'Rotation']
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Normalize Layer Column for splitting
    # Note: .str.lower() returns a Series, so we must use .str again to strip
    df['Layer_Norm'] = df['Layer'].astype(str).str.lower().str.strip()
    
    mask_bot = (df['Layer_Norm'].str.contains('bot')) | \
               (df['Layer_Norm'].str.contains('back')) | \
               (df['Layer_Norm'].str.contains('solder'))
    
    # Create Subsets
    df_internal_raw = df[df['Status'] != 'XY_ONLY'].copy()
    df_xy_all = df[df['Status'] != 'BOM_ONLY'].copy()
    
    # Top/Bottom Split (include everything with a location)
    df_top = df[~mask_bot & (df['Status'] != 'BOM_ONLY')].copy()
    df_bot = df[mask_bot].copy()


    # --- TAB 1: Internal BOM ---
    # Group by Part Number & Description to merge Locations
    
    df_internal_raw['Part Number'] = df_internal_raw['Part Number'].fillna('')
    df_internal_raw['Description'] = df_internal_raw['Description'].fillna('')
    
    # Grouping Logic
    df_internal_grouped = df_internal_raw.groupby(['Part Number', 'Description'])['Ref Des'].apply(
        lambda x: ', '.join(sorted(x.astype(str)))
    ).reset_index()
    
    df_internal_grouped.rename(columns={'Ref Des': 'Location'}, inplace=True)
    
    cols_internal = ['Part Number', 'Description', 'Location']
    _write_sheet(writer, df_internal_grouped, "Internal BOM", cols_internal, header_fmt)


    # --- TAB 2: XY Data Sheet ---
    df_xy_all.rename(columns={
        'Mid X': 'X',
        'Mid Y': 'Y',
        'Ref Des': 'Location'
    }, inplace=True)
    
    cols_xy_sheet = ['X', 'Y', 'Location', 'Rotation', 'Layer']
    _write_sheet(writer, df_xy_all, "XY Data Sheet", cols_xy_sheet, header_fmt)


    # --- TAB 3: XY Data Top ---
    # Req: Part Number ("DNP" if blank), Location, X, Y, Rotation, Layer ("TopLayer")
    
    # 1. Handle DNP
    df_top['Part Number'] = df_top['Part Number'].fillna("DNP")
    # FIX IS HERE: Added .str before .strip()
    df_top.loc[df_top['Part Number'].astype(str).str.strip() == "", 'Part Number'] = "DNP"
    
    # 2. Hardcode Layer Name
    df_top['Layer'] = "TopLayer"
    
    # 3. Rename Columns
    df_top.rename(columns={
        'Ref Des': 'Location',
        'Mid X': 'X',
        'Mid Y': 'Y'
    }, inplace=True)
    
    cols_xy_top = ['Part Number', 'Location', 'X', 'Y', 'Rotation', 'Layer']
    _write_sheet(writer, df_top, "XY Data Top", cols_xy_top, header_fmt)


    # --- TAB 4: XY Data Bottom ---
    
    # 1. Handle DNP
    df_bot['Part Number'] = df_bot['Part Number'].fillna("DNP")
    # FIX IS HERE: Added .str before .strip()
    df_bot.loc[df_bot['Part Number'].astype(str).str.strip() == "", 'Part Number'] = "DNP"
    
    # 2. Hardcode Layer Name
    df_bot['Layer'] = "BottomLayer"
    
    # 3. Rename Columns
    df_bot.rename(columns={
        'Ref Des': 'Location',
        'Mid X': 'X',
        'Mid Y': 'Y'
    }, inplace=True)
    
    # Output
    _write_sheet(writer, df_bot, "XY Data Bottom", cols_xy_top, header_fmt)

    # Save File
    writer.close()
    return output_path

def _write_sheet(writer, df, sheet_name, cols, header_fmt):
    """Helper to write a clean sheet."""
    if df.empty:
        pd.DataFrame(columns=cols).to_excel(writer, sheet_name=sheet_name, index=False)
        return

    # Select cols
    final_df = pd.DataFrame()
    for col in cols:
        if col in df.columns:
            final_df[col] = df[col]
        else:
            final_df[col] = "" 

    # Sort
    if "Location" in final_df.columns:
        final_df = final_df.sort_values(by="Location")

    # Write Data
    final_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)

    # Header & Format
    worksheet = writer.sheets[sheet_name]
    for col_num, value in enumerate(cols):
        worksheet.write(0, col_num, value, header_fmt)
        
        max_len = len(value)
        if not final_df.empty:
             data_len = final_df[value].astype(str).map(len).max()
             if pd.notna(data_len):
                 max_len = max(max_len, data_len)
        
        worksheet.set_column(col_num, col_num, max_len + 2)