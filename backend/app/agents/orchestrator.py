"""
Orchestrator Agent

Drives a structured, one-on-one discovery conversation with the client.
The agent:
  - Asks probing questions across business, technical, and compliance domains
  - Uses Microsoft Learn MCP to pull live Azure docs when recommending services
  - Uses Azure MCP to inspect the client's existing Azure environment (optional)
  - Maintains a question progress tracker so it never repeats itself
  - Returns a plain-text response intended to be spoken via TTS

Discovery question flow (order may adapt based on answers):
  Phase 1 — Business context     (3-4 questions)
  Phase 2 — Technical workloads  (3-4 questions)
  Phase 3 — Compliance & security(2-3 questions)
  Phase 4 — Growth & future      (2 questions)
  Phase 5 — Recommendation       (summarise + architecture sketch)
"""

import json
import logging
from pathlib import Path
from typing import Any

from azure.identity import ManagedIdentityCredential
from openai import AsyncAzureOpenAI

from app.core.config import settings
from app.mcp.client import MCPClientManager
from app.mcp.tool_handler import process_tool_calls

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "orchestrator.md"


def _load_system_prompt() -> str:
    try:
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return FALLBACK_SYSTEM_PROMPT


FALLBACK_SYSTEM_PROMPT = """
You are the Azure Discovery Orchestrator — a senior Azure Solutions Architect 
conducting a one-on-one discovery workshop with a client via voice conversation.

## Conversation style
- Speak naturally, as if in a real meeting. No bullet points or markdown in responses 
  (they will be read aloud by a text-to-speech engine).
- Ask ONE focused question at a time. Wait for the answer before moving on.
- Acknowledge the client's answer briefly before asking the next question.
- Never ask about something the client already answered.

## Discovery phases
Work through these phases in order, adapting based on answers:
1. Business context: industry, size, current infrastructure, key drivers for Azure
2. Technical workloads: applications, data volumes, integrations, latency requirements
3. Compliance & security: regulatory frameworks, data residency, identity requirements
4. Growth & future: scale projections, planned new workloads
5. Recommendation: summarise findings and sketch an Azure architecture recommendation

## Tool use
- Use microsoft_docs_search to verify service capabilities before recommending them.
- Use microsoft_docs_fetch to get specific pricing or SLA details when the client asks.
- Use Azure MCP tools only if the client grants permission to inspect their environment.

## Rules
- Never hallucinate Azure service features or limits.
- Keep each spoken response under 60 words so it sounds natural when read aloud.
- End every response (except the final recommendation) with a clear question.
""".strip()


class OrchestratorAgent:
    """
    Stateful agent that maintains a per-session message history and
    uses GPT-4o with MCP tool-calling to drive the discovery conversation.
    """

    name = "orchestrator"

    def __init__(self, mcp: MCPClientManager | None = None) -> None:
        # Use managed identity when no key is set (running in Azure Container Apps).
        # Fall back to key auth for local development when AZURE_OPENAI_KEY is set.
        if settings.AZURE_OPENAI_KEY:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )
        else:
            from azure.identity import get_bearer_token_provider
            credential = ManagedIdentityCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_ad_token_provider=token_provider,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )
        self._mcp = mcp
        self._system_prompt = _load_system_prompt()

    async def run(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
        history: list[dict] | None = None,
    ) -> str:
        """
        Process a single user turn and return the assistant's spoken response.

        Args:
            user_input:  Transcribed speech (or typed text) from the client.
            context:     Optional metadata (session_id, phase, etc.).
            history:     Full conversation history (mutated in-place with new messages).

        Returns:
            Plain-text response to be spoken via TTS.
        """
        if history is None:
            history = []

        # Prepend system prompt on first turn
        messages: list[dict] = (
            [{"role": "system", "content": self._system_prompt}] + history
            if not any(m["role"] == "system" for m in history)
            else history
        )

        messages.append({"role": "user", "content": user_input})

        tools = self._mcp.all_tools_for_openai() if self._mcp else []

        # ── Agentic loop: keep calling until no more tool_calls ───────────────
        max_rounds = 5
        for round_num in range(max_rounds):
            kwargs: dict[str, Any] = {
                "model": settings.AZURE_OPENAI_DEPLOYMENT,
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": 300,  # keep spoken responses short
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await self._client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            messages.append(choice.message)

            if choice.finish_reason == "tool_calls" and self._mcp:
                await process_tool_calls(choice.message.tool_calls, messages, self._mcp)
                continue  # go round again with tool results

            # Done — extract text
            reply = choice.message.content or ""
            # Update caller's history slice (everything after system prompt)
            history.clear()
            history.extend(messages[1:])  # drop system prompt from stored history
            return reply.strip()

        logger.warning("Orchestrator hit max tool-call rounds (%d)", max_rounds)
        return "I need a moment to gather that information. Could you repeat your last answer?"

    async def opening_message(self) -> str:
        """
        Generate the very first spoken greeting to kick off the discovery session.
        Called once when the voice session starts — no user input yet.
        """
        return await self.run(
            user_input="[SESSION_START]",
            history=[],
        )
