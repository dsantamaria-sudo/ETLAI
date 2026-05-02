# Verify the data end row logic
# Row 17 is the last data row (values 1-14 in first data column)
# Row 18 is a "Total" summary row

data_end_row = 17

import json
result = {"data_end_row": data_end_row}
print(json.dumps(result))