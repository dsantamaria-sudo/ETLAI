# ETL Pipeline with Skills Architecture

## Overview

Build a Python ETL framework that processes Excel files through a sequential pipeline of AI-powered steps. Each step is defined by a `SKILL.md` file that instructs the model on what to do. After each step, a second model call verifies the output before proceeding.

## Project Structure

```
etl-pipeline/
├── CLAUDE.md
├── pyproject.toml
├── .python-version
├── README.md
├── main.py                  # Entry point
├── pipeline/
│   ├── __init__.py
│   ├── runner.py            # Core pipeline loop
│   ├── verifier.py          # LLM-as-a-judge logic
│   ├── tools.py             # Excel tools exposed to the model
│   └── skill.py             # SKILL.md loader and parser
├── skills/
│   ├── detect_headers/
│   │   └── SKILL.md
│   └── detect_bottom/
│       └── SKILL.md
└── input/
    └── sample.xlsx          # Example input file
```

## Setup

Use `uv` for dependency management. Create `pyproject.toml` with:

```toml
[project]
name = "etl-pipeline"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "openai>=1.30.0",
    "openpyxl>=3.1.0",
    "rich>=13.0.0",
]
```

Create `.python-version` with `3.11`.

## Core Concepts

### State

The pipeline passes a shared state dict between steps. It starts with the Excel path and accumulates results:

```python
state = {
    "excel_path": "input/sample.xlsx",
    # populated by steps:
    # "headers": [...],
    # "header_row": 2,
    # "data_end_row": 47,
}
```

### Skills

Each skill is a folder with a `SKILL.md` file. The SKILL.md has two sections:

1. **Instructions** — what the model should do in this step
2. **Success criteria** — what the verifier checks

Example `skills/detect_headers/SKILL.md`:

```markdown
## Instructions

You are processing an Excel file. Your task is to identify the header row.

Inspect the first 10 rows of the Excel file using the available tools.
Headers are typically strings, non-empty, and appear before any numeric data rows.
The row immediately before headers is often empty or contains metadata.

Once identified, return ONLY a JSON object with no extra text:
{"header_row": <int>, "headers": [<string>, ...]}

## Success criteria

- header_row is an integer >= 1
- headers is a non-empty list
- all items in headers are non-empty strings
```

Example `skills/detect_bottom/SKILL.md`:

```markdown
## Instructions

You are processing an Excel file. You already know the header row and column names from previous steps.

Your task is to find the last row that contains actual data (not empty rows, totals, or footers).
Use the available tools to scan from the bottom of the file upward.

Return ONLY a JSON object:
{"data_end_row": <int>}

## Success criteria

- data_end_row is an integer
- data_end_row is greater than header_row
```

### Tools exposed to the model

These are implemented with `openpyxl` and declared to the OpenAI API as function tools:

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_dimensions",
            "description": "Returns total row and column count of the Excel file.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_row",
            "description": "Returns all cell values in a given row as a list.",
            "parameters": {
                "type": "object",
                "properties": {"row": {"type": "integer", "description": "1-indexed row number"}},
                "required": ["row"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_range",
            "description": "Returns a 2D list of cell values for a rectangular range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "row_start": {"type": "integer"},
                    "row_end": {"type": "integer"},
                    "col_start": {"type": "integer"},
                    "col_end": {"type": "integer"},
                },
                "required": ["row_start", "row_end", "col_start", "col_end"],
            },
        },
    },
]
```

Implement them in `pipeline/tools.py` using `openpyxl`. The `tools.py` module should expose:
- A class `ExcelTools(excel_path: str)` with methods `get_dimensions()`, `read_row(row)`, `read_range(row_start, row_end, col_start, col_end)`
- A function `dispatch(tool_name: str, tool_args: dict, excel_tools: ExcelTools) -> str` that routes tool calls and returns a JSON string result

### Pipeline runner

`pipeline/runner.py` contains `run_step(client, skill_content, state, excel_tools)`:

1. Build the system prompt from the skill's Instructions section + current state as JSON context
2. Run the model in a tool-call loop:
   - Call `gpt-4.1-mini-2025-04-14` with `tools=TOOLS` and `response_format={"type": "json_object"}` (only when finish_reason is "stop", not during tool calls)
   - If `finish_reason == "tool_calls"`, execute each tool call via `dispatch()`, append tool results to messages, and loop
   - If `finish_reason == "stop"`, parse the JSON response and return it
3. Merge the step output into state and return updated state

### Verifier

`pipeline/verifier.py` contains `verify_step(client, skill_content, step_output, state)`:

1. Extract the Success criteria section from the SKILL.md
2. Call `gpt-4.1-mini-2025-04-14` (no tools needed) with a prompt that includes:
   - The success criteria
   - The step output as JSON
   - Current state for context
3. Ask it to return `{"ok": true/false, "reason": "..."}` 
4. Return the parsed result

### Main pipeline loop

`pipeline/runner.py` also contains `run_pipeline(excel_path, skill_paths, max_retries=3)`:

```python
state = {"excel_path": excel_path}
excel_tools = ExcelTools(excel_path)

for skill_path in skill_paths:
    skill_content = load_skill(skill_path)
    skill_name = Path(skill_path).parent.name

    for attempt in range(1, max_retries + 1):
        step_output = run_step(client, skill_content, state, excel_tools)
        verification = verify_step(client, skill_content, step_output, state)

        if verification["ok"]:
            state.update(step_output)
            break
        elif attempt == max_retries:
            raise RuntimeError(f"Step '{skill_name}' failed after {max_retries} attempts: {verification['reason']}")
        else:
            # Pass the failure reason as a hint for the next attempt
            state["_last_error"] = verification["reason"]

return state
```

### Skill loader

`pipeline/skill.py` contains `load_skill(path: str) -> str` which simply reads the SKILL.md file and returns its content as a string. Also provide `extract_section(skill_content, section_title) -> str` that extracts a named `## Section` from the markdown.

### Entry point

`main.py` should:
1. Accept an Excel file path as a CLI argument (use `sys.argv` or `argparse`)
2. Define the ordered list of skill paths
3. Call `run_pipeline()`
4. Print the final state as formatted JSON using `rich`
5. Show progress for each step using `rich` (step name, attempt number, verification result)

## Error handling

- If the model returns malformed JSON, catch and retry with an error hint
- If `openpyxl` fails to open the file, raise a clear error immediately
- If max retries are exceeded, print the last verification failure reason before raising

## Sample skills to create

Create both skills listed above (`detect_headers` and `detect_bottom`) as working examples. Also create a minimal `input/sample.xlsx` using `openpyxl` in a setup script (`scripts/create_sample.py`) that generates a realistic-looking spreadsheet: 2 rows of metadata at the top, 1 header row, 30 data rows, 2 empty rows at the bottom.

## Environment

The OpenAI API key is read from the `OPENAI_API_KEY` environment variable. Do not hardcode it.

## What NOT to build

- No async/await — keep it synchronous for simplicity
- No database — state lives in memory
- No web UI — CLI only
- No parallel execution — steps run sequentially by design
- No skill auto-discovery or model-based skill routing — the caller passes the ordered list explicitly
