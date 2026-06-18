"""
MCP Client Manager

Manages connections to two MCP servers:
  1. Microsoft Learn MCP  (HTTP/SSE — remote, no auth needed)
  2. Azure MCP Server     (stdio — local process, uses Azure credential chain)

Both connections are non-fatal — the app starts and serves requests even if
MCP is unavailable. MCP is connected in a background task after startup.
"""

import asyncio
import json
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)

LEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"

AZURE_MCP_PARAMS = StdioServerParameters(
    command="azmcp",
    args=["server", "start"],
    env=None,
)

_CONNECT_TIMEOUT = 15.0


class MCPClientManager:
    def __init__(self) -> None:
        self._learn_session: ClientSession | None = None
        self._azure_session: ClientSession | None = None
        self._learn_tools: list[dict] = []
        self._azure_tools: list[dict] = []
        self._tool_server_map: dict[str, str] = {}
        self._learn_ctx = None
        self._azure_ctx = None

    async def start(self) -> None:
        await self._connect_learn()
        await self._connect_azure()
        logger.info(
            "MCP ready — Learn: %d tools, Azure: %d tools",
            len(self._learn_tools),
            len(self._azure_tools),
        )

    async def _connect_learn(self) -> None:
        try:
            ctx = sse_client(LEARN_MCP_URL)
            read, write = await asyncio.wait_for(ctx.__aenter__(), timeout=_CONNECT_TIMEOUT)
            self._learn_ctx = ctx
            session = ClientSession(read, write)
            await session.__aenter__()
            await asyncio.wait_for(session.initialize(), timeout=_CONNECT_TIMEOUT)
            tools = await asyncio.wait_for(session.list_tools(), timeout=_CONNECT_TIMEOUT)
            self._learn_session = session
            self._learn_tools = self._format_tools(tools.tools)
            for t in tools.tools:
                self._tool_server_map[t.name] = "learn"
            logger.info("Learn MCP connected: %s", [t.name for t in tools.tools])
        except Exception as exc:
            logger.warning("Learn MCP unavailable: %s", exc)
            self._learn_session = None
            self._learn_ctx = None

    async def _connect_azure(self) -> None:
        try:
            ctx = stdio_client(AZURE_MCP_PARAMS)
            read, write = await asyncio.wait_for(ctx.__aenter__(), timeout=_CONNECT_TIMEOUT)
            self._azure_ctx = ctx
            session = ClientSession(read, write)
            await session.__aenter__()
            await asyncio.wait_for(session.initialize(), timeout=_CONNECT_TIMEOUT)
            tools = await asyncio.wait_for(session.list_tools(), timeout=_CONNECT_TIMEOUT)
            self._azure_session = session
            self._azure_tools = self._format_tools(tools.tools)
            for t in tools.tools:
                self._tool_server_map[t.name] = "azure"
            logger.info("Azure MCP connected: %d tools", len(tools.tools))
        except Exception as exc:
            logger.warning("Azure MCP unavailable: %s", exc)
            self._azure_session = None
            self._azure_ctx = None

    async def close(self) -> None:
        for session in [self._learn_session, self._azure_session]:
            if session:
                try:
                    await session.__aexit__(None, None, None)
                except Exception:
                    pass
        for ctx in [self._learn_ctx, self._azure_ctx]:
            if ctx:
                try:
                    await ctx.__aexit__(None, None, None)
                except Exception:
                    pass

    def all_tools_for_openai(self) -> list[dict]:
        return self._learn_tools + self._azure_tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        server = self._tool_server_map.get(tool_name)
        if server == "learn" and self._learn_session:
            result = await self._learn_session.call_tool(tool_name, arguments)
        elif server == "azure" and self._azure_session:
            result = await self._azure_session.call_tool(tool_name, arguments)
        else:
            return f"Tool '{tool_name}' not available."
        parts = []
        for item in result.content:
            if hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(json.dumps(item, default=str))
        return "\n".join(parts)

    @staticmethod
    def _format_tools(tools) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema or {"type": "object", "properties": {}},
                },
            }
            for t in tools
        ]
