from pipeline.validators import is_list_of_lists


def check(output: dict, state: dict) -> tuple[bool, str]:
    ok, msg = is_list_of_lists(output.get("rows"))
    if not ok:
        return False, f"rows: {msg}"
    return True, ""
