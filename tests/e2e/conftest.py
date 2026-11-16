"""
StegaShield E2E Root Pytest Fixtures & CLI Configuration.
"""

from __future__ import annotations

import os
import sys
import pytest
from pathlib import Path

# Ensure project root and backend are on sys.path in correct order
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
for path_dir in [str(BACKEND_DIR), str(PROJECT_ROOT)]:
    p_str = str(path_dir)
    while p_str in sys.path:
        sys.path.remove(p_str)
    sys.path.insert(0, p_str)

from tests.e2e.client import get_e2e_client, StegaShieldClient
from tests.e2e.fixtures import ImageGenerator, PayloadGenerator, TamperGenerator


def pytest_addoption(parser):
    """Register custom CLI options for E2E testing."""
    group = parser.getgroup("stegashield_e2e", "StegaShield E2E Options")
    group.addoption(
        "--e2e-mode",
        action="store",
        default="auto",
        choices=["auto", "direct_core", "asgi_testclient", "live_http"],
        help="Select client adapter execution mode: auto, direct_core, asgi_testclient, or live_http (default: auto)",
    )
    group.addoption(
        "--e2e-url",
        action="store",
        default="http://127.0.0.1:8000",
        help="Target base URL for live HTTP mode (default: http://127.0.0.1:8000)",
    )


@pytest.fixture(scope="session")
def e2e_mode(request) -> str:
    """Returns the requested execution mode."""
    return request.config.getoption("--e2e-mode")


@pytest.fixture(scope="session")
def e2e_url(request) -> str:
    """Returns the target server URL."""
    return request.config.getoption("--e2e-url")


@pytest.fixture(scope="session")
def e2e_client(e2e_mode: str, e2e_url: str) -> StegaShieldClient:
    """Provides the active StegaShield client adapter for E2E tests."""
    return get_e2e_client(mode=e2e_mode, base_url=e2e_url)


@pytest.fixture(scope="session")
def img_gen() -> type[ImageGenerator]:
    """Provides access to procedural cover image generator."""
    return ImageGenerator


@pytest.fixture(scope="session")
def payload_gen() -> type[PayloadGenerator]:
    """Provides access to procedural payload generator."""
    return PayloadGenerator


@pytest.fixture(scope="session")
def tamper_gen() -> type[TamperGenerator]:
    """Provides access to steganographic tampering generator."""
    return TamperGenerator
