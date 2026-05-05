import os
from openai import OpenAI

PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()

if PROVIDER == "minimax":
    MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7")
    client = OpenAI(
        base_url="https://api.minimax.io/v1",
        api_key=os.environ["MINIMAX_API_KEY"],
    )
else:
    MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-2025-08-07")
    client = OpenAI()
