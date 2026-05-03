import pandas as pd
import json

df = pd.read_excel(excel_path, header=None)

header_row   = state["header_row"]
data_end_row = state["data_end_row"]
excluded     = set(state.get("excluded_rows", []))

data_start = header_row + 1
data_end   = data_end_row

non_empty_cols = []
for col_idx in range(df.shape[1]):
    header_val = df.iloc[header_row, col_idx]
    header_is_empty = pd.isna(header_val) or (isinstance(header_val, str) and header_val.strip() == '')

    col_data = df.iloc[data_start:data_end + 1, col_idx]
    col_data = col_data[~col_data.index.isin(excluded)]
    all_data_empty = col_data.isna().all()

    if not (header_is_empty and all_data_empty):
        non_empty_cols.append(col_idx)

headers = [str(df.iloc[header_row, col_idx]) for col_idx in non_empty_cols]

result = {
    "headers": headers,
    "col_indices": non_empty_cols
}
print(json.dumps(result))
