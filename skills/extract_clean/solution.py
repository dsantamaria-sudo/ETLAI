import json
import math
import pandas as pd

header_row   = state["header_row"]
col_indices  = state["col_indices"]   # 0-based pandas column indices
data_end_row = state["data_end_row"]
excluded     = set(state.get("excluded_rows", []))

df = pd.read_excel(excel_path, header=None)


def _serialize(v):
    if v is None:
        return None
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
    except Exception:
        pass
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


rows = []
for i in range(header_row + 1, min(data_end_row + 1, len(df))):
    if i in excluded:
        continue
    row = [_serialize(df.iloc[i, c]) for c in col_indices]
    rows.append(row)

print(json.dumps({"rows": rows}, default=str))
