"""Pytest fixtures for API tests. Uses real app and DATABASE_URL (no override)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient. Uses real DB from env (DATABASE_URL)."""
    with TestClient(app) as c:
        yield c
