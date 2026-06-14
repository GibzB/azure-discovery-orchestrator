"""
Azure Cosmos DB Service - session and conversation persistence
"""
from azure.cosmos.aio import CosmosClient

from app.core.config import settings


class CosmosService:
    def __init__(self) -> None:
        self.client = CosmosClient(
            url=settings.COSMOS_ENDPOINT,
            credential=settings.COSMOS_KEY,
        )
        self.database_name = settings.COSMOS_DATABASE
        self.container_name = settings.COSMOS_CONTAINER

    async def upsert_session(self, session: dict) -> dict:
        db = self.client.get_database_client(self.database_name)
        container = db.get_container_client(self.container_name)
        return await container.upsert_item(session)

    async def get_session(self, session_id: str) -> dict | None:
        db = self.client.get_database_client(self.database_name)
        container = db.get_container_client(self.container_name)
        try:
            return await container.read_item(item=session_id, partition_key=session_id)
        except Exception:
            return None
