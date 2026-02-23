from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient


def _create_content(client: TestClient, text: str) -> int:
    resp = client.post(
        "/api/content/",
        json={"original_text": text},
    )
    assert resp.status_code == 201
    body = resp.json()
    return body["id"]


def test_generate_linkedin_happy_path(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    # Arrange: content with sufficient length
    content_id = _create_content(
        client,
        "This is a sufficiently long piece of content used for LinkedIn generation tests.",
    )

    def fake_generate(_: str) -> list[dict[str, Any]]:
        return [
            {"title": "Post 1", "body": "Body 1"},
            {"title": "Post 2", "body": "Body 2"},
        ]

    monkeypatch.setattr(
        "app.routers.generate.generate_linkedin_posts_from_text",
        fake_generate,
    )

    # Act
    resp = client.post(f"/api/generate/linkedin/{content_id}")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert data["content_id"] == content_id
    assert isinstance(data["posts"], list)
    assert len(data["posts"]) == 2
    first = data["posts"][0]
    assert {"id", "content_id", "title", "body", "created_at"} <= set(first.keys())
    assert first["body"] == "Body 1"


def test_generate_linkedin_404_missing_content(client: TestClient) -> None:
    resp = client.post("/api/generate/linkedin/999999")
    assert resp.status_code == 404


def test_generate_linkedin_400_too_short(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    content_id = _create_content(client, "short text")

    # Ensure service would be called if not for validation
    def fake_generate(_: str) -> list[dict[str, Any]]:
        raise AssertionError("Service should not be called for too-short content")

    monkeypatch.setattr(
        "app.routers.generate.generate_linkedin_posts_from_text",
        fake_generate,
    )

    resp = client.post(f"/api/generate/linkedin/{content_id}")
    assert resp.status_code == 400


def test_generate_linkedin_422_invalid_id(client: TestClient) -> None:
    resp = client.post("/api/generate/linkedin/not-an-int")
    assert resp.status_code == 422


def test_generate_linkedin_502_service_failure(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content for testing service failure handling in the generate endpoint.",
    )

    def failing_generate(_: str) -> list[dict[str, Any]]:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routers.generate.generate_linkedin_posts_from_text",
        failing_generate,
    )

    resp = client.post(f"/api/generate/linkedin/{content_id}")
    assert resp.status_code == 502


def test_generate_linkedin_500_empty_result(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content that will produce an empty list from the generation service.",
    )

    def empty_generate(_: str) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr(
        "app.routers.generate.generate_linkedin_posts_from_text",
        empty_generate,
    )

    resp = client.post(f"/api/generate/linkedin/{content_id}")
    assert resp.status_code == 500

