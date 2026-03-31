"""Mainlayer payment verification helper."""

from __future__ import annotations

import os
from mainlayer import MainlayerClient

_client: MainlayerClient | None = None


def get_client() -> MainlayerClient:
    global _client
    if _client is None:
        _client = MainlayerClient(api_key=os.environ.get("MAINLAYER_API_KEY", ""))
    return _client


async def verify_token(token: str) -> bool:
    """Return True if the token grants access to the blog resource."""
    resource_id = os.environ.get("MAINLAYER_RESOURCE_ID", "")
    client = get_client()
    access = await client.resources.verify_access(resource_id, token)
    return access.authorized
