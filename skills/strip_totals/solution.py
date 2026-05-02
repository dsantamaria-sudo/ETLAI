
import json

# Based on the analysis:
# - Row 2 is the header row
# - Data starts at row 3
# - Row 9 is a "Subtotal" row - should be excluded
# - Row 17 is the last data row (row 18 is "Total")
# - Row 18 is a "Total" row - should be excluded

data_end_row = 17
excluded_rows = [9, 18]

result = {
    "data_end_row": data_end_row,
    "excluded_rows": excluded_rows
}

print(json.dumps(result))
