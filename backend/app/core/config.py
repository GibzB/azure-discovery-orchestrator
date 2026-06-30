"""
Application configuration loaded from environment variables
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Any


class Settings(BaseSettings):
    # Azure OpenAI / AIServices
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-oss-120b"
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    # Azure Speech (STT + TTS — speech-to-speech pipeline)
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "eastus"
    AZURE_SPEECH_VOICE: str = "en-US-AvaMultilingualNeural"

    # Azure AI Search
    SEARCH_ENDPOINT: str = ""
    SEARCH_KEY: str = ""
    SEARCH_INDEX: str = "knowledgebase"

    # Cosmos DB
    COSMOS_ENDPOINT: str = ""
    COSMOS_KEY: str = ""
    COSMOS_DATABASE: str = "discovery"
    COSMOS_CONTAINER: str = "sessions"

    # Azure Blob Storage (reports + knowledgebase containers)
    STORAGE_CONNECTION_STRING: str = ""
    STORAGE_REPORTS_CONTAINER: str = "reports"
    STORAGE_KNOWLEDGEBASE_CONTAINER: str = "knowledgebase"

    # App — accepts JSON array, comma-separated string, or single origin
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        """
        Accept all common formats for the CORS_ORIGINS env var:
          - JSON array:       '["https://foo.com","http://localhost:5173"]'
          - Comma-separated:  'https://foo.com,http://localhost:5173'
          - Single value:     'https://foo.com'
          - Already a list:   ['https://foo.com']
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            # Try JSON first
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"


settings = Settings()
