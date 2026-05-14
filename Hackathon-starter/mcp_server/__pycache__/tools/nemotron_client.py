"""
nemotron_client.py
Handles all communication with the Nemotron-Nano-9B-v2 model
deployed on Azure AI Foundry via the OpenAI-compatible API.
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# ── Environment Variables ─────────────────────────────────────────────────────

NVIDIA_NIM_ENDPOINT = os.environ["NVIDIA_NIM_ENDPOINT"]
NVIDIA_NIM_API_KEY = os.environ["NVIDIA_NIM_API_KEY"]
MODEL = os.environ["NVIDIA_NIM_MODEL"]

# Remove accidental /chat/completions suffix if present
base_url = NVIDIA_NIM_ENDPOINT.replace("/chat/completions", "").rstrip("/")

# OpenAI-compatible client
client = OpenAI(
    base_url=base_url,
    api_key=NVIDIA_NIM_API_KEY,
)

MAX_TOKENS = int(os.getenv("NEMO_MAX_TOKENS", "4096"))

# Lower temperature improves JSON consistency
TEMPERATURE = float(os.getenv("NEMO_TEMPERATURE", "0"))

# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert code reviewer and security analyst.

Your task is to analyze source code and return a STRICT JSON response.

CRITICAL RULES:

- Return ONLY valid JSON.
- Do NOT return markdown.
- Do NOT wrap JSON in triple backticks.
- Do NOT explain anything outside the JSON object.
- Every issue MUST include exact line numbers.
- severity_score must be an integer from 1 to 10.
- severity must be one of:
  critical, high, medium, low, info
- category must be one of:
  security, bug, performance, style, refactor

Return EXACTLY this structure:

{
  "summary": "one sentence overall assessment",
  "issues": [
    {
      "id": 1,
      "severity": "high",
      "severity_score": 8,
      "category": "security",
      "title": "Hardcoded API secret in source code",
      "description": "The variable SECRET_KEY is hardcoded.",
      "line_start": 12,
      "line_end": 12,
      "code_snippet": "SECRET_KEY = 'abc123'",
      "fix_suggestion": "Replace with os.getenv('SECRET_KEY')",
      "impact": "Exposed credentials can leak secrets"
    }
  ]
}
"""

# ── Prompt Builder ────────────────────────────────────────────────────────────

def build_user_prompt(
    code: str,
    filename: Optional[str],
    language: Optional[str],
) -> str:
    """Build user prompt with metadata and code."""

    context_parts = []

    if filename:
        context_parts.append(f"Filename: {filename}")

    if language:
        context_parts.append(f"Language: {language}")

    context = "\n".join(context_parts)

    return f"""
Analyze the following code and return your findings as STRICT JSON ONLY.

{context}

CODE TO ANALYZE:

{code}

Return ONLY the JSON object.
"""

# ── Main Analysis Function ────────────────────────────────────────────────────

def analyze_code(
    code: str,
    filename: Optional[str] = None,
    language: Optional[str] = None,
) -> dict:
    """
    Send code to Nemotron on Azure AI Foundry and return
    a parsed analysis dictionary.
    """

    user_prompt = build_user_prompt(code, filename, language)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    raw = response.choices[0].message.content

    if raw is None:
        raise ValueError("Model returned empty response")

    raw = raw.strip()

    print("\n========== RAW MODEL RESPONSE ==========")
    print(raw)
    print("========================================\n")

    # Remove accidental markdown fences
    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")
    raw = raw.strip()

    # Attempt to extract JSON object
    start = raw.find("{")
    end = raw.rfind("}")

    if start != -1 and end != -1:
        raw = raw[start:end + 1]

    try:
        analysis = json.loads(raw)

    except json.JSONDecodeError as e:
        print("\nFAILED TO PARSE JSON RESPONSE")
        print(raw)
        raise e

    # Attach metadata
    analysis["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    analysis["model"] = MODEL

    return analysis