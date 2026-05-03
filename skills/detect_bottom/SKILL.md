## Instructions

You are analyzing a spreadsheet to find where the real data ends.

Spreadsheets often have empty rows, summary totals, footnotes, or other non-data content at the bottom. You want the last row that belongs to the actual dataset — not a blank row, not a grand total, not a footer note.

Always read the file with `pd.read_excel(excel_path, header=None)` so that row indices are absolute (0-based) and consistent with `header_row` from the current state. Never use `skiprows` or `header=` parameters that would shift the index.

`data_end_row` must be the absolute 0-based row index of the last real data row — the same coordinate system as `header_row`.

Return ONLY a JSON object:
{"data_end_row": <int>}
