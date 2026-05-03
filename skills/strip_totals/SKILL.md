## Instructions

The dataset goes from header_row+1 to data_end_row.
Exclude rows that fall into either of these scenarios:

1. **Labeled totals**: rows that contain a text label like "total", "subtotal", "grand total", "sales", or similar summary keywords explicitly in one of their cells.

2. **Sparse numeric aggregates**: rows that contain only numeric values AND have significantly fewer filled cells than a typical data row (e.g. only 2-3 columns filled out of 15+). These are likely column-level aggregate summaries inserted between or around the data. Do NOT exclude rows that are fully or mostly populated with numeric values — those are real data rows.

Return ONLY a JSON object:
{"data_end_row": <int>, "excluded_rows": [<int>, ...]}