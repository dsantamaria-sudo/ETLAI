import json

from .config import MODEL, client
from .evaluator import EvalResult
from .skill import extract_section, load_skill


class Optimizer:
    def optimize(self, skill_path: str, eval_result: EvalResult) -> str:
        skill_content = load_skill(skill_path)
        current_instructions = extract_section(skill_content, "Instructions")

        failures_text = "\n\n".join(
            f"**File:** {fc.filename}\n"
            f"**Output:** {json.dumps(fc.output, indent=2)}\n"
            f"**Reason:** {fc.reason}"
            for fc in eval_result.failures
        )

        prompt = (
            "You are optimizing the `## Instructions` section of an ETL pipeline skill.\n\n"
            "## Current Instructions\n\n"
            f"{current_instructions}\n\n"
            "## Failures to Fix\n\n"
            "The current instructions failed on the following test cases:\n\n"
            f"{failures_text}\n\n"
            "## Task\n\n"
            "Rewrite the instructions to fix these failures. Rules:\n"
            "- Output ONLY the new instructions text (the body of ## Instructions).\n"
            "- Do NOT include the `## Instructions` header line.\n"
            "- Do NOT add any explanation, notes, or commentary outside the instructions.\n"
            "- Keep the same general structure and intent; only change what is needed to fix the failures.\n"
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
