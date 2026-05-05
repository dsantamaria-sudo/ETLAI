"""Retrain solution.py for a skill using accumulated real-world failures."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from pipeline.cache import load_solution, load_failures
from pipeline.config import MODEL, client
from rich.console import Console
from rich.panel import Panel

console = Console()


def _build_failure_block(failures: list[dict]) -> str:
    parts = []
    for i, f in enumerate(failures, start=1):
        lines = [f"### Failure {i} — {f['timestamp']}"]
        if f.get("excel_path"):
            lines.append(f"**File:** {f['excel_path']}")
        if f.get("code_error"):
            lines.append(f"**Code error:**\n```\n{f['code_error']}\n```")
        if f.get("checker_error"):
            lines.append(f"**Checker error:** {f['checker_error']}")
        if f.get("llm_suggestion"):
            lines.append(f"**LLM attempt for this run:**\n```python\n{f['llm_suggestion']}\n```")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def retrain(skill_path: str, clear_after: bool = False) -> None:
    skill_dir = Path(skill_path)

    solution = load_solution(str(skill_dir))
    if solution is None:
        console.print("[red]No solution.py found. Run the pipeline first to generate one.[/red]")
        sys.exit(1)

    failures = load_failures(str(skill_dir))
    if not failures:
        console.print("[yellow]No failures recorded in failures.jsonl. Nothing to retrain on.[/yellow]")
        return

    console.print(f"[bold]Retraining[/bold] {skill_dir.name} — {len(failures)} failure(s)")

    prompt = (
        "You are fixing a Python script (`solution.py`) used in an ETL pipeline.\n\n"
        "## Current solution.py\n\n"
        f"```python\n{solution}\n```\n\n"
        "## Real-world failures\n\n"
        "This script produced the following errors during actual pipeline runs:\n\n"
        f"{_build_failure_block(failures)}\n\n"
        "## Task\n\n"
        "Rewrite `solution.py` to fix these failures. Rules:\n"
        "- Output ONLY the raw Python code, no markdown fences, no explanation.\n"
        "- Keep the same general logic; only change what is needed to fix the failures.\n"
        "- The script must use `excel_path` from the provided `state` dict and print a JSON result to stdout.\n"
    )

    console.print(Panel(prompt, title="[blue]Retrain Prompt[/blue]", border_style="blue"))

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    new_code = response.choices[0].message.content.strip()

    if new_code.startswith("```"):
        lines = new_code.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        new_code = "\n".join(lines[1:end])

    console.print(Panel(new_code, title="[green]New solution.py[/green]", border_style="green"))

    (skill_dir / "solution.py").write_text(new_code, encoding="utf-8")
    console.print(f"[bold green]✓ solution.py updated for {skill_dir.name}[/bold green]")

    if clear_after:
        (skill_dir / "failures.jsonl").unlink(missing_ok=True)
        console.print("[dim]failures.jsonl cleared[/dim]")


def main():
    parser = argparse.ArgumentParser(description="Retrain solution.py using accumulated real-world failures.")
    parser.add_argument("skill_path", help="Path to the skill directory, e.g. skills/detect_headers")
    parser.add_argument("--clear", action="store_true", help="Delete failures.jsonl after retraining")
    args = parser.parse_args()

    retrain(args.skill_path, clear_after=args.clear)


if __name__ == "__main__":
    main()
