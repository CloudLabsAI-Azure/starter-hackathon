"""
shared_models.py

Pydantic models shared across all three agents.

These are the typed contracts that carry state through the pipeline.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

# ── Planning Agent Output

class AnalysisTask(BaseModel):
    file_path: str
    language: str
    priority: int              # 1 = highest

class WorkPlan(BaseModel):
    tasks: List[AnalysisTask]
    severity_threshold: int    # minimum severity_score to trigger GitHub action
    max_issues_per_file: int   # cap to avoid flooding GitHub with issues
    run_id: str                # unique identifier for this pipeline run

# ── Research Agent Output

class AnalyzedIssue(BaseModel):
    file_path: str
    severity: str
    severity_score: int
    category: str
    title: str
    description: str
    line_start: int
    line_end: int
    code_snippet: str
    fix_suggestion: str
    impact: str

class AnalysisReport(BaseModel):
    run_id: str
    issues: List[AnalyzedIssue]  # sorted by severity_score desc
    files_analyzed: int
    issues_above_threshold: int

# ── Action Agent Output

class GitHubArtifact(BaseModel):
    issue_number: int
    issue_url: str
    branch_name: str
    pr_number: int
    pr_url: str
    issue_title: str

class GitHubArtifacts(BaseModel):
    run_id: str
    artifacts: List[GitHubArtifact]
    total_issues_created: int
    total_prs_created: int