from pipeline.validators import is_non_empty_strings_list, is_non_empty_list


def check(output: dict, state: dict) -> tuple[bool, str]:
    ok, msg = is_non_empty_strings_list(output.get("headers"))
    if not ok:
        return False, f"headers: {msg}"

    col_indices = output.get("col_indices")
    ok, msg = is_non_empty_list(col_indices)
    if not ok:
        return False, f"col_indices: {msg}"
    for i, idx in enumerate(col_indices):
        if not isinstance(idx, int):
            return False, f"col_indices[{i}]: Expected int, got {type(idx).__name__}"
    return True, ""
