import pandas as pd
import json
import openpyxl

df = pd.read_excel(excel_path, header=None)
nrows, ncols = df.shape

best_row = 0
best_score = -1

for row_idx in range(min(20, nrows)):
    row = df.iloc[row_idx]
    non_null_count = row.notna().sum()
    if non_null_count == 0:
        continue

    text_count = sum(1 for v in row if pd.notna(v) and isinstance(v, str))
    score = text_count + (non_null_count * 0.1)

    if score > best_score:
        best_score = score
        best_row = row_idx

headers = [str(v) if pd.notna(v) else '' for v in df.iloc[best_row].tolist()]

if not any(pd.notna(v) for v in df.iloc[best_row]):
    headers = []

result = {
    "header_row": best_row,
    "headers": headers
}
print(json.dumps(result))