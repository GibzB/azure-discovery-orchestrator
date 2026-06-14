"""
Azure Discovery Orchestrator — FastAPI Entry Point
"""
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

# Module-level MCP manager (kept alive for app lifetime)
_mcp: MCPClientManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mcp

    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("Starting Azure Discovery Orchestrator…")

    # Connect to both MCP servers (non-fatal if unavailable)
    _mcp = MCPClientManager()
    await _mcp.start()

    # Wire ConversationService singleton (speech + agent + MCP)
    svc = ConversationService(mcp=_mcp)
    set_conversation_service(svc)

    logger.info("All services ready.")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down…")
    if _mcp:
        await _mcp.close()


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
