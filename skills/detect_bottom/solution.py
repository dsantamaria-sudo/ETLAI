import pandas as pd
import json

df = pd.read_excel(excel_path, header=None)

# Strategy: Find last row that has actual data (non-empty)
# Start from the end and work backwards

data_end_row = len(df) - 1

for i in range(len(df) - 1, -1, -1):
    row = df.iloc[i]
    # Check if this row has any non-null values
    has_data = row.notna().any()
    
    if has_data:
        data_end_row = i
        break

result = {"data_end_row": data_end_row}
print(json.dumps(result))