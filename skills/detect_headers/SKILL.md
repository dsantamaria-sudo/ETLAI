---
name: header-detection
description: >
  Detects the header row of a spreadsheet (.xlsx or .csv) and returns a structured
  JSON with the row index and column names. Use whenever the user asks to identify
  headers, find the header row, read column names from a file, or prepare a
  spreadsheet for downstream analysis. Also trigger when the file has metadata rows,
  titles, or junk rows above the real data.
---

# Header Detection Skill

## Instructions

You are analyzing an Excel file to find the header row.

Use the available tools to inspect rows from the top. Headers are typically:
- Text labels, not numbers or dates
- Unique across columns
- Immediately above the first data row

Once confident, return ONLY:
{"header_row": <int>, "headers": [<string>, ...]}

`header_row` is 0-indexed.

## Success criteria

- `header_row` is an integer >= 0
- `headers` is a non-empty list of strings
- No header is empty or purely numeric