import httpx
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()

class ModelInfo(BaseModel):
    id: str
    name: str
    pricing: Dict[str, Any] = {}

@router.get("/models")
async def get_models(api_key: str = None):
    """
    Fetch available models from OpenRouter.
    Allows passing API key via query param or using server-side env var.
    """
    key_to_use = api_key or settings.OPENROUTER_API_KEY
    
    # if not key_to_use:
    #     # Return a default fallback list if no key is present yet
    #     return {
    #         "data": [
    #             {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
    #             {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"},
    #             {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
    #             {"id": "google/gemini-pro", "name": "Gemini Pro"},
    #         ]
    #     }

    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {key_to_use}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                # Fallback if key is invalid or request fails
                print(f"Failed to fetch models: {response.text}")
                return {"data": [{"id": "openai/gpt-3.5-turbo", "name": "Fallback: GPT-3.5"}]}
            
            data = response.json()
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
