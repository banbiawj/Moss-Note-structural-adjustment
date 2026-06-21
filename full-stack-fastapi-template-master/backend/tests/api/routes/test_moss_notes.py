import uuid

from fastapi.testclient import TestClient

from app.core.config import settings


def test_create_moss_note_creates_default_conversation(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/moss/notes/",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    note_id = uuid.UUID(content["note_id"])
    conversation_id = uuid.UUID(content["default_conversation_id"])
    assert note_id
    assert conversation_id
    assert content["active_conversation_id"] == content["default_conversation_id"]
    assert content["effective_title"] == "Untitled note"
    assert content["preview_text"] == ""


def test_moss_note_snapshot_updates_title_and_preview(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = client.post(
        f"{settings.API_V1_STR}/moss/notes/",
        headers=superuser_token_headers,
    ).json()

    response = client.put(
        f"{settings.API_V1_STR}/moss/notes/{created['note_id']}/snapshot",
        headers=superuser_token_headers,
        json={"canvas_snapshot": "<h1>Project Brief</h1><p>First paragraph for Moss.</p>"},
    )

    assert response.status_code == 200
    content = response.json()
    assert content["note_id"] == created["note_id"]
    assert content["title"] == "Project Brief"
    assert content["preview_text"] == "Project Brief First paragraph for Moss."


def test_list_moss_note_conversations(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = client.post(
        f"{settings.API_V1_STR}/moss/notes/",
        headers=superuser_token_headers,
    ).json()

    response = client.get(
        f"{settings.API_V1_STR}/moss/notes/{created['note_id']}/conversations",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["active_conversation_id"] == created["default_conversation_id"]
    assert len(content["conversations"]) == 1
    assert content["conversations"][0]["conversation_id"] == created["default_conversation_id"]
    assert content["conversations"][0]["title"] == "Default conversation"


def test_create_moss_note_conversation_makes_it_active(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = client.post(
        f"{settings.API_V1_STR}/moss/notes/",
        headers=superuser_token_headers,
    ).json()

    conversation_response = client.post(
        f"{settings.API_V1_STR}/moss/notes/{created['note_id']}/conversations",
        headers=superuser_token_headers,
    )
    assert conversation_response.status_code == 200
    conversation = conversation_response.json()

    list_response = client.get(
        f"{settings.API_V1_STR}/moss/notes/{created['note_id']}/conversations",
        headers=superuser_token_headers,
    )
    assert list_response.status_code == 200
    content = list_response.json()
    assert content["active_conversation_id"] == conversation["conversation_id"]
