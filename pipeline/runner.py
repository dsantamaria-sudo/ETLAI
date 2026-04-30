import json
import re
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .tools import TOOLS, dispatch
from .skill import load_skill
from .skill import extract_section
from .config import MODEL, PROVIDER, client

console = Console()


def run_step(skill_content: str, state: dict) -> dict:
    instructions = extract_section(skill_content, "Instructions")
    system_prompt = (
        f"{instructions}\n\n"
        f"## Current state\n{json.dumps(state, indent=2)}"
    )

    console.print(Panel(system_prompt, title="[bold blue]System Prompt[/bold blue]", border_style="blue"))

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Please process the Excel file now."},
    ]

    excel_path: str = state["excel_path"]

    while True:
        kwargs = {"model": MODEL, "messages": messages, "tools": TOOLS}
        response = client.chat.completions.create(**kwargs)
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
            raw = final.choices[0].message.content
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
            raw = re.sub(r"```(?:json)?\s*([\s\S]*?)```", r"\1", raw)
            raw = raw.strip()
            try:
                output = json.loads(raw)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Model returned malformed JSON: {raw!r}") from e
            console.print(Panel(json.dumps(output, indent=2), title="[bold magenta]Step Output[/bold magenta]", border_style="magenta"))
            return output
        else:
            raise RuntimeError(f"Unexpected finish_reason: {choice.finish_reason!r}")


def run_pipeline(excel_path: str, skill_paths: list[str]) -> dict:
    state = {"excel_path": excel_path}

    for i, skill_path in enumerate(skill_paths, start=1):
        skill_content = load_skill(skill_path)
        skill_name = Path(skill_path).parent.name

        console.rule(f"[bold cyan]Step {i}/{len(skill_paths)}: {skill_name}[/bold cyan] [dim]({PROVIDER} / {MODEL})[/dim]")
        step_output = run_step(skill_content, state)
        state.update(step_output)
        console.print(f"[bold green]✓ {skill_name}[/bold green] — {json.dumps(step_output)}")

    return state
