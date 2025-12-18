# src/core/file_loader.py
import pandas as pd
import openpyxl
import xlrd  # <--- NEW IMPORT
import os

HEADER_KEYWORDS = [
    "ref", "reference", "designator", "part", "component", 
    "value", "qty", "quantity", "description", "footprint"
]

def load_and_clean_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # --- EXCEL HANDLING (Unchanged) ---
    if ext in ['.xlsx', '.xlsm']:
        df = _process_xlsx_with_unmerge(file_path)
        df = _find_and_set_header(df) # Clean up headers
        return df
    
    elif ext == '.xls':
        df = _process_xls_with_unmerge(file_path)
        df = _find_and_set_header(df) # Clean up headers
        return df
        
    # --- TEXT/CSV HANDLING (NEW ROBUST LOGIC) ---
    elif ext in ['.csv', '.txt']:
        # 1. Detect Encoding & Delimiter manually first
        encoding_to_use = 'utf-8'
        start_row = 0
        delimiter = ','
        
        # List of candidate encodings
        encodings = ['utf-8', 'cp1252', 'latin1']
        
        # Read the raw file content first to find the Header Row
        raw_lines = []
        found_encoding = False
        
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    # Read first 50 lines to sniff structure
                    raw_lines = [f.readline() for _ in range(50)]
                encoding_to_use = enc
                found_encoding = True
                break
            except UnicodeDecodeError:
                continue
        
        if not found_encoding:
            raise ValueError("Could not decode file with standard encodings (UTF-8, CP1252).")

        # 2. Find the Header Row Index in the raw text
        # We look for a line containing at least 2 keywords
        header_idx = 0
        best_delimiter = ','
        
        for idx, line in enumerate(raw_lines):
            line_lower = line.lower()
            
            # Simple keyword check
            matches = sum(1 for key in HEADER_KEYWORDS if key in line_lower)
            if matches >= 2:
                header_idx = idx
                
                # Detect separator for this specific line
                if '\t' in line: best_delimiter = '\t'
                elif ';' in line: best_delimiter = ';'
                else: best_delimiter = ',' # Default to comma
                break
        
        # 3. Load Dataframe starting from that specific row
        # This prevents the "Expected 1 fields, saw 8" error because we skip the noise
        try:
            df = pd.read_csv(
                file_path, 
                encoding=encoding_to_use, 
                sep=best_delimiter, 
                skiprows=header_idx, 
                dtype=str, 
                on_bad_lines='skip' # Extra safety: skip corrupted lines if any remain
            )
            
            # Additional cleanup in case the header row itself was messy
            # (pandas might load it as data if we aren't careful, but skiprows usually handles it)
            return df
            
        except Exception as e:
             raise ValueError(f"Pandas failed to parse CSV/TXT even after skipping {header_idx} rows: {str(e)}")

    else:
        raise ValueError(f"Unsupported file format: {ext}")

def _process_xlsx_with_unmerge(file_path):
    """Modern .xlsx handling via openpyxl"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active

    # Detect and unmerge
    merged_ranges = list(sheet.merged_cells.ranges)
    for merged_cell in merged_ranges:
        top_left_cell = sheet.cell(row=merged_cell.min_row, column=merged_cell.min_col)
        value = top_left_cell.value
        sheet.unmerge_cells(str(merged_cell))
        for row in range(merged_cell.min_row, merged_cell.max_row + 1):
            for col in range(merged_cell.min_col, merged_cell.max_col + 1):
                sheet.cell(row=row, column=col).value = value

    data = sheet.values
    cols = next(data)
    df = pd.DataFrame(data, columns=cols)
    df = df.astype(str)
    return df

def _process_xls_with_unmerge(file_path):
    """Legacy .xls handling via xlrd (NEW FUNCTION)"""
    # formatting_info=True is REQUIRED to see merged cells
    book = xlrd.open_workbook(file_path, formatting_info=True)
    sheet = book.sheet_by_index(0)

    # 1. Read all data into a list of lists
    data = []
    for row_idx in range(sheet.nrows):
        row_data = []
        for col_idx in range(sheet.ncols):
            # Read cell value (convert generic types to string)
            val = sheet.cell_value(row_idx, col_idx)
            row_data.append(str(val))
        data.append(row_data)

    # 2. Handle Merged Cells
    # xlrd returns (row_start, row_end, col_start, col_end)
    # Note: row_end/col_end are exclusive (standard Python slicing)
    for crange in sheet.merged_cells:
        rlo, rhi, clo, chi = crange
        
        # Get the value from the top-left cell
        top_left_val = data[rlo][clo]
        
        # Fill the range in our data list
        for row_idx in range(rlo, rhi):
            for col_idx in range(clo, chi):
                data[row_idx][col_idx] = top_left_val

    # 3. Convert to DataFrame
    if not data:
        return pd.DataFrame()
        
    cols = data[0]
    df = pd.DataFrame(data[1:], columns=cols) # Treat first row as temp header
    df = df.astype(str)
    return df

def _find_and_set_header(df):
    """Scans for header row and deduplicates columns."""
    header_row_index = None

    for i, row in df.head(20).iterrows():
        row_str = " ".join(row.astype(str).str.lower().tolist())
        matches = sum(1 for key in HEADER_KEYWORDS if key in row_str)
        if matches >= 2:
            header_row_index = i
            break
    
    if header_row_index is None:
        return df

    new_header = df.iloc[header_row_index].astype(str).tolist()
    
    # Deduplicate Headers
    seen = {}
    unique_header = []
    for col in new_header:
        col_clean = col.strip()
        if col_clean == "" or col_clean.lower() == "nan":
            col_clean = "Unnamed"
        
        if col_clean in seen:
            seen[col_clean] += 1
            unique_header.append(f"{col_clean}.{seen[col_clean]}")
        else:
            seen[col_clean] = 0
            unique_header.append(col_clean)

    df = df[header_row_index + 1:] 
    df.columns = unique_header 
    df.reset_index(drop=True, inplace=True)
    
    return df