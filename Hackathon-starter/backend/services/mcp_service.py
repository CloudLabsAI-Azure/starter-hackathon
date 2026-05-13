"""MCP Service - NVIDIA NIM Integration via Azure AI Foundry"""

import json
import httpx
from typing import Optional, Dict, Any
from backend.core.config import settings


class MCPService:
    """Service for AI classification using NVIDIA NIM on Azure AI Foundry"""

    @staticmethod
    async def classify_expense_ai(
        description: str,
        amount: float,
        category: str = None,
    ) -> Dict[str, Any]:

        if not settings.NVIDIA_NIM_ENDPOINT or not settings.NVIDIA_NIM_API_KEY:
            return {
                "classification": "wants",
                "confidence": 0.5,
                "reasoning": "NVIDIA NIM not configured, using default classification"
            }

        try:
            url = settings.NVIDIA_NIM_ENDPOINT

            system_prompt = """You are a personal finance assistant. Classify expenses into one of these categories:
- needs: Essential expenses (groceries, rent, utilities, healthcare, insurance, transportation to work)
- wants: Non-essential but desired items (entertainment, dining out, hobbies, luxury items)
- goals: Future-oriented savings or investments (retirement, emergency fund, down payment)

Respond with valid JSON only: {"classification": "needs|wants|goals", "confidence": 0.0-1.0, "reasoning": "explanation"}"""

            user_prompt = f"Classify this expense:\nDescription: {description}\nAmount: ${amount}\nCategory: {category or 'not specified'}"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.NVIDIA_NIM_API_KEY}"
            }

            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()

            # Debug log — check docker-compose logs to see this
            print("[MCPService] Raw NVIDIA NIM response:", json.dumps(result, indent=2))

            # Safe parsing
            choices = result.get("choices", [])
            if not choices:
                print(f"[MCPService] No choices in response: {result}")
                return {
                    "classification": "wants",
                    "confidence": 0.3,
                    "reasoning": f"No choices returned from model. Full response: {result}"
                }

            message = choices[0].get("message", {})
            ai_response = message.get("content", "").strip()

            if not ai_response:
                return {
                    "classification": "wants",
                    "confidence": 0.3,
                    "reasoning": "Model returned an empty response."
                }

            try:
                clean = ai_response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                classification_data = json.loads(clean)
                return {
                    "classification": classification_data.get("classification", "wants"),
                    "confidence": classification_data.get("confidence", 0.5),
                    "reasoning": classification_data.get("reasoning", "AI classification completed")
                }
            except json.JSONDecodeError:
                return {
                    "classification": "wants",
                    "confidence": 0.5,
                    "reasoning": f"AI response: {ai_response}"
                }

        except httpx.HTTPStatusError as e:
            error_body = e.response.text if e.response else "no body"
            print(f"[MCPService] HTTP error {e.response.status_code}: {error_body}")
            return {
                "classification": "wants",
                "confidence": 0.3,
                "reasoning": f"HTTP {e.response.status_code} from NVIDIA NIM: {error_body}"
            }
        except Exception as e:
            print(f"[MCPService] Unexpected error: {e}")
            return {
                "classification": "wants",
                "confidence": 0.3,
                "reasoning": f"Unexpected error: {str(e)}"
            }