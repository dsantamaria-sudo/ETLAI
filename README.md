# ETL Pipeline with AI Skills

An ETL (Extract, Transform, Load) framework that uses an LLM to automatically parse and clean Excel files — no hardcoded logic, just natural language instructions per step.

## What it does

Point it at any Excel file and it will:
1. Find which row contains the column headers (skipping titles/metadata at the top)
2. Find where the real data ends (ignoring blank rows, totals, footers)
3. Drop empty or irrelevant columns
4. Extract the clean dataset as structured JSON

Each of these steps is powered by an AI model that can read the spreadsheet and reason about its structure, rather than relying on brittle rules.

## How the technology works

### LLM + Tool Use

The core idea is **tool-augmented AI**. Instead of just asking an LLM "what are the headers?", we give it the ability to actively inspect the file:

```
You (pipeline) ──► LLM: "find the headers"
                    │
                    ▼  (LLM decides to call a tool)
                   run_python("import openpyxl; wb = ...")
                    │
                    ▼  (tool returns output)
                   LLM reads output, reasons, calls more tools if needed
                    │
                    ▼  (LLM is satisfied)
                   {"header_row": 3, "headers": ["Date", "Amount", ...]}
```

The model can write and execute Python code to inspect any part of the spreadsheet. The sandbox pre-loads the most common libraries (`openpyxl`, `pandas`, `json`, `re`, `Path`) so skill code doesn't need explicit import statements. It loops — inspect → reason → inspect again — until it has enough information to give a confident answer.

### Skills Architecture

Each processing step is a **skill**: a folder containing a `SKILL.md` file with plain-English instructions for the model. No Python code per step — just a description of what to do and what to return.

```
skills/
├── detect_headers/SKILL.md   ← "find the row that names the columns"
├── detect_bottom/SKILL.md    ← "find the last row of real data"
├── strip_empty_cols/SKILL.md ← "remove columns that are entirely empty"
├── strip_totals/SKILL.md     ← "remove summary/total rows"
├── extract_clean/SKILL.md    ← "extract the dataset as a list of rows"
└── export_clean/SKILL.md     ← "write the result to a clean file"
```

### Shared State

Steps run sequentially and share a state dictionary. Each step reads what previous steps found and adds its own results:

```python
# After detect_headers:
state = {"excel_path": "...", "header_row": 3, "headers": ["Date", "Amount"]}

# After detect_bottom:
state = {..., "data_end_row": 47}

# After strip_empty_cols:
state = {..., "col_indices": [1, 2, 4]}  # column 3 was empty
```

The model always receives the full current state, so each step has the context of everything discovered so far.

## Project structure

```
etl-pipeline/
├── main.py               # Entry point — runs the pipeline
├── pipeline/
│   ├── runner.py         # Core loop: runs each skill step
│   ├── tools.py          # run_python tool (executes code for the model)
│   └── skill.py          # Loads and parses SKILL.md files
├── skills/               # One folder per step, each with a SKILL.md
└── input/                # Put your Excel files here
```

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **An OpenAI API key** (or a MiniMax API key if using MiniMax)

To install `uv` (if you don't have it):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup

**1. Clone the repo**

```bash
git clone <repo-url>
cd etl-pipeline
```

**2. Install dependencies**

```bash
uv sync
```

This reads `pyproject.toml` and installs everything into an isolated virtual environment automatically. No need to create a venv manually.

**3. Set your API key**

Create a `.env` file in the project root. The pipeline supports two providers:

**OpenAI** (default):
```
OPENAI_API_KEY=sk-...your-key-here...
```
The default model is `gpt-5-2025-08-07`. Override with `OPENAI_MODEL=<model-id>`.

**MiniMax**:
```
LLM_PROVIDER=minimax
MINIMAX_API_KEY=...your-key-here...
```
The default MiniMax model is `MiniMax-M2.7`. Override with `MINIMAX_MODEL=<model-id>`.

## Running it

**With a file picker (easiest):**

```bash
uv run python main.py
```

A dialog will open for you to select an Excel file.

**With a file path directly:**

```bash
uv run python main.py input/sample.xlsx
```

### What you'll see

The terminal shows each step as it runs — the system prompt sent to the model, each Python snippet the model executes, the result, and the final extracted state:

```
──────────── Step 1/2: detect_headers ────────────
⚙ tool call: run_python
✓ result: {"stdout": "Row 1: ['Q1 Sales Report', None, ...]\nRow 2: ..."}
⚙ tool call: run_python
✓ result: ...
╭─ Step Output ─╮
│ {              │
│   "header_row": 3,
│   "headers": ["Date", "Region", "Amount"]
│ }              │
╰───────────────╯
✓ detect_headers — {"header_row": 3, "headers": [...]}
```

## Adding a new skill

1. Create a folder under `skills/`, e.g. `skills/normalize_dates/`
2. Add a `SKILL.md` with two sections:

```markdown
## Instructions

You are processing an Excel file. The state contains `header_row`, `headers`, and `rows`.

Find any columns that look like dates and normalize them to ISO 8601 format (YYYY-MM-DD).

Return ONLY a JSON object:
{"rows": [[<value>, ...], ...]}
```

3. Add the skill path to `SKILL_PATHS` in `main.py`:

```python
SKILL_PATHS = [
    "skills/detect_headers",
    "skills/detect_bottom",
    "skills/normalize_dates",  # ← new
]
```

That's it. The model will receive the current state and figure out what to do from your instructions.

## Dependencies

| Package | Purpose |
|---|---|
| `openai` | Calls the LLM (OpenAI or MiniMax via OpenAI-compatible API) |
| `openpyxl` | Reads `.xlsx` files (available in the model's Python sandbox) |
| `pandas` | Data manipulation (available in the model's Python sandbox) |
| `python-dotenv` | Loads API keys from `.env` |
| `rich` | Pretty terminal output |
