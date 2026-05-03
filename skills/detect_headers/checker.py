import json
from pathlib import Path

from pipeline.validators import is_integer, is_non_empty_strings_list


def check(output: dict, state: dict) -> tuple[bool, str]:
    expected_path = Path(state["excel_path"]).with_suffix(".expected.json")
    if expected_path.exists():
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        if "header_row" in expected:
            got = output.get("header_row")
            if got != expected["header_row"]:
                return False, f"header_row: expected {expected['header_row']}, got {got}"
            return True, ""

    # Fallback: validación estructural cuando no hay expected
    ok, msg = is_integer(output.get("header_row"), min_val=1)
    if not ok:
        return False, f"header_row: {msg}"
    ok, msg = is_non_empty_strings_list(output.get("headers"))
    if not ok:
        return False, f"headers: {msg}"
    return True, ""
