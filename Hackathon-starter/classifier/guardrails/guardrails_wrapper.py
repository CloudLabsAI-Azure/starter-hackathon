"""
guardrails_wrapper.py
Thin wrapper around NeMo Guardrails LLMRails.
Instantiates once at module load and exposes classify().
The existing classifier endpoint calls classify() instead of
calling the LLM directly — no other changes needed.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root BEFORE reading env vars.
# This file lives at <project_root>/classifier/guardrails/guardrails_wrapper.py
# so parents[2] resolves to the project root where .env lives.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Map NVIDIA NIM credentials to the OpenAI env vars that NeMo Guardrails reads.
# This MUST happen before importing nemoguardrails.
nim_api_key = os.getenv("NVIDIA_NIM_API_KEY", "")
nim_endpoint = os.getenv("NVIDIA_NIM_ENDPOINT", "").strip()

# Some configs provide a full completion path. Guardrails expects a base URL.
if nim_endpoint.endswith("/chat/completions"):
    nim_endpoint = nim_endpoint[: -len("/chat/completions")]

if nim_api_key:
    os.environ["OPENAI_API_KEY"] = nim_api_key
if nim_endpoint:
    os.environ["OPENAI_API_BASE"] = nim_endpoint.rstrip("/")

from nemoguardrails import LLMRails, RailsConfig

# Load config from the same directory as this file
_CONFIG_DIR = Path(__file__).parent
_config     = RailsConfig.from_path(str(_CONFIG_DIR))
_rails      = LLMRails(_config)


async def classify(expense_description: str) -> str:
    """
    Classify an expense description through NeMo Guardrails.
    """

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expense classification system. "
                "Your ONLY output must be exactly one of these three words: "
                "'needs', 'wants', or 'goals'. "
                "Do not explain, do not refuse, do not add any other text. "
                "Examples: For 'groceries', output: needs. "
                "For 'movie ticket', output: wants. "
                "For 'gym membership', output: goals. "
                "Now classify this expense."
            ),
        },
        {
            "role": "user",
            "content": expense_description,
        }
    ]

    print(f"\n========== GUARDRAILS DEBUG ==========")
    print(f"INPUT: {expense_description!r}")

    result = await _rails.generate_async(messages=messages)

    print(f"RAW RESULT: {result!r}")

    if isinstance(result, dict):
        if "content" in result:
            output = result["content"]
        elif "messages" in result and result["messages"]:
            output = result["messages"][-1].get("content", "")
        else:
            output = str(result)
    else:
        output = str(result)

    print(f"FINAL OUTPUT: {output!r}")
    print(f"=======================================\n")
    return output