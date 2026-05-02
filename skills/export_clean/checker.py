from pipeline.validators import is_valid_path


def check(output: dict, state: dict) -> tuple[bool, str]:
    ok, msg = is_valid_path(output.get("output_path"))
    if not ok:
        return False, f"output_path: {msg}"
    return True, ""
