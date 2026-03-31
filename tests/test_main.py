"""Tests for the Blog Micropayments API."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_mainlayer():
    """Mock MainlayerClient so tests never hit the real payment API."""
    access_granted = MagicMock(authorized=True)
    access_denied = MagicMock(authorized=False)

    mock_client = MagicMock()
    mock_client.resources.verify_access = AsyncMock(return_value=access_granted)

    with patch("src.main.ml", mock_client):
        yield mock_client, access_granted, access_denied


@pytest.fixture()
def client(mock_mainlayer):
    from src.main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_list_posts_returns_previews(client):
    resp = client.get("/posts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    for post in data["posts"]:
        assert "content" not in post  # full content not in listing
        assert len(post["preview"]) <= 200


def test_get_post_with_valid_token(client, mock_mainlayer):
    mock_client, access_granted, _ = mock_mainlayer
    mock_client.resources.verify_access = AsyncMock(return_value=access_granted)

    resp = client.get("/posts/1", headers={"X-Mainlayer-Token": "valid-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["content"] is not None
    assert len(data["content"]) > 200


def test_get_post_without_token_returns_422(client):
    resp = client.get("/posts/1")
    assert resp.status_code == 422  # missing required header


def test_get_post_with_invalid_token_returns_402(client, mock_mainlayer):
    mock_client, _, access_denied = mock_mainlayer
    mock_client.resources.verify_access = AsyncMock(return_value=access_denied)

    resp = client.get("/posts/1", headers={"X-Mainlayer-Token": "bad-token"})
    assert resp.status_code == 402
    detail = resp.json()["detail"]
    assert detail["error"] == "payment_required"


def test_get_nonexistent_post_returns_404(client):
    resp = client.get("/posts/9999", headers={"X-Mainlayer-Token": "any-token"})
    assert resp.status_code == 404


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
