"""
RAG Indexer - chunks and indexes knowledge base documents into Azure AI Search
"""
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

from app.core.config import settings


class RAGIndexer:
    def __init__(self) -> None:
        self.client = SearchClient(
            endpoint=settings.SEARCH_ENDPOINT,
            index_name=settings.SEARCH_INDEX,
            credential=AzureKeyCredential(settings.SEARCH_KEY),
        )

    async def index_documents(self, documents: list[dict]) -> None:
        async with self.client:
            await self.client.upload_documents(documents=documents)
