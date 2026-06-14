"""
MCP Tool Handler

Processes tool_call arrays returned by GPT-4o and appends
the results back into the messages list for the next completion round.
"""

import json
import logging
from typing import Any

from app.mcp.client import MCPClientManager

logger = logging.getLogger(__name__)


async def process_tool_calls(
    tool_calls: list,
    messages: list[dict],
    mcp: MCPClientManager,
) -> None:
    """
    For each tool_call from the model:
      1. Call the appropriate MCP server
      2. Append a 'tool' role message with the result

    Mutates `messages` in-place.
    """
    for tool_call in tool_calls:
        name = tool_call.function.name
        try:
            args: dict[str, Any] = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}

        logger.info("MCP tool call: %s(%s)", name, args)

        try:
            result = await mcp.call_tool(name, args)
        except Exception as exc:
            result = f"Error calling tool '{name}': {exc}"
            logger.error(result)

        messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": name,
                "content": result,
            }
        )
