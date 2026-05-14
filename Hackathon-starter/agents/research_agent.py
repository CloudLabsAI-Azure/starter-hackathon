"""
research_agent.py
Agent 2 of 3 in the AI-Q pipeline.
Reads files from the WorkPlan, calls /api/v1/analyze for each,
and produces a ranked AnalysisReport for the Action Agent.
"""

import os
import httpx
from dotenv import load_dotenv
from agents.shared_models import (
    AnalysisReport,
    AnalyzedIssue,
    WorkPlan,
)

load_dotenv()

ANALYZE_URL = (
    f"http://{os.getenv('ANALYZE_ENDPOINT_HOST', 'localhost')}"
    f":{os.getenv('ANALYZE_ENDPOINT_PORT', '8080')}"
    f"/api/v1/analyze"
)

def _read_file(path: str) -> str:
    """Read file content from disk."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _call_analyze(code: str, filename: str, language: str) -> dict:
    """POST to /api/v1/analyze and return the parsed JSON response."""
    payload = {
        "code": code,
        "filename": filename,
        "language": language,
    }
    response = httpx.post(
        ANALYZE_URL,
        json=payload,
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()

def run(work_plan: WorkPlan) -> AnalysisReport:
    """
    Entry point for the Research Agent.
    Iterates through work_plan.tasks, analyzes each file,
    and returns a consolidated AnalysisReport.
    """
    all_issues: list[AnalyzedIssue] = []
    files_analyzed = 0
    # Sort tasks by priority before processing
    sorted_tasks = sorted(
        work_plan.tasks,
        key=lambda t: t.priority,
    )
    for task in sorted_tasks:
        print(f"  [Research] Analyzing: {task.file_path}")
        try:
            code = _read_file(task.file_path)
        except FileNotFoundError:
            print(
                f"  [Research] WARNING: "
                f"File not found: {task.file_path}. Skipping."
            )
            continue
        result = _call_analyze(
            code,
            task.file_path,
            task.language,
        )
        files_analyzed += 1
        # Map endpoint response issues to AnalyzedIssue models
        for issue in result.get("issues", []):
            # Filter by severity threshold
            if issue.get("severity_score", 0) >= work_plan.severity_threshold:
                all_issues.append(
                    AnalyzedIssue(
                        file_path=task.file_path,
                        severity=issue["severity"],
                        severity_score=issue["severity_score"],
                        category=issue["category"],
                        title=issue["title"],
                        description=issue["description"],
                        line_start=issue.get("line_start", 1),
                        line_end=issue.get("line_end", 1),
                        code_snippet=issue.get("code_snippet", ""),
                        fix_suggestion=issue["fix_suggestion"],
                        impact=issue.get("impact", ""),
                    )
                )
    # Sort all issues by severity score descending
    all_issues.sort(
        key=lambda i: i.severity_score,
        reverse=True,
    )
    return AnalysisReport(
        run_id=work_plan.run_id,
        issues=all_issues,
        files_analyzed=files_analyzed,
        issues_above_threshold=len(all_issues),
    )