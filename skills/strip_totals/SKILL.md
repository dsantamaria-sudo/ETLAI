## Instructions

The dataset goes from header_row+1 to data_end_row.
Some rows are subtotals or grand totals. Identify them by looking for rows that have a text label like "total", "subtotal", "grand total" explicitly in one of their cells. Do not exclude rows that contain only numeric values, even if those values happen to equal a sum.

Return ONLY a JSON object:
{"data_end_row": <int>, "excluded_rows": [<int>, ...]}