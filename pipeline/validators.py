from pathlib import Path


def is_integer(value, min_val=None) -> tuple[bool, str]:
    if not isinstance(value, int):
        return False, f"Expected int, got {type(value).__name__}"
    if min_val is not None and value < min_val:
        return False, f"Value {value} is less than minimum {min_val}"
    return True, ""


def is_non_empty_list(value) -> tuple[bool, str]:
    if not isinstance(value, list):
        return False, f"Expected list, got {type(value).__name__}"
    if len(value) == 0:
        return False, "List is empty"
    return True, ""


def is_non_empty_strings_list(value) -> tuple[bool, str]:
    ok, msg = is_non_empty_list(value)
    if not ok:
        return ok, msg
    for i, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            return False, f"Item at index {i} is not a non-empty string: {item!r}"
    return True, ""


def is_greater_than(value, other_value, other_name: str) -> tuple[bool, str]:
    if not isinstance(value, (int, float)):
        return False, f"Expected number, got {type(value).__name__}"
    if value <= other_value:
        return False, f"Value {value} is not greater than {other_name} ({other_value})"
    return True, ""


def is_valid_path(value) -> tuple[bool, str]:
    if not isinstance(value, str):
        return False, f"Expected string path, got {type(value).__name__}"
    if not Path(value).exists():
        return False, f"Path does not exist: {value!r}"
    return True, ""


def is_list_of_lists(value) -> tuple[bool, str]:
    if not isinstance(value, list):
        return False, f"Expected list, got {type(value).__name__}"
    for i, item in enumerate(value):
        if not isinstance(item, list):
            return False, f"Item at index {i} is not a list: {type(item).__name__}"
    return True, ""
