## Instructions

The dataset starts at header_row and ends at data_end_row. 
Some columns may be entirely empty or contain only None values across all data rows.
Identify and remove those columns from the headers list.

Return ONLY a JSON object:
{"headers": [<string>, ...], "col_indices": [<int>, ...]}

col_indices are the 1-based column numbers to keep.