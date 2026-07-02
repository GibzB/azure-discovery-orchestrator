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

Implementation note
-------------------
Uses AsyncAzureOpenAI with the AIServices cognitiveservices endpoint
(NOT the legacy *.openai.azure.com endpoint) which IS reachable from
Italy North Container Apps.

Auth priority:
  1. In Container Apps: ManagedIdentityCredential (system-assigned identity)
     — requires AZURE_OPENAI_KEY to be empty/unset
  2. Local dev: DefaultAzureCredential (picks up `az login`)
  3. Fallback: API key from AZURE_OPENAI_KEY (for local dev with a key)

Reasoning model handling:
  gpt-oss-120b is a reasoning model. It emits a `reasoning_content` field
  and often returns empty `content` when max_completion_tokens is too low.
  We use max_completion_tokens=2000 (generous budget) and fall back to
  extracting the last sentence of reasoning_content when content is empty.
"""

import json
import logging
from pathlib import Path
from typing import Any

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


def _get_endpoint() -> str:
    """
    Return the Azure OpenAI / AIServices endpoint.
    Prefers AZURE_FOUNDRY_ENDPOINT, falls back to AZURE_OPENAI_ENDPOINT.
    Trailing slash is stripped — the AsyncAzureOpenAI SDK adds /openai/ itself.
    """
    ep = settings.AZURE_FOUNDRY_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT
    if not ep:
        raise ValueError(
            "Neither AZURE_FOUNDRY_ENDPOINT nor AZURE_OPENAI_ENDPOINT is configured. "
            "Set AZURE_FOUNDRY_ENDPOINT=https://<resource>.cognitiveservices.azure.com/"
        )
    # Strip trailing slash — AsyncAzureOpenAI appends /openai/ automatically.
    # A trailing slash would create a double-slash path that returns 404.
    return ep.rstrip("/")


def _build_client():
    """
    Build an AsyncAzureOpenAI client.

    Note: The gpt-oss-120b model (OpenAI-OSS format) on Azure AIServices does
    NOT support Azure AD / bearer token auth — only API key auth is supported.
    The AZURE_OPENAI_KEY is always required for inference.

    If the key is not set, we attempt managed identity as a best-effort fallback
    (may work for standard Azure OpenAI deployments on the same resource).
    """
    from openai import AsyncAzureOpenAI

    endpoint = _get_endpoint()
    api_version = settings.AZURE_OPENAI_API_VERSION

    if settings.AZURE_OPENAI_KEY:
        logger.info("[OrchestratorAgent] Using API key auth")
        return AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=api_version,
        )

    # Fallback to managed identity (works for standard Azure OpenAI deployments).
    # For gpt-oss-120b (OpenAI-OSS), the key must be provided.
    logger.warning(
        "[OrchestratorAgent] AZURE_OPENAI_KEY is empty — attempting managed identity auth. "
        "Note: gpt-oss-120b (OpenAI-OSS) may not support bearer token auth."
    )
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    return AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version,
    )


def _extract_reply_from_message(message) -> str:
    """
    Extract text content from a chat completion message.

    gpt-oss-120b (reasoning model) sometimes returns empty `content` with the
    actual answer buried in `reasoning_content`. When that happens we extract
    the last sentence of the reasoning as a reasonable spoken response.
    """
    content = (message.content or "").strip()
    if content:
        return content

    # Fallback: extract from reasoning_content
    reasoning = getattr(message, "reasoning_content", None) or ""
    reasoning = reasoning.strip()
    if reasoning:
        logger.warning(
            "[OrchestratorAgent] content empty — extracting summary from reasoning_content (%d chars)",
            len(reasoning),
        )
        sentences = [s.strip() for s in reasoning.replace("\n", " ").split(".") if s.strip()]
        return (sentences[-1] + ".") if sentences else ""

    return ""


class OrchestratorAgent:
    """
    Stateful agent that maintains a per-session message history and
    uses AsyncAzureOpenAI (AIServices endpoint) with MCP tool-calling
    to drive the discovery conversation.
    """

    name = "orchestrator"

    def __init__(self, mcp: MCPClientManager | None = None) -> None:
        self._client = None  # lazy — built on first use so env vars are fully loaded
        self._mcp = mcp
        self._system_prompt = _load_system_prompt()

    def _get_client(self):
        """Lazily build the OpenAI client on first use."""
        if self._client is None:
            self._client = _build_client()
        return self._client

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
            context:     Optional metadata (session_id, phase, etc.) — kept for
                         API compatibility but not used internally.
            history:     Full conversation history (mutated in-place with new messages).

        Returns:
            Plain-text response to be spoken via TTS.
        """
        if history is None:
            history = []

        # Prepend system prompt on first turn
        messages: list[dict] = (
            [{"role": "system", "content": self._system_prompt}] + history
            if not any(m.get("role") == "system" for m in history)
            else list(history)
        )

        messages.append({"role": "user", "content": user_input})

        tools = self._mcp.all_tools_for_openai() if self._mcp else []

        # ── Agentic loop: keep calling until no more tool_calls ───────────────
        max_rounds = 5
        client = self._get_client()
        for round_num in range(max_rounds):
            kwargs: dict[str, Any] = {
                "model": settings.AZURE_OPENAI_DEPLOYMENT,
                "messages": messages,
                "temperature": 0.4,
                # gpt-oss-120b is a reasoning model.
                # Use max_completion_tokens only (includes reasoning tokens).
                # A budget of 2000 is sufficient for short spoken responses.
                "max_completion_tokens": 2000,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            # Serialise the message for history storage (handles tool_calls)
            msg_dict = choice.message.model_dump(exclude_none=True)
            messages.append(msg_dict)

            if choice.finish_reason == "tool_calls" and self._mcp:
                await process_tool_calls(choice.message.tool_calls, messages, self._mcp)
                continue  # go round again with tool results

            reply = _extract_reply_from_message(choice.message)

            if not reply:
                logger.warning(
                    "[OrchestratorAgent] No reply extracted "
                    "(finish_reason=%s, round=%d) — using fallback",
                    choice.finish_reason,
                    round_num,
                )
                reply = "Could you tell me more about your requirements?"

            # Update caller's history slice (drop system prompt from stored history)
            history.clear()
            history.extend(m for m in messages[1:] if isinstance(m, dict))
            return reply

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
