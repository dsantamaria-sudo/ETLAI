import pandas as pd
import json

df = pd.read_excel(excel_path, header=None)
nrows = df.shape[0]

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

raw_headers = [str(v).strip() if pd.notna(v) else '' for v in df.iloc[best_row].tolist()]

# Filtrar columnas con header vacío
valid_columns = [i for i, h in enumerate(raw_headers) if h != '']
headers = [raw_headers[i] for i in valid_columns]

result = {
    "header_row": best_row,
    "headers": headers,
    "valid_columns": valid_columns  # útil para los scripts siguientes
}
print(json.dumps(result))