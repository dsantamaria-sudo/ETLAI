from pipeline.validators import is_integer, is_greater_than


def check(output: dict, state: dict) -> tuple[bool, str]:
    data_end_row = output.get("data_end_row")
    ok, msg = is_integer(data_end_row)
    if not ok:
        return False, f"data_end_row: {msg}"
    ok, msg = is_greater_than(data_end_row, state.get("header_row", 0), "header_row")
    if not ok:
        return False, f"data_end_row: {msg}"

    excluded_rows = output.get("excluded_rows")
    if not isinstance(excluded_rows, list):
        return False, f"excluded_rows: Expected list, got {type(excluded_rows).__name__}"
    for i, row in enumerate(excluded_rows):
        if not isinstance(row, int):
            return False, f"excluded_rows[{i}]: Expected int, got {type(row).__name__}"
    return True, ""
