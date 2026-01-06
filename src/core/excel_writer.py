import pandas as pd
import xlsxwriter

def generate_production_files(df, output_path):
    """
    Generates the PCB Production Workbook.
    Version: 4.2 (Fixed Infinite Borders + Added Remarks)
    """
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
    workbook = writer.book
    
    # --- STYLES ---
    header_fmt = workbook.add_format({
        'bold': True, 
        'bg_color': '#BDD7EE', 
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    wrap_fmt = workbook.add_format({
        'text_wrap': True, 
        'border': 1,
        'valign': 'top'
    })
    
    center_fmt = workbook.add_format({
        'align': 'center', 
        'border': 1
    })

    # --- DATA PREP ---
    cols_numeric = ['Ref X', 'Ref Y', 'Rotation']
    for c in cols_numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    if 'Layer' in df.columns:
        df['Layer_Classified'] = df['Layer'].apply(_classify_layer)
    else:
        df['Layer_Classified'] = "Unknown"

    df_top_all = df[df['Layer_Classified'] == 'Top'].copy()
    df_bot_all = df[df['Layer_Classified'] == 'Bottom'].copy()
    
    if 'Part Number' in df.columns:
        df['Part Number'] = df['Part Number'].fillna("")
        mask_blank = df['Part Number'].astype(str).str.strip() == ""
        df.loc[mask_blank, 'Part Number'] = "DNP"

    # --- TAB 1: INTERNAL BOM ---
    df_internal = df[df['Status'] != 'XY_ONLY'].copy()
    df_internal_grouped = _group_bom_data(df_internal)
    df_internal_grouped.rename(columns={'Designator': 'Location'}, inplace=True)
    
    _write_custom_sheet(writer, df_internal_grouped, "Internal BOM", 
                        ['Part Number', 'Description', 'Location', 'Quantity'], 
                        header_fmt, wrap_fmt, center_fmt, sort_by_bom_order=True)

    # --- TAB 2: XY DATA ---
    df_xy_master = df[df['Status'] != 'BOM_ONLY'].copy()
    df_xy_master.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'}, inplace=True)
    
    _write_custom_sheet(writer, df_xy_master, "XY Data", 
                        ['X', 'Y', 'Location', 'Rotation', 'Layer'], 
                        header_fmt, wrap_fmt, center_fmt, sort_by_bom_order=False)

    # --- TAB 3: BOM TOP ---
    df_bom_top = df_top_all[df_top_all['Status'] != 'XY_ONLY'].copy()
    df_bom_top_grouped = _group_bom_data(df_bom_top)
    df_bom_top_grouped['Layer'] = "TopLayer"
    df_bom_top_grouped.rename(columns={'Designator': 'Location'}, inplace=True)
    
    _write_custom_sheet(writer, df_bom_top_grouped, "BOM Top", 
                        ['Sl No.', 'Part Number', 'Description', 'Location', 'Quantity', 'Layer'], 
                        header_fmt, wrap_fmt, center_fmt, sort_by_bom_order=True, add_sl_no=True)

    # --- TAB 4: BOM BOTTOM ---
    df_bom_bot = df_bot_all[df_bot_all['Status'] != 'XY_ONLY'].copy()
    df_bom_bot_grouped = _group_bom_data(df_bom_bot)
    df_bom_bot_grouped['Layer'] = "BottomLayer"
    df_bom_bot_grouped.rename(columns={'Designator': 'Location'}, inplace=True)
    
    _write_custom_sheet(writer, df_bom_bot_grouped, "BOM Bottom", 
                        ['Sl No.', 'Part Number', 'Description', 'Location', 'Quantity', 'Layer'], 
                        header_fmt, wrap_fmt, center_fmt, sort_by_bom_order=True, add_sl_no=True)

    # --- TAB 5: XY TOP ---
    df_xy_top = df_top_all[df_top_all['Status'] != 'BOM_ONLY'].copy()
    df_xy_top['Layer'] = "TopLayer"
    df_xy_top.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'}, inplace=True)
    
    _write_custom_sheet(writer, df_xy_top, "XY Top", 
                        ['Sl No.', 'Part Number', 'Location', 'X', 'Y', 'Rotation', 'Description', 'Layer'], 
                        header_fmt, wrap_fmt, center_fmt, sort_by_bom_order=True, add_sl_no=True)

    # --- TAB 6: XY BOTTOM ---
    df_xy_bot = df_bot_all[df_bot_all['Status'] != 'BOM_ONLY'].copy()
    df_xy_bot['Layer'] = "BottomLayer"
    df_xy_bot.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'}, inplace=True)
    
    _write_custom_sheet(writer, df_xy_bot, "XY Bottom", 
                        ['Sl No.', 'Part Number', 'Location', 'X', 'Y', 'Rotation', 'Description', 'Layer'], 
                        header_fmt, wrap_fmt, center_fmt, sort_by_bom_order=True, add_sl_no=True)

    # --- TAB 7: EXCEPTIONS REPORT (With Remarks) ---
    mask_error = (df['Status'] != 'MATCHED') & (df['Is Ignored'] == False)
    df_errors = df[mask_error].copy()
    df_errors['Issue Type'] = "Unknown Error"
    df_errors.loc[df_errors['Status'] == 'XY_ONLY', 'Issue Type'] = 'On Board but Missing from BOM (DNP?)'
    df_errors.loc[df_errors['Status'] == 'BOM_ONLY', 'Issue Type'] = 'In BOM but Missing from Board'
    
    df_errors.rename(columns={'Ref Des': 'Location'}, inplace=True)
    
    # Added 'Remarks' to export list
    cols_err = ['Location', 'Issue Type', 'Part Number', 'Layer', 'Description', 'Remarks']
    
    _write_custom_sheet(writer, df_errors, "Exceptions Report", cols_err, 
                        header_fmt, wrap_fmt, center_fmt, sort_by_bom_order=True, add_sl_no=False)
    
    if not df_errors.empty:
        ws = writer.sheets['Exceptions Report']
        ws.set_tab_color('#C00000')

    writer.close()
    return output_path

def _classify_layer(val):
    s = str(val).strip().lower()
    if s in ['b', 'bottom', 'bot', 'bottomlayer', 'bottom layer', 'back', 'solder']: return 'Bottom'
    if s in ['t', 'top', 'toplayer', 'top layer', 'front', 'component']: return 'Top'
    return 'Unknown'

def _group_bom_data(df):
    if df.empty: return df
    fill_cols = ['Part Number', 'Description']
    for c in fill_cols:
        if c in df.columns: df[c] = df[c].fillna('')
    valid_group_cols = [c for c in fill_cols if c in df.columns]
    if not valid_group_cols: return df
    agg_rules = {'Ref Des': lambda x: ', '.join(sorted(x.astype(str)))}
    if 'BOM_Order' in df.columns: agg_rules['BOM_Order'] = 'min'
    grouped = df.groupby(valid_group_cols).agg(agg_rules).reset_index()
    grouped.rename(columns={'Ref Des': 'Designator'}, inplace=True)
    grouped['Quantity'] = grouped['Designator'].apply(lambda x: len(str(x).split(',')))
    return grouped

def _write_custom_sheet(writer, df, sheet_name, cols, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=False, add_sl_no=False):
    
    if df.empty:
        pd.DataFrame(columns=[c for c in cols if c != 'Sl No.']).to_excel(writer, sheet_name=sheet_name, index=False)
        return

    final_df = df.copy()

    # Sort
    if sort_by_bom_order and 'BOM_Order' in final_df.columns:
        final_df = final_df.sort_values(by=['BOM_Order', 'Location' if 'Location' in final_df else 'Designator'])
    else:
        sort_col = 'Location' if 'Location' in final_df.columns else ('Designator' if 'Designator' in final_df.columns else None)
        if sort_col: final_df = final_df.sort_values(by=sort_col)

    # Add Sl No
    if add_sl_no:
        final_df.reset_index(drop=True, inplace=True)
        final_df['Sl No.'] = final_df.index + 1

    # Filter Columns (Ensure Remarks exists if requested)
    export_data = pd.DataFrame()
    for col in cols:
        export_data[col] = final_df[col] if col in final_df.columns else ""

    # --- WRITE DATA & FORMATTING (Fixed Logic) ---
    export_data.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
    
    worksheet = writer.sheets[sheet_name]
    worksheet.set_row_pixels(0, 35)

    # 1. Write Headers & Set Column Widths (Decoupled from styling data)
    for idx, col_name in enumerate(cols):
        worksheet.write(0, idx, col_name, header_fmt)
        
        # Determine Width
        max_len = len(col_name)
        if not export_data.empty:
            sample_len = export_data[col_name].head(50).astype(str).map(len).max()
            if pd.notna(sample_len): max_len = max(max_len, sample_len)
        
        final_width = min(max_len + 4, 50)
        
        # Set Width ONLY (No format passed here!)
        worksheet.set_column(idx, idx, final_width)

    # 2. Apply Styles specifically to the data cells
    # This prevents the style from bleeding to the bottom of the sheet
    for row_idx, row_data in enumerate(export_data.values):
        excel_row = row_idx + 1
        for col_idx, value in enumerate(row_data):
            col_name = cols[col_idx]
            
            # Choose Format
            if col_name == "Location": cell_fmt = wrap_fmt
            elif col_name == "Sl No.": cell_fmt = center_fmt
            else: cell_fmt = center_fmt
            
            # Write with Format
            # Handle NaN/None
            if pd.isna(value): value = ""
            worksheet.write(excel_row, col_idx, value, cell_fmt)