import io
import json as _json
import re as _re
import sys
import traceback
from pathlib import Path

import openpyxl
import pandas as pd
from rich.console import Console
from rich.syntax import Syntax

console = Console()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Runs Python code and returns the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                    }
                },
                "required": ["code"],
            },
        },
    }
]

def run_python(code: str, excel_path: str) -> str:
    stdout_capture = io.StringIO()
    local_vars: dict = {"excel_path": excel_path}

    console.print("[bold yellow]▶ run_python[/bold yellow]")
    console.print(Syntax(code, "python", theme="monokai", line_numbers=False))

    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    try:
        exec(  # noqa: S102
            code,
            {
                "__builtins__": __builtins__,
                "openpyxl": openpyxl,
                "pd": pd,
                "pandas": pd,
                "json": _json,
                "re": _re,
                "Path": Path,
                **local_vars,
            },
            local_vars,
        )
    except Exception:
        sys.stdout = old_stdout
        error = traceback.format_exc()
        console.print(f"[red]✗ error:[/red] {error}")
        return _json.dumps({"error": error})
    finally:
        sys.stdout = old_stdout

    output = stdout_capture.getvalue()
    local_vars.pop("excel_path", None)

    result: dict = {}
    if output:
        result["stdout"] = output
    if local_vars:
        result["locals"] = {k: v for k, v in local_vars.items() if not k.startswith("_")}

    console.print(f"[bold green]✓ result:[/bold green] {_json.dumps(result, default=str)}")
    return _json.dumps(result, default=str)


def dispatch(tool_name: str, tool_args: dict, excel_path: str) -> str:
    if tool_name == "run_python":
        return run_python(tool_args["code"], excel_path)
    return _json.dumps({"error": f"Unknown tool: {tool_name}"})
