import argparse
import json
import sys
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
from rich.panel import Panel
from pipeline.runner import run_pipeline
from pipeline.config import PROVIDER, MODEL

console = Console()

SKILL_PATHS = [
    "skills/detect_headers",
    "skills/detect_bottom",
    "skills/strip_totals",
    "skills/strip_empty_cols",
    "skills/extract_clean",
    "skills/export_clean",
    ]


def pick_file() -> str:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title="Select an Excel file",
        filetypes=[("Excel files", "*.xlsx *.xlsm *.xls"), ("All files", "*.*")],
    )
    root.destroy()
    if not path:
        console.print("[red]No file selected. Exiting.[/red]")
        sys.exit(0)
    return path


def main():
    parser = argparse.ArgumentParser(description="Run ETL pipeline on an Excel file.")
    parser.add_argument("excel_path", nargs="?", help="Path to the input Excel file (opens file picker if omitted)")
    args = parser.parse_args()

    excel_path = args.excel_path or pick_file()

    console.print(Panel(f"[bold]ETL Pipeline[/bold]\nFile:     {excel_path}\nProvider: {PROVIDER}\nModel:    {MODEL}", expand=False))

    try:
        final_state = run_pipeline(excel_path, SKILL_PATHS)
    except RuntimeError as e:
        console.print(f"[bold red]Pipeline failed:[/bold red] {e}")
        raise SystemExit(1)

    display_state = {k: v for k, v in final_state.items() if not k.startswith("_")}
    console.print(Panel(json.dumps(display_state, indent=2), title="[bold green]Final State[/bold green]", expand=False))


if __name__ == "__main__":
    main()
