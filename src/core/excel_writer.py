import pandas as pd
import xlsxwriter

def generate_production_files(df, output_path):
    """
    Generates the PCB Production Workbook.
    Version: 4.1 (Final Polish: Blue Headers #BDD7EE, 35px Height).
    """
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
    workbook = writer.book
    
    # --- STYLES ---
    # Header: Blue background #BDD7EE, Bold, Border, Centered
    header_fmt = workbook.add_format({
        'bold': True, 
        'bg_color': '#BDD7EE',  # <--- NEW COLOR
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # Text Wrap Format for Location Column
    wrap_fmt = workbook.add_format({
        'text_wrap': True, 
        'border': 1,
        'valign': 'top'
    })
    
    # Standard Center Aligned Data
    center_fmt = workbook.add_format({
        'align': 'center', 
        'border': 1
    })

    # --- 1. DATA PREP ---
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
        df.loc[df['Part Number'].astype(str).str.strip() == "", 'Part Number'] = "DNP"

    # --- TAB 1: INTERNAL BOM ---
    df_internal = df[df['Status'] != 'XY_ONLY'].copy()
    df_internal_grouped = _group_bom_data(df_internal)
    df_internal_grouped.rename(columns={'Designator': 'Location'}, inplace=True)
    
    cols_bom = ['Part Number', 'Description', 'Location', 'Quantity']
    _write_custom_sheet(writer, df_internal_grouped, "Internal BOM", cols_bom, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=True, add_sl_no=False)


    # --- TAB 2: XY DATA (Renamed from XY Data Sheet) ---
    df_xy_master = df[df['Status'] != 'BOM_ONLY'].copy()
    df_xy_master.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'}, inplace=True)
    
    cols_xy = ['X', 'Y', 'Location', 'Rotation', 'Layer']
    _write_custom_sheet(writer, df_xy_master, "XY Data", cols_xy, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=False, add_sl_no=False)


    # --- TAB 3: BOM TOP ---
    df_bom_top = df_top_all[df_top_all['Status'] != 'XY_ONLY'].copy()
    df_bom_top_grouped = _group_bom_data(df_bom_top)
    df_bom_top_grouped['Layer'] = "TopLayer"
    df_bom_top_grouped.rename(columns={'Designator': 'Location'}, inplace=True)
    
    cols_bom_layer = ['Sl No.', 'Part Number', 'Description', 'Location', 'Quantity', 'Layer']
    _write_custom_sheet(writer, df_bom_top_grouped, "BOM Top", cols_bom_layer, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=True, add_sl_no=True)


    # --- TAB 4: BOM BOTTOM ---
    df_bom_bot = df_bot_all[df_bot_all['Status'] != 'XY_ONLY'].copy()
    df_bom_bot_grouped = _group_bom_data(df_bom_bot)
    df_bom_bot_grouped['Layer'] = "BottomLayer"
    df_bom_bot_grouped.rename(columns={'Designator': 'Location'}, inplace=True)
    
    _write_custom_sheet(writer, df_bom_bot_grouped, "BOM Bottom", cols_bom_layer, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=True, add_sl_no=True)


    # --- TAB 5: XY TOP ---
    df_xy_top = df_top_all[df_top_all['Status'] != 'BOM_ONLY'].copy()
    df_xy_top['Layer'] = "TopLayer"
    df_xy_top.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'}, inplace=True)
    
    cols_xy_enriched = ['Sl No.', 'Part Number', 'Location', 'X', 'Y', 'Rotation', 'Description', 'Layer']
    _write_custom_sheet(writer, df_xy_top, "XY Top", cols_xy_enriched, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=True, add_sl_no=True)


    # --- TAB 6: XY BOTTOM ---
    df_xy_bot = df_bot_all[df_bot_all['Status'] != 'BOM_ONLY'].copy()
    df_xy_bot['Layer'] = "BottomLayer"
    df_xy_bot.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'}, inplace=True)
    
    _write_custom_sheet(writer, df_xy_bot, "XY Bottom", cols_xy_enriched, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=True, add_sl_no=True)


    # --- TAB 7: EXCEPTIONS REPORT ---
    mask_error = (df['Status'] != 'MATCHED') & (df['Is Ignored'] == False)
    df_errors = df[mask_error].copy()
    df_errors['Issue Type'] = "Unknown Error"
    df_errors.loc[df_errors['Status'] == 'XY_ONLY', 'Issue Type'] = 'On Board but Missing from BOM (DNP?)'
    df_errors.loc[df_errors['Status'] == 'BOM_ONLY', 'Issue Type'] = 'In BOM but Missing from Board'
    
    df_errors.rename(columns={'Ref Des': 'Location'}, inplace=True)
    cols_err = ['Location', 'Issue Type', 'Part Number', 'Layer', 'Description']
    
    _write_custom_sheet(writer, df_errors, "Exceptions Report", cols_err, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=True, add_sl_no=False)
    
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
    if 'BOM_Order' in df.columns:
        agg_rules['BOM_Order'] = 'min'

    grouped = df.groupby(valid_group_cols).agg(agg_rules).reset_index()
    grouped.rename(columns={'Ref Des': 'Designator'}, inplace=True)
    grouped['Quantity'] = grouped['Designator'].apply(lambda x: len(str(x).split(',')))
    
    return grouped

def _write_custom_sheet(writer, df, sheet_name, cols, header_fmt, wrap_fmt, center_fmt, 
                        sort_by_bom_order=False, add_sl_no=False):
    
    if df.empty:
        # Write Empty Header
        pd.DataFrame(columns=[c for c in cols if c != 'Sl No.']).to_excel(writer, sheet_name=sheet_name, index=False)
        return

    final_df = df.copy()

    # 1. SORTING
    if sort_by_bom_order and 'BOM_Order' in final_df.columns:
        final_df = final_df.sort_values(by=['BOM_Order', 'Location' if 'Location' in final_df else 'Designator'])
    else:
        sort_col = 'Location' if 'Location' in final_df.columns else ('Designator' if 'Designator' in final_df.columns else None)
        if sort_col: final_df = final_df.sort_values(by=sort_col)

    # 2. ADD SERIAL NUMBER
    if add_sl_no:
        final_df.reset_index(drop=True, inplace=True)
        final_df['Sl No.'] = final_df.index + 1

    # 3. FILTER COLUMNS
    export_data = pd.DataFrame()
    for col in cols:
        export_data[col] = final_df[col] if col in final_df.columns else ""

    # 4. WRITE DATA
    export_data.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
    
    # 5. APPLY FORMATTING
    worksheet = writer.sheets[sheet_name]
    
    # --- [NEW] SET HEADER HEIGHT TO 35 PIXELS ---
    worksheet.set_row_pixels(0, 35)

    for idx, col_name in enumerate(cols):
        worksheet.write(0, idx, col_name, header_fmt)
        
        if col_name == "Location":
            worksheet.set_column(idx, idx, 50, wrap_fmt)
        elif col_name == "Sl No.":
            worksheet.set_column(idx, idx, 8, center_fmt)
        else:
            max_len = len(col_name)
            if not export_data.empty:
                sample_len = export_data[col_name].head(50).astype(str).map(len).max()
                if pd.notna(sample_len):
                    max_len = max(max_len, sample_len)
            
            final_width = min(max_len + 4, 40)
            worksheet.set_column(idx, idx, final_width, center_fmt)