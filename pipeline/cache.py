import json
from datetime import datetime, timezone
from pathlib import Path


def load_solution(skill_dir: str) -> str | None:
    path = Path(skill_dir) / "solution.py"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def save_solution(skill_dir: str, code: str, failure_reason: str | None = None) -> None:
    skill_path = Path(skill_dir)
    meta = load_meta(skill_dir)

    (skill_path / "solution.py").write_text(code, encoding="utf-8")

    meta["version"] = meta.get("version", 0) + 1
    if failure_reason is None:
        meta["success_count"] = meta.get("success_count", 0) + 1
        meta["solved_at"] = datetime.now(timezone.utc).isoformat()
        meta.pop("last_failure_reason", None)
    else:
        meta["fail_count"] = meta.get("fail_count", 0) + 1
        meta["last_failure_reason"] = failure_reason

    (skill_path / "solution.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_meta(skill_dir: str) -> dict:
    meta_path = Path(skill_dir) / "solution.meta.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}
