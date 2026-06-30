"""
Application configuration loaded from environment variables
"""
import json
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure OpenAI / AIServices
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-oss-120b"
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    # Azure AI Agents / Foundry endpoint (AIServices cognitiveservices URL)
    # When set, the OrchestratorAgent will use azure-ai-agents SDK instead of
    # raw AsyncAzureOpenAI — works with DefaultAzureCredential / managed identity.
    AZURE_FOUNDRY_ENDPOINT: str = ""

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

    # App — stored as raw string, parsed via property
    # Accepts: '["https://a.com"]'  OR  'https://a.com,http://b.com'  OR  'https://a.com'
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

    class Config:
        env_file = ".env"
        # Allow CORS_ORIGINS as an alias for CORS_ORIGINS_RAW so existing env vars still work
        env_prefix = ""


settings = Settings()
