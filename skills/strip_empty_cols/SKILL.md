## Instructions

The dataset goes from header_row+1 to data_end_row.
Some columns may be entirely empty (all None or blank) across all data rows, including the header cell.
Identify and remove those columns. A column is empty if both its header and all its data values are None or blank.

Return ONLY a JSON object:
{"headers": [<string>, ...], "col_indices": [<int>, ...]}

col_indices are the 1-based column numbers to keep.