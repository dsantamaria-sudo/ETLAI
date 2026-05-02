import pandas as pd
import json

excel_path = "C:/Users/Usuario/Downloads/example.xlsx"

# Load the Excel file without assuming any header
df = pd.read_excel(excel_path, header=None)

# The actual data columns are at indices 1, 3, 5, 7, 9, 11, 13, 14, 15, 16, 17
# Based on the user's col_indices [2, 4, 6, 8, 10, 12, 14, 15, 16, 17, 18] treating them as 1-based:
col_indices = [1, 3, 5, 7, 9, 11, 13, 14, 15, 16, 17]

# header_row is 1 (0-based index), so data starts at row 2
# data_end_row is 17 (0-based index is 16, but we need row 17 inclusive)
# Let's get data rows from row 2 to row 16 (inclusive) - rows 2-16 are data rows

# Get data rows (rows 2-16, which are indices 2 to 16)
data_rows = df.iloc[2:17]  # rows 2 through 16 inclusive (17 rows)

# Exclude rows 9 and 18 - these are row numbers in the Excel file (1-based)
# So row 9 is index 8, row 18 is index 17
# Since data starts at row 2, excluded rows in our data subset:
# Row 9 in Excel = index 8 in df = index 6 in data_rows (2,3,4,5,6,7,8 = 7 rows, so index 6)
# Actually let's recalculate:
# df index 2 = Excel row 2 (first data row)
# df index 8 = Excel row 9 (excluded!)
# df index 9 = Excel row 10

# For the data_rows subset (indices 2-16), we need to drop:
# - df index 8 corresponds to data_rows index 6 (since data_rows starts at df index 2)
# - df index 17 is not in our data range (data ends at df index 16)

# Exclude df indices 8 (Excel row 9) from the data
excluded_df_indices = [8]
data_rows = data_rows.drop(excluded_df_indices)

# Now select only the specified columns
selected_df = data_rows.iloc[:, col_indices]

# Convert to list of lists, converting NaN to None
rows = []
for _, row in selected_df.iterrows():
    row_values = []
    for val in row:
        if pd.isna(val):
            row_values.append(None)
        else:
            row_values.append(val)
    rows.append(row_values)

result = {"rows": rows}
print(json.dumps(result, ensure_ascii=False))