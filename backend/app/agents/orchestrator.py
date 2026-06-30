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
This module uses the **azure-ai-agents** SDK (AgentsClient) backed by an
AIServices endpoint with DefaultAzureCredential.  In Azure Container Apps the
credential resolves automatically to the system-assigned managed identity;
locally it falls back through az login / env vars.

Using AgentsClient instead of raw AsyncAzureOpenAI solves two problems seen
in the Italy North region:
  1. Network routing — the Cognitive Services data plane IS reachable, while
     *.openai.azure.com was not from the Container App.
  2. Reasoning model (gpt-oss-120b) empty content — the agents thread API
     extracts the final answer after reasoning completes, no max_tokens tuning.
"""

import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.mcp.client import MCPClientManager

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


def _get_foundry_endpoint() -> str:
    """Return the AI Services endpoint, preferring AZURE_FOUNDRY_ENDPOINT."""
    ep = settings.AZURE_FOUNDRY_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT
    if not ep:
        raise ValueError(
            "Neither AZURE_FOUNDRY_ENDPOINT nor AZURE_OPENAI_ENDPOINT is set. "
            "Set AZURE_FOUNDRY_ENDPOINT=https://<resource>.cognitiveservices.azure.com/"
        )
    return ep.rstrip("/") + "/"


def _build_credential():
    """
    Return an Azure credential appropriate for the current environment.

    - Container Apps with managed identity → DefaultAzureCredential picks up
      the IDENTITY_ENDPOINT / IDENTITY_HEADER env vars automatically.
    - Local dev with `az login` → DefaultAzureCredential falls through to
      AzureCliCredential.
    - Local dev with a key → we still use DefaultAzureCredential so the code
      path is identical; the key is used by report_agent which still uses the
      raw SDK.
    """
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential()


class OrchestratorAgent:
    """
    Stateful agent backed by azure-ai-agents AgentsClient.

    Each session gets its own Agents thread so conversation history is
    managed server-side. In-memory history is also kept for compatibility
    with callers that pass and mutate the history list (e.g. ConversationService
    and the voice pipeline).
    """

    name = "orchestrator"

    def __init__(self, mcp: MCPClientManager | None = None) -> None:
        from azure.ai.agents import AgentsClient

        endpoint = _get_foundry_endpoint()
        credential = _build_credential()

        self._client = AgentsClient(endpoint=endpoint, credential=credential)
        self._mcp = mcp
        self._system_prompt = _load_system_prompt()

        # Lazily-created persistent agent (one per process).
        self._agent_id: str | None = None
        # session_id → Agents thread_id mapping (in-memory; survives the
        # Container App instance lifetime and is also persisted in Cosmos via
        # the chat route).
        self._thread_map: dict[str, str] = {}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _ensure_agent(self) -> str:
        """Create the Agents API agent if it does not exist yet."""
        if self._agent_id:
            return self._agent_id

        agent = self._client.create_agent(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            name="discovery-orchestrator",
            instructions=self._system_prompt,
        )
        self._agent_id = agent.id
        logger.info("[OrchestratorAgent] Created Agents agent id=%s", agent.id)
        return agent.id

    def _get_or_create_thread(self, session_id: str) -> str:
        """Return the thread_id for a session, creating a new one if needed."""
        if session_id not in self._thread_map:
            thread = self._client.create_thread()
            self._thread_map[session_id] = thread.id
            logger.info(
                "[OrchestratorAgent] Created thread id=%s for session=%s",
                thread.id,
                session_id,
            )
        return self._thread_map[session_id]

    def _extract_reply(self, thread_id: str) -> str:
        """Pull the latest assistant message from the thread."""
        messages = self._client.list_messages(thread_id=thread_id)
        # get_last_text_message_by_role returns the most recent assistant msg
        last = messages.get_last_text_message_by_role("assistant")
        if last:
            return (last.text.value or "").strip()
        return ""

    # ── Public API ────────────────────────────────────────────────────────────

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
            history:     Conversation history list (kept for compatibility;
                         the Agents API manages server-side state).

        Returns:
            Plain-text response to be spoken via TTS.
        """
        if history is None:
            history = []

        # Derive a stable session identifier.  Fall back to a hash of the
        # current history length so callers that don't pass context still get
        # thread isolation per agent instance.
        session_id: str = (context or {}).get("session_id", f"anon-{id(history)}")

        try:
            agent_id = self._ensure_agent()
            thread_id = self._get_or_create_thread(session_id)

            # Post the user message to the thread
            self._client.create_message(
                thread_id=thread_id,
                role="user",
                content=user_input,
            )

            # Run the agent and wait for completion (handles tool-call loop internally)
            run = self._client.create_and_process_run(
                thread_id=thread_id,
                agent_id=agent_id,
            )
            logger.debug(
                "[OrchestratorAgent] run id=%s status=%s session=%s",
                run.id,
                run.status,
                session_id,
            )

            reply = self._extract_reply(thread_id)

            if not reply:
                logger.warning(
                    "[OrchestratorAgent] Empty reply from Agents API "
                    "(run_id=%s, status=%s) — using fallback",
                    run.id,
                    run.status,
                )
                reply = "Could you tell me more about your requirements?"

            # Keep history in sync for callers that read it
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": reply})

            return reply

        except Exception as exc:
            logger.error(
                "[OrchestratorAgent] Agents API call failed: %s",
                exc,
                exc_info=True,
            )
            raise

    async def opening_message(self) -> str:
        """
        Generate the very first spoken greeting to kick off the discovery session.
        Called once when the voice session starts — no user input yet.
        """
        return await self.run(
            user_input="[SESSION_START]",
            context={"session_id": "opening"},
            history=[],
        )
