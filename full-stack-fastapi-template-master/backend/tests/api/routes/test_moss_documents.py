from fastapi.testclient import TestClient

from app.core.config import settings


def test_upload_text_document_returns_block_html(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/moss/documents/upload",
        headers=superuser_token_headers,
        files={"file": ("draft.txt", b"First paragraph\n\nSecond paragraph", "text/plain")},
    )

    assert response.status_code == 200
    content = response.json()
    assert content["filename"] == "draft.txt"
    assert content["textContent"] == "First paragraph\n\nSecond paragraph"
    assert 'id="moss-block-' in content["htmlContent"]
    assert "<p>First paragraph</p>" in content["htmlContent"]


def test_export_markdown_document(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/moss/documents/export",
        headers=superuser_token_headers,
        json={
            "format": "markdown",
            "filename": "brief",
            "content": "<h1>Brief</h1><p>Body copy.</p>",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert 'filename="brief.md"' in response.headers["content-disposition"]
    assert "# Brief" in response.text
    assert "Body copy." in response.text


def test_save_moss_document_writes_html_and_metadata(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "MOSS_STORAGE_DIR", str(tmp_path))

    response = client.post(
        f"{settings.API_V1_STR}/moss/documents/save",
        headers=superuser_token_headers,
        json={"docId": "current-doc", "content": "<p>Saved content</p>"},
    )

    assert response.status_code == 200
    assert response.json()["docId"] == "current-doc"
    assert (tmp_path / "documents" / "current-doc.html").read_text(
        encoding="utf-8"
    ) == "<p>Saved content</p>"
    assert '"docId": "current-doc"' in (tmp_path / "documents" / "current-doc.json").read_text(
        encoding="utf-8"
    )
