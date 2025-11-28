from openai import AsyncOpenAI
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.core.config import settings
import asyncio
import httpx
from app.core.logging import logger

# Model tier categorization for intelligent fallback
MODEL_TIERS = {
    "flagship": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "google/gemini-pro-1.5",
        "openai/gpt-4o",
        "anthropic/claude-3-opus"
    ],
    "mid-tier": [
        "anthropic/claude-3-haiku",
        "openai/gpt-3.5-turbo",
        "google/gemini-flash-1.5",
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mistral-medium"
    ],
    "budget": [
        "meta-llama/llama-3.1-8b-instruct",
        "mistralai/mistral-7b-instruct",
        "google/gemma-7b-it",
        "openchat/openchat-7b",
        "01-ai/yi-34b-chat"
    ],
    "coding": [
        "openai/gpt-4-turbo",
        "anthropic/claude-3.5-sonnet",
        "deepseek/deepseek-coder-33b-instruct",
        "codellama/codellama-70b-instruct",
        "phind/phind-codellama-34b-v2"
    ]
}

class LLMService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL

        if not self.api_key:
            raise ValueError("OpenRouter API Key is missing. Please configure it in settings.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        # Fallback tracking
        self.fallback_history: Dict[str, str] = {}
        self.available_models_cache: Optional[List[Dict]] = None
        self.cache_timestamp: Optional[float] = None

    def _get_model_tier(self, model: str) -> str:
        """Determine which tier a model belongs to."""
        for tier, models in MODEL_TIERS.items():
            if model in models:
                return tier
        return "mid-tier"  # Default fallback tier

    def _get_fallback_models(self, model: str, max_fallbacks: int = 3) -> List[str]:
        """Get a list of fallback models from the same tier."""
        tier = self._get_model_tier(model)
        tier_models = MODEL_TIERS[tier].copy()

        # Remove the original model if it's in the list
        if model in tier_models:
            tier_models.remove(model)

        # Put original model first, then fallbacks
        result = [model] + tier_models[:max_fallbacks]
        return result

    async def stream_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-3.5-turbo",
        temperature: float = 0.7,
        max_retries: int = 3,
        websocket: Optional[Any] = None,
        node_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams completion with automatic fallback to equivalent models.

        Returns dict with:
        - chunk: the token content
        - model_used: which model generated this chunk
        - is_fallback: whether a fallback model was used
        - attempt: which attempt this was
        """
        fallback_models = self._get_fallback_models(model, max_retries - 1)
        last_error = None

        for attempt, current_model in enumerate(fallback_models[:max_retries]):
            try:
                logger.info(f"Attempting model: {current_model} (attempt {attempt + 1}/{max_retries})")

                # Notify about fallback if not the first attempt
                if attempt > 0 and websocket and node_id:
                    await websocket.send_json({
                        "type": "model_fallback",
                        "node_id": node_id,
                        "original_model": model,
                        "fallback_model": current_model,
                        "attempt": attempt + 1,
                        "reason": str(last_error) if last_error else "Previous model failed"
                    })

                # Try to stream with this model
                stream = await self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    stream=True
                )

                # Stream successful - yield tokens
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield {
                            "chunk": content,
                            "model_used": current_model,
                            "is_fallback": attempt > 0,
                            "attempt": attempt + 1
                        }

                # Success! Log and return
                if attempt > 0:
                    logger.info(f"✓ Fallback successful: {current_model} worked after {attempt} failures")
                return

            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.error(f"✗ Model {current_model} failed: {error_msg}")

                # Track failure
                self.fallback_history[current_model] = error_msg

                # If this isn't the last attempt, wait with exponential backoff
                if attempt < max_retries - 1:
                    backoff_seconds = 2 ** attempt  # 1s, 2s, 4s
                    logger.info(f"Waiting {backoff_seconds}s before trying next model...")
                    await asyncio.sleep(backoff_seconds)
                    continue
                else:
                    # All models failed - yield error
                    error_message = f"\n[Error: All {max_retries} models failed. Last error: {error_msg}]"
                    logger.error(f"All fallback models exhausted. Giving up.")
                    yield {
                        "chunk": error_message,
                        "model_used": current_model,
                        "is_fallback": True,
                        "attempt": attempt + 1,
                        "error": error_msg
                    }
                    return

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-3.5-turbo",
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Legacy method - streams response without fallback.
        Kept for backward compatibility.
        """
        logger.info(f"LLMService: Requesting {model} via {self.base_url}")
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                     content = chunk.choices[0].delta.content
                     yield content

        except Exception as e:
            logger.error(f"LLM Service Error: {e}")
            yield f"\n[Error: {str(e)}]"

    async def fetch_available_models(self) -> List[Dict[str, Any]]:
        """
        Fetch all available models from OpenRouter.
        Caches results for 1 hour.
        """
        import time

        # Check cache (1 hour TTL)
        if self.available_models_cache and self.cache_timestamp:
            if time.time() - self.cache_timestamp < 3600:
                return self.available_models_cache

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])

                    # Filter out moderated models
                    available_models = [
                        m for m in models
                        if not m.get("is_moderated", False)
                    ]

                    # Update cache
                    self.available_models_cache = available_models
                    self.cache_timestamp = time.time()

                    logger.info(f"Fetched {len(available_models)} models from OpenRouter")
                    return available_models
                else:
                    logger.error(f"Failed to fetch models: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

    def categorize_models_by_pricing(self, models: List[Dict]) -> Dict[str, List[str]]:
        """
        Auto-categorize models into tiers based on pricing.
        """
        tiers = {
            "budget": [],
            "mid-tier": [],
            "flagship": [],
            "coding": []
        }

        for model in models:
            model_id = model.get("id", "")
            pricing = model.get("pricing", {})
            prompt_cost = float(pricing.get("prompt", 0))

            # Categorize by cost (per token)
            if prompt_cost < 0.0001:  # < $0.10 per 1M tokens
                tiers["budget"].append(model_id)
            elif prompt_cost < 0.001:  # < $1 per 1M tokens
                tiers["mid-tier"].append(model_id)
            else:  # >= $1 per 1M tokens
                tiers["flagship"].append(model_id)

            # Special coding category
            if any(keyword in model_id.lower() for keyword in ["code", "coder", "codellama"]):
                tiers["coding"].append(model_id)

        return tiers
