"""
Azure Discovery Orchestrator — FastAPI Entry Point
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.deps import set_conversation_service
from app.core.config import settings
from app.mcp.client import MCPClientManager
from app.services.conversation_service import ConversationService

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

_mcp: MCPClientManager | None = None


async def _connect_mcp_background(mcp: MCPClientManager) -> None:
    """Connect to MCP servers in the background — never blocks startup."""
    try:
        await asyncio.wait_for(mcp.start(), timeout=30.0)
        logger.info("MCP connected in background: %d tools", len(mcp.all_tools_for_openai()))
    except Exception as exc:
        logger.warning("MCP background connect failed (non-fatal): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mcp

    logger.info("Starting Azure Discovery Orchestrator…")

    # Create MCP manager and ConversationService immediately
    _mcp = MCPClientManager()
    svc = ConversationService(mcp=_mcp)
    set_conversation_service(svc)

    # Connect MCP in background — app is healthy before this completes
    asyncio.create_task(_connect_mcp_background(_mcp))

    logger.info("App ready — MCP connecting in background.")
    yield

    logger.info("Shutting down…")
    try:
        await asyncio.wait_for(_mcp.close(), timeout=5.0)
    except Exception:
        pass


app = FastAPI(
    title="Azure Discovery Orchestrator",
    description="AI-powered conversational Azure architecture discovery engine",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    tools_available = len(_mcp.all_tools_for_openai()) if _mcp else 0
    return {
        "status": "healthy",
        "service": "azure-discovery-orchestrator",
        "mcp_tools_available": tools_available,
    }
