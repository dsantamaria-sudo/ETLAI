import argparse
import difflib
import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

load_dotenv()

from pipeline.evaluator import Evaluator
from pipeline.optimizer import Optimizer
from pipeline.skill import extract_section, load_skill, replace_section

console = Console()


def _render_diff(old: str, new: str) -> None:
    diff = list(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile="current",
            tofile="proposed",
        )
    )
    if not diff:
        console.print("[yellow]No changes proposed.[/yellow]")
        return

    text = Text()
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            text.append(line, style="bold green")
        elif line.startswith("-") and not line.startswith("---"):
            text.append(line, style="bold red")
        elif line.startswith("@@"):
            text.append(line, style="cyan")
        else:
            text.append(line, style="dim")

    console.print(Panel(text, title="[bold yellow]Diff: Instructions[/bold yellow]", border_style="yellow"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize a skill's ## Instructions section")
    parser.add_argument("skill_path", help="Path to the skill directory (e.g. skills/detect_headers)")
    parser.add_argument("--max-iterations", type=int, default=10, metavar="N")
    parser.add_argument("--target-score", type=float, default=1.0, metavar="F")
    args = parser.parse_args()

    skill_dir = Path(args.skill_path)
    if not skill_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] {skill_dir} is not a directory.")
        raise SystemExit(1)

    evaluator = Evaluator()
    optimizer = Optimizer()

    for iteration in range(1, args.max_iterations + 1):
        console.rule(f"[bold cyan]Iteration {iteration}/{args.max_iterations} — {skill_dir.name}[/bold cyan]")

        # Reload from disk each iteration so we always use the latest SKILL.md
        skill_content = load_skill(str(skill_dir))
        current_instructions = extract_section(skill_content, "Instructions")

        console.print(f"[bold]Evaluating[/bold] [cyan]{skill_dir.name}[/cyan]…")
        try:
            result = evaluator.evaluate(str(skill_dir))
        except RuntimeError as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            raise SystemExit(1)

        pct = result.score * 100
        score_style = "green" if result.score >= args.target_score else "red"
        console.print(
            f"[bold]Score:[/bold] [{score_style}]{result.passed}/{result.total} passed ({pct:.0f}%)[/{score_style}]"
        )

        if result.failures:
            table = Table(title="Failures", show_header=True, header_style="bold red")
            table.add_column("File", style="red", no_wrap=True)
            table.add_column("Output")
            table.add_column("Reason")
            for fc in result.failures:
                table.add_row(fc.filename, json.dumps(fc.output), fc.reason)
            console.print(table)

        if result.score >= args.target_score:
            console.print("[bold green]Ya está optimizado. Saliendo.[/bold green]")
            break

        console.print("[bold]Calling optimizer…[/bold]")
        new_instructions = optimizer.optimize(str(skill_dir), result)

        _render_diff(current_instructions, new_instructions)

        if not Confirm.ask("¿Aplicar esta versión?"):
            console.print("[yellow]Terminando sin aplicar cambios.[/yellow]")
            break

        # Save current instructions to history
        history_dir = skill_dir / "optimization" / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        version = len(list(history_dir.glob("v*_instructions.md"))) + 1
        (history_dir / f"v{version}_instructions.md").write_text(current_instructions, encoding="utf-8")

        # Update SKILL.md in place
        updated_content = replace_section(skill_content, "Instructions", new_instructions)
        (skill_dir / "SKILL.md").write_text(updated_content, encoding="utf-8")

        # Append entry to results.jsonl
        results_path = skill_dir / "optimization" / "results.jsonl"
        entry = {
            "version": version,
            "score": result.score,
            "passed": result.passed,
            "total": result.total,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with results_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        console.print(
            Panel(
                f"[green]✓[/green] v{version} guardada en [dim]optimization/history/[/dim]\n"
                f"[green]✓[/green] SKILL.md actualizado\n"
                f"[green]✓[/green] Entrada añadida a [dim]optimization/results.jsonl[/dim]",
                title=f"[bold green]Versión v{version} aplicada[/bold green]",
                border_style="green",
            )
        )


if __name__ == "__main__":
    main()
