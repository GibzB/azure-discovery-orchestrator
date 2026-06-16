"""
Application configuration loaded from environment variables
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4.1"
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"

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

    # App
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
