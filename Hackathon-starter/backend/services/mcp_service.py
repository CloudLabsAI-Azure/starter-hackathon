"""
MCP Service - Direct Azure OpenAI Integration
Calls Azure OpenAI directly for AI classification (no separate MCP server needed)
"""

import httpx
import json
from typing import Dict, Any
from backend.core.config import settings


class MCPService:
    """Service for AI classification using Azure OpenAI directly"""
    
    @staticmethod
    async def classify_expense_ai(
        description: str,
        amount: float,
        category: str
    ) -> Dict[str, Any]:
        """
        Classify expense using Azure OpenAI directly
        
        Args:
            description: Expense description
            amount: Expense amount
            category: Optional category hint
            
        Returns:
            Dict with classification, confidence, and reasoning
        """
        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
            return {
                "classification": "wants",
                "confidence": 0.5,
                "reasoning": "Azure OpenAI not configured, using default classification"
            }
        
        try:
            # Build the Azure OpenAI endpoint URL
            url = f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={settings.AZURE_OPENAI_API_VERSION}"
            
            # Create the prompt for expense classification
            system_prompt = """You are a personal finance assistant. Classify expenses into one of these categories:
- needs: Essential expenses (groceries, rent, utilities, healthcare, insurance, transportation to work)
- wants: Non-essential but desired items (entertainment, dining out, hobbies, luxury items)
- goals: Future-oriented savings or investments (retirement, emergency fund, down payment)

Respond with valid JSON only: {"classification": "needs|wants|goals", "confidence": 0.0-1.0, "reasoning": "explanation"}"""
            
            user_prompt = f"Classify this expense:\nDescription: {description}\nAmount: ${amount}\nCategory: {category or 'not specified'}"
            
            # Call Azure OpenAI
            headers = {
                "Content-Type": "application/json",
                "api-key": settings.AZURE_OPENAI_API_KEY
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
                
                # Extract the AI response
                ai_response = result["choices"][0]["message"]["content"].strip()
                
                # Parse JSON response
                try:
                    classification_data = json.loads(ai_response)
                    return {
                        "classification": classification_data.get("classification", "wants"),
                        "confidence": classification_data.get("confidence", 0.5),
                        "reasoning": classification_data.get("reasoning", "AI classification completed")
                    }
                except json.JSONDecodeError:
                    # Fallback if response isn't valid JSON
                    return {
                        "classification": "wants",
                        "confidence": 0.5,
                        "reasoning": f"AI response: {ai_response}"
                    }
                    
        except httpx.HTTPError as e:
            print(f"Azure OpenAI API error: {e}")
            return {
                "classification": "wants",
                "confidence": 0.3,
                "reasoning": f"Error calling Azure OpenAI: {str(e)}"
            }
        except Exception as e:
            print(f"Unexpected error in AI classification: {e}")
            return {
                "classification": "wants",
                "confidence": 0.3,
                "reasoning": f"Unexpected error: {str(e)}"
            }