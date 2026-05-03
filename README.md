# ETL Pipeline with AI Skills

An ETL (Extract, Transform, Load) framework that uses an LLM to automatically parse and clean Excel files — no hardcoded logic, just natural language instructions per step.

## What it does

Point it at any Excel file and it will:
1. Find which row contains the column headers (skipping titles/metadata at the top)
2. Find where the real data ends (ignoring blank rows, totals, footers)
3. Remove summary/total rows
4. Drop empty columns
5. Extract the clean dataset as structured JSON
6. Export the result to a new Excel file

Each step is powered by an AI model that can read the spreadsheet and reason about its structure. Once a step is working well, it can be replaced by a deterministic `solution.py` that runs without any LLM call.

---

## How the technology works

### LLM + Tool Use

The core idea is **tool-augmented AI**. Instead of just asking an LLM "what are the headers?", we give it the ability to actively inspect the file:

```
You (pipeline) ──► LLM: "find the headers"
                    │
                    ▼  (LLM decides to call a tool)
                   run_python("import pandas as pd; df = pd.read_excel(...)")
                    │
                    ▼  (tool returns output)
                   LLM reads output, reasons, calls more tools if needed
                    │
                    ▼  (LLM is satisfied)
                   {"header_row": 3, "headers": ["Date", "Amount", ...]}
```

The model can write and execute Python code to inspect any part of the spreadsheet. The sandbox pre-loads the most common libraries (`openpyxl`, `pandas`, `json`, `re`, `Path`) so skill code doesn't need explicit imports. It loops — inspect → reason → inspect again — until it has enough information to give a confident answer.

### Skills Architecture

Each processing step is a **skill**: a folder containing a `SKILL.md` file with plain-English instructions and optionally a `solution.py` for cache-based execution.

```
skills/
├── detect_headers/
│   ├── SKILL.md       ← instructions for the LLM
│   ├── checker.py     ← validates the step output
│   └── solution.py    ← (optional) deterministic code, skips the LLM
├── detect_bottom/
├── strip_totals/
├── strip_empty_cols/
├── extract_clean/
└── export_clean/
```

### Execution priority

For each step the runner follows this order:

```
1. solution.py exists?
   └─ YES → run it directly (no LLM call)
             checker passes? → done ✓
             checker fails?  → fall through to LLM
   └─ NO  → go to LLM

2. Call LLM → model writes + executes Python → returns JSON
   └─ checker passes? → save code as solution.py (cache), done ✓
   └─ checker fails?  → retry with error hint
```

### Shared State

Steps run sequentially and share a state dictionary. Each step reads what previous steps found and adds its own results:

```python
state = {"excel_path": "..."}           # start
      → {"header_row": 3, "headers": [...]}           # after detect_headers
      → {..., "data_end_row": 47}                     # after detect_bottom
      → {..., "excluded_rows": [8, 17]}               # after strip_totals
      → {..., "col_indices": [0, 1, 3], "headers": [...]}  # after strip_empty_cols
      → {..., "rows": [[...], ...]}                   # after extract_clean
      → {..., "output_path": "file_clean.xlsx"}       # after export_clean
```

The `state` dict is also injected as a variable inside every `solution.py`, so deterministic scripts can read `header_row`, `col_indices`, etc. without hardcoding them.

---

## Project structure

```
etl-pipeline/
├── main.py                  # Entry point — runs the pipeline
├── optimize.py              # CLI to optimize a skill's Instructions via LLM
├── generalize.py            # CLI to synthesize a solution.py from test cases
├── pipeline/
│   ├── runner.py            # Core loop: runs each skill step
│   ├── tools.py             # run_python tool (executes code for the model)
│   ├── skill.py             # Loads and parses SKILL.md files
│   ├── evaluator.py         # Runs a skill against test files, returns EvalResult
│   ├── optimizer.py         # Calls the LLM to rewrite Instructions
│   ├── config.py            # Provider / model configuration
│   ├── cache.py             # solution.py read/write helpers
│   └── validators.py        # Common output validators
├── skills/                  # One folder per step
└── input/                   # Put your Excel files here
```

---

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **An OpenAI API key** (or a MiniMax API key if using MiniMax)

```bash
# Install uv — macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install uv — Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup

```bash
git clone <repo-url>
cd etl-pipeline
uv sync
```

Create a `.env` file:

```env
# Provider: openai | minimax (default: openai)
LLM_PROVIDER=openai

OPENAI_API_KEY=sk-...your-key-here...
# OPENAI_MODEL=gpt-4o          # optional override

