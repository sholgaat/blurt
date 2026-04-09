from fastapi.testclient import TestClient
import pytest

from backend import main
from backend.llm import LlmError


@pytest.fixture
def client():
    return TestClient(main.app)


def test_create_idea_success(monkeypatch, client):
    async def fake_cleanup(raw_text: str):
        return {"title": "AI Title", "summary": "AI Summary", "tags": ["dev"]}

    async def fake_create_issue(**kwargs):
        return "https://example.com/issue/123"

    monkeypatch.setattr(main, "get_backend_settings", lambda: type("Cfg", (), {"dry_run": False})())
    monkeypatch.setattr(main, "call_ai_cleanup", fake_cleanup)
    monkeypatch.setattr(main, "create_issue", fake_create_issue)

    response = client.post(
        "/ideas",
        json={"text": "idea: build something", "user_id": "1", "source": "discord"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "title": "AI Title",
        "summary": "AI Summary",
        "tags": ["dev"],
        "url": "https://example.com/issue/123",
    }


def test_create_idea_dry_run_prepends_nudge(monkeypatch, client):
    async def fake_cleanup(raw_text: str):
        return {"title": "AI Title", "summary": "AI Summary", "tags": ["dev"]}

    async def fake_create_issue(**kwargs):
        return "https://example.com/dry-run-issue"

    monkeypatch.setattr(main, "get_backend_settings", lambda: type("Cfg", (), {"dry_run": True})())
    monkeypatch.setattr(main, "call_ai_cleanup", fake_cleanup)
    monkeypatch.setattr(main, "create_issue", fake_create_issue)

    response = client.post(
        "/ideas",
        json={"text": "idea: build something", "user_id": "1", "source": "discord"},
    )

    assert response.status_code == 200
    assert response.json()["summary"].startswith(
        "Dry run worked. Set DRY_RUN=false in .env.backend and restart the backend to go live."
    )
    assert response.json()["summary"].endswith("AI Summary")


def test_create_idea_llm_failure(monkeypatch, client):
    async def failing_cleanup(raw_text: str):
        raise LlmError("llm down")

    monkeypatch.setattr(main, "call_ai_cleanup", failing_cleanup)

    response = client.post(
        "/ideas",
        json={"text": "idea text", "user_id": "1", "source": "discord"},
    )

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


def test_create_idea_github_failure(monkeypatch, client):
    async def fake_cleanup(raw_text: str):
        return {"title": "T", "summary": "S", "tags": ["dev"]}

    async def failing_issue(**kwargs):
        raise RuntimeError("github down")

    monkeypatch.setattr(main, "call_ai_cleanup", fake_cleanup)
    monkeypatch.setattr(main, "create_issue", failing_issue)

    response = client.post(
        "/ideas",
        json={"text": "idea text", "user_id": "1", "source": "discord"},
    )

    assert response.status_code == 502
    assert "Failed to create GitHub issue" in response.json()["detail"]
