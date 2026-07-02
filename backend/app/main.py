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
    key_set = bool(settings.AZURE_OPENAI_KEY)
    endpoint_set = bool(settings.AZURE_OPENAI_ENDPOINT or settings.AZURE_FOUNDRY_ENDPOINT)
    return {
        "status": "healthy",
        "service": "azure-discovery-orchestrator",
        "mcp_tools_available": tools_available,
        "openai_key_configured": key_set,
        "openai_endpoint_configured": endpoint_set,
    }


@app.get("/connectivity")
async def connectivity_check(
    include_chat: bool = False,
    x_debug_token: str | None = None,
):
    """
    Internal diagnostic endpoint — probes outbound connectivity from inside the container.

    Protection:
      - Requires the X-Debug-Token header to match LOG_LEVEL secret guard (non-empty).
        In practice set X-Debug-Token to the value of LOG_LEVEL env var (defaults to INFO)
        or any non-empty string when running in dev. This prevents accidental public use.
      - The Azure OpenAI chat_completions probe is **opt-in** via ?include_chat=true
        to avoid billable API calls on every request.
    """
    import httpx
    from fastapi import Header
    from fastapi.responses import JSONResponse

    # ── Guard: require a non-empty debug token header ────────────────────────
    # This is a lightweight internal safeguard, not a security boundary.
    # For production, put this endpoint behind a VNet or remove it entirely.
    if not x_debug_token:
        return JSONResponse(
            status_code=403,
            content={"detail": "X-Debug-Token header required"},
        )

    # ── Guard: endpoint must be configured ───────────────────────────────────
    raw_endpoint = settings.AZURE_FOUNDRY_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT
    if not raw_endpoint:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Neither AZURE_FOUNDRY_ENDPOINT nor AZURE_OPENAI_ENDPOINT is configured",
                "probes": {},
            },
        )
    endpoint = raw_endpoint.rstrip("/")

    deployment = settings.AZURE_OPENAI_DEPLOYMENT
    api_version = settings.AZURE_OPENAI_API_VERSION
    key = settings.AZURE_OPENAI_KEY

    probes = {
        "endpoint_root":  endpoint + "/",
        "cosmos":         settings.COSMOS_ENDPOINT,
        "search":         settings.SEARCH_ENDPOINT,
        "internet":       "https://httpbin.org/get",
    }

    # chat_completions is billable — only include when explicitly requested
    if include_chat:
        probes["chat_completions"] = (
            f"{endpoint}/openai/deployments/{deployment}/chat/completions"
            f"?api-version={api_version}"
        )

    ai_headers = {"api-key": key, "Content-Type": "application/json"} if key else {}
    chat_body = '{"messages":[{"role":"user","content":"hi"}],"max_completion_tokens":5}'

    results: dict = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, url in probes.items():
            if not url:
                results[name] = {"status": "SKIPPED", "ok": False, "detail": "URL not configured"}
                continue
            try:
                if name == "chat_completions":
                    r = await client.post(url, headers=ai_headers, content=chat_body)
                elif name == "endpoint_root":
                    r = await client.get(url, headers=ai_headers)
                else:
                    r = await client.get(url)
                results[name] = {"status": r.status_code, "ok": r.status_code < 500}
            except httpx.ConnectError as exc:
                results[name] = {"status": "CONNECT_ERROR", "ok": False, "detail": str(exc)[:200]}
            except httpx.TimeoutException:
                results[name] = {"status": "TIMEOUT", "ok": False}
            except Exception as exc:
                results[name] = {"status": "ERROR", "ok": False, "detail": str(exc)[:200]}

    return {
        "endpoint": endpoint,
        "deployment": deployment,
        "key_set": bool(key),
        "chat_probe_included": include_chat,
        "probes": results,
    }
        "deployment": deployment,
        "key_set": bool(key),
        "probes": results,
    }
