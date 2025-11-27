from openai import AsyncOpenAI
from typing import AsyncGenerator, List, Dict, Any
from app.core.config import settings

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

    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "openai/gpt-3.5-turbo",
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Streams the response from OpenRouter.
        """
        print(f"LLMService: Requesting {model} via {self.base_url}")
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
            print(f"LLM Service Error: {e}")
            yield f"\n[Error: {str(e)}]"
