"""
planning_agent.py

Agent 1 of 3 in the AI-Q pipeline.

Receives a file path and produces a structured WorkPlan for the Research Agent.
"""

import json
import os
import uuid

from dotenv import load_dotenv
from openai import OpenAI

from agents.shared_models import AnalysisTask, WorkPlan

load_dotenv()

client = OpenAI(
    base_url=os.getenv("NVIDIA_NIM_BASE_URL"),
    api_key=os.getenv("NVIDIA_NIM_API_KEY"),
)

MODEL = os.getenv("NEMOTRON_MODEL", "nvidia/NVIDIA-Nemotron-Nano-9B-v2")

PLANNING_SYSTEM_PROMPT = """You are a software engineering lead planning a code review.

Given a file path or list of files, produce a structured analysis work plan.

CRITICAL RULES:

- Return ONLY valid JSON. No markdown, no backticks, no explanation.
- priority 1 = most important to analyze first.
- severity_threshold: integer 1-10. Issues at or above this score trigger GitHub actions.
Use 7 for security-focused reviews, 5 for general quality reviews.
- max_issues_per_file: integer. Use 3 to avoid GitHub noise.
- Infer language from file extension: .py=python, .js=javascript, .ts=typescript, .go=go

Return exactly this JSON structure:

{
"tasks": [
    {
        "file_path": "mock-app/app.py",
        "language": "python",
        "priority": 1
    }
],
"severity_threshold": 7,
"max_issues_per_file": 3
}"""

def run(file_paths: list[str], run_id: str = None) -> WorkPlan:
    """
    Entry point for the Planning Agent.

    file_paths: list of file paths to include in analysis.

    Returns a WorkPlan passed to the Research Agent.
    """

    if run_id is None:
        run_id = str(uuid.uuid4())[:8]

    files_str = "\n".join(file_paths)

    user_msg = f"""Create an analysis work plan for these files:

{files_str}

Return ONLY the JSON work plan. No other text."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=1024,
        temperature=0.1,
    )

    raw = response.choices[0].message.content

    print("RAW RESPONSE:")
    print(repr(raw))

    if raw:
        raw = raw.strip()
    else:
        raw = ""

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    import re

    match = re.search(r'\{[\s\S]*\}', raw)

    if not match:
        raise ValueError(f"No JSON object found in model response:\n{raw}")

    json_text = match.group(0)

    print("EXTRACTED JSON:")
    print(json_text)

    plan_dict = json.loads(json_text)

    plan_dict["run_id"] = run_id

    return WorkPlan(**plan_dict)