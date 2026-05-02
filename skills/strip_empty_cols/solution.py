import openpyxl
import json

# Load the workbook
wb = openpyxl.load_workbook("C:/Users/Usuario/Downloads/example.xlsx")
ws = wb.active

# Configuration from state
header_row = 1
data_end_row = 17
excluded_rows = [9, 18]
given_headers = ["Header 1", "Header 2", "Header 3", "Header 4", "Header 5", 
                 "Header 6", "Header 7", "Header 8", "Header 9", "Header 10", "Header 11"]

# Non-empty columns from our analysis
non_empty_cols = [2, 4, 6, 8, 10, 12, 14, 15, 16, 17, 18]

# Verify what headers are in row 2 for these columns
print("Headers in row 2 for non-empty columns:")
row2_headers = []
for col in non_empty_cols:
    header_val = ws.cell(row=2, column=col).value
    row2_headers.append(header_val)
    print(f"  Column {col}: '{header_val}'")

print(f"\nRow 2 headers: {row2_headers}")
print(f"Given headers: {given_headers}")
print(f"Match: {row2_headers == given_headers}")