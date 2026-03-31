"""Mainlayer payment verification helper.

Handles token verification and entitlement checking for blog post access.
Implements timeout handling and error recovery for network failures.
"""

from __future__ import annotations

import asyncio
import logging
import os

from mainlayer import MainlayerClient

logger = logging.getLogger(__name__)

_client: MainlayerClient | None = None
VERIFY_TIMEOUT_SECONDS = 10
MAX_RETRIES = 2


def get_client() -> MainlayerClient:
    """Get or create the singleton Mainlayer client."""
    global _client
    if _client is None:
        api_key = os.environ.get("MAINLAYER_API_KEY", "")
        if not api_key:
            logger.warning("MAINLAYER_API_KEY not set")
        _client = MainlayerClient(api_key=api_key)
    return _client


async def verify_token(token: str) -> bool:
    """
    Verify that a token grants access to the blog resource.

    Returns True if access is authorized, False otherwise.
    Implements timeout to prevent hanging on network issues.
    """
    if not token or not isinstance(token, str):
        logger.warning("Invalid token format")
        return False

    resource_id = os.environ.get("MAINLAYER_RESOURCE_ID", "")
    if not resource_id:
        logger.error("MAINLAYER_RESOURCE_ID not configured")
        return False

    client = get_client()

    try:
        # Wrap the call in a timeout to prevent hanging
        access = await asyncio.wait_for(
            client.resources.verify_access(resource_id, token),
            timeout=VERIFY_TIMEOUT_SECONDS,
        )
        return bool(access.authorized)
    except asyncio.TimeoutError:
        logger.warning("Token verification timed out after %ds", VERIFY_TIMEOUT_SECONDS)
        return False
    except Exception as err:
        logger.error("Token verification failed: %s", str(err), exc_info=True)
        return False