# MINIMAX_API_KEY=...           # only needed if LLM_PROVIDER=minimax
# MINIMAX_MODEL=MiniMax-M2.7
```

| `LLM_PROVIDER` | Required key | Default model |
|---|---|---|
| `openai` *(default)* | `OPENAI_API_KEY` | `gpt-5-2025-08-07` |
| `minimax` | `MINIMAX_API_KEY` | `MiniMax-M2.7` |

---

## Running the pipeline

```bash
# File picker dialog
uv run python main.py

# Direct path
uv run python main.py input/sample.xlsx

# Protect existing solution.py files (LLM fallback won't overwrite them)
uv run python main.py input/sample.xlsx --read-only-cache
```

---

## Optimizing a skill

When a skill produces wrong results, use `optimize.py` to iteratively improve its `## Instructions` using real test files and a checker.

### 1. Prepare test files

```
skills/detect_headers/optimization/test_files/
├── file_1.xlsx
├── file_1.expected.json    ← {"header_row": 3}
├── file_2.xlsx
├── file_2.expected.json
...
```

`expected.json` is the ground truth for the checker. When present it overrides the structural validation and becomes the only pass/fail criterion.

For skills that depend on previous steps, add a `file_N.state.json` with the required context:

```json
{"header_row": 3, "data_end_row": 47, "excluded_rows": [8]}
```

### 2. Run the optimizer

```bash
uv run python optimize.py skills/detect_headers
uv run python optimize.py skills/detect_headers --max-iterations 10 --target-score 1.0
```

**What happens each iteration:**

```
1. Evaluate current Instructions against all test files → "13/20 passed (65%)"
2. score >= target? → "Already optimized. Done."
3. Show failures table (file, output, reason)
4. LLM rewrites Instructions based on failures
5. Show colored diff (red = removed, green = added)
6. Ask: "Apply this version? [y/n]"
   y → save old Instructions to optimization/history/vN_instructions.md
       update SKILL.md
       append entry to optimization/results.jsonl
       continue to next iteration
   n → exit
```

### 3. Checker with ground truth

Each skill's `checker.py` follows this pattern:

```python
def check(output, state):
    expected_path = Path(state["excel_path"]).with_suffix(".expected.json")
    if expected_path.exists():
        expected = json.loads(expected_path.read_text())
        # compare against ground truth → sole criterion
        ...
    # fallback: structural validation
    ...
```

---

## Generalizing a skill to solution.py

Once a skill reaches 100% on its test files, use `generalize.py` to synthesize a single `solution.py` that runs without any LLM call.

```bash
uv run python generalize.py skills/detect_headers
uv run python generalize.py skills/detect_headers --max-iterations 5 --max-attempts 10
```

**Two-phase process:**

**Phase 1 — Collection** (one-time, uses the LLM):
- Runs the LLM on each test file with `skip_cache=True`
- Validates each result against the checker (uses `expected.json`)
- If wrong, retries up to `--max-attempts` times passing the failure as a hint
- Collects verified `(excel_file, exploration_code, correct_output)` triples

**Phase 2 — Synthesis + Validation loop** (cheap, no LLM per file):
- Sends all collected examples to the LLM: *"write ONE script that handles all these cases"*
- Runs the synthesized code directly against all test files (no LLM)
- If 100% pass → saves as `skills/<name>/solution.py` ✓
- If not → shows failures, asks LLM to fix, repeats up to `--max-iterations`

Once `solution.py` exists, the pipeline uses it automatically. The LLM is only called if the cached solution fails on a new file.

---

## Adding a new skill

1. Create a folder under `skills/`, e.g. `skills/normalize_dates/`
2. Add `SKILL.md`:

```markdown
## Instructions

The state contains `header_row`, `headers`, and `rows`.
Find columns that look like dates and normalize them to ISO 8601 (YYYY-MM-DD).
Return ONLY a JSON object:
{"rows": [[<value>, ...], ...]}
```

3. Add `checker.py`:

```python
def check(output, state):
    if not isinstance(output.get("rows"), list):
        return False, "rows must be a list"
    return True, ""
```

4. Add the skill path to `SKILL_PATHS` in `main.py`:

```python
SKILL_PATHS = [
    ...
    "skills/normalize_dates",
]
```

5. *(Optional)* Add test files to `optimization/test_files/` and run `optimize.py` + `generalize.py`.

---

## Dependencies

| Package | Purpose |
|---|---|
| `openai` | Calls the LLM (OpenAI or MiniMax via OpenAI-compatible API) |
| `openpyxl` | Reads/writes `.xlsx` files |
| `pandas` | Data manipulation in the Python sandbox |
| `python-dotenv` | Loads API keys from `.env` |
| `rich` | Pretty terminal output |
