# src/core/normalizer.py
import pandas as pd
import re

def normalize_bom_data(df, ref_col_name, delimiter=','):
    """
    Takes a DataFrame and 'explodes' the Reference Column.
    Handles ranges (R1-R4) and delimiters (comma, space, etc).
    """
    normalized_rows = []

    # Iterate over every row in the dataframe
    for index, row in df.iterrows():
        raw_ref = str(row[ref_col_name])
        
        # 1. Clean the string (remove accidental double spaces)
        # If user selected space delimiter, we don't want to replace spaces yet.
        if delimiter != ' ': 
            raw_ref = raw_ref.replace(' ', '') 

        # 2. Split into tokens based on delimiter
        # Handle mixed delimiters if necessary, but stick to primary first
        if delimiter == 'auto':
            # naive auto-detect: split by comma or semicolon or space
            tokens = re.split(r'[;, ]+', raw_ref)
        else:
            tokens = raw_ref.split(delimiter)

        # 3. Process each token (check for ranges)
        expanded_refs = []
        for token in tokens:
            token = token.strip()
            if not token: 
                continue # Skip empty strings
            
            # Check for Range (e.g., R1-R4 or C10-C12)
            # Regex Explanation: 
            # ^([A-Za-z]+) -> Start with letters (Group 1: Prefix)
            # (\d+)        -> Followed by digits (Group 2: Start Num)
            # \s*-\s* -> A hyphen with optional spaces
            # ([A-Za-z]*)  -> Optional letters (Group 3: End Prefix, usually same as start)
            # (\d+)$       -> Ends with digits (Group 4: End Num)
            range_match = re.match(r'^([A-Za-z]+)(\d+)\s*-\s*([A-Za-z]*)(\d+)$', token)
            
            if range_match:
                prefix = range_match.group(1)
                start_num = int(range_match.group(2))
                end_prefix = range_match.group(3) # Might be empty
                end_num = int(range_match.group(4))
                
                # Validation: prefixes must match (cannot do R1-C5)
                # If end_prefix exists, it must equal prefix
                if end_prefix and end_prefix.upper() != prefix.upper():
                    # Invalid range (R1-C5), treat as single item or error
                    expanded_refs.append(token)
                else:
                    # Expand the range
                    # Ensure start < end
                    if start_num > end_num:
                        start_num, end_num = end_num, start_num # Swap if reverse order
                    
                    for i in range(start_num, end_num + 1):
                        expanded_refs.append(f"{prefix}{i}")
            else:
                # No range, just a single ref
                expanded_refs.append(token)

        # 4. Create new rows for the DataFrame
        for ref in expanded_refs:
            new_row_dict = row.to_dict() 
            new_row_dict[ref_col_name] = ref.upper() # Standardize
            normalized_rows.append(new_row_dict)

    # Create new DataFrame
    df_normalized = pd.DataFrame(normalized_rows)
    df_normalized.reset_index(drop=True, inplace=True)
    
    return df_normalized