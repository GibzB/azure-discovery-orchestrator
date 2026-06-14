"""
RAG Retriever - queries Azure AI Search for relevant knowledge base chunks
"""
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

from app.core.config import settings


class RAGRetriever:
    def __init__(self) -> None:
        self.client = SearchClient(
            endpoint=settings.SEARCH_ENDPOINT,
            index_name=settings.SEARCH_INDEX,
            credential=AzureKeyCredential(settings.SEARCH_KEY),
        )

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        results = []
        async with self.client:
            search_results = await self.client.search(
                search_text=query,
                top=top_k,
                select=["id", "content", "source", "category"],
            )
            async for result in search_results:
                results.append(dict(result))
        return results
