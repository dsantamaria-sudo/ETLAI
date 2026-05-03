import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

from .runner import run_step
from .skill import load_skill

console = Console()


@dataclass
class FailureCase:
    filename: str
    output: dict
    reason: str


@dataclass
class EvalResult:
    score: float
    total: int
    passed: int
    failures: list[FailureCase] = field(default_factory=list)


def _load_checker(skill_path: str):
    checker_path = Path(skill_path) / "checker.py"
    if not checker_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("checker", str(checker_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_state_override(excel_file: Path) -> dict:
    """Load an optional <stem>.state.json alongside the Excel file to seed prior-step state."""
    state_file = excel_file.parent / f"{excel_file.stem}.state.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning: could not parse {state_file.name}, ignoring.[/yellow]")
    return {}


class Evaluator:
    def evaluate(self, skill_path: str, instructions_override: str | None = None) -> EvalResult:
        skill_dir = Path(skill_path)
        test_files_dir = skill_dir / "optimization" / "test_files"

        if not test_files_dir.exists():
            raise RuntimeError(f"Test files directory not found: {test_files_dir}")

        test_files = sorted(test_files_dir.glob("*.xlsx"))
        if not test_files:
            raise RuntimeError(f"No .xlsx files found in {test_files_dir}")

        skill_content = load_skill(str(skill_dir))
        checker = _load_checker(str(skill_dir))

        passed = 0
        failures: list[FailureCase] = []

        for excel_file in test_files:
            state = {"excel_path": str(excel_file), **_load_state_override(excel_file)}
            output: dict = {}
            try:
                output = run_step(
                    skill_content,
                    state,
                    str(skill_dir),
                    instructions_override=instructions_override,
                    skip_cache=True,
                )
                if checker is not None:
                    ok, reason = checker.check(output, state)
                else:
                    ok, reason = True, ""
            except Exception as exc:
                ok = False
                reason = str(exc)

            if ok:
                passed += 1
            else:
                failures.append(FailureCase(filename=excel_file.name, output=output, reason=reason))

        total = len(test_files)
        score = passed / total if total > 0 else 0.0
        return EvalResult(score=score, total=total, passed=passed, failures=failures)
