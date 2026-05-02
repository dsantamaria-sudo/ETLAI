from pipeline.validators import is_integer, is_non_empty_strings_list


def check(output: dict, state: dict) -> tuple[bool, str]:
    ok, msg = is_integer(output.get("header_row"), min_val=1)
    if not ok:
        return False, f"header_row: {msg}"
    ok, msg = is_non_empty_strings_list(output.get("headers"))
    if not ok:
        return False, f"headers: {msg}"
    return True, ""
