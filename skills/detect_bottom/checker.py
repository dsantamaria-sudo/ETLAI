from pipeline.validators import is_integer, is_greater_than


def check(output: dict, state: dict) -> tuple[bool, str]:
    data_end_row = output.get("data_end_row")
    ok, msg = is_integer(data_end_row)
    if not ok:
        return False, f"data_end_row: {msg}"
    ok, msg = is_greater_than(data_end_row, state.get("header_row", 0), "header_row")
    if not ok:
        return False, f"data_end_row: {msg}"
    return True, ""
