## Instructions

Extract the dataset from the Excel file into a clean structure.
Use header_row for column names and col_indices to know which columns to keep.
Data rows go from header_row+1 to data_end_row inclusive.
Skip any rows whose row number appears in excluded_rows.

Return ONLY a JSON object:
{"rows": [[<value>, ...], ...]}