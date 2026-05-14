# ─── Analysis Endpoint Models

from pydantic import BaseModel, Field
from typing import List, Optional

class AnalyzeRequest(BaseModel):
    """Request body for POST /api/v1/analyze"""
    code: str = Field(
        ...,
        description="Raw source code to analyze",
        min_length=1,
        max_length=50000
    )
    filename: Optional[str] = Field(
        None,
        description="Optional filename for context (e.g. app.py)"
    )
    language: Optional[str] = Field(
        None,
        description="Optional language hint (e.g. python, javascript)"
    )

class CodeIssue(BaseModel):
    """A single issue found in the analyzed code"""
    id: int
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

class AnalyzeResponse(BaseModel):
    """Response body for POST /api/v1/analyze"""
    summary: str
    analyzed_at: str
    model: str
    issues: List[CodeIssue]