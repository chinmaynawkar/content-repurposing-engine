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


def test_generate_twitter_happy_path(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is a sufficiently long piece of content used for Twitter generation tests.",
    )

    def fake_generate(_: str) -> list[dict[str, Any]]:
        return [
            {"title": "Thread 1", "tweets": ["Tweet 1.1", "Tweet 1.2"]},
            {"title": "Thread 2", "tweets": ["Tweet 2.1", "Tweet 2.2"]},
        ]

    monkeypatch.setattr(
        "app.routers.generate.generate_twitter_threads_from_text",
        fake_generate,
    )

    resp = client.post(f"/api/generate/twitter/{content_id}")
    assert resp.status_code == 201
    data = resp.json()
    assert data["content_id"] == content_id
    assert isinstance(data["threads"], list)
    assert len(data["threads"]) == 2
    first = data["threads"][0]
    assert {"id", "content_id", "title", "tweets", "created_at"} <= set(first.keys())
    assert first["tweets"] == ["Tweet 1.1", "Tweet 1.2"]


def test_generate_twitter_404_missing_content(client: TestClient) -> None:
    resp = client.post("/api/generate/twitter/999999")
    assert resp.status_code == 404


def test_generate_twitter_400_too_short(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(client, "short text")

    def fake_generate(_: str) -> list[dict[str, Any]]:
        raise AssertionError("Service should not be called for too-short content")

    monkeypatch.setattr(
        "app.routers.generate.generate_twitter_threads_from_text",
        fake_generate,
    )

    resp = client.post(f"/api/generate/twitter/{content_id}")
    assert resp.status_code == 400


def test_generate_twitter_422_invalid_id(client: TestClient) -> None:
    resp = client.post("/api/generate/twitter/not-an-int")
    assert resp.status_code == 422


def test_generate_twitter_502_service_failure(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content for testing Twitter service failure handling.",
    )

    def failing_generate(_: str) -> list[dict[str, Any]]:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routers.generate.generate_twitter_threads_from_text",
        failing_generate,
    )

    resp = client.post(f"/api/generate/twitter/{content_id}")
    assert resp.status_code == 502


def test_generate_twitter_500_empty_result(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content that will produce an empty list of threads.",
    )

    def empty_generate(_: str) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr(
        "app.routers.generate.generate_twitter_threads_from_text",
        empty_generate,
    )

    resp = client.post(f"/api/generate/twitter/{content_id}")
    assert resp.status_code == 500


