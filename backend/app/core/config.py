"""
Application configuration loaded from environment variables.

Uses pydantic-settings v2. All values are read from environment variables.
The .env file is used for local development only — in Container Apps,
env vars are set directly on the resource and override the .env file.
"""
import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=False,
        case_sensitive=False,
        extra="ignore",
    )

    # Azure OpenAI / AIServices
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-oss-120b"
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    # Azure AI Agents / Foundry endpoint (if set, preferred over AZURE_OPENAI_ENDPOINT)
    AZURE_FOUNDRY_ENDPOINT: str = ""

    # Azure Speech (STT + TTS)
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

    # Azure Blob Storage
    STORAGE_CONNECTION_STRING: str = ""
    STORAGE_REPORTS_CONTAINER: str = "reports"
    STORAGE_KNOWLEDGEBASE_CONTAINER: str = "knowledgebase"

    # App
    CORS_ORIGINS_RAW: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"

    @property
    def CORS_ORIGINS(self) -> list[str]:
        v = self.CORS_ORIGINS_RAW.strip()
        if v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]


settings = Settings()
