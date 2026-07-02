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


@app.get("/connectivity")
async def connectivity_check():
    """Debug endpoint — tests outbound HTTPS from inside the container."""
    import httpx
    results = {}
    urls = [
        ("openai_azure",     "https://discoveryai-aisvc-dev.openai.azure.com/"),
        ("cognitiveservices","https://discoveryai-aisvc-dev.cognitiveservices.azure.com/"),
        ("httpbin",          "https://httpbin.org/get"),
    ]
    async with httpx.AsyncClient(timeout=10) as client:
        for name, url in urls:
            try:
                r = await client.get(url)
                results[name] = {"status": r.status_code, "ok": True}
            except Exception as e:
                results[name] = {"status": None, "ok": False, "error": str(e)[:200]}
    return results


@app.get("/health/connectivity")
async def connectivity_check():
    """
    Probe outbound connectivity from inside the container to key endpoints.
    Returns per-host status so we can diagnose Container App egress issues.
    """
    import httpx

    probes = {
        "openai_azure": f"{settings.AZURE_OPENAI_ENDPOINT}openai/deployments?api-version={settings.AZURE_OPENAI_API_VERSION}",
        "cognitive_services": "https://discoveryai-aisvc-dev.cognitiveservices.azure.com/",
        "cosmos": settings.COSMOS_ENDPOINT,
        "search": settings.SEARCH_ENDPOINT,
        "internet": "https://httpbin.org/get",
    }

    results = {}
    async with httpx.AsyncClient(timeout=8.0) as client:
        for name, url in probes.items():
            try:
                r = await client.get(
                    url,
                    headers={"api-key": settings.AZURE_OPENAI_KEY} if "openai" in name or "cognitive" in name else {},
                )
                results[name] = {"status": r.status_code, "ok": True}
            except httpx.ConnectError as e:
                results[name] = {"status": "CONNECT_ERROR", "ok": False, "detail": str(e)[:200]}
            except httpx.TimeoutException:
                results[name] = {"status": "TIMEOUT", "ok": False}
            except Exception as e:
                results[name] = {"status": "ERROR", "ok": False, "detail": str(e)[:200]}

    return {"endpoint": settings.AZURE_OPENAI_ENDPOINT, "probes": results}
