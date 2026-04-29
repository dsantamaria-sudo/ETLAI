## Instructions

The dataset starts at header_row and ends at data_end_row.
Some rows just before data_end_row may be subtotals, grand totals or summary rows.
Identify them and return the real last data row excluding those rows.

Return ONLY a JSON object:
{"data_end_row": <int>}