import json
from pathlib import Path

from pipeline.validators import is_non_empty_strings_list, is_non_empty_list


def check(output: dict, state: dict) -> tuple[bool, str]:
    expected_path = Path(state["excel_path"]).with_suffix(".expected.json")
    if expected_path.exists():
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        if "col_indices" in expected:
            got = output.get("col_indices")
            if got != expected["col_indices"]:
                return False, f"col_indices: expected {expected['col_indices']}, got {got}"
            return True, ""

    # Fallback: validación estructural
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
