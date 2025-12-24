import pandas as pd
import xlsxwriter

def generate_production_files(df, output_path):
    """
    Generates the PCB Production Workbook.
    Version: 2.2 (Smart Layer Classification for T/B/Top/Bottom).
    """
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
    workbook = writer.book
    
    # --- STYLES ---
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    
    # --- 1. DATA PREPARATION ---
    
    # A. Fix Column Names (Capitalization)
    if "Part number" in df.columns and "Part Number" not in df.columns:
        df.rename(columns={"Part number": "Part Number"}, inplace=True)
    if "Qty" in df.columns and "Quantity" not in df.columns:
        df.rename(columns={"Qty": "Quantity"}, inplace=True)

    # B. Numeric Conversion
    cols_numeric = ['Ref X', 'Ref Y', 'Rotation']
    for c in cols_numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # C. SMART LAYER CLASSIFICATION (The Fix)
    # We create a normalized column to decide Top vs Bottom safely
    if 'Layer' in df.columns:
        df['Layer_Classified'] = df['Layer'].apply(_classify_layer)
    else:
        df['Layer_Classified'] = "Unknown"

    # Split Data based on the new classified column
    # Top = Explicit Top OR (Unknown but valid XY position) - defaulting Unknown to Top is risky, 
    # so we strictly filter for Top/Bottom sheets, and put Unknowns in Exceptions.
    
    df_top_all = df[df['Layer_Classified'] == 'Top'].copy()
    df_bot_all = df[df['Layer_Classified'] == 'Bottom'].copy()
    
    # D. Handle DNP
    if 'Part Number' in df.columns:
        df['Part Number'] = df['Part Number'].fillna("")
        df.loc[df['Part Number'].astype(str).str.strip() == "", 'Part Number'] = "DNP"
    else:
        df['Part Number'] = "DNP"


    # --- TAB 1: INTERNAL BOM ---
    df_internal = df[df['Status'] != 'XY_ONLY'].copy()
    df_internal_grouped = _group_bom_data(df_internal)
    
    cols_bom = ['Part Number', 'VALUE', 'Footprint', 'Designator', 'Quantity', 'Remark']
    _write_sheet(writer, df_internal_grouped, "Internal BOM", cols_bom, header_fmt)


    # --- TAB 2: XY DATA SHEET ---
    df_xy_master = df[df['Status'] != 'BOM_ONLY'].copy()
    
    df_xy_master.rename(columns={'Ref Des': 'Designator'}, inplace=True)
    cols_xy = ['Designator', 'Ref X', 'Ref Y', 'Layer', 'Rotation']
    
    _write_sheet(writer, df_xy_master, "XY Data Sheet", cols_xy, header_fmt)


    # --- TAB 3: BOM TOP ---
    df_bom_top = df_top_all[df_top_all['Status'] != 'XY_ONLY'].copy()
    df_bom_top_grouped = _group_bom_data(df_bom_top)
    df_bom_top_grouped['Layer'] = "TopLayer" # Force standard name for output
    
    cols_bom_layer = ['Part Number', 'VALUE', 'Footprint', 'Designator', 'Quantity', 'Remark', 'Layer']
    _write_sheet(writer, df_bom_top_grouped, "BOM Top", cols_bom_layer, header_fmt)


    # --- TAB 4: BOM BOTTOM ---
    df_bom_bot = df_bot_all[df_bot_all['Status'] != 'XY_ONLY'].copy()
    df_bom_bot_grouped = _group_bom_data(df_bom_bot)
    df_bom_bot_grouped['Layer'] = "BottomLayer"
    
    _write_sheet(writer, df_bom_bot_grouped, "BOM Bottom", cols_bom_layer, header_fmt)


    # --- TAB 5: XY TOP ---
    df_xy_top = df_top_all[df_top_all['Status'] != 'BOM_ONLY'].copy()
    df_xy_top['Layer'] = "TopLayer"
    df_xy_top.rename(columns={'Ref Des': 'Designator'}, inplace=True)
    
    cols_xy_enriched = ['Designator', 'Ref X', 'Ref Y', 'Layer', 'Rotation', 'Part Number', 'Footprint']
    _write_sheet(writer, df_xy_top, "XY Top", cols_xy_enriched, header_fmt)


    # --- TAB 6: XY BOTTOM ---
    df_xy_bot = df_bot_all[df_bot_all['Status'] != 'BOM_ONLY'].copy()
    df_xy_bot['Layer'] = "BottomLayer"
    df_xy_bot.rename(columns={'Ref Des': 'Designator'}, inplace=True)
    
    _write_sheet(writer, df_xy_bot, "XY Bottom", cols_xy_enriched, header_fmt)


    # --- TAB 7: EXCEPTIONS REPORT ---
    # 1. Standard Errors (Status Mismatches)
    mask_mismatch = (df['Status'] != 'MATCHED') & (df['Is Ignored'] == False)
    
    # 2. Layer Errors (Unknown Layers)
    # If the layer wasn't T/B/Top/Bottom, we flag it here so the user knows!
    mask_bad_layer = (df['Layer_Classified'] == 'Unknown') & (df['Status'] != 'BOM_ONLY')
    
    mask_error = mask_mismatch | mask_bad_layer
    df_errors = df[mask_error].copy()
    
    # Define Error Messages
    df_errors['Issue Type'] = "Unknown Error"
    
    # Apply labels safely
    df_errors.loc[df_errors['Status'] == 'XY_ONLY', 'Issue Type'] = 'On Board but Missing from BOM (DNP?)'
    df_errors.loc[df_errors['Status'] == 'BOM_ONLY', 'Issue Type'] = 'In BOM but Missing from Board (No Coordinates)'
    df_errors.loc[df_errors['Layer_Classified'] == 'Unknown', 'Issue Type'] = 'Unknown Layer Name (Check Input File)'
    
    cols_err = ['Ref Des', 'Issue Type', 'Part Number', 'Layer', 'Remark']
    _write_sheet(writer, df_errors, "Exceptions Report", cols_err, header_fmt)
    
    if not df_errors.empty:
        ws = writer.sheets['Exceptions Report']
        ws.set_tab_color('red')

    writer.close()
    return output_path

