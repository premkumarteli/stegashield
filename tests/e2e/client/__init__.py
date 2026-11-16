"""
StegaShield E2E Progressive Client Abstraction Layer.
"""

from __future__ import annotations

import socket
from urllib.parse import urlparse
from typing import Optional

from tests.e2e.client.base import (
    AnalyzeResult,
    AttackLabResult,
    DetectResult,
    EmbedResult,
    ExtractResult,
    StegaShieldClient,
)
from tests.e2e.client.live_http_client import LiveHttpClient
from tests.e2e.client.asgi_client import AsgiClient
from tests.e2e.client.direct_core_adapter import DirectCoreAdapter

__all__ = [
    "StegaShieldClient",
    "EmbedResult",
    "ExtractResult",
    "AnalyzeResult",
    "DetectResult",
    "AttackLabResult",
    "LiveHttpClient",
    "AsgiClient",
    "DirectCoreAdapter",
    "get_e2e_client",
]


def _is_server_listening(base_url: str, timeout: float = 0.3) -> bool:
    """Checks if a TCP port is open at the target base_url."""
    try:
        parsed = urlparse(base_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 8000)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def get_e2e_client(mode: str = "auto", base_url: str = "http://127.0.0.1:8000") -> StegaShieldClient:
    """
    Factory function returning the appropriate StegaShieldClient based on mode.
    - 'live_http': Full network client against running server.
    - 'asgi_testclient': In-memory ASGI client wrapping FastAPI app.
    - 'direct_core': Fallback adapter directly importing backend.app.core modules.
    - 'auto': Automatically selects the highest available tier (Live HTTP -> ASGI -> Direct Core).
    """
    mode = mode.lower().strip()

    if mode == "live_http":
        return LiveHttpClient(base_url=base_url)

    if mode == "asgi_testclient":
        return AsgiClient()

    if mode == "direct_core":
        return DirectCoreAdapter()

    if mode == "auto":
        # 1. Check if live server is reachable
        if _is_server_listening(base_url):
            try:
                client = LiveHttpClient(base_url=base_url)
                # Quick health check
                resp = client._session.get("/docs", timeout=1.0)
                if resp.status_code == 200:
                    return client
            except Exception:
                pass

        # 2. Check if ASGI app can be loaded
        try:
            from backend.app.main import app
            return AsgiClient(app=app)
        except Exception:
            pass

        # 3. Fallback to Direct Core adapter
        return DirectCoreAdapter()

    raise ValueError(f"Unknown client mode: '{mode}'. Expected 'auto', 'live_http', 'asgi_testclient', or 'direct_core'.")
