from fastapi.testclient import TestClient

from app.core.config import settings


def test_moss_agent_chat_stream_returns_sse_chat_chunk(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = client.post(
        f"{settings.API_V1_STR}/moss/notes/",
        headers=superuser_token_headers,
    ).json()

    response = client.post(
        f"{settings.API_V1_STR}/moss/agent/chat-stream",
        headers=superuser_token_headers,
        json={
            "note_id": created["note_id"],
            "conversation_id": created["default_conversation_id"],
            "user_input": "Summarize this",
            "canvas_snapshot": "<p id=\"moss-block-a\">Hello Moss</p>",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: chat_chunk" in response.text
    assert "Mock Moss response" in response.text
    assert "event: done" in response.text
