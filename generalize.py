import argparse
import importlib.util
import json
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

from pipeline.config import MODEL, client
from pipeline.runner import run_code, run_step
from pipeline.skill import extract_section, load_skill

console = Console()


def _load_checker(skill_path: str):
    checker_path = Path(skill_path) / "checker.py"
    if not checker_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("checker", str(checker_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_state(excel_file: Path) -> dict:
    state = {"excel_path": str(excel_file)}
    state_file = excel_file.parent / f"{excel_file.stem}.state.json"
    if state_file.exists():
        try:
            state.update(json.loads(state_file.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    return state


def _collect_solutions(
    skill_path: str, test_files: list[Path], checker, max_attempts: int = 10
) -> list[tuple[Path, str, dict]]:
    """Returns (excel_file, exploration_code, correct_output) triples."""
    skill_content = load_skill(skill_path)
    solutions: list[tuple[Path, str, dict]] = []

    console.rule("[bold cyan]Fase 1: Recopilando soluciones individuales[/bold cyan]")
    console.print(f"Ejecutando el LLM sobre {len(test_files)} archivos (máx {max_attempts} intentos c/u)...\n")

    for i, excel_file in enumerate(test_files, 1):
        state = _load_state(excel_file)
        solved = False

        for attempt in range(1, max_attempts + 1):
            code_sink: list[str] = []
            try:
                # run_step returns the LLM's final JSON answer — validate that, not the exploration code
                output = run_step(skill_content, state, skill_path, skip_cache=True, _code_sink=code_sink)
            except Exception as exc:
                console.print(f"  [red]✗ {excel_file.name}:[/red] {exc}")
                state["_last_error"] = str(exc)
                continue

            if not code_sink:
                reason = "El modelo respondió con finish_reason stop sin generar código"
                console.print(f"  [yellow]↻ {excel_file.name} intento {attempt}: {reason}[/yellow]")
                state["_last_error"] = reason
                continue

            if checker is not None:
                ok, reason = checker.check(output, state)
            else:
                ok, reason = True, ""

            if ok:
                solutions.append((excel_file, code_sink[0], output))
                tag = "" if attempt == 1 else f" [dim](intento {attempt})[/dim]"
                console.print(f"  [green]✓[/green] {excel_file.name}{tag}")
                solved = True
                break
            else:
                console.print(f"  [yellow]↻ {excel_file.name} intento {attempt}: {reason}[/yellow]")
                state["_last_error"] = reason

        if not solved:
            console.print(f"  [red]✗ {excel_file.name}: sin solución válida tras {max_attempts} intentos[/red]")

    console.print(f"\n[bold]Recopiladas {len(solutions)}/{len(test_files)} soluciones verificadas.[/bold]")
    return solutions


def _synthesize(skill_path: str, solutions: list[tuple[Path, str, dict]], failure_info: str | None = None) -> str:
    skill_content = load_skill(skill_path)
    instructions = extract_section(skill_content, "Instructions")

    # Include both the correct output AND the exploration code so the synthesizer
    # understands what the right answer is and how the LLM arrived at it
    solutions_text = "\n\n".join(
        f"### {file.name}\n"
        f"Correct output: {json.dumps(output)}\n\n"
        f"Exploration code:\n```python\n{code}\n```"
        for file, code, output in solutions
    )

    prompt = (
        "You are a Python code synthesis expert.\n\n"
        "## Skill description\n\n"
        f"{instructions}\n\n"
        "## Individual solutions\n\n"
        "Each snippet below solves the task for a specific Excel file.\n"
        "Study the patterns across all of them and write ONE generalized script.\n\n"
        f"{solutions_text}\n\n"
    )

    if failure_info:
        prompt += (
            "## Previous attempt — failures to fix\n\n"
            f"{failure_info}\n\n"
        )

    prompt += (
        "## Requirements for the generalized solution\n\n"
        "- Single Python script, not a function definition.\n"
        "- Use the variable `excel_path` to reference the file (it is already defined).\n"
        "- Print the final result as JSON to stdout: `print(json.dumps(result))`.\n"
        "- Handle the variety of Excel structures seen in the examples.\n"
        "- Output ONLY the Python code. No markdown fences, no explanations.\n"
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    code = response.choices[0].message.content.strip()
    if code.startswith("```"):
        code = "\n".join(
            line for line in code.splitlines() if not line.startswith("```")
        ).strip()
    return code


def _validate(
    code: str, test_files: list[Path], checker
) -> tuple[int, int, list[dict]]:
    passed = 0
    failures: list[dict] = []

    for excel_file in test_files:
        state = _load_state(excel_file)
        output, error = run_code(code, str(excel_file), state=state)

        if error:
            ok, reason = False, f"Runtime error: {error}"
            output = {}
        elif checker is not None:
            ok, reason = checker.check(output or {}, state)
        else:
            ok, reason = True, ""

        if ok:
            passed += 1
        else:
            failures.append({"filename": excel_file.name, "output": output or {}, "reason": reason})

    return passed, len(test_files), failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synthesize a generalized solution.py from per-file LLM solutions"
    )
    parser.add_argument("skill_path", help="Path to the skill directory (e.g. skills/detect_headers)")
    parser.add_argument("--max-iterations", type=int, default=5, metavar="N",
                        help="Max synthesis+validation cycles (default: 5)")
    parser.add_argument("--max-attempts", type=int, default=10, metavar="N",
                        help="Max LLM retries per file in collection phase (default: 10)")
    args = parser.parse_args()

    skill_dir = Path(args.skill_path)
    if not skill_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] {skill_dir} is not a directory.")
        raise SystemExit(1)

    test_files_dir = skill_dir / "optimization" / "test_files"
    test_files = sorted(test_files_dir.glob("*.xlsx"))
    if not test_files:
        console.print(f"[bold red]Error:[/bold red] No .xlsx files found in {test_files_dir}.")
        raise SystemExit(1)

    checker = _load_checker(str(skill_dir))
    solutions = _collect_solutions(str(skill_dir), test_files, checker, max_attempts=args.max_attempts)

    if not solutions:
        console.print("[bold red]Sin soluciones recopiladas. Abortando.[/bold red]")
        raise SystemExit(1)

    failure_info: str | None = None

    for iteration in range(1, args.max_iterations + 1):
        console.rule(f"[bold cyan]Fase 2 — Iteración {iteration}/{args.max_iterations}[/bold cyan]")

        console.print("[bold]Sintetizando solución generalizada...[/bold]")
        code = _synthesize(str(skill_dir), solutions, failure_info)
        console.print(Panel(code, title="[bold blue]Propuesta solution.py[/bold blue]", border_style="blue"))

        console.print("[bold]Validando contra los test files...[/bold]")
        passed, total, failures = _validate(code, test_files, checker)
        pct = passed / total * 100 if total else 0
        score_style = "green" if passed == total else "red"
        console.print(
            f"[bold]Score:[/bold] [{score_style}]{passed}/{total} passed ({pct:.0f}%)[/{score_style}]"
        )

        if failures:
            table = Table(title="Failures", header_style="bold red", show_lines=True)
            table.add_column("File", style="red", no_wrap=True)
            table.add_column("Output")
            table.add_column("Reason")
            for fc in failures:
                table.add_row(fc["filename"], json.dumps(fc["output"]), fc["reason"])
            console.print(table)

        if passed == total:
            solution_path = skill_dir / "solution.py"
            solution_path.write_text(code, encoding="utf-8")
            console.print(
                Panel(
                    f"[green]✓[/green] Guardado en [bold]{solution_path}[/bold]\n"
                    f"[green]✓[/green] El pipeline ejecutará este código sin llamar al LLM.",
                    title="[bold green]¡Generalización completada![/bold green]",
                    border_style="green",
                )
            )
            return

        failure_info = "\n".join(
            f"- {fc['filename']}: output={json.dumps(fc['output'])}, reason={fc['reason']}"
            for fc in failures
        )

    console.print(
        f"[bold red]No se alcanzó 100% tras {args.max_iterations} iteraciones.[/bold red]\n"
        "Considera revisar los test files o aumentar --max-iterations."
    )


if __name__ == "__main__":
    main()
