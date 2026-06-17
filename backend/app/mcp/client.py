"""
MCP Client Manager

Manages connections to two MCP servers:
  1. Microsoft Learn MCP  (HTTP/SSE — remote, no auth needed)
     Tools: microsoft_docs_search, microsoft_docs_fetch, microsoft_code_sample_search
  2. Azure MCP Server     (stdio — local process, uses Azure credential chain)
     Tools: 26+ Azure resource management tools

Usage:
    async with MCPClientManager() as manager:
        tools = manager.all_tools_for_openai()
        result = await manager.call_tool("microsoft_docs_search", {"query": "..."})
"""

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)

# ── Server configs ────────────────────────────────────────────────────────────

LEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"

AZURE_MCP_PARAMS = StdioServerParameters(
    command="azmcp",
    args=["server", "start"],
    env=None,  # inherits process env — Azure CLI / DefaultAzureCredential chain
)


class MCPClientManager:
    """
    Holds active sessions for both MCP servers and provides a unified
    tool-call interface for the orchestrator agents.
    """

    def __init__(self) -> None:
        self._learn_session: ClientSession | None = None
        self._azure_session: ClientSession | None = None
        self._learn_tools: list[dict] = []
        self._azure_tools: list[dict] = []
        self._tool_server_map: dict[str, str] = {}  # tool_name → "learn" | "azure"

        # Context manager handles (kept alive for session duration)
        self._learn_ctx = None
        self._azure_ctx = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Connect to both MCP servers and enumerate tools."""
        await self._connect_learn()
        await self._connect_azure()
        logger.info(
            "MCP ready — Learn tools: %d, Azure tools: %d",
            len(self._learn_tools),
            len(self._azure_tools),
        )

    async def _connect_learn(self) -> None:
        try:
            self._learn_ctx = sse_client(LEARN_MCP_URL)
            read, write = await self._learn_ctx.__aenter__()
            self._learn_session = ClientSession(read, write)
            await self._learn_session.__aenter__()
            await self._learn_session.initialize()
            tools = await self._learn_session.list_tools()
            self._learn_tools = self._format_tools(tools.tools)
            for t in tools.tools:
                self._tool_server_map[t.name] = "learn"
            logger.info("Learn MCP connected: %s", [t.name for t in tools.tools])
        except Exception as exc:
            logger.warning("Learn MCP unavailable (continuing without it): %s", exc)
            self._learn_session = None

    async def _connect_azure(self) -> None:
        try:
            self._azure_ctx = stdio_client(AZURE_MCP_PARAMS)
            read, write = await self._azure_ctx.__aenter__()
            self._azure_session = ClientSession(read, write)
            await self._azure_session.__aenter__()
            await self._azure_session.initialize()
            tools = await self._azure_session.list_tools()
            self._azure_tools = self._format_tools(tools.tools)
            for t in tools.tools:
                self._tool_server_map[t.name] = "azure"
            logger.info("Azure MCP connected: %d tools", len(tools.tools))
        except Exception as exc:
            logger.warning("Azure MCP unavailable (continuing without it): %s", exc)
            self._azure_session = None

    async def close(self) -> None:
        if self._learn_session:
            await self._learn_session.__aexit__(None, None, None)
        if self._azure_session:
            await self._azure_session.__aexit__(None, None, None)
        if self._learn_ctx:
            await self._learn_ctx.__aexit__(None, None, None)
        if self._azure_ctx:
            await self._azure_ctx.__aexit__(None, None, None)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    # ── Tool access ───────────────────────────────────────────────────────────

    def all_tools_for_openai(self) -> list[dict]:
        """Return all tools in the OpenAI function-calling schema format."""
        return self._learn_tools + self._azure_tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """
        Call a tool by name on the correct MCP server.
        Returns the string content of the result.
        """
        server = self._tool_server_map.get(tool_name)

        if server == "learn" and self._learn_session:
            result = await self._learn_session.call_tool(tool_name, arguments)
        elif server == "azure" and self._azure_session:
            result = await self._azure_session.call_tool(tool_name, arguments)
        else:
            return f"Tool '{tool_name}' not available."

        # Flatten result content to a single string
        parts = []
        for item in result.content:
            if hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(json.dumps(item, default=str))
        return "\n".join(parts)

    # ── Helpers ───────────────────────────────────────────────────────────────

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
