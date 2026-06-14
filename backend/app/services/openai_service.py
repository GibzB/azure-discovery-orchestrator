"""
Azure OpenAI Service wrapper
"""
from openai import AsyncAzureOpenAI

from app.core.config import settings


class OpenAIService:
    def __init__(self) -> None:
        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT

    async def chat(self, messages: list[dict], temperature: float = 0.2) -> str:
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