def test_generate_instagram_happy_path(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is a sufficiently long piece of content used for Instagram generation tests.",
    )

    def fake_generate(
        _: str,
        *,
        audience: str,
        tone: str,
        goal: str | None = None,
        title: str | None = None,
    ) -> list[dict[str, Any]]:
        assert audience == "creators"
        assert tone == "friendly"
        return [
            {
                "id": 1,
                "style": "short_hook",
                "text": "Caption 1",
                "hashtags": ["#one", "#two"],
                "character_count": 9,
            },
            {
                "id": 2,
                "style": "story",
                "text": "Caption 2",
                "hashtags": ["#three"],
                "character_count": 9,
            },
        ]

    monkeypatch.setattr(
        "app.routers.generate.generate_instagram_captions_from_text",
        fake_generate,
    )

    resp = client.post(
        f"/api/generate/instagram/{content_id}",
        json={"audience": "creators", "tone": "friendly", "goal": "drive saves"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["content_id"] == content_id
    assert isinstance(data["captions"], list)
    assert len(data["captions"]) == 2
    first = data["captions"][0]
    assert {"id", "style", "text", "hashtags", "character_count"} <= set(first.keys())
    assert first["text"] == "Caption 1"


def test_generate_instagram_404_missing_content(client: TestClient) -> None:
    resp = client.post(
        "/api/generate/instagram/999999",
        json={"audience": "creators", "tone": "friendly"},
    )
    assert resp.status_code == 404


def test_generate_instagram_400_too_short(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(client, "short text")

    def fake_generate(
        _: str,
        *,
        audience: str,
        tone: str,
        goal: str | None = None,
        title: str | None = None,
    ) -> list[dict[str, Any]]:
        raise AssertionError("Service should not be called for too-short content")

    monkeypatch.setattr(
        "app.routers.generate.generate_instagram_captions_from_text",
        fake_generate,
    )

    resp = client.post(
        f"/api/generate/instagram/{content_id}",
        json={"audience": "creators", "tone": "friendly"},
    )
    assert resp.status_code == 400


def test_generate_instagram_422_invalid_id(client: TestClient) -> None:
    resp = client.post(
        "/api/generate/instagram/not-an-int",
        json={"audience": "creators", "tone": "friendly"},
    )
    assert resp.status_code == 422


def test_generate_instagram_502_service_failure(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content for testing Instagram service failure handling.",
    )

    def failing_generate(
        _: str,
        *,
        audience: str,
        tone: str,
        goal: str | None = None,
        title: str | None = None,
    ) -> list[dict[str, Any]]:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routers.generate.generate_instagram_captions_from_text",
        failing_generate,
    )

    resp = client.post(
        f"/api/generate/instagram/{content_id}",
        json={"audience": "creators", "tone": "friendly"},
    )
    assert resp.status_code == 502


def test_generate_instagram_500_empty_result(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content that will produce an empty list of Instagram captions.",
    )

    def empty_generate(
        _: str,
        *,
        audience: str,
        tone: str,
        goal: str | None = None,
        title: str | None = None,
    ) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr(
        "app.routers.generate.generate_instagram_captions_from_text",
        empty_generate,
    )

    resp = client.post(
        f"/api/generate/instagram/{content_id}",
        json={"audience": "creators", "tone": "friendly"},
    )
    assert resp.status_code == 500


def test_generate_seo_happy_path(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is a sufficiently long piece of content used for SEO meta generation tests.",
    )

    def fake_generate(
        _: str,
        *,
        title: str | None,
        primary_keyword: str,
        search_intent: str,
        tone: str | None = None,
    ) -> list[dict[str, Any]]:
        assert primary_keyword == "productivity tips"
        assert search_intent == "informational"
        assert tone == "friendly"
        return [
            {
                "id": 1,
                "description": "First SEO meta description about productivity tips.",
                "character_count": 60,
                "primary_keyword": primary_keyword,
            },
            {
                "id": 2,
                "description": "Second SEO meta description about productivity tips.",
                "character_count": 62,
                "primary_keyword": primary_keyword,
            },
        ]

    monkeypatch.setattr(
        "app.routers.generate.generate_seo_meta_from_text",
        fake_generate,
    )

    resp = client.post(
        f"/api/generate/seo/{content_id}",
        json={
            "primary_keyword": "productivity tips",
            "search_intent": "informational",
            "tone": "friendly",
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["content_id"] == content_id
    assert isinstance(data["metas"], list)
    assert len(data["metas"]) == 2
    first = data["metas"][0]
    assert {"id", "description", "character_count", "primary_keyword"} <= set(first.keys())
    assert first["primary_keyword"] == "productivity tips"


def test_generate_seo_404_missing_content(client: TestClient) -> None:
    resp = client.post(
        "/api/generate/seo/999999",
        json={
            "primary_keyword": "productivity tips",
            "search_intent": "informational",
        },
    )
    assert resp.status_code == 404


def test_generate_seo_400_too_short(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(client, "short text")

    def fake_generate(
        _: str,
        *,
        title: str | None,
        primary_keyword: str,
        search_intent: str,
        tone: str | None = None,
    ) -> list[dict[str, Any]]:
        raise AssertionError("Service should not be called for too-short content")

    monkeypatch.setattr(
        "app.routers.generate.generate_seo_meta_from_text",
        fake_generate,
    )

    resp = client.post(
        f"/api/generate/seo/{content_id}",
        json={
            "primary_keyword": "productivity tips",
            "search_intent": "informational",
        },
    )
    assert resp.status_code == 400


def test_generate_seo_422_invalid_id(client: TestClient) -> None:
    resp = client.post(
        "/api/generate/seo/not-an-int",
        json={
            "primary_keyword": "productivity tips",
            "search_intent": "informational",
        },
    )
    assert resp.status_code == 422


def test_generate_seo_502_service_failure(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content for testing SEO meta service failure handling.",
    )

    def failing_generate(
        _: str,
        *,
        title: str | None,
        primary_keyword: str,
        search_intent: str,
        tone: str | None = None,
    ) -> list[dict[str, Any]]:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routers.generate.generate_seo_meta_from_text",
        failing_generate,
    )

    resp = client.post(
        f"/api/generate/seo/{content_id}",
        json={
            "primary_keyword": "productivity tips",
            "search_intent": "informational",
        },
    )
    assert resp.status_code == 502


def test_generate_seo_500_empty_result(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content that will produce an empty list of SEO metas.",
    )

    def empty_generate(
        _: str,
        *,
        title: str | None,
        primary_keyword: str,
        search_intent: str,
        tone: str | None = None,
    ) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr(
        "app.routers.generate.generate_seo_meta_from_text",
        empty_generate,
    )

    resp = client.post(
        f"/api/generate/seo/{content_id}",
        json={
            "primary_keyword": "productivity tips",
            "search_intent": "informational",
        },
    )
    assert resp.status_code == 500


def test_generate_image_happy_path(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is a sufficiently long piece of content used for image generation tests.",
    )

    # Make the seed deterministic so the URL is predictable.
    def fake_randint(_: int, __: int) -> int:
        return 123456

    monkeypatch.setattr(
        "app.services.pollinations_service.random.randint",
        fake_randint,
    )

    resp = client.post(
        f"/api/generate/image/{content_id}",
        json={"style": "minimal_gradient", "type": "cover"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["content_id"] == content_id
    image = data["image"]
    assert isinstance(image, dict)
    assert image["type"] == "image_cover"
    assert image["style"] == "minimal_gradient"
    assert image["width"] == 1200
    assert image["height"] == 630
    assert "image_url" in image
    assert "prompt" in image
    assert "/api/generate/image/serve/" in image["image_url"]


def test_generate_image_404_missing_content(client: TestClient) -> None:
    resp = client.post(
        "/api/generate/image/999999",
        json={"style": "minimal_gradient", "type": "cover"},
    )
    assert resp.status_code == 404


def test_generate_image_400_too_short(client: TestClient) -> None:
    content_id = _create_content(client, "short text")

    resp = client.post(
        f"/api/generate/image/{content_id}",
        json={"style": "minimal_gradient", "type": "cover"},
    )
    assert resp.status_code == 400


def test_generate_image_422_invalid_id(client: TestClient) -> None:
    resp = client.post(
        "/api/generate/image/not-an-int",
        json={"style": "minimal_gradient", "type": "cover"},
    )
    assert resp.status_code == 422


def test_serve_generated_image_404_missing_row(client: TestClient) -> None:
    resp = client.get("/api/generate/image/serve/999999")
    assert resp.status_code == 404


def test_serve_generated_image_503_missing_api_key(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    content_id = _create_content(
        client,
        "This is valid content used to create a generated image row for proxy tests.",
    )

    # Deterministic seed for generated metadata.
    monkeypatch.setattr(
        "app.services.pollinations_service.random.randint",
        lambda _a, _b: 123456,
    )

    create_resp = client.post(
        f"/api/generate/image/{content_id}",
        json={"style": "minimal_gradient", "type": "cover"},
    )
    assert create_resp.status_code == 201
    image_id = create_resp.json()["image"]["id"]

    monkeypatch.setattr("app.routers.generate.settings.POLLINATIONS_API_KEY", "")
    serve_resp = client.get(f"/api/generate/image/serve/{image_id}")
    assert serve_resp.status_code == 503

