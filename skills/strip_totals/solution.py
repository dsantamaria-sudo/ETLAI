import pandas as pd
import json

df = pd.read_excel(excel_path, header=None)

header_row   = state["header_row"]
data_end_row = state["data_end_row"]
data_start   = header_row + 1

total_keywords = ['total', 'subtotal', 'grand', 'sum', 'sales', 'aggregate', 'summary']

non_null_counts = []
for idx in range(data_start, min(data_end_row + 1, len(df))):
    row = df.iloc[idx]
    non_null_counts.append(row.notna().sum())

typical_count = max(non_null_counts) if non_null_counts else 0

excluded_rows = []

for idx in range(data_start, min(data_end_row + 1, len(df))):
    row = df.iloc[idx]
    non_null_count = row.notna().sum()
    
    first_col_raw = row.iloc[0]
    first_col_value = str(first_col_raw).lower().strip() if pd.notna(first_col_raw) else ""
    
    has_labeled_total = False
    for keyword in total_keywords:
        if keyword in first_col_value:
            has_labeled_total = True
            break
    
    is_sparse = (non_null_count < typical_count * 0.5) and (non_null_count < 5)
    
    if has_labeled_total:
        excluded_rows.append(idx)
    elif is_sparse:
        excluded_rows.append(idx)

all_data_rows = list(range(data_start, min(data_end_row + 1, len(df))))
excluded_set = set(excluded_rows)
valid_data_rows = [r for r in all_data_rows if r not in excluded_set]

data_end_row = valid_data_rows[-1] if valid_data_rows else data_start - 1

result = {"data_end_row": data_end_row, "excluded_rows": sorted(excluded_rows)}
print(json.dumps(result))