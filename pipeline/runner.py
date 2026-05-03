import importlib.util
import json
import re
from pathlib import Path

from rich.console import Console
from rich.markup import escape as markup_escape
from rich.panel import Panel

from .tools import TOOLS, dispatch, run_python
from .skill import load_skill, extract_section
from .config import MODEL, PROVIDER, client
from . import cache as cache_module

console = Console()


def _load_checker(skill_path: str):
    checker_path = Path(skill_path) / "checker.py"
    if not checker_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("checker", str(checker_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_json_response(raw: str) -> dict:
    """Parse a JSON dict from model output that may contain multiple concatenated objects."""
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    raw = re.sub(r"```(?:json)?\s*([\s\S]*?)```", r"\1", raw)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    pos, candidates = 0, []
    while pos < len(raw):
        while pos < len(raw) and raw[pos] in " \t\n\r":
            pos += 1
        if pos >= len(raw):
            break
        try:
            obj, pos = decoder.raw_decode(raw, pos)
            if isinstance(obj, dict):
                candidates.append(obj)
        except json.JSONDecodeError:
            pos += 1

    non_code = [c for c in candidates if set(c.keys()) != {"code"}]
    if non_code:
        return non_code[-1]
    if candidates:
        return candidates[-1]
    raise RuntimeError(f"Model returned malformed JSON: {raw!r}")


def _extract_last_code(messages: list) -> str | None:
    last_code = None
    for msg in messages:
        tool_calls = None
        if hasattr(msg, "tool_calls"):
            tool_calls = msg.tool_calls
        elif isinstance(msg, dict):
            tool_calls = msg.get("tool_calls")

        if not tool_calls:
            continue
        for tc in tool_calls:
            if hasattr(tc, "function"):
                name = tc.function.name
                args_str = tc.function.arguments
            else:
                name = tc.get("function", {}).get("name")
                args_str = tc.get("function", {}).get("arguments", "{}")
            if name == "run_python":
                try:
                    last_code = json.loads(args_str).get("code")
                except (json.JSONDecodeError, AttributeError):
                    pass
    return last_code


def _extract_json_from_text(text: str) -> dict | None:
    """Return the last JSON dict found anywhere in text (handles debug prints before the result)."""
    decoder = json.JSONDecoder()
    candidates: list[dict] = []
    pos = 0
    while pos < len(text):
        while pos < len(text) and text[pos] in " \t\n\r":
            pos += 1
        if pos >= len(text):
            break
        try:
            obj, pos = decoder.raw_decode(text, pos)
            if isinstance(obj, dict):
                candidates.append(obj)
        except json.JSONDecodeError:
            pos += 1
    return candidates[-1] if candidates else None


def _run_cached_code(code: str, excel_path: str, state: dict | None = None) -> tuple[dict | None, str | None]:
    result_str = run_python(code, excel_path, state=state)
    result = json.loads(result_str)
    if "error" in result:
        return None, result["error"]
    # Prefer stdout: model solutions typically do print(json.dumps(output)).
    # Locals contain all intermediate variables and may shadow intended output keys.
    stdout = result.get("stdout", "").strip()
    if stdout:
        found = _extract_json_from_text(stdout)
        if found is not None:
            return found, None
    return result.get("locals", {}), None


def run_code(code: str, excel_path: str, state: dict | None = None) -> tuple[dict | None, str | None]:
    """Execute a Python snippet against an Excel file. Returns (output, error)."""
    return _run_cached_code(code, excel_path, state=state)


def run_step(
    skill_content: str,
    state: dict,
    skill_path: str,
    instructions_override: str | None = None,
    skip_cache: bool = False,
    read_only_cache: bool = False,
    _code_sink: list | None = None,
) -> dict:
    skill_dir = str(Path(skill_path))
    excel_path = state["excel_path"]
    checker = _load_checker(skill_path)
    failure_reason: str | None = None

    # Step 1-2: Try cache code
    solution_code = None if skip_cache else cache_module.load_solution(skill_dir)

    if solution_code is not None:
        console.print("[bold cyan][[CACHE HIT]][/bold cyan] Running cached solution...")
        cached_output, error = _run_cached_code(solution_code, excel_path, state=state)

        if error is not None:
            console.print(f"[bold red][[CACHE MISS]][/bold red] Cached code errored: {error}")
            failure_reason = f"Code raised an error: {error}"
            cache_module.save_solution(skill_dir, solution_code, failure_reason=failure_reason)
        elif checker is not None:
            ok, reason = checker.check(cached_output, state)
            if ok:
                console.print("[bold cyan][[CACHE HIT]][/bold cyan] Cached solution is valid. Returning.")
                cache_module.save_solution(skill_dir, solution_code)
                return cached_output
            else:
                console.print(f"[bold red][[CACHE MISS]][/bold red] Checker failed: {reason}")
                failure_reason = reason
                cache_module.save_solution(skill_dir, solution_code, failure_reason=failure_reason)
        else:
            console.print("[bold cyan][[CACHE HIT]][/bold cyan] No checker — using cached output.")
            cache_module.save_solution(skill_dir, solution_code)
            return cached_output
    else:
        console.print("[bold yellow][[CACHE EMPTY]][/bold yellow] No cached solution found.")

    # Step 3: Call the LLM
    instructions = instructions_override if instructions_override is not None else extract_section(skill_content, "Instructions")
    system_prompt = (
        f"{instructions}\n\n"
        f"Always use the variable `excel_path` to reference the Excel file. Never hardcode file paths.\n\n"
        f"## Current state\n{json.dumps(state, indent=2)}"
    )

    if solution_code is not None and failure_reason is not None:
        system_prompt += (
            f"\n\n## Previous solution (failed)\n"
            f"Reason: {failure_reason}\n\n"
            f"{solution_code}\n\n"
            f"Adjust this solution to handle the current case."
        )

    console.print(Panel(markup_escape(system_prompt), title="[bold blue]System Prompt[/bold blue]", border_style="blue"))

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Please process the Excel file now."},
    ]

    while True:
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            assistant_msg = choice.message
            messages.append(assistant_msg)
            for tool_call in assistant_msg.tool_calls:
                tool_args = json.loads(tool_call.function.arguments)
                console.print(f"[bold yellow]⚙ tool call:[/bold yellow] {tool_call.function.name}")
                result = dispatch(tool_call.function.name, tool_args, excel_path)
                console.print(Panel(result, title="[bold green]Tool Result[/bold green]", border_style="green"))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        elif choice.finish_reason == "stop":
            messages.append({"role": "assistant", "content": choice.message.content})
            messages.append({
                "role": "user",
                "content": "Now return your answer as a JSON object only, no extra text.",
            })
            final = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                response_format={"type": "json_object"},
            )
            output = _parse_json_response(final.choices[0].message.content)

            console.print(Panel(json.dumps(output, indent=2), title="[bold magenta]Step Output[/bold magenta]", border_style="magenta"))

            # Step 4-5: Extract last run_python code and persist as solution
            last_code = _extract_last_code(messages)
            if last_code and not skip_cache and not read_only_cache:
                console.print("[bold cyan][[CACHE UPDATED]][/bold cyan] Saving new solution.")
                cache_module.save_solution(skill_dir, last_code)
            if last_code and _code_sink is not None:
                _code_sink.append(last_code)

            return output

        else:
            raise RuntimeError(f"Unexpected finish_reason: {choice.finish_reason!r}")


def run_pipeline(excel_path: str, skill_paths: list[str], read_only_cache: bool = False) -> dict:
    state = {"excel_path": excel_path}

    for i, skill_path in enumerate(skill_paths, start=1):
        skill_content = load_skill(skill_path)
        skill_name = Path(skill_path).name

        console.rule(f"[bold cyan]Step {i}/{len(skill_paths)}: {skill_name}[/bold cyan] [dim]({PROVIDER} / {MODEL})[/dim]")
        step_output = run_step(skill_content, state, skill_path, read_only_cache=read_only_cache)
        state.update(step_output)
        console.print(f"[bold green]✓ {skill_name}[/bold green] — {json.dumps(step_output)}")

    return state
