"""
Content API tests: POST /api/content/, GET /api/content/, GET /api/content/{id}.

Uses real app and DATABASE_URL. Test data may remain in the DB.
Run: cd backend && pytest tests/ -v
"""

from fastapi.testclient import TestClient


# --- Health ---


def test_api_health_returns_healthy(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data.get("database") == "connected"


# --- POST /api/content/ ---


def test_create_content_success_minimal(client: TestClient):
    payload = {
        "original_text": "This is at least ten characters long so validation will pass."
    }
    response = client.post("/api/content/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    # Backend uses len(original_text.split()) → this sentence has 11 words
    assert data["word_count"] == 11
    assert data["original_text"] == payload["original_text"]
    assert "created_at" in data
    assert data.get("title") is None
    assert data.get("source_url") is None


def test_create_content_success_with_title_and_url(client: TestClient):
    payload = {
        "original_text": "Another valid content block with more than ten characters for the test.",
        "title": "Test title",
        "source_url": "https://example.com/post",
    }
    response = client.post("/api/content/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["source_url"] == payload["source_url"]
    assert data["original_text"] == payload["original_text"]
    # Backend uses len(original_text.split()) → this sentence has 12 words
    assert data["word_count"] == 12


def test_create_content_validation_empty_body(client: TestClient):
    response = client.post("/api/content/", json={})
    assert response.status_code == 422
    err = response.json()
    assert "detail" in err


def test_create_content_validation_missing_original_text(client: TestClient):
    response = client.post("/api/content/", json={"title": "Only title"})
    assert response.status_code == 422


def test_create_content_validation_too_short(client: TestClient):
    response = client.post("/api/content/", json={"original_text": "short"})
    assert response.status_code == 422
    detail = str(response.json().get("detail", []))
    assert "10" in detail or "min_length" in detail.lower()


def test_create_content_validation_over_max_length(client: TestClient):
    response = client.post(
        "/api/content/",
        json={"original_text": "x" * 10_001},
    )
    assert response.status_code == 422
    detail = str(response.json().get("detail", []))
    assert "10000" in detail or "max_length" in detail.lower()


def test_create_content_validation_title_too_long(client: TestClient):
    response = client.post(
        "/api/content/",
        json={
            "original_text": "At least ten characters here for validation to pass.",
            "title": "a" * 256,
        },
    )
    assert response.status_code == 422


def test_create_content_validation_source_url_too_long(client: TestClient):
    response = client.post(
        "/api/content/",
        json={
            "original_text": "At least ten characters here for validation to pass.",
            "source_url": "https://example.com/" + "x" * 500,
        },
    )
    assert response.status_code == 422


# --- GET /api/content/ ---


def test_get_contents_returns_list(client: TestClient):
    response = client.get("/api/content/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_contents_pagination(client: TestClient):
    response = client.get("/api/content/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 2


def test_get_contents_includes_created_item(client: TestClient):
    payload = {"original_text": "Unique content here to find in list later. Enough words."}
    create = client.post("/api/content/", json=payload)
    assert create.status_code == 201
    cid = create.json()["id"]

    list_resp = client.get("/api/content/")
    assert list_resp.status_code == 200
    items = list_resp.json()
    ids = [c["id"] for c in items]
    assert cid in ids


# --- GET /api/content/{id} ---


def test_get_content_by_id_success(client: TestClient):
    payload = {"original_text": "Content for get-by-id test. Has enough characters."}
    create = client.post("/api/content/", json=payload)
    assert create.status_code == 201
    cid = create.json()["id"]

    response = client.get(f"/api/content/{cid}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == cid
    assert data["original_text"] == payload["original_text"]


def test_get_content_by_id_not_found(client: TestClient):
    response = client.get("/api/content/999999")
    assert response.status_code == 404
    assert response.json().get("detail") == "Content not found"


def test_get_content_by_id_invalid_returns_error(client: TestClient):
    response = client.get("/api/content/abc")
    assert response.status_code == 422
