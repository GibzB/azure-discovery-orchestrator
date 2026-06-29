"""
Smoke tests — no Azure credentials needed.

These run in CI (pipeline test stage) using mocked dependencies so the suite
passes without real keys. They verify the app starts, routes are registered,
and request/response shapes are correct.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ── Patch Azure SDKs before importing the app ────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create a TestClient with all Azure SDK calls mocked out."""

    # Mock MCPClientManager so startup doesn't try to connect to real MCP servers
    mock_mcp = MagicMock()
    mock_mcp.all_tools_for_openai.return_value = []
    mock_mcp.start = AsyncMock()
    mock_mcp.close = AsyncMock()

    # Mock ConversationService
    mock_svc = MagicMock()
    mock_svc.get_or_create_session = MagicMock(return_value=MagicMock(
        session_id="test-session",
        history=[],
        turn=1,
        status=MagicMock(value="active"),
        max_turns=20,
    ))

    with patch("app.mcp.client.MCPClientManager", return_value=mock_mcp), \
         patch("app.api.deps.set_conversation_service"), \
         patch("app.api.deps.get_conversation_service", return_value=mock_svc):
        from app.main import app
        with TestClient(app) as c:
            yield c


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert "mcp_tools_available" in body


# ── Chat ──────────────────────────────────────────────────────────────────────

def test_chat_empty_message_rejected(client):
    """Blank message should return 422."""
    res = client.post("/api/v1/chat/", json={"session_id": "s1", "message": "   "})
    assert res.status_code == 422


def test_chat_missing_fields_rejected(client):
    """Missing session_id should return 422."""
    res = client.post("/api/v1/chat/", json={"message": "hello"})
    assert res.status_code == 422


def test_chat_response_shape(client):
    """A valid chat request returns the expected response shape."""
    with patch("app.api.routes.chat.CosmosService"), \
         patch("app.api.routes.chat.get_conversation_service") as mock_dep:

        mock_session = MagicMock()
        mock_session.history = []
        mock_session.turn = 0
        mock_session.max_turns = 20
        mock_session.status = MagicMock(value="active")

        mock_svc = MagicMock()
        mock_svc.get_or_create_session.return_value = mock_session
        mock_svc._agent.run = AsyncMock(return_value="What industry is your company in?")
        mock_dep.return_value = mock_svc

        res = client.post("/api/v1/chat/", json={"session_id": "test-123", "message": "Hello"})
        assert res.status_code == 200
        body = res.json()
        assert "response" in body
        assert "session_id" in body
        assert "turn" in body
        assert "is_final" in body


# ── Sessions ──────────────────────────────────────────────────────────────────

def test_get_session_not_found(client):
    """Non-existent session should return 404."""
    with patch("app.api.routes.sessions.CosmosService") as mock_cosmos_cls:
        mock_cosmos = AsyncMock()
        mock_cosmos.get_session = AsyncMock(return_value=None)
        mock_cosmos_cls.return_value = mock_cosmos

        res = client.get("/api/v1/sessions/nonexistent-id")
        assert res.status_code == 404


def test_get_session_found(client):
    """Existing session returns the document without Cosmos internal fields."""
    fake_session = {
        "id": "abc123",
        "sessionId": "abc123",
        "turn": 5,
        "status": "active",
        "_rid": "should-be-stripped",
        "_ts": 12345,
    }
    with patch("app.api.routes.sessions.CosmosService") as mock_cosmos_cls:
        mock_cosmos = AsyncMock()
        mock_cosmos.get_session = AsyncMock(return_value=fake_session)
        mock_cosmos_cls.return_value = mock_cosmos

        res = client.get("/api/v1/sessions/abc123")
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == "abc123"
        assert "_rid" not in body
        assert "_ts" not in body


# ── Reports ───────────────────────────────────────────────────────────────────

def test_generate_report_session_not_found(client):
    """Generating a report for a missing session should return 404."""
    with patch("app.api.routes.reports._get_cosmos") as mock_cosmos_fn:
        mock_cosmos = AsyncMock()
        mock_cosmos.get_session = AsyncMock(return_value=None)
        mock_cosmos_fn.return_value = mock_cosmos

        res = client.post("/api/v1/reports/no-such-session/generate")
        assert res.status_code == 404


def test_generate_report_returns_markdown(client):
    """Successful report generation returns non-empty markdown text."""
    fake_session = {
        "id": "sess-1",
        "sessionId": "sess-1",
        "history": [
            {"role": "user", "content": "We are a healthcare startup."},
            {"role": "assistant", "content": "What compliance frameworks do you need?"},
        ],
    }
    with patch("app.api.routes.reports._get_cosmos") as mock_cosmos_fn, \
         patch("app.api.routes.reports._report_agent") as mock_agent:

        mock_cosmos = AsyncMock()
        mock_cosmos.get_session = AsyncMock(return_value=fake_session)
        mock_cosmos.upsert_session = AsyncMock(return_value=fake_session)
        mock_cosmos_fn.return_value = mock_cosmos

        mock_agent.run = AsyncMock(return_value="# Azure Architecture Discovery Report\n\nExecutive Summary...")

        res = client.post("/api/v1/reports/sess-1/generate")
        assert res.status_code == 200
        assert "Azure Architecture" in res.text


# ── Voice REST ────────────────────────────────────────────────────────────────

def test_voice_status(client):
    """Voice status endpoint returns session metadata."""
    with patch("app.api.routes.voice.get_conversation_service") as mock_dep:
        mock_svc = MagicMock()
        mock_svc.get_or_create_session.return_value = MagicMock(
            status=MagicMock(value="active"),
            turn=3,
            max_turns=20,
        )
        mock_dep.return_value = mock_svc

        res = client.get("/api/v1/voice/status/my-session")
        assert res.status_code == 200
        body = res.json()
        assert body["session_id"] == "my-session"
        assert "status" in body
        assert "turn" in body