def _classify_layer(val):
    """
    Standardizes Layer names.
    Handles: T, Top, TopLayer, B, Bottom, BottomLayer, etc.
    """
    s = str(val).strip().lower()
    
    # BOTTOM VARIANTS
    if s in ['b', 'bottom', 'bot', 'bottomlayer', 'bottom layer', 'bottom_layer', 'solder', 'back']:
        return 'Bottom'
    
    # TOP VARIANTS
    if s in ['t', 'top', 'toplayer', 'top layer', 'top_layer', 'front', 'component']:
        return 'Top'
        
    return 'Unknown'

def _group_bom_data(df):
    if df.empty: return df
    
    if "Part number" in df.columns:
        df.rename(columns={"Part number": "Part Number"}, inplace=True)

    fill_cols = ['Part Number', 'VALUE', 'Footprint', 'Remark', 'Quantity']
    for c in fill_cols:
        if c in df.columns:
            df[c] = df[c].fillna('')

    valid_group_cols = [c for c in fill_cols if c in df.columns]
    if not valid_group_cols: return df

    grouped = df.groupby(valid_group_cols)['Ref Des'].apply(
        lambda x: ', '.join(sorted(x.astype(str)))
    ).reset_index()
    
    grouped.rename(columns={'Ref Des': 'Designator'}, inplace=True)
    return grouped

def _write_sheet(writer, df, sheet_name, cols, header_fmt):
    if df.empty:
        pd.DataFrame(columns=cols).to_excel(writer, sheet_name=sheet_name, index=False)
        return

    final_df = pd.DataFrame()
    for col in cols:
        final_df[col] = df[col] if col in df.columns else ""

    sort_col = 'Designator' if 'Designator' in final_df.columns else ('Ref Des' if 'Ref Des' in final_df.columns else None)
    if sort_col:
        final_df = final_df.sort_values(by=sort_col)

    final_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)

    worksheet = writer.sheets[sheet_name]
    for idx, col_name in enumerate(cols):
        worksheet.write(0, idx, col_name, header_fmt)
        max_len = len(col_name)
        if not final_df.empty:
             data_len = final_df[col_name].astype(str).map(len).max()
             if pd.notna(data_len):
                 max_len = max(max_len, data_len)
        worksheet.set_column(idx, idx, max_len + 2)