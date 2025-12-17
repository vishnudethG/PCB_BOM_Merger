# src/core/file_loader.py
import pandas as pd
import openpyxl
import os

# Define keywords to identify the header row
HEADER_KEYWORDS = [
    "ref", "reference", "designator", "part", "component", 
    "value", "qty", "quantity", "description", "footprint"
]

def load_and_clean_file(file_path):
    """
    Main entry point. Detects file type, handles unmerging, finds headers.
    Returns: Cleaned Pandas DataFrame.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext in ['.xlsx', '.xls', '.xlsm']:
        df = _process_excel_with_unmerge(file_path)
    elif ext == '.csv':
        df = pd.read_csv(file_path, dtype=str)
    elif ext == '.txt':
        df = pd.read_csv(file_path, sep='\t', dtype=str)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    # Step 2: Find the actual header row (ignoring "Customer Name" etc)
    df_clean = _find_and_set_header(df)
    
    return df_clean

def _process_excel_with_unmerge(file_path):
    """
    Uses OpenPyXL to detect merged cells, unmerge them, and fill values down.
    Then passes data to Pandas.
    """
    # Load workbook and active sheet
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active

    # CRITICAL: Detect and unmerge cells
    # We copy the list because unmerging modifies the range inplace
    merged_ranges = list(sheet.merged_cells.ranges)
    
    for merged_cell in merged_ranges:
        # Get the value from the top-left cell of the merge
        top_left_cell = sheet.cell(row=merged_cell.min_row, column=merged_cell.min_col)
        value = top_left_cell.value
        
        # Unmerge the range
        sheet.unmerge_cells(str(merged_cell))
        
        # Fill the unmerged range with the top-left value
        for row in range(merged_cell.min_row, merged_cell.max_row + 1):
            for col in range(merged_cell.min_col, merged_cell.max_col + 1):
                sheet.cell(row=row, column=col).value = value

    # Convert OpenPyXL sheet to values list
    data = sheet.values
    
    # Create DataFrame (assuming first row read is just the first row of file)
    # We treat all data as strings to prevent scientific notation conversion
    cols = next(data) # Grab first row as temp headers
    df = pd.DataFrame(data, columns=cols)
    
    # Force all data to string to avoid "5.00E+05" issues
    df = df.astype(str)
    
    return df

def _find_and_set_header(df):
    """
    Scans first 20 rows for keywords. Promotes that row to header.
    Ensures column names are unique to prevent pandas errors.
    """
    header_row_index = None

    # Iterate through first 20 rows
    for i, row in df.head(20).iterrows():
        # Convert row to a single lowercase string for searching
        row_str = " ".join(row.astype(str).str.lower().tolist())
        
        # Check if at least 2 keywords exist in this row
        matches = sum(1 for key in HEADER_KEYWORDS if key in row_str)
        if matches >= 2:
            header_row_index = i
            break
    
    if header_row_index is None:
        return df

    # Promote the found row to header
    new_header = df.iloc[header_row_index].astype(str).tolist() # Convert to list of strings
    
    # --- CRITICAL FIX: Deduplicate Headers ---
    # Turns ["Qty", "Qty", ""] into ["Qty", "Qty.1", "Unnamed.2"]
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
    # -----------------------------------------

    df = df[header_row_index + 1:] # Take data below header
    df.columns = unique_header # Set unique headers
    df.reset_index(drop=True, inplace=True) # Reset index numbers
    
    return df