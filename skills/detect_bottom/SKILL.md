## Instructions

You are analyzing a spreadsheet to find where the real data ends.

Spreadsheets often have empty rows, summary totals, footnotes, or other non-data content at the bottom. You want the last row that belongs to the actual dataset — not a blank row, not a grand total, not a footer note.

Return ONLY a JSON object:
{"data_end_row": <int>}
