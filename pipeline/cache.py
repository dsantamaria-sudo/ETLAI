import json
from datetime import datetime, timezone
from pathlib import Path


def load_solution(skill_dir: str) -> str | None:
    path = Path(skill_dir) / "solution.py"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def save_solution(skill_dir: str, code: str) -> None:
    """Write solution.py and record a success in meta. Only called on success or first-time save."""
    skill_path = Path(skill_dir)
    meta = load_meta(skill_dir)

    (skill_path / "solution.py").write_text(code, encoding="utf-8")

    meta["version"] = meta.get("version", 0) + 1
    meta["success_count"] = meta.get("success_count", 0) + 1
    meta["solved_at"] = datetime.now(timezone.utc).isoformat()
    meta.pop("last_failure_reason", None)

    (skill_path / "solution.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def append_failure(
    skill_dir: str,
    *,
    code_error: str | None = None,
    checker_error: str | None = None,
    excel_path: str | None = None,
    llm_suggestion: str | None = None,
) -> None:
    """Log a failure to failures.jsonl and update meta. Never touches solution.py."""
    skill_path = Path(skill_dir)
    meta = load_meta(skill_dir)

    meta["fail_count"] = meta.get("fail_count", 0) + 1
    meta["last_failure_reason"] = code_error or checker_error
    (skill_path / "solution.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "solution_version": meta.get("version"),
        "excel_path": excel_path,
        "code_error": code_error,
        "checker_error": checker_error,
        "llm_suggestion": llm_suggestion,
    }
    with (skill_path / "failures.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_meta(skill_dir: str) -> dict:
    meta_path = Path(skill_dir) / "solution.meta.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def load_failures(skill_dir: str) -> list[dict]:
    path = Path(skill_dir) / "failures.jsonl"
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records
