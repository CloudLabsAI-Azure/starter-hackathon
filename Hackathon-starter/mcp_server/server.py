"""
Zava MCP Server — AI service with NVIDIA NIM classification.

The classification endpoint calls the NVIDIA NIM inference endpoint, which
exposes an OpenAI-compatible API at /v1/chat/completions.  All NIM
connection details are read from environment variables so they can be
rotated without restarting the process (use POST /reload-env to pick up
changes to the .env file at runtime).
"""

import os
import json
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel

# ── Initial environment load ──────────────────────────────────────────────────
load_dotenv()

app = FastAPI(title="Zava MCP Server", version="1.0.0")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _nim_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured for NVIDIA NIM.

    The client is constructed on every call so that environment variable
    changes made via /reload-env are picked up without restarting the server.
    """
    endpoint = os.environ.get("NVIDIA_NIM_ENDPOINT")
    api_key = os.environ.get("NVIDIA_NIM_API_KEY")

    if not endpoint or not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "NVIDIA NIM is not configured. "
                "Set NVIDIA_NIM_ENDPOINT and NVIDIA_NIM_API_KEY."
            ),
        )

    # Ensure the base_url ends without a trailing slash so the OpenAI client
    # appends /chat/completions correctly.
    return AsyncOpenAI(
        base_url=endpoint.rstrip("/"),
        api_key=api_key,
    )


def _nim_model() -> str:
    model = os.environ.get("NVIDIA_NIM_MODEL")
    if not model:
        raise HTTPException(
            status_code=503,
            detail="NVIDIA_NIM_MODEL is not set.",
        )
    return model


# ── Request / response schemas ────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    text: str
    system_prompt: str = (
        "You are a precise classification assistant. "
        "Respond with only the category label, nothing else."
    )
    categories: list[str] = []


class ClassifyResponse(BaseModel):
    classification: str
    model: str
    usage: dict[str, Any] | None = None


class ReloadResponse(BaseModel):
    status: str
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest) -> ClassifyResponse:
    """Classify *text* using the NVIDIA NIM model.

    The NIM endpoint is OpenAI-compatible, so we use the standard
    /v1/chat/completions path under the hood.
    """
    client = _nim_client()
    model = _nim_model()

    user_content = request.text
    if request.categories:
        category_list = ", ".join(request.categories)
        user_content = (
            f"Classify the following text into one of these categories: "
            f"{category_list}\n\nText: {request.text}"
        )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    classification = response.choices[0].message.content or ""
    usage = None
    if response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    return ClassifyResponse(
        classification=classification.strip(),
        model=model,
        usage=usage,
    )


@app.post("/reload-env", response_model=ReloadResponse)
async def reload_env() -> ReloadResponse:
    """Reload environment variables from the .env file without restarting.

    Call this endpoint after updating the .env file to make the MCP server
    pick up new values for NVIDIA_NIM_ENDPOINT, NVIDIA_NIM_API_KEY,
    NVIDIA_NIM_MODEL, or any other variable.
    """
    load_dotenv(override=True)
    return ReloadResponse(
        status="ok",
        message="Environment variables reloaded from .env.",
    )


from datetime import datetime, timezone
from fastapi import HTTPException
from mcp_server.models import AnalyzeRequest, AnalyzeResponse
from mcp_server.tools.nemotron_client import analyze_code
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: AnalyzeRequest):
   """
   POST /api/v1/analyze

   Accepts a code snippet and routes it to Nemotron-Nano-9b-v2
   on Azure AI Foundry. Returns a structured JSON analysis.
   """

   logger.info(f"Analyze request received: filename={request.filename}")

   try:
      result = analyze_code(
            code=request.code,
            filename=request.filename,
            language=request.language,
      )

      return AnalyzeResponse(**result)

   except json.JSONDecodeError as e:
      logger.error(f"Nemotron returned non-JSON response: {e}")

      raise HTTPException(
            status_code=502,
            detail="Model returned an unparseable response. Retry or check prompt template."
      )

   except Exception as e:
      logger.error(f"Analysis failed: {e}")

      raise HTTPException(
            status_code=500,
            detail=f"Analysis error: {str(e)}"
      )