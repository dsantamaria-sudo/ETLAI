## Instructions

The dataset goes from header_row+1 to data_end_row.
Some columns may be entirely empty (all None or blank) across all data rows, including the header cell.
Identify and remove those columns. A column is empty if both its header and all its data values are None or blank.

Always read the file with `pd.read_excel(excel_path, header=None)` so row and column indices are absolute.

Return ONLY a JSON object:
{"headers": [<string>, ...], "col_indices": [<int>, ...]}

col_indices are 0-based column numbers (column A = 0, column B = 1, ...).
When using pandas with header=None, the pandas column index equals the col_index directly.