import pandas as pd
from openpyxl import Workbook
import os

# Use the values from the current state
excel_path = "C:/Users/Usuario/Downloads/example.xlsx"
header_row = 1  # 1-based
headers = [
    "Header 1",
    "Header 2",
    "Header 3",
    "Header 4",
    "Header 5",
    "Header 6",
    "Header 7",
    "Header 8",
    "Header 9",
    "Header 10",
    "Header 11"
]
excluded_rows = [9, 18]  # 1-based row numbers
col_indices = [2, 4, 6, 8, 10, 12, 14, 15, 16, 17, 18]  # 0-based column indices

# Load the Excel file
df = pd.read_excel(excel_path, header=header_row - 1)

print(f"Number of columns in the file: {len(df.columns)}")
print(f"Column names: {list(df.columns)}")

# Select columns based on 0-based indices - filter to only valid indices
num_cols = len(df.columns)
selected_columns = [df.columns[i] for i in col_indices if i < num_cols]
print(f"Selected columns: {selected_columns}")

df_filtered = df[selected_columns]

# Convert excluded_rows (1-based) to 0-based indices for the dataframe
excluded_indices = [r - 1 for r in excluded_rows]

# Filter out the excluded rows (only valid indices)
excluded_indices = [i for i in excluded_indices if i < len(df_filtered)]
df_clean = df_filtered.drop(index=excluded_indices)

# Reset index after dropping rows
df_clean = df_clean.reset_index(drop=True)

# Generate output path
base_path = excel_path.rsplit('.', 1)[0]
output_path = base_path + "_clean.xlsx"

# Write to new Excel file with headers in row 1
df_clean.to_excel(output_path, index=False, header=True)

print(f"Output saved to: {output_path}")