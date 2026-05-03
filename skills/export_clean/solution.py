import json
from pathlib import Path
import openpyxl

rows    = state["rows"]
headers = state["headers"]

out_path = str(Path(excel_path).with_name(Path(excel_path).stem + "_clean.xlsx"))

wb = openpyxl.Workbook()
ws = wb.active
ws.append(headers)
for row in rows:
    ws.append(row)
wb.save(out_path)

print(json.dumps({"output_path": out_path}))
